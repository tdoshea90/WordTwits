from datetime import datetime
import os
import re
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

ticker_regex = re.compile(r'^[A-Za-z0-9_.]{1,5}$')
reverselookup_regex = re.compile(r'^[A-Za-z]{2,64}$')


@app.route('/')
def home():
    return render_template('home.html', title='WordTwits')


@app.route('/search/', methods=['POST'])
def get_ticker_from_search():
    ticker = request.form['ticker']
    return redirect(url_for('get_ticker_from_url', url_ticker=ticker))


@app.route('/<url_ticker>/')
def get_ticker_from_url(url_ticker):
    if not ticker_regex.match(url_ticker):
        abort(404)
    ticker = url_ticker.upper().strip()
    get_ticker_response = stwrapper.get_ticker(ticker)
    return render_template('ticker.html', title=ticker, get_ticker_response=get_ticker_response)


@app.route('/reverselookup/', methods=['POST'])
def reverse_lookup_from_search():
    word = request.form['word']
    return redirect(url_for('reverse_lookup_from_url', url_reverselookup=word))


@app.route('/reverselookup/<url_reverselookup>/')
def reverse_lookup_from_url(url_reverselookup):
    if not reverselookup_regex.match(url_reverselookup):
        abort(404)
    word = url_reverselookup.upper().strip()
    reverselookup_response = stwrapper.get_reverselookup(word)
    return render_template('reverselookup.html', title=word, reverselookup_response=reverselookup_response)


@app.route('/update/<url_ticker>/')
def update_ticker(url_ticker):
    if not ticker_regex.match(url_ticker):
        abort(404)
    ticker = url_ticker.upper().strip()
    # TODO: make a system account on ST and use for all automated calls.
    # new app secret keys will kill session and create new token
    tims_oauth_token = os.environ.get('ST_OAUTH_TOKEN')
    stwrapper.update_ticker(ticker, tims_oauth_token)
    return render_template('update_ticker.html', title=ticker)


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


# comment this out while developing on localhost.
@app.before_request
def check_session():
    if 'auth_redirect_uri' != request.endpoint and 'update_ticker' != request.endpoint:
        if 'user_id' not in session or 'access_token' not in session:
            auth_code_url = authwrapper.get_auth_code_url(request.url_root)
            return redirect(auth_code_url)

    return None


@app.before_request
def check_rate_reset():
    """ we must obey """
    # TODO: maybe move this off of all requests?

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


@app.errorhandler(400)
def no_app_access(error):
    return render_template('no_app_access.html', title='400'), 400


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html', title='404'), 404


@app.errorhandler(429)
def rate_limit_reached(error):
    return render_template('rate_limit_reached.html', title='429'), 429


if __name__ == '__main__':
    # app.run(debug=True)
    app.run()
