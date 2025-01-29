from dash import Input, Output
from data.fetch_dropdown_options import fetch_dropdown_options
from data.fetch_contributors_commits_size import fetch_contributors_commits_size
from data.fetch_iac_data import fetch_iac_data
from data.fetch_active_inactive_data import fetch_active_inactive_data
from data.fetch_classification_data import fetch_classification_data
from data.fetch_language_data import fetch_language_data
from data.fetch_heatmap_data import fetch_heatmap_data
from callbacks.viz_contributors_commits_size import viz_contributors_commits_size
from callbacks.viz_iac_chart import viz_iac_chart
from callbacks.viz_active_inactive import viz_active_inactive
from callbacks.viz_classification import viz_classification
from callbacks.viz_main_language import viz_main_language
from data.fetch_cloc_by_language import fetch_cloc_by_language
from callbacks.viz_cloc_by_language import viz_cloc_by_language
from data.fetch_language_contributors_heatmap import fetch_language_contributors_heatmap
from callbacks.viz_language_contributors_heatmap import viz_language_contributors_heatmap
from data.fetch_trivy_vulnerabilities import fetch_trivy_vulnerabilities
from callbacks.viz_trivy_vulnerabilities import viz_trivy_vulnerabilities
from data.fetch_semgrep_findings import fetch_semgrep_findings
from callbacks.viz_semgrep_findings import viz_semgrep_findings
from data.fetch_multi_language_usage import fetch_multi_language_usage
from callbacks.viz_multi_language_usage import viz_multi_language_usage
from data.fetch_last_commit_buckets import fetch_last_commit_buckets
from callbacks.viz_last_commit_buckets import viz_last_commit_buckets
from data.fetch_label_tech_data import fetch_label_tech_data
from callbacks.viz_label_tech import viz_label_tech
from data.fetch_kpi_data import fetch_kpi_data

def register_dropdown_callbacks(app):
    @app.callback(
        [
            Output("host-name-filter", "options"),
            Output("activity-status-filter", "options"),
            Output("tc-filter", "options"),
            Output("language-filter", "options"),
            Output("classification-filter", "options"),
        ],
        [Input("app-layout", "children")]
    )
    def populate_dropdown_options(_):
        options = fetch_dropdown_options()
        return (
            [{"label": name, "value": name} for name in options["host_names"]],
            [{"label": status, "value": status} for status in options["activity_statuses"]],
            [{"label": tc, "value": tc} for tc in options["tcs"]],
            [{"label": lang, "value": lang} for lang in options["languages"]],
            [{"label": label, "value": label} for label in options["classification_labels"]],
        )

def register_callbacks(app):
    @app.callback(
        [
            Output("active-inactive-bar", "figure"),
            Output("classification-pie", "figure"),
            Output("scatter-plot", "figure"),
            Output("repos-by-language-bar", "figure"),
            Output("cloc-bar-chart", "figure"),
            Output("iac-bar-chart", "figure"),
            Output("language-contributors-heatmap", "figure"),
            Output("trivy-vulnerabilities-bar-chart", "figure"),
            Output("semgrep-findings-bar-chart", "figure"),
            Output("language-usage-buckets-bar", "figure"),
            Output("last-commit-buckets-bar", "figure"),

            Output("label-tech-bar-chart-java-version", "figure"),
            Output("label-tech-bar-chart-build-tool", "figure"),
            Output("label-tech-bar-chart-appserver", "figure"),
            Output("label-tech-bar-chart-database", "figure"),
            Output("label-tech-bar-chart-spring-framework-version", "figure"),
            Output("label-tech-bar-chart-spring-boot-version", "figure"),
            Output("label-tech-bar-chart-middleware", "figure"),
            Output("label-tech-bar-chart-logging", "figure"),

            Output("kpi-total-repos", "children"),
            Output("kpi-avg-commits", "children"),
            Output("kpi-avg-contributors", "children"),
            Output("kpi-avg-loc", "children"),
            Output("kpi-avg-ccn", "children"),
            Output("kpi-avg-repo-size", "children"),

        ],
        [
            Input("host-name-filter", "value"),
            Input("activity-status-filter", "value"),
            Input("tc-filter", "value"),
            Input("language-filter", "value"),
            Input("classification-filter", "value"),
            Input("app-id-filter", "value"),
        ],
    )
    def update_charts(selected_hosts, selected_statuses, selected_tcs, selected_languages, selected_classifications, app_id_input):
        if app_id_input:
            app_ids = [id.strip() for id in app_id_input.split(",")]
        else:
            app_ids = None
        filters = {
            "host_name": selected_hosts,
            "activity_status": selected_statuses,
            "tc": selected_tcs,
            "all_languages": selected_languages,
            "classification_label": selected_classifications,
            "app_id": app_ids,
        }
        active_inactive_data = fetch_active_inactive_data(filters)
        contributors_commits_size_data = fetch_contributors_commits_size(filters)
        iac_data = fetch_iac_data(filters)
        classification_data = fetch_classification_data(filters)
        language_data = fetch_language_data(filters)
        cloc_data = fetch_cloc_by_language(filters)
        heatmap_data = fetch_language_contributors_heatmap(filters)
        trivy_data = fetch_trivy_vulnerabilities(filters)
        semgrep_data = fetch_semgrep_findings(filters)
        multi_lang_usage_data = fetch_multi_language_usage(filters)
        last_commit_buckets_data = fetch_last_commit_buckets(filters)
        scatter_fig = viz_contributors_commits_size(contributors_commits_size_data)
        iac_chart_fig = viz_iac_chart(iac_data)
        active_inactive_fig = viz_active_inactive(active_inactive_data)
        classification_fig = viz_classification(classification_data)
        language_chart_fig = viz_main_language(language_data)
        cloc_chart_fig = viz_cloc_by_language(cloc_data)
        heatmap_fig = viz_language_contributors_heatmap(heatmap_data)
        trivy_chart_fig = viz_trivy_vulnerabilities(trivy_data)
        semgrep_chart_fig = viz_semgrep_findings(semgrep_data)
        multi_lang_usage_fig = viz_multi_language_usage(multi_lang_usage_data)
        last_commit_buckets_fig = viz_last_commit_buckets(last_commit_buckets_data)

        java_data = fetch_label_tech_data(filters, "cto.io/java-version")
        java_fig = viz_label_tech(java_data)

        buildtool_data = fetch_label_tech_data(filters, "cto.io/build-tool")
        buildtool_fig = viz_label_tech(buildtool_data)

        appserver_data = fetch_label_tech_data(filters, "cto.io/appserver")
        appserver_fig = viz_label_tech(appserver_data)

        db_data = fetch_label_tech_data(filters, "cto.io/database")
        db_fig = viz_label_tech(db_data)

        sf_data = fetch_label_tech_data(filters, "cto.io/spring-framework-version")
        sf_fig = viz_label_tech(sf_data)

        sb_data = fetch_label_tech_data(filters, "cto.io/spring-boot-version")
        sb_fig = viz_label_tech(sb_data)

        mw_data = fetch_label_tech_data(filters, "cto.io/middleware")
        mw_fig = viz_label_tech(mw_data)

        logging_data = fetch_label_tech_data(filters, "cto.io/logging")
        logging_fig = viz_label_tech(logging_data)

        kpi_data = fetch_kpi_data(filters)

        kpi_data = fetch_kpi_data(filters)
        total_repos = kpi_data["total_repos"]
        avg_commits = kpi_data["avg_commits"]
        avg_contributors = kpi_data["avg_contributors"]
        avg_loc = kpi_data["avg_loc"]
        avg_ccn = kpi_data["avg_ccn"]
        avg_repo_size = kpi_data["avg_repo_size"]

        return (
            active_inactive_fig,
            classification_fig,
            scatter_fig,
            language_chart_fig,
            cloc_chart_fig,
            iac_chart_fig,
            heatmap_fig,
            trivy_chart_fig,
            semgrep_chart_fig,
            multi_lang_usage_fig,
            last_commit_buckets_fig,
            java_fig,
            buildtool_fig,
            appserver_fig,
            db_fig,
            sf_fig,
            sb_fig,
            mw_fig,
            logging_fig,

            total_repos,
            avg_commits,
            avg_contributors,
            avg_loc,
            avg_ccn,
            avg_repo_size
        )
