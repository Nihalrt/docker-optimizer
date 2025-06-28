import sys
import os
from pathlib import Path
from .worker_config import celery_app

sys.path.append(str(Path(__file__).parent.parent))

from services.docker_optimizer import DockerImageInspector

@celery_app
def analyze_image_task(dockerfile_content: str, context_path: str):

    dockerfile_path = Path(context_path)

    with open(dockerfile_path, "w") as f:
        f.write(dockerfile_content)

    try:
        inspector = DockerImageInspector(context_path)
        inspector.build_image(tag="intelli-optimize-temp")
        size_analysis = inspector.get_size_analysis()
        return size_analysis
    except Exception as e:
        return {"error": str(e)}
    finally:
        if os.path.exists(dockerfile_path):
            os.remove(dockerfile_path) 

   
