import argparse
import datetime
import logging
import inspect
import math
import os
import warnings
from typing import Dict, Optional, Tuple
from omegaconf import OmegaConf

import torch
import torch.nn.functional as F
import torch.utils.checkpoint

import diffusers
import transformers
from accelerate import Accelerator
from accelerate.logging import get_logger
from accelerate.utils import set_seed
from diffusers import AutoencoderKL, DDPMScheduler, DDIMScheduler
from diffusers.optimization import get_scheduler
from diffusers.utils import check_min_version
from diffusers.utils.import_utils import is_xformers_available
from tqdm.auto import tqdm
from transformers import CLIPTextModel, CLIPTokenizer, CLIPImageProcessor, CLIPVisionModelWithProjection
from motion_editor.models.unet_2d_condition import UNet2DConditionModel
from motion_editor.data.dataset import VideoDataset

from einops import rearrange
import random
from motion_editor.p2p.p2p_stable import AttentionReplace, AttentionRefine
from motion_editor.p2p.ptp_utils import register_attention_control
from diffusers import ControlNetModel
import re

from motion_editor.pipelines.pipeline_motion_editor import MotionEditorPipeline

# Will error if the minimal version of diffusers is not installed. Remove at your own risks.
check_min_version("0.10.0.dev0")

logger = get_logger(__name__, log_level="INFO")


def are_models_equal(model1, model2):
    for (name1, param1), (name2, param2) in zip(model1.named_parameters(), model2.named_parameters()):
        if name1 != name2:
            print("The name is different")
            return False
        # if "cross_pose_attn" not in name1 and not torch.equal(param1.data, param2.data):
        if not torch.equal(param1.data, param2.data):
            print("The value is different")
            print(name1)
            print(name2)
            return False
    return True

def prepare_control(unet, prompts, validation_data):
    assert len(prompts) == 2

    print(prompts[0])
    print(prompts[1])
    length1 = len(prompts[0].split(' '))
    length2 = len(prompts[1].split(' '))
    if length1 == length2:
        # prepare for attn guidance
        cross_replace_steps = 0.8
        self_replace_steps = 0.4
        controller = AttentionReplace(prompts, validation_data['num_inference_steps'],
                                      cross_replace_steps=cross_replace_steps,
                                      self_replace_steps=self_replace_steps)
    else:
        cross_replace_steps = 0.8
        self_replace_steps = 0.4
        controller = AttentionRefine(prompts, validation_data['num_inference_steps'],
                                     cross_replace_steps=self_replace_steps,
                                     self_replace_steps=self_replace_steps)

    print(controller)
    register_attention_control(unet, controller)

    # the update of unet forward function is inplace
    return cross_replace_steps, self_replace_steps


def main(
    pretrained_model_path: str,
    output_dir: str,
    input_data: Dict,
    validation_data: Dict,
    input_batch_size: int = 1,
    gradient_accumulation_steps: int = 1, # 여러스탭에 걸쳐서 그라디언트를 누적하고 한번에 업데이트
    gradient_checkpointing: bool = True, # 메모리 절약을 위해 중간 계산 결과를 저장하지 않음
    mixed_precision: Optional[str] = "fp16", # f16을 사용하여 메모리 절약과 속토를 향상
    enable_xformers_memory_efficient_attention: bool = True, # 어텐션 연산을 메모리 효울적으로 할 수 있게 해 줌
    seed: Optional[int] = None,
    use_sc_attn: bool = True, # spatial attention 사용 여부
    use_st_attn: bool = True, # temporal attention 사용 여부
    st_attn_idx: int = 0, # 모델의 어느 부분에서 시간적 어텐션을 적용할지
    fps: int = 8,
    validation_steps: int = 100,
    trainable_modules: Tuple[str] = ( # 각각 어텐션 계층의 일부
        "attn1.to_q",
        "attn2.to_q",
        "attn_temp",
    ),
    trainable_params: Tuple[str] = (),
    train_batch_size: int = 1,
    max_train_steps: int = 500,
    learning_rate: float = 3e-5,
    scale_lr: bool = False, # 배치 사이즈에 맞춰 러닝레이트 조정
    lr_scheduler: str = "constant", # 어떻게 스케줄링할지. 이건 고정
    lr_warmup_steps: int = 0, # 학습 초기 몇 단계 동안 학습률을 점진적으로 증가시키는 데 사용할 스텝 수
    adam_beta1: float = 0.9, # 모멘텀
    adam_beta2: float = 0.999, # 과거 반영 정도
    adam_weight_decay: float = 1e-2,
    adam_epsilon: float = 1e-08,
    max_grad_norm: float = 1.0, # 그라디언트 클리핑을 위한 max값
    use_8bit_adam: bool = False,
    resume_from_checkpoint: Optional[str] = None,
    checkpointing_steps: int = 500,
    one_stage_checkpoint: Optional[str] = None,
):
    *_, config = inspect.getargvalues(inspect.currentframe())

    # Hugging Face의 Accelerate 라이브러리를 사용하여 모델 학습 과정을 가속화하고, 효율적인 학습 환경을 설정
    accelerator = Accelerator(
        gradient_accumulation_steps=gradient_accumulation_steps,
        mixed_precision=mixed_precision,
    )

    # Make one log on every process with the configuration for debugging.
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=logging.INFO,
    )
    logger.info(accelerator.state, main_process_only=False) # 메인 프로세스엔 더 많이 로깅을 하고 하위 프로세스엔 로깅을 더 적게 함
    # single GPU 환경에서는 하나의 메인 프로세스만 존재한다.
    if accelerator.is_local_main_process:
        transformers.utils.logging.set_verbosity_warning()
        diffusers.utils.logging.set_verbosity_info()
    else:
        transformers.utils.logging.set_verbosity_error()
        diffusers.utils.logging.set_verbosity_error()

    # If passed along, set the training seed now.
    if seed is not None:
        set_seed(seed)

    # Handle the output folder creation
    if accelerator.is_main_process:
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/sample", exist_ok=True)
        OmegaConf.save(config, os.path.join(output_dir, 'config.yaml'))

    # Load tokenizer and models.
    tokenizer = CLIPTokenizer.from_pretrained(pretrained_model_path, subfolder="tokenizer")
    text_encoder = CLIPTextModel.from_pretrained(pretrained_model_path, subfolder="text_encoder")
    vae = AutoencoderKL.from_pretrained(pretrained_model_path, subfolder="vae")
    unet = UNet2DConditionModel.from_pretrained(
        pretrained_model_path, subfolder="unet", use_sc_attn=use_sc_attn,
        use_st_attn=use_st_attn, st_attn_idx=st_attn_idx)
    noise_scheduler = DDPMScheduler.from_pretrained(pretrained_model_path, subfolder="scheduler") # 노이즈 스케줄러는 각 단계에서 얼마만큼의 노이즈를 추가할지, 그리고 노이즈를 어떻게 제거할지를 결정
    controlnet = ControlNetModel.from_pretrained("lllyasviel/sd-controlnet-openpose", torch_dtype=torch.float16)

    # Freeze vae, text_encoder, and unet
    vae.requires_grad_(False)
    text_encoder.requires_grad_(False)
    unet.requires_grad_(False)
    controlnet.requires_grad_(False)

    for name, module in unet.named_modules():
        if "controlnet_adapter" in name:
            for params in module.parameters():
                params.requires_grad = True


    if enable_xformers_memory_efficient_attention:
        if is_xformers_available():
            unet.enable_xformers_memory_efficient_attention()
        else:
            raise ValueError("xformers is not available. Make sure it is installed correctly")

    if gradient_checkpointing: # 훈련 중간과정을 저장하지 않아 메모리를 효율화
        unet.enable_gradient_checkpointing()

    if scale_lr:
        learning_rate = (
            learning_rate * gradient_accumulation_steps * train_batch_size * accelerator.num_processes
        )

    if use_8bit_adam: # 메모리 사용량을 줄임
        try:
            import bitsandbytes as bnb
        except ImportError:
            raise ImportError(
                "Please install bitsandbytes to use 8-bit Adam. You can do so by running `pip install bitsandbytes`"
            )

        optimizer_cls = bnb.optim.AdamW8bit
    else:
        optimizer_cls = torch.optim.AdamW

    optimizer = optimizer_cls(
        unet.parameters(),
        lr=learning_rate,
        betas=(adam_beta1, adam_beta2),
        weight_decay=adam_weight_decay,
        eps=adam_epsilon,
    )

    # Get the training dataset
    input_dataset = VideoDataset(**input_data)

    # Preprocessing the dataset
    input_dataset.prompt_ids = tokenizer(
        input_dataset.prompt, max_length=tokenizer.model_max_length, padding="max_length", truncation=True, return_tensors="pt"
    ).input_ids[0]

    # DataLoaders creation:
    input_dataloader = torch.utils.data.DataLoader(
        input_dataset, batch_size=input_batch_size
    )

    # Get the validation pipeline
    validation_pipeline = MotionEditorPipeline(
        vae=vae,
        text_encoder=text_encoder,
        tokenizer=tokenizer,
        unet=unet,
        scheduler=DDIMScheduler.from_pretrained(pretrained_model_path, subfolder="scheduler"),
        safety_checker=None,
        controlnet=controlnet,
    )
    validation_pipeline.enable_vae_slicing()
    ddim_inv_scheduler = DDIMScheduler.from_pretrained(pretrained_model_path, subfolder='scheduler')
    ddim_inv_scheduler.set_timesteps(validation_data.num_inv_steps)

    lr_scheduler = get_scheduler(
        lr_scheduler,
        optimizer=optimizer,
        num_warmup_steps=lr_warmup_steps * gradient_accumulation_steps,
        num_training_steps=max_train_steps * gradient_accumulation_steps,
    )

    unet, optimizer, input_dataloader, lr_scheduler = accelerator.prepare(
        unet, optimizer, input_dataloader, lr_scheduler
    )

    # For mixed precision training we cast the text_encoder and vae weights to half-precision
    # as these models are only used for inference, keeping weights in full precision is not required.
    weight_dtype = torch.float32
    if accelerator.mixed_precision == "fp16":
        weight_dtype = torch.float16
    elif accelerator.mixed_precision == "bf16":
        weight_dtype = torch.bfloat16

    # Move text_encode and vae to gpu and cast to weight_dtype
    text_encoder.to(accelerator.device, dtype=weight_dtype)
    vae.to(accelerator.device, dtype=weight_dtype)
    controlnet.to(accelerator.device, dtype=weight_dtype)

    # We need to recalculate our total training steps as the size of the training dataloader may have changed.
    num_update_steps_per_epoch = math.ceil(len(input_dataloader) / gradient_accumulation_steps)
    num_train_epochs = math.ceil(max_train_steps / num_update_steps_per_epoch)

    # We need to initialize the trackers we use, and also store our configuration.
    # The trackers initializes automatically on the main process.
    if accelerator.is_main_process:
        accelerator.init_trackers("vid2vid-zero")

    # Zero-shot Eval!
    total_batch_size = input_batch_size * accelerator.num_processes * gradient_accumulation_steps

    logger.info("***** Running training *****")
    logger.info(f"  Num examples = {len(input_dataset)}")
    logger.info(f"  Num Epochs = {num_train_epochs}")
    logger.info(f"  Instantaneous batch size per device = {input_batch_size}")
    logger.info(f"  Total input batch size (w. parallel, distributed & accumulation) = {total_batch_size}")
    global_step = 0
    first_epoch = 0

    if resume_from_checkpoint:
        if resume_from_checkpoint != "latest":
            path = os.path.basename(resume_from_checkpoint)
        else:
            # Get the most recent checkpoint
            dirs = os.listdir(output_dir)
            dirs = [d for d in dirs if d.startswith("checkpoint")]
            dirs = sorted(dirs, key=lambda x: int(x.split("-")[1]))
            path = dirs[-1]
        accelerator.print(f"Resuming from checkpoint {path}")
        accelerator.load_state(os.path.join(output_dir, path))
        global_step = int(path.split("-")[1])

        first_epoch = global_step // num_update_steps_per_epoch
        resume_step = global_step % num_update_steps_per_epoch

    progress_bar = tqdm(range(global_step, max_train_steps), disable=not accelerator.is_local_main_process)
    progress_bar.set_description("Steps")

    image_embed_drop = 0.1
    resume_from_one_stage_checkpoint = one_stage_checkpoint
    accelerator.load_state(resume_from_one_stage_checkpoint)

    initial_params = {}
    for name, param in unet.named_parameters():
        initial_params[name] = param.clone().detach()

    for epoch in range(first_epoch, num_train_epochs):
        unet.train()
        train_loss = 0.0
        for step, batch in enumerate(input_dataloader):
            if resume_from_checkpoint and epoch == first_epoch and step < resume_step:
                if step % gradient_accumulation_steps == 0:
                    progress_bar.update(1)
                continue
            with accelerator.accumulate(unet):
                samples = []
                pixel_values = batch["pixel_values"].to(weight_dtype)

                # save input video
                video = (pixel_values / 2 + 0.5).clamp(0, 1).detach().cpu()
                video = video.permute(0, 2, 1, 3, 4)  # (b, f, c, h, w)
                samples.append(video)
                # start processing
                video_length = pixel_values.shape[1]
                pixel_values = rearrange(pixel_values, "b f c h w -> (b f) c h w")
                latents = vae.encode(pixel_values).latent_dist.sample()
                # take video as input
                latents = rearrange(latents, "(b f) c h w -> b c f h w", f=video_length)
                latents = latents * 0.18215

                source_skeleton = batch["source_conditions"]["openposefull"].to(weight_dtype)
                noise = torch.randn_like(latents)
                bsz = latents.shape[0]
                timesteps = torch.randint(0, noise_scheduler.num_train_timesteps, (bsz,), device=latents.device)
                timesteps = timesteps.long()
                noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)
                encoder_hidden_states = text_encoder(batch["prompt_ids"])[0]

                if noise_scheduler.prediction_type == "epsilon":
                    target = noise
                elif noise_scheduler.prediction_type == "v_prediction":  ## use this for unclip model
                    target = noise_scheduler.get_velocity(latents, noise, timesteps)
                else:
                    raise ValueError(f"Unknown prediction type {noise_scheduler.prediction_type}")

                controlnet_batch_size = 1
                num_images_per_prompt = 1
                do_classifier_free_guidance = False
                device = validation_pipeline._execution_device
                images = validation_pipeline.prepare_image(
                    image=source_skeleton,
                    width=input_data.width,
                    height=input_data.height,
                    batch_size=controlnet_batch_size * num_images_per_prompt,
                    num_images_per_prompt=num_images_per_prompt,
                    device=device,
                    dtype=controlnet.dtype,
                    do_classifier_free_guidance=do_classifier_free_guidance,
                )
                images = rearrange(images, "b f c h w -> (b f) c h w").to(device=controlnet.device, dtype=controlnet.dtype)
                controlnet_latent_model_input = noisy_latents
                controlnet_latent_model_input = rearrange(controlnet_latent_model_input, "b c f h w -> (b f) c h w").to(dtype=controlnet.dtype)
                down_block_res_samples, mid_block_res_sample = controlnet(
                    controlnet_latent_model_input,
                    timesteps,
                    encoder_hidden_states=encoder_hidden_states.repeat(video_length, 1, 1),
                    controlnet_cond=images,
                    conditioning_scale=1.0,
                    return_dict=False,
                )
                down_block_res_samples = [rearrange(sample, "(b f) c h w -> b c f h w", f=video_length) for sample in down_block_res_samples]
                mid_block_res_sample = rearrange(mid_block_res_sample, "(b f) c h w -> b c f h w", f=video_length)

                model_pred = unet(noisy_latents, timesteps, encoder_hidden_states=encoder_hidden_states, down_block_additional_residuals=down_block_res_samples, mid_block_additional_residual=mid_block_res_sample).sample
                loss = F.mse_loss(model_pred.float(), target.float(), reduction="mean")
                avg_loss = accelerator.gather(loss.repeat(train_batch_size)).mean()
                train_loss += avg_loss.item() / gradient_accumulation_steps

                accelerator.backward(loss)
                if accelerator.sync_gradients:
                    accelerator.clip_grad_norm_(unet.parameters(), max_grad_norm)
                optimizer.step()
                lr_scheduler.step()
                optimizer.zero_grad()

            if accelerator.sync_gradients:
                progress_bar.update(1)
                global_step += 1
                accelerator.log({"train_loss": train_loss}, step=global_step)
                train_loss = 0.0

                if global_step % checkpointing_steps == 0:
                    if accelerator.is_main_process:
                        save_path = os.path.join(output_dir, f"checkpoint-{global_step}-two-stage")
                        accelerator.save_state(save_path)
                        controlnet_adapter_weights = unet.controlnet_adapter.state_dict()
                        controlnet_adapter_weights_path = os.path.join(output_dir, f"controlnet_adapter_checkpoint-{global_step}.pth")
                        torch.save(controlnet_adapter_weights, controlnet_adapter_weights_path)
                        logger.info(f"Saved state to {save_path}")

                if global_step % validation_steps == 0:
                    if accelerator.is_main_process:
                        unet.eval()
                        trained_params = {}
                        for name, param in unet.named_parameters():
                            trained_params[name] = param.clone().detach()
                        parameters_changed = False
                        for name in initial_params.keys():
                            if not torch.equal(initial_params[name], trained_params[name]):
                                print(name)
                                parameters_changed = True
                                break
                        if parameters_changed:
                            print("The weights of the model have changed after training")
                        else:
                            print("The weights of the model remain the same after training")
            logs = {"step_loss": loss.detach().item(), "lr": lr_scheduler.get_last_lr()[0]}
            progress_bar.set_postfix(**logs)
            if global_step >= max_train_steps:
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="./configs/motion_editor.yaml")
    args = parser.parse_args()
    main(**OmegaConf.load(args.config))