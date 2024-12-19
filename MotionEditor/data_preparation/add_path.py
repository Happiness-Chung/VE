import json
import os

# Load the existing JSON file
json_file_path = '/root/video-edit/MotionEditor/data/case-30-resized/images/camera_poses.json'
output_file_path = '/root/video-edit/MotionEditor/data/case-30-resized/images/camera_poses_f.json'
image_folder_path = '/root/video-edit/MotionEditor/data/case-30-resized/images/'

# Function to update file paths in the JSON
def update_file_paths(json_file_path, image_folder_path, output_file_path):
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    # Iterate over each key in the JSON (each image)
    for image_name in data.keys():
        # Update the file_path for each image
        data[image_name]["file_path"] = os.path.join(image_folder_path, image_name)

    # Save the updated JSON to a new file
    with open(output_file_path, 'w') as outfile:
        json.dump(data, outfile, indent=4)

# Call the function to update paths and save the new file
update_file_paths(json_file_path, image_folder_path, output_file_path)

print("Updated JSON saved to:", output_file_path)
