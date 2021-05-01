'''
Team Pass
GMU-DAEN-690-DL2@SPRING2021

The Dashboard we create is interactive, user-friendly to those who don't have any analytics background.

Highlights:
Fetch data from AWS S3
Ensure data privacy and data security

Features:
Business unit/Location: 1) click cell to show top 5 chart and top 10 chart; 2) drop down to select specific location; 3) search box
User List: 1) click cell to show top 5 chart and top 10 chart; 2) when selecting specifc location, the user list would be shown. The data can be filtered in the following: user id, total rating, disposals rating, locations rating, receiving rating
Role Description: when selecting specific user in user list, the corresponding numbers would be displayed.

Require:
Python3 with packages on AWS EC2 terminal
pip3 install dash pandas dash-bootstrap-components boto3 plotly.express OrderedDict io
'''

# import modules
import pandas as pd
import dash
import dash_table
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Output, Input, State, ALL
import boto3
import io
import json
import plotly.express as px
from collections import OrderedDict
import plotly.graph_objects as go

# set path and name of data files
is_data_on_s3 = True  # True: use csv on s3, False: csv on local disk
s3_bucket = 'dean690-dataset'
file_location = 'table.Location_Rating.0412.csv'
file_user = 'table.Rating.0412.csv'
file_location_user_disposals = 'table.processed_disposals_df_1.0412.csv'
file_location_user_receiving = 'table.processed_receiving_df_1.0412.csv'
file_location_user_locations = 'table.processed_locations_df_1.0412.csv'
rating_all = 'table.Rating_all.0412.csv'

# create a function to get data on aws s3 bucket


def get_s3_df(filename):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=s3_bucket, Key=filename)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()))
    return df


# load data files into DataFrames
if is_data_on_s3:
    df_location = get_s3_df(file_location)
    df_user = get_s3_df(file_user)
    df_location_user_disposals = get_s3_df(file_location_user_disposals)
    df_location_user_receiving = get_s3_df(file_location_user_receiving)
    df_location_user_locations = get_s3_df(file_location_user_locations)
    df_rating_all = get_s3_df(rating_all)



# business-unit-based table adjustments
df_location = df_location.sort_values('total_rating', ascending=False)[
    ['location', 'total_rating']]
df_location = df_location[df_location.total_rating > 0]
df_location['id'] = df_location.location

df_all_user = df_user.sort_values('total_rating', ascending=False)
df_all_user = df_all_user.nlargest(100, 'total_rating')

df_all_location = df_location.sort_values('total_rating', ascending=False)
df_all_location = df_all_location.nlargest(100, 'total_rating')

trace1 = go.Bar(x=df_location.location, y=df_location.total_rating)
# Stack rating each roles
trace2 = go.Bar(name="Disposals_Rating", x=df_all_user.user,
                y=df_all_user.disposals_rating, offsetgroup=0)
trace3 = go.Bar(name="Locations_Rating", x=df_all_user.user,
                y=df_all_user.locations_rating, offsetgroup=0)
trace4 = go.Bar(name="Receiving_Rating", x=df_all_user.user,
                y=df_all_user.receiving_rating, offsetgroup=0)
#rate_all = go.Bar(name="All_Rating",x=df_all_user.user,y=df_all_user.total_rating,offsetgroup=0)

# Disposals count

disp_error_count = 0
disp_correct_count = 0
for i in range(len(df_rating_all)):
    if (df_rating_all['disposals_rating'][i] == 0) and df_rating_all['disposal_role'][i] == 1:
        disp_correct_count = disp_correct_count + 1
    else:
        disp_error_count = disp_error_count + 1

# Location count
loc_error_count = 0
loc_correct_count = 0
for i in range(len(df_rating_all)):
    if (df_rating_all['locations_rating'][i] == 0) and df_rating_all['locations_role'][i] == 1:
        loc_correct_count = loc_correct_count + 1
    else:
        loc_error_count = loc_error_count + 1

# Receiving count
recv_error_count = 0
recv_correct_count = 0
for i in range(len(df_rating_all)):
    if (df_rating_all['receiving_rating'][i] == 0) and df_rating_all['receiving_role'][i] == 1:
        recv_correct_count = recv_correct_count + 1
    else:
        recv_error_count = recv_error_count + 1

pie_color = ['red', 'green']
trace5 = go.Pie(labels=['Error', 'Correct'], values=[
                disp_error_count, disp_correct_count], marker=dict(colors=pie_color))
trace6 = go.Pie(labels=['Error', 'Correct'], values=[
                loc_error_count, loc_correct_count], marker=dict(colors=pie_color))
trace7 = go.Pie(labels=['Error', 'Correct'], values=[
                recv_error_count, recv_correct_count], marker=dict(colors=pie_color))

# user-based table adjustments
df_user = df_user.sort_values(
    'total_rating', ascending=False).set_index('user')
df_user = df_user[df_user.total_rating > 0]
df_user['id'] = df_user.index


# round the data to 6 digits
df_location = round(df_location, 6)
df_user = round(df_user, 6)
df_location_user_disposals = round(df_location_user_disposals, 6)
df_location_user_locations = round(df_location_user_locations, 6)
df_location_user_receiving = round(df_location_user_receiving, 6)

# combine 3 role's location-user mapping
df_location_user = pd.concat([df_location_user_disposals, df_location_user_receiving, df_location_user_locations])[
    ['location', 'user']].drop_duplicates(ignore_index=True).set_index('location')


# initialize Dash application
app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])


# set dashboard page content: location list
# build location topX selection chart
def build_location_top_selection():
    df_per_row_dropdown = pd.DataFrame(OrderedDict([
        ('id', ['5', '10']),
        ('top', ['TOP 5', 'TOP 10']),
        ('total_rating', ['show', 'show']),
    ]))
    # chart title
    title = 'Click cell to show TOP X chart, or dropdown to select a location'
    return dash_table.DataTable(
        id='id_location_top_selection',
        columns=[{"name": [title, ""], "id": "top"}] +
        [{"name": [title, s], "id": s} for s in ("total_rating",)],
        data=df_per_row_dropdown.to_dict('records'),
        style_header={
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        style_cell={
            'textAlign': 'center',
            'minWidth': '120px', 'width': '120px', 'maxWidth': '120px',
        },
        style_as_list_view=False,
        page_size=20,
        merge_duplicate_headers=True,
    )


# set dashboard page content: location list
# build location dropdown
def build_location_dropdown():
    options = [{'label': df_location.iloc[i].location + ' total_rating ' +
                str(df_location.iloc[i].total_rating), 'value': df_location.iloc[i].location} for i in range(len(df_location))]
    return dcc.Dropdown(
        id='id_location_dropdown',
        options=options,
        placeholder="Select a location",
    )


# set dashboard page content: location list
# build location barchart
def build_location_barchart(index):
    if index > 0:
        data = df_location.head(index)
    else:
        data = df_location.tail((-1)*index)
    fig = px.bar(data, x="location", y="total_rating",
                 color="location", title="")
    fig.update_layout(showlegend=False)
    return dcc.Graph(
        id={
            'type': 'id_location_barchart',
                    'index': 1
        },
        figure=fig,
        animate=False,
        responsive=True,
        config={"displayModeBar": False}
    )


# set dashboard page content: user list
# build user topX selection chart
def build_user_top_selection():
    df_per_row_dropdown = pd.DataFrame(OrderedDict([
        ('id', ['5', '10']),
        ('top', ['TOP 5', 'TOP 10']),
        ('total_rating', ['show', 'show']),
        ('disposals_rating', ['show', 'show']),
        ('locations_rating', ['show', 'show']),
        ('receiving_rating', ['show', 'show']),
    ]))
    # chart title
    title = 'Click a cell to show TOP X chart'
    return dash_table.DataTable(
        id='id_user_top_selection',
        columns=[{"name": [title, ""], "id": "top"}] + [{"name": [title, s], "id": s} for s in (
            "total_rating", 'disposals_rating', 'locations_rating', 'receiving_rating')],
        data=df_per_row_dropdown.to_dict('records'),
        style_header={
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        style_cell={
            'textAlign': 'center',
            'minWidth': '120px', 'width': '120px', 'maxWidth': '120px',
        },
        style_as_list_view=False,
        page_size=20,
        merge_duplicate_headers=True,
    )


# set dashboard page content: user list
# define structure and style for user table
def build_user_table(location_id=None):
    if location_id is None:
        data = None
    else:
        # get current location's user list
        data = df_user[df_user.index.isin(df_location_user.user.loc[[location_id]])][[
            'id', 'total_rating', 'disposals_rating', 'locations_rating', 'receiving_rating']]
        # sort by total rating
        data = data.sort_values(
            ['total_rating'], ascending=False).reset_index().to_dict('records')

    return dash_table.DataTable(
        id={'type': 'id_user_table', 'index': '1'},
        columns=[{"name": s, "id": s} for s in (
            "user", "total_rating", 'disposals_rating', 'locations_rating', 'receiving_rating')],
        editable=True,
        data=data,
        style_header={
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        style_cell={
            'textAlign': 'left',
            'minWidth': '60px', 'width': '130px', 'maxWidth': '130px',
        },
        style_data_conditional=[
            {
                "if": {"state": "selected"},
                "backgroundColor": "inherit !important",
                "border": "inherit !important",
            }
        ],
        style_table={'overflowX': 'scroll'},
        filter_action='native',
        row_selectable='single',
        style_as_list_view=False,
        page_size=20,
        merge_duplicate_headers=True,
        dropdown_conditional=[{
            'if': {
                'column_id': 'total_rating',
                'filter_query': '{id} eq "user_dropdown"'
            },
            'options': [{'label': '1', 'value': '1'}, {'label': '2', 'value': '2'}]
        }],
    )


# set dashboard page content: user list
# build user topX barchart
def build_user_barchart(by, index):
    if index > 0:
        data = df_user.sort_values(by, ascending=False).head(index)
    else:
        data = df_user.sort_values(by, ascending=False).tail((-1)*index)
    if by == 'total_rating':
        data = data[['disposals_rating', 'locations_rating',
                     'receiving_rating']].reset_index()
        fig = px.bar(data, x="user", y=[
                     "disposals_rating", "locations_rating", "receiving_rating"], title="")
        fig.update_layout(barmode='stack', xaxis={'categoryorder': 'total descending'}, title="Top "+str(
            index)+" Users vs total rating", yaxis={'title': 'rating'})
    else:
        data = data[[by]].reset_index()
        fig = px.bar(data, x="user", y=[by], color="user", title="")
        fig.update_layout(title="Top "+str(index) +
                          " Users vs " + by, yaxis={'title': by})
        fig.update_layout(showlegend=False)
    return dcc.Graph(
        id={
            'type': 'id_user_barchart',
                    'index': 1
        },
        figure=fig,
        animate=False,
        responsive=True,
        config={"displayModeBar": False}
    )


# set dashboard page content: detail table
# define structure and style for detail tables
def build_detail_table(idstr, columns, data):
    return dash_table.DataTable(
        id=idstr,
        columns=columns,
        data=data,
        style_header={
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        style_cell={
            'textAlign': 'left',
        },
        style_data_conditional=[
            {
                "if": {"state": "selected"},
                "backgroundColor": "inherit !important",
                "border": "inherit !important",
            }
        ],
        style_as_list_view=True,
        page_size=20,
        merge_duplicate_headers=True,
    )


# set dashboard page content: detail table
# build layout for user detail tables
def build_detail_zone():
    detail_disposal_empty = [
        {'scan_type_#': '', 'ret_date_#': '', 'disp_doc_#': '', 'err_cost_disposals': ''}]
    detail_location_empty = [
        {'val_ds584_flag_#': '', 'err_cost_locations': ''}]
    detail_receiving_empty = [{'misclf_fap_#': '',
                               'cre_mthod_#': '', 'err_cost_receiving': ''}]
    return [
        build_detail_table('id_detail_disposals',
                           [{"name": ["Role Disposals", "Number of error action (scan_type_#)"], "id": "scan_type_#"},
                            {"name": [
                                "Role Disposals", "Number of error action (ret_date_#)"], "id": "ret_date_#"},
                            {"name": [
                                "Role Disposals", "Number of error action (disp_doc_#)"], "id": "disp_doc_#"},
                            {"name": ["Role Disposals", "Involved error cost (err_cost_disposals)"], "id": "err_cost_disposals"}],
                           detail_disposal_empty),
        html.Div(style={"margin-top": "50px"}),
        build_detail_table('id_detail_location',
                           [{"name": ["Role Location", "Number of error action (val_ds584_flag_#)"], "id": "val_ds584_flag_#"},
                            {"name": ["Role Location", "Involved error cost (err_cost_locations)"], "id": "err_cost_locations"}],
                           detail_location_empty),
        html.Div(style={"margin-top": "50px"}),
        build_detail_table('id_detail_receiving',
                           [{"name": ["Role Receiving", "Number of error action (misclf_fap_#)"], "id": "misclf_fap_#"},
                            {"name": [
                                "Role Receiving", "Number of error action (cre_mthod_#)"], "id": "cre_mthod_#"},
                            {"name": ["Role Receiving", "Involved error cost (err_cost_receiving)"], "id": "err_cost_receiving"}],
                           detail_receiving_empty),
    ]


# set Home page contents
def build_homepage_text():
    return [
        # project name
        html.H3("Accurate User Database and Traning Resource Optimization", style={
                "margin-top": "100px", "margin-left": "50px"}),
        # Abstract
        html.H4(html.B("Abstract"), style={
                "margin-top": "100px", "margin-left": "50px"}),
        # Abstract contents
        html.H5("With the fast-growing global supply chain system and with an increased number of businesses depending on it, proper users training has become a necessity. In this project, Accenture Federal provided us with its client’s system, which tracks assets procurement, distribution, maintenance, and retirement. This system contains many years’ worth of data, and its users, each with various roles, need training in order to utilize it properly. Our goal is to build a model that can help the client list the users who need or are overdue for training. We used the data provided by Accenture Federal service to determine which user needed to train and which types of training that the user needed. We implemented the model to calculate the standardized error action scores and error costs for each user. After applying weights for different attributes and roles, we summarized the total ratings for users in all three roles. ",
                style={"margin-top": "15px", "margin-left": "50px"}),
        # domain of problem
        html.H4(html.B("Domain of problem"), style={
                "margin-top": "40px", "margin-left": "50px"}),
        # domain of problem contents
        html.H5("Cloud Computing, Data Engineering, Data Analytics, Data Visualization", style={
                "margin-top": "15px", "margin-left": "50px"}),
        # project goals
        html.H4(html.B("Project Goals"), style={
                "margin-top": "40px", "margin-left": "50px"}),
        # project goals contents
        html.H5("Our team builds a model that can prioritize the users who need training and the training area they need. Also, create a dashboard that can be drop down by location and give a list of users and the training area for each location.", style={
                "margin-top": "15px", "margin-left": "50px"}),
        # findings
        html.H4(html.B("Findings"), style={
                "margin-top": "40px", "margin-left": "50px"}),
        # findings content 1
        html.H5("1. The Top 100 Users: the graph shows the top 100 error ratings for users. Due to the weights of roles, the rating of disposal roles has the largest impact on the total rating.", style={
                "margin-top": "15px", "margin-left": "50px"}),
        # graph for finding 1
        #html.H5("Graph1", style={"margin-top": "15px", "margin-left": "50px"}),
        html.Div(dcc.Graph(id='3roles', style={'width': '190vh', 'height': 'fit-content'}, figure=go.Figure(data=[trace2, trace3, trace4], layout={'barmode':'stack',
                 'title': 'Top 100 Error Rating Each Users', 'xaxis': {'title': 'Users'}, 'yaxis': {'title': 'Error Rating'}}))),
        # findings content 2
        html.H5("2. Error Rating Each Location: the graph shows the total rating for each location sorting from the highest to the lowesr. The locations with higher number of users most likely results a higher rating.", style={
                "margin-top": "15px", "margin-left": "50px"}),
        # graph for finding 2
        #html.H5("Graph2", style={"margin-top": "15px", "margin-left": "50px"}),
        html.Div(dcc.Graph(id='location', style={'width': '190vh'}, figure=go.Figure(data=[trace1], layout={
                 'title': 'Error Rating Each Locations', 'xaxis': {'title': 'Users'}, 'yaxis': {'title': 'Error Rating'}})),),
        # findings content 3
        html.H5("3. The Percentage of Error in Each Role: the graphs show the percentage of users who did the error transactions compared with the total number of users in each role.  The location role has the most users, and the disposal role has the highest user error rate in all three roles.", style={
                "margin-top": "15px", "margin-left": "50px"}),
        # graph for finding 3
        #html.H5("Graph3", style={"margin-top": "15px", "margin-left": "50px"}),
        html.Div([
            # html.Div(children='The Percentage Of Error In Each Roles', style={'textAlign': 'left',"font-size": "28px","background-color": "#ffeecc"}),
            dbc.Row([dbc.Col(dcc.Graph(id='Disposals Pie', style={'width': '50vh'}, figure=go.Figure(data=[trace5], layout={'title': 'Disposals'}))), dbc.Col(dcc.Graph(id='Locations Pie', style={'width': '50vh'}, figure=go.Figure(data=[trace6], layout={'title': 'Locations'}))), dbc.Col(dcc.Graph(id='Receiving Pie', style={'width': '50vh'}, figure=go.Figure(data=[trace7], layout={'title': 'Receiving'})))
                     ]),
        ]),
        # creators
        html.H4(html.B("Created by Team Pass (GMU-DAEN-690-DL2@SPRING2021)"),
                style={"margin-top": "100px", "margin-left": "50px"}),
    ]

# define structure and style for data tables


def build_table(idstr, columns, data, selectable):
    return dash_table.DataTable(
        id=idstr,
        columns=columns,
        data=data,
        style_header={
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        style_cell={
            'textAlign': 'left',
        },
        style_data_conditional=[
            {
                "if": {"state": "selected"},
                "backgroundColor": "inherit !important",
                "border": "inherit !important",
            }
        ],
        row_selectable='single' if selectable else None,
        style_as_list_view=True,
        page_size=20,
        merge_duplicate_headers=True,
    )

# build location dropdown


def build_location_zone(duplicate=False):
    if not duplicate:
        return dcc.Dropdown(
            id='id_location_dropdown',
            options=[{'label': df_location.iloc[i].location + ' total_rating ' + str(
                df_location.iloc[i].total_rating), 'value': df_location.iloc[i].location} for i in range(len(df_location))],
            placeholder="Select a location",
        )
    return dcc.Dropdown(
        id='id_location_dropdown_2',
        options=[{'label': df_location.iloc[i].location + ' total_rating ' +
                  str(df_location.iloc[i].total_rating), 'value': df_location.iloc[i].location} for i in range(len(df_location))],
        placeholder="Select a location",
    )

# build user datatable


def build_user_zone(location_id=None):
    if location_id is None:
        userinfo = None
    else:
        # get current location's user list
        userinfo = df_user[df_user.index.isin(
            df_location_user.user.loc[[location_id]])][['id', 'total_rating']]
        userinfo = userinfo.round({'total_rating': 4})
        # sort by total rating, remove user whose rating=0
        userinfo = userinfo[userinfo.total_rating > 0].sort_values(
            ['total_rating'], ascending=False).reset_index().to_dict('records')
    return [build_table('id_user', [{"name": s, "id": s} for s in ("user", "total_rating")], userinfo, True)]


# define homepage and dashboard layout
section_header_style = {"margin-top": "0px",
                        "margin-bottom": "50px", "text-align": "center"}
app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(
            label='Home',
            children=build_homepage_text()
        ),
        dcc.Tab(
            label='Dashboard',
            children=[
                dbc.Row([
                    dbc.Col(children=[
                        html.H4("Business Unit/Location",
                                style=section_header_style),
                        html.Div(id='id_location_top_selection_div',
                                 children=build_location_top_selection()),
                        html.Div(id='id_location_dropdown_div',
                                 children=build_location_dropdown()),
                        html.Div(id='id_location_barchart_div')
                    ], width=4),
                    dbc.Col(children=[
                        html.H4("User List", style=section_header_style),
                        build_user_top_selection(),
                        html.Div(id='id_user_barchart_or_table_div',
                                 style={"margin-top": "50px"})
                    ], width=5),
                    dbc.Col(children=[html.H4(
                        "Role Description", style=section_header_style)] + build_detail_zone(), width=3),
                ], align='start', style={"margin-top": "50px"}),
                html.Div([
                    html.Div(children=[html.Div('Graphs Section')], style={
                             'paddingLeft': '15px', 'textAlign': 'left', "font-size": "28px", "background-color": "#ffeecc"}),
                    html.Div([
                        html.Div([
                            html.Div(id='user_rating_bar2'),
                            html.Div(id='user_rating_bar')
                        ],
                            style={'display': 'flex', 'flexDirection': 'row',
                                   'justifyContent': 'center'}
                        ),
                    ], style={'marginLeft': '2%', 'marginTop': '1%'}),
                ], style={'marginTop': '50px'})
            ]
        ),
    ]),
    html.Div(id='id_selected_location', style={'display': 'none'}),
    html.Div(id='id_selected_user', style={'display': 'none'}),
], style={'width': '100vw', 'marginBottom': '100px'})


# interative features: input detected in location zone, from either dropdown or barchart
@app.callback(Output('id_selected_location', 'children'),
              Output('id_location_barchart_div', 'children'),
              #Output('id_location_top_selection', 'active_cell'),
              #Output('id_location_top_selection', 'selected_cells'),
              Input('id_location_dropdown', 'value'),
              Input({'type': 'id_location_barchart', 'index': ALL}, 'clickData'),
              Input('id_location_top_selection', 'active_cell')
              )
def callback_location_input(dropdown_id, clickDataAll, active_cell):
    barchart_index = {'location_top5': 5, 'location_top10': 10}
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update#, dash.no_update, dash.no_update
    else:
        fire_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if fire_id == 'id_location_dropdown':
            return dropdown_id, None#, None, []
        elif fire_id == 'id_location_top_selection':
            if active_cell is None:
                return dash.no_update, dash.no_update#, dash.no_update, dash.no_update
            elif active_cell['column_id'] == 'top':  # first column selected
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update
            else:
                return None, build_location_barchart(int(active_cell['row_id']))#, dash.no_update, dash.no_update
        else:
            return clickDataAll[0]['points'][0]['x'], dash.no_update#, dash.no_update, dash.no_update


# # interative features: new location selected, or input in user topX selection
@app.callback(Output('id_user_barchart_or_table_div', 'children'),
              #Output('id_user_top_selection', 'active_cell'),
              #Output('id_user_top_selection', 'selected_cells'),
              Output('id_location_top_selection_div', 'children'),
              Output('id_location_dropdown_div', 'children'),
              Input('id_selected_location', 'children'),
              Input('id_user_top_selection', 'active_cell')
              )
def callback_user_top_input(location_id, active_cell):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update
    else:
        fire_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if fire_id == 'id_selected_location':
            return None if location_id is None else build_user_table(location_id), dash.no_update, dash.no_update
        else:
            if active_cell is None or active_cell['column_id'] == 'top':
                return dash.no_update, dash.no_update, dash.no_update
            else:
                return [build_user_barchart(active_cell['column_id'], int(active_cell['row_id'])),
                        build_location_top_selection(),
                        build_location_dropdown()]


# interative features: input detected in user table/barchart zone
@app.callback(Output('id_selected_user', 'children'),
              Input({'type': 'id_user_table', 'index': ALL}, 'selected_row_ids'),
              Input({'type': 'id_user_barchart', 'index': ALL}, 'clickData'),
              )
def callback_user_table_chart_input(row_id, clickDataAll):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    else:
        fire_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if json.loads(fire_id)['type'] == 'id_user_table':
            return dash.no_update if row_id is None or row_id[0] is None else row_id[0][0]
        else:
            try:
                r = clickDataAll[0]['points'][0]['x']
            except Exception:
                r = dash.no_update
            return r


# interative features: new user selected
@app.callback(Output('id_detail_disposals', 'data'),
              Output('id_detail_location', 'data'),
              Output('id_detail_receiving', 'data'),
              Input('id_selected_user', 'children'))
def callback_user_selected(user_id):
    if user_id is None:
        return dash.no_update, dash.no_update, dash.no_update
    info = df_user.loc[user_id]
    detail_disposal = [info[["scan_type_#", "ret_date_#",
                             "disp_doc_#", "err_cost_disposals"]].to_dict()]
    detail_location = [
        info[["val_ds584_flag_#", "err_cost_locations"]].to_dict()]
    detail_receiving = [
        info[["misclf_fap_#", "cre_mthod_#", "err_cost_receiving"]].to_dict()]
    return detail_disposal, detail_location, detail_receiving


def build_user_rating_bar2(df_user, user_id=None):
    if not user_id:
        color = ['#186ded' for x in range(len(df_user))]
    else:
        color = ['#186ded' if x['id'] !=
                 user_id else '#e30909' for i, x in df_user.iterrows()]
    df_user = df_user.sort_values(
        by=['total_rating'], ascending=False).reset_index(drop=True)
    bar2 = go.Figure(data=go.Bar(
        x=df_user['id'],
        y=df_user['total_rating'],
        marker=dict(color=color)),

        layout={'title': {
            'text': 'Error Rating Per Users',
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        }})
    bar2.update_layout(xaxis_title="User", yaxis_title="Error Rating")
    return [html.Div(dcc.Graph(figure=bar2))]

# Function to create and return bar chart


def build_user_rating_bar(user_info, cols=['disposals_rating', 'locations_rating', 'receiving_rating']):
    #ratings = ["{:0,.4f}".format(float(user_info[col])) for col in cols]
    ratings = [round(float(user_info[col]), 4) for col in cols]
    bar = go.Figure(data=go.Bar(
        x=[col.replace('_', ' ').title() for col in cols],
        y=ratings,
        text=ratings,
        textposition='auto',
        marker_color=['#186ded', '#0ac45e', '#f0e443']
    ),
        layout={'title': {
            'text': 'Error Rating Each Roles',
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        }})
    bar.update_layout(xaxis_title="User Roles", yaxis_title="Error Rating")
    return [html.Div(dcc.Graph(figure=bar))]

# main callback to udpate data table content upon input


@app.callback([Output('user_rating_bar', 'children'),
               Output('user_rating_bar2', 'children')],
              [Input('id_location_dropdown', 'value'),
               Input('id_selected_user', 'children')],
              prevent_initial_call=True
              )
def update_info(location_id, user_id):
    ctx = dash.callback_context
    if not ctx.triggered:
        return ['', '']
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    location_users = df_user[df_user.index.isin(
        df_location_user.user.loc[[location_id]])]
    location_users = location_users[location_users.total_rating > 0].sort_values(
        ['total_rating'], ascending=False).reset_index(drop=True)

    # selcted a new location
    if button_id == 'id_location_dropdown':
        user_rating_bar2 = build_user_rating_bar2(location_users)
        return ['', user_rating_bar2]
    # selected a new user
    elif button_id == 'id_selected_user':
        info = df_user.loc[user_id]
        user_rating_bar = build_user_rating_bar(info)
        user_rating_bar2 = build_user_rating_bar2(location_users, user_id)
        return [user_rating_bar, user_rating_bar2]
    else:
        print('ERROR: unhandled input', button_id)


# run web server at port 8050
if __name__ == "__main__":
    app.run_server(debug=False, host='0.0.0.0', port=8050)
