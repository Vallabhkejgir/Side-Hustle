import os
import subprocess
from typing import List, Dict
import modal
import tempfile
import concurrent.futures

app = modal.App("youtube-assembler")
image = modal.Image.debian_slim().apt_install("ffmpeg")

@app.function(image=image, cpu=32.0, memory=16384, timeout=10800)
def assemble_video_in_cloud(scene_media_bytes: List[Dict[str, bytes]]) -> bytes:
    """
    Runs in Modal cloud. Takes a list of dicts with 'audio' and 'video' bytes,
    runs the FFmpeg assembly process, and returns the assembled final_video.mp4 bytes.
    """
    with tempfile.TemporaryDirectory() as temp_dir:

        def process_scene(i, media):
            audio_bytes = media.get('audio')
            video_bytes = media.get('video')

            if not audio_bytes or not video_bytes:
                return None

            audio_path = os.path.join(temp_dir, f"audio_{i}.mp3")
            video_path = os.path.join(temp_dir, f"video_{i}.mp4")

            with open(audio_path, "wb") as f:
                f.write(audio_bytes)
            with open(video_path, "wb") as f:
                f.write(video_bytes)

            combined_clip_path = os.path.join(temp_dir, f"combined_{i}.mp4")
            print(f"[Modal] Combining audio and video for scene {i}...")

            cmd = [
                "ffmpeg",
                "-y", # Overwrite if exists
                "-stream_loop", "-1", # Loop the video
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "libx264", # Re-encode video to ensure consistent format for concatenation
                "-preset", "ultrafast", # Speed up encoding significantly
                "-threads", "4", # 4 threads per scene
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                combined_clip_path
            ]

            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                print(f"[Modal] Successfully processed scene {i}")
                return (i, combined_clip_path)
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode('utf-8', errors='ignore')
                print(f"[Modal] FFmpeg failed for scene {i}: {error_msg}")
                raise Exception(f"FFmpeg failed for scene {i}: {error_msg}")

        # Run scenes in parallel using max 8 workers to prevent OOM
        # 8 workers * 4 threads = 32 CPUs effectively used
        processed_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(process_scene, i, media) for i, media in enumerate(scene_media_bytes)]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    processed_results.append(res)

        # Sort by index to maintain correct order
        processed_results.sort(key=lambda x: x[0])
        processed_clips = [x[1] for x in processed_results]

        if not processed_clips:
            raise Exception("No scenes were successfully processed.")

        # Concatenate all combined clips sequentially
        manifest_path = os.path.join(temp_dir, "manifest.txt")
        with open(manifest_path, "w") as f:
             for clip in processed_clips:
                  f.write(f"file '{clip}'\n")

        print("[Modal] Concatenating scenes via FFmpeg...")
        final_output = os.path.join(temp_dir, "final_video.mp4")
        concat_cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", manifest_path,
            "-c", "copy",
            final_output
        ]

        try:
            subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print("[Modal] Successfully concatenated final video!")
        except subprocess.CalledProcessError as e:
            print(f"[Modal] FFmpeg concatenation failed: {e.stderr.decode('utf-8', errors='ignore')}")
            raise Exception("Video concatenation failed.")

        # Read the final video bytes to return
        with open(final_output, "rb") as f:
            final_bytes = f.read()

        return final_bytes


class AssemblyEngine:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir

    def assemble_final_video(self, scenes_media: List[Dict[str, str]]) -> str:
        """
        Reads local files, ships them to Modal for assembly,
        and writes the resulting assembled video back locally.
        """
        final_output = os.path.join(self.workspace_dir, "final_video.mp4")
        print("Preparing to offload assembly to Modal...")

        scene_media_bytes = []
        for i, media in enumerate(scenes_media):
            audio_path = media.get('audio')
            video_path = media.get('video')

            if not audio_path or not os.path.exists(audio_path) or not video_path or not os.path.exists(video_path):
                print(f"Skipping scene {i} due to missing media files.")
                continue

            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            with open(video_path, "rb") as f:
                video_bytes = f.read()

            scene_media_bytes.append({
                'audio': audio_bytes,
                'video': video_bytes
            })

        if not scene_media_bytes:
            raise Exception("No valid scene media found to assemble.")

        print("Executing FFmpeg in Modal cloud...")
        # Start the Modal app context and call the remote function
        with app.run():
            final_video_bytes = assemble_video_in_cloud.remote(scene_media_bytes)

        print("Writing final video to local workspace...")
        with open(final_output, "wb") as f:
            f.write(final_video_bytes)

        print("Final video assembled successfully via Modal!")

        return final_output
