from dash import dcc
from dash import html

import dash_bootstrap_components as dbc

from global_helper_functions import get_networks, cite


downloadable_networks = get_networks(net_source='gtex_chip')

citation_link = {
    'gtex_chip': 'Farahmand2019Causal'
}

network_links_full_structure_children = []

for organism, o_dict in downloadable_networks.items():
    title = dbc.Row(dbc.Col(html.H4('Organism: ' + ' '.join(map(str.capitalize, organism.split('_'))))))
    network_links_full_structure_children.append(title)
    for source, s_dict in o_dict.items():
        title = 'Source: ' + ' '.join(map(str.capitalize, source.split('_')))
        title = dbc.Row(dbc.Col(html.H5(title), width={"offset": 1}))
        network_links_full_structure_children.append(title)
        if source in citation_link:
            citation_key = citation_link[source]
            citation = dbc.Row(dbc.Col(['Reference: ', cite(citation_key, full=False)], width={"offset": 1}), class_name='mb-2')
            network_links_full_structure_children.append(citation)
            
        for net_type, t_dict in s_dict.items():
            title = dbc.Row(dbc.Col(html.H6('Type: ' + ' '.join(map(str.capitalize, net_type.split('_')))), width={"offset": 2}))
            network_links_full_structure_children.append(title)

            children = []
            title = dbc.Col(html.H6('Networks: '), width={"size": 12})
            # children.append(title)
            for net_name, net_url in dict(sorted(t_dict.items())).items():
                link = dbc.Col(html.A(net_name.replace('.rels', ''), href=net_url, download=net_url), width={"size": 3})
                children.append(link)

            content = dbc.Row(dbc.Col(dbc.Row(children), width={"offset":3}), class_name='mb-4')
            network_links_full_structure_children.append(content)

menu = []

body = [

    dbc.Row(dbc.Col(
        dbc.Card([
            dbc.CardHeader('Download Network Data'),
            dbc.CardBody(network_links_full_structure_children),
        ],),
    ), class_name="mb-4 mt-4"),

]

