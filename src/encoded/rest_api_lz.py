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
from .search import iter_search_results
from .search import list_visible_columns_for_schemas
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
#log.setLevel(logging.INFO)

def includeme(config):
    config.add_route('lz_api', '/lz_api/{search_params}/{json}')
    config.scan(__name__)

# includes concatenated properties
_tsv_mapping = OrderedDict([
    ('File accession', ['files.title']),
    ('File format', ['files.file_type']),
    ('Output type', ['files.output_type']),
    ('Experiment accession', ['accession']),
    ('Annotation accession', ['accession']),
    ('Assay', ['assay_term_name']),
    ('Annotation', ['annotation_type']),
    ('Biosample term id', ['biosample_term_id']),
    ('Biosample term name', ['biosample_term_name']),
    ('Biosample type', ['biosample_type']),
    ('Biosample synonyms', ['biosample_synonyms']),
    ('software_used', ['software_used']),
    ('System slims', ['system_slims']),
    ('Organ slims', ['organ_slims']),
    ('Biosample life stage', ['replicates.library.biosample.life_stage']),
    ('Biosample sex', ['replicates.library.biosample.sex']),
    ('Biosample Age', ['replicates.library.biosample.age',
                       'replicates.library.biosample.age_units']),
    ('Biosample organism', ['replicates.library.biosample.organism.scientific_name']),
    ('Biosample treatments', ['replicates.library.biosample.treatments.treatment_term_name']),
    ('Biosample subcellular fraction term name', ['replicates.library.biosample.subcellular_fraction_term_name']),
    ('Biosample phase', ['replicates.library.biosample.phase']),
    ('Biosample synchronization stage', ['replicates.library.biosample.fly_synchronization_stage',
                                         'replicates.library.biosample.worm_synchronization_stage',
                                         'replicates.library.biosample.post_synchronization_time',
                                         'replicates.library.biosample.post_synchronization_time_units']),
    ('Experiment target', ['target.name']),
    ('Antibody accession', ['replicates.antibody.accession']),
    ('Library made from', ['replicates.library.nucleic_acid_term_name']),
    ('Library depleted in', ['replicates.library.depleted_in_term_name']),
    ('Library extraction method', ['replicates.library.extraction_method']),
    ('Library lysis method', ['replicates.library.lysis_method']),
    ('Library crosslinking method', ['replicates.library.crosslinking_method']),
    ('Library strand specific', ['replicates.library.strand_specificity']),
    ('Experiment date released', ['date_released']),
    ('Project', ['award.project']),
    ('RBNS protein concentration', ['files.replicate.rbns_protein_concentration', 'files.replicate.rbns_protein_concentration_units']),
    ('Library fragmentation method', ['files.replicate.library.fragmentation_method']),
    ('Library size range', ['files.replicate.library.size_range']),
    ('Biological replicate(s)', ['files.biological_replicates']),
    ('Technical replicate', ['files.replicate.technical_replicate_number']),
    ('Read length', ['files.read_length']),
    ('Mapped read length', ['files.mapped_read_length']),
    ('Run type', ['files.run_type']),
    ('Paired end', ['files.paired_end']),
    ('Paired with', ['files.paired_with']),
    ('Derived from', ['files.derived_from']),
    ('Size', ['files.file_size']),
    ('Lab', ['files.lab.title']),
    ('md5sum', ['files.md5sum']),
    ('bed_file_state', ['files.bed_file_state']),
    ('bed_file_value', ['files.bed_file_value']),
    ('file_format', ['files.file_format']),
    ('files.date_created', ['files.date_created']),
    ('dbxrefs', ['files.dbxrefs']),
    ('File download URL', ['files.href']),
    ('Assembly', ['files.assembly']),
    ('Platform', ['files.platform.title']),
    ('Controlled by', ['files.controlled_by']),
    ('External Source', ['dbxrefs']),
    ('File Status', ['files.status'])
])
target_gene_prediction_annotation = ['Coaccessible target genes']
def get_file_uuids(result_dict):
    file_uuids = []
    for item in result_dict['@graph']:
        for file in item['files']:
            file_uuids.append(file['uuid'])
    return list(set(file_uuids))

def get_biosample_accessions(file_json, experiment_json):
    for f in experiment_json['files']:
        if file_json['uuid'] == f['uuid']:
            accession = f.get('replicate', {}).get('library', {}).get('biosample', {}).get('accession')
            if accession:
                return accession
    accessions = []
    for replicate in experiment_json.get('replicates', []):
        accession = replicate['library']['biosample']['accession']
        accessions.append(accession)
    return ', '.join(list(set(accessions)))

def get_peak_metadata_links(request):
    if request.matchdict.get('search_params'):
        search_params = request.matchdict['search_params']
    else:
        search_params = request.query_string

    peak_download_tsv_link = '{host_url}/peak_download/{search_params}/peak_download.tsv'.format(
        host_url=request.host_url,
        search_params= search_params
    )
    return [peak_download_tsv_link]

def get_region_metadata_links(request):
    if request.matchdict.get('search_params'):
        search_params = request.matchdict['search_params']
    else:
        search_params = request.query_string

    region_metadata_tsv_link = '{host_url}/region_metadata/{search_params}/region_metadata.tsv'.format(
        host_url=request.host_url,
        search_params=search_params
    )
    return [region_metadata_tsv_link]

@view_config(route_name='lz_api', request_method='GET')
def lz_api(context, request):
    param_list = parse_qs(request.matchdict['search_params'])
    param_list['field'] = []
    param_list['limit'] = ['all']
    path = '/region-search/?{}&{}'.format(urlencode(param_list, True),'referrer=peak_metadata')
    results = request.embed(path, as_user=True)
    uuids_in_results = get_file_uuids(results)
    rows = []
    json_doc = {}
    json_doc['data'] = []
    for row in results['peaks']:
        if row['_id'] in uuids_in_results:
            file_json = request.embed(row['_id'])
            annotation_json = request.embed(file_json['dataset'])
            biosample = annotation_json['biosample_term_name']
            annotation = annotation_json['annotation_type']
            for hit in row['inner_hits']['positions']['hits']['hits']:
                data_row = []
                chrom = '{}'.format(row['_index'])
                assembly = '{}'.format(row['_type'])
                start = int('{}'.format(hit['_source']['start']))
                stop = int('{}'.format(hit['_source']['end']))
                state = '{}'.format(hit['_source']['state'])
                score = '{}'.format(hit['_source']['val'])
                target_gene =  state.split('_', 1)[-1].replace('.', '').upper()
                promoter = state.split(':', 1)[-1]
                promoter1 = promoter.split('-',1)[0]
                json_doc['data'].append({'chrom':chrom, 'regulatory element':start, 'promoter':promoter1, 'target':target_gene, 'score':score })
                    #unique by id (aka. unique by same state & same tissue/cell)
                    #json_doc2['data'] = list({v['id']:v for v in json_doc['data']}.values())
    if 'lz_api.json' in request.url:
        return Response(
            content_type='text/plain',
            body=json.dumps(json_doc,indent=2,sort_keys=True),
        )
