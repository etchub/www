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
    flask.flash('Successfully signed out')
    #return flask.redirect(flask.url_for('login'))
    return flask.redirect(flask.url_for('index'))

@app.route('/login')
def login():
    # FIXME: github login to be tested
    referrer = flask.request.headers.get("Referer", '')
    code = flask.request.args.get('code')
    error = flask.request.args.get('error')
    if referrer.startswith('https://github.com'):
        if error:
            return flask.render_template('error.html',
                                         code=500,
                                         title=f"GitHub Authentication Error ({flask.request.args.get('error')})",
                                         description=f"{flask.request.args.get('error_description')} ({flask.request.args.get('error_uri')})",
                                         url=url_for('login'))
        if code:
            token = requests.post('https://github.com/login/oauth/access_token',
                                  data={'state': flask.session.get('last_state'),
                                        'client_id': app.config['github_client_id'],
                                        'client_secret': app.config['github_client_secret'],
                                        'code': code,
                                        'accept': 'application/json'}).json()

            user_emails = requests.get('/user/emails',
                                       headers={'Authorization:', f"token {token['access_token']}"}).json()
            user_email = [email for email in user_emails if email['primary']].pop()
            flask.flash('Logged in as {user_email}')
            flask.rediect(url_for('index'))
    elif False:
        return f"You are logged in as {flask.session.get('user')}"
    else:
        flask.session['last_state'] = ''.join(str(random.random())[2:] for i in range(5))
        auth_url = requests.Request('GET', 'https://github.com/login/oauth/authorize',
                                     params={'state': flask.session['last_state'],
                                             'scope': 'user:email',
                                             'client_id': app.config['github_client_id'],
                                             'redirect_uri': flask.url_for('login')}).prepare().url
        #FIXME:
        #flask.redirect(auth_url)
        #FIXME: dev purpose
        if flask.request.args.get('user'):
            flask.session['user'] = flask.request.args.get('user')
        return flask.render_template('login.html',
                                     user=flask.session.get('user'),
                                     redirect=auth_url)
