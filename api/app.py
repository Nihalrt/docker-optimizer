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

    print("--- FLASK API RECEIVED THE FOLLOWING DOCKERFILE CONTENT ---")
    print(dockerfile_content)    
    
    # For now, the build context is the root of the project directory.
    context_path = os.getcwd() 

    # Call the task with .delay() to run it in the background worker
    task = analyze_image_task.delay(context_path)

    # Immediately return the task ID
    return jsonify({"task_id": task.id}), 202


@app.route('/results/<task_id>', methods=['GET'])
def get_task_result(task_id):
    """
    Fetches the result of a background task in a robust way.
    """
    task = AsyncResult(task_id, app=celery_app)

    if task.state == 'PENDING':
        # The task has not started yet
        response = {
            'status': 'PENDING',
            'state': task.state,
        }
    elif task.state == 'SUCCESS':
        # The task finished successfully
        response = {
            'status': 'SUCCESS',
            'state': task.state,
            'result': task.result  # .result is safe to access on success
        }
    elif task.state == 'FAILURE':
        # The task failed
        response = {
            'status': 'FAILURE',
            'state': task.state,
            'error_message': str(task.info) # .info contains the exception
        }
    else:
        # This covers other states like 'STARTED', 'RETRY', etc.
        response = {
            'status': 'IN_PROGRESS',
            'state': task.state
        }
        
    return jsonify(response)





if __name__ == '__main__':
    app.run(debug=True)