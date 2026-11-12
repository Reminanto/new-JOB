# Job Application Tracker and Analytics System

A beginner-friendly web application built using Python, Flask, SQLite, HTML, Bootstrap, and CSS.

## Features

- User registration and login
- Secure password hashing
- Individual user accounts and private application records
- Add, view, edit, search, filter, and delete job applications
- Track Applied, Assessment, Interview, Selected, Rejected, and On Hold statuses
- Dashboard with totals and status analytics
- Add and view upcoming follow-up reminders
- SQLite database created automatically

## Requirements

- Python 3.9 or newer
- Internet connection for the Bootstrap CDN on the web pages

## Installation

1. Extract the ZIP file.
2. Open a terminal inside the `Job_Application_Tracker` folder.
3. Create a virtual environment (recommended):

   ```bash
   python -m venv venv
   ```

4. Activate it on Windows:

   ```bash
   venv\Scripts\activate
   ```

   On macOS/Linux:

   ```bash
   source venv/bin/activate
   ```

5. Install Flask:

   ```bash
   python -m pip install -r requirements.txt
   ```

## Run the project

```bash
python app.py
```

Open this address in your browser:

`http://127.0.0.1:5000`

Register a new account, log in, and add your first job application.

## Database

The `jobs.db` SQLite database is created automatically the first time the app runs. It contains:

- `users`
- `applications`
- `followups`

Do not delete `jobs.db` if you want to keep your saved records.

## Important security note

This is a local learning/portfolio project. Before deploying it publicly:
- Set a long, random `app.secret_key` using an environment variable.
- Turn off Flask debug mode.
- Add CSRF protection and production-grade deployment settings.
- Use HTTPS and review database backup and access controls.

## Main files

- `app.py` — Flask routes, login, application management, dashboard
- `database.py` — SQLite connection and table creation
- `templates/` — HTML pages
- `static/style.css` — custom styling
