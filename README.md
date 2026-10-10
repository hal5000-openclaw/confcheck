# confcheck

Small stdlib-only Python 3.11+ CLI that validates INI and TOML files.

Why: catch config mistakes (duplicates, empty values, bad lines) that parsers silently accept or reject with vague errors.

## Install

No dependencies. Copy `confcheck.py` or run it in place.

## Usage

    python3 confcheck.py app.ini config.toml
    python3 confcheck.py --json app.ini

Files ending in `.toml` are parsed as TOML; everything else as INI.

Reports, with line numbers: duplicate sections, duplicate keys (case-insensitive, INI),
empty values, unparseable lines, keys outside a section (INI), and TOML syntax errors
(including TOML-level duplicate keys). Exit code is 1 if any problem is found, else 0.

Example:

    $ python3 confcheck.py sample.ini
    sample.ini:3: duplicate_key: duplicate key 'x' in [a] (first at line 2)

## Tests

    python3 -m unittest discover -s tests
