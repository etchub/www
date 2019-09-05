"""
REST Web Service
"""

import flask
import requests
import random
import logging

log = logging.getLogger(__name__)
#logging.getLogger('sh').setLevel(logging.CRITICAL)

app = flask.Flask(__name__)
app.secret_key = ''.join(str(random.random())[2:] for i in range(5))
app.config['github_client_id'] = '9826ee3f2035ce2b3e40'
app.config['github_client_secret'] = '5d2f2b37e3b51c8f6e492cf638bb0d8a0b58a666'
app.config['files_path'] = '../files'

def error(title, description, url, code=500):
    return flask.render_template('error.html',
                                 title=title,
                                 description=description,
                                 url=url,
                                 code=code), code

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/upload', methods=['PUT'])
def upload():
    file_name = f"{str(random.random())[2:]}.sh"
    file_body = 'echo hello world'
    return '', 201

@app.route('/logout')
def logout():
    flask.session['user'] = None
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

    #FIXME: dev purpose
    #if flask.request.args.get('user'):
    #    flask.session['user'] = flask.request.args.get('user')

    if flask.session.get('user'):
        return flask.render_template('login.html',
                                     user=flask.session.get('user'))

    flask.session['last_state'] = ''.join(str(random.random())[2:] for i in range(5))
    auth_url = requests.Request('GET', 'https://github.com/login/oauth/authorize',
                                 params={'state': flask.session['last_state'],
                                         'scope': 'user:email',
                                         'client_id': app.config['github_client_id'],
                                         'redirect_uri': flask.url_for('login', _external=True)}).prepare().url
    return flask.redirect(auth_url)
