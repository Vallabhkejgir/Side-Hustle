import os
import subprocess
from typing import List, Dict

class AssemblyEngine:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir

    def assemble_final_video(self, scenes_media: List[Dict[str, str]]) -> str:
        """
        Assembles the final video by stitching audio and video,
        ensuring audio duration dictates video trimming/looping.
        Uses NVENC (NVIDIA GPU) for hardware-accelerated encoding.
        """
        final_output = os.path.join(self.workspace_dir, "final_video.mp4")
        print("Assembling final video using local GPU (NVENC)...")

        processed_clips = []
        for i, media in enumerate(scenes_media):
            audio_path = media.get('audio')
            video_path = media.get('video')

            if not audio_path or not video_path:
                 continue

            combined_clip_path = os.path.join(self.workspace_dir, f"combined_{i}.mp4")
            print(f"Combining audio and video for scene {i}...")

            # Use FFmpeg to combine video and audio.
            # -stream_loop -1 loops the video infinitely.
            # -shortest stops encoding when the shortest stream (the audio) ends.
            # -c:v h264_nvenc encodes using NVIDIA GPU
            cmd = [
                "ffmpeg",
                "-y", # Overwrite if exists
                "-stream_loop", "-1", # Loop the video
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "h264_nvenc", # Re-encode video using GPU
                "-preset", "fast",    # NVENC preset
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                # Normalize resolution and framerate for seamless concatenation
                "-vf", "scale=1920:1080,fps=30",
                "-shortest",
                combined_clip_path
            ]

            try:
                # Remove stdout=DEVNULL, stderr=PIPE to allow FFmpeg progress to show in terminal
                subprocess.run(cmd, check=True)
                processed_clips.append(combined_clip_path)
                print(f"\nSuccessfully processed scene {i}")
            except subprocess.CalledProcessError as e:
                print(f"\nFFmpeg failed for scene {i}")
                continue

        if not processed_clips:
            raise Exception("No scenes were successfully processed.")

        # Concatenate all combined clips sequentially
        manifest_path = os.path.join(self.workspace_dir, "manifest.txt")
        with open(manifest_path, "w") as f:
             for clip in processed_clips:
                  f.write(f"file '{clip}'\n")

        print("\nConcatenating scenes via FFmpeg...")
        # FFmpeg command to concatenate
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
            subprocess.run(concat_cmd, check=True)
            print("\nSuccessfully concatenated final video!")
        except subprocess.CalledProcessError as e:
            print(f"\nFFmpeg concatenation failed")
            raise Exception("Video concatenation failed.")

        return final_output
