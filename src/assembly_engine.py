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
        """
        final_output = os.path.join(self.workspace_dir, "final_video.mp4")
        print("Assembling final video...")

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
            # -c:v copy copies the video stream without re-encoding (if possible)
            # -c:a aac encodes audio to standard AAC.
            # -fflags +shortest -max_interleave_delta 100M helps prevent sync issues when looping.
            
            cmd = [
                "ffmpeg",
                "-y", # Overwrite if exists
                "-stream_loop", "-1", # Loop the video
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "libx264", # Re-encode video to ensure consistent format for concatenation
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                combined_clip_path
            ]
            
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                processed_clips.append(combined_clip_path)
                print(f"Successfully processed scene {i}")
            except subprocess.CalledProcessError as e:
                print(f"FFmpeg failed for scene {i}: {e.stderr.decode('utf-8', errors='ignore')}")
                continue

        if not processed_clips:
            raise Exception("No scenes were successfully processed.")

        # 3. Concatenate all combined clips sequentially
        manifest_path = os.path.join(self.workspace_dir, "manifest.txt")
        with open(manifest_path, "w") as f:
             for clip in processed_clips:
                  f.write(f"file '{clip}'\n")

        print("Concatenating scenes via FFmpeg...")
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
            subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print("Successfully concatenated final video!")
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg concatenation failed: {e.stderr.decode('utf-8', errors='ignore')}")
            raise Exception("Video concatenation failed.")

        return final_output
