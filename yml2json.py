import yaml
import json

with open("file.yml", "r") as yaml_file:
    yaml_content = yaml.safe_load(yaml_file)

with open("file.json", "w") as json_file:
    json.dump(yaml_content, json_file, indent=2)

print("YAML has been converted to JSON successfully.")
