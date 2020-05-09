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
    config.add_route('variant_graph', '/variant_graph/{search_params}/{json}')
    config.add_route('variant_graph_all', '/variant_graph_all/{search_params}/{json}')
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
    'right lobe of liver': '#ffd700',
    'Liver fetal (hepatocyte)': '#ffd700',
    'hepatocyte': '#ffd700',
    'islet of Langerhans':'#8b0000',
    'pancreas':'#8b0000',
    'pancreatic alpha cell': '#8b0000',
    'pancreatic beta cell': '#8b0000',
    'pancreatic delta cell': '#8b0000',
    'pancreatic stellate cell':'#8b0000',
    'pancreatic acinar cell':'#8b0000',
    'pancreatic ductal cell':'#8b0000',
    'pancreatic polypeptide-secreting cell':'#8b0000',
    'Pancreatic progenitors (progenitor cell of endocrine pancreas)': '#8b0000',
    'EndoC_BH1': '#8b0000',
    'adipocyte': '#f98900',
    'Adipose SGBS cell line (adipocyte)': '#f98900',
    'Preadipose SGBS cell line (adipocyte)': '#f98900',
    'subcutaneous adipose tissue': '#66ffff',
    'omental fat pad': '#66ffff',
    'adipose tissue': '#66ffff',
    'skeletal muscle myoblast':'#2c5e8d',
    'gastrocnemius medialis(Muscle - Skeletal)':'#1a5353',
    'heart':'#ff0000',
    'aorta': '#ff0000',
    'heart left ventricle':'#ff0000',
    'heart right ventricle':'#ff0000',
    'right cardiac atrium':'#ff0000',
    'Heart fetal (cardiac muscle cell)':'#ff0000',
    'coronary artery':'#ff0000',
    'ascending aorta':'#ff0000',    
    'cardiac fibroblast':'#ff0000',
    'cardiac precursors (cardiac muscle cell)':'#ff0000',
    'cardiomyocytes (cardiac muscle cell)':'#ff0000',
    'cardiac muscle cell':'#ff0000',
    'kidney':'#7fff00',
    'kidney epithelial cell':'#7fff00',
    'left kidney':'#7fff00',
    'renal cortical epithelial cell':'#7fff00',
    'glomerular endothelial cell':'#7fff00',
    'glomerular visceral epithelial cell':'#7fff00',
    'epithelial cell of proximal tubule':'#7fff00',
    'brain':'#ff00ff',
    'frontal cortex':'#ff00ff',
    'dorsolateral prefrontal cortex(Brain - Frontal Cortex (BA9))':'#ff00ff',
    'brain microvascular endothelial cell':'#ff00ff',
    'brain pericyte':'#ff00ff',
    'cerebellum (Hemisphere)':'#ff00ff',
    'cerebellum':'#ff00ff',
    'astrocyte of the cerebellum':'#ff00ff',
    "Ammon's horn(Hippocampus)":'#ff00ff',
    'astrocyte of the hippocampus':'#ff00ff',
    'putamen':'#ff00ff',
    'substantia nigra':'#ff00ff',
    'amygdala':'#ff00ff',
    'anterior cingulate cortex':'#ff00ff',
    'hypothalamus':'#ff00ff',
    'nucleus accumbens':'#ff00ff',
    'temporal lobe':'#ff00ff',
    'angular gyrus':'#ff00ff',
    'occipital lobe':'#ff00ff',
    'tibial nerve':'#d6d1d1',
    'naive thymus-derived CD8-positive, alpha-beta T cell':'#d6d1d1',
    'B cell':'#d6d1d1',
    'memory B cell':'#d6d1d1',
    'natural killer cell':'#d6d1d1',
    'regulatory T cell':'#d6d1d1',
    'retina':'#d6d1d1',
    'muscle of leg':'#d6d1d1',
    'CD4-positive, alpha-beta T cell':'#d6d1d1',
    'activated CD4-positive, alpha-beta T cell':'#d6d1d1',
    'macrophage':'#d6d1d1',
    'megakaryocyte':'#d6d1d1',
    'naive B cel':'#d6d1d1',
    'naive thymus-derived CD4-positive, alpha-beta T cell':'#d6d1d1',
    'non-classical monocyte':'#d6d1d1',
    'plasmacytoid dendritic cell':'#d6d1d1',
    'psoas muscle':'#d6d1d1',
    'thoracic aorta':'#d6d1d1',
    'hindlimb muscle':'#d6d1d1',
    'retinal pigment epithelial cell':'#d6d1d1',
    'ESC derived cell line':'#d6d1d1',
    'T follicular helper cell':'#d6d1d1',
    'T-helper 1 cell':'#d6d1d1',
    'T-helper 1cell':'#d6d1d1',
    'T-helper cell':'#d6d1d1',
    'activated CD8-positive, alpha-beta T cell':'#d6d1d1',
    'tibial artery':'#d6d1d1',
    'omental fat pad':'#d6d1d1',
    'CD8-positive, alpha-beta T cell':'#d6d1d1',
    'endothelial cell of umbilical vein':'#d6d1d1',
    'monocyte':'#d6d1d1',
    'C1 segment of cervical spinal cord':'#d6d1d1',
    'left ventricle myocardium':'#d6d1d1',
    'caudate nucleus':'#d6d1d1',
}
biosample_term_list = ['tibial nerve', 'naive thymus-derived CD8-positive, alpha-beta T cell', 'B cell', 'memory B cell', 'natural killer cell', 'regulatory T cell', 'retina', 'muscle of leg', 'CD4-positive, alpha-beta T cell', 'activated CD4-positive, alpha-beta T cell', 'macrophage', 'megakaryocyte', 'naive B cel', 'naive thymus-derived CD4-positive, alpha-beta T cell', 'non-classical monocyte', 'plasmacytoid dendritic cell', 'psoas muscle', 'thoracic aorta', 'hindlimb muscle', 'retinal pigment epithelial cell', 'ESC derived cell line', 'T follicular helper cell', 'T-helper 1 cell', 'T-helper 1cell', 'T-helper cell', 'activated CD8-positive, alpha-beta T cell', 'tibial artery', 'omental fat pad', 'CD8-positive, alpha-beta T cell', 'endothelial cell of umbilical vein', 'monocyte', 'C1 segment of cervical spinal cord', 'left ventricle myocardium', 'caudate nucleus', 'kidney epithelial cell', 'kidney', 'left kidney', 'renal cortical epithelial cell', 'glomerular endothelial cell', 'glomerular visceral epithelial cell', 'epithelial cell of proximal tubule', 'skeletal muscle myoblast', 'gastrocnemius medialis(Muscle - Skeletal)', 'Adipose SGBS cell line (adipocyte)', 'adipocyte', 'Preadipose SGBS cell line (adipocyte)', 'subcutaneous adipose tissue', 'omental fat pad', 'adipose tissue', 'skeletal muscle myoblast', 'gastrocnemius medialis(Muscle - Skeletal)']
pancreatic_cells = ['Pancreatic progenitors (progenitor cell of endocrine pancreas)', 'pancreas', 'islet of Langerhans', 'pancreatic beta cell', 'pancreatic alpha cell', 'pancreatic acinar cell', 'pancreatic delta cell', 'pancreatic ductal cell', 'pancreatic polypeptide-secreting cell', 'pancreatic stellate cell', 'EndoC_BH1']
heart_tissues =['heart', 'heart left ventricle', 'heart right ventricle', 'Heart fetal (cardiac muscle cell)', 'coronary artery', 'cardiac fibroblast', 'cardiac precursors (cardiac muscle cell)', 'cardiomyocytes (cardiac muscle cell)', 'right cardiac atrium', 'cardiac muscle cell', 'ascending aorta','aorta']
brain_tissues = ['frontal cortex', 'dorsolateral prefrontal cortex(Brain - Frontal Cortex (BA9))', 'brain microvascular endothelial cell', 'brain pericyte', 'cerebellum (Hemisphere)', 'cerebellum', 'astrocyte of the cerebellum', "Ammon's horn(Hippocampus)", 'astrocyte of the hippocampus', 'putamen', 'substantia nigra', 'amygdala', 'anterior cingulate cortex', 'hypothalamus', 'nucleus accumbens', 'temporal lobe', 'angular gyrus', 'occipital lobe' ]
liver_cells =  ['liver', 'right lobe of liver', 'Liver fetal (hepatocyte)', 'HepG2', 'hepatocyte']

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
            elif biosample in brain_tissues:
                if 'brain' not in biosample_check:
                    json_doc['nodes'].append({'path':query + '|brain','id':'brain', 'color': _biosample_color['brain'], 'link':'biosample_term_name=brain', 'label':'brain', 'name': 'brain', 'type':'biosample','type':'biosample', 'biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    biosample_check.append('brain')
                if biosample not in cell_check:
                    json_doc['nodes'].append({'path':query + '|brain|' + biosample,'id':'brain|'+biosample, 'color': _biosample_color[biosample], 'link':'biosample_term_name=' + biosample ,'label':biosample, 'name': biosample, 'type':'cell','biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
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
                if harmonized_state in _high_states or annotation == 'accessible chromatin' or annotation == 'variant allelic effects' or annotation == 'Coaccessible target genes' or annotation == 'Chromatin interaction target genes' or annotation == 'binding sites':
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
                    elif biosample_term in brain_tissues:
                        links = "&accession=".join(json_doc1[state_biosample])
                        accession_ids = ", ".join(json_doc1[state_biosample])
                        json_doc['nodes'].append({'path':query + '|brain|' + biosample_term + '|' + harmonized_state, 'id':state_biosample, 'color': _biosample_color[biosample_term], 'link': 'accession=' + links, 'label': harmonized_state, 'name': json_doc1[state_biosample], 'type':'annotation', 'biosample':biosample_term, 'annotation_type':annotation, 'accession_ids':accession_ids})
                #unique by id (aka. unique by same state & same tissue/cell)
                json_doc2['nodes'] = list({v['id']:v for v in json_doc['nodes']}.values())
    if 'variant_graph.json' in request.url:
        return Response(
            content_type='text/plain',
            body=json.dumps(json_doc2,indent=2,sort_keys=True),
        )

@view_config(route_name='variant_graph_all', request_method='GET')
def variant_graph_all(context, request):
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
            elif biosample in brain_tissues:
                if 'brain' not in biosample_check:
                    json_doc['nodes'].append({'path':query + '|brain','id':'brain', 'color': _biosample_color['brain'], 'link':'biosample_term_name=brain', 'label':'brain', 'name': 'brain', 'type':'biosample','type':'biosample', 'biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
                    biosample_check.append('brain')
                if biosample not in cell_check:
                    json_doc['nodes'].append({'path':query + '|brain|' + biosample,'id':'brain|'+biosample, 'color': _biosample_color[biosample], 'link':'biosample_term_name=' + biosample ,'label':biosample, 'name': biosample, 'type':'cell','biosample':biosample, 'annotation_type':'-', 'accession_ids':'-'})
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
                elif biosample_term in brain_tissues:
                    links = "&accession=".join(json_doc1[state_biosample])
                    accession_ids = ", ".join(json_doc1[state_biosample])
                    json_doc['nodes'].append({'path':query + '|brain|' + biosample_term + '|' + harmonized_state, 'id':state_biosample, 'color': _biosample_color[biosample_term], 'link': 'accession=' + links, 'label': harmonized_state, 'name': json_doc1[state_biosample], 'type':'annotation', 'biosample':biosample_term, 'annotation_type':annotation, 'accession_ids':accession_ids})
                #unique by id (aka. unique by same state & same tissue/cell)
                json_doc2['nodes'] = list({v['id']:v for v in json_doc['nodes']}.values())
    if 'variant_graph_all.json' in request.url:
        return Response(
            content_type='text/plain',
            body=json.dumps(json_doc2,indent=2,sort_keys=True),
        )
