# Yield Curve

The project is separated into a `backend` (FastAPI + sqlite) and `frontend` (React + TS) directory

---

## Prerequisites

* Make sure `uv` is installed on your machine. On macOs: `brew install uv`
* Have `node v22` installed on your machine.
* Clone the project, navigating to its root.

---

## backend

* `cd backend`
* `uv run sync`
* To run in `dev`: `uv run fastapi dev app.py`

The project should be available locally at `localhost:8000`
OpenAPI can be seen at `localhost:8000/docs`

---

## frontend

* `cd frontend`
* Confirm `node -v` outputs node v22+
* `npm i`
* To run in `dev`: `npm run dev`
