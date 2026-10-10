#!/usr/bin/env python3
"""confcheck: validate INI and TOML files."""
import argparse
import json
import re
import sys
import tomllib

SECTION = re.compile(r"^\[([^\[\]]+)\]\s*(?:[#;].*)?$")
KEYVAL = re.compile(r"^([^=:\s][^=:]*?)\s*([=:])\s*(.*)$")


def check_ini(text):
    """Return list of (line, kind, message)."""
    probs = []
    section = None
    sections = {}
    keys = {}
    for n, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if not s or s[0] in "#;":
            continue
        if raw[0] in " \t" and section is not None and keys.get(section):
            continue  # continuation line
        m = SECTION.match(s)
        if m:
            section = m.group(1)
            if section in sections:
                probs.append((n, "duplicate_section",
                              f"duplicate section [{section}] (first at line {sections[section]})"))
            else:
                sections[section] = n
                keys.setdefault(section, {})
            keys.setdefault(section, {})
            continue
        m = KEYVAL.match(s)
        if not m:
            probs.append((n, "unparseable", f"unparseable line: {s!r}"))
            continue
        if section is None:
            probs.append((n, "no_section", "key outside any section"))
            continue
        key = m.group(1).strip().lower()
        if key in keys[section]:
            probs.append((n, "duplicate_key",
                          f"duplicate key {key!r} in [{section}] (first at line {keys[section][key]})"))
        else:
            keys[section][key] = n
        if not m.group(3).strip():
            probs.append((n, "empty_value", f"empty value for {key!r} in [{section}]"))
    return probs


def check_toml(text):
    try:
        tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        msg = str(e)
        m = re.search(r"\(at line (\d+)", msg)
        return [(int(m.group(1)) if m else None, "syntax", msg)]
    probs = []
    for n, raw in enumerate(text.splitlines(), 1):
        if re.match(r"^\s*[\w.\"'-]+\s*=\s*(#.*)?$", raw):
            probs.append((n, "empty_value", "empty value"))
        elif re.match(r"^\s*[\w.\"'-]+\s*=\s*(\"\"|'')\s*(#.*)?$", raw):
            probs.append((n, "empty_value", "empty string value"))
    return probs


def check_file(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if path.lower().endswith(".toml"):
        return check_toml(text)
    return check_ini(text)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate INI (.ini/.cfg/...) and TOML (.toml) files.")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--json", action="store_true", help="JSON output")
    a = ap.parse_args(argv)
    result = {}
    for p in a.files:
        try:
            result[p] = [dict(line=l, kind=k, message=m) for l, k, m in check_file(p)]
        except (OSError, UnicodeDecodeError) as e:
            result[p] = [dict(line=None, kind="io", message=str(e))]
    if a.json:
        print(json.dumps(result, indent=2))
    else:
        for p, ps in result.items():
            for x in ps:
                loc = f":{x['line']}" if x["line"] else ""
                print(f"{p}{loc}: {x['kind']}: {x['message']}")
    return 1 if any(result.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
