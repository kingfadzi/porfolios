from dash import dcc, html
import dash_bootstrap_components as dbc

def chart_layout():
    """
    Layout for all charts including the scatter plot.
    """
    return dbc.Col(
        [
            # Row: Active vs Inactive Repositories & Repository Classification
            dbc.Row(
                [
                    # Active vs Inactive
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.B("Active vs Inactive Repositories", className="text-center"),
                                    className="bg-light",
                                ),
                                dcc.Graph(
                                    id="active-inactive-bar",
                                    config={"displayModeBar": False},
                                    style={"height": 300},
                                ),
                            ],
                            className="mb-4",
                        ),
                        width=6,
                    ),
                    # Repository Classification
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.B("Repository Classification", className="text-center"),
                                    className="bg-light",
                                ),
                                dcc.Graph(
                                    id="classification-pie",
                                    config={"displayModeBar": False},
                                    style={"height": 300},
                                ),
                            ],
                            className="mb-4",
                        ),
                        width=6,
                    ),
                ],
                className="mb-4",
            ),

            # Contributors vs Commits Scatter Plot
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.B("Contributors vs Commits Scatter Plot", className="text-center"),
                        className="bg-light",
                    ),
                    dcc.Graph(
                        id="scatter-plot",
                        config={"displayModeBar": False},
                        style={"height": 300},
                    ),
                ],
                className="mb-4",
            ),

            # Repositories by Main Language
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.B("Repositories by Main Language", className="text-center"),
                        className="bg-light",
                    ),
                    dcc.Graph(
                        id="repos-by-language-bar",
                        config={"displayModeBar": False},
                        style={"height": 300},
                    ),
                ],
                className="mb-4",
            ),

            # CLOC Metrics by Language
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.B("CLOC Metrics by Language", className="text-center"),
                        className="bg-light",
                    ),
                    dcc.Graph(
                        id="cloc-bar-chart",
                        config={"displayModeBar": False},
                        style={"height": 300},
                    ),
                ],
                className="mb-4",
            ),

            # Repositories by IaC Type
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.B("Repositories by IaC Type", className="text-center"),
                        className="bg-light",
                    ),
                    dcc.Graph(
                        id="iac-bar-chart",
                        config={"displayModeBar": False},
                        style={"height": 300},
                    ),
                ],
                className="mb-4",
            ),

            # Programming Languages vs Contributor Buckets Heatmap
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.B("Programming Languages vs Contributor Buckets Heatmap", className="text-center"),
                        className="bg-light",
                    ),
                    dcc.Graph(
                        id="language-contributors-heatmap",
                        config={"displayModeBar": False},
                        style={"height": 600},
                    ),
                ],
                className="mb-4",
            ),

            # Row: Trivy Vulnerabilities & Semgrep Findings
            dbc.Row(
                [
                    # Trivy Vulnerabilities
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.B("Vulnerabilities by Severity (Shallow scan)", className="text-center"),
                                    className="bg-light",
                                ),
                                dcc.Graph(
                                    id="trivy-vulnerabilities-bar-chart",
                                    config={"displayModeBar": False},
                                    style={"height": 300},
                                ),
                            ],
                            className="mb-4",
                        ),
                        width=6,
                    ),
                    # Semgrep Findings
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.B("Standards Issues", className="text-center"),
                                    className="bg-light",
                                ),
                                dcc.Graph(
                                    id="semgrep-findings-bar-chart",
                                    config={"displayModeBar": False},
                                    style={"height": 300},
                                ),
                            ],
                            className="mb-4",
                        ),
                        width=6,
                    ),
                ],
                className="mb-4",
            ),

        ]
    )
