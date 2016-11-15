from datetime import datetime
import logging
import os
import time

from flask import Flask, render_template, request, redirect, url_for, session, abort

from auth_wrapper import AuthWrapper
from lib.regexify import Regexify
from stocktwits_wrapper import StockTwitsWrapper


application = Flask(__name__)
app = application
app.secret_key = os.environ.get('APP_SECRET_KEY')

authwrapper = AuthWrapper()
stwrapper = StockTwitsWrapper()
regexes = Regexify()
regexes.compile_regex_patterns()


@app.route('/')
def home():
    check_session()
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


@app.route('/update/<url_ticker>/')
def update_ticker(url_ticker):
    ticker = url_ticker.upper().strip()
    tims_oauth_token = os.environ.get('ST_OAUTH_TOKEN')
    stwrapper.update_ticker(ticker, tims_oauth_token)
    return render_template('update_ticker.html', title=ticker)


@app.route('/about/')
def about():
    return render_template('about.html', title='About')


@app.route('/auth_redirect_uri/')
def auth_redirect_uri():
    exchange_code = request.args.get('code')

    logging.error('Exchange code: %s' % exchange_code)

    token_response = authwrapper.get_auth_token(exchange_code, request.url_root)

    session['access_token'] = token_response.access_token
    session['user_id'] = token_response.user_id
    session['username'] = token_response.username

    logging.error('Access token: %s' % session.get('access_token', 'None found?'))

    return redirect(request.url_root)   # go back home after successful auth


# TODO fix
# comment this out while developing on localhost.
@app.before_request
def check_session():
    if '/auth_redirect_uri/' != request.path:
        if 'user_id' not in session or 'access_token' not in session:
            auth_code_url = authwrapper.get_auth_code_url(request.url_root)

            logging.error('Redirecting to auth code url: %s' % auth_code_url)

            return redirect(auth_code_url)

    return None


# TODO: maybe move this off of all requests and have a query db only request if rate is up.
@app.before_request
def check_rate_reset():
    """ we must obey """

    local_time_now = time.time()
    utc_offset = (datetime.fromtimestamp(
        local_time_now) - datetime.utcfromtimestamp(local_time_now)).total_seconds()
    local_utc_time_now = float(datetime.utcnow().strftime("%s"))
    true_utc_time_now = local_utc_time_now + utc_offset

    utc_rate_reset = float(session.get('rate_reset', true_utc_time_now))

    # 1. check if we can reset the time left
    if true_utc_time_now >= utc_rate_reset:
        session['rate_limited'] = False

    # 2. check if rate limit has been reached
    if session.get('rate_limited', False):
        abort(429)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html', title='404'), 404


@app.errorhandler(429)
def rate_limit_reached(error):
    return render_template('rate_limit_reached.html', title='429'), 429


if __name__ == '__main__':
    # app.run(debug=True)
    app.run()
