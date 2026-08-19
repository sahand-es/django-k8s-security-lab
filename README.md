# Django Kubernetes Security Lab

Reusable training material for Django backend security and Kubernetes-oriented CTF practice.

## Sections

1. `presentation.html` and `presentation-*.md` contain the slide deck and speaker support material.
2. `manage.py`, `security_lab/`, `demos/`, `templates/`, and `demo_files/` contain the guided Django demos.
3. `challenge_1/` and `challenge_2/` contain standalone whitebox challenges.
4. `CTF/` contains the Kubernetes blackbox CTF stack.

## Run the guided demos

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/part1/`.

## Run the standalone challenges

```bash
docker compose up --build
```

The root compose file starts:

- Challenge 1 on `http://127.0.0.1:8001`
- Challenge 2 on `http://127.0.0.1:8002`

Override flags and ports with environment variables:

```bash
C1_PORT=9001 C2_PORT=9002 \
C1_FLAGS='FLAG{one},FLAG{two},FLAG{three}' \
C2_FLAGS='FLAG{one},FLAG{two}' \
docker compose up --build
```

## Run the Kubernetes CTF

See `CTF/SETUP.md` for the kind, Traefik, image build, deployment, verification, and teardown workflow.

The default local hostname is `ctf.localhost`. Override it by changing `CTF_HOST`-related values in `CTF/docker-compose.yml`, `CTF/k8s/backend/configmap.yaml`, and `CTF/k8s/backend/ingress.yaml`.

## Repository Hygiene

This repository should contain source, manifests, and authored training material only. Local databases, virtual environments, generated archives, compiled Python output, uploaded demo files, and static build output are ignored.
