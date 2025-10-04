import os
from google import genai
from google.genai import types

# ✅ Initialize Gemini client
client = genai.Client(api_key="AIzaSyAdLamwSmWes7xQxf8mI0X3JtmhRNe35qQ")  # <-- replace with your API key

# ✅ Folder containing your images
image_folder = r'optiv_sec\file-cleanser\src'  # use raw string to avoid \f issue

# ✅ Supported image formats
supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')

# ✅ Loop through all images in the folderr
for filename in os.listdir(image_folder):
    if filename.lower().endswith(supported_formats):
        image_path = os.path.join(image_folder, filename)
        print(f"\n📷 Processing: {filename}")

        try:
            # Read image bytes
            with open(image_path, 'rb') as f:
                image_bytes = f.read()

            # Generate caption using Gemini
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type='image/jpeg' if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg') else 'image/png',
                    ),
                    'Describe this image in one or two lines as a caption.'
                ]
            )

            print(f"📝 Caption: {response.text.strip()}")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
