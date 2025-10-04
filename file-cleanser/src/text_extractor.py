import pytesseract
from PIL import Image
import cv2
import numpy as np
from typing import Tuple, List, Dict
from .config import Config

class TextExtractor:
    def __init__(self):
        if Config.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD
    
    def extract_from_image(self, image_path: str) -> Tuple[str, List[Dict]]:
        """
        Extract text and bounding boxes from image
        Returns: (extracted_text, bounding_boxes)
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image)
            
            # Extract text
            text = pytesseract.image_to_string(
                processed_image, 
                config=Config.OCR_CONFIG
            )
            
            # Get bounding boxes with text
            data = pytesseract.image_to_data(
                processed_image, 
                config=Config.OCR_CONFIG,
                output_type=pytesseract.Output.DICT
            )
            
            bounding_boxes = self._extract_bounding_boxes(data)
            
            return text, bounding_boxes
            
        except Exception as e:
            print(f"Error extracting text from {image_path}: {str(e)}")
            return "", []
    
    def _preprocess_image(self, image):
        """Preprocess image to improve OCR accuracy"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh
    
    def _extract_bounding_boxes(self, data: Dict) -> List[Dict]:
        """Extract bounding boxes with associated text"""
        boxes = []
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            if int(data['conf'][i]) > 30:  # Confidence threshold
                text = data['text'][i].strip()
                if text:  # Only include non-empty text
                    boxes.append({
                        'text': text,
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'w': data['width'][i],
                        'h': data['height'][i],
                        'confidence': data['conf'][i]
                    })
        
        return boxes
    
    def extract_from_text_file(self, file_path: str) -> str:
        """Extract text from text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading text file {file_path}: {str(e)}")
            return ""