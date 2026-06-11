# Deploying to PythonAnywhere (free tier)

The website is a plain WSGI app (`web.py` exposes `app`), so PythonAnywhere runs
it directly. These steps assume the GitHub repo is public; if it is private, use
a personal access token or an SSH key on the clone step.

## One-time setup

1. In a PythonAnywhere **Bash console**, clone the repo:

   ```
   git clone https://github.com/brianssparetime/BronicaHelicoidScaleMaker.git
   ```

2. Make a virtualenv and install the two runtime dependencies (Python 3.10 or
   newer):

   ```
   mkvirtualenv --python=/usr/bin/python3.10 bronica
   pip install -r BronicaHelicoidScaleMaker/requirements.txt
   ```

3. In the **Web** tab, add a new web app, accept the free
   `username.pythonanywhere.com` domain, and pick **Manual configuration** with
   the same Python version as the virtualenv.

4. On the web app's config page:
   - **Virtualenv**: enter `/home/<username>/.virtualenvs/bronica`.
   - **WSGI configuration file**: open it and replace the contents with the body
     of `deploy/pythonanywhere_wsgi.py`, substituting your username.
   - **Static files** (optional, faster): map URL `/static/` to directory
     `/home/<username>/BronicaHelicoidScaleMaker/static`.

5. Click **Reload**, then visit `username.pythonanywhere.com`.

## Updating after a change

```
cd BronicaHelicoidScaleMaker && git pull
```

Then **Reload** the web app. Run `pip install -r requirements.txt` again only if
the dependencies changed.

## Free-tier notes

- Generation streams in memory; the app writes nothing to disk, so it stays
  inside the 512 MB and 100 CPU-second-per-day limits with room to spare.
- PythonAnywhere disables a free web app periodically and emails a link to keep
  it running. Click it to extend.
