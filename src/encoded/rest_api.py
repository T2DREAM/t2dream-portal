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
    config.add_route('peak_metadata', '/peak_metadata/{search_params}/{tsv}')
    config.add_route('variant_graph', '/variant_graph/{search_params}/{json}')
    config.add_route('variant_all_graph', '/variant_all_graph/{search_params}/{json}')
    config.add_route('variant_table', '/variant_table/{search_params}/{json}')
    config.add_route('region_metadata', '/region_metadata/{search_params}/{tsv}')
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

varshney_chromhmm_states = {
    'Strong_transcription': 'Transcription',
    'Repressed_polycomb': 'Repressed-polycomb',
    'Genic_enhancer': 'Enhancer_Genic',
    'Weak_TSS': 'Promoter_Weak',
    'Weak_repressed_polycomb': 'Repressed-polycomb_Weak',
    'Quiescent/low_signal': 'Quiescent-low',
    'Active_enhancer_1': 'Enhancer_Active_1',
    'Active_enhancer_2': 'Enhancer_Active_2',
    'Weak_transcription': 'Transcription_Weak',
    'Flanking_TSS': 'Promoter_Flanking',
    'Active_TSS': 'Promoter_Active',
    'Bivalent/poised_TSS': 'Promoter_Bivalent',
    'Weak_enhancer': 'Enhancer_Weak'
}
roadmap_chromhmm_states = {
    'Tx': 'Transcription',
    'Txn': 'Transcription',
    'ReprPC': 'Repressed-polycomb',
    'ReprPCWk': 'Repressed-polycomb_Weak',
    'EnhG': 'Enhancer_Genic',
    'EnhG1': 'Enhancer_Genic_1',
    'EnhG2': 'Enhancer_Genic_2',
    'Quies': 'Quiescent-low',
    'EnhA1': 'Enhancer_Active_1',
    'EnhA2': 'Enhancer_Active_2',
    'TxWk': 'Transcription_Weak',
    'TssAFlnk': 'Promoter_Flanking',
    'TssFlnk': 'Promoter_Flanking',
    'TssA': 'Promoter_Active',
    'TssBiv': 'Promoter_Bivalent',
    'BivFlnk': 'Promoter_Bivalent_Flanking',
    'EnhWk': 'Enhancer_Weak',
    'TssFlnkU': 'Promoter_Flanking_Upstream',
    'Het': 'Heterochromatin',
    'ZNF/Rpts': 'ZNF-Repeat',
    'TssFlnkD': 'Promoter_Flanking_Downstream',
    'EnhBiv': 'Enhancer_Bivalent',
    'TxFlnk': 'Transcription_Flanking',
    'Enh': 'Enhancer',
    'Ctcf': 'CTCF-bound'
}

_states_maps = {
    'Strong_transcription': 'Transcription',
    'Repressed_polycomb': 'Repressed-polycomb',
    'Genic_enhancer': 'Enhancer_Genic',
    'Weak_TSS': 'Promoter_Weak',
    'Weak_repressed_polycomb': 'Repressed-polycomb_Weak',
    'Quiescent/low_signal': 'Quiescent-low',
    'Active_enhancer_1': 'Enhancer_Active_1',
    'Active_enhancer_2': 'Enhancer_Active_2',
    'Weak_transcription': 'Transcription_Weak',
    'Flanking_TSS': 'Promoter_Flanking',
    'Active_TSS': 'Promoter_Active',
    'Bivalent/poised_TSS': 'Promoter_Bivalent',
    'Weak_enhancer': 'Enhancer_Weak',
    'Tx': 'Transcription',
    'Txn': 'Transcription',
    'ReprPC': 'Repressed-polycomb',
    'ReprPCWk': 'Repressed-polycomb_Weak',
    'EnhG': 'Enhancer_Genic',
    'EnhG1': 'Enhancer_Genic_1',
    'EnhG2': 'Enhancer_Genic_2',
    'Quies': 'Quiescent-low',
    'EnhA1': 'Enhancer_Active_1',
    'EnhA2': 'Enhancer_Active_2',
    'TxWk': 'Transcription_Weak',
    'TssAFlnk': 'Promoter_Flanking',
    'TssFlnk': 'Promoter_Flanking',
    'TssA': 'Promoter_Active',
    'TssBiv': 'Promoter_Bivalent',
    'BivFlnk': 'Promoter_Bivalent_Flanking',
    'EnhWk': 'Enhancer_Weak',
    'TssFlnkU': 'Promoter_Flanking_Upstream',
    'Het': 'Heterochromatin',
    'ZNF/Rpts': 'ZNF-Repeat',
    'TssFlnkD': 'Promoter_Flanking_Downstream',
    'EnhBiv': 'Enhancer_Bivalent',
    'TxFlnk': 'Transcription_Flanking',
    'Enh': 'Enhancer',
    'Ctcf': 'CTCF-bound',
    'alpha_1': 'Glucagon high',
    'alpha_2': 'Glucagon low',
    'beta_1': 'Insulin high',
    'beta_2': 'Insulin low',
    'delta_1': 'Somatostatin high',
    'delta_2': 'Somatostatin low'
    }
_high_states = ['Enhancer_Active_1', 'Enhancer_Active_2',  'Promoter_Active']
_biosample_color = {
    'liver':'#ffd700',
    'HepG2':'#ffd700',
    'islet of Langerhans':'#8b0000',
    'adipocyte': '#f98900',
    'subcutaneous adipose': '#66ffff',
    'visceral omenum adipose': '#5daaaa',
    'skeletal muscle myoblast':'#2c5e8d',
    'skeletal muscle':'#1a5353',
    'pancreas':'#8b0000',
    'pancreatic alpha cell': '#8b0000',
    'pancreatic beta cell': '#8b0000',
    'pancreatic delta cell': '#8b0000',
    'pancreatic stellate cell':'#8b0000',
    'pancreatic acinar cell':'#8b0000',
    'pancreatic cell':'#8b0000',
    'pancreatic ductal cell':'#8b0000',
    'pancreatic endothelial cell':'#8b0000',
    'pancreatic exocrine cell':'#8b0000',
    'pancreatic glial cell':'#8b0000',
    'pancreatic immune cell':'#8b0000',
    'pancreatic polypeptide-secreting cell':'#8b0000',
    'heart':'#ff0000',
    'aorta': '#ff0000',
    'heart left ventricle':'#ff0000',
    'heart right ventricle':'#ff0000',
    'kidney':'#7fff00',
    'right cardiac atrium':'#ff0000',
    'endothelial cell of umbilical vein':'#ff00ff',
    'coronary artery':'#ff0000',
    'ascending aorta':'#ff0000',    
    'CD34-PB':'#d6d1d1',
    'GM12878':'#d6d1d1',
    'H1':'#d6d1d1',
    'K562':'#d6d1d1',
    'caudate nucleus':'#d6d1d1',
    'cingulate gyrus':'#d6d1d1',
    'colonic mucosa':'#d6d1d1',
    'duodenum mucosa':'#d6d1d1',
    'fibroblast of lung':'#d6d1d1',
    'keratinocyte':'#d6d1d1',
    'layer of hippocampus':'#d6d1d1',
    'mammary epithelial cell':'#d6d1d1',
    'mesenchymal cell':'#d6d1d1',
    'mid-frontal lobe':'#d6d1d1',
    'mucosa of rectum':'#d6d1d1',
    'rectal smooth muscle':'#d6d1d1',
    'stomach smooth muscle':'#d6d1d1',
    'substantia nigra':'#d6d1d1',
    'temporal lobe':'#d6d1d1',
    'muscle of leg':'#d6d1d1',
    'germinal matrix':'#d6d1d1',
    'angular gyrus':'#d6d1d1',
    'ESC derived cell line':'#d6d1d1',
}
biosample_term_list = [ 'adipocyte','subcutaneous adipose', 'ESC derived cell line', 'kidney','skeletal muscle', 'visceral omenum adipose', 'CD34-PB', 'GM12878', 'H1', 'K562', 'caudate nucleus', 'cingulate gyrus', 'colonic mucosa', 'duodenum mucosa', 'endothelial cell of umbilical vein', 'fibroblast of lung', 'keratinocyte', 'layer of hippocampus', 'mammary epithelial cell', 'mesenchymal cell', 'mid-frontal lobe', 'mucosa of rectum', 'rectal smooth muscle', 'skeletal muscle myoblast', 'stomach smooth muscle', 'substantia nigra', 'temporal lobe', 'muscle of leg', 'germinal matrix', 'angular gyrus']
pancreatic_cells = [ 'pancreas', 'pancreatic acinar cell', 'pancreatic cell', 'pancreatic ductal cell', 'pancreatic endothelial cell', 'pancreatic exocrine cell', 'pancreatic glial cell', 'pancreatic immune cell', 'pancreatic alpha cell', 'pancreatic beta cell', 'pancreatic delta cell','islet of Langerhans', 'pancreatic polypeptide-secreting cell',  'pancreatic stellate cell']
heart_tissues =[ 'aorta', 'heart left ventricle', 'heart right ventricle', 'right cardiac atrium', 'coronary artery', 'ascending aorta', 'heart']
liver_cells =  ['HepG2', 'liver']

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
    json_doc1 = {}
    json_doc2 = {}
    json_doc['nodes'] = []
    json_doc1['nodes'] = []
    json_doc2['nodes'] = []
    query = results['query']
    biosample_check = []
    cell_check = []
    json_doc['nodes'].append({'path':query,'id':query, 'color':'#170451', 'link':'region=' + query + '&genome=GRCh37','label':query, 'name': query, 'type':'rsid','biosample':'-', 'annotation_type':'-', 'accession_ids':'-'})
    for row in results['peaks']:
        if row['_id'] in uuids_in_results:
            file_json = request.embed(row['_id'])
            annotation_json = request.embed(file_json['dataset'])
            biosample = annotation_json['biosample_term_name']
            if biosample in biosample_term_list:
                if biosample not in biosample_check:
                    json_doc['nodes'].append({'path':query + '|' + biosample,'id':biosample, 'color': _biosample_color[biosample], 'link':'biosample_term_name=' + biosample ,'label':biosample, 'name': biosample, 'type':'biosample','biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    biosample_check.append(biosample)
            if biosample in pancreatic_cells:
                if 'pancreas' not in biosample_check:
                    json_doc['nodes'].append({'path':query + '|pancreas','id':'pancreas', 'color': _biosample_color['pancreas'], 'link':'biosample_term_name=pancreas', 'label':'pancreas', 'name': 'pancreas', 'type':'biosample','biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    biosample_check.append('pancreas')
                if biosample not in cell_check:
                    json_doc['nodes'].append({'path':query + '|pancreas|' + biosample,'id':'pancreas|'+biosample, 'color': _biosample_color[biosample], 'link':'biosample_term_name=' + biosample, 'label':biosample, 'name': biosample, 'type':'cell','biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    cell_check.append(biosample)
            elif biosample in liver_cells:
                if 'liver' not in biosample_check:
                    json_doc['nodes'].append({'path':query + '|liver','id':'liver', 'color': _biosample_color['liver'], 'link':'biosample_term_name=liver', 'label':'liver', 'name': 'liver', 'type':'biosample','biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    biosample_check.append('liver')
                if biosample not in cell_check:
                    json_doc['nodes'].append({'path':query + '|liver|' + biosample,'id':'liver|'+biosample, 'color': _biosample_color[biosample], 'link':'biosample_term_name=' + biosample ,'label':biosample, 'name': biosample, 'type':'cell','biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    cell_check.append(biosample)
            elif biosample in heart_tissues:
                if 'heart' not in biosample_check:
                    json_doc['nodes'].append({'path':query + '|heart','id':'heart', 'color': _biosample_color['heart'], 'link':'biosample_term_name=heart', 'label':'heart', 'name': 'heart', 'type':'biosample','type':'biosample', 'biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    biosample_check.append('heart')
                if biosample not in cell_check:
                    json_doc['nodes'].append({'path':query + '|heart|' + biosample,'id':'heart|'+biosample, 'color': _biosample_color[biosample], 'link':'biosample_term_name=' + biosample ,'label':biosample, 'name': biosample, 'type':'cell','biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    cell_check.append(biosample)
            for hit in row['inner_hits']['positions']['hits']['hits']:
                data_row = []
                chrom = '{}'.format(row['_index'])
                assembly = '{}'.format(row['_type'])
                start = int('{}'.format(hit['_source']['start']))
                stop = int('{}'.format(hit['_source']['end']))
                state = '{}'.format(hit['_source']['state'])
                new_state = re.sub(r'\d+[_]','',state) if re.match(r'\d+[_]', state) else state
                harmonized_state = _states_maps[new_state] if new_state in _states_maps else state
                val = '{}'.format(hit['_source']['val'])
                file_accession = file_json['accession']
                annotation_accession = annotation_json['accession']
                coordinates = '{}:{}-{}'.format(row['_index'], hit['_source']['start'], hit['_source']['end'])
                annotation = annotation_json['annotation_type']
                biosample_type = annotation_json['biosample_type']
                biosample_term = annotation_json['biosample_term_name']
                annotation_list = []
                state_list = []
                state_biosample = harmonized_state + '|' +biosample_term
                if state_biosample not in json_doc1:
                    json_doc1[state_biosample] = []
                    json_doc1[state_biosample].append(
                        annotation_accession
                        )
                else:
                    json_doc1[state_biosample].append(
                        annotation_accession
                        )
                if harmonized_state in _high_states or annotation == 'accessible chromatin' or annotation == 'variant allelic effects' or annotation == 'target gene predictions' or annotation == 'binding sites':
                    if biosample_term in biosample_term_list:
                        links = "&accession=".join(json_doc1[state_biosample])
                        accession_ids = ", ".join(json_doc1[state_biosample])
                        json_doc['nodes'].append({'path':query + '|' + biosample_term + '|' + harmonized_state, 'id':state_biosample, 'color': _biosample_color[biosample_term], 'link': 'accession=' + links, 'label': harmonized_state, 'name': json_doc1[state_biosample], 'type':'annotation', 'biosample':biosample_term, 'annotation_type':annotation, 'accession_ids':accession_ids}) 
                    elif biosample_term in pancreatic_cells:
                        links = "&accession=".join(json_doc1[state_biosample])
                        accession_ids = ", ".join(json_doc1[state_biosample])
                        json_doc['nodes'].append({'path':query + '|pancreas|' + biosample_term + '|' + harmonized_state, 'id':state_biosample, 'color': _biosample_color[biosample_term], 'link': 'accession=' + links, 'label': harmonized_state, 'name': json_doc1[state_biosample], 'type':'annotation', 'biosample':biosample_term, 'annotation_type':annotation, 'accession_ids':accession_ids})  
                    elif biosample_term in liver_cells:
                        links = "&accession=".join(json_doc1[state_biosample])
                        accession_ids = ", ".join(json_doc1[state_biosample])
                        json_doc['nodes'].append({'path':query + '|liver|' + biosample_term + '|' + harmonized_state, 'id':state_biosample, 'color': _biosample_color[biosample_term], 'link': 'accession=' + links, 'label': harmonized_state, 'name': json_doc1[state_biosample], 'type':'annotation', 'biosample':biosample_term, 'annotation_type':annotation, 'accession_ids':accession_ids})  
                    elif biosample_term in heart_tissues:
                        links = "&accession=".join(json_doc1[state_biosample])
                        accession_ids = ", ".join(json_doc1[state_biosample])
                        json_doc['nodes'].append({'path':query + '|heart|' + biosample_term + '|' + harmonized_state, 'id':state_biosample, 'color': _biosample_color[biosample_term], 'link': 'accession=' + links, 'label': harmonized_state, 'name': json_doc1[state_biosample], 'type':'annotation', 'biosample':biosample_term, 'annotation_type':annotation, 'accession_ids':accession_ids})
                #unique by id (aka. unique by same state & same tissue/cell)
                json_doc2['nodes'] = list({v['id']:v for v in json_doc['nodes']}.values())
    if 'variant_graph.json' in request.url:
        return Response(
            content_type='text/plain',
            body=json.dumps(json_doc2,indent=2,sort_keys=True),
        )

@view_config(route_name='variant_all_graph', request_method='GET')
def variant_all_graph(context, request):
    param_list = parse_qs(request.matchdict['search_params'])
    param_list['field'] = []
    param_list['limit'] = ['all']
    path = '/variant-search/?{}&{}'.format(urlencode(param_list, True),'referrer=peak_metadata')
    results = request.embed(path, as_user=True)
    uuids_in_results = get_file_uuids(results)
    rows = []
    json_doc = {}
    json_doc1 = {}
    json_doc2 = {}
    json_doc['nodes'] = []
    json_doc1['nodes'] = []
    json_doc2['nodes'] = []
    query = results['query']
    biosample_check = []
    cell_check = []
    json_doc['nodes'].append({'path':query,'id':query, 'color':'#170451', 'link':'region=' + query + '&genome=GRCh37','label':query, 'name': query, 'type':'rsid','biosample':'-', 'annotation_type':'-', 'accession_ids':'-'})
    for row in results['peaks']:
        if row['_id'] in uuids_in_results:
            file_json = request.embed(row['_id'])
            annotation_json = request.embed(file_json['dataset'])
            biosample = annotation_json['biosample_term_name']
            if biosample in biosample_term_list:
                if biosample not in biosample_check:
                    json_doc['nodes'].append({'path':query + '|' + biosample,'id':biosample, 'color': _biosample_color[biosample], 'link':'biosample_term_name=' + biosample ,'label':biosample, 'name': biosample, 'type':'biosample','biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    biosample_check.append(biosample)
            if biosample in pancreatic_cells:
                if 'pancreas' not in biosample_check:
                    json_doc['nodes'].append({'path':query + '|pancreas','id':'pancreas', 'color': _biosample_color['pancreas'], 'link':'biosample_term_name=pancreas', 'label':'pancreas', 'name': 'pancreas', 'type':'biosample','biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    biosample_check.append('pancreas')
                if biosample not in cell_check:
                    json_doc['nodes'].append({'path':query + '|pancreas|' + biosample,'id':'pancreas|'+biosample, 'color': _biosample_color[biosample], 'link':'biosample_term_name=' + biosample, 'label':biosample, 'name': biosample, 'type':'cell','biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    cell_check.append(biosample)
            elif biosample in liver_cells:
                if 'liver' not in biosample_check:
                    json_doc['nodes'].append({'path':query + '|liver','id':'liver', 'color': _biosample_color['liver'], 'link':'biosample_term_name=liver', 'label':'liver', 'name': 'liver', 'type':'biosample','biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    biosample_check.append('liver')
                if biosample not in cell_check:
                    json_doc['nodes'].append({'path':query + '|liver|' + biosample,'id':'liver|'+biosample, 'color': _biosample_color[biosample], 'link':'biosample_term_name=' + biosample ,'label':biosample, 'name': biosample, 'type':'cell','biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    cell_check.append(biosample)
            elif biosample in heart_tissues:
                if 'heart' not in biosample_check:
                    json_doc['nodes'].append({'path':query + '|heart','id':'heart', 'color': _biosample_color['heart'], 'link':'biosample_term_name=heart', 'label':'heart', 'name': 'heart', 'type':'biosample', 'biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    biosample_check.append('heart')
                if biosample not in cell_check:
                    json_doc['nodes'].append({'path':query + '|heart|' + biosample,'id':'heart|'+biosample, 'color': _biosample_color[biosample], 'link':'biosample_term_name=' + biosample ,'label':biosample, 'name': biosample, 'type':'cell', 'biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    cell_check.append(biosample)
            for hit in row['inner_hits']['positions']['hits']['hits']:
                data_row = []
                chrom = '{}'.format(row['_index'])
                assembly = '{}'.format(row['_type'])
                start = int('{}'.format(hit['_source']['start']))
                stop = int('{}'.format(hit['_source']['end']))
                state = '{}'.format(hit['_source']['state'])
                new_state = re.sub(r'\d+[_]','',state) if re.match(r'\d+[_]', state) else state
                harmonized_state = _states_maps[new_state] if new_state in _states_maps else state
                val = '{}'.format(hit['_source']['val'])
                file_accession = file_json['accession']
                annotation_accession = annotation_json['accession']
                coordinates = '{}:{}-{}'.format(row['_index'], hit['_source']['start'], hit['_source']['end'])
                annotation = annotation_json['annotation_type']
                biosample_type = annotation_json['biosample_type']
                biosample_term = annotation_json['biosample_term_name']
                annotation_list = []
                state_list = []
                state_biosample = harmonized_state + '|' +biosample_term
                if state_biosample not in json_doc1:
                    json_doc1[state_biosample] = []
                    json_doc1[state_biosample].append(
                        annotation_accession
                        )
                else:
                    json_doc1[state_biosample].append(
                        annotation_accession
                        )
                if biosample_term in biosample_term_list:
                    links = "&accession=".join(json_doc1[state_biosample])
                    accession_ids = ", ".join(json_doc1[state_biosample])
                    json_doc['nodes'].append({'path':query + '|' + biosample_term + '|' + harmonized_state, 'id':state_biosample, 'color': _biosample_color[biosample_term], 'link': 'accession=' + links, 'label': harmonized_state, 'name': json_doc1[state_biosample], 'type':'annotation', 'biosample':biosample_term, 'annotation_type':annotation, 'accession_ids':accession_ids}) 
                elif biosample_term in pancreatic_cells:
                    links = "&accession=".join(json_doc1[state_biosample])
                    accession_ids = ", ".join(json_doc1[state_biosample])
                    json_doc['nodes'].append({'path':query + '|pancreas|' + biosample_term + '|' + harmonized_state, 'id':state_biosample, 'color': _biosample_color[biosample_term], 'link': 'accession=' + links, 'label': harmonized_state, 'name': json_doc1[state_biosample], 'type':'annotation', 'biosample':biosample_term, 'annotation_type':annotation, 'accession_ids':accession_ids})  
                elif biosample_term in liver_cells:
                    links = "&accession=".join(json_doc1[state_biosample])
                    accession_ids = ", ".join(json_doc1[state_biosample])
                    json_doc['nodes'].append({'path':query + '|liver|' + biosample_term + '|' + harmonized_state, 'id':state_biosample, 'color': _biosample_color[biosample_term], 'link': 'accession=' + links, 'label': harmonized_state, 'name': json_doc1[state_biosample], 'type':'annotation', 'biosample':biosample_term, 'annotation_type':annotation, 'accession_ids':accession_ids})  
                elif biosample_term in heart_tissues:
                    links = "&accession=".join(json_doc1[state_biosample])
                    accession_ids = ", ".join(json_doc1[state_biosample])
                    json_doc['nodes'].append({'path':query + '|heart|' + biosample_term + '|' + harmonized_state, 'id':state_biosample, 'color': _biosample_color[biosample_term], 'link': 'accession=' + links, 'label': harmonized_state, 'name': json_doc1[state_biosample], 'type':'annotation', 'biosample':biosample_term, 'annotation_type':annotation, 'accession_ids':accession_ids})
                #unique by id (aka. unique by same state & same tissue/cell)
                json_doc2['nodes'] = list({v['id']:v for v in json_doc['nodes']}.values())
    if 'variant_all_graph.json' in request.url:
        return Response(
            content_type='text/plain',
            body=json.dumps(json_doc2,indent=2,sort_keys=True),
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
            log.warn(title)
            md5sum = f['md5sum']
            log.warn(md5sum)
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
        software = None if annotation_json.get("software_used")== None else annotation_json["software_used"][0]["software"]["title"]
        biosample_term_name = annotation_json['biosample_term_name']
        biosample_synonyms = annotation_json['biosample_synonyms'] if 'biosample_synonyms' in annotation_json else None
        system_slims = annotation_json['system_slims'] if 'system_slims' in annotation_json else None
        organ_slims = annotation_json['organ_slims'] if 'organ_slims' in annotation_json else None
        biosample_type = annotation_json['biosample_type']
        biosample_term_id = annotation_json['biosample_term_id'] if 'biosample_term_id' in annotation_json else None
        dbxrefs = annotation_json['dbxrefs'] 
        harmonized_states = varshney_chromhmm_states if dbxrefs == ['dbGaP:phs001188.v1.p1'] and dbxrefs != ['ENCODE:ENCSR123'] else None  if annotation_type != 'chromatin state' and dbxrefs != ['ENCODE:ENCSR123'] else roadmap_chromhmm_states  
        #harmonized_states = roadmap_chromhmm_states if annotation_type == 'chromatin state' and dbxrefs != ['ENCODE:ENCSR123'] else None  if annotation_type != 'chromatin state' and dbxrefs != ['ENCODE:ENCSR123'] else varshney_chromhmm_states  
        if files:
            if annotation_type not in json_doc:
                json_doc[annotation_type] = []
                json_doc[annotation_type].append({
                    'annotation_type': annotation_type,
                    'annotation_id': annotation_id,
                    'dbxrefs': dbxrefs,
                    'biosample_term_id': biosample_term_id,
                    'biosample_term_name': biosample_term_name,
                    'biosample_synonyms': biosample_synonyms,
                    'biosample_type': biosample_type,
                    'organ_slims': organ_slims,
                    'system_slims': system_slims,
                    'harmonized_states': harmonized_states,
                    'file_download': files,
                    'annotation_method': software
                })  
            else:
                json_doc[annotation_type].append({
                    'annotation_type': annotation_type,
                    'annotation_id': annotation_id,
                    'dbxrefs': dbxrefs,
                    'biosample_term_id': biosample_term_id,
                    'biosample_term_name': biosample_term_name,
                    'biosample_synonyms': biosample_synonyms,
                    'biosample_type': biosample_type,
                    'organ_slims': organ_slims,
                    'system_slims':system_slims,
                    'harmonized_states': harmonized_states,
                    'file_download': files,
                    'annotation_method': software
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
