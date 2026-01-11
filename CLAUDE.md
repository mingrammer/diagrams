# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Diagrams is a Python library that lets you draw cloud system architecture diagrams using Python code. It uses Graphviz to render diagrams and supports major cloud providers (AWS, Azure, GCP, etc.), Kubernetes, on-premises infrastructure, and more.

## Development Commands

### Setup
```bash
# Install dependencies with Poetry
poetry install

# Or with pip
pip install -e .
```

### Running Tests
```bash
python -m unittest tests/*.py -v
```

### Auto-generating Node Classes
Node classes are auto-generated from icon resources. Never edit files in `diagrams/` directly (except `__init__.py` and `cli.py`).

```bash
./autogen.sh
```

Requires: `round` (Go tool), `inkscape`, `imagemagick`, and `black`

### Linting
```bash
black diagrams/**/*.py --line-length=120
```

## Architecture

### Core Classes (diagrams/__init__.py)
- **Diagram**: Top-level context manager that creates the graphviz diagram. Handles output format, direction, and rendering.
- **Cluster** (alias: Group): Nested context for grouping nodes visually.
- **Node**: Base class for all service nodes. Supports edge operators (`>>`, `<<`, `-`) for connecting nodes.
- **Edge**: Represents connections between nodes with directional arrows and labels.

Global context is managed via `contextvars` - nodes automatically register to the current diagram/cluster context.

### Provider Structure
Each cloud provider has:
- `diagrams/<provider>/__init__.py`: Base provider class inheriting from `Node`
- `diagrams/<provider>/<type>.py`: Auto-generated node classes for each service type
- `resources/<provider>/<type>/*.png`: Icon images (256x256 max)

### Code Generation Pipeline
1. `scripts/resource.py`: Cleans filenames, converts SVG to PNG, rounds corners (AWS only)
2. `scripts/generate.py`: Uses Jinja2 templates to generate Python module files from resource icons
3. `config.py`: Contains provider configs, aliases (`ALIASES`), and uppercase word mappings (`UPPER_WORDS`)
4. `templates/module.tmpl`: Template for generating node class files

### Custom Nodes
`diagrams/custom/__init__.py` allows users to create nodes with custom icon paths.

### C4 Model Support
`diagrams/c4/__init__.py` provides C4 architecture diagram components (Container, Database, System, Person, etc.).

## Adding New Resources

1. Add PNG icon to `resources/<provider>/<type>/` (max 256x256)
2. Run `./autogen.sh` to regenerate classes
3. Optionally add aliases in `config.py` under `ALIASES`

## Adding New Providers

1. Add provider to `providers` array in `autogen.sh`
2. Update `config.py`: add to `PROVIDERS`, `FILE_PREFIXES`, optionally `UPPER_WORDS` and `ALIASES`
3. Add cleaner function in `scripts/resource.py`
4. Create `diagrams/<provider>/__init__.py` with base class
5. Run `./autogen.sh`
