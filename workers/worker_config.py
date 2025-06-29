from celery import Celery

# The first argument is the name of the current module.
# The `broker` keyword argument specifies the URL of the message broker (Redis).
# The `backend` argument is where Celery will store the results of the tasks.
celery_app = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    imports=('workers.tasks',)
)

# Optional configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone='America/Vancouver',
    enable_utc=True,
)

