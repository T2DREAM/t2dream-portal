#!/usr/bin/env python2
import argparse
import os
import sys
from collections import OrderedDict
from pyramid.compat import bytes_
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config
from pyramid.response import Response
from snovault import TYPES
from collections import OrderedDict
from snovault.util import simple_path_ids
from urllib.parse import (
    parse_qs,
    urlencode,
)
from pyramid.config import Configurator
import pprint
import csv
import io
import json
import subprocess
import requests
import shlex
import sys
import logging
import re
log = logging.getLogger(__name__)
EPILOG = '''
 %(prog)s GET file uuids associated with the experiment
Basic Useage:
sudo /srv/encoded/bin/py %(prog)s --accession TSTSR999372 
    
    accession id
'''
def get_files_uuids(result_dict):
    file_uuids = []
    for file in result_dict["files"]:
        file_uuids.append(file["uuid"])
    return list(set(file_uuids))


def file_uuid(accession):
    HEADERS = {'accept': 'application/json'}
    path = ('http://ec2-34-219-91-34.us-west-2.compute.amazonaws.com/experiment/' + accession)
    response = requests.get(path,headers=HEADERS)
    response_json_dict = response.json()
    results = json.dumps(response_json_dict, indent=4, separators=(',', ': '))
    uuids_in_results = get_files_uuids(response_json_dict)
    fout = io.StringIO()
    writer = csv.writer(fout, delimiter='\n')
    writer.writerows([uuids_in_results])
    return uuids_in_results

def main():
    parser = argparse.ArgumentParser(
        description=__doc__, epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        )
    parser.add_argument('--accession', help="accession id")
    args = parser.parse_args()
    accession = args.accession
    response = file_uuid(accession)
    print("\n".join(response))
if __name__ == "__main__":
    main()
