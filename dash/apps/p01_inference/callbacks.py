import os
import json
import datetime
from pprint import pprint

import numpy as np
import pandas as pd
import plotly.express as px

import dash_bootstrap_components as dbc
from dash import callback_context as ctx
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash import dcc, html, dash_table
from app import app

from global_helper_functions import get_networks
from .helper_functions import parse_contents, load_json_file
from .helper_functions import submit_job, get_job_status


networks = get_networks()


@app.callback(
    Output({'type': 'net-select', 'key': 'net_source'}, 'options'),
    Output({'type': 'net-select', 'key': 'net_source'}, 'value'),
    Input('use-predefined-network', 'value'),)
def populate_network_net_source_dropdown(use_predefined):

    if ctx.triggered[0]['prop_id'] == 'use-predefined-network.value':
        raise PreventUpdate

    if not use_predefined:
        options = []
        value = None
    else:
        options_lst = list(networks.keys())
        options_lst.sort()
        options = [{'label': ' '.join(map(str.capitalize, k.split('_'))), 'value': k} for k in options_lst]
        value = 'gtex_chip'

    return options, value


@app.callback(
    Output({'type': 'net-select', 'key': 'net_organism'}, 'options'),
    Output({'type': 'net-select', 'key': 'net_organism'}, 'value'),
    Input({'type': 'net-select', 'key': 'net_source'}, 'value'),)
def populate_network_net_organism_dropdown(net_source):
    if not net_source:
        options = []
        value = None
    else:
        options_lst = list(networks[net_source].keys())
        options_lst.sort()
        options = [{'label': ' '.join(map(str.capitalize, k.split('_'))), 'value': k} for k in options_lst]
        value = 'homo_sapiens' if 'homo_sapiens' in options_lst else (options[0]['value'] if options else None)

    return options, value


@app.callback(
    Output({'type': 'net-select', 'key': 'ntype'}, 'options'),
    Output({'type': 'net-select', 'key': 'ntype'}, 'value'),
    Input({'type': 'net-select', 'key': 'net_source'}, 'value'),
    Input({'type': 'net-select', 'key': 'net_organism'}, 'value'),)
def populate_network_ntype_dropdown(net_source, net_organism):
    if not net_source or not net_organism:
        options = []
        value = None
    else:
        options_lst = list(networks[net_source][net_organism].keys())
        options_lst.sort()
        options = [{'label': ' '.join(map(str.capitalize, k.split('_'))), 'value': k} for k in options_lst]
        value = 'tissue_independent' if 'tissue_independent' in options_lst else (options[0]['value'] if options else None)

    return options, value


@app.callback(
    Output({'type': 'net-select', 'key': 'name'}, 'options'),
    Output({'type': 'net-select', 'key': 'name'}, 'value'),
    State({'type': 'net-select', 'key': 'net_source'}, 'value'),
    State({'type': 'net-select', 'key': 'net_organism'}, 'value'),
    Input({'type': 'net-select', 'key': 'ntype'}, 'value'),)
def populate_network_name_dropdown(net_source, net_organism, ntype):
    if not ntype or not net_organism or not net_source:
        options = []
        value = None
    else:
        options_lst = list(networks[net_source][net_organism][ntype].keys())
        options_lst.sort()
        options = [{'label': ' '.join(map(str.capitalize, k.replace('.rels', '').split('_'))), 'value': k} for k in options_lst]
        value = 'three_tissue.rels' if 'three_tissue.rels' in options_lst else (options[0]['value'] if options else None)

    return options, value


@app.callback(
    Output('data-selected-network', 'data'),
    State({'type': 'net-select', 'key': ALL}, 'id'),
    Input({'type': 'net-select', 'key': ALL}, 'value'), )
def update_network_selected(nids, netsel):
    ns = {i['key']:v for i, v in zip(nids, netsel)}
    if all([bool(v) for v in netsel]):
        s, o, t, n = ns['net_source'], ns['net_organism'], ns['ntype'], ns['name']
        network_file = networks[s][o][t][n]
        with open(network_file, 'r') as file:
            return json.load(file)

    raise PreventUpdate


@app.callback(
    Output('data-uploaded-network', 'data'),
    Output('upload-network', 'children'),
    Input('upload-network', 'contents'),
    State('upload-network', 'filename'),
    State('upload-network', 'last_modified'))
def update_network_upload(content, filename, date):
    if not filename:
        raise PreventUpdate
    network = parse_contents(content, filename)
    if isinstance(network, pd.DataFrame):
        # clean up the names of the columns to try to match with possible roles.
        # We convert to lowercase and use string translation to remove uninformative
        # characters 
        t = str.maketrans('', '', '.-_ ')
        smpl_cols = [c.lower().translate(t) for c in network.columns]

        # possible matches for each role. The order matters, we select the the first
        # match of the list
        tst_collection = {
            'src': ['src', 'tf', 'factor'],
            'trg': ['trg', 'gene'],
            'mor': ['mor', 'type', 'sign', 'reg', 'sgn'],
        }

        gcn = {}
        missing_columns = []
        for role in tst_collection.keys():
            # we run each test in order. If we find a match, both loops get broken
            # if no match, the inner loop is complete and we go to the next test
            for tst in tst_collection[role]:
                for scol, col in zip(smpl_cols, network.columns):
                    if tst in scol:
                        gcn[role] = col
                        break
                else:
                    continue
                break
            else:
                missing_columns.append(f"'{role}'")
                print(f"Error: failed to guess columns for '{role}'")
        if missing_columns:
            droparea_text = html.Div([
                f'Loaded data: {filename}', html.Br(),
                f'Error: missing',
                'column ' if len(missing_columns) == 1 else 'columns ',
                ', '.join(missing_columns),
            ])
            return {}, droparea_text

        network = network.loc[:, [gcn['src'], gcn['trg'], gcn['mor']]]
        network = network.dropna()
        network[gcn['src']] = network[gcn['src']].astype(str)
        network[gcn['trg']] = network[gcn['trg']].astype(str)
        network[gcn['mor']] = network[gcn['mor']].apply(np.sign).astype(int)

        dff = network.set_index([gcn['src'], gcn['trg']])
        dff = dff.groupby(level=0).apply(lambda df: df.xs(df.name)[gcn['mor']].to_dict())
        network = dff.to_dict()

    n_src = len(network.keys())
    n_trg = len(set([k for d in network.values() for k in d.keys()]))
    n_rel = sum([len(d) for d in network.values()])
    droparea_text = html.Div([
        f'Loaded data: {filename}', html.Br(),
        f"{n_src} tfs, {n_trg} genes, {n_rel} edges"
    ])
    
    return network, droparea_text


@app.callback(
    Output('output-data-upload', 'children'),
    Output('upload-data', 'children'),
    Output('data-columns-available', 'data'),
    Output('input-data', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'))
def update_output(content, filename, date):
    if content is not None:
        df = parse_contents(content, filename)
        if df is not None:
            table = html.Div([
                html.H5(filename),
                html.H6(datetime.datetime.fromtimestamp(date)),

                dash_table.DataTable(
                    df.iloc[:50].to_dict('records'),
                    [{'name': i, 'id': i} for i in df.columns],
                    page_size=5,
                ),
            ])
        else:
            table = html.Div(['There was an error processing this file.'])

        nrows = df.shape[0]
        droparea_text = html.Div([ f'Loaded data: {filename} ({nrows} rows)'])
        return table, droparea_text, df.columns.to_list(), df.to_dict()
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'data-column-role', 'key': MATCH}, 'options'),
    Output({'type': 'data-column-role', 'key': MATCH}, 'value'),
    State({'type': 'data-column-role', 'key': MATCH}, 'id'),
    Input('data-columns-available', 'data'))
def guess_columns(id, cols):
    # the column role is either 'gene', 'pval' or 'logfc'
    role = id['key']

    # the default outputs
    na_option = {'label': 'Not Available', 'value': 'not-available'}
    na_value = 'not-available'

    if not cols:
        return [na_option], na_value

    # make the list of column options
    idxs = list(range(len(cols)))
    options = [{'label': f"{idx+1}: {col}", 'value': col}
               for idx, col in zip(idxs, cols)]
    options.append(na_option)

    # clean up the names of the columns to try to match with possible roles.
    # We convert to lowercase and use string translation to remove uninformative
    # characters 
    t = str.maketrans('', '', '.-_ ')
    smpl_cols = [c.lower().translate(t) for c in cols]

    # possible matches for each role. The order matters, we select the the first
    # match of the list
    tst_collection = {
        'gene': ['geneid', 'ncbi', 'entrez', 'ensembl', 'symbol', 'gene', 'name'],
        'pval': ['adj', 'pval'],
        'logfc': ['log2fc', 'logfc', 'foldchange'],
    }

    # we run each test in order. If we find a match, both loops get broken
    # if no match, the inner loop is complete and we go to the next test
    for tst in tst_collection[role]:
        for scol, col in zip(smpl_cols, cols):
            if tst in scol:
                value = col
                break
        else:
            continue
        break
    else:
        # we didn't find any matches
        value = na_value

    return options, value


@app.callback(
    Output('volcano-plot', 'children'),
    Output('selected-evidence-final', 'data'),
    Output('processed-data-table', 'children'),
    Output('final-evidence-info', 'children'),
    Input('input-data', 'data'),
    State({'type': 'data-column-role', 'key': ALL}, 'id'),
    Input({'type': 'data-column-role', 'key': ALL}, 'value'),
    Input('selected-network-final', 'data'),
    Input('logfc-threshold', 'value'),
    Input('pval-threshold', 'value'), )
def process_input_data(data, cids, colnames, network, logfc_threshold, p_val_threshold):
    try:
        logfc_threshold = float(logfc_threshold)
        p_val_threshold = float(p_val_threshold)
    except TypeError:
        raise PreventUpdate

    if not data or len(data) == 0:
        return None, {}, None, None

    if not network or len(network) == 0:
        return None, {}, None, None

    # determine tfs and genes available in the network
    # we will filter out genes not available
    # src_set = set(network.keys())
    trg_set = set([k for d in network.values() for k in d.keys()])
    # n_edges = sum([len(d.values()) for d in network.values()])

    # this is a map specifying the columns to use
    t = {i['key']:c for i, c in zip(cids, colnames) if c != 'not-available'}
    if 'gene' not in t.keys() or 'logfc' not in t.keys():
        return None, {}, None, None

    keys = ['gene', 'pval', 'logfc']
    std_names = ['Gene', 'P-Value', 'Log2FC']
    orig_names_avail = []
    std_names_avail = []
    for k, s in zip(keys, std_names):
        if k in t.keys():
            orig_names_avail.append(t[k])
            std_names_avail.append(s)

    # we build the dataframe and select only the columns of interest
    # then change the column names to the standard names we can work with
    df = pd.DataFrame(data)
    df = df.loc[:, orig_names_avail]
    df.columns = std_names_avail

    # determine which genes were differentially expressed according to 
    # logfc and pvalue thresholds
    logfc_filter = lambda x: 1 if x > logfc_threshold else (-1 if x < -logfc_threshold else 0)
    df['DE value'] = df['Log2FC'].apply(logfc_filter)

    if 'pval' in t.keys():
        # filter by pvalue
        df['DE value'] *= (df['P-Value'] < p_val_threshold).astype(int)

        # generate a series to show in volcano plot
        plot_y = '-log10(P-Value)'
        df[plot_y] = -np.log10(df['P-Value']+np.finfo(float).eps)

        df = df.sort_values('P-Value')
    else:
        # generate a series to show in volcano plot
        plot_y = 'abs(log2FC)'
        df[plot_y] = np.abs(df['Log2FC'])

        # if no pvalue is available, we sort by abs(log2fc)
        # create a dummy column for pvalue
        df['P-Value'] = 0.
        df = df.sort_values('abs(log2FC)', ascending=False)

    # eliminate duplicated genes, keeping the most significant result
    # according to pvalue (or abs(log2fc))
    df = df.drop_duplicates('Gene').dropna()
    df['Gene'] = df['Gene'].astype(str)

    # keep only genes available in the network
    df = df.loc[df['Gene'].isin(trg_set)]

    evidence_map = {-1: 'down', 0:'', 1: 'up'}
    df['evidence'] = df['DE value'].map(evidence_map)
    color_map = {'down': 'blue', '': 'lightgray', 'up': 'red'}
    fig = px.scatter(df, x='Log2FC', y=plot_y, color='evidence', color_discrete_map=color_map)
    fig.update_layout(xaxis_range=[-4,4])

    df = df.loc[df['DE value'] != 0]
    evidence = df.set_index('Gene')['DE value'].to_dict()

    n_deg = len(evidence)
    # final_evidence_info = dbc.Alert(f'There are {n_deg} DE genes selected', color='success')
    final_evidence_info = dbc.Badge([
        'There are ',
        dbc.Badge(f"{n_deg}", pill=True, color="primary", className="me-1"),
        ' DE genes selected' ],
        color='white',
        text_color='primary',
        className="border me-1 float-end",
    )
    dt_data = df.iloc[:50].to_dict('records')
    dt_columns = [{'name': i, 'id': i} for i in df.columns]
    return dcc.Graph(figure=fig), evidence, dash_table.DataTable(dt_data, dt_columns, page_size=5), final_evidence_info


@app.callback(
    Output('queue-task-info', 'data'),
    Input('submit-job-button', 'n_clicks'),
    Input('selected-network-final', 'data'),
    Input('selected-evidence-final', 'data'),
)
def submit_inference_job(button_click, network, evidence):

    button_clicked = ctx.triggered[0]['prop_id'] == 'submit-job-button.n_clicks'
    if button_clicked:
        job_id, task_id, data = submit_job(network, evidence)
        return {
            'job_id': job_id,
            'task_id': task_id,
            # 'data': data,
        }
    

@app.callback(
    Output('inference-info', 'children'),
    Output('inference-progress-timer', 'disabled'),
    Input('queue-task-info', 'data'),
    Input('inference-progress-timer', 'n_intervals'),
    State({'type': 'net-select', 'key': 'net_organism'}, 'value'),
)
def update_job_status(info, refresh_trigger, organism):
    if info is None:
        raise PreventUpdate

    disable_interval = False

    job_id = info['job_id']
    task_id = info['task_id']
    posterior_hash = None

    meta = get_job_status(task_id)
    status = meta.get('status', 'PENDING')
    meta = meta.get('result')
    if meta is not None:
        if 'meta' in meta.keys():
            posterior_hash = meta.get('posterior_hash')
            meta = meta.get('meta')
        elapsed_time = meta.get('elapsed_time', '')
        n_sampled = meta.get('n_sampled', 0)
        gr_stat = meta.get('gr_stat', float('inf'))
    else:
        elapsed_time = ''
        n_sampled = 0
        gr_stat = float('inf')

    children = [ f'Job ID: {job_id}', html.Br(),
                 f"Status: {status}", html.Br(),
                 f"Elapsed Time: {elapsed_time}", html.Br(),
                 f"N Sampled: {n_sampled}", html.Br(),
                 f"Gelman-Rubin Statistic: {gr_stat:.4f}", html.Br(), ]

    if posterior_hash is not None:
        posterior = load_json_file(posterior_hash)
        annotation_filepath = f"data/annotations/{organism}/ncbi/symbol.json"
        if os.path.exists(annotation_filepath):
            with open(annotation_filepath) as file:
                annotation = json.load(file)
        else:
            annotation = {}

        posterior_df = pd.DataFrame(posterior).reset_index().sort_values('X', ascending=False)
        posterior_df.columns = ['TF', 'X', 'T']
        if len(set(posterior_df['TF']).intersection(annotation.keys())) > 0:
            posterior_df['symbol'] = posterior_df['TF'].map(annotation)
            posterior_df = posterior_df.iloc[:, [0, 3, 1, 2]]

        dt_data = posterior_df.to_dict('records')
        dt_columns = [{'name': i, 'id': i} for i in posterior_df.columns]
        dt_table = dash_table.DataTable(dt_data, dt_columns, page_size=25)
        children.append(dt_table)
        disable_interval = True

    return html.Div(children), disable_interval


app.clientside_callback(
    """
    function update_network_selec_visibility(use_predefined) {
        if(use_predefined) {
            return {'display': 'block'};
        } else {
            return {'display': 'none'};
        }
    }
    """,
    Output('network-selection-container', 'style'),
    Input('use-predefined-network', 'value')
)


app.clientside_callback(
    """
    function update_network_upload_visibility(use_predefined) {
        if(use_predefined) {
            return {'display': 'none'};
        } else {
            return {'display': 'block'};
        }
    }
    """,
    Output('network-upload-container', 'style'),
    Input('use-predefined-network', 'value')
)


app.clientside_callback(
    """
    function update_selected_network(use_predef, predef_sel_net, uploaded_net) {
        //console.log(use_predef, typeof(predef_sel_net), typeof(uploaded_net));
        //console.log(Object.keys(predef_sel_net).length, Object.keys(uploaded_net).length);
        if (use_predef) return predef_sel_net;
        return uploaded_net;
    }
    """,
    Output('selected-network-final', 'data'),
    Input('use-predefined-network', 'value'),
    Input('data-selected-network', 'data'),
    Input('data-uploaded-network', 'data'),
)


app.clientside_callback(
    """
    function update_pval_th_disabled(col) {
        if (col == 'not-available') return true;
        return false;
    }
    """,
    Output('pval-threshold', 'disabled'),
    Input({'type': 'data-column-role', 'key': 'pval'}, 'value'),
)


app.clientside_callback(
    """
    function update_submit_button_disabled(network, evidence) {
        if (Object.keys(network).length == 0) return true
        if (Object.keys(evidence).length == 0) return true
        return false
    }
    """,
    Output('submit-job-button', 'disabled'),
    Input('selected-network-final', 'data'),
    Input('selected-evidence-final', 'data'),
)

