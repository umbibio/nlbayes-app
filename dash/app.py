import os
import dash

import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template


url_base_pathname = '/nlbayes/'
# url_base_pathname = '/'

###################
### Theme Setup ###
###################

# theme="slate"
theme="spacelab"
# theme="bootstrap"

# This loads the themed figure template from dash-bootstrap-templates library,
# adds it to plotly.io and makes it the default figure template.
load_figure_template(theme)

external_stylesheets = [
    getattr(dbc.themes, theme.upper()),
    dbc.icons.BOOTSTRAP,
]
app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    url_base_pathname=url_base_pathname,
    suppress_callback_exceptions=True,
    title='NLBayes', update_title='Loading...')

server = app.server
