import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from modular.models import Ruleset, Violation, Label

# Database connection string
DATABASE_URL = "postgresql://postgres:postgres@192.168.1.188:5422/gitlab-usage"

# Create database engine
engine = create_engine(DATABASE_URL)

# YAML file to process
YAML_FILE = "/tmp/kantra_output_sonar-metrics/output.yaml"

# Function to process the YAML and populate the tables
def populate_from_yaml(yaml_file, repo_id):
    # Load YAML file
    with open(yaml_file, "r") as file:
        data = yaml.safe_load(file)

    # Open a database session
    with Session(engine) as session:
        for ruleset_data in data:
            # Upsert ruleset
            ruleset = session.query(Ruleset).filter_by(name=ruleset_data.get("name")).first()
            if not ruleset:
                ruleset = Ruleset(
                    name=ruleset_data.get("name"),
                    description=ruleset_data.get("description")
                )
                session.add(ruleset)
            else:
                ruleset.description = ruleset_data.get("description")

            # Process violations
            for violation_key, violation_data in ruleset_data.get("violations", {}).items():
                violation = session.query(Violation).filter_by(
                    description=violation_data.get("description"),
                    ruleset_name=ruleset.name,
                    repo_id=repo_id
                ).first()
                if not violation:
                    violation = Violation(
                        ruleset_name=ruleset.name,
                        description=violation_data.get("description"),
                        category=violation_data.get("category"),
                        effort=violation_data.get("effort"),
                        repo_id=repo_id
                    )
                    session.add(violation)

                # Process labels
                for label in violation_data.get("labels", []):
                    if "=" in label:
                        key, value = label.split("=", 1)
                        label_obj = session.query(Label).filter_by(key=key, value=value).first()
                        if not label_obj:
                            label_obj = Label(key=key, value=value)
                            session.add(label_obj)
                    else:
                        print(f"Skipping invalid label: {label}")

        # Commit the transaction
        session.commit()

# Run the population script
if __name__ == "__main__":
    REPO_ID = "example-repo-id"  # Replace with the actual repository ID
    populate_from_yaml(YAML_FILE, REPO_ID)
    print("Data populated successfully!")
