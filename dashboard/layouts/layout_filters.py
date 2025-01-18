from dash import dcc, html
import dash_bootstrap_components as dbc

def filter_layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        dbc.Label("Filter by Host Name", html_for="host-name-filter"),
                        dcc.Dropdown(
                            id="host-name-filter",
                            options=[],  # Options will be populated dynamically
                            multi=True,
                            placeholder="Select Host Name(s)",
                            clearable=True,
                            maxHeight=600,
                            optionHeight=50,
                            style={"fontSize": "14px"}
                        ),
                    ],
                    className="mb-4",
                ),
                html.Div(
                    [
                        dbc.Label("Filter by Activity Status", html_for="activity-status-filter"),
                        dcc.Dropdown(
                            id="activity-status-filter",
                            options=[],  # Options will be populated dynamically
                            multi=True,
                            placeholder="Select Activity Status",
                            clearable=True,
                            maxHeight=600,
                            optionHeight=50,
                            style={"fontSize": "14px"}
                        ),
                    ],
                    className="mb-4",
                ),
                html.Div(
                    [
                        dbc.Label("Filter by TC", html_for="tc-filter"),
                        dcc.Dropdown(
                            id="tc-filter",
                            options=[],  # Options will be populated dynamically
                            multi=True,
                            placeholder="Select TC(s)",
                            clearable=True,
                            maxHeight=600,
                            optionHeight=50,
                            style={"fontSize": "14px"}
                        ),
                    ],
                    className="mb-4",
                ),
                html.Div(
                    [
                        dbc.Label("Filter by Main Language", html_for="language-filter"),
                        dcc.Dropdown(
                            id="language-filter",
                            options=[],  # Options will be populated dynamically
                            multi=True,
                            placeholder="Select Language(s)",
                            clearable=True,
                            maxHeight=600,
                            optionHeight=50,
                            style={"fontSize": "14px"}
                        ),
                    ],
                    className="mb-4",
                ),
                html.Div(
                    [
                        dbc.Label(
                            [
                                "Filter by Classification",
                                html.Span(
                                    " ?",
                                    id="classification-help-text",
                                    style={"color": "blue", "cursor": "pointer", "fontSize": "14px"},
                                ),
                            ],
                            html_for="classification-filter",
                        ),
                        dbc.Tooltip(
                            r"""
                            Classification Guide:
                            - Tiny: <500 LOC, <20 files, <1MB.
                            - Small: <5,000 LOC, <200 files, <10MB.
                            - Medium: <50,000 LOC, <1,000 files, <100MB.
                            - Large: <100,000 LOC, <5,000 files, <1GB.
                            - Massive: ≥100,000 LOC, ≥5,000 files, ≥1GB.
                            - Unclassified: Doesn't fit any above criteria.
                            """,
                            target="classification-help-text",
                            placement="left",
                            style={
                                "whiteSpace": "pre-wrap",
                                "maxWidth": 600px",
                                "width": 600px",
                                "fontSize": "14px"
                            },
                        ),
                        dcc.Dropdown(
                            id="classification-filter",
                            options=[],  # Options will be populated dynamically
                            multi=True,
                            placeholder="Select Classification(s)",
                            clearable=True,
                            maxHeight=600,
                            optionHeight=50,
                            style={"fontSize": "14px"}
                        ),
                    ],
                    className="mb-4",
                ),
                html.Div(
                    [
                        dbc.Label("Filter by App ID", html_for="app-id-filter"),
                        dcc.Input(
                            id="app-id-filter",
                            type="text",
                            placeholder="Enter App IDs (comma-separated)...",
                            debounce=True,
                            className="form-control",
                            style={"fontSize": "14px"}
                        ),
                    ],
                    className="mb-4",
                ),
            ]
        ),
        className="bg-light mb-4",
    )