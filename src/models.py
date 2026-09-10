from pydantic import BaseModel
from typing import List

class Scene(BaseModel):
    voiceover_text: str
    video_prompt: str

class VideoScript(BaseModel):
    title: str
    description: str
    tags: List[str]
    scenes: List[Scene]