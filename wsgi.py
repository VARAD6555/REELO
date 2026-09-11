"""WSGI entry point for the REELO Flask app.

Named ``wsgi.py`` (not ``app.py``) on purpose: this project has an ``app/``
package, and a top-level ``app.py`` next to it creates an import-name
collision that Python resolves inconsistently across versions (the classic
"cannot import name 'create_app' from partially initialized module 'app'"
error). Keeping the entry point's filename distinct from the package name
avoids that entirely.

Run locally with:
    flask run
    # or: python wsgi.py

For production, run with a real WSGI server instead, e.g.:
    gunicorn "wsgi:app"
"""

import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", True))
