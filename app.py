# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import os
import dash_core_components as dcc
import dash_html_components as html
import dash_auth
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output, State
import datetime as dt
import numpy as np
from flask import request
from decouple import config
from dotenv import load_dotenv
import gettext

load_dotenv()


def load_datafile(filename):
    """
    Load the auxiliary data from a .csv file
    and check the weight / height (i.e. for kg/m instead of g/cm).

    If the file exists, returns a dataframe with g/cm;
    if it doesn't, returns None.

    Thus np.any() can check whether the data exists or not.
    """

    try:
        raw_data = pd.read_csv(filename)
        if max(raw_data[weightcol]) < 1000:
            raw_data[weightcol] *= 1000
            if sd_wt_col in raw_data:
                raw_data[sd_wt_col] *= 1000
        if max(raw_data[heightcol]) < 5:
            raw_data[heightcol] *= 100
            if sd_ht_col in raw_data:
                raw_data[sd_ht_col] *= 100
    except FileNotFoundError:
        raw_data = None
    return raw_data


def calc_age(days, disp='days'):
    """Used for plotting to set the X-scale."""
    if disp == 'days':
        return(days)
    else:
        return(days / 365.25)


def calc_weight(gram, disp='g'):
    """Used to set the plotting weight axis."""
    if disp == 'g':
        return(gram)
    else:
        return(gram / 1000)


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.config['suppress_callback_exceptions'] = True

VALID_USERNAME_PASSWORD_PAIRS = {
    'parent': config('PARENT'),
    'family': config('FAMILY')
}

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

server = app.server

app.title = config('APPNAME')
p1name = config('P1NAME')
p2name = config('P2NAME')
cname = config('CHILDNAME')
childbday = config('CHILDBDAY')
p1file = config('P1FILE')
p2file = config('P2FILE')
cfile = config('CFILE')
grofile = config('GROFILE')
datecol = config('DATECOL')
agecol = config('AGECOL')
weightcol = config('WEIGHTCOL')
heightcol = config('HEIGHTCOL')
headcol = config('HEADCOL')
comcol = config('COMCOL')
sd_wt_col = config('SDWTCOL')
sd_ht_col = config('SDHTCOL')
p1bday = config('P1BDAY')
p2bday = config('P2BDAY')
logfile_name = config('LOGFILE')

max_age_factor = float(config('MAX_AGE'))

applang = gettext.translation(
    'base', localedir='locales', languages=[
        config('APPLANG')])
applang.install()
_ = applang.gettext

os.makedirs(os.path.dirname(logfile_name), exist_ok=True)

with open(logfile_name, 'w') as logfile:
    nowstr = dt.datetime.now().isoformat(timespec='seconds', sep=' ')
    logstr = nowstr + ' Server rebooted\n'
    logfile.write(logstr)

hover_age_d = '<b>' + _("Age") + '</b>: %{x} ' + _("days") + '<br>'
hover_age_y = '<b>' + _("Age") + '</b>: %{x:3.2f} ' + _("years") + '<br>'
hover_w_g = '<b>' + _("Weight") + '</b>: %{y} ' + 'g <br>%{customdata}'
hover_w_kg = '<b>' + _("Weight") + '</b>: %{y} ' + 'kg <br>%{customdata}'
hover_date = '<b>' + _("Date") + '</b>: %{text}<br>'

child_birth = dt.datetime.strptime(childbday, '%Y%m%d')
h_birth = dt.datetime.strptime(p1bday, '%Y%m%d')
l_birth = dt.datetime.strptime(p2bday, '%Y%m%d')

p1_raw_data = load_datafile(p1file)
p2_raw_data = load_datafile(p2file)
gro_raw_data = load_datafile(grofile)

app.layout = html.Div(children=[
    dcc.Graph(
        id='mainplot'
    ),
    html.Div(children=[
        dcc.Checklist(
            id='checkboxes',
            options=[
                {'label': _("Plot") + ' ' + _("weight"), 'value': 'show_wt'},
                {'label': _("Plot") + ' ' + _("height"), 'value': 'show_ht'},
                {'label': _("Plot") + ' ' + _("growth curves") + (
                    _(' (ERROR: not found!)') if not np.any(gro_raw_data) else ''),
                 'value': 'gro_curves'},
                {'label': _("Plot") + ' ' + p1name + ' ' +
                 _("for comparison") + (
                    _(' (ERROR: not found!)') if not np.any(p1_raw_data) else ''),
                 'value': 'showp1'},
                {'label': _("Plot") + ' ' + p2name + ' ' +
                 _("for comparison") + (
                    _(' (ERROR: not found!)') if not np.any(p2_raw_data) else ''),
                 'value': 'showp2'},
                {'label': _("Zoom in around") + ' ' + cname, 'value': 'zoom'}],
            value=['show_ht', 'show_wt', 'showp1', 'showp2', 'zoom'],
            style={'width': '290px'}
        )], style={'columns': 2, 'margin-right': 'auto',
                   'margin-left': 'auto', 'width': '600px'}),
    html.Div(children=[
        html.Label(_("Weight scale:"),
                   style={'display': 'inline-block'}),
        html.Div(style={'display': 'inline-block', 'width': '10px'}),
        dcc.Dropdown(id='weightdrop',
                     options=[{'label': _('Grams'), 'value': 'g'},
                              {'label': _('Kilograms'), 'value': 'kg'}],
                     value='g',
                     style={'width': '100px', 'display': 'inline-block',
                     'top': '15px'}),
        html.Div(),
        html.Label(_("Age scale:"), style={'display': 'inline-block'}),
        html.Div(style={'display': 'inline-block', 'width': '10px'}),
        dcc.Dropdown(id='agedrop',
                     options=[{'label': _('Days'), 'value': 'days'},
                              {'label': _('Years'), 'value': 'years'}],
                     value='days',
                     style={'width': '100px', 'display': 'inline-block',
                     'top': '15px'})
    ], style={'columns': 2, 'margin-right': 'auto',
              'margin-left': 'auto', 'width': '600px'}),
    html.Div(id='input-form'),
    html.Div(id='numclicks', style={'display': 'none'}, children=0)
])


@app.callback(Output('input-form', 'children'),
              [Input('checkboxes', 'value')])
def make_inputs(check):
    usr = request.authorization['username']
    with open(logfile_name, 'a') as logfile:
        nowstr = dt.datetime.now().isoformat(timespec='seconds', sep=' ')
        logstr = nowstr + ' Connection by ' + usr + '\n'
        logfile.write(logstr)
    if usr == 'parent':
        input_form = html.Div(children=[
            dcc.Markdown('##### ' + _("Add data point") + ':\n\n'),
            dcc.DatePickerSingle(
                id='setdate',
                min_date_allowed=child_birth,
                max_date_allowed=child_birth + dt.timedelta(weeks=5200),
                initial_visible_month=dt.date.today(),
                date=dt.date.today(),
                style={'display': 'inline-block'}),
            html.Div(style={'display': 'inline-block', 'width': '10px'}),
            html.Label(_('Weight') + ' (g):', style={'display': 'inline-block'}),
            html.Div(style={'display': 'inline-block', 'width': '5px'}),
            dcc.Input(
                id='new_weight',
                style={
                    'display': 'inline-block',
                    'width': '100px'}),
            html.Div(style={'display': 'inline-block', 'width': '10px'}),
            html.Label(_('Height') + ' (cm):', style={'display': 'inline-block'}),
            html.Div(style={'display': 'inline-block', 'width': '5px'}),
            dcc.Input(
                id='new_height',
                style={
                    'display': 'inline-block',
                    'width': '100px'}),
            html.Div(style={'display': 'inline-block', 'width': '10px'}),
            html.Label(_('Head circumference') + ' (cm):', style={
                       'display': 'inline-block'}),
            html.Div(style={'display': 'inline-block', 'width': '5px'}),
            dcc.Input(
                id='new_head',
                style={
                    'display': 'inline-block',
                    'width': '100px'}),
            html.Div(style={'display': 'inline-block', 'width': '10px'}),
            html.Label(_('Comment') + ':', style={'display': 'inline-block'}),
            html.Div(style={'display': 'inline-block', 'width': '5px'}),
            dcc.Input(
                id='new_comment',
                style={
                    'display': 'inline-block',
                    'width': '150px'}),
            html.Div(style={'display': 'inline-block', 'width': '10px'}),
            html.Button(
                _("Submit"),
                id='submit-button',
                n_clicks=0,
                style={
                    'display': 'inline-block'})
        ], style={'margin-right': 'auto',
                  'margin-left': 'auto', 'max-width': '1100px'})
    else:
        input_form = ''
    return(input_form)


@app.callback(
    Output('numclicks', 'children'),
    [Input('submit-button', 'n_clicks')],
    [State('numclicks', 'children'),
     State('setdate', 'date'),
     State('new_weight', 'value'),
     State('new_height', 'value'),
     State('new_head', 'value'),
     State('new_comment', 'value')])
def new_datapoint(clicks, old_clicks, sel_date, new_weight, new_height,
                 new_head, new_comment, suppress_callback_exceptions=True):
    c_data = pd.read_csv(cfile)
    sel_date = dt.date.fromisoformat(sel_date)
    old_clicks = int(old_clicks)

    if clicks != old_clicks:
        if new_weight:
            new_weight = int(new_weight)
        else:
            new_weight = np.nan
        if new_height:
            new_height = float(new_height)
        else:
            new_height = np.nan
        if new_head:
            new_head = float(new_head)
        else:
            new_head = np.nan
        if new_comment:
            new_comment = str(new_comment)
        else:
            new_comment = np.nan
        age = sel_date - child_birth
        data_point = pd.DataFrame({
            datecol: sel_date.isoformat(),
            agecol: [age.days],
            weightcol: [new_weight],
            heightcol: [new_height],
            headcol: [new_head],
            comcol: [new_comment]})
        c_data = c_data.append(data_point)
        c_data.to_csv(cfile, index=False)
    else:
        pass
    return(clicks)


@app.callback(
    Output('mainplot', 'figure'),
    [Input('checkboxes', 'value'), Input('numclicks', 'children'),
     Input('weightdrop', 'value'), Input('agedrop', 'value')])
def update_figure(checkbox, num_clicks, weight_pref, age_pref,
                  suppress_callback_exceptions=True):
    p1 = p1name[0]
    p2 = (p2name[0] if p2name[0] != p1 else p2name[0:2])
    c0 = cname[0]
    if age_pref == 'days':
        hover_age = hover_age_d
    else:
        hover_age = hover_age_y
    if weight_pref == 'g':
        hover_w = hover_w_g
    else:
        hover_w = hover_w_kg

    lenhover = hover_date + hover_age + \
        ('<b>' + _("Height") + '</b>: %{y} cm <br>%{customdata}')

    vikthover = hover_date + \
        hover_age + hover_w

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    c_data = pd.read_csv(cfile)
    c_data[comcol] = c_data[comcol].convert_dtypes()
    if 'show_wt' in checkbox:
        fig.add_trace(
            go.Scatter(x=calc_age(c_data[agecol], age_pref),
                       y=calc_weight(c_data[weightcol], weight_pref),
                       name=c0 + " " + _("weight"),
                       hovertemplate=vikthover,
                       text=[dt.date.isoformat(child_birth + dt.timedelta(days=daze))
                             for daze in c_data[agecol]], mode='lines+markers',
                       connectgaps=True,
                       customdata=[
                '<br>' +
                comment if str(comment) != '<NA>' else '' for comment in c_data[comcol]]
            ),
            secondary_y=False,
        )
    if 'show_ht' in checkbox:
        fig.add_trace(
            go.Scatter(x=calc_age(c_data[agecol], age_pref), y=c_data[heightcol],
                       name=c0 + " " + _("height"),
                       hovertemplate=lenhover,
                       text=[dt.date.isoformat(child_birth + dt.timedelta(days=daze))
                             for daze in c_data[agecol]], mode='lines+markers',
                       customdata=[
                '<br>' +
                comment if str(comment) != '<NA>' else '' for comment in c_data[comcol]],
                connectgaps=True),
            secondary_y=True,
        )

    if 'gro_curves' in checkbox and np.any(gro_raw_data):
        if 'zoom' in checkbox:
            gro_data = gro_raw_data.loc[gro_raw_data[agecol]
                                        < max_age_factor * max(c_data[agecol])]
        else:
            gro_data = gro_raw_data

        if 'show_wt' in checkbox:
            fig.add_trace(
                go.Scatter(
                    x=calc_age(
                        gro_data[agecol],
                        age_pref),
                    y=calc_weight(
                        gro_data[weightcol],
                        weight_pref),
                    name=_("Average weight"),
                    connectgaps=True,
                    line={
                        'color': 'black'},
                    mode='lines',
                    hovertemplate=''),
                secondary_y=False)

            fig.add_trace(
                go.Scatter(
                    x=calc_age(
                        gro_data[agecol],
                        age_pref),
                    y=calc_weight(
                        (gro_data[weightcol] + gro_data[sd_wt_col]),
                        weight_pref),
                    name=_("Average weight") + " + 1 SD",
                    showlegend=False,
                    fill='tonexty',
                    mode='none',
                    hoveron='points+fills',
                    hovertemplate=_("Average weight") + ' + 1 SD',
                    line={
                        'color': '#CCCCCC'},
                    connectgaps=True),
                secondary_y=False)

            fig.add_trace(
                go.Scatter(
                    x=calc_age(
                        gro_data[agecol],
                        age_pref),
                    y=calc_weight(
                        (gro_data[weightcol] - gro_data[sd_wt_col]),
                        weight_pref),
                    name=_("Average weight") + ' - 1 SD',
                    showlegend=False,
                    fill='tonexty',
                    mode='none',
                    hoveron='points+fills',
                    hovertemplate=_("Average weight") + ' - 1 SD',
                    line={
                        'color': '#CCCCCC'},
                    connectgaps=True),
                secondary_y=False)
        if 'show_ht' in checkbox:
            fig.add_trace(
                go.Scatter(
                    x=calc_age(
                        gro_data[agecol],
                        age_pref),
                    y=gro_data[heightcol],
                    name=_("Average height"),
                    connectgaps=True,
                    mode='lines',
                    hovertemplate=''),
                secondary_y=True)

            fig.add_trace(
                go.Scatter(
                    x=calc_age(
                        gro_data[agecol],
                        age_pref),
                    y=(
                        gro_data[heightcol] +
                        gro_data[sd_ht_col]),
                    name=_("Average height") +
                    ' + 1 SD',
                    showlegend=False,
                    fill='tonexty',
                    mode='none',
                    hoveron='points+fills',
                    hovertemplate=_("Average height") +
                    ' + 1 SD',
                    line={
                        'color': '#CCCCCC'},
                    connectgaps=True),
                secondary_y=True)

            fig.add_trace(
                go.Scatter(
                    x=calc_age(
                        gro_data[agecol],
                        age_pref),
                    y=(
                        gro_data[heightcol] -
                        gro_data[sd_ht_col]),
                    name=_("Average height") +
                    ' - 1 SD',
                    showlegend=False,
                    fill='tonexty',
                    mode='none',
                    hoveron='points+fills',
                    hovertemplate=_("Average height") +
                    ' + 1 SD',
                    line={
                        'color': '#CCCCCC'},
                    connectgaps=True),
                secondary_y=True)

    if 'showp1' in checkbox and np.any(p1_raw_data):
        if 'zoom' in checkbox:
            p1_data = p1_raw_data.loc[p1_raw_data[agecol]
                                      < max_age_factor * max(c_data[agecol])]
        else:
            p1_data = p1_raw_data

        if 'show_wt' in checkbox:
            fig.add_trace(
                go.Scatter(
                    x=calc_age(
                        p1_data[agecol],
                        age_pref),
                    y=calc_weight(
                        p1_data[weightcol],
                        weight_pref),
                    name=p1 +
                    " " +
                    _("weight"),
                    connectgaps=True,
                    hovertemplate=vikthover,
                    text=[
                        dt.date.isoformat(
                            h_birth +
                            dt.timedelta(
                                days=daze)) for daze in p1_data[agecol]],
                    customdata=[
                        '' for i in p1_data[agecol]],
                    mode='lines+markers'),
                secondary_y=False,
            )
        if 'show_ht' in checkbox:
            fig.add_trace(
                go.Scatter(
                    x=calc_age(
                        p1_data[agecol],
                        age_pref),
                    y=p1_data[heightcol],
                    name=p1 +
                    " " +
                    _("height"),
                    connectgaps=True,
                    hovertemplate=lenhover,
                    text=[
                        dt.date.isoformat(
                            h_birth +
                            dt.timedelta(
                                days=daze)) for daze in p1_data[agecol]],
                    mode='lines+markers',
                    customdata=[
                        '' for i in p1_data[agecol]]),
                secondary_y=True,
            )

    if 'showp2' in checkbox and np.any(p2_raw_data):
        if 'zoom' in checkbox:
            p2_data = p2_raw_data.loc[p2_raw_data[agecol]
                                      < max_age_factor * max(c_data[agecol])]
        else:
            p2_data = p2_raw_data
        if 'show_wt' in checkbox:
            fig.add_trace(
                go.Scatter(
                    x=calc_age(
                        p2_data[agecol],
                        age_pref),
                    y=calc_weight(
                        p2_data[weightcol],
                        weight_pref),
                    name=p2 +
                    " " +
                    _("weight"),
                    connectgaps=True,
                    hovertemplate=vikthover,
                    text=[
                        dt.date.isoformat(
                            l_birth +
                            dt.timedelta(
                                days=daze)) for daze in p2_data[agecol]],
                    customdata=[
                        '' for i in p2_data[agecol]],
                    mode='lines+markers'),
                secondary_y=False,
            )
        if 'show_ht' in checkbox:
            fig.add_trace(
                go.Scatter(
                    x=calc_age(
                        p2_data[agecol],
                        age_pref),
                    y=p2_data[heightcol],
                    name=p2 +
                    " " +
                    _("height"),
                    connectgaps=True,
                    hovertemplate=lenhover,
                    text=[
                        dt.date.isoformat(
                            l_birth +
                            dt.timedelta(
                                days=daze)) for daze in p2_data[agecol]],
                    mode='lines+markers',
                    customdata=[
                        '' for i in p2_data[agecol]]),
                secondary_y=True,
            )
    fig.update_layout(
        title_text=(cname + _("'s development"))
    )
    if age_pref == 'days':
        fig.update_xaxes(
            title_text=(
                "<b>" +
                _("Age") +
                "</b> (" +
                _("days") +
                ")"))
    else:
        fig.update_xaxes(
            title_text=(
                "<b>" + _("Age") + "</b> (" + _("years") + ")"))
    if weight_pref == 'g':
        fig.update_yaxes(
            title_text=(
                "<b>" + _("Weight") + "</b> (g)"),
            secondary_y=False)
    else:
        fig.update_yaxes(
            title_text=(
                "<b>" + _("Weight") + "</b> (kg)"),
            secondary_y=False)
    fig.update_yaxes(
        title_text=(
            "<b>" + _("Height") + "</b> (cm)"),
        secondary_y=True)
    fig.update_layout(transition_duration=500)
    return(fig)


if __name__ == '__main__':
    app.run_server(debug=True)
