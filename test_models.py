import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client()

models_to_test = [
    "gemini-2.5-flash-preview-tts",
    "gemini-flash-latest",
    "veo-3.1-generate-preview",
]

for m in models_to_test:
    print(f"\nTesting {m}...")
    try:
        if "veo" in m:
            response = client.models.generate_videos(
                model=m,
                source={"prompt": "Hello"},
                config=types.GenerateVideosConfig(aspect_ratio="9:16")
            )
            print("Success! Operation:", response.name)
        elif "tts" in m:
            response = client.models.generate_content(
                model=m,
                contents="Hello",
                config=types.GenerateContentConfig(response_modalities=["AUDIO"], speech_config="charon")
            )
            print("Success! Parts:", len(response.candidates[0].content.parts))
        else:
            response = client.models.generate_content(
                model=m,
                contents="Hello"
            )
            print("Success! Response:", response.text)
    except Exception as e:
        print(f"Failed: {e}")
