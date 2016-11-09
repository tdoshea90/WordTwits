from contextlib import closing
from datetime import datetime
import html
import logging
import os
import re
import time

from flask import abort, session
import requests
from stop_words import get_stop_words

from lib.mysql_wrapper import MysqlWrapper


class StockTwitsWrapper:
    """ ST api wrapper. not all endpoints require auth token. """

    mysql_conn = MysqlWrapper.get_connection()

    oauth_token = os.environ.get('ST_OAUTH_TOKEN')

    bot_blacklist = [727510]

    @classmethod
    def compile_regex_patterns(self):
        """ strip out: cashtags, @s, links, and common words """

        stop_words = get_stop_words('english')

        # append ST specific stop words
        stop_words.extend(['company', 'stocks?', 'will', 'just'])

        stop_words = r'\b%s\b' % r'\b|\b'.join(stop_words)
        stop_words = stop_words.replace("'", "")    # python blows at regex with ' for some reason

        # common words not worth tracking
        self.stop_words_regex = re.compile(stop_words, re.IGNORECASE)

        # cashtags and @s
        self.st_regex = re.compile(r'(\$|@)\S+')

        # simple url regex
        self.link_regex = re.compile(r'(http|https):\/\/\S+', re.IGNORECASE)

        # everything but letters and space
        self.letter_only_regex = re.compile(r'[^A-Za-z ]')

        # company names can have numbers. everything but letters, numbers, and space
        self.company_name_regex = re.compile(r'[^A-Za-z0-9 ]')

    @classmethod
    def get_ticker(self, ticker):
        """ https://stocktwits.com/developers/docs/api#streams-symbol-docs """

        self.__check_rate_reset()

        get_ticker_url = 'https://api.stocktwits.com/api/2/streams/symbol/'
        url_postfix = '.json?'
        pagination_since = self.__get_last_message(ticker)

        logging.warning('Ticker: %s. Last message: %s' % (ticker, pagination_since))

        # TODO: use visitors token for watchlist, etc.
        # only time we don't have access_token is on localhost so kind of an unnecessary check
        # if 'access_token' in session:
        # url_postfix = '%s&access_token=%s' % (url_postfix, session['access_token'])

        # TODO: make a system account on ST
        # use my token for all automated calls
        url_postfix = '%s&access_token=%s' % (url_postfix, self.oauth_token)

        # TODO: only messages 'since' show up, use visitors token and get last 30 messages.
        if pagination_since != -1:
            url_postfix = '%s&since=%s' % (url_postfix, str(pagination_since))

        # call ST api
        request_url = '%s%s%s' % (get_ticker_url, ticker, url_postfix)

        response = requests.get(request_url)
        response_json = response.json()

        # check rate headers from response. headers are strings.
        rate_remaining = response.headers.get('X-RateLimit-Remaining')
        rate_reset = response.headers.get('X-RateLimit-Reset')
        session['rate_remaining'] = rate_remaining
        session['rate_reset'] = rate_reset  # returned in true UTC time

        self.__check_response_code(response_json, rate_remaining)

        symbol = response_json['symbol']['symbol']
        co_name = response_json['symbol']['title']

        st_compliant_posts = []
        simple_messages = []

        # first message is the most recent
        if(len(response_json['messages']) > 0):
            logging.warning('New last message: %s' % (response_json['messages'][0]['id']))
            last_message = response_json['messages'][0]['id']
            self.__update_last_message(ticker, last_message)

        for message in response_json['messages']:

            # 1. https://stocktwits.com/developers/docs/display_requirement
            st_compliant_posts.append(self.__build_st_compliant_post(message))

            if message["user"]["id"] in self.bot_blacklist:
                continue

            # 2. simple message
            simple_message = self.__regexify_message(html.unescape(message['body']).strip().upper(), ticker, co_name)
            if len(simple_message) > 1:
                simple_messages.append(simple_message)

        word_map = self.__build_word_map(simple_messages)

        self.__update_word_frequencies(ticker, word_map)

        # TODO: retrieve ticker words from db
        ticker_tuples = self.__query_ticker(ticker)
        #word_freq_map = dict((word, freq) for word, freq in ticker_tuples)
        # print(word_freq_map)

        return GetTickerResponse(rate_remaining, rate_reset, symbol, co_name, st_compliant_posts, word_map)

    @classmethod
    def __build_st_compliant_post(self, message):
        """ stocktwits.com/developers/docs/display_requirement """
        body = html.unescape(message['body'])
        author = message['user']['username']
        timestamp = message['created_at']
        link_to_message = '%s%s%s%s' % ('https://www.stocktwits.com/', author, '/message/', message['id'])
        return STCompliantPost(author, body, timestamp, link_to_message)

    @classmethod
    def __build_word_map(self, simple_messages):
        """ do word mapping """

        # TODO: move word frequency mapping into javascript maybe? how much?

        all_words = [(word) for message in simple_messages for word in message.split()]

        # http://www.artima.com/weblogs/viewpost.jsp?thread=98196
        word_map = {}
        for word in all_words:
            if(len(word) > 1):
                frequency = word_map.get(word, 0)
                word_map[word] = frequency + 1

        return word_map

    @classmethod
    def __regexify_message(self, message, ticker, co_name):
        """ apply different regexes """

        # 1. possessive words. message is already uppered.
        simple_message = message.replace("'S", "")

        # 2. remove links first
        simple_message = re.sub(self.link_regex, '', simple_message)

        # 3. remove cashtags and @s
        simple_message = re.sub(self.st_regex, '', simple_message)

        # 4. remove all special characters
        simple_message = re.sub(self.letter_only_regex, '', simple_message)

        # 5. remove common words
        simple_message = re.sub(self.stop_words_regex, '', simple_message)

        # 6. remove the actual ticker but without cashtag
        ticker_string = r'%s%s%s' % (r'\b', ticker, r'\b')
        ticker_pattern_regex = re.compile(ticker_string, re.IGNORECASE)
        simple_message = re.sub(ticker_pattern_regex, '', simple_message)

        # 7. remove company name like 'amazon' or 'apple'
        co_name_string = re.sub(self.company_name_regex, ' ', co_name)
        co_name_split = co_name_string.split()
        co_name_string_joined = r'\b%s\b' % r'\b|\b'.join(co_name_split)
        co_name_regex = re.compile(co_name_string_joined, re.IGNORECASE)
        simple_message = re.sub(co_name_regex, '', simple_message)

        return simple_message

    @classmethod
    def __check_rate_reset(self):
        """ we must obey """

        local_time_now = time.time()
        utc_offset = (datetime.fromtimestamp(
            local_time_now) - datetime.utcfromtimestamp(local_time_now)).total_seconds()
        local_utc_time_now = float(datetime.utcnow().strftime("%s"))
        true_utc_time_now = local_utc_time_now + utc_offset
        utc_rate_reset = float(session.get('rate_reset', true_utc_time_now))

        # 1. check if rate limit reset is up
        if true_utc_time_now >= utc_rate_reset:
            session['rate_limited'] = False

        # 2. check if rate limit has been reached
        if session.get('rate_limited', False):
            abort(429)

    @classmethod
    def __check_response_code(self, response_json, rate_remaining):
        """ check ST did not give us an error """

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
        with closing(self.mysql_conn.cursor()) as cursor:
            result_args = cursor.callproc('get_last_message', (ticker, 0))
            return result_args[1]

    @classmethod
    def __query_ticker(self, ticker):
        with closing(self.mysql_conn.cursor()) as cursor:
            cursor.callproc('query_ticker', (ticker,))
            query_result = next(cursor.stored_results())
            return query_result.fetchall()

    @classmethod
    def __update_word_frequencies(self, ticker, word_map):
        with closing(self.mysql_conn.cursor()) as cursor:
            for word in word_map:
                cursor.callproc('update_word_frequencies', (ticker, word, word_map[word]))
            self.mysql_conn.commit()

    @classmethod
    def __update_last_message(self, ticker, last_message):
        with closing(self.mysql_conn.cursor()) as cursor:
            cursor.callproc('update_last_message', (ticker, last_message))
            self.mysql_conn.commit()


class GetTickerResponse:

    def __init__(self, rate_remaining, rate_reset, symbol, co_name, posts, word_map):
        self.rate_remaining = rate_remaining
        self.rate_reset = rate_reset
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
