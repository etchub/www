"""
Command-line Usage:
    python3 -m www
"""

from . import app
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s: %(message)s')
#logging.getLogger('werkzeug').setLevel(logging.ERROR)

app.run(
    host='0.0.0.0',
    port='5555', # 5000 is used by upnp on raspbian with xwindows
    debug=True,
    use_reloader=True)
