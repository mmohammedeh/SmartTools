import logging

import requests
from bs4 import BeautifulSoup as bs
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# This file is used for the various api calls used through out all of my code
# The class makes a session that will handle api calls so it can keep the authorization

# Logging code
logging.basicConfig(filename='session log.log', level=logging.DEBUG)

# These are the urls for live/stage
live = ''
stage = ''

# Change sd_type so we can test on stage instead of live
sd_type = live


########################################################################################################################
# Session calls
def get(session, **kwargs):
    api = kwargs['api']
    try:
        data = kwargs['data']
    except KeyError:
        data = None
    url = sd_type + api
    r = session.get(url, data=data)
    return r


def post(session, **kwargs):
    api = kwargs['api']
    try:
        data = kwargs['data']
    except KeyError:
        data = None
    try:
        files = kwargs['files']
    except KeyError:
        files = None
    url = sd_type + api
    r = session.post(url, data=data, files=files)
    return r

def put(session, **kwargs):
    api = kwargs['api']
    try:
        data = kwargs['data']
    except KeyError:
        data = None
    try:
        files = kwargs['files']
    except KeyError:
        files = None
    try:
        json_input = kwargs['json']
    except KeyError:
        json_input = None
    url = sd_type + api
    r = session.put(url, data=data, files=files, json=json_input)
    return r


def delete(session, **kwargs):
    api = kwargs['api']
    url = sd_type + api
    r = session.delete(url)
    return r


########################################################################################################################
# Logging in/out SD
def login():
    # Creating the session
    session_sd = requests.Session()
    retry = Retry(total=60, connect=60, read=3, redirect=3, status=3, status_forcelist=None, backoff_factor=0.2,
                  raise_on_redirect=True, raise_on_status=True)
    retry.BACKOFF_MAX = 60  # maximum time between requests in seconds
    adapter = HTTPAdapter(max_retries=retry)
    session_sd.mount('http://', adapter)
    session_sd.mount('https://', adapter)
    r = post(session_sd, api='/api2/login', data={'Username': '', 'Password': '', 'returnUrl': '/#/',
                                               'zendeskReturnTo': ''})
    return session_sd, r


def logout(session):
    resp = get(api='/api2/logoff')
    session.close()
    return resp


########################################################################################################################
# Updating program
def update_program_check():
    # all this really does is talk to github and see if the version number online is different from the one in the app
    # the app launches the installer after it's downloaded and quits out of the app so files can be overwritten
    # there is definitely better ways to do this since its downloading ~150 mb every time instead of just updating
    # small parts of the app
    session_git = requests.Session()
    USER = ''
    PASSWORD = ''
    # The weird way to get github token
    req = session_git.get('').text
    html = bs(req, features="lxml")
    token = html.find("input", {"name": "authenticity_token"}).attrs['value']
    com_val = html.find("input", {"name": "commit"}).attrs['value']
    login_data = {'login': USER,
                  'password': PASSWORD,
                  'commit': com_val,
                  'authenticity_token': token}
    r_auth = session_git.post('', data=login_data)
    r_online_version = session_git.get('')
    online_version = r_online_version.content.decode("utf-8").replace('\n', '')
    return session_git, online_version


## total (int) –
# Total number of retries to allow. Takes precedence over other counts.
#
# Set to None to remove this constraint and fall back on other counts. It’s a good idea to set this to some
# sensibly-high value to account for unexpected edge cases and avoid infinite retry loops.
#
# Set to 0 to fail on the first retry.
#
# Set to False to disable and imply raise_on_redirect=False.
#
## connect (int) –
# How many connection-related errors to retry on.
#
# These are errors raised before the request is sent to the remote server, which we assume
# has not triggered the server to process the request.
#
# Set to 0 to fail on the first retry of this type.
#
## read (int) –
# How many times to retry on read errors.
#
# These errors are raised after the request was sent to the server, so the request may have side-effects.
#
# Set to 0 to fail on the first retry of this type.
#
## redirect (int) –
# How many redirects to perform. Limit this to avoid infinite redirect loops.
#
# A redirect is a HTTP response with a status code 301, 302, 303, 307 or 308.
#
# Set to 0 to fail on the first retry of this type.
#
# Set to False to disable and imply raise_on_redirect=False.
#
## status (int) –
# How many times to retry on bad status codes.
#
# These are retries made on responses, where status code matches status_forcelist.
#
# Set to 0 to fail on the first retry of this type.
#
## method_whitelist (iterable) –
# Set of uppercased HTTP method verbs that we should retry on.
#
# By default, we only retry on methods which are considered to be idempotent (multiple requests
# with the same parameters end with the same state). See Retry.DEFAULT_METHOD_WHITELIST.
#
# Set to a False value to retry on any verb.
#
## status_forcelist (iterable) –
# A set of integer HTTP status codes that we should force a retry on. A retry is initiated if
# the request method is in method_whitelist and the response status code is in status_forcelist.
#
# By default, this is disabled with None.
#
## backoff_factor (float) –
# A backoff factor to apply between attempts after the second try (most errors are
# resolved immediately by a second try without a delay). urllib3 will sleep for:
#
# {backoff factor} * (2 ** ({number of total retries} - 1))
# seconds. If the backoff_factor is 0.1, then sleep() will sleep for [0.0s, 0.2s, 0.4s, …]
# between retries. It will never be longer than Retry.BACKOFF_MAX.
#
# By default, backoff is disabled (set to 0).
#
## raise_on_redirect (bool) –
#
# Whether, if the number of redirects is exhausted, to raise a MaxRetryError, or
# to return a response with a response code in the 3xx range.
#
## raise_on_status (bool) –
#
# Similar meaning to raise_on_redirect: whether we should raise an exception, or
# return a response, if status falls in status_forcelist range and retries have been exhausted.
#
## history (tuple) –
#
# The history of the request encountered during each call to increment().
# The list is in the order the requests occurred. Each list item is of class RequestHistory.
#
## respect_retry_after_header (bool) –

# Whether to respect Retry-After header on status codes defined as Retry.RETRY_AFTER_STATUS_CODES or not.
#
## remove_headers_on_redirect (iterable) –
#
# Sequence of headers to remove from the request when a response indicating a
# redirect is returned before firing off the redirected request.