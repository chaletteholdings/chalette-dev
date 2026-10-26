"""Scrub scan. Usage:
  python scrub_scan.py terms --book <book folder: _hq/data/entities.json, or the older _hq/data/entities/ parts> > terms.txt
  python scrub_scan.py scan --terms terms.txt <file or - for stdin> [...]
Prints one finding per line: KIND<TAB>match<TAB>where. Exit 1 if anything found.

Private lists live in the gitignored config/scrub.local.json of this plugin, on the
operator's own computer only:
  {"family": [surnames always flagged], "ignore_names": [first names that are noise],
   "ignore_words": [words that are noise]}
Nothing real is written in this file."""
import json, re, sys, glob, os

TEAM = {"matthew", "erick", "eric", "isabella", "claude", "chalette", "command room", "penelope"}
GENERIC_DOMAINS = {"gmail.com", "yahoo.com", "icloud.com", "me.com", "outlook.com", "hotmail.com", "aol.com",
                   "wework.com", "superhuman.com", "chaletteholdings.com"}
WORDS = {"company", "builders", "contact", "complete", "beach", "power", "group", "partners", "systems", "holdings",
         "capital", "advisors", "leaders", "school", "life", "word", "franchise", "partnership", "consulting",
         "venture", "trading", "system", "global", "brands", "clean", "labs", "solutions", "investors", "logistics",
         "speakers", "talent", "forum", "fund", "deal", "construction", "living", "green", "place"}
TEAM_FULL = ["Matthew Davidov", "Erick Burg", "Isabella Cardenas"]  # the team may be named; removed before scanning
INTERNAL = ("command room", "chalette", "penelope", "new bot build", "cr56 testbot")


def _local():
    here = os.path.dirname(os.path.abspath(__file__))
    for p in (os.path.join(here, "..", "..", "..", "config", "scrub.local.json"),
              os.environ.get("CR1_SCRUB_LOCAL", "")):
        if p and os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    return {}


LOCAL = _local()
FAMILY = list(LOCAL.get("family", []))
COMMON = {w.lower() for w in LOCAL.get("ignore_names", [])}
WORDS |= {w.lower() for w in LOCAL.get("ignore_words", [])}


def _pieces(name):
    for p in re.split(r"\s+(?:—|-|/)\s+|\s*/\s*|,\s+", re.sub(r"\s*\(.*?\)", "", name)):
        p = p.strip()
        if p:
            yield p


def _records(book):
    """Every entity record in the book: the split parts (_hq/data/entities/*.jsonl.txt), then the
    single Command Room 1 file (_hq/data/entities.json: its people, orgs and threads lists, at the top
    level or, in a current book, under its "entities" block, cr1#455)."""
    for f in glob.glob(os.path.join(book, "_hq", "data", "entities", "*.jsonl.txt")):
        for line in open(f, encoding="utf-8"):
            try:
                yield json.loads(line)
            except ValueError:
                continue
    one = os.path.join(book, "_hq", "data", "entities.json")
    if os.path.isfile(one):
        try:
            with open(one, encoding="utf-8") as f:
                data = json.load(f)
        except ValueError:
            data = {}
        blocks = [data] if isinstance(data, dict) else []
        if blocks and isinstance(data.get("entities"), dict):
            blocks.append(data["entities"])
        for block in blocks:
            for kind in ("people", "orgs", "threads"):
                for r in block.get(kind) or []:
                    if isinstance(r, dict):
                        yield r


def terms(book):
    out = set(FAMILY)
    for r in _records(book):
        name = r.get("canonical_name") or ""
        if name.lower().startswith(INTERNAL) or name in TEAM_FULL:
            continue
        is_org = bool(r.get("domains") or r.get("folder_name") or r.get("scope") or r.get("kind"))
        for p in list(_pieces(name)) + [r.get("folder_name") or ""]:
            if len(p) < 4 or p.lower().startswith(INTERNAL) or p.startswith("_"):
                continue
            if " " in p or is_org:
                out.add(p.split("/")[-1])
                if " " in p and not is_org and p.split()[-1].isalpha() and len(p.split()[-1]) >= 5:
                    out.add(p.split()[-1])  # a surname on its own
        for e in r.get("emails") or []:
            out.add(e)
            d = e.split("@")[-1].lower()
            if d not in GENERIC_DOMAINS:
                out.add(d)
        for d in r.get("domains") or []:
            if d.lower() not in GENERIC_DOMAINS:
                out.add(d)
    team = {w.lower() for n in TEAM_FULL for w in n.split()} | TEAM
    return sorted({t for t in out if t.lower() not in team and t.lower() not in COMMON and t.lower() not in WORDS}, key=str.lower)


MONEY = re.compile(r"(?:[$€£]\s?\d[\d,]*(?:\.\d+)?\s?(?:[kKmM]|million|thousand)?\b)|(?:\b\d[\d,.]*\s?(?:USD|dollars|k/mo|/month|/mo)\b)", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"(?<!\d)(?:\+1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)")
SECRET = re.compile(r"(?:xox[abpr]-[\w-]{10,}|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|password\s*[:=]\s*\S+)", re.I)

_PAT = {}


def scan(term_list, label, text):
    for n in TEAM_FULL:
        text = re.sub(re.escape(n), "", text, flags=re.I)
    found = []
    if term_list:
        key = tuple(term_list)
        if key not in _PAT:
            alts = "|".join(re.escape(t) for t in sorted(term_list, key=len, reverse=True))
            _PAT[key] = re.compile(r"(?<![A-Za-z0-9])(?:" + alts + r")(?![A-Za-z0-9])", re.I)
        found += [("NAME", m.group(0)) for m in _PAT[key].finditer(text)]
    found += [("MONEY", m.group(0)) for m in MONEY.finditer(text)]
    for m in EMAIL.finditer(text):
        v = m.group(0).lower()
        if not re.search(r"@example\.|\.example(\.|$)|noreply|users\.noreply\.github|^dev@chaletteholdings\.com$", v):
            found += [("EMAIL", m.group(0))]
    found += [("PHONE", m.group(0)) for m in PHONE.finditer(text)]
    found += [("SECRET", m.group(0)[:12] + "...") for m in SECRET.finditer(text)]
    return [(k, v, label) for k, v in found]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Windows defaults to cp1252, which the scan step cannot read back
    if sys.argv[1] == "terms":
        found = terms(sys.argv[sys.argv.index("--book") + 1])
        # No names from the book (wrong folder, unreadable or empty book, family list only):
        # refuse, never hand back a list a scan would pass as clean (cr1#455).
        if not set(found) - set(FAMILY):
            print("The name check did not run: no names could be read from this workspace.", file=sys.stderr)
            sys.exit(2)
        print("\n".join(found))
        sys.exit(0)
    tl = [t.strip() for t in open(sys.argv[sys.argv.index("--terms") + 1], encoding="utf-8") if t.strip()]
    targets = [a for a in sys.argv[2:] if a not in ("--terms",) and a != sys.argv[sys.argv.index("--terms") + 1]]
    hits = []
    for t in targets:
        text = sys.stdin.read() if t == "-" else open(t, encoding="utf-8", errors="replace").read()
        hits += scan(tl, t, text)
    for k, v, w in sorted(set(hits)):
        print(f"{k}\t{v}\t{w}")
    sys.exit(1 if hits else 0)
