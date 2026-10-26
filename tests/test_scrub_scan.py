"""The scrub reads a Command Room 1 book (one _hq/data/entities.json) and the older split parts alike (v0.8.0).

Before v0.8.0 the terms step read only _hq/data/entities/*.jsonl.txt, so on a cr1 book it found no
names at all and every scan passed on the fixed checks alone. Sample names only in this file."""
import json
import os
import pathlib
import subprocess
import sys

SCRIPT = (pathlib.Path(__file__).resolve().parent.parent / "chalette-dev" / "skills" / "cr1-scrub"
          / "scripts" / "scrub_scan.py")

PEOPLE = [{"id": "p1", "canonical_name": "Avery Samplewright", "emails": ["avery@samplefirm.example"]}]
ORGS = [{"id": "o1", "canonical_name": "Northwind Fixtures", "domains": ["northwindfix.example"], "scope": "client"},
        {"id": "o2", "canonical_name": "Command Room", "scope": "self"}]
THREADS = [{"id": "t1", "canonical_name": "Northwind Fixtures - Rollout", "folder_name": "Northwind Rollout",
            "kind": "client"}]


def _terms(book):
    out = subprocess.run([sys.executable, str(SCRIPT), "terms", "--book", str(book)],
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return [t for t in out.splitlines() if t.strip()]


def _split_book(root):
    d = root / "_hq" / "data" / "entities"
    d.mkdir(parents=True)
    for name, rows in (("people", PEOPLE), ("orgs", ORGS), ("threads", THREADS)):
        (d / f"{name}.part1.jsonl.txt").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return root


def _cr1_book(root):
    d = root / "_hq" / "data"
    d.mkdir(parents=True)
    (d / "entities.json").write_text(json.dumps({"version": 1, "people": PEOPLE, "orgs": ORGS,
                                                  "threads": THREADS, "engagements": []}), encoding="utf-8")
    return root


def test_cr1_book_yields_names(tmp_path):
    terms = _terms(_cr1_book(tmp_path / "cr1"))
    assert "Avery Samplewright" in terms and "Northwind Fixtures" in terms and "northwindfix.example" in terms
    assert not any(t.lower().startswith("command room") for t in terms), "the product name is never a term"


def test_cr1_book_and_split_book_give_the_same_terms(tmp_path):
    assert _terms(_cr1_book(tmp_path / "a")) == _terms(_split_book(tmp_path / "b"))


def _nested_book(root):
    """A current Command Room 1 book keeps people, orgs and threads under an "entities" block (cr1#455)."""
    d = root / "_hq" / "data"
    d.mkdir(parents=True)
    (d / "entities.json").write_text(json.dumps({"version": 1, "entities": {"people": PEOPLE, "orgs": ORGS,
                                                                           "threads": THREADS},
                                                  "workspace": {}}), encoding="utf-8")
    return root


def _run_terms(book, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), "terms", "--book", str(book)],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def test_nested_book_gives_the_same_terms_as_a_flat_book(tmp_path):
    terms = _terms(_nested_book(tmp_path / "nested"))
    assert "Avery Samplewright" in terms and "Northwind Fixtures" in terms and "northwindfix.example" in terms
    assert terms == _terms(_cr1_book(tmp_path / "flat"))


REFUSAL = "The name check did not run: no names could be read from this workspace."


def _assert_refused(r):
    assert r.returncode != 0, "a list with no book names must never pass as clean"
    assert r.stdout.strip() == "", "nothing a caller could mistake for a name list"
    assert REFUSAL in r.stderr


def test_missing_folder_refuses(tmp_path):
    _assert_refused(_run_terms(tmp_path / "no-such-book"))


def test_book_with_no_people_or_orgs_refuses(tmp_path):
    d = tmp_path / "empty" / "_hq" / "data"
    d.mkdir(parents=True)
    (d / "entities.json").write_text(json.dumps({"version": 1, "people": [], "orgs": [], "threads": []}),
                                     encoding="utf-8")
    _assert_refused(_run_terms(tmp_path / "empty"))


def test_family_list_alone_refuses(tmp_path):
    """A book with no names, with a sample family list loaded, still refuses.

    The script is copied out of the plugin so the plugin's own private config can
    never stand in for the sample list; the first run proves the sample list loaded."""
    copy = tmp_path / "plugin" / "skills" / "cr1-scrub" / "scripts" / "scrub_scan.py"
    copy.parent.mkdir(parents=True)
    copy.write_bytes(SCRIPT.read_bytes())
    local = tmp_path / "scrub.local.json"
    local.write_text(json.dumps({"family": ["Quillfernby"]}), encoding="utf-8")
    env = dict(os.environ, CR1_SCRUB_LOCAL=str(local))
    run = lambda book: subprocess.run([sys.executable, str(copy), "terms", "--book", str(book)],
                                      capture_output=True, text=True, encoding="utf-8", env=env)
    loaded = run(_nested_book(tmp_path / "named"))
    assert loaded.returncode == 0 and "Quillfernby" in loaded.stdout.splitlines(), "the sample family list loaded"
    d = tmp_path / "empty" / "_hq" / "data"
    d.mkdir(parents=True)
    (d / "entities.json").write_text(json.dumps({"version": 1, "entities": {"people": [], "orgs": [], "threads": []}}),
                                     encoding="utf-8")
    _assert_refused(run(tmp_path / "empty"))


def test_scan_catches_a_name_and_an_amount(tmp_path):
    terms = tmp_path / "terms.txt"
    terms.write_text("\n".join(_terms(_cr1_book(tmp_path / "book"))), encoding="utf-8")
    post = tmp_path / "post.md"
    post.write_text("Avery Samplewright sent an invoice for $1,234.56 (a sample amount).\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), "scan", "--terms", str(terms), str(post)],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 1
    kinds = {line.split("\t")[0] for line in r.stdout.splitlines()}
    assert {"NAME", "MONEY"} <= kinds

