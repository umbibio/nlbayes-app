from dash import dcc
from dash import html

import dash_bootstrap_components as dbc

from global_helper_functions import cite


description = '''
Welcome to the NLBayes web portal! NLBayes is a tool for the inference of transcription 
factor (TF) activity from differential gene expression data, that uses noisy boolean logic 
and causal graphs, to model transcriptional regulatory interactions between TFs and their 
target genes.

NLBayes is available for R and Python as instalable packages
[nlbayes-python](https://github.com/umbibio/nlbayes-python),
[nlbayes-rcran](https://github.com/umbibio/nlbayes-rcran).

This web portal provides a [simple interface](inference) to use the corresponding inference
algorithm and for [obtaining data](data) relevant to the method.
'''

menu = None

body = [
    dbc.Row(dbc.Col(
        dbc.Card([
            dbc.CardHeader(html.H2("Noisy Logic Bayesian Inference")),
            dbc.CardBody(
                dbc.Row([
                    dbc.Col(dcc.Markdown(description),
                    width={'size': '6', 'offset': '0'}),
                # dbc.Col(
                #     dbc.Carousel(items=[
                #         {"key": "1", "src": "/babesiasc/assets/newplot-expression.png"},
                #         {"key": "2", "src": "/babesiasc/assets/newplot-pstime.png"},
                #         {"key": "3", "src": "/babesiasc/assets/network-graph.png"},
                #     ], interval=5000, className="carousel-fade", indicators=False)),
                ])
            ),
        ],),
    ), class_name="mb-4 mt-4"),
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.H4("Citation")),
            dbc.CardBody(dcc.Markdown('''
''')),
        ],),),
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.H4("Contact")),
            dbc.CardBody(dcc.Markdown('''
''')),
        ],),),
    ]),
]

