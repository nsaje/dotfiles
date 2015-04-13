# List of modules to import when celery starts.
CELERY_IMPORTS = ('convapi.tasks', )

CELERY_DEFAULT_CONVAPI_QUEUE = 'convapi'

CELERY_ROUTES = {
    'server.tasks.process_ga_report': {'queue': 'convapi'},
}
CELERY_ANNOTATIONS = {'convapi.tasks': {'rate_limit': '10/s'}}

CELERY_TASK_MAX_RETRIES = 2
CELERY_TASK_RETRY_DEPLAY = 60

CELERY_QUEUE_PREFIX = 'test'
