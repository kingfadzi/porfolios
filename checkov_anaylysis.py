def save_sarif_results(session, repo_id, sarif_log):
    try:
        print(f"Saving SARIF results for repo_id: {repo_id} to the database.")

        for run in sarif_log.runs:
            tool = run.get("tool", {})
            driver = tool.get("driver", {})
            rules = {rule["id"]: rule for rule in driver.get("rules", [])}

            for result in run.get("results", []):
                rule_id = result.get("ruleId")
                rule = rules.get(rule_id, {})
                severity = rule.get("properties", {}).get("severity", "UNKNOWN")
                message = result.get("message", {}).get("text", "No message provided")

                for location in result.get("locations", []):
                    physical_location = location.get("physicalLocation", {})
                    artifact_location = physical_location.get("artifactLocation", {})
                    region = physical_location.get("region", {})
                    file_path = artifact_location.get("uri", "N/A")
                    start_line = region.get("startLine", -1)
                    end_line = region.get("endLine", -1)

                    # Insert into database
                    session.execute(
                        insert(CheckovSarifResult).values(
                            repo_id=repo_id,
                            rule_id=rule_id,
                            rule_name=rule.get("name", "No name"),
                            severity=severity,
                            file_path=file_path,
                            start_line=start_line,
                            end_line=end_line,
                            message=message
                        ).on_conflict_do_update(
                            index_elements=["repo_id", "rule_id", "file_path", "start_line", "end_line"],
                            set_={
                                "rule_name": rule.get("name", "No name"),
                                "severity": severity,
                                "message": message
                            }
                        )
                    )
        session.commit()
        print("SARIF results successfully saved to the database.")
    except Exception as e:
        print(f"Error while saving SARIF results to the database: {e}")
        raise
