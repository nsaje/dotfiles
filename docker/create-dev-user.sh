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
u = User.objects.create_superuser('test@test.com', 'test123')
u.groups.set(Group.objects.all())
EOF
