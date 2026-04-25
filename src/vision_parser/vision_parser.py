"""
Vision Parser module for screen analysis using YOLO and OCR.

This module provides the ScreenParser class, which captures the screen,
detects UI elements using a YOLO model, and extracts text content
using Tesseract OCR.
"""
import cv2
import json
import pytesseract
from ultralytics import YOLO
import mss
import numpy as np

class ScreenParser:
    """Class for parsing screen content using computer vision.

    Uses YOLO for object detection and Tesseract for Optical Character Recognition (OCR)
    to identify and describe UI elements on the screen.
    """
    def __init__(self, model_path='runs/detect/yolo_ui_parser/weights/best.pt'):
        """Initializes the ScreenParser with a YOLO model.

        Args:
            model_path: Path to the trained YOLO weights file.
        """
        print("Loading vision model and Tesseract settings...")
        self.model = YOLO(model_path) 
        self.lang = 'tur'  # Language setting for OCR

    def parse_and_visualize(self, image_source=None):
        """Analyzes an image to detect UI elements and extract text.

        If no image source is provided, it captures a live screenshot.

        Args:
            image_source: Optional path to an image file.

        Returns:
            list: A list of dictionaries, each containing data about a detected element.

        Raises:
            ValueError: If the provided image source cannot be read.
        """
        img = None
        
        # --- IMAGE ACQUISITION ---
        if image_source is None:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                img = np.array(sct_img)
                # Convert from BGRA to BGR
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                print("Captured live screenshot.")
        else:
            img = cv2.imread(image_source)
            if img is None:
                raise ValueError(f"Image not found: {image_source}")

        # Create a copy for debugging/visualization purposes
        debug_img = img.copy()

        # --- YOLO DETECTION ---
        results = self.model(img, conf=0.25)[0]
        parsed_elements = []

        print(f"Number of detected objects: {len(results.boxes)}")

        for box in results.boxes:
            # Extract coordinates and metadata
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            confidence = float(box.conf[0])
            
            # Get class name from model names dictionary
            label_name = self.model.names.get(cls_id, f"Class_{cls_id}")

            # --- OCR PROCESSING ---
            # Add padding to ROI for better OCR accuracy
            pad = 5
            h_img, w_img, _ = img.shape
            roi_x1 = max(0, x1 - pad)
            roi_y1 = max(0, y1 - pad)
            roi_x2 = min(w_img, x2 + pad)
            roi_y2 = min(h_img, y2 + pad)

            roi = img[roi_y1:roi_y2, roi_x1:roi_x2]

            try:
                roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                # Binary thresholding to clarify text
                _, roi_thresh = cv2.threshold(roi_gray, 180, 255, cv2.THRESH_BINARY_INV)
                
                detected_text = pytesseract.image_to_string(
                    roi_thresh, lang=self.lang
                ).strip().replace('\n', ' ')
            except Exception:
                detected_text = ""

            # --- DATA STRUCTURING ---
            element_data = {
                "type": label_name,
                "id": cls_id,
                "confidence": round(confidence, 2),
                "bbox": {"x": x1, "y": y1, "w": x2-x1, "h": y2-y1},
                "content": detected_text
            }
            parsed_elements.append(element_data)

            # --- VISUALIZATION (Debugging) ---
            # 1. Draw bounding box (Green)
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # 2. Add label and confidence (Red)
            label_str = f"{label_name} ({confidence:.2f})"
            cv2.putText(debug_img, label_str, (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # 3. Add OCR text (Blue)
            if detected_text:
                cv2.putText(debug_img, f"OCR: {detected_text}", (x1, y2 + 15), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        return parsed_elements

    def save_json(self, data, output_path):
        """Saves parsed element data to a JSON file.

        Args:
            data: The data to be saved.
            output_path: The file path where the JSON will be written.
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"JSON saved to: {output_path}")