import os
import shutil
import time
from src.script_engine import ScriptEngine
from src.audio_engine import AudioEngine
from src.video_engine import VideoEngine
from src.assembly_engine import AssemblyEngine
from src.youtube_engine import YouTubeEngine

def run_pipeline(topic: str):
    # 1. Initialize Workspace
    workspace_dir = f"/tmp/youtube_pipeline_{int(time.time())}"
    os.makedirs(workspace_dir, exist_ok=True)
    print(f"Workspace initialized at {workspace_dir}")

    try:
        # 2. Script & Prompt Generation
        script_engine = ScriptEngine()
        script = script_engine.generate_script(topic)

        audio_engine = AudioEngine(workspace_dir)
        video_engine = VideoEngine(workspace_dir)

        # To hold the paths for assembly
        scenes_media = []

        # 3 & 4. Audio & Video Synthesis (Iterating sequentially here, can be parallelized)
        for i, scene in enumerate(script.scenes):
            audio_path = audio_engine.generate_audio_for_scene(scene, i)
            video_path = video_engine.generate_video_for_scene(scene, i)

            scenes_media.append({
                 'audio': audio_path,
                 'video': video_path
            })

        # 5. Media Assembly
        assembly_engine = AssemblyEngine(workspace_dir)
        final_video_path = assembly_engine.assemble_final_video(scenes_media)

        # 6. Publishing
        youtube_engine = YouTubeEngine()
        youtube_engine.upload_video(
             final_video_path,
             title=script.title,
             description=script.description,
             tags=script.tags
        )

    finally:
        # 7. Lifecycle Management (Cleanup)
        print(f"Cleaning up workspace {workspace_dir}...")
        shutil.rmtree(workspace_dir, ignore_errors=True)
        print("Pipeline run complete.")

if __name__ == "__main__":
    # Test the pipeline
    run_pipeline("The Hidden History of the Colosseum")
