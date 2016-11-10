import re
from stop_words import get_stop_words
from util.extended_stopwords import ExtendedStopWords


class Regexify(object):
    """ need to sift through all the garbage """

    @classmethod
    def compile_regex_patterns(self):
        """ strip out: cashtags, @s, links, and common words """

        stop_words = get_stop_words('english')

        # ST specific words and others that are of no value
        stop_words.extend(ExtendedStopWords.get_extended_stop_words())

        stop_words = r'\b%s\b' % r'\b|\b'.join(stop_words)
        stop_words = stop_words.replace("'", "")    # python blows at regex with ' for some reason

        # words not worth tracking
        self.stop_words_regex = re.compile(stop_words, re.IGNORECASE)

        # cashtags and @s
        self.st_regex = re.compile(r'(\$|@)\S+')

        # simple url regex
        self.link_regex = re.compile(r'(http|https):\/\/\S+', re.IGNORECASE)

        # everything but letters and space
        self.letter_only_regex = re.compile(r'[^A-Za-z ]')

        # company names can have numbers. everything but letters, numbers, and space.
        self.company_name_regex = re.compile(r'[^A-Za-z0-9 ]')

        # 1 char regex for anything left over
        self.one_word_regex = re.compile(r'\b\w{1}\b')

    @classmethod
    def regexify_message(self, message, ticker, co_name):
        """ apply different regexes """

        if len(message) < 2:
            return ''

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

        # 8. remove single characters left over
        simple_message = re.sub(self.one_word_regex, '', simple_message)

        return simple_message
