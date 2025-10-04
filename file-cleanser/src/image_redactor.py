# src/image_redactor.py - Fixed version with proper blurring
import cv2
import numpy as np
from typing import List, Dict
from .config import Config

class ImageRedactor:
    def __init__(self):
        self.redaction_mode = Config.REDACTION_MODE
        self.blur_intensity = Config.BLUR_INTENSITY
        # Ensure blur intensity is odd number for OpenCV
        if self.blur_intensity % 2 == 0:
            self.blur_intensity += 1
    
    def redact_image(self, image_path: str, sensitive_boxes: List[Dict], output_path: str):
        """Redact sensitive regions in image"""
        try:
            print(f"Loading image: {image_path}")
            image = cv2.imread(image_path)
            
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            print(f"Image loaded successfully. Shape: {image.shape}")
            print(f"Found {len(sensitive_boxes)} sensitive regions to redact")
            print(f"Redaction mode: {self.redaction_mode}")
            
            # Apply redaction to each sensitive box
            for i, box in enumerate(sensitive_boxes):
                x, y, w, h = box['x'], box['y'], box['w'], box['h']
                
                print(f"Processing box {i+1}: text='{box['text']}' at ({x},{y}) size={w}x{h}")
                
                # Add padding around the text for better coverage
                padding = 8
                x_start = max(0, x - padding)
                y_start = max(0, y - padding)
                x_end = min(image.shape[1], x + w + padding)
                y_end = min(image.shape[0], y + h + padding)
                
                # Ensure we have valid dimensions
                if x_end > x_start and y_end > y_start:
                    if self.redaction_mode == "blur":
                        print(f"Applying blur with intensity {self.blur_intensity}")
                        self._blur_region(image, x_start, y_start, x_end - x_start, y_end - y_start)
                    else:  # blackout
                        print("Applying blackout")
                        self._blackout_region(image, x_start, y_start, x_end - x_start, y_end - y_start)
                else:
                    print(f"Invalid box dimensions, skipping: {x_start},{y_start} to {x_end},{y_end}")
            
            # Save redacted image
            print(f"Saving redacted image to: {output_path}")
            success = cv2.imwrite(output_path, image)
            if not success:
                raise ValueError(f"Could not save redacted image to: {output_path}")
            else:
                print("✅ Image saved successfully!")
                
        except Exception as e:
            print(f"❌ Error redacting image: {str(e)}")
            raise
    
    def _blur_region(self, image: np.ndarray, x: int, y: int, w: int, h: int):
        """Apply Gaussian blur to specific region"""
        try:
            print(f"Blurring region: ({x},{y}) size {w}x{h}")
            
            # Extract the region of interest
            roi = image[y:y+h, x:x+w].copy()
            
            if roi.size == 0:
                print("Warning: Empty ROI, skipping blur")
                return
            
            print(f"ROI shape: {roi.shape}")
            
            # Apply multiple blur passes for stronger effect
            blurred_roi = roi.copy()
            
            # Apply Gaussian blur multiple times for stronger effect
            for i in range(3):  # Multiple passes for stronger blur
                kernel_size = max(5, self.blur_intensity)  # Ensure minimum kernel size
                blurred_roi = cv2.GaussianBlur(blurred_roi, (kernel_size, kernel_size), 0)
            
            # Optional: Add motion blur for even stronger effect
            # Create motion blur kernel
            kernel_motion = np.zeros((15, 15))
            kernel_motion[int((15-1)/2), :] = np.ones(15)
            kernel_motion = kernel_motion / 15
            blurred_roi = cv2.filter2D(blurred_roi, -1, kernel_motion)
            
            # Replace the original region with the blurred version
            image[y:y+h, x:x+w] = blurred_roi
            print("✅ Blur applied successfully")
            
        except Exception as e:
            print(f"Error applying blur: {str(e)}")
            # Fallback to blackout if blur fails
            self._blackout_region(image, x, y, w, h)
    
    def _blackout_region(self, image: np.ndarray, x: int, y: int, w: int, h: int):
        """Apply blackout to specific region"""
        try:
            print(f"Blacking out region: ({x},{y}) size {w}x{h}")
            image[y:y+h, x:x+w] = [0, 0, 0]  # Black color
            print("✅ Blackout applied successfully")
        except Exception as e:
            print(f"Error applying blackout: {str(e)}")
    
    def create_preview_image(self, image_path: str, sensitive_boxes: List[Dict]) -> str:
        """Create a preview image with rectangles around sensitive areas (for debugging)"""
        try:
            image = cv2.imread(image_path)
            
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Draw rectangles around sensitive areas
            for i, box in enumerate(sensitive_boxes):
                x, y, w, h = box['x'], box['y'], box['w'], box['h']
                
                # Draw rectangle
                cv2.rectangle(image, (x, y), (x+w, y+h), (0, 0, 255), 2)  # Red rectangle
                
                # Add label
                label = f"{box.get('sensitive_type', 'sensitive')}: {box['text'][:15]}..."
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                
                # Background rectangle for text
                cv2.rectangle(image, (x, y-25), (x + label_size[0], y-5), (0, 0, 255), -1)
                cv2.putText(image, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Save preview image
            preview_path = image_path.replace('.', '_preview.')
            cv2.imwrite(preview_path, image)
            print(f"Preview image saved to: {preview_path}")
            
            return preview_path
            
        except Exception as e:
            print(f"Error creating preview: {str(e)}")
            return None
    
    def test_blur_effect(self, image_path: str, output_path: str = None):
        """Test different blur effects on the entire image"""
        if output_path is None:
            output_path = image_path.replace('.', '_blur_test.')
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            h, w = image.shape[:2]
            
            # Create a grid of different blur effects
            result = np.zeros_like(image)
            
            # Test different blur intensities
            blur_intensities = [5, 15, 25, 35]
            
            for i, intensity in enumerate(blur_intensities):
                # Calculate region for this test
                region_h = h // 2
                region_w = w // 2
                start_y = (i // 2) * region_h
                start_x = (i % 2) * region_w
                end_y = start_y + region_h
                end_x = start_x + region_w
                
                # Apply blur to this region
                roi = image[start_y:end_y, start_x:end_x].copy()
                
                if intensity % 2 == 0:
                    intensity += 1  # Ensure odd number
                
                blurred_roi = cv2.GaussianBlur(roi, (intensity, intensity), 0)
                result[start_y:end_y, start_x:end_x] = blurred_roi
                
                # Add label
                cv2.putText(result, f'Blur: {intensity}', 
                           (start_x + 10, start_y + 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            cv2.imwrite(output_path, result)
            print(f"Blur test image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error creating blur test: {str(e)}")
            return None