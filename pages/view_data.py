import dash
from dash import dcc, html, Input, Output, State, callback
import dash_ag_grid as dag

dash.register_page(__name__, path="/view_data")

# Layout for the page
layout = html.Div(
    [
        html.H1("View Data", style={"textAlign": "center"}),

        # Dropdown to select a dataset
        html.Div(
            [
                html.Label("Select a Dataset:"),
                dcc.Dropdown(
                    id="dataset-dropdown",
                    options=[
                        {"label": "Elective Cases", "value": "nu"},
                        {"label": "Surgeon Roster", "value": "sg"},
                        {"label": "Available Time (Summary)", "value": "dm"},
                        {"label": "Available Time (Dictionary)", "value": "dic"},
                    ],
                    placeholder="Select a dataset to view...",
                    style={"width": "50%"},
                ),
            ],
            style={"marginBottom": "20px"},
        ),

        # Placeholder to display the table
        html.Div(id="dataset-display", style={"marginTop": "20px"}),
    ],
    style={"padding": "20px", "backgroundColor": "#f8f9fa"},  # Light gray background for the page
)

@callback(
    Output("dataset-display", "children"),
    [Input("dataset-dropdown", "value")],
    [State("shared-store-files", "data")],
)

def display_dataset(selected_dataset, shared_data):
    if not shared_data or selected_dataset not in shared_data:
        return html.Div("Data not uploaded.", style={"color": "red", "fontStyle": "italic", "textAlign": "center"})

    dataset = shared_data[selected_dataset]

    # Calculate number of records and columns
    num_records = len(dataset)
    num_columns = len(dataset[0].keys()) if dataset else 0

    # Define the columns dynamically based on the dataset
    columnDefs = [
        {"headerName": col, "field": col} for col in dataset[0].keys()
    ]

    return html.Div(
        [
            # Display the number of records and columns
            html.P(
                f"Displaying {num_records} records and {num_columns} columns.",
                style={"marginBottom": "10px", "fontWeight": "bold", "fontSize": "16px"},
            ),
            dag.AgGrid(
                id="data-table",
                rowData=dataset,  # Provide the dataset as rowData
                columnDefs=columnDefs,  # Use column definitions
                columnSize=None,  # Automatically adjust column sizes
                defaultColDef={"sortable": True, "filter": True, "resizable": True},
                dashGridOptions={  # Configure pagination options here
                    "pagination": True,
                    "paginationPageSize": 20,  # Set the number of rows per page
                    "domLayout": "autoHeight",
                },
            ),
        ],
        style={
            "backgroundColor": "white",
            "padding": "20px",
            "borderRadius": "8px",
            "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
            "minHeight": "800px",
            "width": "100%",
            "margin": "0 auto",
        },
    )
