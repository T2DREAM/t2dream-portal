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
    config.add_route('batch_download', '/batch_download/{search_params}')
    config.add_route('metadata', '/metadata/{search_params}/{tsv}')
    config.add_route('peak_metadata', '/peak_metadata/{search_params}/{tsv}')
    config.add_route('peak_download', '/peak_download/{search_params}/{tsv}')
    config.add_route('variant_graph', '/variant_graph/{search_params}/{json}')
    config.add_route('region_metadata', '/region_metadata/{search_params}/{tsv}')
    config.add_route('report_download', '/report.tsv')
    config.add_route('experiment_metadata', '/experiment_metadata/{search_params}/{tsv}')
    config.add_route('annotation_metadata', '/annotation_metadata/{search_params}/{tsv}')
    config.add_route('data_filters', '/data_filters/{search_params}/{tsv}')
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
    ('File Status', ['files.status'])
])

_audit_mapping = OrderedDict([
    ('Audit WARNING', ['audit.WARNING.path',
                       'audit.WARNING.category',
                       'audit.WARNING.detail']),
    ('Audit INTERNAL_ACTION', ['audit.INTERNAL_ACTION.path',
                               'audit.INTERNAL_ACTION.category',
                               'audit.INTERNAL_ACTION.detail']),
    ('Audit NOT_COMPLIANT', ['audit.NOT_COMPLIANT.path',
                             'audit.NOT_COMPLIANT.category',
                             'audit.NOT_COMPLIANT.detail']),
    ('Audit ERROR', ['audit.ERROR.path',
                     'audit.ERROR.category',
                     'audit.ERROR.detail'])
])
_biosample_color = {
    'liver':'#fdd993',
    'HepG2':'#8b0000',
    'islet of Langerhans':'#f28080',
    'adipocyte': '#f98900',
    'ESC derived cell line':'#ab93fd',
    'subcutaneous adipose': '#21a041',
    'pancreas':'#78ff02'
}
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

def make_cell(header_column, row, exp_data_row):
    temp = []
    for column in _tsv_mapping[header_column]:
        c_value = []
        for value in simple_path_ids(row, column):
            if str(value) not in c_value:
                c_value.append(str(value))
        if column == 'replicates.library.biosample.post_synchronization_time' and len(temp):
            if len(c_value):
                temp[0] = temp[0] + ' + ' + c_value[0]
        elif len(temp):
            if len(c_value):
                temp = [x + ' ' + c_value[0] for x in temp]
        else:
            temp = c_value
    exp_data_row.append(', '.join(list(set(temp))))


def make_audit_cell(header_column, experiment_json, file_json):
    categories = []
    paths = []
    for column in _audit_mapping[header_column]:
        for value in simple_path_ids(experiment_json, column):
            if 'path' in column:
                paths.append(value)
            elif 'category' in column:
                categories.append(value)
    data = []
    for i, path in enumerate(paths):
        if '/files/' in path and file_json.get('title', '') not in path:
            # Skip file audits that does't belong to the file
            continue
        else:
            data.append(categories[i])
    return ', '.join(list(set(data)))


@view_config(route_name='peak_metadata', request_method='GET')
def peak_metadata(context, request):
    param_list = parse_qs(request.matchdict['search_params'])
    param_list['field'] = []
    header = ['annotation_type', 'source', 'coordinates', 'file.accession', 'annotation.accession']
    param_list['limit'] = ['all']
    path = '/variant-search/?{}&{}'.format(urlencode(param_list, True),'referrer=peak_metadata')
    results = request.embed(path, as_user=True)
    uuids_in_results = get_file_uuids(results)
    rows = []
    json_doc = {}
    for row in results['peaks']:
        if row['_id'] in uuids_in_results:
            file_json = request.embed(row['_id'])
            annotation_json = request.embed(file_json['dataset'])
            for hit in row['inner_hits']['positions']['hits']['hits']:
                data_row = []
                chrom = '{}'.format(row['_index'])
                assembly = '{}'.format(row['_type'])
                start = int('{}'.format(hit['_source']['start']))
                stop = int('{}'.format(hit['_source']['end']))
                state = '{}'.format(hit['_source']['state'])
                val = '{}'.format(hit['_source']['val'])
                file_accession = file_json['accession']
                annotation_accession = annotation_json['accession']
                coordinates = '{}:{}-{}'.format(row['_index'], hit['_source']['start'], hit['_source']['end'])
                annotation = annotation_json['annotation_type']
                biosample_term = annotation_json['biosample_term_name']
                data_row.extend([annotation, biosample_term, coordinates, annotation_accession])
                rows.append(data_row)
                if annotation not in json_doc:
                    json_doc[annotation] = []
                    json_doc[annotation].append({
                        'annotation_type': annotation,
                        'coordinates':coordinates,
                        'state': state,
                        'value': val,
                        'biosample_term_name': biosample_term,
                        'genome': assembly,
                        'accession': annotation_accession
                    })
                else:
                    json_doc[annotation].append({
                        'annotation_type': annotation,
                        'coordinates':coordinates,
                        'state': state,
                        'value': val,
                        'biosample_term_name': biosample_term,
                        'genome': assembly,
                        'accession': annotation_accession
                })
    return Response(
        content_type='text/plain',
        body=json.dumps(json_doc,indent=2,sort_keys=True)
        )
    fout = io.StringIO()
    writer = csv.writer(fout, delimiter='\t')
    writer.writerow(header)
    writer.writerows(rows)
    return Response(
        content_type='text/tsv',
        body=fout.getvalue(),
        content_disposition='attachment;filename="%s"' % 'peak_download.tsv'
    )


@view_config(route_name='variant_graph', request_method='GET')
def variant_graph(context, request):
    param_list = parse_qs(request.matchdict['search_params'])
    param_list['field'] = []
    param_list['limit'] = ['all']
    path = '/variant-search/?{}&{}'.format(urlencode(param_list, True),'referrer=peak_metadata')
    results = request.embed(path, as_user=True)
    uuids_in_results = get_file_uuids(results)
    rows = []
    json_doc = {}
    json_doc['nodes'] = []
    query = results['query']
    json_doc['nodes'].append({'path':query,'id':"", 'color':"#170451", "link":"region=" + query + "&genome=GRCh37","label":query})
    for row in results['peaks']:
        if row['_id'] in uuids_in_results:
            file_json = request.embed(row['_id'])
            annotation_json = request.embed(file_json['dataset'])
            biosample_term_list = ['liver', 'pancreas', 'adipocyte', 'islet of Langerhans', 'HepG2', 'ESC derived cell line', 'subcutaneous adipose']
            biosample = annotation_json['biosample_term_name']
            biosample_term_list = ['liver', 'pancreas', 'adipocyte', 'islet of Langerhans', 'HepG2', 'ESC derived cell line', 'subcutaneous adipose']
            if biosample in biosample_term_list:
                json_doc['nodes'].append({'path':query + '|' + biosample,'id':biosample, 'color': _biosample_color[biosample], "link":"biosample_term_name=" + biosample ,"label":biosample, "name": biosample})
            for hit in row['inner_hits']['positions']['hits']['hits']:
                data_row = []
                chrom = '{}'.format(row['_index'])
                assembly = '{}'.format(row['_type'])
                start = int('{}'.format(hit['_source']['start']))
                stop = int('{}'.format(hit['_source']['end']))
                state = '{}'.format(hit['_source']['state'])
                val = '{}'.format(hit['_source']['val'])
                file_accession = file_json['accession']
                annotation_accession = annotation_json['accession']
                coordinates = '{}:{}-{}'.format(row['_index'], hit['_source']['start'], hit['_source']['end'])
                annotation = annotation_json['annotation_type']
                biosample_term = annotation_json['biosample_term_name']
                biosample_term_list = ['liver', 'pancreas', 'adipocyte', 'islet of Langerhans', 'HepG2', 'ESC derived cell line', 'subcutaneous adipose']
                if biosample_term in biosample_term_list:
                    json_doc['nodes'].append({'path':query + '|' + biosample_term + '|' + state + '_' + coordinates, 'id':state, 'color': _biosample_color[biosample_term], "link": "accession=" + annotation_accession, "label": state, "name":annotation_accession})  
    if 'variant_graph.json' in request.url:
        return Response(
            content_type='text/plain',
            body=json.dumps(json_doc,indent=2,sort_keys=True),
        )

@view_config(route_name='peak_download', request_method='GET')
def peak_download(context, request):
    param_list = parse_qs(request.matchdict['search_params'])
    param_list['field'] = []
    header = ['annotation_type', 'source', 'coordinates', 'file.accession', 'annotation.accession']
    param_list['limit'] = ['all']
    path = '/variant-search/?{}&{}'.format(urlencode(param_list, True),'referrer=download_metadata')
    results = request.embed(path, as_user=True)
    uuids_in_results = get_file_uuids(results)
    rows = []
    json_doc = {}
    for row in results['peaks']:
        if row['_id'] in uuids_in_results:
            file_json = request.embed(row['_id'])
            annotation_json = request.embed(file_json['dataset'])
            for hit in row['inner_hits']['positions']['hits']['hits']:
                data_row = []
                chrom = '{}'.format(row['_index'])
                assembly = '{}'.format(row['_type'])
                start = int('{}'.format(hit['_source']['start']))
                stop = int('{}'.format(hit['_source']['end']))
                state = '{}'.format(hit['_source']['state'])
                val = '{}'.format(hit['_source']['val'])
                file_accession = file_json['accession']
                annotation_accession = annotation_json['accession']
                coordinates = '{}:{}-{}'.format(row['_index'], hit['_source']['start'], hit['_source']['end'])
                annotation = annotation_json['annotation_type']
                biosample_term = annotation_json['biosample_term_name']
                data_row.extend([annotation, biosample_term, coordinates, annotation_accession])
                rows.append(data_row)
                if annotation not in json_doc:
                    json_doc[annotation] = []
                    json_doc[annotation].append({
                        'annotation_type': annotation,
                        'coordinates':coordinates,
                        'state': state,
                        'value': val,
                        'biosample_term_name': biosample_term,
                        'genome': assembly,
                        'accession': annotation_accession
                    })
                else:
                    json_doc[annotation].append({
                        'annotation_type': annotation,
                        'coordinates':coordinates,
                        'state': state,
                        'value': val,
                        'biosample_term_name': biosample_term,
                        'genome': assembly,
                        'accession': annotation_accession
                })
    fout = io.StringIO()
    writer = csv.writer(fout, delimiter='\t')
    writer.writerow(header)
    writer.writerows(rows)
    return Response(
        content_type='text/tsv',
        body=fout.getvalue(),
        content_disposition='attachment;filename="%s"' % 'peak_metadata.tsv'
    )

@view_config(route_name='region_metadata', request_method='GET')
def region_metadata(context, request):
    param_list = parse_qs(request.matchdict['search_params'])
    param_list['field'] = []
    header = ['annotation_type', 'source', 'coordinates', 'file.accession', 'annotation.accession']
    param_list['limit'] = ['all']
    path = '/region-search/?{}&{}'.format(urlencode(param_list, True),'referrer=region_metadata')
    results = request.embed(path, as_user=True)
    uuids_in_results = get_file_uuids(results)
    rows = []
    json_doc = {}
    for row in results['peaks']:
        if row['_id'] in uuids_in_results:
            file_json = request.embed(row['_id'])
            annotation_json = request.embed(file_json['dataset'])
            for hit in row['inner_hits']['positions']['hits']['hits']:
                data_row = []
                chrom = '{}'.format(row['_index'])
                assembly = '{}'.format(row['_type'])
                start = int('{}'.format(hit['_source']['start']))
                stop = int('{}'.format(hit['_source']['end']))
                state = '{}'.format(hit['_source']['state'])
                val = '{}'.format(hit['_source']['val'])
                file_accession = file_json['accession']
                annotation_accession = annotation_json['accession']
                coordinates = '{}:{}-{}'.format(row['_index'], hit['_source']['start'], hit['_source']['end'])
                annotation = annotation_json['annotation_type']
                biosample_term = annotation_json['biosample_term_name']
                data_row.extend([annotation, biosample_term, coordinates, annotation_accession])
                rows.append(data_row)
                if annotation not in json_doc:
                    json_doc[annotation] = []
                    json_doc[annotation].append({
                        'annotation_type': annotation,
                        'coordinates':coordinates,
                        'state': state,
                        'value': val,
                        'biosample_term_name': biosample_term,
                        'genome': assembly,
                        'accession': annotation_accession
                    })
                else:
                    json_doc[annotation].append({
                        'annotation_type': annotation,
                        'coordinates':coordinates,
                        'state': state,
                        'value': val,
                        'biosample_term_name': biosample_term,
                        'genome': assembly,
                        'accession': annotation_accession
                })
    return Response(
        content_type='text/plain',
        body=json.dumps(json_doc,indent=2,sort_keys=True)
        )
    fout = io.StringIO()
    writer = csv.writer(fout, delimiter='\t')
    writer.writerow(header)
    writer.writerows(rows)
    return Response(
        content_type='text/tsv',
        body=fout.getvalue(),
        content_disposition='attachment;filename="%s"' % 'region_metadata.tsv'
    )
@view_config(route_name='metadata', request_method='GET')
def metadata_tsv(context, request):
    param_list = parse_qs(request.matchdict['search_params'])
    if 'referrer' in param_list:
        search_path = '/{}/'.format(param_list.pop('referrer')[0])
    else:
        search_path = '/search/'
    param_list['field'] = []
    header = []
    file_attributes = []
    for prop in _tsv_mapping:
        header.append(prop)
        param_list['field'] = param_list['field'] + _tsv_mapping[prop]
        if _tsv_mapping[prop][0].startswith('files'):
            file_attributes = file_attributes + [_tsv_mapping[prop][0]]
    param_list['limit'] = ['all']
    path = '{}?{}'.format(search_path, urlencode(param_list, True))
    results = request.embed(path, as_user=True)
    rows = []
    for experiment_json in results['@graph']:
        if experiment_json['files']:
            exp_data_row = []
            for column in header:
                if not _tsv_mapping[column][0].startswith('files'):
                    make_cell(column, experiment_json, exp_data_row)

            f_attributes = ['files.title', 'files.file_type',
                            'files.output_type']
            
            for f in experiment_json['files']:
                if 'files.file_type' in param_list:
                    if f['file_type'] not in param_list['files.file_type']:
                        continue
                f['href'] = request.host_url + f['href']
                f_row = []
                for attr in f_attributes:
                    f_row.append(f[attr[6:]])
                data_row = f_row + exp_data_row
                for prop in file_attributes:
                    if prop in f_attributes:
                        continue
                    path = prop[6:]
                    temp = []
                    for value in simple_path_ids(f, path):
                        temp.append(str(value))
                    if prop == 'files.replicate.rbns_protein_concentration':
                        if 'replicate' in f and 'rbns_protein_concentration_units' in f['replicate']:
                            temp[0] = temp[0] + ' ' + f['replicate']['rbns_protein_concentration_units']
                    if prop in ['files.paired_with', 'files.derived_from']:
                        # chopping of path to just accession
                        if len(temp):
                            new_values = [t[7:-1] for t in temp]
                            temp = new_values
                    data = list(set(temp))
                    data.sort()
                    data_row.append(', '.join(data))
                audit_info = [make_audit_cell(audit_type, experiment_json, f) for audit_type in _audit_mapping]
                data_row.extend(audit_info)
                rows.append(data_row)
    fout = io.StringIO()
    writer = csv.writer(fout, delimiter='\t')
    header.extend([prop for prop in _audit_mapping])
    writer.writerow(header)
    writer.writerows(rows)
    return Response(
        content_type='text/tsv',
        body=fout.getvalue(),
        content_disposition='attachment;filename="%s"' % 'metadata.tsv'
    )
@view_config(route_name= 'experiment_metadata', request_method='GET')
def experiment_metadata(context, request):
    param_list = parse_qs(request.matchdict['search_params'])
    if 'referrer' in param_list:
        search_path = '/{}/'.format(param_list.pop('referrer')[0])
    else:
        search_path = '/search/'
    param_list['field'] = []
    file_attributes = []
    for prop in _tsv_mapping:
        param_list['field'] = param_list['field'] + _tsv_mapping[prop]
        if _tsv_mapping[prop][0].startswith('files'):
            file_attributes = file_attributes + [_tsv_mapping[prop][0]]
    param_list['limit'] = ['all']
    path = '{}?{}'.format(search_path, urlencode(param_list, True))
    results = request.embed(path, as_user=True)
    json_doc = {}
    for experiment_json in results['@graph']:
        files = {}
        for f in experiment_json['files']:
            title = f['title']
            lab = f['lab']['title']
            href = request.host_url + f['href']
            status = f['status']
            if title not in files:
                files[title] = []
                files[title].append({
                    'href': href,
                    'status': status,
                    'lab': lab
                    })
            else:
                files[title].append({
                    'href': href,
                    'status': status,
                    'lab': lab
                    })                
        assay_id = experiment_json['accession']
        assay = experiment_json['assay_term_name']
        biosample_term = experiment_json['biosample_term_name']
        replicate = experiment_json['replicates']
        if assay not in json_doc:
            json_doc[assay] = []
            json_doc[assay].append({
                'assay_term_name': assay,
                'assay_id': assay_id,
                'biosample_term': biosample_term,
                'file_download': files,
                'replicates': replicate
                })  
        else:
            json_doc[assay].append({
                'assay': assay,
                'assay id': assay_id,
                'biosample_term': biosample_term,
                'file_download': files,
                'replicates': replicate
                })  
    if 'experiment_metadata.json' in request.url:
        return Response(
            content_type='text/plain',
            body=json.dumps(json_doc,indent=2,sort_keys=True),
            content_disposition='attachment;filename="%s"' % 'experiment_metadata.json'
    )
@view_config(route_name= 'annotation_metadata', request_method='GET')
def annotation_metadata(context, request):
    param_list = parse_qs(request.matchdict['search_params'])
    if 'referrer' in param_list:
        search_path = '/{}/'.format(param_list.pop('referrer')[0])
    else:
        search_path = '/search/'
    param_list['field'] = []
    file_attributes = []
    for prop in _tsv_mapping:
        param_list['field'] = param_list['field'] + _tsv_mapping[prop]
        if _tsv_mapping[prop][0].startswith('files'):
            file_attributes = file_attributes + [_tsv_mapping[prop][0]]
    param_list['limit'] = ['all']
    path = '{}?{}'.format(search_path, urlencode(param_list, True))
    results = request.embed(path, as_user=True)
    json_doc = {}
    for annotation_json in results['@graph']:
        files = {}
        for f in annotation_json['files']:
            title = f['title']
            md5sum = f['md5sum']
            date_created = f['date_created']
            lab = f['lab']['title']
            href = request.host_url + f['href']
            status = f['status']
            assembly = f['assembly']
            state_key = 'bed_file_state'
            value_key = 'bed_file_value'
            if state_key and value_key in f:
                state_descriptor = f['bed_file_state']
                value_descriptor = f['bed_file_value']
            else:
                state_descriptor = 'none'
                value_descriptor = 'none'
            if f['file_format'] == 'bed':
                if title not in files:
                    files[title] = []
                    files[title].append({
                        'md5sum': md5sum,
                        'date_created': date_created,
                        'href': href,
                        'status': status,
                        'lab': lab,
                        'assembly': assembly,
                        'value_descriptor': value_descriptor,
                        'state_descriptor': state_descriptor
                    })
                else:
                    files[title].append({
                        'md5sum': md5sum,
                        'date_created': date_created,
                        'href': href,
                        'status': status,
                        'lab': lab,
                        'assembly': assembly,
                        'value_descriptor': value_descriptor,
                        'state_descriptor': state_descriptor
                    })
        annotation_id = annotation_json['accession']
        annotation_type = annotation_json['annotation_type']
        biosample_term_name = annotation_json['biosample_term_name']
        if files:
            if annotation_type not in json_doc:
                json_doc[annotation_type] = []
                json_doc[annotation_type].append({
                    'annotation_type': annotation_type,
                    'annotation_id': annotation_id,
                    'biosample_term_name': biosample_term_name,
                    'file_download': files
                })  
            else:
                json_doc[annotation_type].append({
                    'annotation_type': annotation_type,
                    'annotation_id': annotation_id,
                    'biosample_term_name': biosample_term_name,
                    'file_download': files
                })  
    if 'annotation_metadata.json' in request.url:
        return Response(
            content_type='text/plain',
            body=json.dumps(json_doc,indent=2,sort_keys=True),
            content_disposition='attachment;filename="%s"' % 'annotation_metadata.json'
    )
@view_config(route_name='data_filters', request_method='GET')
def data_filters(context, request):
    param_list = parse_qs(request.matchdict['search_params'])
    if 'referrer' in param_list:
        search_path = '/{}/'.format(param_list.pop('referrer')[0])
    else:
        search_path = '/search/'
    param_list['field'] = []
    param_list['limit'] = ['all']
    path = '{}?{}'.format(search_path, urlencode(param_list, True))
    results = request.embed(path, as_user=True)
    json_doc = {}
    for dataFilter_json in results['facets']:
        field = dataFilter_json['field']
        for term in dataFilter_json['terms']:
            if term['doc_count'] != 0:
                if field not in json_doc:
                    json_doc[field] = []
                    json_doc[field].append({term['key']:term['doc_count']})
                else:
                    json_doc[field].append({term['key']:term['doc_count']})
    if 'data_filters.json' in request.url:
        return Response(
            content_type='text/plain',
            body=json.dumps(json_doc,indent=2,sort_keys=True),
            content_disposition='attachment;filename="%s"' % 'data_filters.json'
        )
@view_config(route_name='batch_download', request_method='GET')
def batch_download(context, request):
    # adding extra params to get required columns
    param_list = parse_qs(request.matchdict['search_params'])
    param_list['field'] = ['files.href', 'files.file_type']
    param_list['limit'] = ['all']
    path = '/search/?%s' % urlencode(param_list, True)
    results = request.embed(path, as_user=True)
    metadata_link = '{host_url}/metadata/{search_params}/metadata.tsv'.format(
        host_url=request.host_url,
        search_params=request.matchdict['search_params']
    )
    files = [metadata_link]
    if 'files.file_type' in param_list:
        for exp in results['@graph']:
            for f in exp['files']:
                if f['file_type'] in param_list['files.file_type']:
                    files.append('{host_url}{href}'.format(
                        host_url=request.host_url,
                        href=f['href']
                    ))
    else:
        for exp in results['@graph']:
            for f in exp['files']:
                files.append('{host_url}{href}'.format(
                    host_url=request.host_url,
                    href=f['href']
                ))
    return Response(
        content_type='text/plain',
        body='\n'.join(files),
        content_disposition='attachment; filename="%s"' % 'files.txt'
    )
def lookup_column_value(value, path):
    nodes = [value]
    names = path.split('.')
    for name in names:
        nextnodes = []
        for node in nodes:
            if name not in node:
                continue
            value = node[name]
            if isinstance(value, list):
                nextnodes.extend(value)
            else:
                nextnodes.append(value)
        nodes = nextnodes
        if not nodes:
            return ''
    # if we ended with an embedded object, show the @id
    if nodes and hasattr(nodes[0], '__contains__') and '@id' in nodes[0]:
        nodes = [node['@id'] for node in nodes]
    seen = set()
    deduped_nodes = [n for n in nodes if not (n in seen or seen.add(n))]
    return u','.join(u'{}'.format(n) for n in deduped_nodes)


def format_row(columns):
    """Format a list of text columns as a tab-separated byte string."""
    return b'\t'.join([bytes_(c, 'utf-8') for c in columns]) + b'\r\n'


@view_config(route_name='report_download', request_method='GET')
def report_download(context, request):
    types = request.params.getall('type')
    if len(types) != 1:
        msg = 'Report view requires specifying a single type.'
        raise HTTPBadRequest(explanation=msg)

    # Make sure we get all results
    request.GET['limit'] = 'all'

    schemas = [request.registry[TYPES][types[0]].schema]
    columns = list_visible_columns_for_schemas(request, schemas)
    
    # Work around Excel bug; can't open single column TSV with 'ID' header
    if len(columns) == 1 and '@id' in columns:
        columns['@id']['title'] = 'id'

    header = [column.get('title') or field for field, column in columns.items()]

    def generate_rows():
        yield format_row(header)
        for item in iter_search_results(context, request):
            values = [lookup_column_value(item, path) for path in columns]
            yield format_row(values)
    # Stream response using chunked encoding.
    request.response.content_type = 'text/tsv'
    request.response.content_disposition = 'attachment;filename="%s"' % 'report.tsv'
    request.response.app_iter = generate_rows()
    return request.response
