import logging
import os

from flask import Flask, render_template, request, redirect, url_for, session

from auth_wrapper import AuthWrapper
from stocktwits_wrapper import StockTwitsWrapper


application = Flask(__name__)
app = application
app.secret_key = os.environ.get('APP_SECRET_KEY')
# app.permanent_session_lifetime = timedelta(days=1)

stwrapper = StockTwitsWrapper()
stwrapper.compile_regex_patterns()
authwrapper = AuthWrapper()


@app.route('/')
def home():
    #     query = 'SELECT tickers.ticker, word_frequencies.word, word_frequencies.frequency \
    #              FROM word_frequencies \
    #              INNER JOIN tickers ON word_frequencies.ticker_id = tickers.id;'
    #
    #     cursor.execute(query)
    #     for (ticker, word, frequency) in cursor:
    #         logging.error('%s\t%s\t%s' % (ticker, word, frequency))
    #         print('%s\t%s\t%s' % (ticker, word, frequency))

    return render_template('home.html', title='WordTwits')


@app.route('/search/', methods=['POST'])
def get_ticker_from_search():
    ticker = request.form['ticker']
    return redirect(url_for('get_ticker_from_url', url_ticker=ticker))


@app.route('/<url_ticker>/')
def get_ticker_from_url(url_ticker):
    ticker = url_ticker.upper().strip()
    get_ticker_response = stwrapper.get_ticker(ticker)
    return render_template('ticker.html', title=ticker, get_ticker_response=get_ticker_response)


@app.route('/about/')
def about():
    return render_template('about.html', title='About')


@app.route('/auth_redirect_uri/')
def auth_redirect_uri():
    exchange_code = request.args.get('code')
    token_response = authwrapper.get_auth_token(exchange_code, request.url_root)

    session['access_token'] = token_response.access_token
    session['user_id'] = token_response.user_id
    session['username'] = token_response.username

    return redirect(request.url_root)   # go back home after successful auth


# Not using any ST endpoints that require auth yet
# @app.before_request
# def check_session():
#     session.permanent = True
    # comment out this block to develop locally
#     if '/auth_redirect_uri/' != request.path:
#         if 'user_id' not in session or 'access_token' not in session:
#             auth_code_url = authwrapper.get_auth_code_url(request.url_root)
#             return redirect(auth_code_url)
#
#     return None


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html', title='404'), 404


@app.errorhandler(429)
def rate_limit_reached(error):
    return render_template('rate_limit_reached.html', title='429'), 429


if __name__ == '__main__':
    app.run(debug=True)
    # app.run()
