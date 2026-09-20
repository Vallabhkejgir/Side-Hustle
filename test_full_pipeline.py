import os
import shutil
import time
from dotenv import load_dotenv
from src.script_engine import ScriptEngine
from src.audio_engine import AudioEngine
from src.video_engine import VideoEngine

load_dotenv()

def test_generation():
    workspace_dir = f"/tmp/youtube_pipeline_test_{int(time.time())}"
    os.makedirs(workspace_dir, exist_ok=True)
    print(f"Workspace initialized at {workspace_dir}")

    try:
        # 1. Script Generation
        print("\n--- Testing Script Engine ---")
        script_engine = ScriptEngine()
        script = script_engine.generate_script("A brief history of AI")
        print(f"✅ Script generated! Title: {script.title}")
        print(f"Scenes count: {len(script.scenes)}")

        # 2. Audio Generation
        print("\n--- Testing Audio Engine (TTS) ---")
        audio_engine = AudioEngine(workspace_dir)
        scene = script.scenes[0]
        
        # Audio generation failed due to 400 INVALID ARGUMENT in the test run
        # This usually means the text payload was improperly formatted or empty.
        print(f"Testing audio with text: '{scene.voiceover_text}'")
        try:
             audio_path = audio_engine.generate_audio_for_scene(scene, 0)
             print(f"✅ Audio generated at {audio_path}")
        except Exception as e:
             print(f"❌ Audio generation failed: {e}")

        # 3. Video Generation
        print("\n--- Testing Video Engine (Veo) ---")
        video_engine = VideoEngine(workspace_dir)
        
        print(f"Testing video with prompt: '{scene.video_prompt}'")
        try:
             video_path = video_engine.generate_video_for_scene(scene, 0)
             print(f"✅ Video generated at {video_path}")
        except Exception as e:
             print(f"❌ Video generation failed: {e}")

    except Exception as e:
        print(f"\n❌ PIPELINE TEST FAILED: {e}")
    finally:
        shutil.rmtree(workspace_dir, ignore_errors=True)
        print("Cleanup complete.")

if __name__ == "__main__":
    test_generation()
