# List of modules to import when celery starts.
CELERY_IMPORTS = ('convapi.tasks', )

CELERY_DEFAULT_CONVAPI_QUEUE = 'convapi'
CELERY_DEFAULT_CONVAPI_V2_QUEUE = 'convapi_v2'

CELERY_ROUTES = {
    'server.tasks.process_ga_report': {'queue': 'convapi'},
    'server.tasks.process_ga_report_v2': {'queue': 'convapi_v2'},
}
CELERY_ANNOTATIONS = {'convapi.tasks': {'rate_limit': '10/s'}}

CELERY_TASK_MAX_RETRIES = 2
CELERY_TASK_RETRY_DEPLOY = 60

CELERY_QUEUE_PREFIX = 'test'

# BROKER_BACKEND = 'memory'
