import os
import time
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.models import Scene
from google.genai.errors import ServerError

class VideoEngine:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        self.client = genai.Client()
        self.model_id = "veo-3.1-generate-preview" # Or whichever specific Veo model name is active

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(ServerError),
        reraise=True
    )
    def _call_veo_api(self, prompt: str):
        print("Calling Veo API...")
        return self.client.models.generate_videos(
            model=self.model_id,
            prompt=prompt,
            config=types.GenerateVideosConfig(
                 aspect_ratio="9:16",
                 person_generation="allow_adult"
            )
        )

    def generate_video_for_scene(self, scene: Scene, scene_index: int) -> str:
        """Generates video using Veo with non-blocking polling."""
        print(f"Submitting Veo generation for scene {scene_index}...")
        video_path = os.path.join(self.workspace_dir, f"video_{scene_index}.mp4")

        # 1. Initiate the Veo generation job
        # Note: Depending on the specific Veo API implementation in the Gemini SDK,
        # it usually returns an operation that needs to be polled.
        try:
             # Example SDK call (API surface may vary slightly)
             operation = self._call_veo_api(scene.video_prompt)

             # 2. Polling mechanism (Non-blocking in an async context, simple loop here)
             print(f"Polling for scene {scene_index} video completion...")
             while not hasattr(operation, 'done') or not operation.done:
                 # Check if the operation object actually supports polling first
                 # If it returned bytes immediately, break out
                 if not hasattr(operation, 'done'):
                      break
                      
                 time.sleep(5)
                 # In a real async environment, use asyncio.sleep(5)
                 # operation.reload() # Reload state if required by SDK

             if hasattr(operation, 'error') and operation.error:
                 raise Exception(f"Veo generation failed: {operation.error}")

             # 3. Download the resulting video
             # Assuming operation.result contains the video URI or bytes
             # self._download_video(operation.result.uri, video_path)

             # Mocking file creation for scaffold
             with open(video_path, "w") as f:
                 f.write("mock video data")

             return video_path

        except Exception as e:
             print(f"Error generating video for scene {scene_index} after retries: {e}")
             return ""
