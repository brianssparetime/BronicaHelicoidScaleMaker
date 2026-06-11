# Reference for the PythonAnywhere WSGI configuration file.
#
# On PythonAnywhere the real file lives at
#   /var/www/<username>_pythonanywhere_com_wsgi.py
# and is edited through the Web tab, not from this repo. Copy the body below
# into it, replacing <username> with your account name. The web worker's working
# directory is not the project root, so the path is added explicitly.

import sys

PROJECT_DIR = "/home/<username>/BronicaHelicoidScaleMaker"
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from web import app as application  # noqa: E402
