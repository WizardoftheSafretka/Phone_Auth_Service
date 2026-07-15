#!/bin/sh

echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done
echo "PostgreSQL started"

echo "Waiting for Redis..."
while ! nc -z $REDIS_HOST $REDIS_PORT; do
  sleep 1
done
echo "Redis started"

echo "Applying migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Creating superuser..."
python manage.py shell << PYTHON_EOF
from users.models import CustomUser
if not CustomUser.objects.filter(phone_number='+79999999999').exists():
    user = CustomUser.objects.create_superuser(
        phone_number='+79999999999',
        password='admin123'
    )
    user.is_verified = True
    user.save()
    print('Superuser created')
PYTHON_EOF

echo "Starting server..."
exec gunicorn --bind 0.0.0.0:8000 app.wsgi:application