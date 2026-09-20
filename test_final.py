import os
import shutil
import time
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError
from src.video_engine import VideoEngine
from src.models import Scene

load_dotenv()
client = genai.Client()

def test_generation():
    workspace_dir = f"/tmp/youtube_pipeline_test_{int(time.time())}"
    os.makedirs(workspace_dir, exist_ok=True)
    
    print("\n--- Testing Video Engine (Veo) ---")
    video_engine = VideoEngine(workspace_dir)
    # Using a dummy scene
    scene = Scene(voiceover_text="This is a test of the video engine.", video_prompt="Cinematic, 35mm lens, a futuristic city at sunset.")
    print(f"Testing video with prompt: '{scene.video_prompt}'")
    try:
         video_path = video_engine.generate_video_for_scene(scene, 0)
         print(f"✅ Video generated at {video_path}")
    except Exception as e:
         print(f"❌ Video generation failed: {e}")
         
if __name__ == "__main__":
    test_generation()
