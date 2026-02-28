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

# Fields in header config that are internal (not emitted in YAML frontmatter).
_INTERNAL_FIELDS = {"type", "skip", "output_name"}


# ─── Config ──────────────────────────────────────────────────────────────────


def load_config() -> dict:
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


# ─── Discovery ───────────────────────────────────────────────────────────────


def discover_skills() -> list[str]:
    """Walk source/skills/ and return the name of each skill directory."""
    skills_dir = SOURCE / "skills"
    if not skills_dir.exists():
        return []
    return sorted(p.name for p in skills_dir.iterdir() if p.is_dir())


# ─── Text transforms ────────────────────────────────────────────────────────


def strip_yaml_header(text: str) -> str:
    """Remove existing YAML frontmatter (--- ... ---) from source."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3 :].lstrip("\n")
    return text


def _filter_inline_conditionals(line: str, backend: str) -> str:
    """Handle inline <!-- BEGIN:x -->content<!-- END:x --> within a single line."""
    pattern = r"<!--\s*BEGIN:([^>]+?)\s*-->(.*?)<!--\s*END:[^>]+?\s*-->"

    def _replace(m: re.Match) -> str:
        allowed = {b.strip() for b in m.group(1).split(",")}
        return m.group(2) if backend in allowed else ""

    return re.sub(pattern, _replace, line)


def filter_conditional_blocks(text: str, backend: str) -> str:
    """Process <!-- BEGIN:backend_list --> / <!-- END:backend_list --> markers.

    Block-level (marker on its own line) and inline (marker within a line).
    """
    lines = text.split("\n")
    result: list[str] = []
    include = True
    depth = 0

    for line in lines:
        begin_match = re.match(r"^\s*<!--\s*BEGIN:([^>]+?)\s*-->\s*$", line)
        end_match = re.match(r"^\s*<!--\s*END:([^>]+?)\s*-->\s*$", line)

        if begin_match:
            allowed = {b.strip() for b in begin_match.group(1).split(",")}
            if include:
                include = backend in allowed
            depth += 1
            continue

        if end_match:
            depth -= 1
            if depth <= 0:
                include = True
                depth = 0
            continue

        if include:
            result.append(_filter_inline_conditionals(line, backend))

    return "\n".join(result)


def substitute_placeholders(text: str, placeholders: dict) -> str:
    """Replace {{KEY}} and {{INVOKE:name}} tokens with backend-specific values."""
    # {{INVOKE:name}}
    invoke_table = placeholders.get("INVOKE", {})
    text = re.sub(
        r"\{\{INVOKE:([^}]+)\}\}",
        lambda m: str(invoke_table.get(m.group(1), f"{{{{INVOKE:{m.group(1)}}}}}")),
        text,
    )
    # {{KEY}} (simple string values only)
    for key, value in placeholders.items():
        if isinstance(value, str):
            text = text.replace(f"{{{{{key}}}}}", value)
    return text


def make_yaml_header(header_cfg: dict) -> str:
    """Build YAML frontmatter from config, skipping internal fields."""
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


def collapse_blank_lines(text: str) -> str:
    """Collapse runs of 3+ consecutive newlines down to 2."""
    return re.sub(r"\n{3,}", "\n\n", text)


# ─── Output paths ───────────────────────────────────────────────────────────


def output_path_for(backend: str, name: str, cfg: dict) -> Path:
    """Compute the output file path for a skill."""
    if backend == "claude":
        return ROOT / "skills" / name / "SKILL.md"

    if backend == "cursor":
        return ROOT / ".cursor" / "skills" / name / "SKILL.md"

    if backend == "codex":
        header_cfg = cfg.get("codex", {}).get("headers", {}).get(name, {})
        output_name = header_cfg.get("output_name")
        if output_name:
            codex_name = output_name
        else:
            prefix = cfg.get("codex", {}).get("skill_prefix", "choochoo-codex-")
            codex_name = f"{prefix}{name}"
        return ROOT / "codex" / "skills" / codex_name / "SKILL.md"

    raise ValueError(f"Unknown backend: {backend}")


# ─── Reference copying ──────────────────────────────────────────────────────


def copy_references(refs_dir: Path, dest_dir: Path) -> None:
    """Copy all files from refs_dir into dest_dir/references/."""
    for ref in refs_dir.iterdir():
        if ref.is_file():
            dest = dest_dir / "references" / ref.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ref, dest)


# ─── Skill processing pipeline ──────────────────────────────────────────────


def process_skill(name: str, backend: str, cfg: dict) -> None:
    """Process a single skill for a single backend."""
    header_cfg = cfg.get(backend, {}).get("headers", {}).get(name, {})
    if header_cfg.get("skip"):
        print(f"  {backend:8s}    (skipped)")
        return

    src_path = SOURCE / "skills" / name / "SKILL.md"
    if not src_path.exists():
        print(f"  SKIP {name} (SKILL.md not found)", file=sys.stderr)
        return

    text = src_path.read_text()

    # 1. Strip existing YAML header
    text = strip_yaml_header(text)

    # 2. Filter conditional blocks
    text = filter_conditional_blocks(text, backend)

    # 3. Substitute placeholders
    placeholders = cfg.get(backend, {}).get("placeholders", {})
    text = substitute_placeholders(text, placeholders)

    # 4. Prepend backend-specific YAML header
    if header_cfg:
        text = make_yaml_header(header_cfg) + "\n\n" + text

    # 5. Collapse excessive blank lines
    text = collapse_blank_lines(text)

    # 6. Ensure trailing newline
    if not text.endswith("\n"):
        text += "\n"

    # 7. Write output
    out_path = output_path_for(backend, name, cfg)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text)

    # 8. Copy general references (shared across all skills)
    general_refs = SOURCE / "references"
    if general_refs.exists():
        copy_references(general_refs, out_path.parent)

    # 9. Copy skill-specific references (override general on name collision)
    skill_refs = SOURCE / "skills" / name / "references"
    if skill_refs.exists():
        copy_references(skill_refs, out_path.parent)

    print(f"  {backend:8s} → {out_path.relative_to(ROOT)}")


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
    codex_tmpl = TEMPLATES / "codex"
    if not codex_tmpl.exists():
        return

    agents_src = codex_tmpl / "AGENTS.md"
    if agents_src.exists():
        dest = ROOT / "codex" / "AGENTS.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(agents_src, dest)

    script_src = codex_tmpl / "install-skills.sh"
    if script_src.exists():
        dest = ROOT / "codex" / "scripts" / "install-skills.sh"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(script_src, dest)


# ─── Claude manifests ───────────────────────────────────────────────────────


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


# ─── Claude settings ────────────────────────────────────────────────────────


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


# ─── Main ────────────────────────────────────────────────────────────────────


def main() -> None:
    cfg = load_config()

    print("choochoo-plugins: generating backend output\n")

    for name in discover_skills():
        print(f"[{name}]")
        for backend in BACKENDS:
            process_skill(name, backend, cfg)
        print()

    print("[formulas]")
    distribute_formulas()
    print("  Distributed to all backends\n")

    print("[templates]")
    distribute_templates()
    print("  Codex templates copied\n")

    print("[claude manifests]")
    generate_claude_manifests(cfg)
    print("  .claude-plugin/plugin.json")
    print("  .claude-plugin/marketplace.json\n")

    print("[claude settings]")
    generate_claude_settings()
    print("  .claude/settings.local.json\n")

    print("Done.")


if __name__ == "__main__":
    main()
