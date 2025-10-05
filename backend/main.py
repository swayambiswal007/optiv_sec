from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import tempfile
import google.generativeai as genai
from pathlib import Path
from typing import List, Dict
import json

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
model = genai.GenerativeModel("gemini-2.5-flash")

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

def analyze_file_with_ai(file_path: str, file_name: str, file_type: str) -> Dict:
    """Analyze file using Gemini AI"""
    try:
        # Read file bytes
        with open(file_path, "rb") as f:
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
        
        # For images, use the existing AI prompt
        if file_type == "IMAGE":
            response = model.generate_content([
                {"text": """You are analyzing an image for a security systems audit report. 
Your task is to extract *operational and analytical insights*, not just describe what you see.

Please respond in the following structured format:

FILE DESCRIPTION:
Provide a factual 2-3 sentence description of the image (what it visually shows — main object, context, and visible text).

KEY FINDINGS:
List 2-4 concise bullet points that analyze the *function, purpose, or implications* of what is shown. 
Focus on:
• Security or identity verification aspects (if applicable)
• Possible vulnerabilities, authenticity indicators, or automation potential
• Operational relevance (e.g., how it works, what it enables, risks involved)
• DO NOT restate the visible text or describe appearance in Key Findings.
• DO NOT write about design, colors, or patterns unless relevant to function.

Example tone:
- "Enables digital identity verification through magnetic stripe scanning."
- "Relies on physical cards, which may be lost or duplicated."
- "Provides low tamper resistance; suitable only for internal, low-security use."

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
            # For non-image files, create a simpler prompt
            response = model.generate_content([
                {"text": f"""Analyze this {file_type} file and provide insights in the following format:

FILE DESCRIPTION:
Provide a 2-3 sentence description of what this file likely contains based on its type and context.

KEY FINDINGS:
List 2-4 bullet points analyzing potential security implications, data sensitivity, or operational aspects of this file type.

Format your output exactly as:
FILE DESCRIPTION: [your description here]

KEY FINDINGS:
• [first finding]
• [second finding]
• [third finding]"""}
            ])
        
        # Parse the response
        response_text = response.text.strip()
        
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
        
        # Clean up and compress response for UI readability
        def _truncate_sentence(text: str, max_chars: int = 180) -> str:
            t = (text or "").strip()
            if len(t) <= max_chars:
                return t
            # try to cut at the last period within limit
            cut = t.rfind('.', 0, max_chars)
            if cut != -1 and cut >= int(max_chars * 0.6):
                return t[:cut + 1].strip()
            return (t[:max_chars].rstrip(' ,.\n\t') + '…')

        # Description: keep first 1-2 sentences and cap length
        description = description.strip()
        if not description:
            description = f"{file_name} appears to be a {file_type} file with potential data content."
        else:
            # keep up to two sentences
            sentences = [s.strip() for s in description.replace('\n', ' ').split('.') if s.strip()]
            if sentences:
                description = '. '.join(sentences[:2])
                if not description.endswith('.'):
                    description += '.'
            description = _truncate_sentence(description, 220)
        
        # Findings: ensure at most 3 concise bullets, each trimmed
        if not findings:
            findings = [
                f"File type: {file_type}",
                "Content analysis required for detailed assessment",
                "Standard security protocols apply"
            ]
        # Normalize bullets: remove leading symbols and trim
        normalized = []
        for item in findings:
            item_text = str(item).lstrip('•-* ').strip()
            # Prefer first sentence if multiple
            first_sentence = item_text.split('. ')[0].strip()
            concise = _truncate_sentence(first_sentence, 140)
            if concise:
                normalized.append(concise)
            if len(normalized) >= 3:
                break
        findings = normalized or findings[:3]
        
        return {
            "description": description,
            "findings": findings
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
                "keyFindings": analysis["findings"]
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
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
