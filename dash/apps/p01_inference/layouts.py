from dash import dcc
from dash import html

import dash_bootstrap_components as dbc

menu = [
    html.Br(),
    html.H3("Define Inputs"),
    html.Hr(),
    html.Div([
        html.H4("Network selection"),
        dbc.Alert(html.Small("Use one of the predefined networks we make available, "
            "or upload a custom network. "
            "Use the switch below to toggle between these two options."), color="info")
    ]),
    dbc.Switch('use-predefined-network', label='Use Predefined Network', value=True),
    
    html.Div(
        children = [
            dbc.Label("Select Network:"),
        ] + [
            dbc.Row([
                dbc.Label(label, id=key + '-net-select-label', html_for={'type': 'net-select', 'key': key}, width=4),
                dbc.Tooltip(info, target=key + '-net-select-label', placement='right'),
                dbc.Col(dbc.Select(id={'type': 'net-select', 'key': key}), width=8), ], class_name='mb-2')
            for label, key, info in zip(
                ['Source', 'Organism', 'Type', 'Name'],
                ['net_source', 'net_organism', 'ntype', 'name'],
                [
                    'The source where the network was obtained from.',
                    'Specify the organism or species for the network',
                    'Whether the network is built for a specific context (tissue specific), or not (tissue independent).',
                    'The name that identifies the network.',
                ])
        ] + [
            dbc.Alert(html.Small("Selected network uses NCBI ids."), color='info'),
        ],
        id='network-selection-container',
        style={'display': 'none'},
    ),

    html.Div(
        children=[
            dbc.Label("Upload Network File:", html_for='upload-network'),
            dcc.Upload(
                id='upload-network',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select File')
                ]),
                style={
                    'width': '100%',
                    'padding': '2em 1em',
                    'lineHeight': '1.2em',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '0px'
                },
                multiple=False
            ),
            html.Br(),
            html.Div([
            html.P('A network file should be either a table (csv or tsv) file with columns:'),
            html.P(html.Code(' "tf_id": str, "gene_id": str, "mor": int')),
            html.P('or a json file with format:'),
            html.P(html.Code(' { "tf_id": {"gene_id": mor, ...}, ...}')),
            html.P([
                "The ", html.Code("mor"), " values are integer numbers representing the mode of ",
                "regulation for the tf-gene pair and must be either 1, 0 or -1. ",
                "TF and gene ids must match the ids used in the Experiment ",
                "Data file in the field bellow. Ids will be treated as strings. ",
            ]),
            ], id='network-upload-instructions'),
        ],
        id='network-upload-container',
        style={'display': 'none'},
    ),
    html.Hr(),
    html.Div([
        html.H4("Data upload"),
        dbc.Alert(html.Small(
            "Use the form below to upload a csv, tsv or xlsx file with the differential expression to analyze. "
            "Gene IDs must match those used in the loaded network. Fold change column is required and will be "
            "converted into discrete values -1, 0, +1."), color='info')
    ]),
    html.Div([
        dbc.Label("Upload Experiment Data:", html_for='upload-data'),
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                # html.Br(),html.Br(),
                'Drag and Drop or ',
                html.A('Select File')
            ]),
            style={
                'width': '100%',
                'padding': '2em 1em',
                'lineHeight': '1.2em',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '0px'
            },
            multiple=False
        ),
    ]),
    html.Br(),

    dbc.Label("Select Data Columns:"),
    *[dbc.Row([
        dbc.Label(label, html_for={'type': 'data-column-role', 'key': key}, width=4),
        dbc.Col(dbc.Select(id={'type': 'data-column-role', 'key': key}, options=[{'label': 'Not Available', 'value': 'not-available'}], value='not-available'), width=8), ], class_name='mb-2')
      for label, key in zip(['Gene ID', 'P-Value', 'Log2 FC'], ['gene', 'pval', 'logfc']) ],
    html.Br(),

    # dbc.Label("Gene ID type:"),
    # html.Br(),

    dbc.Label("Set Differential Expression limits:"),
    html.Br(),
    dbc.Row([
        dbc.Label('P-Value Threshold:', html_for='pval-threshold', width=6),
        dbc.Col(dbc.Input('pval-threshold', type='number', value='1e-3', min=0., max=1., step='any'), width=6), ], class_name='mb-2'),
    dbc.Row([
        dbc.Label('log2FC Threshold:', html_for='logfc-threshold', width=6),
        dbc.Col(dbc.Input('logfc-threshold', type='number', value='1', min=0., step='any'), width=6), ], class_name='mb-2'),
    html.Br(),

    dbc.Row(dbc.Col(html.P(id='final-evidence-info')), class_name='mb-3'),

    dbc.Row(dbc.Col(dbc.Button('Submit Job', id='submit-job-button', disabled=True, class_name='float-end'))),
]

body = [
    dcc.Interval('inference-progress-timer', 5000, disabled=True),
    dcc.Store('queue-task-info'),

    dcc.Store('data-uploaded-network', data={}),
    dcc.Store('data-selected-network', data={}),
    dcc.Store('selected-network-final'),

    dcc.Store('input-data'),
    dcc.Store('data-columns-available'),
    dcc.Store('selected-evidence-final', data={}),

    dcc.Store('output-data'),

    dbc.Row(dbc.Col(
        dbc.Card([
            dbc.CardBody(dbc.Row([
                dbc.Col(html.H5("Input Data (top 50 preview)", className='card-title'), class_name='mt-0'),
                dbc.Col(html.Div(id='output-data-upload'), width=12),
            ])),
        ],),
    ), class_name="mb-4 mt-4"),
    dbc.Row(dbc.Col(
        dbc.Card([
            dbc.CardBody(dbc.Row([
                dbc.Col(html.H5("Processed Data (top 50 preview)", className='card-title'), class_name='mt-0'),
                dbc.Col(html.Div(id='processed-data-table'), width=12),
            ])),
        ],),
    ), class_name="mb-4 mt-4"),
    dbc.Row(dbc.Col(
        dbc.Card([
            dbc.CardBody(dbc.Row([
                dbc.Col(html.H5("Volcano Plot", className='card-title'), class_name='mt-0'),
                dbc.Col(html.Div(id='volcano-plot'), width=12),
            ])),
        ],),
    ), class_name="mb-4 mt-4"),
    dbc.Row(dbc.Col(
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(html.H5("Active TF Inference", className='card-title'), class_name='mt-0'),
                    dbc.Col(html.Div(id='inference-info'), width=12),
                ]),
                dbc.Row([
                    dbc.Col([
                        dcc.Download(id='inference-result-download'),
                        dbc.Button('Download TSV', id='inference-result-download-button', style={'display': 'none'}),
                    ])
                ])
            ]),
        ],),
    ), class_name="mb-4 mt-4"),
]

