"""
Dataset Preparation module for vision model training.

This module downloads a UI element detection dataset from Hugging Face,
organizes it into the YOLO directory structure, and generates the
necessary YAML configuration file for training.
"""
import os
import shutil
from huggingface_hub import snapshot_download
from pathlib import Path
import yaml

# --- CONFIGURATION ---
REPO_ID = "YashJain/UI-Elements-Detection-Dataset"
DOWNLOAD_DIR = "./raw_download"  # Temporary directory for initial download
FINAL_DIR = "./ui_yolo_dataset"  # Final directory structure for training


def setup_dataset():
    """Downloads, organizes, and configures the UI dataset for YOLO training.
    
    Performs the following steps:
    1. Cleans up existing directories.
    2. Downloads the dataset from Hugging Face.
    3. Creates the standard YOLO folder structure.
    4. Moves and organizes image and label files.
    5. Analyzes class counts and generates the data.yaml config.
    """
    # 1. Cleanup old data
    if os.path.exists(FINAL_DIR):
        shutil.rmtree(FINAL_DIR)
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)

    # 2. Download dataset
    print(f"📥 Downloading dataset from: {REPO_ID}...")
    snapshot_download(
        repo_id=REPO_ID, 
        local_dir=DOWNLOAD_DIR, 
        repo_type="dataset", 
        ignore_patterns=[".gitattributes", "README.md"]
    )

    # 3. Create Folder Structure
    # YOLO expects images and labels in separate folders for train and valid splits
    for split in ['train', 'valid']:
        os.makedirs(os.path.join(FINAL_DIR, split, 'images'), exist_ok=True)
        os.makedirs(os.path.join(FINAL_DIR, split, 'labels'), exist_ok=True)

    print("📂 Organizing files...")

    # 4. File Organization Helper
    def move_files(source_split, target_split):
        """Moves files from the raw download to the organized target split.

        Args:
            source_split: The name of the split in the download folder.
            target_split: The name of the split in the final folder.
        """
        src_path = Path(DOWNLOAD_DIR)
        
        # Search for images and labels recursively in the download directory
        found_images = list(src_path.rglob(f"{source_split}/**/images/*.*"))
        found_labels = list(src_path.rglob(f"{source_split}/**/labels/*.txt"))

        if not found_images:
            print(f"⚠️ WARNING: No images found for {source_split}!")
            return

        print(f"   -> {source_split}: Moving {len(found_images)} images and {len(found_labels)} labels...")

        # Copy images to final destination
        for img_file in found_images:
            shutil.copy(img_file, os.path.join(FINAL_DIR, target_split, 'images', img_file.name))
        
        # Copy labels to final destination
        for lbl_file in found_labels:
            shutil.copy(lbl_file, os.path.join(FINAL_DIR, target_split, 'labels', lbl_file.name))

    # Map raw dataset splits to YOLO splits
    move_files('train', 'train')
    move_files('test', 'valid')

    # 5. Detect Number of Classes
    print("🔍 Analyzing class counts...")
    max_id = -1
    label_files = list(Path(FINAL_DIR).rglob("*.txt"))
    
    for lf in label_files:
        with open(lf, 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split()
                if parts:
                    try:
                        class_id = int(parts[0])
                        if class_id > max_id:
                            max_id = class_id
                    except ValueError:
                        pass # Skip malformed lines

    num_classes = max_id + 1
    print(f"✅ Detected {num_classes} total classes (IDs: 0-{max_id}).")

    # 6. Generate data.yaml
    # We use generic names as the source dataset mapping might vary.
    class_names = [f"Class_{i}" for i in range(num_classes)]

    yaml_data = {
        'path': os.path.abspath(FINAL_DIR),
        'train': 'train/images',
        'val': 'valid/images',
        'nc': num_classes,
        'names': class_names
    }

    yaml_path = os.path.join(FINAL_DIR, 'data.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_data, f)

    print(f"\n🚀 Preparation Complete! Config file saved to: {yaml_path}")
    print("You can now proceed with the training script.")


if __name__ == "__main__":
    setup_dataset()