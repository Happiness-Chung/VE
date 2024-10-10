# This code is based on https://github.com/Mael-zys/T2M-GPT.git
import os
import json

import torch
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter

import models.vqvae as vqvae
import utils.losses as losses 
import options.option_vqvae as option_vq
import utils.utils_model as utils_model
from dataloader import vqvae_loader, eval_loader
from utils.evaluate import vqvae_evaluation
from options.get_eval_option import get_opt
from models.evaluator_wrapper import EvaluatorModelWrapper
import warnings
warnings.filterwarnings('ignore')
from utils.word_vectorizer import WordVectorizer

def update_lr_warm_up(optimizer, nb_iter, warmup_step, lr):

    current_lr = lr * (nb_iter + 1) / (warmup_step + 1)
    for param_group in optimizer.param_groups:
        param_group["lr"] = current_lr

    return optimizer, current_lr

args = option_vq.get_args_parser()
torch.manual_seed(args.seed)
os.makedirs(args.out_dir, exist_ok = True)

def main():
    logger = utils_model.get_logger(args.out_dir)
    writer = SummaryWriter(args.out_dir)
    logger.info(json.dumps(vars(args), indent=4, sort_keys=True))

    w_vectorizer = WordVectorizer('./glove', 'our_vab')

    if args.dataname == 'kit' : 
        dataset_opt_path = './checkpoints/kit/Comp_v6_KLD005/opt.txt'  
        args.nb_joints = 21
    else :
        dataset_opt_path = './checkpoints/t2m/Comp_v6_KLD005/opt.txt'
        args.nb_joints = 22

    logger.info(f'Training on {args.dataname}, motions are with {args.nb_joints} joints')

    wrapper_opt = get_opt(dataset_opt_path, torch.device('cuda'))
    eval_wrapper = EvaluatorModelWrapper(wrapper_opt)

    train_loader = vqvae_loader.DATALoader(args.dataname,
                                            args.batch_size,
                                            window_size=args.window_size,
                                            unit_length=2**args.down_t)

    train_loader_iter = vqvae_loader.cycle(train_loader)

    val_loader = eval_loader.DATALoader(args.dataname, 'val', 32, w_vectorizer, unit_length=2**args.down_t)

    net = vqvae.HumanVQVAE(args, ## use args to define different parameters in different quantizers
                           args.nb_code,
                           args.code_dim,
                           args.output_emb_width,
                           args.down_t,
                           args.stride_t,
                           args.width,
                           args.depth,
                           args.dilation_growth_rate,
                           args.vq_act,
                           args.vq_norm)

    if args.resume_pth:
        logger.info('loading checkpoint from {}'.format(args.resume_pth))
        ckpt = torch.load(args.resume_pth, map_location='cpu')
        net.load_state_dict(ckpt['net'], strict=True)
    net.train()
    net.cuda()

    optimizer = optim.AdamW(net.parameters(), lr=args.learning_rate, betas=(0.9, 0.99), weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, milestones=args.lr_scheduler, gamma=args.gamma)

    Loss = losses.ReConsLoss(args.recons_loss, args.nb_joints)

    avg_recons, avg_perplexity, avg_commit = 0., 0., 0.

    for nb_iter in range(1, args.warmup_steps):
        optimizer, current_lr = update_lr_warm_up(optimizer, nb_iter, args.warmup_steps, args.learning_rate)

        gt_motion = next(train_loader_iter)
        gt_motion = gt_motion.cuda().float() # (bs, 64, dim)

        pred_motion, loss_commit, perplexity = net(gt_motion)
        loss_motion = Loss(pred_motion, gt_motion)
        loss_vel = Loss.forward_vel(pred_motion, gt_motion)

        loss = loss_motion + args.commit * loss_commit + args.loss_vel * loss_vel

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        avg_recons += loss_motion.item()
        avg_perplexity += perplexity.item()
        avg_commit += loss_commit.item()

        if nb_iter % args.print_iter ==  0 :
            avg_recons /= args.print_iter
            avg_perplexity /= args.print_iter
            avg_commit /= args.print_iter

            logger.info(f"Warmup. Iter {nb_iter} :  lr {current_lr:.5f} \t Commit. {avg_commit:.5f} \t PPL. {avg_perplexity:.2f} \t Recons.  {avg_recons:.5f}")

            avg_recons, avg_perplexity, avg_commit = 0., 0., 0.

    avg_recons, avg_perplexity, avg_commit = 0., 0., 0.
    best_fid, best_div, best_top1, best_top2, best_top3, best_matching, writer, logger = vqvae_evaluation(args.out_dir, val_loader, net, logger, writer, eval_wrapper, 0, best_fid=1000, best_div=100, best_top1=0, best_top2=0, best_top3=0, best_matching=100)
    
    for nb_iter in range(1, args.total_iter + 1):
        gt_motion = next(train_loader_iter)
        gt_motion = gt_motion.cuda().float() # bs, nb_joints, joints_dim, seq_len

        pred_motion, loss_commit, perplexity = net(gt_motion)
        loss_motion = Loss(pred_motion, gt_motion)
        loss_vel = Loss.forward_vel(pred_motion, gt_motion)

        loss = loss_motion + args.commit * loss_commit + args.loss_vel * loss_vel

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        scheduler.step()

        avg_recons += loss_motion.item()
        avg_perplexity += perplexity.item()
        avg_commit += loss_commit.item()

        if nb_iter % args.print_iter ==  0 :
            avg_recons /= args.print_iter
            avg_perplexity /= args.print_iter
            avg_commit /= args.print_iter

            writer.add_scalar('./Train/L1', avg_recons, nb_iter)
            writer.add_scalar('./Train/PPL', avg_perplexity, nb_iter)
            writer.add_scalar('./Train/Commit', avg_commit, nb_iter)

            logger.info(f"Train. Iter {nb_iter} : \t Commit. {avg_commit:.5f} \t PPL. {avg_perplexity:.2f} \t Recons.  {avg_recons:.5f}")

            avg_recons, avg_perplexity, avg_commit = 0., 0., 0.,

        if nb_iter % args.eval_iter==0 :
            best_fid, best_div, best_top1, best_top2, best_top3, best_matching, writer, logger = vqvae_evaluation(args.out_dir, val_loader, net, logger, writer, nb_iter, best_fid, best_div, best_top1, best_top2, best_top3, best_matching, eval_wrapper=eval_wrapper)


if __name__ == '__main__':
    main()
