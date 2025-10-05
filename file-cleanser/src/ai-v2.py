import os
import google.generativeai as genai
from pathlib import Path

#API_KEY = os.getenv("GOOGLE_API_KEY")
API_KEY="AIzaSyAdLamwSmWes7xQxf8mI0X3JtmhRNe35qQ"
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

image_path = Path(__file__).parent.parent / "data" / "input" / "sample.png"

with open(image_path, "rb") as f:
    image_bytes = f.read()

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
- “Enables digital identity verification through magnetic stripe scanning.”
- “Relies on physical cards, which may be lost or duplicated.”
- “Provides low tamper resistance; suitable only for internal, low-security use.”

Format your output exactly as:
FILE DESCRIPTION: [your description here]

KEY FINDINGS:
• [first finding]
• [second finding]
• [third finding]"""},

    {"inline_data": {
        "mime_type": "image/png",
        "data": image_bytes
    }}
])

print("Description from Gemini:")
print(response.text)