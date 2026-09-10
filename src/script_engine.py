import os
import re
from google import genai
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.models import VideoScript
from google.genai.errors import ServerError

class ScriptEngine:
    def __init__(self):
        # Requires GEMINI_API_KEY environment variable
        self.client = genai.Client()
        self.model_id = "gemini-flash-latest" # Defaulting to latest stable flash

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(ServerError),
        reraise=True
    )
    def _call_gemini_api(self, prompt: str) -> VideoScript:
        """Wrapper for API call with exponential backoff for 503 ServerError."""
        print("Calling Gemini API...")
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": VideoScript,
            },
        )
        
        if response.parsed:
             return response.parsed
        else:
             import json
             return VideoScript.model_validate_json(response.text)

    def generate_script(self, topic: str) -> VideoScript:
        """Generates a complete video script and visual prompts based on a topic."""
        print(f"Generating script for topic: {topic}")

        prompt = f"""
        You are an expert YouTube Shorts producer. Create a script and visual prompts for a vertical short (9:16) about: "{topic}".

        Requirements:
        1. Keep the total duration under 60 seconds (approx 4-6 short scenes).
        2. Ensure the video_prompt is highly descriptive, cinematic, and explicitly styled (e.g., "Cinematic, 35mm lens, 4k resolution, highly detailed").
        3. Make the voiceover_text engaging and punchy. Do not include markdown, emojis, or sound effect brackets in the voiceover_text.
        """
        
        try:
            script_data = self._call_gemini_api(prompt)
        except Exception as e:
            print(f"Failed to generate script after retries: {e}")
            raise e

        # Preprocessing: Sanitize text for TTS (removing unexpected markdown)
        for scene in script_data.scenes:
            scene.voiceover_text = self._sanitize_for_tts(scene.voiceover_text)
            # Video Preprocessing: Enforce global style if the model forgot
            if "cinematic" not in scene.video_prompt.lower():
                 scene.video_prompt = f"Cinematic, 35mm lens, {scene.video_prompt}"

        return script_data

    def _sanitize_for_tts(self, text: str) -> str:
        """Removes markdown and symbols that TTS engines struggle with."""
        text = re.sub(r'[*_#]', '', text)
        return text.strip()
