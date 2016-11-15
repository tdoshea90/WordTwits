import logging
import os
import urllib.parse
from flask import abort
import requests


class AuthWrapper:
    """ deals with oauth from ST """

    client_id = '7cc80ecf361d0f13'
    auth_redirect_postfix = 'auth_redirect_uri/'

    @classmethod
    def get_auth_code_url(self, auth_redirect_root):
        """ step 1 """

        auth_code_params = dict(
            response_type='code',
            redirect_uri=auth_redirect_root + self.auth_redirect_postfix,
            client_id=self.client_id,
            scope='read'
        )

        url_params = urllib.parse.urlencode(auth_code_params)
        return '%s%s' % ('https://api.stocktwits.com/api/2/oauth/authorize?', url_params)

    @classmethod
    def get_auth_token(self, auth_code, auth_redirect_root):
        """ step 2 """

        auth_token_params = dict(
            code=auth_code,
            redirect_uri=auth_redirect_root,
            client_id=self.client_id,
            client_secret=os.environ.get('ST_API_KEY'),
            grant_type='authorization_code'
        )

        auth_token_url = 'https://api.stocktwits.com/api/2/oauth/token'
        auth_token_response = requests.post(url=auth_token_url, data=auth_token_params)
        auth_token_json = auth_token_response.json()

        self.__check_response_code(auth_token_json)

        access_token = auth_token_json['access_token']
        user_id = auth_token_json['user_id']
        username = auth_token_json['username']

        logging.error('New oauth token: %s' % access_token)

        return TokenResponse(access_token, user_id, username)

    @classmethod
    def __check_response_code(self, response_json):
        response_code = response_json['response']['status']
        if response_code != 200:
            logging.error('Response code: %s' % (response_code))
            if 'errors' in response_json:
                logging.error(response_json['errors'])

            abort(response_code)


class TokenResponse:

    def __init__(self, access_token, user_id, username):
        self.access_token = access_token
        self.user_id = user_id
        self.username = username
