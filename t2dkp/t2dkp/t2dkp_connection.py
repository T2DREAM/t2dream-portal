import argparse
import os
import sys
import json
import requests
from pyramid.config import Configurator
from pyramid.response import Response
def list_cities(request):
    return Response('List of cities\n')
#r = requests.get(url = T2DKP_API_ENDPOINT, params = input_query)
dict1={'chromosome': 'chr10', 'start':'75252201', 'end':'75252201', 'assembly':'GRCh37', 'limit':'5'}
region = '{}:{}-{}'.format(dict1['chromosome'],dict1['start'],dict1['end'])
limit = dict1['limit']
genome = 'GRCh37'
HEADERS = {'accept': 'application/json'}
URL = 'http://t2depigenome-test.org/peak_metadata/region='
response = requests.get(URL + region  + '&genome=' + genome + '&limit=' + limit +'/peak_metadata.json', headers=HEADERS)
json_doc = response.json()
json_doc = json.dumps(json_doc, indent=4, separators=(',', ': '))
print(json_doc)
#r1 = requests.post(url = T2DKP_API_ENDPOINT, data = json_doc)
if __name__ == '__main__':
    config = Configurator()
    config.add_route('t2dkp', '/t2dkp')
    config.add_view(list_cities, route_name='t2dkp')
