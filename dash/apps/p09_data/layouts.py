import os
from dash import dcc
from dash import html

import dash_bootstrap_components as dbc

from global_helper_functions import get_networks, cite


downloadable_networks = get_networks(net_source='gtex_chip')
# downloadable_networks = get_networks(net_source='*')

citation_link = {
    'gtex_chip': 'Farahmand2019Causal',
    'aracne': 'Lachmann2016Aracne',
}

network_links_full_structure_children = []

for net_source, o_dict in downloadable_networks.items():
    title = dbc.Row(dbc.Col(html.H4('Source: ' + ' '.join(map(str.capitalize, net_source.split('_'))))))
    network_links_full_structure_children.append(title)
    if net_source in citation_link:
        citation_key = citation_link[net_source]
        citation = dbc.Row(dbc.Col(['Reference: ', cite(citation_key, full=False)], width={"offset": 0}), class_name='mb-2')
        network_links_full_structure_children.append(citation)
    for net_organism, s_dict in o_dict.items():
        title = 'Organism: ' + ' '.join(map(str.capitalize, net_organism.split('_')))
        title = dbc.Row(dbc.Col(html.H5(title), width={"offset": 1}))
        network_links_full_structure_children.append(title)
            
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


source_code_path = os.path.join('assets', 'scripts', 'aracne2net.R')
with open(source_code_path) as file:
  convert_aracne_code = f""" ```R {file.read()} ``` """


menu = []

body = [

    dbc.Row(dbc.Col(
        dbc.Card([
            dbc.CardHeader('Download Network Data'),
            dbc.CardBody([
                *network_links_full_structure_children,
                html.H4('References'),
                html.Hr(),
                cite('Farahmand2019Causal', full=True),
            ]),
        ],),
    ), class_name="mb-4 mt-4"),

    dbc.Row(dbc.Col(
        dbc.Card([
            dbc.CardHeader('How to process ARACNe networks'),
            dbc.CardBody([
                html.P([
                    'In this work we have used networks based on regulons developed by ', cite('Lachmann2016Aracne'), '. ',
                    'You can use the R code below to process these regulons and convert them into networks that can be '
                    'used in NLBayes. This script selects only DNA binding transcription factors using GO terms, '
                    'similar to what was done by ', cite('Alvarez2016Functional'), '. '
                    'In our case, we leave out cofactors and signaling pathway related genes.'
                ]),
                dbc.Accordion(
                    [
                        dbc.AccordionItem([
                            'Download: ', html.A(os.path.basename(source_code_path), href=source_code_path.replace(os.sep, '/'), download=os.path.basename(source_code_path)),
                            html.Hr(),
                            dcc.Markdown(convert_aracne_code),
                        ], title='R script', ),
                    ],
                    class_name='mb-4',
                    start_collapsed=True,
                ),
                html.H4('References'),
                html.Hr(),
                cite('Lachmann2016Aracne', full=True),
                html.Hr(),
                cite('Alvarez2016Functional', full=True),
            ]),
        ],),
    ), class_name="mb-4 mt-4"),

]

