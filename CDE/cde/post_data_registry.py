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
@view_config(route_name='getAnnotationRegistry', request_method='POST', renderer='json', permission=Allow)
def t2dkp(context, request):
    payload = request.json_body
    data = json.dumps(payload)
    AUTHID='BA5V5EID'; AUTHPW='tr4i3skb5yquihn2'; HEADERS = {'content-type': 'application/json'}; SERVER = 'https://www.diabetesepigenome.org/'
    URL = 'https://www.diabetesepigenome.org/annotation_registry_metadata/'
    URL1 = '%s/annotation_registry_metadata.json' % (urlencode(payload,doseq=True))
    r1 = requests.get(URL + URL1, auth=(AUTHID,AUTHPW), headers=HEADERS).json()
    json_doc = json.dumps(r1, indent=4, separators=(',', ': '))
    return Response(content_type='text/plain',body=json_doc)
if __name__ == '__main__':
    config = Configurator()
    config.add_route('getAnnotationRegistry','/getAnnotationRegistry')
    config.add_view(getAnnotationRegistry, route_name='getAnnotationRegistry')
    config.scan()
    app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 8080, app)
    server.serve_forever()
