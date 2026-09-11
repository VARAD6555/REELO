# REELO

A marketplace where short-form video creators find and hire video editors.

This started as a single 1,800-line `index.html` with fake `localStorage`
"login" and hardcoded sample data. It's now a proper multi-page Flask app
with a real database backing authentication and the marketplace itself.

## What changed

- **Real pages, not one giant file.** Every screen (dashboard, profile,
  projects, payments, saved editors, messages, editor studio, login,
  register) is its own route + template, using Jinja layout inheritance
  (`base.html`) instead of one HTML file with JS show/hide panels.
- **Real authentication.** Accounts, sessions, and password hashing run
  through Flask-Login + Flask-SQLAlchemy + Werkzeug's `generate_password_hash`
  / `check_password_hash` (scrypt) — no plaintext passwords, no
  `localStorage.setItem('reeloUser', ...)`.
- **Real database.** `User`, `VideoSample`, `SavedEditor`, `Order`, `Payment`,
  and `Message` models replace the hardcoded HTML cards and tables. Hiring an
  editor actually creates an `Order` + `Payment` row; saving an editor writes
  a row; chat messages persist.
- **CSRF protection & form validation** via Flask-WTF on every POST
  (login, register, hire, save, send message, editor studio).
- **App-factory structure** (`create_app()`), blueprints (`auth`, `main`),
  environment-based config, and `flask db` migrations via Flask-Migrate —
  the standard layout for a Flask app you'd actually deploy.
- Visual design (the glassmorphism / Instagram-gradient look) is unchanged —
  same CSS, same layout, same interactions — just served from real pages
  instead of one file.

## Project structure

```
REELO/
├── wsgi.py                 # entry point (flask run / gunicorn "wsgi:app")
│                            # named wsgi.py, not app.py, to avoid colliding
│                            # with the app/ package (see comment in the file)
├── config.py               # Dev/Test/Prod config from environment variables
├── requirements.txt
├── .env.example             # copy to .env and fill in
├── app/
│   ├── __init__.py         # application factory
│   ├── extensions.py       # db, login_manager, migrate, csrf
│   ├── models.py           # User, VideoSample, SavedEditor, Order, Payment, Message
│   ├── forms.py             # Flask-WTF login/register forms
│   ├── cli.py                # `flask init-db` / `flask seed-db`
│   ├── auth/                 # login, register, logout
│   ├── main/                  # dashboard, profile, projects, payments, saved, messages, editor studio
│   ├── templates/
│   │   ├── base.html          # shared header/sidebar layout
│   │   ├── auth/               # login.html, register.html
│   │   └── main/                # one template per page
│   └── static/
│       ├── css/                # style.css (app), auth.css (login/register)
│       └── js/main.js           # modals + small UI widgets only
└── instance/                     # SQLite database lives here (gitignored)
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # set SECRET_KEY at minimum
flask seed-db                   # creates tables + demo accounts
flask run                       # or: python wsgi.py
```

Visit `http://127.0.0.1:5000`. Demo accounts (seeded, password
`password123`):

| Email                | Role    |
|-----------------------|---------|
| `alex@reelo.dev`      | editor  |
| `liam@reelo.dev`      | editor  |
| `creator@reelo.dev`   | creator |

## Database

Defaults to a local SQLite file at `instance/reelo.db`. To use Postgres/MySQL
in production, set `DATABASE_URL` in `.env`, e.g.:

```
DATABASE_URL=postgresql://user:password@localhost:5432/reelo
```

Schema changes going forward should go through Flask-Migrate:

```bash
flask db init      # once, if you want migrations instead of create_all
flask db migrate -m "describe the change"
flask db upgrade
```

## Notes for going further

- Payments are recorded, not actually processed — there's no real payment
  gateway wired in. `app/main/routes.py:hire()` is the place to integrate one
  (Razorpay/Stripe) and flip `Payment.status` from `deposit_held` to
  `paid_to_editor` on a webhook.
- Passwords need at least 8 characters (`app/forms.py`); tighten further if
  you need it.
- `SECRET_KEY` in `.env.example` is a placeholder — always set a real random
  value before deploying.
