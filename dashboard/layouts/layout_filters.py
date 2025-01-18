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
                        dbc.Label("Filter by Classification", html_for="classification-filter"),
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
                        dbc.Button(
                            "Show Classification Details",
                            id="classification-toggle",
                            color="link",
                            className="mt-2",
                        ),
                        dbc.Collapse(
                            html.Div(
                                "Classification values represent the categorization of repositories. For example, 'Critical' indicates high-priority repositories, while 'Deprecated' indicates repositories that are no longer maintained.",
                                className="text-muted",
                                style={"fontSize": "12px"}
                            ),
                            id="classification-collapse",
                            is_open=False,
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