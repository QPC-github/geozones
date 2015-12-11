import os
import re
from string import Template

import requests


RE_WIKIPEDIA = re.compile(
    r'https?://(?P<namespace>\w+)?\.?wikipedia\.org/wiki/(?P<resource>.+)$')
SPARQL_SERVER = 'http://dbpedia.inria.fr/sparql'
# We want population and/or area from French DBPedia or
# their international counterparts as fallbacks.
SPARQL_POPULATION_TEMPLATE = Template('''SELECT ?population ?area WHERE {
    {<$resource_url> <http://fr.dbpedia.org/property/population>|
                     <http://dbpedia.org/ontology/populationTotal> ?population}
UNION
    {<$resource_url> <http://fr.dbpedia.org/property/superficie>|
                     <http://dbpedia.org/ontology/area> ?area}
}''')

# We want flag and/or blason from French DBPedia or
# their international counterparts as fallbacks.
SPARQL_IMAGE_TEMPLATE = Template('''SELECT ?flag ?blazon WHERE {
    {<$resource_url> <http://dbpedia.org/ontology/flag> ?flag}
UNION
    {<$resource_url> <http://dbpedia.org/ontology/blazon> ?blazon}
}''')


class DBPedia(object):

    def __init__(self, resource):
        resource = resource.strip('').replace(' ', '_')
        # Special wrong case: `fr:fr:Communauté_de_communes_d'Altkirch`
        if resource.startswith('fr:fr:'):
            namespace, _, self.resource = resource.split(':')
        elif ':' in resource and not resource.startswith('http'):
            namespace, self.resource = resource.split(':')
        elif RE_WIKIPEDIA.match(resource):
            m = RE_WIKIPEDIA.match(resource)
            namespace, self.resource = m.group('namespace', 'resource')
        else:
            self.resource = resource
            namespace = None

        if namespace:
            self.base_url = 'http://{0}.dbpedia.org'.format(namespace)
        else:
            self.base_url = 'http://dbpedia.org'
        self.resource_url = '{base_url}/resource/{resource}'.format(
            base_url=self.base_url, resource=self.resource)

    def fetch_population_or_area(self):
        sparql_query = SPARQL_POPULATION_TEMPLATE.substitute(
            resource_url=self.resource_url)
        parameters = {
            'default-graph-uri': 'http://fr.dbpedia.org',
            'query': sparql_query,
            'format': 'json'
        }
        response = requests.get(SPARQL_SERVER, params=parameters)
        data = response.json()
        population_or_area = {}
        try:
            results = data['results']['bindings'][0]
        except IndexError:
            return population_or_area
        if 'population' in results:
            population_or_area['population'] = results['population']['value']
        if 'area' in results:
            population_or_area['area'] = results['area']['value']
        return population_or_area

    def fetch_flag_or_blazon(self):
        sparql_query = SPARQL_IMAGE_TEMPLATE.substitute(
            resource_url=self.resource_url)
        parameters = {
            'default-graph-uri': 'http://fr.dbpedia.org',
            'query': sparql_query,
            'format': 'json'
        }
        response = requests.get(SPARQL_SERVER, params=parameters)
        data = response.json()
        flag_or_blazon = {}
        try:
            results = data['results']['bindings'][0]
        except IndexError:
            return flag_or_blazon
        if 'flag' in results:
            flag_name = results['flag']['value'].replace(' ', '_')
            flag_or_blazon['flag'] = flag_name
        if 'blazon' in results:
            blazon_name = results['blazon']['value'].replace(' ', '_')
            flag_or_blazon['blazon'] = blazon_name
        return flag_or_blazon
