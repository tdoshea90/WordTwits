import os
import urllib.parse

import requests


class AuthWrapper:
    """ deals with oauth from ST """

    client_id = '7cc80ecf361d0f13'
    auth_redirect_postfix = 'auth_redirect_uri/'
    # uncomment along with other 2 lines for local oauth testing
    #bs_auth_redirect_url = 'https://stocktwitsanalyzer-env.us-west-2.elasticbeanstalk.com/'

    @classmethod
    def get_auth_code_url(self, auth_redirect_root):
        """ step 1 """

        auth_code_params = dict(
            response_type='code',
            redirect_uri=auth_redirect_root + self.auth_redirect_postfix,
            #redirect_uri=self.bs_auth_redirect_url + self.auth_redirect_postfix,
            client_id=self.client_id,
            scope='read'
        )

        auth_code_url = 'https://api.stocktwits.com/api/2/oauth/authorize?'
        url_params = urllib.parse.urlencode(auth_code_params)
        return auth_code_url + url_params

    @classmethod
    def get_auth_token(self, auth_code, auth_redirect_root):
        """ step 2 """

        auth_token_params = dict(
            code=auth_code,
            redirect_uri=auth_redirect_root,
            #redirect_uri=self.bs_auth_redirect_url + self.auth_redirect_postfix,
            client_id=self.client_id,
            client_secret=os.environ.get('ST_API_KEY'),
            grant_type='authorization_code'
        )

        auth_token_url = 'https://api.stocktwits.com/api/2/oauth/token'
        auth_token_response = requests.post(url=auth_token_url, data=auth_token_params)
        auth_token_json = auth_token_response.json()

        access_token = auth_token_json['access_token']
        user_id = auth_token_json['user_id']
        username = auth_token_json['username']

        return TokenResponse(access_token, user_id, username)


class TokenResponse:

    def __init__(self, access_token, user_id, username):
        self.access_token = access_token
        self.user_id = user_id
        self.username = username
