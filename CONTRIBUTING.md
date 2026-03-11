# Contributing

## Adding a New Diagram Type

1. **Create a script** in `scripts/` following the `uv` inline metadata format:

    ```python
    # /// script
    # requires-python = ">=3.10"
    # dependencies = ["your-library"]
    # ///
    """Brief description of what this diagram shows."""
    from pathlib import Path

    def main() -> None:
        Path("output").mkdir(exist_ok=True)
        # ... build diagram ...
        print(f"Saved: output/your-diagram.svg")

    if __name__ == "__main__":
        main()
    ```

2. **Update the routing table** in `skills/generate-diagram/SKILL.md` with the new diagram type, primary library, and any alternatives.

3. **Run checks** to verify everything passes:

    ```bash
    just all
    ```

## Script Requirements

- Use `uv` inline script metadata (`# /// script` block) with pinned dependencies.
- Output files to the `output/` directory (create it with `Path("output").mkdir(exist_ok=True)`).
- Include type hints on all function signatures.
- Use a `main()` function with `if __name__ == "__main__":` guard.

## Code Style

- **Python**: formatted and linted with [ruff](https://docs.astral.sh/ruff/).
- **Markdown**: checked with [markdownlint](https://github.com/DavidAnson/markdownlint).

## CI

All checks must pass before merge. The GitHub Actions workflow runs ruff, pyrefly, markdownlint, and smoke tests on every push and PR.

## Library Guidelines

- **Prefer pure-pip libraries** that need no system dependencies (e.g., svgwrite, drawsvg, schemdraw).
- If a library requires a system binary (e.g., Graphviz), document the install commands for macOS, Ubuntu, and Fedora in the script's docstring and in the SKILL.md library reference.
- Pin unmaintained dependencies to known-working versions (see seqdiag/blockdiag scripts for examples).
