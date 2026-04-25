"""
YOLO Training module for UI element detection.

This module provides a script to train a YOLO model on a custom dataset
representing UI elements like buttons, inputs, and icons.
"""
from ultralytics import YOLO

def train_ui_model():
    """Trains a YOLO model using a specified dataset configuration.
    
    Initializes a YOLOv11 model and trains it on the UI dataset for a fixed
    number of epochs, saving the resulting weights and plots.
    """
    # Initialize the model. YOLOv11n (nano) is used for speed; 
    # consider yolov11m (medium) for better accuracy if hardware permits.
    model = YOLO('yolo11n.pt') 

    # Path to the dataset configuration file (YAML format)
    yaml_path = "ui_yolo_dataset/dataset.yaml"

    print("🔥 YOLO Training Starting...")
    
    # Execute the training process
    results = model.train(
        data=yaml_path,
        epochs=50,             # Number of training epochs
        imgsz=640,             # Input image size (pixels)
        batch=16,              # Batch size (reduce if memory errors occur)
        name='yolo_ui_parser', # Output directory name in 'runs/detect'
        device=0,              # GPU device ID (use 'cpu' if no NVIDIA GPU available)
        plots=True             # Generate and save training metrics plots
    )
    
    print(f"Training completed. Weights are saved in: {results.save_dir}")

if __name__ == '__main__':
    train_ui_model()