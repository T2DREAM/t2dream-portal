import json
import requests
import re
#from urllib.parse import urlencode
from elasticsearch import Elasticsearch
host = 'http://t2depigenome-test.org'
es = Elasticsearch(['t2depigenome-test.org'],port=9200)
#es = Elasticsearch()
print "Connected", es.info()
#r = requests.get(url = URL, params = PARAMS)
start = '114758349'
end = '114758349'
chromosome = 'chr10'
_FACETS = [
    ('annotation_type', {'title': 'Annotation'}),
    ('biosample_term_name', {'title': 'Biosample term'}),
    ('assembly', {'title': 'Genome assembly'}),
    ('files.file_type', {'title': 'Available data'})
]
result = {}
def build_aggregation(facet_name, facet_options, min_doc_count=0):
    exclude = []
    if facet_name == 'type':
        field = 'embedded.@type.raw'
        exclude = ['Item']
    elif facet_name.startswith('audit'):
        field = facet_name
    else:
        field = 'embedded.' + facet_name + '.raw'
    agg_name = facet_name.replace('.', '-')
    facet_type = facet_options.get('type', 'terms')
    if facet_type == 'terms':
        agg = {
            'terms': {
                'field': field,
                'min_doc_count': min_doc_count,
                'size': 100,
                },
            }
        if exclude:
            agg['terms']['exclude'] = exclude
    elif facet_type == 'exists':
        agg = {
            'filters': {
                'filters': {
                    'yes': {'exists': {'field': field}},
                    'no': {'missing': {'field': field}},
                    },
                },
            }
    else:
        raise ValueError('Unrecognized facet type {} for {} facet'.format(facet_type, field))
    return agg_name, agg
def get_bool_query(start, end):
    must_clause = {
        'bool': {
            'must': [
                {
                    'range': {
                        'positions.start': {
                            'lte': start,
                        }
                    }
                },
                {
                    'range': {
                        'positions.end': {
                            'gte': end,
                        }
                    }
                }
            ]
        }
    }
    return must_clause

def get_peak_query(start, end, with_inner_hits=False, within_peaks=False):
    query = {
        'query': {
            'filtered': {
                'filter': {
                    'nested': {
                        'path': 'positions',
                        'filter': {
                            'bool': {
                                'should': []
                            }
                        }
                    }
                },
                '_cache': True,
            }
        },
        '_source': False,
    }
    search_ranges = {
        'peak_inside_range': {
            'start': start,
            'end': end
            },
        'range_inside_peaks': {
            'start': end,
            'end': start
            },
        'peaks_overlap_start_range': {
            'start': start,
            'end': start
            },
        'peak_overlap_end_range': {
            'start': end,
            'end': end
            }
        }
    for key,value in search_ranges.items():
        query['query']['filtered']['filter']['nested']['filter']['bool']['should'].append(get_bool_query(value['start'],value['end']))
    if with_inner_hits:
        query['query']['filtered']['filter']['nested']['inner_hits'] = {'size': 99999}
    return query

def get_filtered_query(term, search_fields, result_fields, principals, doc_types):
    return {
        'query': {
            'query_string': {
                'query': term,
                'fields': search_fields,
                'default_operators': 'AND'
                }
            },
        'filter': {
            'and': {
                'filters': [
                    {
                        'terms': {
                            'principals_allowed.view': principals
                            }
                        },
                    {
                        'terms': {
                            'embedded.@type.raw': doc_types
                            }
                        }
                    ]
                }
            },
        '_source': list(result_fields),
}

def set_facets(facets, used_filters, principals, doc_types):
    aggs = {}
    for facet_name, facet_options in facets:
        filters = [
            {'terms': {'principals_allowed.view': principals}},
            {'terms': {'embedded.@type.raw': doc_types}},
            ]
        for field, terms in used_filters.items():
            if field.endswith('!'):
                query_field = field[:-1]
            else:
                query_field = field
            if query_field == facet_name:
                continue
            if not query_field.startswith('audit'):
                query_field = 'embedded.' + query_field + '.raw'
            if field.endswith('!'):
                if terms == ['*']:
                    filters.append({'missing': {'field': query_field}})
                else:
                    filters.append({'not': {'terms': {query_field: terms}}})
            else:
                if terms == ['*']:
                    filters.append({'exists': {'field': query_field}})
                else:
                    filters.append({'terms': {query_field: terms}})
            agg_name, agg = build_aggregation(facet_name, facet_options)
            aggs[agg_name] = {
                'aggs': {
                    agg_name: agg
                    },
                'filter': {
                    'bool': {
                        'must': filters,
                        },
                    },
                }
            return aggs
assembly = 'hg19'
principals = ['system.Everyone']
peak_query = get_peak_query(start, end,with_inner_hits=True, within_peaks=True)
#print(peak_query)
peak_results = es.search(body=peak_query,index=chromosome,doc_type = assembly,size=99999)
#print(peak_results)
file_uuids = []
for hit in peak_results['hits']['hits']:
    if hit['_id'] not in file_uuids:
        file_uuids.append(hit['_id'])
file_uuids = list(set(file_uuids))
#print(file_uuids)
if len(file_uuids):
    query = get_filtered_query('', [], set(), principals, ['Annotation'])
    del query['query']
    query['filter']['and']['filters'].append({
        'terms': {
            'embedded.files.uuid': file_uuids
            }
        })
    used_filters={}
    used_filters['files.uuid'] = file_uuids
    #print(used_filters)
    query['aggs'] = set_facets(_FACETS, used_filters, principals, ['Annotation'])
    print(query)
    #print(['Annotation'])
    schemas = (types[item_type].schema for item_type in ['Annotation'])
    #print(schemas)
    es_results = es.search(body=query, index='snovault', doc_type='annotation', size=100)
    #print(es_results)
    result['peaks'] = list(peak_results['hits']['hits'])
    #print(result['peaks'])
    #uuids_in_results = get_file_uuids(results)
    path = 'https://t2depigenome-test.org/region-search/?region={}:{}-{}&genome={}'.format(row['_index'], hit['_source']['start'], hit['_source']['end']
    rows = []
    json_doc = {}
    for row in result['peaks']:
        #print(row['_id'])
        if row['_id'] in file_uuids:
            #file_json = (peak_results(row['path']))
            #print file_json
            #annotation_json = 
            #print(file_json['dataset'])
            #annotation_json = file_json['dataset']
            for hit in row['inner_hits']['positions']['hits']['hits']:
                data_row = []
                chrom = '{}'.format(row['_index'])
                assembly = '{}'.format(row['_type'])
                start = '{}'.format(hit['_source']['start'])
                stop = '{}'.format(hit['_source']['end'])
                #file_accession = file_json
                #annotation_accession = annotation_json['accession']
                #annotation = annotation_json['annotation_type']
                #biosample_term = annotation_json['biosample_term_name']
                #data_row.extend([coordinates, file_accession])
                #rows.append(data_row)
                json_doc[assembly] = []
                json_doc[assembly].append({
                        #'ANNOTATION_TYPE': annotation,
                        #'source': biosample_term,
                    'CHROM': chrom,
                    'START': start,
                    'STOP': stop,
                    'VALUE': 'NULL',
                    'ASSEMBLY': assembly,
                    #'ANNOTATION_FILE': file_accession,
                        #'ANNOTATION_ID': annotation_accession
                })
#        print(json_doc)

#r1 = requests.post(url = T2DKP_API_ENDPOINT, data = json_doc)
