"""Generate the traceability matrix in docs/TestPlan.md from test case Req columns.

Run without arguments to check coverage; add --write to regenerate section 16.
"""
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
PLAN = str(ROOT / "docs" / "TestPlan.md")
SRS = str(ROOT / "docs" / "SRS.md")

TEST_PREFIX = r"(?:UT|IT|E2E|SEC-T|PERF|LOAD|RES|AIE|RAGE|A11Y|UAT|INSP)"
ROW = re.compile(r"^\| (" + TEST_PREFIX + r"(?:-[A-Z0-9]+)*-[A-Z]?\d{2,3}) \| ([^|]+) \|")
REQ = re.compile(r"\b((?:BR|CON|SEC|CMP|AI|RAG|KR|GAM|LB|I18N|DATA|RPT|AC|UC|FR-[A-Z]+|NFR-[A-Z]+|IF-[A-Z]+)-\d{3}|UC-\d{2})\b")
REF = re.compile(r"\b(" + TEST_PREFIX + r"(?:-[A-Z0-9]+)*?-[A-Z]?\d{2,3})\b")

text = open(PLAN).read()
lines = text.splitlines()

# requirement catalogue from SRS
srs = open(SRS).read()
cat = {}
for m in re.finditer(r"\*\*([A-Z0-9-]+-\d{3})\*\* `\[(M|S|C) \| (MVP|R2|R3) \| ([TDIA])\]`", srs):
    cat[m.group(1)] = (m.group(2), m.group(3), m.group(4))
for m in re.finditer(r"^\| (NFR-PERF-\d{3}) \|", srs, re.M):
    cat.setdefault(m.group(1), ("M", "MVP", "T"))
ext = {}
for m in re.finditer(r"^\| (IF-EXT-\d{3}) \|[^\n]*", srs, re.M):
    ext[m.group(1)] = ("M", "R2" if "(R2)" in m.group(0) else "MVP", "T")
acs = sorted(set(re.findall(r"\*\*(AC-\d{3})\*\*", srs)))
uc_src = open(SRS.replace("SRS.md", "UseCases.md")).read()
ucs = sorted(set(re.findall(r"^### (UC-\d{2})", uc_src, re.M)))

defined = []
req_to_tests = collections.defaultdict(list)
for l in lines:
    m = ROW.match(l)
    if not m:
        continue
    tid, reqs = m.group(1), m.group(2)
    defined.append(tid)
    for r in REQ.findall(reqs.replace("†", "")):
        if tid not in req_to_tests[r]:
            req_to_tests[r].append(tid)

dups = [t for t, c in collections.Counter(defined).items() if c > 1]
dset = set(defined)

# referenced test IDs anywhere (excluding the generated matrix region)
body = text.split("<!-- MATRIX -->")[0] + text.split("<!-- /MATRIX -->")[-1] if "<!-- /MATRIX -->" in text else text
refs = set(REF.findall(body))
placeholder = {r for r in refs if re.search(r"NN", r)}
missing_refs = sorted(r for r in refs - dset - placeholder)

mvp = {k: v for k, v in cat.items() if v[1] == "MVP"}
unknown_reqs = sorted(r for r in req_to_tests if r not in cat and r not in ext and not r.startswith(("AC-", "UC-")))
ext_mvp = [k for k, v in ext.items() if v[1] == "MVP"]
print("IF-EXT MVP uncovered:", [k for k in ext_mvp if k not in req_to_tests])
uncov = sorted(k for k in mvp if k not in req_to_tests)
uncov_m = [k for k in uncov if mvp[k][0] == "M"]
uncov_s = [k for k in uncov if mvp[k][0] == "S"]
ac_uncov = [a for a in acs if a not in req_to_tests]
uc_uncov = [u for u in ucs if u not in req_to_tests and u not in text.split("## 15. Test Scenarios")[1].split("## 16.")[0]]

print("defined tests", len(defined), "dups", dups)
print("catalogue", len(cat), "MVP", len(mvp), "M", sum(1 for v in mvp.values() if v[0] == "M"), "S", sum(1 for v in mvp.values() if v[0] == "S"))
print("ACs", len(acs), "UCs", len(ucs))
print("uncovered MVP M:", uncov_m)
print("uncovered MVP S:", uncov_s)
print("uncovered AC:", ac_uncov)
print("uncovered UC:", uc_uncov)
print("unknown req ids in Req cols:", unknown_reqs)
print("missing referenced tests:", missing_refs)

if "--write" not in sys.argv:
    sys.exit(0)

def level(t):
    return t.split("-")[0] if not t.startswith("SEC-T") else "SEC-T"

LEVELS = ["UT", "IT", "E2E", "SEC-T", "PERF", "LOAD", "RES", "AIE", "RAGE", "A11Y", "UAT", "INSP"]
AREA = collections.OrderedDict([
    ("BR", "Business requirements"), ("CON", "Constraints"), ("FR", "Functional requirements"),
    ("NFR", "Non-functional requirements"), ("IF", "Interfaces"), ("SEC", "Security"),
    ("CMP", "Compliance"), ("AI", "AI behaviour"), ("RAG", "RAG"), ("KR", "Knowledge repository"),
    ("GAM", "Gamification"), ("LB", "Leaderboards"), ("I18N", "Internationalisation"),
    ("DATA", "Data"), ("RPT", "Reporting"),
])

def key(r):
    p = r.split("-")
    return (list(AREA).index(p[0]) if p[0] in AREA else 99, r)

out = []
out.append("The matrix below is generated from the Req column of every test case table in this document (sections 5–14 and 18.1). Regenerate it after any change to a test case with `python scripts/qa/gen_matrix.py --write`. Requirements are listed with their SRS tag: priority, release, verification method.\n")
mvp_m = [k for k in mvp if mvp[k][0] == "M"]
mvp_s = [k for k in mvp if mvp[k][0] == "S"]
cov_m = sum(1 for k in mvp_m if k in req_to_tests)
cov_s = sum(1 for k in mvp_s if k in req_to_tests)
cov_ac = sum(1 for a in acs if a in req_to_tests)
lvl_count = collections.Counter(level(t) for t in defined)

out.append("### 16.1 Coverage summary\n")
out.append("| Measure | Covered | Total | Coverage | Target |")
out.append("| --- | --- | --- | --- | --- |")
out.append(f"| MVP Must requirements | {cov_m} | {len(mvp_m)} | {100*cov_m/len(mvp_m):.1f}% | 100% |")
out.append(f"| MVP Should requirements | {cov_s} | {len(mvp_s)} | {100*cov_s/max(1,len(mvp_s)):.1f}% | ≥ 90% |")
out.append(f"| All MVP requirements | {cov_m+cov_s+sum(1 for k in mvp if mvp[k][0]=='C' and k in req_to_tests)} | {len(mvp)} | {100*sum(1 for k in mvp if k in req_to_tests)/len(mvp):.1f}% | ≥ 90% |")
cov_ext = sum(1 for k in ext_mvp if k in req_to_tests)
out.append(f"| External interfaces (IF-EXT, MVP) | {cov_ext} | {len(ext_mvp)} | {100*cov_ext/len(ext_mvp):.1f}% | 100% |")
out.append(f"| Acceptance criteria | {cov_ac} | {len(acs)} | {100*cov_ac/len(acs):.1f}% | 100% |")
out.append(f"| Use cases (scenarios in section 15) | {len(ucs)-len(uc_uncov)} | {len(ucs)} | {100*(len(ucs)-len(uc_uncov))/len(ucs):.1f}% | 100% |")
out.append("")
out.append("Test cases by level:\n")
out.append("| " + " | ".join(LEVELS) + " | Total |")
out.append("| " + " | ".join("---" for _ in LEVELS) + " | --- |")
out.append("| " + " | ".join(str(lvl_count[l]) for l in LEVELS) + f" | {len(defined)} |")
out.append("")
later = sorted((k for k, v in cat.items() if v[1] != "MVP"), key=key)
later_cov = [k for k in later if k in req_to_tests]
out.append(f"Release 2 and 3 requirements ({len(later)}) are out of MVP scope (section 2.2). {len(later_cov)} of them already {'has' if len(later_cov) == 1 else 'have'} test cases, which are tagged for the later release and do not gate the MVP.\n")

out.append("### 16.2 Acceptance criteria → tests\n")
out.append("| AC | Tests |")
out.append("| --- | --- |")
for a in acs:
    out.append(f"| {a} | {', '.join(req_to_tests.get(a, ['**NOT COVERED**']))} |")
out.append("")

out.append("### 16.3 Requirements → tests\n")
out.append("Columns: requirement, SRS tag, number of test cases, and the test cases grouped by level.\n")
groups = collections.OrderedDict()
for k in sorted(mvp, key=key):
    groups.setdefault(k.split("-")[0], []).append(k)
for g, ids in groups.items():
    out.append(f"#### {AREA.get(g, g)} ({g})\n")
    out.append("| Requirement | Tag | # | Tests |")
    out.append("| --- | --- | --- | --- |")
    for k in ids:
        ts = req_to_tests.get(k, [])
        ts = sorted(ts, key=lambda t: (LEVELS.index(level(t)), t))
        p, rel, v = cat[k]
        out.append(f"| {k} | {p} · {rel} · {v} | {len(ts)} | {', '.join(ts) if ts else '**NOT COVERED**'} |")
    out.append("")
out.append("#### External interfaces (IF-EXT, SRS 8.3 table)\n")
out.append("| Interface | Tag | # | Tests |")
out.append("| --- | --- | --- | --- |")
for k in ext_mvp:
    ts = sorted(req_to_tests.get(k, []), key=lambda t: (LEVELS.index(level(t)), t))
    out.append(f"| {k} | table · MVP · T | {len(ts)} | {', '.join(ts) if ts else '**NOT COVERED**'} |")
out.append("")

out.append("### 16.4 Test level coverage by requirement area\n")
out.append("Number of MVP requirements in each area that have at least one test at each level.\n")
out.append("| Area | Reqs | " + " | ".join(LEVELS) + " |")
out.append("| --- | --- | " + " | ".join("---" for _ in LEVELS) + " |")
for g, ids in groups.items():
    row = []
    for l in LEVELS:
        row.append(str(sum(1 for k in ids if any(level(t) == l for t in req_to_tests.get(k, [])))))
    out.append(f"| {g} | {len(ids)} | " + " | ".join(row) + " |")
out.append("")

matrix = "\n".join(out)
if "<!-- /MATRIX -->" in text:
    text = re.sub(r"<!-- MATRIX -->.*?<!-- /MATRIX -->", lambda _: "<!-- MATRIX -->\n\n" + matrix + "\n<!-- /MATRIX -->", text, flags=re.S)
else:
    text = text.replace("<!-- MATRIX -->", "<!-- MATRIX -->\n\n" + matrix + "\n<!-- /MATRIX -->")
open(PLAN, "w").write(text)
print("matrix written")
