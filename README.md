# Automated YouTube Video Pipeline (Python & Gemini Ecosystem)

This project provides a fully automated, headless video generation and publishing pipeline. Built on Python, the system leverages the Google GenAI SDK to orchestrate scriptwriting, voiceover synthesis, and cinematic video clip generation (via Veo 3.1). Final assembly is handled locally via FFmpeg, with programmatic publishing managed through the YouTube Data API v3.

## System Architecture

The pipeline follows a modular, event-driven architecture designed to decouple AI generation tasks from heavy media processing and API rate-limiting constraints.

*   **Orchestration Layer (`src/main.py`):** Coordinates the workflow, manages state, and handles the ephemeral workspace.
*   **Cognitive Layer (`src/script_engine.py`):** Gemini 2.5 Flash enforces strict data schemas (via Pydantic) to generate narrative scripts and highly descriptive visual prompts.
*   **Synthesis Layer (`src/audio_engine.py` & `src/video_engine.py`):** Synthesizes TTS audio per scene and uses Veo 3.1 for high-fidelity video clip generation with asynchronous polling.
*   **Assembly Layer (`src/assembly_engine.py`):** A local FFmpeg wrapper that concatenates media streams, loops/trims video to match audio durations perfectly, and renders the final output.
*   **Distribution Layer (`src/youtube_engine.py`):** Uploads the final video to YouTube as a private draft.

## Prerequisites

*   Python 3.10+
*   FFmpeg installed and available in your system `PATH`.
*   Google Cloud Console Project with YouTube Data API v3 enabled.
*   Gemini API Key.

## Setup Instructions

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables:**
    Create a `.env` file in the root of the project with the following structure:

    ```env
    # Gemini API Configuration
    GEMINI_API_KEY="your_gemini_api_key_here"

    # YouTube API Configuration (If using a service account or specific OAuth setup)
    # Alternatively, you may need a client_secrets.json file in your root directory depending on your OAuth implementation.
    # YOUTUBE_CLIENT_ID="your_client_id"
    # YOUTUBE_CLIENT_SECRET="your_client_secret"
    ```

3.  **YouTube Authentication:**
    *Note: The current `YouTubeEngine` is scaffolded. You will need to implement the standard Google OAuth2 flow using `google-auth-oauthlib`.*

## Running the Pipeline

To run a test of the pipeline, execute the main script:

```bash
python -m src.main
```

The pipeline will:
1. Create a temporary workspace in `/tmp`.
2. Generate the script, audio, and video clips.
3. Assemble the final `.mp4`.
4. (Attempt to) upload to YouTube.
5. Clean up the temporary workspace.

## Modifying Topics

To change the topic generated, modify the call at the bottom of `src/main.py`:

```python
if __name__ == "__main__":
    run_pipeline("The Hidden History of the Colosseum")
```
