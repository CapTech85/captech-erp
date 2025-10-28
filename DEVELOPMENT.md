# DEVELOPMENT
## Setup
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r dev-requirements.txt

## Run server
python manage.py migrate
python manage.py runserver

## Redis for dev
docker run -d --name redis-dev -p 6379:6379 redis:7
python manage.py rqworker default

## Create sample data
python manage.py create_sample_data

## Tests
pytest -q

## Dark mode
click the sun/moon icon in header to toggle
