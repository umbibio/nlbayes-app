from dash import dcc
from dash import html

import dash_bootstrap_components as dbc

menu = None

body = [
    dbc.Row(dbc.Col(
        dbc.Card([
            dbc.CardHeader(html.H2("Noisy Logic Bayesian Inference")),
            dbc.CardBody(
                dbc.Row([
                    dbc.Col(dcc.Markdown('''
Description

''')),
                dbc.Col(
                    # dbc.Carousel(items=[
                    #     {"key": "1", "src": "/babesiasc/assets/newplot-expression.png"},
                    #     {"key": "2", "src": "/babesiasc/assets/newplot-pstime.png"},
                    #     {"key": "3", "src": "/babesiasc/assets/network-graph.png"},
                    # ], interval=5000, className="carousel-fade", indicators=False)
                )])),
        ],),
    ), class_name="mb-4 mt-4"),
#     dbc.Row([
#         dbc.Col(dbc.Card([
#             dbc.CardHeader(html.H4("Citation")),
#             dbc.CardBody(dcc.Markdown('''
# ''')),
#         ],),),
#         dbc.Col(dbc.Card([
#             dbc.CardHeader(html.H4("Contact")),
#             dbc.CardBody(dcc.Markdown('''
# ''')),
#         ],),),
#     ]),
]

