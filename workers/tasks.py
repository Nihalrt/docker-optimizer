# workers/tasks.py

import os
from pathlib import Path
from .worker_config import celery_app
from services.docker_optimizer import DockerImageInspector

@celery_app.task
def analyze_image_task(dockerfile_content: str, context_path: str):
    """
    A Celery task to build a Docker image and analyze its layers.
    """
    # Use a unique name for the temporary Dockerfile to avoid conflicts
    dockerfile_path = Path(context_path) / "Dockerfile.temp.build"
    with open(dockerfile_path, "w") as f:
        f.write(dockerfile_content)

    try:
        inspector = DockerImageInspector(context_path)
        inspector.build_image(tag='intelli-optimize-temp')
        size_analysis = inspector.get_size_analysis()
        return size_analysis
    except Exception as e:
        return {"error": str(e)}
    finally:
        # Ensure cleanup happens even if the build fails
        if os.path.exists(dockerfile_path):
            os.remove(dockerfile_path)