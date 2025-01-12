from dash import Input, Output
from data.data_loader import (
    fetch_active_inactive_data,
    fetch_classification_data,
    fetch_language_data,
    fetch_heatmap_data,
    fetch_dropdown_options,
)
from callbacks.viz_functions import create_bar_chart, create_pie_chart, create_language_chart, create_heatmap

def register_dropdown_callbacks(app):
    @app.callback(
        [
            Output("host-name-filter", "options"),
            Output("language-filter", "options"),
            Output("classification-filter", "options"),
            Output("activity-status-filter", "options"),  # New field
        ],
        [Input("app-layout", "children")]  # Trigger callback on app layout load
    )
    def populate_dropdown_options(_):
        # Fetch dropdown options dynamically
        options = fetch_dropdown_options()
        
        return (
            [{"label": name, "value": name} for name in options["host_names"]],
            [{"label": lang, "value": lang} for lang in options["languages"]],
            [{"label": label, "value": label} for label in options["classification_labels"]],
            [{"label": status, "value": status} for status in options["activity_statuses"]],  # Populate activity_status
        )

def register_callbacks(app):
    @app.callback(
        [
            Output("active-inactive-bar", "figure"),
            Output("classification-pie", "figure"),
            Output("repos-by-language-bar", "figure"),
            Output("heatmap-viz", "figure"),
        ],
        [
            Input("host-name-filter", "value"),
            Input("language-filter", "value"),
            Input("classification-filter", "value"),
            Input("activity-status-filter", "value"),  # New field
        ],
    )
    def update_charts(selected_hosts, selected_languages, selected_classifications, selected_statuses):
        # Create a dictionary of filters dynamically
        filters = {
            "host_name": selected_hosts,
            "main_language": selected_languages,
            "classification_label": selected_classifications,
            "activity_status": selected_statuses,  # Add activity_status to filters
        }

        # Fetch data for each visualization
        active_inactive_data = fetch_active_inactive_data(filters)
        classification_data = fetch_classification_data(filters)
        language_data = fetch_language_data(filters)
        heatmap_data = fetch_heatmap_data(filters)

        # Generate visualizations
        return (
            create_bar_chart(active_inactive_data),
            create_pie_chart(classification_data),
            create_language_chart(language_data),
            create_heatmap(heatmap_data),
        )