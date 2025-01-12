from dash import dcc, html
import dash_bootstrap_components as dbc

def filter_layout(host_names, languages, app_ids, classification_labels):
    return dbc.Col(
        [
            html.Label("Filter by Host Name:", className="form-label"),
            dcc.Dropdown(
                id="host-name-filter",
                options=[{"label": name, "value": name} for name in host_names],
                multi=True,
                placeholder="Select Host Name(s)",
                className="form-select mb-3",
            ),
            html.Label("Filter by Main Language:", className="form-label"),
            dcc.Dropdown(
                id="language-filter",
                options=[{"label": lang, "value": lang} for lang in languages],
                multi=True,
                placeholder="Select Language(s)",
                className="form-select mb-3",
            ),
            html.Label("Filter by App ID:", className="form-label"),
            dcc.Dropdown(
                id="app-id-filter",
                options=[{"label": app, "value": app} for app in app_ids],
                multi=True,
                placeholder="Select App ID(s)",
                className="form-select mb-3",
            ),
            html.Label("Filter by Classification:", className="form-label"),
            dcc.Dropdown(
                id="classification-filter",
                options=[
                    {"label": label, "value": label} for label in classification_labels
                ],
                multi=True,
                placeholder="Select Classification(s)",
                className="form-select mb-3",
            ),
        ],
        width=3,
    )