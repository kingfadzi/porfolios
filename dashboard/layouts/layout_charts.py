from dash import dcc, html
import dash_bootstrap_components as dbc

def chart_layout():
    return dbc.Col(
        [
            # Row: Active vs Inactive Repositories & Repository Classification
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.B("Activity Status", className="text-center"),
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

            # Row: Language Usage Buckets & Repository Activity by Last Commit Date
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.B("Language Usage Buckets", className="text-center"),
                                    className="bg-light",
                                ),
                                dcc.Graph(
                                    id="language-usage-buckets-bar",
                                    config={"displayModeBar": False},
                                    style={"height": 300},
                                ),
                            ],
                            className="mb-4",
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.B("Repository Activity by Last Commit Date", className="text-center"),
                                    className="bg-light",
                                ),
                                dcc.Graph(
                                    id="last-commit-buckets-bar",
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


            # Row: Category vs Technology (Stacked Bar)
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.B("Category vs Technology Usage", className="text-center"),
                                    className="bg-light",
                                ),
                                dcc.Graph(
                                    id="label-tech-bar-chart",
                                    config={"displayModeBar": False},
                                    style={"height": 300},
                                ),
                            ],
                            className="mb-4",
                        ),
                        width=12,
                    ),
                ],
                className="mb-4",
            ),

            # Row 1: java-version, build-tool
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(html.B("Java Version: Category vs Technology Usage", className="text-center")),
                        dcc.Graph(id="label-tech-bar-chart-java-version", config={"displayModeBar": False}, style={"height": 300}),
                    ], className="mb-4"),
                    width=6
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(html.B("Build Tool: Category vs Technology Usage", className="text-center")),
                        dcc.Graph(id="label-tech-bar-chart-build-tool", config={"displayModeBar": False}, style={"height": 300}),
                    ], className="mb-4"),
                    width=6
                ),
            ], className="mb-4"),

            # Row 2: appserver, database
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(html.B("App Server: Category vs Technology Usage", className="text-center")),
                        dcc.Graph(id="label-tech-bar-chart-appserver", config={"displayModeBar": False}, style={"height": 300}),
                    ], className="mb-4"),
                    width=6
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(html.B("Database: Category vs Technology Usage", className="text-center")),
                        dcc.Graph(id="label-tech-bar-chart-database", config={"displayModeBar": False}, style={"height": 300}),
                    ], className="mb-4"),
                    width=6
                ),
            ], className="mb-4"),

            # Row 3: spring-framework-version, spring-boot-version
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(html.B("Spring Framework Version: Category vs Technology Usage", className="text-center")),
                        dcc.Graph(id="label-tech-bar-chart-spring-framework-version", config={"displayModeBar": False}, style={"height": 300}),
                    ], className="mb-4"),
                    width=6
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(html.B("Spring Boot Version: Category vs Technology Usage", className="text-center")),
                        dcc.Graph(id="label-tech-bar-chart-spring-boot-version", config={"displayModeBar": False}, style={"height": 300}),
                    ], className="mb-4"),
                    width=6
                ),
            ], className="mb-4"),

            # Row 4: middleware, logging
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(html.B("Middleware: Category vs Technology Usage", className="text-center")),
                        dcc.Graph(id="label-tech-bar-chart-middleware", config={"displayModeBar": False}, style={"height": 300}),
                    ], className="mb-4"),
                    width=6
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(html.B("Logging: Category vs Technology Usage", className="text-center")),
                        dcc.Graph(id="label-tech-bar-chart-logging", config={"displayModeBar": False}, style={"height": 300}),
                    ], className="mb-4"),
                    width=6
                ),
            ], className="mb-4"),

        ]
    )
