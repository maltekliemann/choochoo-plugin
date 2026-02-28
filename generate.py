#!/usr/bin/env python3
"""Generate backend-specific output from canonical source files.

Reads source/ and config.toml, applies per-backend transforms
(YAML headers, placeholder substitution, conditional blocks),
and writes output in-place at the repo root.

No external dependencies — stdlib only (requires Python 3.11+ for tomllib).
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        print("Python 3.11+ required (or install tomli for 3.10)", file=sys.stderr)
        sys.exit(1)

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
TEMPLATES = ROOT / "templates"
CONFIG_PATH = ROOT / "config.toml"

BACKENDS = ("claude", "cursor", "codex")

# Source files: name → (kind, subdirectory).
# Commands live in source/skills/, skills in source/references/.
SOURCE_FILES: dict[str, tuple[str, str]] = {
    "install": ("command", "skills"),
    "spec": ("command", "skills"),
    "pour": ("command", "skills"),

}


# ─── Config loading ──────────────────────────────────────────────────────────


def load_config() -> dict:
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


# ─── Placeholder resolution ─────────────────────────────────────────────────


def _resolve_invoke(match: re.Match, placeholders: dict) -> str:
    """Resolve {{INVOKE:name}} from placeholders.INVOKE table."""
    name = match.group(1)
    invoke_table = placeholders.get("INVOKE", {})
    return str(invoke_table.get(name, f"{{{{INVOKE:{name}}}}}"))


def _resolve_refs(match: re.Match, placeholders: dict) -> str:
    """Resolve {{REFS:name}} from placeholders.REFS table."""
    name = match.group(1)
    refs_table = placeholders.get("REFS", {})
    return str(refs_table.get(name, f"{{{{REFS:{name}}}}}"))


def substitute_placeholders(text: str, placeholders: dict) -> str:
    """Replace {{PLACEHOLDER}} tokens with backend-specific values."""
    # First handle INVOKE: and REFS: patterns
    text = re.sub(
        r"\{\{INVOKE:([^}]+)\}\}",
        lambda m: _resolve_invoke(m, placeholders),
        text,
    )
    text = re.sub(
        r"\{\{REFS:([^}]+)\}\}",
        lambda m: _resolve_refs(m, placeholders),
        text,
    )
    # Then handle simple {{KEY}} placeholders (skip nested tables)
    for key, value in placeholders.items():
        if isinstance(value, str):
            text = text.replace(f"{{{{{key}}}}}", value)
    return text


# ─── Conditional blocks ─────────────────────────────────────────────────────


def _filter_inline_conditionals(line: str, backend: str) -> str:
    """Handle inline <!-- BEGIN:x -->content<!-- END:x --> within a single line.

    Keeps content between markers if backend is in the list; removes it otherwise.
    Always strips the marker tags themselves.
    """
    pattern = r"<!--\s*BEGIN:([^>]+?)\s*-->(.*?)<!--\s*END:[^>]+?\s*-->"

    def _replace(m: re.Match) -> str:
        backends_str = m.group(1)
        allowed = {b.strip() for b in backends_str.split(",")}
        if backend in allowed:
            return m.group(2)
        return ""

    return re.sub(pattern, _replace, line)


def filter_conditional_blocks(text: str, backend: str) -> str:
    """Process <!-- BEGIN:backend_list --> / <!-- END:backend_list --> markers.

    Supports two forms:
    1. **Block-level**: Marker on its own line — keeps or drops enclosed lines.
    2. **Inline**: Marker within a line — keeps or drops the enclosed text span.
    """
    lines = text.split("\n")
    result: list[str] = []
    include = True
    depth = 0

    for line in lines:
        begin_match = re.match(r"^\s*<!--\s*BEGIN:([^>]+?)\s*-->\s*$", line)
        end_match = re.match(r"^\s*<!--\s*END:([^>]+?)\s*-->\s*$", line)

        if begin_match:
            backends_str = begin_match.group(1)
            allowed = {b.strip() for b in backends_str.split(",")}
            if include:
                include = backend in allowed
                depth += 1
            else:
                depth += 1
            continue  # drop the marker line

        if end_match:
            depth -= 1
            if depth <= 0:
                include = True
                depth = 0
            continue  # drop the marker line

        if include:
            # Process any inline conditionals within the line
            line = _filter_inline_conditionals(line, backend)
            result.append(line)

    return "\n".join(result)


# ─── YAML header generation ─────────────────────────────────────────────────


# Fields that are internal to the build system, not emitted in YAML headers.
_INTERNAL_FIELDS = {"type", "skip", "output_name"}


def make_yaml_header(header_cfg: dict) -> str:
    """Build a YAML frontmatter header from config."""
    lines = ["---"]
    for key, value in header_cfg.items():
        if key in _INTERNAL_FIELDS:
            continue
        if isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


# ─── Source stripping ────────────────────────────────────────────────────────


def strip_yaml_header(text: str) -> str:
    """Remove existing YAML frontmatter (--- ... ---) from source."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].lstrip("\n")
    return text


# ─── Output path calculation ────────────────────────────────────────────────


def output_path_for(backend: str, name: str, kind: str, cfg: dict) -> Path:
    """Determine the output file path for a source file."""
    if backend == "claude":
        if kind == "command":
            return ROOT / "commands" / f"{name}.md"
        else:  # skill
            return ROOT / "skills" / name / "SKILL.md"

    elif backend == "cursor":
        # Everything is a skill in .cursor/skills/{name}/SKILL.md
        return ROOT / ".cursor" / "skills" / name / "SKILL.md"

    elif backend == "codex":
        # Check for output_name override in header config
        header_cfg = cfg.get("codex", {}).get("headers", {}).get(name, {})
        output_name = header_cfg.get("output_name")
        if output_name:
            codex_name = output_name
        else:
            prefix = cfg.get("codex", {}).get("skill_prefix", "choochoo-codex-")
            codex_name = f"{prefix}{name}"
        return ROOT / "codex" / "skills" / codex_name / "SKILL.md"

    raise ValueError(f"Unknown backend: {backend}")


# ─── Reference file distribution ────────────────────────────────────────────


def distribute_references(cfg: dict) -> None:
    """Copy source/references/ files to backend-specific locations."""
    refs_dir = SOURCE / "references"
    if not refs_dir.exists():
        return

    for backend in BACKENDS:
        refs_map = cfg.get(backend, {}).get("references", {})
        for src_name, dest_rel in refs_map.items():
            src_path = refs_dir / src_name
            dest_path = ROOT / dest_rel
            if src_path.exists():
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)


# ─── Formula distribution ───────────────────────────────────────────────────


def distribute_formulas() -> None:
    """Copy source/formulas/ to all backend locations."""
    formulas_dir = SOURCE / "formulas"
    if not formulas_dir.exists():
        return

    for formula_file in formulas_dir.iterdir():
        if not formula_file.is_file():
            continue

        # Claude: formulas/
        dest = ROOT / "formulas" / formula_file.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(formula_file, dest)

        # Cursor: .cursor/skills/install/formulas/
        dest = ROOT / ".cursor" / "skills" / "install" / "formulas" / formula_file.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(formula_file, dest)

        # Codex: codex/skills/choochoo-codex-install/assets/
        dest = (
            ROOT
            / "codex"
            / "skills"
            / "choochoo-codex-install"
            / "assets"
            / formula_file.name
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(formula_file, dest)

        # Codex also gets a top-level copy
        dest = ROOT / "codex" / "formulas" / formula_file.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(formula_file, dest)


# ─── Template distribution ──────────────────────────────────────────────────


def distribute_templates() -> None:
    """Copy templates/ to backend output locations."""
    # Codex templates
    codex_tmpl = TEMPLATES / "codex"
    if codex_tmpl.exists():
        # AGENTS.md → codex/AGENTS.md
        agents_src = codex_tmpl / "AGENTS.md"
        if agents_src.exists():
            dest = ROOT / "codex" / "AGENTS.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(agents_src, dest)

        # install-skills.sh → codex/scripts/install-skills.sh
        script_src = codex_tmpl / "install-skills.sh"
        if script_src.exists():
            dest = ROOT / "codex" / "scripts" / "install-skills.sh"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(script_src, dest)


# ─── Claude manifests ────────────────────────────────────────────────────────


def generate_claude_manifests(cfg: dict) -> None:
    """Generate .claude-plugin/plugin.json and marketplace.json."""
    plugin_cfg = cfg.get("plugin", {})

    plugin_json = {
        "name": plugin_cfg.get("name", "choochoo"),
        "version": plugin_cfg.get("version", "0.2.0"),
        "description": plugin_cfg.get("description", ""),
        "author": {
            "name": plugin_cfg.get("author_name", ""),
            "url": plugin_cfg.get("author_url", ""),
        },
        "repository": plugin_cfg.get("repository", ""),
        "keywords": plugin_cfg.get("keywords", []),
    }

    dest_dir = ROOT / ".claude-plugin"
    dest_dir.mkdir(parents=True, exist_ok=True)

    with open(dest_dir / "plugin.json", "w") as f:
        json.dump(plugin_json, f, indent=2)
        f.write("\n")

    marketplace_json = {
        "name": plugin_cfg.get("name", "choochoo"),
        "owner": {
            "name": plugin_cfg.get("author_name", ""),
            "url": plugin_cfg.get("author_url", ""),
        },
        "metadata": {
            "description": "Autonomous coding using the Ralph Wiggum technique",
            "version": plugin_cfg.get("version", "0.2.0"),
        },
        "plugins": [
            {
                "name": plugin_cfg.get("name", "choochoo"),
                "source": {
                    "source": "github",
                    "repo": "maltekliemann/choochoo-claude",
                    "ref": "main",
                },
                **plugin_json,
            }
        ],
    }

    with open(dest_dir / "marketplace.json", "w") as f:
        json.dump(marketplace_json, f, indent=2)
        f.write("\n")


# ─── Claude settings ─────────────────────────────────────────────────────────


def generate_claude_settings() -> None:
    """Generate .claude/settings.local.json."""
    settings = {
        "permissions": {
            "allow": [
                "mcp__github__get_file_contents",
                "mcp__github__issue_write",
                "Bash(cat:*)",
                "Bash(claude plugin install:*)",
                "Bash(claude plugin:*)",
                "Bash(claude plugin --help:*)",
                "Bash(claude install:*)",
                "Bash(find:*)",
            ]
        }
    }

    dest_dir = ROOT / ".claude"
    dest_dir.mkdir(parents=True, exist_ok=True)

    with open(dest_dir / "settings.local.json", "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")


# ─── Cleanup of consecutive blank lines ─────────────────────────────────────


def collapse_blank_lines(text: str) -> str:
    """Collapse runs of 3+ consecutive newlines down to 2 (one empty line)."""
    return re.sub(r"\n{3,}", "\n\n", text)


# ─── Main pipeline ──────────────────────────────────────────────────────────


def process_source(
    name: str,
    kind: str,
    subdir: str,
    backend: str,
    cfg: dict,
) -> None:
    """Process a single source file for a single backend."""
    # Check if this source should be skipped for this backend
    header_cfg = cfg.get(backend, {}).get("headers", {}).get(name, {})
    if header_cfg.get("skip"):
        print(f"  {backend:8s}    (skipped)")
        return

    src_path = SOURCE / subdir / f"{name}.md"
    if not src_path.exists():
        print(f"  SKIP {name} (source not found)", file=sys.stderr)
        return

    text = src_path.read_text()

    # 1. Strip existing YAML header from source
    text = strip_yaml_header(text)

    # 2. Filter conditional blocks for this backend
    text = filter_conditional_blocks(text, backend)

    # 3. Substitute placeholders
    placeholders = cfg.get(backend, {}).get("placeholders", {})
    text = substitute_placeholders(text, placeholders)

    # 4. Prepend backend-specific YAML header
    header_cfg = cfg.get(backend, {}).get("headers", {}).get(name, {})
    if header_cfg:
        header = make_yaml_header(header_cfg)
        text = header + "\n\n" + text

    # 5. Clean up excessive blank lines
    text = collapse_blank_lines(text)

    # 6. Ensure trailing newline
    if not text.endswith("\n"):
        text += "\n"

    # 7. Write to output path
    out_path = output_path_for(backend, name, kind, cfg)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text)

    print(f"  {backend:8s} → {out_path.relative_to(ROOT)}")


def main() -> None:
    cfg = load_config()

    print("choochoo-plugins: generating backend output\n")

    # Process each source file for each backend
    for name, (kind, subdir) in SOURCE_FILES.items():
        print(f"[{name}]")
        for backend in BACKENDS:
            process_source(name, kind, subdir, backend, cfg)
        print()

    # Distribute formulas
    print("[formulas]")
    distribute_formulas()
    print("  Distributed to all backends\n")

    # Distribute references
    print("[references]")
    distribute_references(cfg)
    print("  Distributed per config\n")

    # Distribute templates
    print("[templates]")
    distribute_templates()
    print("  Codex templates copied\n")

    # Generate Claude manifests
    print("[claude manifests]")
    generate_claude_manifests(cfg)
    print("  .claude-plugin/plugin.json")
    print("  .claude-plugin/marketplace.json\n")

    # Generate Claude settings
    print("[claude settings]")
    generate_claude_settings()
    print("  .claude/settings.local.json\n")

    print("Done.")


if __name__ == "__main__":
    main()
