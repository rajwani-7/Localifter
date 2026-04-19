# LocaLifter

LocaLifter is a Flask-based service marketplace where customers can hire helpers and helpers can apply, get approved, and manage jobs from a dedicated portal.

## Stack

- Backend: Flask
- Frontend: HTML5 + Tailwind CSS + JavaScript
- Database: MySQL
- Auth: Flask session login with role-based routing

## Main Flows

- Become a Helper: application form, pending review, approval or rejection state, generated helper login credentials
- Want a Helper: customer signup, login, helper search, profile view, booking, review, rebook
- Admin Panel: helper approval, suspension, deletion, customer visibility, booking and revenue summary

## Run Locally

1. Install dependencies.
2. Set `DATABASE_URL` to a MySQL connection string or use the default MySQL URL in `app/__init__.py`.
3. Create the database and run `database/schema.sql`.
4. Start the app with `python app.py`.

## Deploy On Render

This repo includes `render.yaml` for one-click blueprint deployment.

1. Push this project to GitHub.
2. In Render dashboard, click `New` -> `Blueprint`.
3. Select your repository (`rajwani-7/Localifter`).
4. Render will create:
	 - Web service: `localifter-web`
	 - Postgres database: `localifter-db`
5. Click `Apply` and wait for build/deploy.
6. Open the deployed URL.

### Notes for Render

- Start command is `gunicorn app:app`.
- `SECRET_KEY` is generated automatically.
- `DATABASE_URL` is injected automatically from Render Postgres.
- Default admin login remains:
	- Username: `admin`
	- Password: `admin`

## Default Admin

- Username: `admin`
- Password: `admin`

## Notes

- Profile photo and ID proof uploads are stored under `app/static/uploads`.
- Helper approvals generate a helper login ID and temporary password for the dashboard.
