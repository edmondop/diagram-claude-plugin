# diagram-claude-plugin

A Claude Code plugin that generates professional diagrams from natural language. It routes each request to the best-fit Python library, produces a `uv run`-compatible script, and saves both the script and SVG output for version control.

## Installation

Add the plugin to your Claude Code settings (`.claude/settings.json`):

```json
{
  "extraKnownMarketplaces": [
    "https://github.com/edmondop/diagram-claude-plugin"
  ]
}
```

## Prerequisites

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/)** — scripts use `uv run` with inline dependency metadata
- **Graphviz** (system binary) — required for graphviz, diagrams, seqdiag, and blockdiag libraries

Install Graphviz:

```bash
# macOS
brew install graphviz

# Ubuntu / Debian
sudo apt-get install graphviz

# Fedora
sudo dnf install graphviz
```

## Supported Diagram Types

| Diagram type             | Primary library           | Alternative    | When to pick alternative                        |
|--------------------------|---------------------------|----------------|-------------------------------------------------|
| Flowchart / pipeline     | graphviz                  | schemdraw      | No Graphviz installed; simple linear flow        |
| Generic architecture     | graphviz                  | --             | --                                               |
| Cloud/infra architecture | diagrams (mingrammer)     | graphviz       | Don't need cloud provider icons                  |
| ERD                      | graphviz                  | --             | --                                               |
| Pyramid / stacked layers | svgwrite                  | drawsvg        | Prefer cleaner API, less precise control needed  |
| Sequence diagram         | seqdiag                   | svgwrite       | seqdiag for speed; svgwrite for full control     |
| Network / DAG            | networkx + matplotlib     | graphviz       | graphviz for DOT-style output                    |
| Block diagram            | blockdiag                 | schemdraw      | schemdraw for flow-style blocks                  |
| State machine / FSM      | graphviz                  | --             | --                                               |

## Usage

Use the `/diagram` slash command or just ask Claude to draw something:

```
/diagram authentication flow for a web app
```

```
Draw me an ERD for an e-commerce system with users, orders, and products
```

```
Create a cloud architecture diagram showing an AWS setup with ECS, RDS, and ElastiCache
```

The plugin will classify the diagram type, suggest a library, generate a script, run it, and open the SVG for review. You can iterate on the output until it looks right.

## Development

Install [just](https://github.com/casey/just), then run all checks:

```bash
just all
```

This runs ruff (lint + format), pyrefly (type check), markdownlint, and smoke tests for all scripts.

## License

[MIT](LICENSE) — Copyright (c) 2026 Edmondo Porcu
