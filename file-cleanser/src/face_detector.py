# src/face_detector.py - Face detection and blurring module
import cv2
import numpy as np
from typing import List, Dict, Tuple
from pathlib import Path

class FaceDetector:
    """Detect and blur faces in images using multiple detection methods"""
    
    def __init__(self):
        self.cascade_paths = self._get_cascade_paths()
        self.face_cascade = None
        self.eye_cascade = None
        self.profile_cascade = None
        
        # Try to load Haar Cascades
        self._load_cascades()
        
        # Detection parameters
        self.scale_factor = 1.1
        self.min_neighbors = 5
        self.min_face_size = (30, 30)
    
    def _get_cascade_paths(self) -> Dict[str, str]:
        """Get paths to Haar Cascade XML files"""
        # Try to find cascades in OpenCV installation
        cv2_data_dir = cv2.data.haarcascades if hasattr(cv2, 'data') else None
        
        cascades = {
            'face': 'haarcascade_frontalface_default.xml',
            'face_alt': 'haarcascade_frontalface_alt2.xml',
            'profile': 'haarcascade_profileface.xml',
            'eye': 'haarcascade_eye.xml',
        }
        
        if cv2_data_dir:
            return {
                name: str(Path(cv2_data_dir) / filename) 
                for name, filename in cascades.items()
            }
        
        return cascades
    
    def _load_cascades(self):
        """Load Haar Cascade classifiers"""
        try:
            # Load face cascade (frontal)
            face_path = self.cascade_paths.get('face')
            if face_path and Path(face_path).exists():
                self.face_cascade = cv2.CascadeClassifier(face_path)
                print(f"✅ Loaded face cascade from: {face_path}")
            else:
                print(f"⚠️  Face cascade not found at: {face_path}")
            
            # Load profile face cascade
            profile_path = self.cascade_paths.get('profile')
            if profile_path and Path(profile_path).exists():
                self.profile_cascade = cv2.CascadeClassifier(profile_path)
                print(f"✅ Loaded profile cascade")
            
            # Load eye cascade (for verification)
            eye_path = self.cascade_paths.get('eye')
            if eye_path and Path(eye_path).exists():
                self.eye_cascade = cv2.CascadeClassifier(eye_path)
                print(f"✅ Loaded eye cascade")
                
        except Exception as e:
            print(f"⚠️  Error loading cascades: {e}")
    
    def detect_faces(self, image_path: str) -> List[Dict]:
        """Detect all faces in image using multiple methods"""
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ Could not load image: {image_path}")
            return []
        
        print(f"🔍 Detecting faces in image...")
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        all_faces = []
        
        # Method 1: Haar Cascade (frontal)
        if self.face_cascade is not None:
            faces = self._detect_with_cascade(gray, self.face_cascade, "Frontal Face")
            all_faces.extend(faces)
        
        # Method 2: Profile face detection
        if self.profile_cascade is not None:
            profile_faces = self._detect_with_cascade(gray, self.profile_cascade, "Profile Face")
            all_faces.extend(profile_faces)
        
        # Method 3: DNN-based detection (more accurate, if available)
        dnn_faces = self._detect_with_dnn(img)
        all_faces.extend(dnn_faces)
        
        # Method 4: Skin color detection (fallback for very small faces)
        skin_faces = self._detect_skin_regions(img)
        all_faces.extend(skin_faces)
        
        # Remove duplicate/overlapping faces
        unique_faces = self._remove_overlapping_faces(all_faces)
        
        print(f"🎯 Total faces detected: {len(unique_faces)}")
        
        return unique_faces
    
    def _detect_with_cascade(self, gray_img: np.ndarray, cascade, method_name: str) -> List[Dict]:
        """Detect faces using Haar Cascade"""
        faces = cascade.detectMultiScale(
            gray_img,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_face_size,
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        face_boxes = []
        for (x, y, w, h) in faces:
            # Add padding around face
            padding = int(min(w, h) * 0.2)
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = w + 2 * padding
            h = h + 2 * padding
            
            face_boxes.append({
                'x': int(x),
                'y': int(y),
                'w': int(w),
                'h': int(h),
                'confidence': 0.8,
                'method': method_name,
                'type': 'face'
            })
        
        if len(faces) > 0:
            print(f"   {method_name}: Found {len(faces)} face(s)")
        
        return face_boxes
    
    def _detect_with_dnn(self, img: np.ndarray) -> List[Dict]:
        """Detect faces using DNN (Deep Neural Network) - more accurate"""
        try:
            # Try to load DNN model if available
            model_file = "res10_300x300_ssd_iter_140000.caffemodel"
            config_file = "deploy.prototxt"
            
            # These files need to be downloaded separately
            # For now, we'll skip DNN if files aren't available
            if not Path(model_file).exists():
                return []
            
            net = cv2.dnn.readNetFromCaffe(config_file, model_file)
            
            h, w = img.shape[:2]
            blob = cv2.dnn.blobFromImage(
                cv2.resize(img, (300, 300)), 
                1.0, 
                (300, 300), 
                (104.0, 177.0, 123.0)
            )
            
            net.setInput(blob)
            detections = net.forward()
            
            faces = []
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                
                if confidence > 0.5:  # 50% confidence threshold
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (x, y, x2, y2) = box.astype("int")
                    
                    faces.append({
                        'x': x,
                        'y': y,
                        'w': x2 - x,
                        'h': y2 - y,
                        'confidence': float(confidence),
                        'method': 'DNN',
                        'type': 'face'
                    })
            
            if faces:
                print(f"   DNN: Found {len(faces)} face(s)")
            
            return faces
            
        except Exception as e:
            # DNN detection failed, return empty
            return []
    
    def _detect_skin_regions(self, img: np.ndarray) -> List[Dict]:
        """Detect potential face regions using skin color detection"""
        # Convert to HSV color space
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Define skin color range in HSV
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        
        # Create mask for skin color
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Apply morphological operations to clean up mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        faces = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter by area (avoid too small or too large regions)
            if 500 < area < 50000:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check aspect ratio (faces are roughly square-ish)
                aspect_ratio = w / float(h)
                if 0.5 < aspect_ratio < 2.0:
                    faces.append({
                        'x': x,
                        'y': y,
                        'w': w,
                        'h': h,
                        'confidence': 0.5,
                        'method': 'Skin Detection',
                        'type': 'face'
                    })
        
        if faces:
            print(f"   Skin Detection: Found {len(faces)} potential face region(s)")
        
        return faces
    
    def _remove_overlapping_faces(self, faces: List[Dict]) -> List[Dict]:
        """Remove duplicate and overlapping face detections"""
        if len(faces) <= 1:
            return faces
        
        # Sort by confidence
        faces.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        unique_faces = []
        
        for face in faces:
            is_duplicate = False
            
            for existing_face in unique_faces:
                # Calculate overlap
                overlap = self._calculate_overlap(face, existing_face)
                
                if overlap > 0.5:  # 50% overlap threshold
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_faces.append(face)
        
        return unique_faces
    
    def _calculate_overlap(self, face1: Dict, face2: Dict) -> float:
        """Calculate overlap ratio between two bounding boxes"""
        x1_min = face1['x']
        y1_min = face1['y']
        x1_max = face1['x'] + face1['w']
        y1_max = face1['y'] + face1['h']
        
        x2_min = face2['x']
        y2_min = face2['y']
        x2_max = face2['x'] + face2['w']
        y2_max = face2['y'] + face2['h']
        
        # Calculate intersection
        x_overlap = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
        y_overlap = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
        
        intersection_area = x_overlap * y_overlap
        
        # Calculate union
        area1 = face1['w'] * face1['h']
        area2 = face2['w'] * face2['h']
        union_area = area1 + area2 - intersection_area
        
        # Return IoU (Intersection over Union)
        return intersection_area / union_area if union_area > 0 else 0
    
    def blur_faces(self, image_path: str, output_path: str, blur_intensity: int = 45) -> Tuple[bool, int]:
        """Detect and blur all faces in image"""
        # Detect faces
        faces = self.detect_faces(image_path)
        
        if not faces:
            print("⚠️  No faces detected")
            # Copy original image
            img = cv2.imread(image_path)
            cv2.imwrite(output_path, img)
            return False, 0
        
        # Load image
        img = cv2.imread(image_path)
        
        print(f"🌀 Blurring {len(faces)} detected face(s)...")
        
        # Blur each face
        for i, face in enumerate(faces, 1):
            x, y, w, h = face['x'], face['y'], face['w'], face['h']
            
            print(f"   {i}. Blurring face at ({x},{y}) size {w}x{h} [{face['method']}]")
            
            # Extract face region
            face_roi = img[y:y+h, x:x+w]
            
            if face_roi.size == 0:
                continue
            
            # Apply very strong blur (multiple passes)
            blurred_face = face_roi.copy()
            
            # Ensure blur intensity is odd
            kernel_size = blur_intensity if blur_intensity % 2 == 1 else blur_intensity + 1
            
            # Multiple blur passes for complete obscuring
            for _ in range(10):
                blurred_face = cv2.GaussianBlur(blurred_face, (kernel_size, kernel_size), 0)
            
            # Additional motion blur
            motion_kernel = np.ones((20, 20), np.float32) / 400
            blurred_face = cv2.filter2D(blurred_face, -1, motion_kernel)
            
            # Apply median blur for extra smoothing
            blurred_face = cv2.medianBlur(blurred_face, 21)
            
            # Replace original face with blurred version
            img[y:y+h, x:x+w] = blurred_face
        
        # Save result
        success = cv2.imwrite(output_path, img)
        
        if success:
            print(f"✅ Faces blurred and saved to: {output_path}")
        else:
            print(f"❌ Failed to save blurred image")
        
        return success, len(faces)
    
    def create_face_preview(self, image_path: str, output_path: str) -> bool:
        """Create preview image showing detected faces"""
        faces = self.detect_faces(image_path)
        
        if not faces:
            return False
        
        img = cv2.imread(image_path)
        
        # Draw rectangles around faces
        colors = [
            (0, 0, 255),    # Red
            (0, 255, 0),    # Green
            (255, 0, 0),    # Blue
            (255, 255, 0),  # Cyan
            (255, 0, 255),  # Magenta
        ]
        
        for i, face in enumerate(faces):
            x, y, w, h = face['x'], face['y'], face['w'], face['h']
            color = colors[i % len(colors)]
            
            # Draw rectangle
            cv2.rectangle(img, (x, y), (x+w, y+h), color, 3)
            
            # Add label
            label = f"Face {i+1} ({face['method']})"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # Background for label
            cv2.rectangle(img, (x, y-30), (x + label_size[0] + 10, y), color, -1)
            cv2.putText(img, label, (x+5, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        success = cv2.imwrite(output_path, img)
        
        if success:
            print(f"🔍 Face preview saved: {output_path}")
        
        return success