"""
REST Web Service
"""

import flask
import werkzeug
import requests
import sh
import glob
import random
import logging
import os

logging.getLogger('sh').setLevel(logging.CRITICAL)
log = logging.getLogger(__name__)

app = flask.Flask(__name__)
app.secret_key = ''.join(str(random.random())[2:] for i in range(5))
app.config['github_client_id'] = '9826ee3f2035ce2b3e40'
app.config['github_client_secret'] = '5d2f2b37e3b51c8f6e492cf638bb0d8a0b58a666'
app.config['files_path'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')

def error(title, description, url, code=500):
    return flask.render_template('error.html', title=title, description=description, url=url, code=code), code

@app.errorhandler(werkzeug.exceptions.HTTPException)
def handle_error(e):
    return error(title=e.name, description=e.description, url=None, code=e.code)

@app.route('/')
def index():
    files = [file[len(app.config['files_path'])+1:]
             for file in glob.glob(os.path.join(app.config['files_path'], '*', '*'))]
    return flask.render_template('index.html', files=files)

@app.route('/file/<path:name>')
def file(name):
    with open(os.path.join(app.config['files_path'], name)) as f:
        return f.read()

@app.route('/upload')
def upload():
    if not flask.session.get('user'):
        raise werkzeug.exceptions.Forbidden('Please sign in to upload.')
    return flask.render_template('upload.html')

@app.route('/upload', methods=['PUT'])
def api_upload():
    if not flask.session.get('user'):
        return 'Please provide a cookie for authentication', 403

    try:
        fileob = flask.request.files['data']
        sh.mkdir('-p', os.path.join(app.config['files_path'], flask.session['user']))
        filename_user = os.path.join(flask.session['user'], fileob.filename)
        filename_absolute = os.path.join(app.config['files_path'], filename_user)
        fileob.save(filename_absolute)
        log.info(f"Saved uploded file to {filename_absolute}")
    except Exception as e:
        try:
            return f"Failed uploading {filename_user} ({e.__class__.__name__}: {e})", 500
        except:
            return f"Upload failed ({e.__class__.__name__}: {e})", 500

    try:
        git = sh.git.bake(git_dir=os.path.join(app.config['files_path'], '.git'),
                          work_tree=app.config['files_path'])
        git.add(filename_absolute)
        try:
            git.commit(message=f"Added by {flask.session['user']}", porcelain=True)
        except sh.ErrorReturnCode_1:
            return f"Same file already exists: {filename_user}", 202
    except Exception as e:
        return f"Failed versioning file: {filename_user} ({e.__class__.__name__}: {e})", 500

    return f"Uploaded {fileob.filename}", 201

@app.route('/logout')
def logout():
    del flask.session['user']
    flask.flash('You signed out, see you !')
    #return flask.redirect(flask.url_for('login'))
    return flask.redirect(flask.url_for('index'))

@app.route('/login')
def login():
    def github_error(response):
        return error(title=f"GitHub Authentication Error", #: {response.get('error')}",
                     description=f"{response.get('error_description')}", #)({response.get('error_uri')})",
                     url=flask.url_for('login'),
                     code=500)

    #FIXME: dev purpose
    if flask.request.args.get('user'):
       flask.session['user'] = flask.request.args.get('user')

    if flask.session.get('user'):
        return flask.render_template('login.html',
                                     user=flask.session.get('user'))

    if flask.request.args.get('error'):
        return github_error(flask.request.args)

    if flask.request.args.get('code'):
        oauth = requests.post('https://github.com/login/oauth/access_token',
                              data={'state': flask.session.get('last_state'),
                                    'client_id': app.config['github_client_id'],
                                    'client_secret': app.config['github_client_secret'],
                                    'code': flask.request.args.get('code')},
                              headers={'Accept': 'application/json'}).json()
        if 'error' in oauth:
            return github_error(oauth)
        #user_emails = requests.get('https://api.github.com/user/emails',
        #                           headers={'Authorization': f"token {oauth['access_token']}"}).json()
        #user_email = [email for email in user_emails if email['primary']].pop()
        user = requests.get('https://api.github.com/user',
                            headers={'Authorization': f"token {oauth['access_token']}"}).json()

        flask.session['user'] = user['login']
        #flask.session['user_avatar'] = user['avatar_url']
        flask.flash(f"Logged in as {flask.session['user']}")
        return flask.redirect(flask.url_for('index'))

    flask.session['last_state'] = ''.join(str(random.random())[2:] for i in range(5))
    auth_url = requests.Request('GET', 'https://github.com/login/oauth/authorize',
                                 params={'state': flask.session['last_state'],
                                         'scope': 'user:email',
                                         'client_id': app.config['github_client_id'],
                                         'redirect_uri': flask.url_for('login', _external=True)}).prepare().url
    return flask.redirect(auth_url)
