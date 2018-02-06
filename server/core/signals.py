import django.dispatch


settings_change = django.dispatch.Signal(providing_args=['request', 'instance', 'changes'])
