# workers/tasks.py

import os
from pathlib import Path
from .worker_config import celery_app
from services.docker_optimizer import DockerImageInspector
from services.gemini_analyzer import GeminiAnalyzer

@celery_app.task
def analyze_image_task(context_path: str): # <-- Now only accepts the path
    """
    A Celery task that reads the Dockerfile from disk, gets AI suggestions,
    builds the image, and analyzes its layers.
    """
    dockerfile_path = Path(context_path) / "Dockerfile"
    dockerfile_content = ""
    
    # --- Part 1: Read the Dockerfile from disk ---
    try:
        with open(dockerfile_path, "r") as f:
            dockerfile_content = f.read()
    except FileNotFoundError:
        return {
            "ai_suggestions": "Error: Dockerfile not found at the project root.",
            "size_analysis": "Build failed.",
            "build_error": "Dockerfile not found."
        }

    # --- Part 2: AI Analysis ---
    gemini_analyzer = GeminiAnalyzer()
    ai_suggestions = gemini_analyzer.analyze_dockerfile_for_optimizations(dockerfile_content)

    # --- Part 3: Image Build and Size Analysis ---
    # We no longer need to create a temporary file. The build uses the original Dockerfile.
    size_analysis = {}
    build_error = None
    try:
        inspector = DockerImageInspector(context_path)
        inspector.build_image(tag='intelli-optimize-temp')
        size_analysis = inspector.get_size_analysis()
    except Exception as e:
        build_error = str(e)

    # --- Part 4: Combine all results ---
    final_result = {
        "ai_suggestions": ai_suggestions,
        "size_analysis": size_analysis,
        "build_error": build_error
    }
    
    return final_result