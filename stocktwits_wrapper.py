from contextlib import closing
import html
import logging

from flask import abort, session
import requests

from lib.mysql_wrapper import MysqlWrapper
from lib.regexify import Regexify


class StockTwitsWrapper:
    """ ST api wrapper. not all endpoints require auth token. """

    mysql_conn = MysqlWrapper.get_connection()
    regexes = Regexify()

    bot_blacklist = [727510]

    @classmethod
    def get_ticker(self, ticker):
        """ https://stocktwits.com/developers/docs/api#streams-symbol-docs """

        oauth_token = session.get('access_token', '')

        request_url = self.__build_get_symbol_url(ticker)
        request_params = self.__build_get_symbol_params(oauth_token, '')
        response_json = self.__get_symbol(request_url, request_params)
        st_compliant_posts = []
        for message in response_json['messages']:
            # https://stocktwits.com/developers/docs/display_requirement
            st_compliant_posts.append(self.__build_st_compliant_post(message))

        # TODO: thread the above and below, they are unrelated.

        self.update_ticker(ticker, oauth_token)

        ticker_tuples = self.__query_ticker(ticker)
        result_set_list = []
        for ticker_tuple in ticker_tuples:
            result_set_list.append(
                dict(
                    text=ticker_tuple[0],
                    size=ticker_tuple[1]
                )
            )

        return GetTickerResponse(ticker, response_json['symbol']['title'], st_compliant_posts, result_set_list)

    @classmethod
    def update_ticker(self, ticker, oauth_token):
        """ update the ticker in the db """

        since_param = self.__get_pagination_param(ticker)

        # TODO: make a system account on ST and use for all automated calls.
        request_url = self.__build_get_symbol_url(ticker)
        request_params = self.__build_get_symbol_params(oauth_token, since_param)
        response_json = self.__get_symbol(request_url, request_params)
        all_messages = response_json['messages']

        if(len(all_messages) < 1):
            return

        # first message is the most recent
        last_message = all_messages[0]['id']
        self.__update_last_message(ticker, last_message)

        simple_messages = []
        for message in all_messages:
            if message["user"]["id"] in self.bot_blacklist:
                continue

            simple_message = self.regexes.regexify_message(
                html.unescape(message['body']).strip().upper(),
                ticker,
                response_json['symbol']['title'])
            if len(simple_message) > 1:
                simple_messages.append(simple_message)

        all_words = [(word) for message in simple_messages for word in message.split()]
        self.__update_word_frequencies(ticker, all_words)
        return

    @classmethod
    def __get_pagination_param(self, ticker):
        pagination_since = self.__get_last_message(ticker)
        since_param = str(pagination_since)
        if pagination_since == -1:
            since_param = ''

        return since_param

    @classmethod
    def __get_symbol(self, request_url, request_params):
        response = requests.get(request_url, params=request_params)
        response_json = response.json()

        # check rate headers from response. headers are strings.
        # http://stocktwits.com/developers/docs/rate_limiting
        # unauthenticated calls originate from the ec2 instance.
        # basically 200 unauthenticated calls an hour total for the site.
        rate_remaining = response.headers.get('X-RateLimit-Remaining')
        rate_reset = response.headers.get('X-RateLimit-Reset')
        session['rate_remaining'] = rate_remaining
        session['rate_reset'] = rate_reset  # returned in true UTC time

        logging.error('Response for: %s' % response_json['symbol']['symbol'])
        logging.error('Rate remaining: %s' % rate_remaining)
        logging.error('Access Token: %s' % session.get('access_token', 'Unauthenticated'))

        self.__check_response_code(response_json, rate_remaining)

        return response_json

    @classmethod
    def __build_get_symbol_url(self, ticker):
        return '%s%s%s' % ('https://api.stocktwits.com/api/2/streams/symbol/', ticker, '.json')

    @classmethod
    def __build_get_symbol_params(self, access_token_param, since_param):
        return dict(
            access_token=access_token_param,
            since=since_param
        )

    @classmethod
    def __build_st_compliant_post(self, message):
        """ stocktwits.com/developers/docs/display_requirement """
        body = html.unescape(message['body'])
        author = message['user']['username']
        timestamp = message['created_at']
        link_to_message = '%s%s%s%s' % ('https://www.stocktwits.com/', author, '/message/', message['id'])
        return STCompliantPost(author, body, timestamp, link_to_message)

    # TODO: alarm on these errors
    @classmethod
    def __check_response_code(self, response_json, rate_remaining):
        response_code = response_json['response']['status']
        if response_code != 200:
            logging.error('Response code: %s' % (response_code))
            if int(rate_remaining) <= 1:
                session['rate_limited'] = True
            if 'errors' in response_json:
                logging.error(response_json['errors'])

            abort(response_code)

    @classmethod
    def __get_last_message(self, ticker):
        self.__check_connection()
        with closing(self.mysql_conn.cursor()) as cursor:
            result_args = cursor.callproc('get_last_message', (ticker, 0))
            last_message = result_args[1]
            self.mysql_conn.commit()
            return last_message

    @classmethod
    def __query_ticker(self, ticker):
        self.__check_connection()
        with closing(self.mysql_conn.cursor()) as cursor:
            cursor.callproc('query_ticker', (ticker,))
            query_result = next(cursor.stored_results()).fetchall()
            self.mysql_conn.commit()
            return query_result

    @classmethod
    def __query_word(self, word):
        self.__check_connection()
        with closing(self.mysql_conn.cursor()) as cursor:
            cursor.callproc('query_word', (word,))
            query_result = next(cursor.stored_results()).fetchall()
            self.mysql_conn.commit()
            return query_result

    @classmethod
    def __update_word_frequencies(self, ticker, word_map):
        self.__check_connection()
        with closing(self.mysql_conn.cursor()) as cursor:
            for word in word_map:
                # TODO: benchmark this
                cursor.callproc('update_word_frequencies', (ticker, word, 1))
            self.mysql_conn.commit()

    @classmethod
    def __update_last_message(self, ticker, last_message):
        self.__check_connection()
        with closing(self.mysql_conn.cursor()) as cursor:
            cursor.callproc('update_last_message', (ticker, last_message))
            self.mysql_conn.commit()

    @classmethod
    def __check_connection(self):
        if not self.mysql_conn.is_connected():
            self.mysql_conn = MysqlWrapper.get_connection()


class GetTickerResponse:

    def __init__(self, symbol, co_name, posts, word_map):
        self.symbol = symbol
        self.co_name = co_name
        self.posts = posts
        self.word_map = word_map


class STCompliantPost:

    def __init__(self, author, body, timestamp, link_to_message):
        self.author = author
        self.body = body
        self.timestamp = timestamp
        self.link_to_message = link_to_message
