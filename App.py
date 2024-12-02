import sys
import os
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import threading
import webview

# Determine the base directory
if getattr(sys, 'frozen', False):
    # If the application is frozen (e.g., packaged with cx_Freeze)
    base_dir = os.path.dirname(sys.executable)
    resources_dir = os.path.join(os.path.dirname(base_dir), 'Resources')
else:
    # If the application is running as a script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    resources_dir = base_dir

# Set the assets and pages folder paths
assets_folder = os.path.join(resources_dir, 'assets')
pages_folder = os.path.join(resources_dir, 'pages')

# Initialize the app with the correct pages_folder path
app = dash.Dash(
    __name__,
    pages_folder=pages_folder,  # Set the pages_folder parameter
    assets_folder=assets_folder,
    use_pages=True,
    title="Surgery Block Time Dashboard",
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
server = app.server

# Sidebar layout
sidebar = html.Div(
    [
        dbc.Row(
            [
                html.Img(
                    src="assets/logos/hospital_logo.png",
                    style={
                        "maxWidth": "100%",
                        "maxHeight": "120px",
                        "width": "auto",
                        "height": "auto",
                        "display": "block",
                        "margin": "0 auto",
                    },
                )
            ],
            className="sidebar-logo",
        ),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Upload Data", href="/upload_data", active="exact"),
                dbc.NavLink("View Data", href="/view_data", active="exact"),
                dbc.NavLink("Process Data", href="/process_data", active="exact"),
                dbc.NavLink("Utilization Overview", href="/overview", active="exact"),
                dbc.NavLink("Utilization by Specialty", href="/specialty", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
        html.Div(
            [
                html.Span("Created by "),
                html.A(
                    "Your Name",
                    href="https://github.com/yourgithubprofile",
                    target="_blank",
                ),
                html.Br(),
                html.Span("Data Source "),
                html.A(
                    "Hospital Data",
                    href="https://example-data-source-link.com",
                    target="_blank",
                ),
            ],
            className="sidebar-footer",
        ),
    ],
    className="sidebar",
    style={
        "width": "250px",
        "position": "fixed",
        "height": "100%",
        "padding": "20px",
        "box-shadow": "2px 0px 5px rgba(0, 0, 0, 0.1)",
    },
)

# Content area
content = html.Div(
    [
        dcc.Store(id="shared-store-files", storage_type="local"),
        dcc.Store(id="shared-store-processed", storage_type="local"),
        dcc.Store(id="shared-store-replacement", storage_type="memory"),
        dash.page_container,
    ],
    style={
        "margin-left": "250px",
        "padding": "20px",
        "background-color": "#f8f9fa",
        "height": "100vh",
        "overflow": "auto",
    },
)

# App layout
app.layout = html.Div(
    [
        sidebar,
        content,
    ],
)

if __name__ == "__main__":
    app.run_server(port=8080, debug=True)
