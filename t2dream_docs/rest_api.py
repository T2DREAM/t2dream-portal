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
    config.add_route('variant_graph_new', '/variant_graph_new/{search_params}/{json}')
    config.add_route('variant_all_graph', '/variant_all_graph/{search_params}/{json}')
    config.add_route('target_gene_matrix', '/target_gene_matrix/{search_params}/{json}')
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
    ('Status', ['status']),
    ('Collection Tags',  ['collection_tags']),
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
    "pancreatic alpha cell":"#add8e6",
    "pancreatic beta cell":"#add8e6",
    "pancreatic delta cell":"#add8e6",
    "pancreatic acinar cell":"#add8e6",
    "pancreatic ductal cell":"#add8e6",
    "pancreatic polypeptide-secreting cell":"#add8e6",
    "pancreatic stellate cell":"#add8e6",
    "pancreas":"#add8e6",
    "EndoC_BH1":"#add8e6",
    "islet of Langerhans": "#add8e6",
    "liver": "#ff7f50",
    "HepG2": "#ff7f50",
    "heart left ventricle": "#ff0000",
    "heart right ventricle": "#ff0000",
    "heart": "#ff0000",
    "right cardiac atrium": "#ff0000",
    "adipose tissue": "#654321",
    "white adipose cell": "#654321",
    "psoas muscle" : "#8b0000",
    "cardiomyocytes (cardiac muscle cell)" : "#8b0000",
    "cardiac precursors (cardiac muscle cell)" : "#8b0000",
    "Ammon's horn": "#ffd700", 
    "dorsolateral prefrontal cortex": "#ffd700",
    "aorta": "#66ffff",
    "endothelial cell of umbilical vein": "#66ffff",
   "lung": "#d6d1d1",
    "CD4-positive, alpha-beta T cell": "#d6d1d1",
    "CD8-positive, alpha-beta T cell": "#d6d1d1",
    "activated CD4-positive, alpha-beta T cell": "#d6d1d1",
    "macrophage": "#d6d1d1",
    "lymphocyte of B lineage (iPSC)": "#d6d1d1",
    "megakaryocyte": "#d6d1d1",
    "monocyte": "#d6d1d1",
    "naive thymus-derived CD4-positive, alpha-beta T cell": "#d6d1d1",
    "naive thymus-derived CD8-positive, alpha-beta T cell": "#d6d1d1",
    "B cell": "#d6d1d1",
    "B-lymphoblastoid cell line": "#d6d1d1",
    "activated CD8-positive, alpha-beta T cell": "#d6d1d1",
    "adult endothelial progenitor cell": "#d6d1d1",
    "alternatively activated macrophage": "#d6d1d1",
    "bladder (urinary bladder)": "#d6d1d1",
    "conventional dendritic cell": "#d6d1d1",
    "embryonic stem cell": "#d6d1d1",
    "endothelial cell": "#d6d1d1",
    "erythroblast": "#d6d1d1",
    "esophagus": "#d6d1d1",
    "fibroblast cell line": "#d6d1d1",
    "gastric (mucosa of stomach)": "#d6d1d1",
    "inflammatory macrophage": "#d6d1d1",
    "memory B cell": "#d6d1d1",
    "mesenchymal stem cell": "#d6d1d1",
    "mesendoderm": "#d6d1d1",
    "naive B cel": "#d6d1d1",
    "naive B cell": "#d6d1d1",
    "natural killer cell": "#d6d1d1",
    "natural killer cell mediated cytotoxicity": "#d6d1d1",
    "neural progenitor cell (neural stem cell)": "#d6d1d1",
    "neutrophil": "#d6d1d1",
    "non-classical monocyte": "#d6d1d1",
    "ovary": "#d6d1d1",
    "plasmacytoid dendritic cell": "#d6d1d1",
    "regulatory T cell": "#d6d1d1",
    "sigmoid colon": "#d6d1d1",
    "small intestine": "#d6d1d1",
    "spleen": "#d6d1d1",
    "stellate neuron": "#d6d1d1",
    "trophoblast": "#d6d1d1",
    "adrenal gland": "#d6d1d1",
    "thymus": "#d6d1d1"
}
biosample_term_list = ["pancreatic alpha cell", "pancreatic beta cell", "pancreatic delta cell", "pancreatic acinar cell", "pancreatic ductal cell", "pancreatic polypeptide-secreting cell", "pancreatic stellate cell", "pancreas", "EndoC_BH1", "islet of Langerhans", "liver", "HepG2", "heart left ventricle", "heart right ventricle", "heart", "right cardiac atrium", "adipose tissue", "white adipose cell", "psoas muscle", "cardiomyocytes (cardiac muscle cell)", "cardiac precursors (cardiac muscle cell)", "Ammon's horn", "dorsolateral prefrontal cortex", "aorta", "endothelial cell of umbilical vein", "lung", "CD4-positive, alpha-beta T cell", "CD8-positive, alpha-beta T cell", "activated CD4-positive, alpha-beta T cell", "macrophage", "lymphocyte of B lineage (iPSC)", "megakaryocyte", "monocyte", "naive thymus-derived CD4-positive, alpha-beta T cell", "naive thymus-derived CD8-positive, alpha-beta T cell", "B cell", "B-lymphoblastoid cell line", "activated CD8-positive, alpha-beta T cell", "adult endothelial progenitor cell", "alternatively activated macrophage", "bladder (urinary bladder)", "conventional dendritic cell", "embryonic stem cell", "endothelial cell", "erythroblast", "esophagus", "fibroblast cell line", "gastric (mucosa of stomach)", "inflammatory macrophage", "memory B cell", "mesenchymal stem cell", "mesendoderm", "naive B cel", "naive B cell", "natural killer cell", "natural killer cell mediated cytotoxicity", "neural progenitor cell (neural stem cell)", "neutrophil", "non-classical monocyte", "ovary", "plasmacytoid dendritic cell", "regulatory T cell", "sigmoid colon", "small intestine", "spleen", "stellate neuron", "trophoblast", "adrenal gland", "thymus"]

matrix_biosample = ["pancreatic alpha cell" , "pancreatic beta cell" , "pancreatic delta cell" , "pancreatic acinar cell" , "pancreatic ductal cell" , "pancreatic polypeptide-secreting cell" , "pancreatic stellate cell" , "pancreas" , "EndoC_BH1" , "islet of Langerhans" , "liver" , "HepG2" , "heart left ventricle" , "heart right ventricle" , "heart" , "right cardiac atrium" , "adipose tissue" , "white adipose cell" , "psoas muscle" , "cardiomyocytes (cardiac muscle cell)" , "cardiac precursors (cardiac muscle cell)" , "Ammon's horn" , "dorsolateral prefrontal cortex" , "aorta" , "endothelial cell of umbilical vein"]

variant_allelic_effects = ['variant allelic effects']
EQTL = ['eQTL']
accessible_chromatin = ['accessible chromatin']
allelic_effect_accessible_chromatin = ['variant allelic effects', 'accessible chromatin']
target_gene_prediction_annotation = ['target gene predictions']
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
@view_config(route_name='variant_graph_new', request_method='GET')
def variant_graph_new(context, request):
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
    json_doc3 = {}
    json_doc4 = {}
    json_doc5 = {}
    json_doc6 = {}
    json_doc['nodes'] = []
    json_doc1['nodes'] = []
    json_doc2['nodes'] = []
    json_doc['links'] = []
    json_doc2['links'] = []
    json_doc3['new_state'] = []
    query = results['query']
    biosample_check = []
    biosamples_annotation_allelic = {}
    biosamples_annotation_accessible = {}
    biosamples_annotation_both = {}
    biosample_annotation = {}
    variant_coordinates = results['coordinates']
    #variant node
    json_doc['nodes'].append({'path':query,'id':query, 'color':'LightGrey', 'link':'region=' + query + '&genome=GRCh37','label':query, 'name': query, 'type':'rsid','biosample':'-', 'annotation_type':'-', 'accession_ids':'-', 'level': 1, 'state_len': 1.5, 'score': None, 'distance': None})
    for row in results['peaks']:
        if row['_id'] in uuids_in_results:
            file_json = request.embed(row['_id'])
            annotation_json = request.embed(file_json['dataset'])
            biosample = annotation_json['biosample_term_name']
            annotation = annotation_json['annotation_type']
            if annotation in variant_allelic_effects:
                if annotation in accessible_chromatin:
                    if biosample not in biosamples_annotation_both:
                        biosamples_annotation_both[biosample] = []
                        biosamples_annotation_both[biosample].append(
                            annotation
                        )
                    else:
                        biosamples_annotation_both[biosample].append(
                            annotation
                        )
            if annotation in variant_allelic_effects:
                if biosample not in biosamples_annotation_allelic:
                    biosamples_annotation_allelic[biosample] = []
                    biosamples_annotation_allelic[biosample].append(
                        annotation
                    )
                else:
                    biosamples_annotation_allelic[biosample].append(
                        annotation
                    )
            if annotation in accessible_chromatin:
                if biosample not in biosamples_annotation_accessible:
                    biosamples_annotation_accessible[biosample] = []
                    biosamples_annotation_accessible[biosample].append(
                        annotation
                    )
                else:
                    biosamples_annotation_accessible[biosample].append(
                        annotation
                    )
    #biosample node
    for row in results['peaks']:
        if row['_id'] in uuids_in_results:
            file_json = request.embed(row['_id'])
            annotation_json = request.embed(file_json['dataset'])
            biosample = annotation_json['biosample_term_name']
            annotation = annotation_json['annotation_type']
            if annotation in target_gene_prediction_annotation:
                if biosample in biosample_term_list:
                    if biosample not in biosample_check:
                        link_color = '#003399' if biosample in biosamples_annotation_allelic and biosamples_annotation_accessible else '#bfcce6' if biosample in biosamples_annotation_allelic else '#738fc7' if biosample in biosamples_annotation_accessible else '#BEBEBE'
                        link = 'biosample_term_name=' + biosample
                        label = 'allelic effect & accessible chromatin' if biosample in biosamples_annotation_allelic and biosamples_annotation_accessible else 'allelic effect' if biosample in biosamples_annotation_allelic else 'accessible chromatin' if biosample in biosamples_annotation_accessible else None
                        width = 3 if biosample in biosamples_annotation_allelic and biosamples_annotation_accessible else 3 if biosample in biosamples_annotation_allelic else 3 if biosample in biosamples_annotation_accessible else 1
                        json_doc['nodes'].append({'path': biosample, 'id': biosample, 'color': _biosample_color[biosample], 'link': 'biosample_term_name=' + biosample ,'label': biosample, 'name': biosample, 'type': 'biosample', 'biosample': biosample, 'annotation_type': '-', 'accession_ids': '-', "level": 2, 'state_len': 1, 'score': None, 'distance': None})
                        json_doc['links'].append({'source': query, 'target': biosample, 'id': query + biosample, 'link_color': link_color, 'length': 30, 'linkout': link, 'label': label, 'width': width})
                        biosample_check.append(biosample)
            for hit in row['inner_hits']['positions']['hits']['hits']:
                data_row = []
                chrom = '{}'.format(row['_index'])
                assembly = '{}'.format(row['_type'])
                start = int('{}'.format(hit['_source']['start']))
                stop = int('{}'.format(hit['_source']['end']))
                state = '{}'.format(hit['_source']['state'])
                new_state = state.split('_', 1)[-1].replace('.', '').upper()
                val = '{}'.format(hit['_source']['val'])
                file_accession = file_json['accession']
                annotation_accession = annotation_json['accession']
                coordinates = '{}:{}-{}'.format(row['_index'], hit['_source']['start'], hit['_source']['end'])
                annotation = annotation_json['annotation_type']
                biosample_type = annotation_json['biosample_type']
                biosample_term = annotation_json['biosample_term_name']
                annotation_list = []
                state_list = []
                new_state_annotation = new_state + '|' + annotation_accession
                state_biosample = new_state + '|' +biosample_term
                software = 'None' if annotation_json.get("software_used")== None else annotation_json["software_used"][0]["software"]["description"]
                score = 'None' if annotation_json.get("val")==None  else val
                #software_accession_score = software + annotation_accession + score 
                if annotation in target_gene_prediction_annotation:
                    if new_state not in json_doc1:
                        json_doc1[new_state] = []
                        json_doc1[new_state].append(
                            annotation_accession
                        )
                    else:
                        json_doc1[new_state].append(
                            annotation_accession
                        )
                    if new_state not in json_doc3:
                        json_doc3[new_state] = []
                        json_doc3[new_state].append(
                            new_state_annotation
                        )
                    else:
                        json_doc3[new_state].append(
                            new_state_annotation
                        )
                    if new_state not in json_doc4:
                        json_doc4[new_state] = []
                        json_doc4[new_state].append(
                            annotation
                        )
                    else:
                        json_doc4[new_state].append(
                            annotation
                        )
                    if new_state not in json_doc5:
                        json_doc5[new_state] = []
                        json_doc5[new_state].append(
                            val
                        )
                    else:
                        json_doc5[new_state].append(
                            val
                        )
            for hit in row['inner_hits']['positions']['hits']['hits']:
                annotation = annotation_json['annotation_type']
                if annotation in target_gene_prediction_annotation:
                    data_row = []
                    chrom = '{}'.format(row['_index'])
                    assembly = '{}'.format(row['_type'])
                    start = int('{}'.format(hit['_source']['start']))
                    stop = int('{}'.format(hit['_source']['end']))
                    state = '{}'.format(hit['_source']['state'])
                    new_state = state.split('_', 1)[-1].replace('.', '').upper()
                    val = '{}'.format(hit['_source']['val'])
                    file_accession = file_json['accession']
                    annotation_accession = annotation_json['accession']
                    coordinates = '{}:{}-{}'.format(row['_index'], hit['_source']['start'], hit['_source']['end'])
                    annotation = annotation_json['annotation_type']
                    biosample_type = annotation_json['biosample_type']
                    biosample_term = annotation_json['biosample_term_name']
                    annotation_list = []
                    state_list = []
                    new_state_annotation = new_state + '|' + annotation_accession
                    state_biosample = new_state + '|' +biosample_term
                    target_gene_accession = list(set(json_doc1[new_state]))
                    method = list(set(json_doc4[new_state]))
                    #target gene predictions
                    if new_state not in json_doc6:
                        json_doc6[new_state] = []
                        json_doc6[new_state].append(
                            state.split(':', 1)[1]
                            )
                    else:
                        json_doc6[new_state].append(
                            state.split(':', 1)[1]
                            )
                    promoter = json_doc6[new_state]
                    variant_gene_coordinates = variant_coordinates.split(':', 1)[1]
                    variant_gene_first_coordinate = variant_gene_coordinates.split('-')[0]
                    target_gene_first_coordinate = [i.split('-')[0] for i in promoter]
                    distances = [str(abs(int(i) - int(variant_gene_first_coordinate))) for i in target_gene_first_coordinate]
                    distance = ", ".join(distances)
                    if biosample_term in biosample_term_list:
                        state_count = (len(set(json_doc3[new_state])))
                        #state_len = state_count + 0.7 if state_count <= 2 else 3.1 
                        state_len = 2
                        links = "&accession=".join(target_gene_accession)
                        accession_ids = ", ".join(target_gene_accession)
                        method = ", ".join(method)
                        score = ", ".join(json_doc5[new_state])
                        state_color = '#FFC0CB' if state_count == 1 else '#FF69B4' if state_count == 2 else '#DB7093' if state_count == 3 else '#C71585' 
                        link_color = '#BEBEBE'
                        json_doc['nodes'].append({'path': new_state, 'id': new_state, 'color': state_color, 'link': 'accession=' + links, 'label': new_state, 'name': 'accession: ' + accession_ids + '\n' + 'evidence: ' + method + '\n' + 'score: ' + score + '\n' +'distance: ' + distance,  'type':'annotation', 'biosample': biosample_term, 'annotation_type': annotation, 'accession_ids': accession_ids, 'level': 3, 'state_len': state_len, 'score': val, 'distance': distance}) 
                        json_doc['links'].append({'source': biosample, 'link_color':link_color, 'target': new_state, 'id': biosample + new_state, 'length': 50, 'link':None, 'label': None, 'width': 1})
                #unique by id (aka. unique by same state & same tissue/cell)
                json_doc2['nodes'] = list({v['id']:v for v in json_doc['nodes']}.values())
                #unique by source
                json_doc2['links'] = list({v['id']:v for v in json_doc['links']}.values())
    if 'variant_graph_new.json' in request.url:
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
    json_doc3 = {}
    json_doc['nodes'] = []
    json_doc1['nodes'] = []
    json_doc2['nodes'] = []
    json_doc3['nodes'] = []
    query = results['query']
    biosample_check = []
    for row in results['peaks']:
        if row['_id'] in uuids_in_results:
            file_json = request.embed(row['_id'])
            annotation_json = request.embed(file_json['dataset'])
            biosample = annotation_json['biosample_term_name']
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
                #annotation_accession_score = annotation_accession + '(' + val + ')' 
                if state_biosample not in json_doc1:
                    json_doc1[state_biosample] = []
                    json_doc1[state_biosample].append(
                        annotation_accession
                        )
                else:
                    json_doc1[state_biosample].append(
                        annotation_accession
                        )
                if state_biosample not in json_doc3:
                    json_doc3[state_biosample] = []
                    json_doc3[state_biosample].append(
                        val
                        )
                else:
                    json_doc3[state_biosample].append(
                        val
                        )
                accession_ids = ", ".join(json_doc1[state_biosample])
                score = ",".join(json_doc3[state_biosample])
                table_id = state + ',' + biosample_term + ',' + annotation +  ',' + accession_ids
                if harmonized_state in _high_states or annotation == 'accessible chromatin' or annotation == 'variant allelic effects' or annotation == 'Coaccessible target genes' or annotation == 'Chromatin interaction target genes' or annotation == 'binding sites' or annotation == 'gene expression' or annotation == 'eQTL':
                    if biosample_term in biosample_term_list:                    
                        links = "&accession=".join(json_doc1[state_biosample])
                        accession_ids = ", ".join(json_doc1[state_biosample])
                        score = ",".join(json_doc3[state_biosample])
                        json_doc['nodes'].append({'id':state_biosample, 'link': 'accession=' + links, 'label': state, 'biosample':biosample_term, 'annotation_type':annotation, 'accession_ids':accession_ids, 'table_id': table_id, 'score': score }) 
                #unique by id (aka. unique by same state & same tissue/cell)
                json_doc2['nodes'] = list({v['id']:v for v in json_doc['nodes']}.values())
    if 'variant_all_graph.json' in request.url:
        return Response(
            content_type='text/plain',
            body=json.dumps(json_doc2,indent=2,sort_keys=True),
        )
@view_config(route_name='target_gene_matrix', request_method='GET')
def target_gene_matrix(context, request):
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
    json_doc3 = {}
    json_doc['matrix'] = []
    json_doc1['matrix'] = []
    json_doc2['matrix'] = []
    json_doc3['matrix'] = []
    query = results['query']
    biosample_check = []
    #variant_coordinates = results['coordinates']
    for row in results['peaks']:
        if row['_id'] in uuids_in_results:
            file_json = request.embed(row['_id'])
            annotation_json = request.embed(file_json['dataset'])
            biosample = annotation_json['biosample_term_name']
            annotation = annotation_json['annotation_type']
            #if annotation in target_gene_prediction_annotation:
            #    json_doc3['matrix'].append(biosample)
    for row in results['peaks']:
        if row['_id'] in uuids_in_results:
            file_json = request.embed(row['_id'])
            annotation_json = request.embed(file_json['dataset'])
            biosample = annotation_json['biosample_term_name']
            annotation = annotation_json['annotation_type']
            for hit in row['inner_hits']['positions']['hits']['hits']:
                data_row = []
                state = '{}'.format(hit['_source']['state'])
                new_state = state.split('_', 1)[-1].replace('.', '').upper()
                biosample_term = annotation_json['biosample_term_name']
                if annotation in target_gene_prediction_annotation:
                    if new_state not in json_doc1:
                        json_doc1[new_state] = []
                        json_doc1[new_state].append(
                            biosample_term
                        )
                    else:
                        json_doc1[new_state].append(
                            biosample_term
                        )
            for hit in row['inner_hits']['positions']['hits']['hits']:
                annotation = annotation_json['annotation_type']
                if annotation in target_gene_prediction_annotation:
                    data_row = []
                    state = '{}'.format(hit['_source']['state'])
                    new_state = state.split('_', 1)[-1].replace('.', '').upper()
                    biosample_term = annotation_json['biosample_term_name']
                    state_biosample = new_state + '|' +biosample_term
                    biosample_gene = json_doc1[new_state]
                    #target gene predictions                                                                                                            
                    if biosample_term in matrix_biosample:
                        json_doc['matrix'].append({'id': new_state, 'gene': new_state, 'biosamples': biosample_gene})
                #unique by id (aka. unique by same state & same tissue/cell)                                                                                          
                json_doc2['matrix'] = list({v['id']:v for v in json_doc['matrix']}.values())
    if 'target_gene_matrix.json' in request.url:
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
            #log.warn(title)
            md5sum = f['md5sum']
            #log.warn(md5sum)
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
        dataset_status = annotation_json['status']
        collection_tags = None if annotation_json.get('collection_tags')== None else annotation_json['collection_tags']
        software = None if annotation_json.get("software_used")== None else annotation_json["software_used"][0]["software"]["title"]
        biosample_term_name = annotation_json.get("biosample_term_name", None)
        biosample_synonyms = annotation_json['biosample_synonyms'] if 'biosample_synonyms' in annotation_json else None
        system_slims = annotation_json['system_slims'] if 'system_slims' in annotation_json else None
        organ_slims = annotation_json['organ_slims'] if 'organ_slims' in annotation_json else None
        biosample_type = annotation_json.get("biosample_type", None)
        #log.warn(biosample_type)
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
                    'annotation_method': software,
                    'dataset_status': dataset_status,
                    'collection_tags': collection_tags
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
                    'annotation_method': software,
                    'dataset_status': status,
                    'collection_tags': collection_tags
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
