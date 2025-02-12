# BOLD Public Portal

## Infrastructure

- Docker
- NGINX
- Python: FastAPI and Socketserver Logger
- Redis and File System Cache
- Couchbase
- Barcode Core Data Model

Dependencies:
- Barcode Core Data Model repository
- SSL Certificates
- Maintenance job to clear File System Cache
  - `find /tmp/bold-public-portal/cache -type f -amin +1440 -delete`

## Local Deployment

Requirements:
- [Docker Desktop](https://docs.docker.com/desktop/)
- [Tilt](https://docs.tilt.dev/install.html)

```bash
REPO_DIR="bold-public-portal"

# Spool Up
cd $REPO_DIR
tilt up -f docker/Tiltfile

# Spool Down
cd $REPO_DIR
tilt down -f docker/Tiltfile

# Check Status
# Go to http://localhost:10350/overview
```

## Production Deployment

Check that `.env` is configured correctly and to production values. The following assumes the ansible playbook is not being used and Couchbase is hosted on a different server.

```bash
REPO_DIR="bold-public-portal"

# Spool Up
cd $REPO_DIR
docker build -t fastapi-app -f docker/Dockerfile .
docker build -t socketserver-logging -f docker/Dockerfile.socketserver_logging .
docker compose -f docker-compose-production.yml up -d

# Spool Down
cd $REPO_DIR
docker compose -f docker-compose-production.yml down

# Check Status
docker ps -a
```

Alternatively, if the use of screens are required instead of Docker containers:
```bash
systemctl start nginx
systemctl start redis

screen -S fastapi-app
cd $REPO_DIR/src
gunicorn main:app --workers 24 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000

screen -S socketserver-logging
cd $REPO_DIR/src
python socketserver_logging.py
```

## Testing

See `CYPRESS.md`

## Repository Structure

- `ansible`
  - Ansible playbooks and deployment
- `db_data`
  - Local simulated database data
- `docker`
  - Docker and Tilt components
- `src`
  - Main source code
  - `cypress`
    - Cypress testing configuration
  - `docs`
    - Additional documentation
  - `ETL`
    - Data (BCDM) extration, transformation and loading
  - `services`
    - API services; serves the application data but can also be used independently
  - `static`
    - Assets for application presentation
  - `templates`
    - Jinja2/HTML application layout
  - `tools`
    - Miscellaneous tools for the application
  - `views`
    - Application view controllers
