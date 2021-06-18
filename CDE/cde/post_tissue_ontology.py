import argparse
import os
import sys
import json
import requests
from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.security import (
    ALL_PERMISSIONS,
    Allow,
    Authenticated,
    Deny,
    DENY_ALL,
    Everyone,
)
import urllib.request
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
@view_config(route_name='tissueOntology', request_method='POST', renderer='json', permission=Allow)
def t2dkp(context, request):
    HEADERS = {'content-type': 'application/json', 'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS', 'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization', 'Access-Control-Allow-Credentials': 'true', 'Access-Control-Max-Age': '1728000'};
    url = 'https://dga-harmonization.s3-us-west-2.amazonaws.com/ontology_v3.json'
    url1 = requests.get(url, headers=HEADERS).json()
    json_doc = json.dumps(url1, indent=4, separators=(',', ': '))
    return Response(content_type='text/plain',body=json_doc)
if __name__ == '__main__':
    config = Configurator()
    config.add_route('tissueOntology','/tissueOntology')
    config.add_view(tissueOntology, route_name='tissueOntology')
    config.scan()
    app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 8080, app)
    server.serve_forever()
