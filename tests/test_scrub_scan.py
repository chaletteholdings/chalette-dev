"""The scrub reads a Command Room 1 book (one _hq/data/entities.json) and the older split parts alike (v0.8.0).

Before v0.8.0 the terms step read only _hq/data/entities/*.jsonl.txt, so on a cr1 book it found no
names at all and every scan passed on the fixed checks alone. Sample names only in this file."""
import json
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

