import yaml
from urllib import quote

RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"

RDF_TYPE = {
    'boolean': 'http://www.w3.org/2001/XMLSchema#boolean',
    'date': 'http://www.w3.org/2001/XMLSchema#date',
    'datetime': 'http://www.w3.org/2001/XMLSchema#datetime',
    'int': 'http://www.w3.org/2001/XMLSchema#int',
    'double': 'http://www.w3.org/2001/XMLSchema#double'
}

SUBJECT_URI = "https://data.opendatasoft.com/ld/resources/{dataset_id}/{class_name}/$({field_name})"

SOURCE = '{dataset_id}.json~jsonpath'
ITERATOR = '$.[*].fields'


def serialize(confirmed_correspondances, dataset_id):
    rdf_mapping = {}
    rdf_mapping = _add_source(rdf_mapping, dataset_id)
    rdf_mapping['mappings'] = {}
    for class_correspondance in confirmed_correspondances['classes']:
        class_correspondance['class'] = quote(class_correspondance['class'].encode('utf8'))
        rdf_mapping = _add_class_map(rdf_mapping, class_correspondance, dataset_id)
    for property_correspondance in confirmed_correspondances['properties']:
        property_correspondance['associated_class'] = quote(property_correspondance['associated_class'].encode('utf8'))
        rdf_mapping = _add_predicate_map(rdf_mapping, property_correspondance, confirmed_correspondances['classes'])
    return yaml.safe_dump(rdf_mapping)


def _add_source(rdf_mapping, dataset_id):
    rdf_mapping['sources'] = {'dataset-source': [SOURCE.format(dataset_id=dataset_id), ITERATOR]}
    return rdf_mapping


def _add_class_map(rdf_mapping, class_correspondance, dataset_id):
    subject_id = '{}-{}'.format(class_correspondance['class'], class_correspondance['field_name'])
    template = SUBJECT_URI.format(dataset_id=dataset_id, class_name=class_correspondance['class'], field_name=class_correspondance['field_name'])
    class_map = {'source': 'dataset-source', 'subject': template, 'predicateobjects': []}
    # Adding classe and sub_classes of the resource
    class_map['predicateobjects'].append(['a', class_correspondance['uri']])
    for sub_class in class_correspondance['sub']:
        class_map['predicateobjects'].append(['a', sub_class])
    # Adding label of the resource
    class_map['predicateobjects'].append([RDFS_LABEL, '$({})'.format(class_correspondance['field_name'])])
    rdf_mapping['mappings'][subject_id] = class_map
    return rdf_mapping


def _add_predicate_map(rdf_mapping, property_correspondance, class_correspondances):
    subject_id = '{}-{}'.format(property_correspondance['associated_class'], property_correspondance['associated_field'])
    properties = [property_correspondance['uri']]
    for sub_property in property_correspondance['sub']:
        properties.append(sub_property)
    field_name = property_correspondance['field_name']
    class_correspondance = _get_class(field_name, class_correspondances)
    if class_correspondance:
        # Target of the predicate is a resource (URI)
        parent_map_id = '{}-{}'.format(class_correspondance['class'], class_correspondance['field_name'])
        if parent_map_id != subject_id:
            for prop in properties:
                rdf_mapping['mappings'][subject_id]['predicateobjects'].append({'objects': [{'mapping': parent_map_id}], 'predicates': prop})
            return rdf_mapping
        else:
            field_name = class_correspondance['field_name']
    # Target of the predicate is a field value (Term)
    field_type = property_correspondance['type']
    if field_type in RDF_TYPE:
        for prop in properties:
            rdf_mapping['mappings'][subject_id]['predicateobjects'].append([prop, '$({})'.format(field_name), RDF_TYPE[field_type]])
    else:
        for prop in properties:
            rdf_mapping['mappings'][subject_id]['predicateobjects'].append([prop, '$({})'.format(field_name)])
    return rdf_mapping


def _get_class(field_name, class_correspondances):
    for class_correspondance in class_correspondances:
        if field_name == class_correspondance['field_name']:
            return class_correspondance
    return None