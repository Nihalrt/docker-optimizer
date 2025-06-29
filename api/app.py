# api/app.py

import os
from flask import Flask, request, jsonify
from workers.tasks import analyze_image_task
from services.docker_optimizer import DockerfileAnalyzer
from celery.result import AsyncResult
from workers.worker_config import celery_app


app = Flask(__name__)


@app.route('/analyze', methods=['POST'])
def analyze_dockerfile():
    """
    API endpoint to perform static analysis on a Dockerfile.
    """
    dockerfile_content = request.data.decode('utf-8')
    
    temp_dockerfile_path = "temp_dockerfile_for_static_analysis"
    with open(temp_dockerfile_path, "w") as f:
        f.write(dockerfile_content)

    analyzer = DockerfileAnalyzer(temp_dockerfile_path)
    suggestions = analyzer.analyze()
    
    os.remove(temp_dockerfile_path)
    return jsonify({"suggestions": suggestions})


@app.route('/inspect', methods=['POST'])
def inspect_image():
    """
    Triggers a background task to build and inspect a Docker image.
    """
    dockerfile_content = request.data.decode('utf-8')
    
    # For now, the build context is the root of the project directory.
    context_path = os.getcwd() 

    # Call the task with .delay() to run it in the background worker
    task = analyze_image_task.delay(dockerfile_content, context_path)

    # Immediately return the task ID
    return jsonify({"task_id": task.id}), 202


@app.route('/results/<task_id>', methods=['GET'])
def get_task_result(task_id):

    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.ready():

        if task_result.successful():
            result = task_result.get()

            return (
                {
                    "status": "SUCCESS",
                    "result": result

                }
            )
        else:
            return jsonify({"status": "PENDING"}), 202



if __name__ == '__main__':
    app.run(debug=True)