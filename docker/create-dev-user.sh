#!/bin/bash

set -eo pipefail

if [[ -f /app/zemanta-eins/manage.py ]]; then
	  DIR=/app/zemanta-eins
else
	  DIR=/app/z1
fi

DB_NAME=$(echo 'from django.conf import settings; print(settings.DATABASES["default"]["NAME"])' | $DIR/manage.py shell 2>/dev/null)

if [[ "$DB_NAME" != "one-dev" ]]; then
    echo "ERROR: Running create-dev-user in non-dev environment! Exiting."
    exit 1
fi

cat <<EOF | python $DIR/manage.py shell
from zemauth.models import User
from django.contrib.auth.models import Group
import oauth2_provider.models

u = User.objects.create_superuser('test@test.com', 'test123')
u.groups.set(Group.objects.all())

sspd_u = User.objects.get_or_create_service_user('sspd')
sspd_u.groups.set(Group.objects.all())

oauth2_provider.models.Application.objects.get_or_create(
    client_id='GQ3eM9CBHabjaiCDsRh3Yro3srXzCqa4rUf1vYvQ',
    user=sspd_u,
    redirect_uris='http://localhost:8080/login',
    client_type='confidential',
    authorization_grant_type='authorization-code',
    client_secret='jTZis7Hx8yAhxelQQsqgzrUMEu2MKVtKfSM2oSrZdqYgpTrqZyREaIJOGOxJfCT81iLGoYU3eQBEhIR5m4Uogv5JPG7UXYDZ6Mdjf0mDewpNIX1M6Y5EsDqHgvyLyvKV',
    name='SSPDashboard',
    skip_authorization=False
)

oauth2_provider.models.Application.objects.get_or_create(
    client_id='2IR8uOePVExOw7qFp3ooNA0YxktiswFkoAq9EVXk',
    user=sspd_u,
    redirect_uris='',
    client_type='confidential',
    authorization_grant_type='client-credentials',
    client_secret='eX3PFlzP8hycjoMvBHwESCuL6WFxybWdK4S4seVVB65KehyXr4thBwih6Vv9mzAO5jZWQFAlvLZrzYuermhUDn2OBZqIudX6tf6XaUmJTguW68iC6Ey1XqcHCImMnFfq',
    name='SSPDashboard - api',
    skip_authorization=False
)
EOF
