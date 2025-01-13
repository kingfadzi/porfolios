from dash import dcc, html
import dash_bootstrap_components as dbc

def filter_layout():
    return dbc.Col(
        [
            html.Label("Filter by Host Name:", className="form-label"),
            dcc.Dropdown(
                id="host-name-filter",
                options=[],  # Empty options, will be populated dynamically
                multi=True,
                placeholder="Select Host Name(s)",
                className="form-select mb-3",
            ),
            html.Label("Filter by Activity Status:", className="form-label"),
            dcc.Dropdown(
                id="activity-status-filter",
                options=[],  # Empty options, will be populated dynamically
                multi=True,
                placeholder="Select Activity Status",
                className="form-select mb-3",
            ),
            html.Label("Filter by TC Cluster:", className="form-label"),
            dcc.Dropdown(
                id="tc-cluster-filter",
                options=[],  # Empty options, will be populated dynamically
                multi=True,
                placeholder="Select TC Cluster(s)",
                className="form-select mb-3",
            ),
            html.Label("Filter by TC:", className="form-label"),
            dcc.Dropdown(
                id="tc-filter",
                options=[],  # Empty options, will be populated dynamically
                multi=True,
                placeholder="Select TC(s)",
                className="form-select mb-3",
            ),
            html.Label("Filter by Main Language:", className="form-label"),
            dcc.Dropdown(
                id="language-filter",
                options=[],  # Empty options, will be populated dynamically
                multi=True,
                placeholder="Select Language(s)",
                className="form-select mb-3",
            ),
            html.Label("Filter by Classification:", className="form-label"),
            dcc.Dropdown(
                id="classification-filter",
                options=[],  # Empty options, will be populated dynamically
                multi=True,
                placeholder="Select Classification(s)",
                className="form-select mb-3",
            ),
            html.Label("Filter by App ID:", className="form-label"),
            dcc.Input(
                id="app-id-filter",
                type="text",
                placeholder="Enter App IDs (comma-separated)...",
                debounce=True,  # Trigger callback only after typing stops
                className="form-control mb-3",
            ),
        ],
        width=3,
    )