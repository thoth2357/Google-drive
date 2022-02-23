import functools
import os

import flask
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv

from authlib.integrations.requests_client import OAuth2Session
import google.oauth2.credentials
import googleapiclient.discovery

load_dotenv(override=True)

ACCESS_TOKEN_URI = 'https://www.googleapis.com/oauth2/v4/token'
AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/v2/auth?access_type=offline&prompt=consent'
AUTHORIZATION_SCOPE ='openid email profile https://www.googleapis.com/auth/drive'
AUTH_REDIRECT_URI = os.environ.get("FN_AUTH_REDIRECT_URI", default=False)
BASE_URI = os.getenv("FN_BASE_URI")
AUTH_TOKEN_KEY = 'auth_token'
AUTH_STATE_KEY = 'auth_state'


app = flask.Blueprint('drive_google_auth', __name__)
CORS(app)

def is_logged_in():
    return True if AUTH_TOKEN_KEY in flask.session else False

def get_user_info(token):
    credentials = build_credentials(token)
    oauth2_client = googleapiclient.discovery.build(
                        'oauth2', 'v2',
                        credentials=credentials)
    return oauth2_client.userinfo().get().execute()

def build_credentials(token):
    # if not is_logged_in():
    #     raise Exception('User must be logged in')

    # oauth2_tokens = flask.session[AUTH_TOKEN_KEY]
    
    return google.oauth2.credentials.Credentials(
                token,
                refresh_token=token,
                client_id=flask.session['CLIENT_ID'],
                client_secret=flask.session['CLIENT_SECRET'],
                token_uri=ACCESS_TOKEN_URI)


def no_cache(view):
    @functools.wraps(view)
    def no_cache_impl(*args, **kwargs):
        response = flask.make_response(view(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return functools.update_wrapper(no_cache_impl, view)

@app.route('/api/login')
@no_cache
@cross_origin()
def login():
    # BASE_URI = flask.request.args.get('base')
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')  # Todo make the client id and secret a env variable.
    # CLIENT_ID = flask.request.args.get('id')
    # CLIENT_SECRET = flask.request.args.get('secret')
    session = OAuth2Session(CLIENT_ID, CLIENT_SECRET,
                            scope=AUTHORIZATION_SCOPE,
                            redirect_uri=AUTH_REDIRECT_URI)
  
    flask.session['CLIENT_ID'] = CLIENT_ID
    flask.session['CLIENT_SECRET'] = CLIENT_SECRET
    flask.session['BASE_URI'] = BASE_URI
    uri, state = session.create_authorization_url(AUTHORIZATION_URL)
    flask.session[AUTH_STATE_KEY] = state
    flask.session.permanent = True

    return flask.redirect(uri, code=302)

@app.route('/hordanso-google/auth')
@cross_origin()
@no_cache
def google_auth_redirect():

    try:
        req_state = flask.request.args.get('state', default=None, type=None)
        if req_state != flask.session[AUTH_STATE_KEY]:
            response = flask.make_response('Invalid state parameter', 401)
            return response
        
        session = OAuth2Session(flask.session['CLIENT_ID'],flask.session['CLIENT_SECRET'],
                                scope=AUTHORIZATION_SCOPE,
                                state=flask.session[AUTH_STATE_KEY],
                                redirect_uri=AUTH_REDIRECT_URI)

        oauth2_tokens = session.fetch_access_token(
                            ACCESS_TOKEN_URI,            
                            authorization_response=flask.request.url)

        flask.session[AUTH_TOKEN_KEY] = oauth2_tokens
    except KeyError:
        return "Login state not found"
    url_token = f'{flask.session["BASE_URI"]}/?token={oauth2_tokens["refresh_token"]}'
    return flask.redirect(url_token, code=302)

@app.route('/api/logout')
@no_cache
@cross_origin()
def logout():
    flask.session.pop(AUTH_TOKEN_KEY, None)
    flask.session.pop(AUTH_STATE_KEY, None)

    return flask.redirect(flask.session["BASE_URI"], code=302)