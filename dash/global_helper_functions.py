import os
from glob import glob
import bibtexparser

from dash import html


def get_networks(net_source = '*', net_organism = '*', net_type = '*'):
    networks = {}
    for network_file in glob(os.path.join('assets', 'data', 'networks', net_source, net_organism, net_type, '*.json')):
        _, _, _, s, o, t, n = os.path.splitext(network_file)[0].split(os.sep)

        if not s in networks.keys():
            networks[s] = {}

        if not o in networks[s].keys():
            networks[s][o] = {}

        if not t in networks[s][o].keys():
            networks[s][o][t] = {}

        networks[s][o][t][n] = network_file

    return networks


with open(os.path.join('assets', 'references.bib')) as bibtex_file:
    references = bibtexparser.load(bibtex_file).entries


references_dict = {}
for item in references:
    references_dict[item['ID']] = item


months = {
    '1': 'January', '01': 'January', 'Jan': 'January',
    '2': 'February', '02': 'February', 'Feb': 'February',
    '3': 'March', '03': 'March', 'Mar': 'March',
    '4': 'April', '04': 'April', 'Apr': 'April',
    '5': 'May', '05': 'May', 'May': 'May',
    '6': 'June', '06': 'June', 'Jun': 'June',
    '7': 'July', '07': 'July', 'Jul': 'July',
    '8': 'August', '08': 'August', 'Aug': 'August',
    '9': 'September', '09': 'September', 'Sep': 'September',
    '10': 'October', 'Oct': 'October',
    '11': 'November', 'Nov': 'November',
    '12': 'December', 'Dec': 'December',
}


def cite(key, full=False):
    if key not in references_dict:
        return

    ref = references_dict[key]
    authors = []
    for i, a in enumerate(ref['author'].split(' and ')):
        if ', ' in a:
            familyname, givenname = a.split(', ')
        else:
            full_name = a.split(' ')
            familyname = full_name[-1]
            givenname = ' '.join(full_name[:-1])

        a = givenname + ' ' + familyname
        authors.append(a)
        if i == 0:
            first_author_familyname = familyname
    authors_str = ', '.join(authors[:-1]) + ' and ' + authors[-1]

    if not full:
        return html.A(f"({first_author_familyname}, et al. {ref['year']})", href=ref['url'], target='blank')


    if 'doi' in ref:
        doi_url = 'https://doi.org/' + ref['doi']
        doi_url = html.A(doi_url, href=doi_url, target='blank')
    else:
        doi_url = None

    if ref['journal'].lower() in ['arxiv', 'biorxiv']:
        published_str = "Preprint:"
    else:
        published_str = "Published:"
    if 'month' in ref:
        published_str += ' ' + months[ref['month']]
    published_str += ' ' + ref['year']
    return html.Div([
        html.Span('“' + ref['title'].strip('{}') + '”. '), html.Br(),
        html.Span(authors_str + '. '), html.Br(),
        html.I(ref['journal']),
        ', Volume ' + ref['volume'] if 'volume' in ref else None,
        ', Issue ' + ref['number'] if 'number' in ref else None,
        html.Br(),
        doi_url,
        html.Br(),
        published_str,
    ])
