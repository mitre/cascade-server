# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

import re

from flask import Response
import markdown

from app.server import flask_app


@flask_app.route("/docs/<filebase>", methods=['GET'])
def serve_document(filebase):
    if "\\" in filebase or "/" in filebase or "." in filebase:
        return Response(status=404)

    try:
        with open("docs/{}.md".format(filebase), "r") as f:
            html = markdown.markdown(f.read(), output_format="html5")
    except IOError:
        return Response(status=404)

    for open_tag, title, close_tag in re.findall("<(h[0-9])>(.*?)</(h[0-9])>", html):
        if open_tag != close_tag:
            continue

        chunk = "<{tag}>{contents}</{tag}>".format(tag=open_tag, contents=title)
        section_id = title.replace(" ", "-").lower()
        new_chunk = '<{tag} id="{id}">{contents}</{tag}>'.format(tag=open_tag, id=section_id, contents=title)
        html = html.replace(chunk, new_chunk)

    html = '<div class="documentation container">{}</div'.format(html)
    return Response(html, 200)
