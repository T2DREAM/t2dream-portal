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
    config.add_route('region_metadata', '/region_metadata/{search_params}/{tsv}')
    config.add_route('experiment_metadata', '/experiment_metadata/{search_params}/{json}')
    config.add_route('annotation_metadata', '/annotation_metadata/{search_params}/{tsv}')
    config.add_route('annotation_registry_metadata', '/annotation_registry_metadata/{search_params}/{tsv}')
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
    ('Annotation Category', ['annotation_category']),
    ('Assay Type', ['annotation_type_category']),
    ('Status', ['status']),
    ('Version', ['schema_version']),
    ('Collection Tags',  ['collection_tags']),
    ('Knowledge Portal Tissue Category', ['portal_tissue']),
    ('KP usage', ['portal_usage']),
    ('Tissue term id', ['tissue_term_id']),
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
    ('RFA', ['award.rfa']),
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
    ('Laboratory', ['lab.name']),
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
    ('Annotation Source', ['annotation_source']),
    ('Publications', ['references']),
    ('references_title',['references.title']),
    ('references_identifiers',['references.identifiers']), 
    ('File Status', ['files.status']),
    ('Documents Status', ['documents.status']),
    ('documents_uuid', ['documents.uuid']),
    ('Documents Description', ['documents.description']),
    ('documents_md5sum', ['documents.attachment.md5sum']),
    ('documents_href', ['documents.attachment.href'])
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
variant_allelic_effects = ['variant allelic effects']
EQTL = ['eQTL']
accessible_chromatin = ['accessible chromatin']
allelic_effect_accessible_chromatin = ['variant allelic effects', 'accessible chromatin']
target_gene_prediction_annotation = ['target gene predictions', 'Coaccessible target genes']
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
                state = '{}'.format(hit['_source']['state_annotation'])
                val = '{}'.format(hit['_source']['value_annotation'])
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
                state = '{}'.format(hit['_source']['state_annotation'])
                val = '{}'.format(hit['_source']['value_annotation'])
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
        for f in annotation_json.get('files', []):
            title = f['title']
            md5sum = f['md5sum']
            date_created = f['date_created']
            lab = f['lab']['title']
            href = request.host_url + f['href']
            status = f['status']
            assembly = f['assembly']
            output_type = f['output_type']
            if f['file_format'] == 'bed' or f['file_format'] == 'tsv' and f['status'] != 'archived':
                if title not in files:
                    files[title] = []
                    files[title].append({
                        'files_md5sum': md5sum,
                        'files_date_created': date_created,
                        'files_href': href,
                        'files_status': status,
                        'files_lab': lab,
                        'files_assembly': assembly,
                        'output_type': output_type
                    })
                else:
                    files[title].append({
                        'files_md5sum': md5sum,
                        'files_date_created': date_created,
                        'files_href': href,
                        'files_status': status,
                        'files_lab': lab,
                        'files_assembly': assembly,
                        'output_type': output_type
                    })
        references = []
        for r in annotation_json['references']:
            identifier = 'identifiers'
            if  identifier in r:
                identifiers = r['identifiers']
            else:
                identifiers = []
            references.extend(identifiers)
        documents = {}
        for d in annotation_json.get('documents', []):
            href = request.host_url + d['attachment']['href']
            md5sum = d['attachment']['md5sum']
            description = d['description']
            uuid = d['uuid']
            status = d['status']
            if uuid not in documents:
                documents[uuid] = []
                documents[uuid].append({
                    'documents_md5sum': md5sum,
                    'documents_description': description,
                    'documents_href': href,
                    'documents_status': status
                })
            else:
                documents[uuid].append({
                    'documents_md5sum': md5sum,
                    'documents_description': description,
                    'documents_href': href,
                    'documents_status': status
                    })
        annotation_id = annotation_json['accession']
        project = annotation_json['award']['project']
        annotation_type = annotation_json['annotation_type']
        status = annotation_json['status']
        version = annotation_json['schema_version']
        portal_tissue = None if annotation_json.get('portal_tissue')== None else annotation_json['portal_tissue']
        assay_type = annotation_json.get("annotation_type_category", None)
        collection_tags = None if annotation_json.get('collection_tags')== None else annotation_json['collection_tags']
        software = None if annotation_json.get("software_used")== None else annotation_json["software_used"][0]["software"]["title"]
        biosample_term_name = annotation_json.get("biosample_term_name", None)
        biosample_type = annotation_json.get("biosample_type", None)
        portal_tissue_id = annotation_json['tissue_term_id'] if 'tissue_term_id' in annotation_json else None
        biosample_term_id = annotation_json['biosample_term_id'] if 'biosample_term_id' in annotation_json else None
        dbxrefs = annotation_json['dbxrefs']
        annotation_source = None if annotation_json.get('annotation_source')== None else annotation_json['annotation_source']
        annotation_category = annotation_json['annotation_category'] if 'annotation_category' in annotation_json else 'Others'
        portal_usage = None if annotation_json.get('portal_usage')== None else annotation_json['portal_usage']
        #publication = None if annotation_json.get("references")== None else annotation_json['references']['identifiers']
        if files:
            if version not in json_doc:
                json_doc[version] = []
                json_doc[version].append({
                    'annotation_type': annotation_type,
                    'annotation_id': annotation_id,
                    'dbxrefs': dbxrefs,
                    'biosample_term_id': biosample_term_id,
                    'biosample_term_name': biosample_term_name,
                    'biosample_type': biosample_type,
                    'project': project,
                    'file_download': files,
                    'documents': documents,
                    'annotation_method': software,
                    'dataset_status': status,
                    'collection_tags': collection_tags,
                    'portal_tissue': portal_tissue,
                    'portal_tissue_id': portal_tissue_id,
                    'underlying_assay': assay_type,
                    'publications': references,
                    'annotation_source': annotation_source,
                    'annotation_category': annotation_category,
                    'portal_usage': portal_usage
                })  
            else:
                json_doc[version].append({
                    'annotation_type': annotation_type,
                    'annotation_id': annotation_id,
                    'dbxrefs': dbxrefs,
                    'project': project,
                    'biosample_term_id': biosample_term_id,
                    'biosample_term_name': biosample_term_name,
                    'biosample_type': biosample_type,
                    'file_download': files,
                    'documents': documents,
                    'annotation_method': software,
                    'dataset_status': status,
                    'portal_tissue': portal_tissue,
                    'portal_tissue_id':portal_tissue_id,
                    'underlying_assay':assay_type,
                    'collection_tags': collection_tags,
                    'publications': references,
                    'annotation_source': annotation_source,
                    'annotation_category': annotation_category,
                    'portal_usage': portal_usage
                    })             
    if 'annotation_metadata.json' in request.url:
        return Response(
            content_type='text/plain',
            body=json.dumps(json_doc,indent=2,sort_keys=True),
            content_disposition='attachment;filename="%s"' % 'annotation_metadata.json'
    )
@view_config(route_name= 'annotation_registry_metadata', request_method='GET')
def annotation_registry_metadata(context, request):
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
        references = []
        for r in annotation_json['references']:
            identifier = 'identifiers'
            if  identifier in r:
                identifiers = r['identifiers']
            else:
                identifiers = []
            references.extend(identifiers)
        annotation_id = annotation_json['accession']
        project = annotation_json['award']['project']
        annotation_type = annotation_json['annotation_type']
        status = annotation_json['status']
        lab = annotation_json['lab']['name']
        version = annotation_json['schema_version']
        portal_tissue = None if annotation_json.get('portal_tissue')== None else annotation_json['portal_tissue']
        assay_type = annotation_json.get("annotation_type_category", None)
        rfa = annotation_json['award']['rfa']
        collection_tags = None if annotation_json.get('collection_tags')== None else annotation_json['collection_tags']
        software = None if annotation_json.get("software_used")== None else annotation_json["software_used"][0]["software"]["title"]
        biosample_term_name = annotation_json.get("biosample_term_name", None)
        biosample_type = annotation_json.get("biosample_type", None)
        portal_tissue_id = annotation_json['tissue_term_id'] if 'tissue_term_id' in annotation_json else None
        biosample_term_id = annotation_json['biosample_term_id'] if 'biosample_term_id' in annotation_json else None
        dbxrefs = annotation_json['dbxrefs']
        annotation_source = None if annotation_json.get('annotation_source')== None else annotation_json['annotation_source']
        annotation_category = annotation_json['annotation_category'] if 'annotation_category' in annotation_json else 'Others'
        portal_usage = None if annotation_json.get('portal_usage')== None else annotation_json['portal_usage']
        #publication = None if annotation_json.get("references")== None else annotation_json['references']['identifiers']
        if rfa == 'AMP2' and status != 'deleted':
            if version not in json_doc:
                json_doc[version] = []
                json_doc[version].append({
                    'annotation_type': annotation_type,
                    'annotation_id': annotation_id,
                    'dbxrefs': dbxrefs,
                    'project': project,
                    'lab': lab,
                    'rfa': rfa,
                    'biosample_term_id': biosample_term_id,
                    'biosample_term_name': biosample_term_name,
                    'biosample_type': biosample_type,
                    'annotation_method': software,
                    'dataset_status': status,
                    'collection_tags': collection_tags,
                    'portal_tissue': portal_tissue,
                    'portal_tissue_id': portal_tissue_id,
                    'underlying_assay': assay_type,
                    'publications': references,
                    'annotation_source': annotation_source,
                    'annotation_category': annotation_category,
                    'portal_usage': portal_usage
                })  
            else:
                json_doc[version].append({
                    'annotation_type': annotation_type,
                    'annotation_id': annotation_id,
                    'dbxrefs': dbxrefs,
                    'project': project,
                    'lab': lab,
                    'rfa': rfa,
                    'biosample_term_id': biosample_term_id,
                    'biosample_term_name': biosample_term_name,
                    'biosample_type': biosample_type,
                    'annotation_method': software,
                    'dataset_status': status,
                    'portal_tissue': portal_tissue,
                    'portal_tissue_id':portal_tissue_id,
                    'underlying_assay':assay_type,
                    'collection_tags': collection_tags,
                    'publications': references,
                    'annotation_source': annotation_source,
                    'annotation_category': annotation_category,
                    'portal_usage': portal_usage
                    })             
    if 'annotation_registry_metadata.json' in request.url:
        return Response(
            content_type='text/plain',
            body=json.dumps(json_doc,indent=2,sort_keys=True),
            content_disposition='attachment;filename="%s"' % 'annotation_registry_metadata.json'
    )
