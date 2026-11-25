#!/usr/bin/env python3
"""gomod-sbom.py <graph-dir> <src-root> <expected-list> <sbom-out-dir> <go-version> [--write-list]

rules_go binaries carry no Go module buildinfo (`go version -m` shows only the Go version), so no scanner can see the
modules they link (docs/SCAN_MATCHER_DEFECTS.md, case 3). This writes, for every Go binary in the image, an SPDX 2.3
document listing exactly the modules it links, in the image at /usr/share/kubevirt/sbom/<binary>.spdx.json, where
syft's sbom-cataloger (our cerodeo scan) and BuildKit's SBOM attestation read it.

The module set comes from Bazel, not from a hand-written list: <graph-dir> holds, per binary, the output of
`bazel cquery --notool_deps --noimplicit_deps 'filter("^//(vendor|staging)/", deps(<go_binary>))' --output=label`
with the build's own configs (kubevirt-build.sh writes <graph-dir>/<binary>.labels). Vendored packages map to modules
through <src-root>/vendor/modules.txt, replacements applied (the module and version that is compiled is named);
packages of the go.work staging modules (kubevirt.io/api, kubevirt.io/client-go) are KubeVirt's own source at this
release, named with KUBEVIRT_GIT_VERSION. It is checked against the kit's committed <expected-list> (one
"binary<TAB>module<TAB>version" line per module, sorted); the build fails when they differ, so a change to what
the image links is always a reviewed kit change. --write-list writes <expected-list> instead of checking it.

Deterministic: packages sorted, SPDX ids derived from names, created = SOURCE_DATE_EPOCH, documentNamespace from a
hash of the content."""
import hashlib
import json
import os
import re
import sys
import time

graph, src, expected, outdir, gover = sys.argv[1:6]
modtxt = os.path.join(src, "vendor", "modules.txt")
write = "--write-list" in sys.argv
sde = int(os.environ["SOURCE_DATE_EPOCH"])
kvver = os.environ.get("KUBEVIRT_GIT_VERSION", "v1.9.1")

# go.work "use" directories other than the root: KubeVirt's staging modules, each with its own go.mod module path
staging = []
if os.path.exists(os.path.join(src, "go.work")):
    for d in re.findall(r"^\s*(\./staging/\S+)\s*$", open(os.path.join(src, "go.work")).read(), re.M):
        gm = os.path.join(src, d, "go.mod")
        mod = re.search(r"^module\s+(\S+)", open(gm).read(), re.M).group(1)
        staging.append((os.path.normpath(d), mod))
staging.sort(key=lambda m: -len(m[0]))

# vendor/modules.txt: "# <module> <version> [=> <replacement> [<version>]]" heads each module's package list
mods = []
for line in open(modtxt):
    if not line.startswith("# "):
        continue
    f = line[2:].split()
    name, ver = f[0], (f[1] if len(f) > 1 and f[1] != "=>" else "")
    if "=>" in f:
        r = f[f.index("=>") + 1:]
        if r and not r[0].startswith(("./", "../")):
            name, ver = r[0], (r[1] if len(r) > 1 else ver)
    mods.append((f[0], name, ver))                 # (import prefix as vendored, module compiled, version)
mods.sort(key=lambda m: -len(m[0]))


def module_of(pkg):
    for prefix, name, ver in mods:
        if pkg == prefix or pkg.startswith(prefix + "/"):
            return name, ver
    return None


rows = set()
binaries = sorted(f[:-len(".labels")] for f in os.listdir(graph) if f.endswith(".labels"))
for b in binaries:
    for lab in open(os.path.join(graph, b + ".labels")):
        lab = lab.strip()
        m = re.match(r"//vendor/([^:]+):", lab)
        if m:
            mod = module_of(m.group(1))
            if mod is None:
                sys.exit(f"{b}: vendored package {m.group(1)} is in no module of vendor/modules.txt")
            rows.add((b, mod[0], mod[1]))
            continue
        m = re.match(r"//(staging/[^:]+):", lab)
        if m:
            hit = [mod for d, mod in staging if m.group(1) == d or m.group(1).startswith(d + "/")]
            if not hit:
                sys.exit(f"{b}: {m.group(1)} is in no go.work staging module")
            rows.add((b, hit[0], kvver))
lines = "".join(f"{b}\t{m}\t{v}\n" for b, m, v in sorted(rows))
if write:
    open(expected, "w").write(lines)
    print(f"wrote {expected}: {len(rows)} binary-module pairs")
elif open(expected).read() != lines:
    want = set(tuple(l.split("\t")) for l in open(expected).read().splitlines())
    have = set(tuple(l.split("\t")) for l in lines.splitlines())
    diff = [f"  + {' '.join(r)}" for r in sorted(have - want)] + [f"  - {' '.join(r)}" for r in sorted(want - have)]
    sys.exit("the Go modules the image links differ from the kit's " + os.path.basename(expected) + ":\n" + "\n".join(diff[:40]))

created = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(sde))
os.makedirs(outdir, exist_ok=True)
for b in binaries:
    pk = sorted((m, v) for bb, m, v in rows if bb == b)
    pk = [("stdlib", gover)] + pk
    sid = lambda n: "SPDXRef-Package-go-" + re.sub(r"[^A-Za-z0-9.-]", "-", n)
    purl = lambda n, v: f"pkg:golang/stdlib@{v.lstrip('go')}" if n == "stdlib" else f"pkg:golang/{n}@{v}"
    packages = [{"name": b, "SPDXID": "SPDXRef-Package-binary-" + re.sub(r"[^A-Za-z0-9.-]", "-", b),
                 "versionInfo": "v1.9.1", "downloadLocation": "https://github.com/kubevirt/kubevirt",
                 "filesAnalyzed": False, "primaryPackagePurpose": "APPLICATION",
                 "externalRefs": [{"referenceCategory": "PACKAGE-MANAGER", "referenceType": "purl",
                                   "referenceLocator": "pkg:golang/kubevirt.io/kubevirt@v1.9.1"}]}]
    rels = [{"spdxElementId": "SPDXRef-DOCUMENT", "relationshipType": "DESCRIBES", "relatedSpdxElement": packages[0]["SPDXID"]}]
    for n, v in pk:
        packages.append({"name": n, "SPDXID": sid(n), "versionInfo": v, "downloadLocation": "NOASSERTION",
                         "filesAnalyzed": False,
                         "externalRefs": [{"referenceCategory": "PACKAGE-MANAGER", "referenceType": "purl",
                                           "referenceLocator": purl(n, v)}]})
        rels.append({"spdxElementId": packages[0]["SPDXID"], "relationshipType": "CONTAINS", "relatedSpdxElement": sid(n)})
    body = {"spdxVersion": "SPDX-2.3", "dataLicense": "CC0-1.0", "SPDXID": "SPDXRef-DOCUMENT",
            "name": f"kubevirt-v1.9.1-{b}", "creationInfo": {"created": created, "creators": [
                "Tool: readystack-gomod-sbom (bazel cquery deps() through vendor/modules.txt)"]},
            "packages": packages, "relationships": rels}
    h = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:32]
    body["documentNamespace"] = f"https://readystack.dev/spdx/kubevirt/v1.9.1/{b}/{h}"
    p = os.path.join(outdir, f"{b}.spdx.json")
    with open(p, "w") as f:
        json.dump(body, f, indent=1, sort_keys=True)
        f.write("\n")
    os.utime(p, (sde, sde))
    print(f"GOMOD_SBOM {b}: {len(pk)} packages (stdlib + {len(pk) - 1} modules)")
