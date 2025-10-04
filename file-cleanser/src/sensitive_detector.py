# src/sensitive_detector.py - Enhanced for Aadhaar cards and government documents
import re
from typing import List, Dict, Tuple
from .config import Config

class SensitiveDataDetector:
    def __init__(self):
        # Enhanced patterns for Indian documents
        self.patterns = {
            **Config.SENSITIVE_PATTERNS,  # Include original patterns
            
            # Aadhaar-specific patterns
            'aadhaar_number': r'\b\d{4}\s+\d{4}\s+\d{4}\b',  # 0000 1111 2222
            'aadhaar_compact': r'\b\d{12}\b',  # 000011112222
            
            # Date patterns (DOB)
            'date_dob': r'\b\d{2}[-/]\d{2}[-/]\d{4}\b',  # 06-09-2016
            'date_indian': r'\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b',
            
            # Name patterns (after keywords)
            'name_field': r'(?:Name\s*[:\-]\s*)([A-Za-z\s]{2,30})',
            'gender_field': r'(?:Gender\s*[:\-]\s*)(MALE|FEMALE|M|F)',
            
            # Government document numbers
            'pan_number': r'\b[A-Z]{5}\d{4}[A-Z]\b',
            'voter_id': r'\b[A-Z]{3}\d{7}\b',
            
            # Phone numbers (Indian format)
            'indian_phone': r'\b[6-9]\d{9}\b',
            'phone_with_code': r'\+91[-\s]?[6-9]\d{9}\b',
            
            # Address components
            'pincode': r'\b\d{6}\b',
            
            # General sensitive keywords
            'government_doc': r'(?:GOVERNMENT\s+OF\s+INDIA|भारत\s+सरकार)',
        }
        
        # Keywords that indicate sensitive regions (for OCR bounding box detection)
        self.sensitive_keywords = [
            'name', 'dob', 'gender', 'aadhaar', 'pan', 'phone', 'mobile',
            'address', 'email', 'catmal', 'male', 'female', 'government',
            # Numbers that look sensitive
            r'\d{4}\s+\d{4}\s+\d{4}',  # Aadhaar format
            r'\d{2}[-/]\d{2}[-/]\d{4}',  # Date format
        ]
    
    def detect_in_text(self, text: str) -> List[Dict]:
        """Enhanced detection including fuzzy matching"""
        matches = []
        
        # Original pattern matching
        for data_type, pattern in self.patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                matches.append({
                    'type': data_type,
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 1.0
                })
        
        # Additional fuzzy detection for names and dates
        additional_matches = self._fuzzy_detection(text)
        matches.extend(additional_matches)
        
        # Remove duplicates
        matches = self._remove_overlapping_matches(matches)
        
        return matches
    
    def _fuzzy_detection(self, text: str) -> List[Dict]:
        """Fuzzy detection for names, dates, and numbers that might be OCR errors"""
        fuzzy_matches = []
        
        # Look for standalone numbers that might be Aadhaar
        number_patterns = [
            r'\b\d{4}\s+\d{4}\s+\d{4}\b',  # Standard Aadhaar format
            r'\b\d{4}\s?\d{4}\s?\d{4}\b',   # With optional spaces
            r'\b\d{12}\b',                   # Compact format
        ]
        
        for pattern in number_patterns:
            for match in re.finditer(pattern, text):
                fuzzy_matches.append({
                    'type': 'suspected_aadhaar',
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.8
                })
        
        # Look for date-like patterns
        date_patterns = [
            r'\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b',
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
        ]
        
        for pattern in date_patterns:
            for match in re.finditer(pattern, text):
                fuzzy_matches.append({
                    'type': 'suspected_date',
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.7
                })
        
        # Look for names after keywords (case insensitive)
        name_context_patterns = [
            r'(?:name|naam)\s*[:\-]?\s*([a-zA-Z\s]{2,25})',
        ]
        
        for pattern in name_context_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).strip()
                if len(name) > 1 and not name.isdigit():
                    fuzzy_matches.append({
                        'type': 'suspected_name',
                        'text': name,
                        'start': match.start(1),
                        'end': match.end(1),
                        'confidence': 0.6
                    })
        
        return fuzzy_matches
    
    def _remove_overlapping_matches(self, matches: List[Dict]) -> List[Dict]:
        """Remove overlapping matches, keeping the highest confidence ones"""
        if not matches:
            return matches
        
        # Sort by start position
        matches.sort(key=lambda x: x['start'])
        
        filtered = []
        for match in matches:
            # Check if this match overlaps with any already added
            overlaps = False
            for existing in filtered:
                if (match['start'] < existing['end'] and match['end'] > existing['start']):
                    # There's an overlap - keep the higher confidence one
                    if match.get('confidence', 1.0) > existing.get('confidence', 1.0):
                        filtered.remove(existing)
                        filtered.append(match)
                    overlaps = True
                    break
            
            if not overlaps:
                filtered.append(match)
        
        return filtered
    
    def detect_in_bounding_boxes(self, bounding_boxes: List[Dict]) -> List[Dict]:
        """Enhanced detection in OCR bounding boxes"""
        sensitive_boxes = []
        
        print(f"🔍 Analyzing {len(bounding_boxes)} OCR regions...")
        
        for i, box in enumerate(bounding_boxes):
            text = box['text'].strip()
            
            if len(text) < 2:  # Skip very short text
                continue
            
            print(f"   Region {i+1}: '{text}' at ({box['x']},{box['y']})")
            
            is_sensitive = False
            sensitive_type = 'unknown'
            
            # Check against all patterns
            for data_type, pattern in self.patterns.items():
                if re.search(pattern, text, re.IGNORECASE):
                    is_sensitive = True
                    sensitive_type = data_type
                    print(f"      ✓ Matches {data_type} pattern")
                    break
            
            # Check for keyword-based detection
            if not is_sensitive:
                for keyword in self.sensitive_keywords:
                    if isinstance(keyword, str):
                        if keyword.lower() in text.lower():
                            is_sensitive = True
                            sensitive_type = f'keyword_{keyword}'
                            print(f"      ✓ Contains sensitive keyword: {keyword}")
                            break
                    else:  # It's a regex pattern
                        if re.search(keyword, text, re.IGNORECASE):
                            is_sensitive = True
                            sensitive_type = 'pattern_match'
                            print(f"      ✓ Matches sensitive pattern")
                            break
            
            # Special checks for Aadhaar card elements
            if not is_sensitive:
                # Check for numbers that could be Aadhaar
                if re.search(r'\d{4}', text) and len(text) >= 4:
                    is_sensitive = True
                    sensitive_type = 'suspected_number'
                    print(f"      ✓ Suspected sensitive number")
                
                # Check for government document indicators
                elif any(word in text.lower() for word in ['government', 'india', 'male', 'female', 'catmal']):
                    is_sensitive = True
                    sensitive_type = 'government_info'
                    print(f"      ✓ Government document information")
            
            if is_sensitive:
                sensitive_box = box.copy()
                sensitive_box['sensitive_type'] = sensitive_type
                sensitive_boxes.append(sensitive_box)
                print(f"      🚨 MARKED AS SENSITIVE: {sensitive_type}")
        
        print(f"🎯 Total sensitive regions found: {len(sensitive_boxes)}")
        return sensitive_boxes
    
    def detect_large_regions_for_redaction(self, bounding_boxes: List[Dict], image_shape) -> List[Dict]:
        """Create larger redaction regions to ensure complete coverage"""
        sensitive_boxes = self.detect_in_bounding_boxes(bounding_boxes)
        
        if not sensitive_boxes:
            return sensitive_boxes
        
        # Group nearby sensitive regions
        merged_boxes = self._merge_nearby_boxes(sensitive_boxes, merge_distance=50)
        
        # Expand boxes for better coverage
        expanded_boxes = []
        for box in merged_boxes:
            expanded_box = self._expand_box(box, image_shape, padding=20)
            expanded_boxes.append(expanded_box)
        
        return expanded_boxes
    
    def _merge_nearby_boxes(self, boxes: List[Dict], merge_distance: int = 50) -> List[Dict]:
        """Merge boxes that are close to each other"""
        if len(boxes) <= 1:
            return boxes
        
        merged = []
        used = set()
        
        for i, box1 in enumerate(boxes):
            if i in used:
                continue
            
            # Start with this box
            min_x = box1['x']
            min_y = box1['y']
            max_x = box1['x'] + box1['w']
            max_y = box1['y'] + box1['h']
            
            # Check all other boxes
            for j, box2 in enumerate(boxes[i+1:], i+1):
                if j in used:
                    continue
                
                # Calculate distance between boxes
                center1_x = box1['x'] + box1['w'] // 2
                center1_y = box1['y'] + box1['h'] // 2
                center2_x = box2['x'] + box2['w'] // 2
                center2_y = box2['y'] + box2['h'] // 2
                
                distance = ((center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2) ** 0.5
                
                if distance <= merge_distance:
                    # Merge this box
                    min_x = min(min_x, box2['x'])
                    min_y = min(min_y, box2['y'])
                    max_x = max(max_x, box2['x'] + box2['w'])
                    max_y = max(max_y, box2['y'] + box2['h'])
                    used.add(j)
            
            # Create merged box
            merged_box = box1.copy()
            merged_box['x'] = min_x
            merged_box['y'] = min_y
            merged_box['w'] = max_x - min_x
            merged_box['h'] = max_y - min_y
            merged.append(merged_box)
            used.add(i)
        
        return merged
    
    def _expand_box(self, box: Dict, image_shape, padding: int = 20) -> Dict:
        """Expand bounding box with padding"""
        height, width = image_shape[:2]
        
        expanded = box.copy()
        expanded['x'] = max(0, box['x'] - padding)
        expanded['y'] = max(0, box['y'] - padding)
        expanded['w'] = min(width - expanded['x'], box['w'] + 2 * padding)
        expanded['h'] = min(height - expanded['y'], box['h'] + 2 * padding)
        
        return expanded
    
    def redact_text(self, text: str, matches: List[Dict]) -> str:
        """Redact sensitive data from text with enhanced replacement"""
        if not matches:
            return text
        
        # Sort matches by position (reverse order for proper replacement)
        matches.sort(key=lambda x: x['start'], reverse=True)
        
        redacted_text = text
        for match in matches:
            # More descriptive redaction labels
            redaction_type = match['type'].upper().replace('_', ' ')
            replacement = f"[{redaction_type} REDACTED]"
            
            redacted_text = (
                redacted_text[:match['start']] + 
                replacement + 
                redacted_text[match['end']:]
            )
        
        return redacted_text