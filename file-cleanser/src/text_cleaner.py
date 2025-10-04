import re

class TextCleaner:
    def __init__(self):
        self.cleaning_patterns = [
            # Remove excessive whitespace
            (r'\s+', ' '),
            # Remove special characters but keep basic punctuation
            (r'[^\w\s.,;:!?()-]', ''),
            # Fix common OCR errors
            (r'\bl\b', 'I'),  # lone 'l' to 'I'
            (r'\b0\b', 'O'),  # lone '0' to 'O' in words
            # Normalize punctuation spacing
            (r'\s*([.,;:!?])\s*', r'\1 '),
            (r'\s*([(){}])\s*', r' \1'),
        ]
    
    def clean_text(self, text: str) -> str:
        """Clean and standardize text"""
        if not text:
            return ""
        
        # Apply cleaning patterns
        cleaned_text = text
        for pattern, replacement in self.cleaning_patterns:
            cleaned_text = re.sub(pattern, replacement, cleaned_text)
        
        # Additional cleaning steps
        cleaned_text = self._fix_line_breaks(cleaned_text)
        cleaned_text = self._standardize_casing(cleaned_text)
        cleaned_text = self._remove_artifacts(cleaned_text)
        
        # Final cleanup
        cleaned_text = ' '.join(cleaned_text.split())  # Normalize whitespace
        
        return cleaned_text.strip()
    
    def _fix_line_breaks(self, text: str) -> str:
        """Fix awkward line breaks from OCR"""
        # Remove line breaks within sentences
        text = re.sub(r'([a-z,])\n([a-z])', r'\1 \2', text)
        # Keep paragraph breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text
    
    def _standardize_casing(self, text: str) -> str:
        """Standardize casing patterns"""
        # Fix all caps sentences (convert to sentence case)
        sentences = re.split(r'([.!?]+)', text)
        result = []
        
        for sentence in sentences:
            if sentence.strip() and sentence.isupper() and len(sentence) > 10:
                # Convert all caps to sentence case
                sentence = sentence.lower().capitalize()
            result.append(sentence)
        
        return ''.join(result)
    
    def _remove_artifacts(self, text: str) -> str:
        """Remove common OCR artifacts"""
        artifacts = [
            r'\b[A-Z]{1}\s[A-Z]{1}\s[A-Z]{1}\b',  # Single scattered letters
            r'[|\\/<>]',  # Common OCR misrecognitions
            r'\b\w{1}\b\s+',  # Single character words (except I and a)
        ]
        
        for artifact in artifacts:
            text = re.sub(artifact, ' ', text)
        
        return text