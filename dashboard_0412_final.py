# import tables
import dash
import dash_table
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Output, Input, State
import pandas as pd
import boto3
import io
import plotly.graph_objects as go
import plotly.express as px

# set path and name of data files
is_data_on_s3 = True  # True: use csv on s3, False: csv on local disk
s3_bucket = 'dean690-dataset'
file_location = 'table.Location_Rating.0412.csv'
file_user = 'table.Rating.0412.csv'
file_location_user_disposals = 'table.processed_disposals_df_1.0412.csv'
file_location_user_receiving = 'table.processed_receiving_df_1.0412.csv'
file_location_user_locations = 'table.processed_locations_df_1.0412.csv'
rating_all = 'table.Rating_all.0412.csv'


# create a function to get the files on s3
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
#else:
#    df_location = pd.read_csv(file_location)
#    df_user = pd.read_csv(file_user)
#    df_location_user_disposals = pd.read_csv(file_location_user_disposals)
#    df_location_user_receiving = pd.read_csv(file_location_user_receiving)
#    df_location_user_locations = pd.read_csv(file_location_user_locations)
df_all_user = df_user.sort_values('total_rating', ascending=False)
df_all_user = df_all_user.nlargest(100,'total_rating')

df_all_location = df_location.sort_values('total_rating', ascending=False)
df_all_location = df_all_location.nlargest(100,'total_rating')



df_location = df_location.sort_values('total_rating', ascending=False)[['location', 'total_rating']]
df_location['id'] = df_location.location
df_user = df_user.set_index('user')
df_user['id'] = df_user.index
#Prepare pie chart

## Disposals count

disp_error_count = 0
disp_correct_count = 0
for i in range(len(df_rating_all)):
    if (df_rating_all['disposals_rating'][i] == 0) and df_rating_all['disposal_role'][i] == 1 :disp_correct_count = disp_correct_count +1
    else:disp_error_count = disp_error_count +1

## Location count
loc_error_count = 0
loc_correct_count = 0
for i in range(len(df_rating_all)):
    if (df_rating_all['locations_rating'][i] == 0) and df_rating_all['locations_role'][i] == 1 :loc_correct_count = loc_correct_count +1
    else:loc_error_count = loc_error_count +1

## Receiving count
recv_error_count = 0
recv_correct_count = 0
for i in range(len(df_rating_all)):
    if (df_rating_all['receiving_rating'][i] == 0) and df_rating_all['receiving_role'][i] == 1 :recv_correct_count = recv_correct_count +1
    else:recv_error_count = recv_error_count +1

# combine 3 role's location-user mapping
df_location_user = pd.concat([df_location_user_disposals, df_location_user_receiving, df_location_user_locations])[['location', 'user']].drop_duplicates(ignore_index=True).set_index('location')

# init Dash app
app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])


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
def build_location_zone():
    return dcc.Dropdown(
        id='id_location_dropdown',
        options=[{'label': df_location.iloc[i].location + ' total_rating ' + str(df_location.iloc[i].total_rating), 'value': df_location.iloc[i].location} for i in range(len(df_location))],
        placeholder="Select a location",
    )


# build user datatable
def build_user_zone(location_id=None):
    if location_id is None:
        userinfo = None
    else:
        # get current location's user list
        userinfo = df_user[df_user.index.isin(df_location_user.user.loc[[location_id]])][['id', 'total_rating']]
        userinfo =  userinfo.round({'total_rating': 4})
        # sort by total rating, remove user whose rating=0
        userinfo = userinfo[userinfo.total_rating > 0].sort_values(['total_rating'], ascending=False).reset_index().to_dict('records')
    return [build_table('id_user', [{"name": s, "id": s} for s in ("user", "total_rating")], userinfo, True)]


# build layout for user detail tables
def build_detail_zone():
    return [
        build_table('id_detail_disposals',
                    [{"name": ["Role Disposals", "Number of error action (scan_type_#)"], "id": "scan_type_#"},
                     {"name": ["Role Disposals", "Number of error action (ret_date_#)"], "id": "ret_date_#"},
                     {"name": ["Role Disposals", "Number of error action (disp_doc_#)"], "id": "disp_doc_#"},
                     {"name": ["Role Disposals", "Involved error cost (err_cost_disposals)"], "id": "err_cost_disposals"}],
                    None, False),
        build_table('id_detail_location',
                    [{"name": ["Role Location", "Number of error action (val_ds584_flag_#)"], "id": "val_ds584_flag_#"},
                     {"name": ["Role Location", "Involved error cost (err_cost_locations)"], "id": "err_cost_locations"}],
                    None, False),
        build_table('id_detail_receiving',
                    [{"name": ["Role Receiving", "Number of error action (misclf_fap_#)"], "id": "misclf_fap_#"},
                     {"name": ["Role Receiving", "Number of error action (cre_mthod_#)"], "id": "cre_mthod_#"},
                     {"name": ["Role Receiving", "Involved error cost (err_cost_receiving)"], "id": "err_cost_receiving"}],
                    None, False)
    ]


# Function to create and return bar chart 
def build_user_rating_bar(user_info, cols=['disposals_rating', 'locations_rating', 'receiving_rating']): 
    #ratings = ["{:0,.4f}".format(float(user_info[col])) for col in cols]
    ratings = [round(float(user_info[col]), 4) for col in cols]
    bar = go.Figure(data=go.Bar(
            x=[col.replace('_', ' ').title() for col in cols], 
            y=ratings,
            text=ratings,
            textposition='auto',
            marker_color=['#186ded', '#0ac45e', '#f0e443']),layout = {'title':'Error Rating Each Roles'})
    bar.update_layout(xaxis_title="User Roles",yaxis_title="Error Score")
    return [html.Div(dcc.Graph(figure=bar))]
    
def build_user_rating_bar2(df_user, user_id=None):
    if not user_id:
        color= ['#186ded' for x in range(len(df_user))] 
    else: 
        color= ['#186ded' if x['id']!=user_id else '#e30909' for i, x in df_user.iterrows()] 
    df_user = df_user.sort_values(by=['total_rating'], ascending=False).reset_index(drop=True)
    bar2 = go.Figure(data=go.Bar(
        x=df_user['id'],
        y=df_user['total_rating'], 
	marker = dict(color=color)),
	
	layout = {'title':'Error Rating Per Users'})
    bar2.update_layout(xaxis_title="User",yaxis_title="Error Score")
    return [html.Div(dcc.Graph(figure=bar2))]

trace1 = go.Bar(x=df_location.location,y=df_location.total_rating)

trace2 = go.Bar(name="Disposals_score",x=df_all_user.user,y=df_all_user.disposals_rating,offsetgroup=0)
trace3 = go.Bar(name="Locations_score",x=df_all_user.user,y=df_all_user.locations_rating,offsetgroup=0)
trace4 = go.Bar(name="Receiving_score",x=df_all_user.user,y=df_all_user.receiving_rating,offsetgroup=0)
rate_all = go.Bar(name="All_score",x=df_all_user.user,y=df_all_user.total_rating,offsetgroup=0)
pie_color = ['red','green']
trace5 = go.Pie(labels=['Error','Correct'],values = [disp_error_count,disp_correct_count],marker = dict(colors=pie_color))
trace6 = go.Pie(labels=['Error','Correct'],values = [loc_error_count,loc_correct_count],marker = dict(colors=pie_color))
trace7 = go.Pie(labels=['Error','Correct'],values = [recv_error_count,recv_correct_count],marker = dict(colors=pie_color))

# define dashboard layout
app.layout = html.Div([
    dcc.Store('bar_colors'), 
    dbc.Row([
        dbc.Col("USER TRAINING DASHBOARD", style={
            "height": "fit-content",
            "background-color": "#1e2130",
            "color": "#ADAFAE",
            "font-size": "28px",
            "display": "flex",
            "flex-direction": "row",
            "align-items": "center",
            "justify-content": "center",
            "border-bottom": "2px solid #4B5460",
            "padding": "1rem 10rem",
            "width": "100%",
        }),
    ]),
html.Div(children='This dasboard is show the visualization and list the users who need to be training and which the training area sorted by the urgency',style={'textAlign': 'left',"font-size": "28px","background-color": "#ffeecc"}),
   
    dcc.Graph(id='3roles', style={'width':'200vh','height':'fit-content'},figure = go.Figure(data=[rate_all,trace2,trace3,trace4],layout = {'title':'Top 100 Error Rating Each Users','xaxis':{'title':'Users'},'yaxis':{'title':'Error Score'}})),
    dcc.Graph(id='location', style={'width':'200vh'},figure = go.Figure(data=[trace1],layout = {'title':'Error Rating Each Locations','xaxis':{'title':'Users'},'yaxis':{'title':'Error Score'}})),
html.Div(children='The Percentage Of Error In Each Roles', style={'textAlign': 'left',"font-size": "28px","background-color": "#ffeecc"}),    
   dbc.Row([dbc.Col(dcc.Graph(id='Disposals Pie', style={'width':'50vh'},figure = go.Figure(data=[trace5],layout={'title':'Disposals'})))
    , dbc.Col(dcc.Graph(id='Locations Pie', style={'width':'50vh'},figure = go.Figure(data=[trace6],layout={'title':'Locations'})))
    , dbc.Col(dcc.Graph(id='Receiving Pie', style={'width':'50vh'},figure = go.Figure(data=[trace7],layout={'title':'Receiving'})))
]),
       
html.Div(children='The table below show the error rating for each users breakdown by location', style={'textAlign': 'left',"font-size": "28px","background-color": "#ffeecc"}),
    dbc.Row([
        dbc.Col(children=build_location_zone(), width=4),
        dbc.Col([
                html.Div(id='id_user_zone', children=build_user_zone()),
                html.Div(id='user_rating_bar2'),
            ], 
            width=4 
        ),
        dbc.Col([
            html.Div(build_detail_zone()), 
            html.Div(id='user_rating_bar')
        ], width=4),
    ], align='start'),

], style={'width': '100vw'})


# main callback to udpate data table content upon input
@app.callback([Output('id_user_zone', 'children'),
               Output('id_detail_disposals', 'data'),
               Output('id_detail_location', 'data'),
               Output('id_detail_receiving', 'data'), 
               Output('user_rating_bar', 'children'), 
               Output('user_rating_bar2', 'children')],
              [Input('id_location_dropdown', 'value'),
               Input('id_user', 'selected_row_ids')],
              [State('id_user_zone', 'children')], 
              prevent_initial_call=True
)
def update_info(location_id, user_id, current_user_zone):
    # print('update_info', location_id, user_id)
    detail_disposal = [{'scan_type_#': '', 'ret_date_#': '', 'disp_doc_#': '', 'err_cost_disposals': ''}]
    detail_location = [{'val_ds584_flag_#': '', 'err_cost_locations': ''}]
    detail_receiving = [{'misclf_fap_#': '', 'cre_mthod_#': '', 'err_cost_receiving': ''}]

    ctx = dash.callback_context
    if not ctx.triggered:
        return [build_user_zone(), detail_disposal, detail_location, detail_receiving]
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    location_users = df_user[df_user.index.isin(df_location_user.user.loc[[location_id]])]
    location_users = location_users[location_users.total_rating > 0].sort_values(['total_rating'], ascending=False).reset_index(drop=True)
    
    # selcted a new location
    if button_id == 'id_location_dropdown':
        user_rating_bar2 = build_user_rating_bar2(location_users)
        return [build_user_zone(location_id), detail_disposal, detail_location, detail_receiving, '', user_rating_bar2]
    # selected a new user
    elif button_id == 'id_user':
        info = df_user.loc[user_id[0]]
        detail_disposal = [info[["scan_type_#", "ret_date_#", "disp_doc_#", "err_cost_disposals"]].to_dict()]
        detail_location = [info[["val_ds584_flag_#", "err_cost_locations"]].to_dict()]
        detail_receiving = [info[["misclf_fap_#", "cre_mthod_#", "err_cost_receiving"]].to_dict()]
        user_rating_bar = build_user_rating_bar(info)
        user_rating_bar2 = build_user_rating_bar2(location_users, user_id[0])
        return [current_user_zone, detail_disposal, detail_location, detail_receiving, user_rating_bar, user_rating_bar2]
    else:
        print('ERROR: unhandled input', button_id)


# run web server at port 8050, open to public internet
if __name__ == "__main__":
    app.run_server(debug=False, port=8050, host="0.0.0.0")
