
delete from bitbucket_repositories;
delete from go_enry_analysis;
delete from repo_metrics;
delete from lizard_summary;
delete from cloc_metrics;
delete from grype_results;
delete from checkov_summary;
delete from trivy_vulnerability;
delete from analysis_execution_log;
delete from semgrep_results;

update bitbucket_repositories set status = 'NEW';
