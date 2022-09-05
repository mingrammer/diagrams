import os
from pathlib import Path

RESOURCE_DIR = Path("..", "resources")
CHEAT_SHEAT_DIR = Path("..", "docs", "cheat-sheet.md")

resource_paths = []

def walkdir(dirname):
    for cur, _, files in os.walk(dirname):
        for f in files:
            full_path = f"{cur}/{f}"
            resource_paths.append(full_path)

def generate_markdown_table(resource_paths):
    with open(CHEAT_SHEAT_DIR, "w") as md_file:
        md_file.write("# Diagrams Cheat Sheet\n")
        md_file.write("| Image | Python Import |\n")
        md_file.write("| ----- | ------------- |\n")
        for img_path in resource_paths:
            path = Path(img_path)
            import_path = '.'.join(path.parts[1:-1]).replace("-", "_")
            module_name = path.parts[-1].replace("-", " ").title().replace(" ", "").replace(".Png", "")
            table_entry = f"| ![module_name]({path}) | `from {import_path} import {module_name}` |\n"
            md_file.write(table_entry)

if __name__ == "__main__":
    walkdir(RESOURCE_DIR)
    generate_markdown_table(resource_paths)
