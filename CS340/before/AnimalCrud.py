#mohamed babiker
# AnimalCrud.py

import base64
import logging
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_leaflet as dl
import dash_table
import pandas as pd
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from flask import Flask
from mongo import AnimalShelter  # Ensure you have the correct path

# Add other necessary imports
import plotly.express as px

# Create the dash application
app = dash.Dash(
    __name__,
    url_base_pathname="/animal-shelter/",
    suppress_callback_exceptions=True,
    prevent_initial_callbacks=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],  # Add Bootstrap theme
)

# username and password and CRUD Python module name
username = "accuser"
password = "aacuserpass"
aac = AnimalShelter(username, password)
logger = logging.getLogger(__name__)
logger.info(f"Connected to {aac.database.name} Database")

# Add in Grazioso Salvare’s logo
image_filename_logo = "data/GraziosoSalvareLogo.png"
encoded_image_logo = base64.b64encode(open(image_filename_logo, "rb").read())

image_filename_dog = "data/australian_shepherd.jpg"
encoded_image_dog = base64.b64encode(open(image_filename_dog, "rb").read())

query = aac.read_all()
df = pd.DataFrame.from_records(query)

# Declare the application interfaces
app.layout = html.Div(
    [
        html.Hr(),
        html.Div(id="query_out"),
        html.Div(id="hidden_div", style={"display": "none"}),
        html.Div(
            [
                dbc.Col(
                    [
                        html.A(
                            [
                                html.Img(
                                    src="data:image/png;base64,{}".format(
                                        encoded_image_logo.decode()
                                    ),
                                    style={"height": "200px"},
                                )
                            ],
                            href="https://www.snhu.edu",
                        ),
                        html.Img(
                            src="data:image/png;base64,{}".format(encoded_image_dog.decode()),
                            style={"height": "200px"},
                            className="align-right",
                        ),
                        html.H4(
                            children="Created by Arys Pena",
                            style={"textAlign": "right", "color": "white"},
                        ),
                        html.B(
                            html.Center(
                                [
                                    html.H1(
                                        "Grazioso Salvare Animal Shelter Web Application Dashboard"
                                    ),
                                    html.H3("Web Application Dashboard"),
                                ]
                            ),
                            style={"color": "white"},
                        ),
                    ],
                    className="col-6",
                ),
            ],
            style={"height": "auto", "width": "auto", "backgroundColor": "#0067b9",},
        ),
        html.Hr(),
        html.Div(
            [
                html.B("Step 1: "),
                "Select a rescue type from the options below:",
                html.Br(),
                dcc.RadioItems(
                    id="radio_items_id",
                    options=[
                        {"label": "Water Rescue", "value": "WR"},
                        {"label": "Mountain Rescue", "value": "MR"},
                        {"label": "Disaster Rescue", "value": "DR"},
                        {"label": "Reset", "value": "R"},
                    ],
                    labelStyle={"display": "inline-block"},
                ),
                html.Br(),
                html.B("Step 2: "),
                "Click on the circle on the left of the row within the table to filter the plots below. Clicking on a row highlights the dog's name in the bar chart.",
                html.Br(),
            ]
        ),
        html.Div(
            [
                dash_table.DataTable(
                    id="datatable_id",
                    columns=[
                        {"name": i, "id": i, "deletable": False, "selectable": True}
                        for i in df.columns
                    ],
                    editable=False,
                    filter_action="native",
                    row_selectable="single",
                    selected_columns=[],
                ),
                html.Br(),
                html.B("Step 3: "),
                "Click 'Reset' to display all results (limited to 40 for performance).",
            ]
        ),
        html.Br(),
        html.Hr(),
        html.Div(
            dbc.Row(
                [
                    dbc.Col(html.Div(id="datatable_id_container"), width=6),
                    dbc.Col(html.Div(id="map_id"), width=6),
                ],
            ),
        ),
    ]
)

# Interaction Between Components / Controller
# This callback will highlight a row on the data table when the user selects it
@app.callback(
    Output("datatable_id", "style_data_conditional"), [Input("datatable_id", "selected_columns")]
)
def update_styles(selected_columns):
    return [{"if": {"column_id": i}, "background_color": "#D2F3FF"} for i in selected_columns]

@app.callback(
    Output("datatable_id_container", "children"),
    [
        Input("datatable_id", "derived_virtual_data"),
        Input("datatable_id", "derived_virtual_selected_rows"),
    ],
)
def update_graphs(derived_virtual_data, derived_virtual_selected_rows):
    if derived_virtual_selected_rows is None:
        derived_virtual_selected_rows = []

    dff = df if derived_virtual_data is None else pd.DataFrame(derived_virtual_data)

    colors = [
        "#7FDBFF" if i in derived_virtual_selected_rows else "#0074D9" for i in range(len(dff))
    ]

    return [
        dcc.Graph(
            id=column,
            figure={
                "data": [{"x": dff["name"], "type": "bar", "marker": {"color": colors},}],
                "layout": {
                    "xaxis": {"automargin": True},
                    "yaxis": {"automargin": True, "title": {"text": column}},
                    "height": 250,
                    "margin": {"t": 10, "l": 10, "r": 10},
                },
            },
        )
        for column in ["age_upon_outcome_in_weeks"]
        if column in dff
    ]

@app.callback(Output("datatable_id", "data"), [Input("radio_items_id", "value")])
def update_datatable(value):
    if value == "R":
        df = pd.DataFrame.from_records(aac.read_all()).to_dict("records")
        print("Reset button pressed")
        return df
    if value == "WR":
        df = pd.DataFrame.from_records(aac.filter_water_rescue())
        print(f"Filtered to Water Rescue \n {df.head(5)}")
        return df.to_dict("records")
    if value == "MR":
        df = pd.DataFrame.from_records(aac.filter_mountain_wilderness())
        print(f"Filtered to Mountain  \n {df.head(5)}")
        return df.to_dict("records")
    if value == "DR":
        df = pd.DataFrame.from_records(aac.filter_disaster_rescue_tracking())
        print(f"Filtered to Disaster Rescue \n {df.head(5)}")
        return df.to_dict("records")

@app.callback(
    Output("map_id", "children"),
    [
        Input("datatable_id", "derived_virtual_data"),
        Input("datatable_id", "derived_virtual_selected_rows"),
    ],
)
def update_map(derived_virtual_data, selected_row_index):
    dff = df if selected_row_index is None else pd.DataFrame(derived_virtual_data)
    if selected_row_index is None or selected_row_index is None or len(selected_row_index) == 0:
        raise PreventUpdate

    return [
        dl.Map(
            style={"width": "1000px", "height": "500px"},
            center=[
                float(dff.iloc[selected_row_index, 13].values[0]),
                float(dff.iloc[selected_row_index, 14].values[0]),
            ],
            zoom=10,
            children=[
                dl.TileLayer(id=f"base_layer_id"),
                dl.Marker(
                    position=[
                        float(dff.iloc[selected_row_index, 13].values[0]),
                        float(dff.iloc[selected_row_index, 14].values[0]),
                    ],
                    children=[
                        dl.Tooltip(dff.iloc[selected_row_index, 4]),
                        dl.Popup(
                            [html.H2("Animal Name"), html.P(dff.iloc[selected_row_index, 9])]
                        ),
                    ],
                ),
            ],
        )
    ]

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", debug=True)
