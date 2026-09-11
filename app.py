"""Entry point for running the REELO Flask app locally.

For production, run with a WSGI server instead, e.g.:
    gunicorn "app:create_app()"
"""

import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", True))
