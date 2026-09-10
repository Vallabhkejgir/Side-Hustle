import os
import re
from google import genai
from pydantic import BaseModel
from src.models import VideoScript

class ScriptEngine:
    def __init__(self):
        # Requires GEMINI_API_KEY environment variable
        self.client = genai.Client()
        self.model_id = "gemini-flash-latest" # Defaulting to latest stable flash

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

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": VideoScript,
            },
        )

        # Pydantic validates and parses the JSON natively if using standard SDK approaches
        # For simplicity in this scaffold, assuming the SDK handles the schema validation correctly.
        if response.parsed:
             script_data = response.parsed
        else:
             import json
             script_data = VideoScript.model_validate_json(response.text)

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
