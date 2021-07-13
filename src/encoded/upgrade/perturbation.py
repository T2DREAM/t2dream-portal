from snovault import upgrade_step

@upgrade_step('perturbation', '', '2')
def embedding(value, system):
    if 'datasets' in value:
        value['datasets'] = list(set(value['datasets']))

