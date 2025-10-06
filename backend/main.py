from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import tempfile
import google.generativeai as genai
from pathlib import Path
from typing import List, Dict
import json
import sys
import base64

# Add file-cleanser to path
file_cleanser_path = os.path.join(os.path.dirname(__file__), '..', 'file-cleanser', 'src')
sys.path.insert(0, file_cleanser_path)

# Import file-cleanser modules with absolute imports
try:
    import config as file_cleanser_config
    import universal_processor
    import sensitive_detector
    import text_cleaner
    
    # Create instances
    Config = file_cleanser_config.Config
    UniversalFileProcessor = universal_processor.UniversalFileProcessor
    SensitiveDataDetector = sensitive_detector.SensitiveDataDetector
    TextCleaner = text_cleaner.TextCleaner
except ImportError as e:
    print(f"Error importing file-cleanser modules: {e}")
    print("Make sure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

# Initialize FastAPI app
app = FastAPI(title="File Analyzer Backend", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
API_KEY = "AIzaSyAdLamwSmWes7xQxf8mI0X3JtmhRNe35qQ"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash", generation_config={
    "max_output_tokens": 2048,  # Increase max tokens for longer responses
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 40
})

# Initialize file-cleanser components
processor = UniversalFileProcessor()
sensitive_detector = SensitiveDataDetector()
text_cleaner = TextCleaner()

# Supported file formats
SUPPORTED_FORMATS = [
    '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.gif',
    '.pdf', '.txt', '.csv', '.xlsx', '.xls', '.json', '.xml', '.docx', '.doc'
]

def get_file_type(file_extension: str) -> str:
    """Map file extension to type"""
    if file_extension.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.gif']:
        return "IMAGE"
    elif file_extension.lower() in ['.pdf']:
        return "PDF"
    elif file_extension.lower() in ['.xlsx', '.xls']:
        return "XLSX"
    elif file_extension.lower() in ['.csv']:
        return "CSV"
    elif file_extension.lower() in ['.json']:
        return "JSON"
    elif file_extension.lower() in ['.xml']:
        return "XML"
    elif file_extension.lower() in ['.docx', '.doc']:
        return "DOC"
    elif file_extension.lower() in ['.txt']:
        return "TXT"
    else:
        return file_extension.upper().replace('.', '')

def redact_file(file_path: str) -> tuple[str, str]:
    """Redact sensitive data from file and return (redacted_file_path, redacted_image_base64)"""
    try:
        # Process file with redaction
        result = processor.process_file(file_path, sensitive_detector, text_cleaner)
        
        # Get the redacted file path
        redacted_path = file_path
        redacted_image_base64 = None
        
        if result.get('output_files'):
            redacted_path = result['output_files'][0]
            
            # If it's an image file, convert to base64 for frontend display
            file_ext = Path(file_path).suffix.lower()
            if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.gif']:
                try:
                    with open(redacted_path, "rb") as f:
                        redacted_image_base64 = base64.b64encode(f.read()).decode('utf-8')
                except Exception as e:
                    print(f"Error encoding redacted image: {str(e)}")
        
        return redacted_path, redacted_image_base64
    except Exception as e:
        print(f"Error redacting file {file_path}: {str(e)}")
        # Return original file if redaction fails
        return file_path, None

def analyze_file_with_ai(file_path: str, file_name: str, file_type: str) -> Dict:
    """Analyze file using Gemini AI after redaction"""
    try:
        # First redact the file
        redacted_file_path, redacted_image_base64 = redact_file(file_path)
        
        # Read redacted file bytes
        with open(redacted_file_path, "rb") as f:
            file_bytes = f.read()
        
        # Determine MIME type
        mime_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.webp': 'image/webp',
            '.gif': 'image/gif',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword'
        }
        
        file_ext = Path(file_name).suffix.lower()
        mime_type = mime_type_map.get(file_ext, 'application/octet-stream')
        
        # For images, analyze redacted content
        if file_type == "IMAGE":
            response = model.generate_content([
                {"text": """You are analyzing a REDACTED image for a security systems audit report. 
This image has been processed to remove sensitive data (names, numbers, personal info) while preserving the document structure and layout.

Your task is to analyze what type of document this appears to be and assess its security implications based on the visible structure, layout, and any remaining non-sensitive elements.

Please respond in the following structured format:

FILE DESCRIPTION:
Provide a factual 2-3 sentence description of what type of document this appears to be based on its structure, layout, and visible non-sensitive elements.

KEY FINDINGS:
List 2-4 concise bullet points that analyze the *document type, security implications, and operational aspects* based on what you can observe from the redacted structure. 
Focus on:
• Document type identification (ID card, form, certificate, etc.)
• Security features visible in the structure
• Potential vulnerabilities or risks based on document type
• Operational implications for security systems

Example tone:
- "Appears to be an identity verification document with photo and data fields."
- "Contains structured layout typical of government-issued identification."
- "Lacks visible security features like holograms or watermarks."

Format your output exactly as:
FILE DESCRIPTION: [your description here]

KEY FINDINGS:
• [first finding]
• [second finding]
• [third finding]"""},
                {"inline_data": {
                    "mime_type": mime_type,
                    "data": file_bytes
                }}
            ])
        else:
            # For non-image files, analyze redacted content
            response = model.generate_content([
                {"text": f"""You are analyzing a REDACTED {file_type} file for a security systems audit report.
This file has been processed to remove sensitive data while preserving its structure and format.

Your task is to analyze what type of data this file contains and assess its security implications based on the visible structure and any remaining non-sensitive elements.

Please respond in the following structured format:

FILE DESCRIPTION:
Provide a 2-3 sentence description of what type of data this file likely contains based on its structure and format.

KEY FINDINGS:
List 2-4 bullet points analyzing potential security implications, data sensitivity, or operational aspects based on the file type and visible structure.

Format your output exactly as:
FILE DESCRIPTION: [your description here]

KEY FINDINGS:
• [first finding]
• [second finding]
• [third finding]"""}
            ])
        
        # Parse the response
        response_text = response.text.strip()
        
        # Debug: Print the full response to see if it's being truncated
        print(f"Full AI response for {file_name}:")
        print(response_text)
        print("=" * 50)
        
        # Extract description and findings
        lines = response_text.split('\n')
        description = ""
        findings = []
        
        in_description = False
        in_findings = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('FILE DESCRIPTION:'):
                description = line.replace('FILE DESCRIPTION:', '').strip()
                in_description = True
                in_findings = False
            elif line.startswith('KEY FINDINGS:'):
                in_description = False
                in_findings = True
            elif in_description and line and not line.startswith('•'):
                description += " " + line
            elif in_findings and line.startswith('•'):
                findings.append(line.replace('•', '').strip())
        
        # Clean up description
        description = description.strip()
        if not description:
            description = f"{file_name} appears to be a {file_type} file with potential data content."
        
        # If no findings, create generic ones
        if not findings:
            findings = [
                f"File type: {file_type}",
                "Content analysis required for detailed assessment",
                "Standard security protocols apply"
            ]
        
        return {
            "description": description,
            "findings": findings,
            "redacted_image_base64": redacted_image_base64
        }
        
    except Exception as e:
        return {
            "description": f"Error analyzing {file_name}: {str(e)}",
            "findings": ["Analysis failed", "Manual review required"]
        }

@app.get("/")
async def root():
    return {"message": "File Analyzer Backend is running!"}

@app.post("/analyze")
async def analyze_files(files: List[UploadFile] = File(...)):
    """Analyze uploaded files and return structured results"""
    
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    results = []
    
    for file in files:
        # Validate file type
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in SUPPORTED_FORMATS:
            results.append({
                "fileName": file.filename,
                "type": "UNSUPPORTED",
                "description": f"File type {file_ext} is not supported",
                "keyFindings": ["Unsupported file format", "Cannot process this file type"]
            })
            continue
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Get file info
            file_size = len(content)
            file_size_mb = file_size / (1024 * 1024)
            file_type = get_file_type(file_ext)
            
            # Analyze with AI
            analysis = analyze_file_with_ai(tmp_file_path, file.filename, file_type)
            
            # Format response (no filename/size prefix in description)
            result = {
                "fileName": file.filename,
                "type": file_type,
                "description": analysis["description"],
                "keyFindings": analysis["findings"],
                "redactedImageBase64": analysis.get("redacted_image_base64")
            }
            
            results.append(result)
            
        except Exception as e:
            results.append({
                "fileName": file.filename,
                "type": "ERROR",
                "description": f"Error processing {file.filename}: {str(e)}",
                "keyFindings": ["Processing failed", "Manual review required"]
            })
        
        finally:
            # Clean up temp files
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            # Clean up redacted file if it's different from original
            if 'redacted_file_path' in locals() and redacted_file_path != tmp_file_path and os.path.exists(redacted_file_path):
                os.unlink(redacted_file_path)
    
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
