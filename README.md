# Python Docker Analyzer

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-black)](https://flask.palletsprojects.com/)
[![Celery](https://img.shields.io/badge/Celery-5.3-green)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-4.5-red)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-20.10%2B-blue)](https://docker.com)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Pro-purple)](https://ai.google.dev/)

An advanced backend service that provides intelligent, AI-driven analysis and optimization suggestions for Dockerfiles. The service uses a distributed task queue to handle long-running image builds asynchronously, ensuring the API remains responsive and scalable.

## Core Features

- **AI-Powered Suggestions**: Integrates the Google Gemini 2.5 Pro API to deliver high-level, context-aware advice on Dockerfile security, efficiency, and best practices.
- **Dynamic Image Inspection**: Builds the Docker image to perform a technical analysis, providing a detailed breakdown of layer sizes.
- **Asynchronous Processing**: Utilizes a Celery and Redis task queue to run slow processes like `docker build` in the background, preventing API timeouts.
- **RESTful API**: Exposes simple endpoints to submit analysis jobs and retrieve the results, allowing for easy integration with other tools and CI/CD pipelines.

## Tech Stack

- **Python**: The core programming language for the entire application.
- **Flask**: A lightweight web framework used to build and serve the REST API.
- **Celery**: A distributed task queue that manages and executes background jobs (e.g., AI analysis, image building).
- **Redis**: An in-memory data store that serves as both the message broker and the result backend for Celery.
- **Docker SDK for Python**: The library used to programmatically interact with the Docker daemon to build and inspect images.
- **Google Gemini API**: The AI model used to provide intelligent analysis and optimization recommendations.

## Architecture Overview

The application is composed of three main services that run concurrently:

1.  **Flask API Server**: The public-facing entry point. It receives requests, creates a new analysis job, and immediately returns a `task_id`.
2.  **Redis Server**: The message broker. It holds the queue of jobs waiting to be processed and stores the final results.
3.  **Celery Worker**: The background process. It constantly monitors the Redis queue, picks up new jobs, performs the AI analysis and Docker build, and saves the result back to Redis.

## API Endpoints

### 1. Submit an Analysis Job

Triggers a new analysis for the `Dockerfile` located in the project's root directory.

- **Endpoint**: `/inspect`
- **Method**: `POST`
- **Example Request**:
  ```bash
  curl -X POST [http://127.0.0.1:5000/inspect](http://127.0.0.1:5000/inspect)
  ```
- **Success Response**:
  ```json
  {
    "task_id": "some-unique-task-id"
  }
  ```

### 2. Retrieve Analysis Results

Fetches the status and result of a previously submitted job.

- **Endpoint**: `/results/<task_id>`
- **Method**: `GET`
- **Example Request**:
  ```bash
  curl [http://127.0.0.1:5000/results/some-unique-task-id](http://127.0.0.1:5000/results/some-unique-task-id)
  ```
- **Success Response**:
  ```json
  {
    "status": "SUCCESS",
    "state": "SUCCESS",
    "result": {
      "ai_suggestions": "...",
      "size_analysis": { "...": "..." },
      "build_error": null
    }
  }
  ```

## Local Setup and Installation

### Prerequisites

- Python 3.9+
- Docker Desktop (or Docker Engine)
- Redis

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Nihalrt/docker-optimizer.git](https://github.com/Nihalrt/docker-optimizer.git)
    cd docker-optimizer
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your Gemini API Key:**
    - Get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
    - Create a file named `.env` in the project root.
    - Add your API key to the `.env` file:
      ```
      GEMINI_API_KEY="YOUR_API_KEY_HERE"
      ```

### Running the Application

You must run three separate services in three different terminal windows.

1.  **Terminal 1: Start Redis**
    If you installed Redis via Homebrew, you can start it as a service:
    ```bash
    brew services start redis
    ```
    If not, run the Redis server directly:
    ```bash
    redis-server
    ```

2.  **Terminal 2: Start the Flask API Server**
    Navigate to the project directory, activate the virtual environment, and run:
    ```bash
    # (Inside the project directory)
    source venv/bin/activate
    python -m api.app
    ```

3.  **Terminal 3: Start the Celery Worker**
    Navigate to the project directory, activate the virtual environment, and run:
    ```bash
    # (Inside the project directory)
    source venv/bin/activate
    celery -A workers.worker_config:celery_app worker --loglevel=info
    ```
    **Important for macOS users:** If you experience Docker connection issues from within VS Code's integrated terminal, run the Celery worker in a separate, standard macOS Terminal application.

Once all three services are running, you can use the API endpoints as described above.
