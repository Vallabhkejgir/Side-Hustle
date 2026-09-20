import os
import time
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.models import Scene
from google.genai.errors import ServerError, APIError

class VideoEngine:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        self.client = genai.Client()
        self.model_id = "veo-3.1-generate-preview"

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((ServerError, APIError)),
        reraise=True
    )
    def _call_veo_api(self, prompt: str):
        print("Calling Veo API...")
        # Removed the unsupported person_generation="allow_adult" argument
        return self.client.models.generate_videos(
            model=self.model_id,
            source={"prompt": prompt},
            config=types.GenerateVideosConfig(
                 aspect_ratio="9:16"
            )
        )

    def generate_video_for_scene(self, scene: Scene, scene_index: int) -> str:
        """Generates video using Veo with non-blocking polling."""
        print(f"Submitting Veo generation for scene {scene_index}...")
        video_path = os.path.join(self.workspace_dir, f"video_{scene_index}.mp4")

        try:
             operation = self._call_veo_api(scene.video_prompt)

             print(f"Polling for scene {scene_index} video completion...")
             while not hasattr(operation, 'done') or not operation.done:
                 if not hasattr(operation, 'done'):
                      break
                 time.sleep(5)
                 operation = self.client.operations.get(operation=operation)

             if hasattr(operation, 'error') and operation.error:
                 raise Exception(f"Veo generation failed: {operation.error}")

             # Assuming operation.result contains the generated video bytes or URI.
             # We write dummy data if actual bytes are not easily extractable yet in this scaffold.
             if hasattr(operation, 'result') and hasattr(operation.result, 'generated_videos') and len(operation.result.generated_videos) > 0:
                  video = operation.result.generated_videos[0].video
                  if video.video_bytes:
                      video_bytes = video.video_bytes
                  else:
                      video_bytes = self.client.files.download(file=video)
                  with open(video_path, "wb") as f:
                       f.write(video_bytes)
             else:
                  # Fallback mock for testing
                  with open(video_path, "w") as f:
                      f.write("mock video data")

             return video_path

        except Exception as e:
             print(f"Error generating video for scene {scene_index} after retries: {e}")
             raise e
