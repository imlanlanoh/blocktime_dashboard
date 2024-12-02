import dash
from dash import dcc, html, Input, Output, State, callback
import pandas as pd
import io
import base64

dash.register_page(__name__, path="/upload_data")

# Layout for the page
layout = html.Div(
    [
        html.H1("Upload Data", style={"textAlign": "center"}),

        # Upload sections
        html.Div(
            [
                # Elective Cases Upload
                html.Div(
                    [
                        html.H2("Elective Cases", style={"textAlign": "left", "marginBottom": "10px"}),
                        dcc.Upload(
                            id="upload-nu",
                            children=html.Button("Click to Upload Elective Cases", className="btn btn-primary"),
                            style={"border": "1px dashed #ccc", "padding": "20px"},
                        ),
                        html.Div(id="upload-nu-status", style={"marginTop": "10px", "color": "green"}),  # Message area
                    ],
                    style={
                        "backgroundColor": "white",
                        "padding": "20px",
                        "marginBottom": "20px",
                        "borderRadius": "8px",
                        "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
                    },  # White box styling
                ),

                # Surgeon Roster Upload
                html.Div(
                    [
                        html.H2("Surgeon Roster", style={"textAlign": "left", "marginBottom": "10px"}),
                        dcc.Upload(
                            id="upload-sg",
                            children=html.Button("Click to Upload Surgeon Roster", className="btn btn-primary"),
                            style={"border": "1px dashed #ccc", "padding": "20px"},
                        ),
                        html.Div(id="upload-sg-status", style={"marginTop": "10px", "color": "green"}),  # Message area
                    ],
                    style={
                        "backgroundColor": "white",
                        "padding": "20px",
                        "marginBottom": "20px",
                        "borderRadius": "8px",
                        "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
                    },  # White box styling
                ),

                # Available Time Upload
                html.Div(
                    [
                        html.H2("Available Time", style={"textAlign": "left", "marginBottom": "10px"}),
                        dcc.Upload(
                            id="upload-dm",
                            children=html.Button("Click to Upload Available Time", className="btn btn-primary"),
                            style={"border": "1px dashed #ccc", "padding": "20px"},
                        ),
                        html.Div(id="upload-dm-status", style={"marginTop": "10px", "color": "green"}),  # Message area
                    ],
                    style={
                        "backgroundColor": "white",
                        "padding": "20px",
                        "marginBottom": "20px",
                        "borderRadius": "8px",
                        "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
                    },  # White box styling
                ),
            ],
            style={"maxWidth": "800px", "margin": "0 auto"},  # Center the sections
        ),
    ],
    style={"backgroundColor": "#f8f9fa", "padding": "40px"},  # Light gray background for the page
)


# Callbacks to handle file uploads and show status messages
@callback(
    [
        Output("upload-nu-status", "children"),
        Output("upload-sg-status", "children"),
        Output("upload-dm-status", "children"),
        Output("shared-store-files", "data"),  # Store the data
    ],
    [
        Input("upload-nu", "contents"),
        Input("upload-sg", "contents"),
        Input("upload-dm", "contents"),
    ],
    [
        State("upload-nu", "filename"),
        State("upload-sg", "filename"),
        State("upload-dm", "filename"),
        State("shared-store-files", "data"),
    ],
    prevent_initial_call=True,
)
def handle_file_upload(upload_nu, upload_sg, upload_dm, filename_nu, filename_sg, filename_dm, shared_data):
    shared_data = shared_data or {}
    nu_status = sg_status = dm_status = None

    # Handle Elective Cases upload
    if upload_nu:
        shared_data["nu"] = process_upload(upload_nu)
        nu_status = f"File '{filename_nu}' uploaded successfully!"

    # Handle Surgeon Roster upload
    if upload_sg:
        shared_data["sg"] = process_upload(upload_sg)
        sg_status = f"File '{filename_sg}' uploaded successfully!"

    # Handle Available Time upload
    if upload_dm:
        shared_data["dm"] = process_upload_xlsm(upload_dm, sheet_name="Summary by Each Month")
        shared_data["dic"] = process_upload_xlsm(upload_dm, sheet_name="Dictionary")
        dm_status = f"File '{filename_dm}' uploaded successfully!"

    return nu_status, sg_status, dm_status, shared_data


# Helper function to process uploads
def process_upload(contents):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    return pd.read_excel(io.BytesIO(decoded)).to_dict("records")


def process_upload_xlsm(contents, sheet_name):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    return pd.read_excel(io.BytesIO(decoded), sheet_name=sheet_name).to_dict("records")
