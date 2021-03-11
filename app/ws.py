# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

from flask import request

from app.server import flask_app, WSGI_WEBSOCKET
from app.cascade.session import Session


@flask_app.route('/api/ws/session/<session_id>', methods=['GET', 'POST'])
def session_stream(session_id):
    """
    Session specific notification stream
    :param session_id: the id of the current session
    """
    current_session = Session.objects.get(id=session_id)
    if isinstance(current_session, Session):
        # Open a new socket to stream messages to the server
        if request.method == 'GET':
            if request.environ.get(WSGI_WEBSOCKET):
                ws = request.environ[WSGI_WEBSOCKET]
                for message in current_session.queue.stream():
                    ws.send(message)

        # Add a new message to the stream
        elif request.method == 'POST':
            if isinstance(request.json, dict):
                current_session.queue.add(request.json)

    return ""

