from snovault import upgrade_step

@upgrade_step('embedding', '', '2')
def embedding(value, system):
    if 'datasets' in value:
        value['datasets'] = list(set(value['datasets']))
    if 'datasets_experiment' in value:
        value['datasets_experiment'] = list(set(value['datasets_experiment']))

