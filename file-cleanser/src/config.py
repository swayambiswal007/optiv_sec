# src/config.py - Universal configuration for all document types
import os

class Config:
    # ==================== DIRECTORY SETTINGS ====================
    INPUT_DIR = "data/input"
    OUTPUT_DIR = "data/output"
    TEMP_DIR = "data/temp"
    LOG_DIR = "data/logs"
    
    # ==================== FILE FORMAT SUPPORT ====================
    # Image formats
    SUPPORTED_IMAGE_FORMATS = [
        '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', 
        '.webp', '.gif', '.ico', '.ppm', '.pgm'
    ]
    
    # Text formats
    SUPPORTED_TEXT_FORMATS = [
        '.txt', '.log', '.csv', '.tsv', '.md', '.rst'
    ]
    
    # Document formats
    SUPPORTED_DOCUMENT_FORMATS = [
        '.pdf', '.docx', '.doc', '.odt', '.rtf'
    ]
    
    # Spreadsheet formats
    SUPPORTED_SPREADSHEET_FORMATS = [
        '.xlsx', '.xls', '.ods', '.csv'
    ]
    
    # Data formats
    SUPPORTED_DATA_FORMATS = [
        '.json', '.xml', '.yaml', '.yml', '.ini', '.conf'
    ]
    
    # All supported formats combined
    SUPPORTED_FORMATS = (
        SUPPORTED_IMAGE_FORMATS + 
        SUPPORTED_TEXT_FORMATS + 
        SUPPORTED_DOCUMENT_FORMATS + 
        SUPPORTED_SPREADSHEET_FORMATS + 
        SUPPORTED_DATA_FORMATS
    )
    
    # ==================== OCR SETTINGS ====================
    TESSERACT_CMD = None  # Auto-detect
    OCR_CONFIG = r'--oem 3 --psm 6'
    OCR_CONFIDENCE_THRESHOLD = 30
    OCR_LANGUAGES = 'eng+hin'  # English + Hindi for Indian documents
    
    # ==================== REDACTION SETTINGS ====================
    REDACTION_MODE = "blur"  # "blur" or "blackout"
    BLUR_INTENSITY = 45  # Very strong blur
    BLUR_PASSES = 10  # Number of blur passes
    BLACKOUT_COLOR = (0, 0, 0)  # Black
    PADDING_SIZE = 15  # Padding around sensitive regions
    MERGE_NEARBY_REGIONS = True  # Merge close sensitive regions
    MERGE_DISTANCE = 50  # Distance threshold for merging
    
    # ==================== COMPREHENSIVE SENSITIVE DATA PATTERNS ====================
    SENSITIVE_PATTERNS = {
        # ===== INDIAN GOVERNMENT DOCUMENTS =====
        'aadhaar_spaced': r'\b\d{4}\s+\d{4}\s+\d{4}\b',
        'aadhaar_compact': r'\b\d{12}\b',
        'aadhaar_masked': r'\b[X*]{8}\d{4}\b',  # Masked Aadhaar
        'pan_card': r'\b[A-Z]{5}\d{4}[A-Z]\b',
        'voter_id': r'\b[A-Z]{3}\d{7}\b',
        'passport': r'\b[A-Z]\d{7}\b',
        'driving_license': r'\b[A-Z]{2}\d{13,14}\b',
        'gstin': r'\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z\d]\b',
        
        # ===== US DOCUMENTS =====
        'ssn': r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
        'ssn_masked': r'\b[X*]{3}[-\s]?[X*]{2}[-\s]?\d{4}\b',
        'us_passport': r'\b[Cc]?\d{9}\b',
        'ein': r'\b\d{2}[-\s]?\d{7}\b',
        
        # ===== CREDIT CARDS (ALL MAJOR NETWORKS) =====
        'visa': r'\b4\d{3}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'mastercard': r'\b5[1-5]\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'amex': r'\b3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}\b',
        'discover': r'\b6011[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'rupay': r'\b6\d{3}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'credit_card_generic': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'cvv': r'\b\d{3,4}\b',  # CVV/CVC codes
        
        # ===== BANKING INFORMATION =====
        'iban': r'\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b',
        'swift_code': r'\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b',
        'account_number': r'\b(?:A/C|ACC|ACCT|ACCOUNT)[-:\s]?\d{8,18}\b',
        'ifsc_code': r'\b[A-Z]{4}0[A-Z0-9]{6}\b',
        'routing_number': r'\b\d{9}\b',
        
        # ===== EMAIL ADDRESSES =====
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'email_obfuscated': r'\b[A-Za-z0-9._%+-]+\s*(?:@|\[at\]|\(at\))\s*[A-Za-z0-9.-]+\s*(?:\.|\[dot\]|\(dot\))\s*[A-Z|a-z]{2,}\b',
        
        # ===== PHONE NUMBERS (INTERNATIONAL) =====
        'indian_mobile': r'\b(?:\+91[-\s]?)?[6-9]\d{9}\b',
        'us_phone': r'\b(?:\+1[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b',
        'uk_phone': r'\b(?:\+44[-\s]?)?(?:0|\(0\))?\d{4}[-\s]?\d{6}\b',
        'generic_phone': r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4,6}\b',
        
        # ===== IP ADDRESSES & NETWORK =====
        'ipv4': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        'ipv6': r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b',
        'ipv6_compressed': r'\b(?:[A-Fa-f0-9]{1,4}:){1,7}:\b',
        'mac_address': r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b',
        'subnet_mask': r'\b(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}\b',
        
        # ===== DATES (MULTIPLE FORMATS) =====
        'date_dmy': r'\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b',
        'date_mdy': r'\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b',
        'date_ymd': r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
        'date_iso': r'\b\d{4}-\d{2}-\d{2}\b',
        'date_with_time': r'\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\b',
        
        # ===== URLS & DOMAINS =====
        'url_http': r'https?://[^\s<>"{}|\\^`\[\]]+',
        'url_ftp': r'ftp://[^\s<>"{}|\\^`\[\]]+',
        'domain': r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b',
        
        # ===== PASSWORDS & SECRETS =====
        'password_field': r'(?i)(?:password|passwd|pwd)[\s:=]+[^\s]+',
        'api_key': r'(?i)(?:api[_-]?key|apikey)[\s:=]+[A-Za-z0-9_\-]{16,}',
        'secret_key': r'(?i)(?:secret[_-]?key|secretkey)[\s:=]+[A-Za-z0-9_\-]{16,}',
        'token': r'(?i)(?:token|bearer)[\s:=]+[A-Za-z0-9_\-\.]{16,}',
        'jwt': r'\beyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b',
        'private_key': r'-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----',
        
        # ===== MEDICAL INFORMATION =====
        'medicare': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?[A-Z]\b',
        'medical_record': r'\b(?:MRN|MR|MEDICAL\s+RECORD)[-:\s]?\d{6,10}\b',
        
        # ===== ADDRESSES & LOCATIONS =====
        'zipcode_us': r'\b\d{5}(?:-\d{4})?\b',
        'postal_code_uk': r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}\b',
        'pincode_india': r'\b\d{6}\b',
        
        # ===== BIOMETRIC DATA =====
        'fingerprint_id': r'\bFP[-_]?\d{8,12}\b',
        'iris_id': r'\bIRIS[-_]?\d{8,12}\b',
        
        # ===== CRYPTOCURRENCY =====
        'bitcoin_address': r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',
        'ethereum_address': r'\b0x[a-fA-F0-9]{40}\b',
        
        # ===== VEHICLE INFORMATION =====
        'vin': r'\b[A-HJ-NPR-Z0-9]{17}\b',
        'license_plate': r'\b[A-Z]{2}[-\s]?\d{2}[-\s]?[A-Z]{1,2}[-\s]?\d{4}\b',
        
        # ===== TAX INFORMATION =====
        'tax_id': r'\b\d{2}[-\s]?\d{7}\b',
        
        # ===== COORDINATES =====
        'gps_coordinates': r'\b[-+]?\d{1,3}\.\d+,\s*[-+]?\d{1,3}\.\d+\b',
        
        # ===== NAMES (CONTEXT-BASED) =====
        'name_after_keyword': r'(?i)(?:name|naam|नाम)[\s:=-]+([A-Za-z\s]{2,50})',
        'father_name': r'(?i)(?:father|पिता)[\s:=-]+([A-Za-z\s]{2,50})',
        'mother_name': r'(?i)(?:mother|माता)[\s:=-]+([A-Za-z\s]{2,50})',
        # Add these inside SENSITIVE_PATTERNS
'name_standalone': r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Detect capitalized names like Paul Smith
'license_number_generic': r'\b[A-Z]{2,5}\d{3,10}[A-Z]{0,3}\b',  # Matches SMIT092316US and similar
        'license_number_india': r'\b[A-Z]{2}\d{2}[A-Z]{0,2}\d{4,7}\b',  # Matches MH12AB1234
        'license_number_us': r'\b[A-Z0-9]{1,7}\b',  # Matches 1 to 7 alphanumeric characters
        

        
        # ===== EMPLOYEE/STUDENT IDs =====
        'employee_id': r'\b(?:EMP|EMPLOYEE|STAFF)[-_]?\d{4,8}\b',
        'student_id': r'\b(?:STU|STUDENT|ROLL)[-_]?\d{4,8}\b',
        'badge_number': r'\b(?:BADGE|ID)[-_]?\d{4,8}\b',
    }
    
    # ===== CONTEXT-BASED DETECTION =====
    # Keywords that indicate sensitive content
    SENSITIVE_KEYWORDS = [
        'confidential', 'secret', 'private', 'internal', 'restricted',
        'password', 'token', 'key', 'ssn', 'aadhaar', 'pan', 'credit card',
        'account', 'salary', 'medical', 'diagnosis', 'prescription'
    ]
    
    # Document type detection patterns
    DOCUMENT_TYPE_INDICATORS = {
        'aadhaar_card': ['aadhaar', 'uidai', 'government of india', 'भारत सरकार'],
        'pan_card': ['income tax', 'permanent account number', 'pan'],
        'passport': ['passport', 'republic of india', 'nationality'],
        'credit_card': ['credit card', 'visa', 'mastercard', 'valid thru', 'cvv'],
        'bank_statement': ['account statement', 'balance', 'transaction', 'ifsc'],
        'medical_record': ['patient', 'diagnosis', 'prescription', 'medical record'],
        'payslip': ['payslip', 'salary', 'gross pay', 'net pay', 'deductions'],
    }
    
    # ==================== PROCESSING SETTINGS ====================
    # Batch processing
    BATCH_SIZE = 10
    MAX_FILE_SIZE_MB = 50
    
    # Multi-threading
    USE_MULTITHREADING = True
    MAX_WORKERS = 4
    
    # Output settings
    SAVE_METADATA = True
    SAVE_PREVIEW_IMAGES = True
    CREATE_PROCESSING_LOG = True
    
    # Debug settings
    DEBUG_MODE = True
    VERBOSE_OUTPUT = True
    
    # ==================== IMAGE PROCESSING SETTINGS ====================
    # Image preprocessing for better OCR
    APPLY_IMAGE_PREPROCESSING = True
    DENOISE_BEFORE_OCR = True
    SHARPEN_BEFORE_OCR = False
    AUTO_ROTATE = True
    
    # Output image quality
    OUTPUT_IMAGE_QUALITY = 95  # For JPEG
    OUTPUT_IMAGE_FORMAT = 'png'  # Default output format
    
    # ==================== TEXT PROCESSING SETTINGS ====================
    # Text cleaning
    REMOVE_EXTRA_WHITESPACE = True
    STANDARDIZE_CASING = False  # Keep original casing
    FIX_OCR_ERRORS = True
    
    # Text redaction
    REDACTION_PLACEHOLDER = "[REDACTED]"
    INCLUDE_TYPE_IN_PLACEHOLDER = True  # "[EMAIL REDACTED]" vs "[REDACTED]"
    
    # ==================== SPREADSHEET SETTINGS ====================
    # Excel processing
    PROCESS_ALL_SHEETS = True
    PRESERVE_FORMULAS = True
    PRESERVE_FORMATTING = True
    
    # ==================== JSON/XML SETTINGS ====================
    # Structured data
    REDACT_JSON_VALUES = True
    REDACT_XML_TEXT = True
    PRESERVE_STRUCTURE = True
    PRETTY_PRINT_OUTPUT = True
    
    # ==================== PDF SETTINGS ====================
    PDF_DPI = 300  # DPI for PDF to image conversion
    PDF_EXTRACT_IMAGES = True
    PDF_REDACT_IMAGES = True
    
    # ==================== SECURITY SETTINGS ====================
    SECURE_DELETE_TEMP_FILES = True
    OVERWRITE_ORIGINAL = False  # Never overwrite originals
    CREATE_BACKUP = False  # Optional backup before processing
    
    # Compliance
    GDPR_COMPLIANT = True
    HIPAA_COMPLIANT = True
    
    # ==================== REPORTING ====================
    GENERATE_SUMMARY_REPORT = True
    REPORT_FORMAT = 'json'  # 'json', 'html', 'txt'
    
    # ==================== CUSTOM PATTERNS ====================
    # Users can add custom patterns here
    CUSTOM_PATTERNS = {}
    
    @classmethod
    def add_custom_pattern(cls, name: str, pattern: str):
        """Add a custom sensitive data pattern"""
        cls.CUSTOM_PATTERNS[name] = pattern
        cls.SENSITIVE_PATTERNS[name] = pattern
    
    @classmethod
    def get_all_patterns(cls):
        """Get all patterns including custom ones"""
        return {**cls.SENSITIVE_PATTERNS, **cls.CUSTOM_PATTERNS}
    
    @classmethod
    def is_supported_file(cls, file_path: str) -> bool:
        """Check if file type is supported"""
        from pathlib import Path
        ext = Path(file_path).suffix.lower()
        return ext in cls.SUPPORTED_FORMATS