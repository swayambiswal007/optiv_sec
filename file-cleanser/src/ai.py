import os
from google import genai
from google.genai import types

# Load API key from environment
API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize Gemini client
client = genai.Client(api_key=API_KEY)

# Folder containing your images
image_folder = r'optiv_sec\file-cleanser\src'

# Supported image formats
supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')

filename = "sample.png"
image_path= r'optiv_sec\file-cleanser\data\input\sample.png'
if filename.lower().endswith(supported_formats):
        image_path = os.path.join(image_folder, filename)
        print(f"\n📷 Processing: {filename}")

        try:
            # Read image bytes
            with open(image_path, 'rb') as f:
                image_bytes = f.read()

            # Determine MIME type
            if filename.lower().endswith(('.jpg', '.jpeg')):
                mime_type = 'image/jpeg'
            elif filename.lower().endswith('.png'):
                mime_type = 'image/png'
            else:
                mime_type = 'application/octet-stream'  # fallback

            # Generate caption using Gemini
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    'Describe this image in one or two lines as a caption.'
                ]
            )

            print(f"📝 Caption: {response.text.strip()}")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
