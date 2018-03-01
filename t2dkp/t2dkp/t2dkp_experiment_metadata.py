import argparse
import os
import sys
import json
import requests
from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.view import view_config
from urllib.parse import (
    parse_qs,
    urlencode,
)
from collections import OrderedDict
from pyramid.compat import bytes_
from pyramid.httpexceptions import HTTPBadRequest
import logging
import io
import urllib
log = logging.getLogger(__name__)
@view_config(route_name='getExperimentMetadata', request_method='GET', renderer='json')
def t2dkp(context, request):
    HEADERS = {'accept': 'application/json'}
    URL = 'http://t2depigenome-test.org/experiment_metadata/experiment_metadata.json'
    r1 = requests.get(URL)
    json_doc = r1.json()
    json_doc = json.dumps(json_doc, indent=4, separators=(',', ': '))
    return Response(content_type='text/plain',body=json_doc)
if __name__ == '__main__':
    config = Configurator()
    config.add_route('getExperimentMetadata', '/getExperimentMetadata')
    config.add_view(getExperimentMetadata, route_name='getExperimentMetadata')
    config.scan()
    app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 8080, app)
    server.serve_forever()
