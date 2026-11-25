#!/bin/bash
# =====================================================================================================================
# kubevirt-build.sh <fetch|build|gomod-list> <component> — KubeVirt v1.9.1's OWN Bazel build of one image (or virtctl), run inside
# KubeVirt's pinned builder image (quay.io/kubevirt/builder, CentOS Stream 9, Bazel 6.5.0).
#
#   fetch  (Dockerfile.vendor, online): vendor every RPM the image's trees need into a Bazel repository cache (by
#          sha256, from the WORKSPACE URLs, KubeVirt's builddeps mirror or the CentOS Stream Koji), then let Bazel
#          fetch the rest of the external repositories (Go SDK, rules, distroless base, libssl3 .deb) into the same
#          cache with `bazel build --nobuild`.
#   build  (Dockerfile.offline.pinned, --network=none): apply the ReadyStack patch series, KubeVirt's bootstrap (its
#          bazeldnf sandbox, hack/bootstrap.sh without gazelle: the release's BUILD files are committed), the image
#          target, then its OCI layers unpacked into /out/rootfs (oci-rootfs.py: config parity with this kit's
#          Dockerfile, no build path left in any file). virtctl: the static binary and its deterministic tarball in
#          /out/virtctl.
#
# The source tree is $W (KubeVirt's own path in its builder), Bazel's output base the builder's default
# (/root/.cache/bazel/_bazel_root/<md5 of $W>), so every path the build sees is the same on every build.
# =====================================================================================================================
set -euo pipefail
MODE=${1:?fetch|build}; C=${2:?component}
KIT=/kvs/kit
W=/root/go/src/kubevirt.io/kubevirt
CACHE=${KVS_REPO_CACHE:-/kvs/cache/repo}
# shellcheck disable=SC1091
. "$KIT/kubevirt-pins.env"
export KUBEVIRT_GIT_COMMIT KUBEVIRT_GIT_TREE_STATE KUBEVIRT_GIT_VERSION
: "${SOURCE_DATE_EPOCH:?SOURCE_DATE_EPOCH must be set for a reproducible build}"
[ "$SOURCE_DATE_EPOCH" = "$KUBEVIRT_SOURCE_DATE_EPOCH" ] || {
  echo "SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH, but this kit pins $KUBEVIRT_SOURCE_DATE_EPOCH (the commit date)" >&2; exit 1; }
export SOURCE_DATE_EPOCH

case "$C" in
  virtctl) TARGET=//cmd/virtctl:virtctl-amd64 ;;
  virt-operator|virt-api|virt-controller|virt-exportproxy|virt-handler|virt-launcher) TARGET=//cmd/$C:$C-image ;;
  *) echo "unknown component $C" >&2; exit 2 ;;
esac

cd "$W"
# --- the ReadyStack patch series (each patch says what it changes and why) ------------------------------------------
for p in "$KIT"/patches/*.patch; do echo "== patch $(basename "$p")"; patch -p1 --no-backup-if-mismatch -s < "$p"; done
# as hack/bootstrap.sh does when rpm/BUILD.bazel changes: the sandbox marker follows the lock
sha=$(sha256sum rpm/BUILD.bazel | head -c 40)
sed -i "/^[[:blank:]]*sandbox_hash[[:blank:]]*=/s/=.*/=\"${sha}\"/" hack/bootstrap.sh
python3 "$KIT/gen_rpmdb.py" . --check

cat > user.bazelrc <<RC
build --repository_cache=$CACHE
fetch --repository_cache=$CACHE
query --repository_cache=$CACHE
cquery --repository_cache=$CACHE
build --color=no --curses=no --show_progress_rate_limit=60
# libnbd's wrappers.h assert() embeds __FILE__; in a sandbox that path carries the per-action sandbox number, which
# changes from build to build. Compiled in the execroot it is the same on every build.
build --strategy_regexp=libguestfs[.]org/libnbd=local
RC
ARCH=x86_64
FLAGS="--config=$ARCH --config=cs9 --define container_prefix= --define image_prefix= --define container_tag="

# The Go modules each binary of the image links, from Bazel's own graph (rules_go writes no module buildinfo).
gomod_graph() {  # gomod_graph <dir>: <dir>/<binary>.labels per go_binary in $TARGET
  local G=$1 lab cfg b
  mkdir -p "$G"
  bazel cquery $FLAGS --notool_deps --noimplicit_deps "kind(\"go_binary rule\", deps($TARGET))" --output=label \
    2>/dev/null > "$G/binaries.txt"
  [ -s "$G/binaries.txt" ] || { echo "no go_binary found in $TARGET" >&2; exit 1; }
  while read -r lab cfg; do
    b=${lab##*:}; [ "$C" = virtctl ] && b=virtctl
    bazel cquery $FLAGS --notool_deps --noimplicit_deps "filter(\"^//(vendor|staging)/\", deps($lab))" --output=label \
      2>/dev/null > "$G/$b.labels"
  done < "$G/binaries.txt"
}

if [ "$MODE" = fetch ]; then
  # every RPM of the x86_64 cs9 trees (sha256-verified); the ones this image does not use are dropped below
  echo "== vendor the RPMs (x86_64, CentOS Stream 9 trees)"
  python3 "$KIT/vendor/rpm_closure.py" . /tmp/rpm-closure.json
  python3 "$KIT/vendor/rpm_fetch.py" /tmp/rpm-closure.json "$CACHE" "$CACHE/../rpm-sources.json"
fi

# --- KubeVirt's bootstrap: its bazeldnf sandbox (hack/bootstrap.sh, minus gazelle) -----------------------------------
echo "== bootstrap $(date -u +%T)"
KUBEVIRT_BOOTSTRAPPING=true bazel run $FLAGS //rpm:sandbox_${ARCH}_cs9
touch ".bazeldnf/sandbox/$sha"
cat > .bazeldnf/sandbox.bazelrc <<RC
build --sandbox_add_mount_pair=$W/.bazeldnf/sandbox/default/root/usr/:/usr/
build --sandbox_add_mount_pair=$W/.bazeldnf/sandbox/default/root/lib64:/lib64
build --sandbox_add_mount_pair=$W/.bazeldnf/sandbox/default/root/lib:/lib
build --sandbox_add_mount_pair=$W/.bazeldnf/sandbox/default/root/bin:/bin

build --incompatible_enable_cc_toolchain_resolution --platforms=//bazel/platforms:${ARCH}-none-linux-gnu
RC
bazel clean

if [ "$MODE" = gomod-list ]; then
  gomod_graph /tmp/gomod-graph
  mkdir -p /out
  python3 "$KIT/gomod-sbom.py" /tmp/gomod-graph . "/out/gomod-$C.txt" /tmp/gomod-sbom "$KUBEVIRT_GO_SDK" --write-list
  bazel shutdown
  exit 0
fi

if [ "$MODE" = fetch ]; then
  echo "== fetch the external repositories of $TARGET"
  bazel build --nobuild $FLAGS "$TARGET"
  # keep only the RPMs Bazel fetched for this image (a fetched repository leaves external/@<name>.marker)
  EXT="$(bazel info output_base 2>/dev/null)/external"
  python3 - "$EXT" "$CACHE" /tmp/rpm-closure.json <<'PY'
import json, os, sys
ext, cache, closure = sys.argv[1:4]
rpms = json.load(open(closure))["rpms"]
drop = [r for r in rpms if not os.path.exists(os.path.join(ext, "@%s.marker" % r))]
for r in drop:
    p = os.path.join(cache, "content_addressable", "sha256", rpms[r]["sha256"])
    if os.path.isdir(p):
        for f in os.listdir(p): os.remove(os.path.join(p, f))
        os.rmdir(p)
print("RPMs kept %d, dropped %d (not used by this image)" % (len(rpms) - len(drop), len(drop)))
PY
  bazel shutdown
  rm -rf /root/.cache/bazel
  exit 0
fi

echo "== build $TARGET $(date -u +%T)"
bazel build $FLAGS "$TARGET"
OUT=$(bazel cquery $FLAGS --output=files "$TARGET" 2>/dev/null | head -1)
mkdir -p /out
if [ "$C" = virtctl ]; then
  mkdir -p /out/virtctl/pkg
  install -m 0755 "$OUT" /out/virtctl/virtctl
  install -m 0644 LICENSE /out/virtctl/pkg/LICENSE
  install -m 0755 "$OUT" /out/virtctl/pkg/virtctl
  gomod_graph /tmp/gomod-graph
  python3 "$KIT/gomod-sbom.py" /tmp/gomod-graph . "$KIT/gomod-$C.txt" /out/virtctl/usr/share/kubevirt/sbom \
    "$KUBEVIRT_GO_SDK"
  install -m 0644 /out/virtctl/usr/share/kubevirt/sbom/virtctl.spdx.json /out/virtctl/pkg/virtctl.spdx.json
  /out/virtctl/virtctl version --client | grep -q "GitVersion:\"$KUBEVIRT_GIT_VERSION\"" || {
    echo "virtctl does not report $KUBEVIRT_GIT_VERSION" >&2; exit 1; }
  if readelf -l /out/virtctl/virtctl | grep -q "program interpreter"; then echo "virtctl is not static" >&2; exit 1; fi
  T=virtctl-$KUBEVIRT_GIT_VERSION-linux-amd64.tar.gz
  tar --format=gnu --sort=name --mtime="@$SOURCE_DATE_EPOCH" --owner=0 --group=0 --numeric-owner \
      -C /out/virtctl/pkg -cf - LICENSE virtctl virtctl.spdx.json | gzip -n -9 > "/out/virtctl/$T"
  (cd /out/virtctl && sha256sum "$T" > "$T.sha256")
  rm -rf /out/virtctl/pkg
  echo "VIRTCTL_SHA256=$(sha256sum /out/virtctl/virtctl | cut -c1-64)"
  echo "VIRTCTL_TARBALL_SHA256=$(cut -c1-64 "/out/virtctl/$T.sha256")"
else
  python3 "$KIT/oci-rootfs.py" "$OUT" /out/rootfs "$KIT/Dockerfile.offline.pinned"
  gomod_graph /tmp/gomod-graph
  python3 "$KIT/gomod-sbom.py" /tmp/gomod-graph . "$KIT/gomod-$C.txt" /out/rootfs/usr/share/kubevirt/sbom \
    "$KUBEVIRT_GO_SDK"
fi
bazel shutdown
# the output base (several GB) is not part of the image: leave nothing of it in this stage
rm -rf /root/.cache/bazel
echo "== done $(date -u +%T)"
