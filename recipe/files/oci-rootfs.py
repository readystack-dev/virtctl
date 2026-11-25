#!/usr/bin/env python3
"""oci-rootfs.py <bazel-oci-layout> <rootfs-dir> <Dockerfile> : unpack the image KubeVirt's Bazel build made into the
filesystem the kit's final stage (FROM scratch) copies, and refuse anything that would make that image differ from
Bazel's own:

  * layers are applied in manifest order the way containerd applies them (symlinks in a member's path followed inside
    the root, owners, modes, mtimes and file capabilities kept: virt-launcher-monitor carries cap_net_bind_service as
    an xattr); a whiteout entry is refused, since a Bazel-built layer has none;
  * config parity: User, Entrypoint, Cmd, Env, WorkingDir, ExposedPorts and Volumes of Bazel's image config must equal
    what the Dockerfile's final stage declares, and every label Bazel sets must be set to the same value there (the
    Dockerfile adds only the ReadyStack OCI label block);
  * no file of the image may embed a build path (a Bazel sandbox directory or the output base), the defect that made
    upstream's virt-launcher irreproducible.

Prints Bazel's own image digest, which the build log records next to the kit's published digest."""
import json
import os
import re
import shlex
import shutil
import stat
import sys
import tarfile

layout, rootfs, dockerfile = sys.argv[1:4]


def blob(d):
    return os.path.join(layout, "blobs", "sha256", d.split(":", 1)[1])


idx = json.load(open(os.path.join(layout, "index.json")))
assert len(idx["manifests"]) == 1, "expected one image in the layout"
mdig = idx["manifests"][0]["digest"]
man = json.load(open(blob(mdig)))
cfg = json.load(open(blob(man["config"]["digest"])))
print(f"BAZEL_IMAGE_DIGEST={mdig} layers={len(man['layers'])}")

# --- unpack -----------------------------------------------------------------------------------------------------------
# Each layer is applied the way containerd applies an image layer (archive/tar.go): a member's parent path is resolved
# inside the root, following symlinks there (KubeVirt's RPM tree makes /var/run a symlink to ../run and then ships
# var/run/faillock, which lands in /run/faillock); an existing entry is replaced unless both are directories; owners,
# modes, xattrs (file capabilities) and mtimes are restored, directory mtimes once the layer is done. GNU tar cannot do
# this: it holds a symlink with '..' in its target back as a placeholder file until the end, so a later member under
# it fails ("Cannot mkdir: Not a directory").
def inside(root, rel, depth=0):
    """root-relative path `rel` resolved inside root, every symlink in it followed and clamped to root (securejoin)."""
    if depth > 40:
        raise OSError(f"too many symlinks resolving {rel}")
    out = root
    parts = [x for x in rel.split("/") if x not in ("", ".")]
    for i, part in enumerate(parts):
        if part == "..":
            out = os.path.dirname(out) if out != root else root
            continue
        nxt = os.path.join(out, part)
        if os.path.islink(nxt):
            tgt = os.readlink(nxt)
            base = "" if tgt.startswith("/") else os.path.relpath(out, root)
            out = inside(root, os.path.normpath(os.path.join(base, tgt)).lstrip("/") if tgt else ".", depth + 1)
            if not out.startswith(root):
                out = root
        else:
            out = nxt
    return out


def apply_layer(root, path, n, digest):
    dirs = []
    with tarfile.open(path) as t:                                  # autodetects gzip
        for m in t:
            name = m.name.lstrip("/")
            name = name[2:] if name.startswith("./") else name
            name = name.rstrip("/")
            if not name or name == ".":
                continue
            base = os.path.basename(name)
            if base.startswith(".wh."):
                sys.exit(f"layer {n} ({digest[:19]}) has a whiteout {m.name}: not expected in a Bazel-built layer")
            parent = inside(root, os.path.dirname(name))
            os.makedirs(parent, exist_ok=True)
            dst = os.path.join(parent, base)
            if os.path.lexists(dst) and not (m.isdir() and os.path.isdir(dst) and not os.path.islink(dst)):
                if os.path.isdir(dst) and not os.path.islink(dst):
                    shutil.rmtree(dst)
                else:
                    os.unlink(dst)
            if m.isdir():
                os.makedirs(dst, exist_ok=True)
                dirs.append((dst, m))
            elif m.isreg():
                with open(dst, "wb") as f:
                    shutil.copyfileobj(t.extractfile(m), f)
            elif m.issym():
                os.symlink(m.linkname, dst)
            elif m.islnk():
                ln = m.linkname.lstrip("/")
                os.link(inside(root, ln[2:] if ln.startswith("./") else ln), dst)
                continue                                            # a hard link shares its target's inode metadata
            elif m.ischr() or m.isblk() or m.isfifo():
                kind = stat.S_IFCHR if m.ischr() else stat.S_IFBLK if m.isblk() else stat.S_IFIFO
                os.mknod(dst, kind | (m.mode & 0o7777), os.makedev(m.devmajor, m.devminor))
            else:
                sys.exit(f"layer {n}: {m.name} has tar type {m.type!r}, which this unpacker does not handle")
            os.lchown(dst, m.uid, m.gid)
            for k, v in (m.pax_headers or {}).items():
                if k.startswith("SCHILY.xattr."):
                    os.setxattr(dst, k[len("SCHILY.xattr."):], v.encode("utf-8", "surrogateescape"), follow_symlinks=False)
            if not m.issym():
                os.chmod(dst, m.mode & 0o7777)
                os.utime(dst, (m.mtime, m.mtime))
            else:
                os.utime(dst, (m.mtime, m.mtime), follow_symlinks=False)
    for dst, m in reversed(dirs):                                  # after the files inside them, as containerd does
        os.utime(dst, (m.mtime, m.mtime))


os.makedirs(rootfs, exist_ok=True)
rootfs = os.path.realpath(rootfs)
for n, layer in enumerate(man["layers"]):
    apply_layer(rootfs, blob(layer["digest"]), n, layer["digest"])

# --- config parity ----------------------------------------------------------------------------------------------------
lines, cur = [], ""
for raw in open(dockerfile).read().splitlines():
    s = raw.strip()
    if not cur and (not s or s.startswith("#")):
        continue
    if s.endswith("\\"):
        cur += s[:-1] + " "
        continue
    lines.append(cur + s)
    cur = ""
final = []
for ln in lines:
    if re.match(r"(?i)FROM\s", ln):
        final = []
    final.append(ln)
decl = {"User": "", "Entrypoint": None, "Cmd": None, "Env": [], "WorkingDir": "", "ExposedPorts": {}, "Volumes": {},
        "Labels": {}}


def kv(rest):
    out = []
    for tok in shlex.split(rest):
        k, _, v = tok.partition("=")
        out.append((k, v))
    return out


for ln in final[1:]:
    ins, _, rest = ln.partition(" ")
    ins, rest = ins.upper(), rest.strip()
    if ins == "USER":
        decl["User"] = rest
    elif ins in ("ENTRYPOINT", "CMD"):
        decl["Entrypoint" if ins == "ENTRYPOINT" else "Cmd"] = json.loads(rest)
    elif ins == "ENV":
        for k, v in kv(rest):
            decl["Env"] = [e for e in decl["Env"] if not e.startswith(k + "=")] + [f"{k}={v}"]
    elif ins == "WORKDIR":
        decl["WorkingDir"] = rest
    elif ins == "EXPOSE":
        for p in rest.split():
            decl["ExposedPorts"][p if "/" in p else p + "/tcp"] = {}
    elif ins == "VOLUME":
        for v in (json.loads(rest) if rest.startswith("[") else rest.split()):
            decl["Volumes"][v] = {}
    elif ins == "LABEL":
        decl["Labels"].update(dict(kv(rest)))
c = cfg.get("config") or {}
bad = []
for k in ("User", "Entrypoint", "Cmd", "Env", "WorkingDir", "ExposedPorts", "Volumes"):
    want = c.get(k) or ({} if k in ("ExposedPorts", "Volumes") else [] if k == "Env" else "" if k in ("User", "WorkingDir") else None)
    if decl[k] != want:
        bad.append(f"{k}: Bazel image {want!r}, Dockerfile {decl[k]!r}")
for k, v in (c.get("Labels") or {}).items():
    if decl["Labels"].get(k) != v:
        bad.append(f"label {k}: Bazel image {v!r}, Dockerfile {decl['Labels'].get(k)!r}")
if bad:
    sys.exit("config parity FAILED (the Dockerfile's final stage must declare what KubeVirt's image declares):\n  "
             + "\n  ".join(bad))
print("CONFIG_PARITY=ok " + json.dumps({k: c.get(k) for k in ("User", "Entrypoint", "Env", "WorkingDir")}))

# --- no build path in any file ----------------------------------------------------------------------------------------
LEAK = re.compile(rb"(processwrapper-sandbox/\d+|linux-sandbox/\d+|darwin-sandbox/\d+|/sandbox/[a-z-]+-sandbox/)")
hits = []
for r, _, fs in os.walk(rootfs):
    for f in fs:
        p = os.path.join(r, f)
        if os.path.islink(p) or not os.path.isfile(p):
            continue
        with open(p, "rb") as fh:
            m = LEAK.search(fh.read())
        if m:
            hits.append(f"{os.path.relpath(p, rootfs)}: {m.group(0).decode(errors='replace')}")
if hits:
    sys.exit("build paths embedded in the image (not reproducible):\n  " + "\n  ".join(hits[:20]))
print("LEAK_SCAN=ok")
