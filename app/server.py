# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

from __future__ import print_function

import logging

from flask import Flask
from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer

import app.async_wrapper
import app.cascade.database
from app import settings
from app.cascade import attack, runner


def configure_flask_logger():
    """
    Unfortunately there is a known issue using geventwebsocket.WebSocketHandler
    and the core logging module. This is a hack to still be able to see the flask logs.
    http://www.gevent.org/gevent.pywsgi.html#gevent.pywsgi.LoggingLogAdapter
    """
    flask_logger = logging.getLogger()
    flask_ch = logging.StreamHandler()
    flask_logger.setLevel(logging.INFO)
    flask_logger.addHandler(flask_ch)
    return flask_logger


logger = logging.getLogger(__name__)
url = None

flask_app = Flask('CASCADE', static_url_path='', static_folder='www')
WSGI_WEBSOCKET = "wsgi.websocket"


@flask_app.route("/", methods=['GET'])
def main_page():
    """" The main entrypoint for the client side application. """
    return flask_app.send_static_file('index.html')


def connect_to_database():
    # Connect to the database and update anything that needs to be
    # ASYNC should be started first
    app.async_wrapper.enable_async()
    app.cascade.database.connect()


def run_job_loop(debug=False):
    app.async_wrapper.enable_async()
    connect_to_database()
    runner.run(debug=debug)


def run_server(debug=False):
    global flask_app

    config = settings.load()
    attack.attack_url = config['links']['attack']
    attack.proxies = config['links']['proxies']

    interface = config['server']['interface']
    port = config['server']['port']
    threaded = True if debug else not app.async_wrapper.enable_async()

    flask_logger = configure_flask_logger()
    connect_to_database()

    # if not threaded and not debug:
    ssl_context = {}
    https = config['server']['https']
    if https['enabled']:
        ssl_context['certfile'] = https['certfile']
        ssl_context['keyfile'] = https['keyfile']

    flask_app.debug = debug

    print('Running CASCADE via WSGIServer on {url}'.format(url=config['server']['url']))
    wsgi = WSGIServer((interface, port), flask_app, log=flask_logger, handler_class=WebSocketHandler, **ssl_context)
    wsgi.serve_forever()
