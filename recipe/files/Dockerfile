# =====================================================================================================================
# KubeVirt v1.9.1 virtctl: KubeVirt's OWN Bazel build, offline (docker buildx build --network=none).
# Stage kubevirt-build is KubeVirt's pinned builder (quay.io/kubevirt/builder, CentOS Stream 9, Bazel 6.5.0). It runs
# kubevirt-build.sh: the ReadyStack patch series (patches/, each patch says what it changes and why), KubeVirt's
# bootstrap and `bazel build //cmd/virtctl:virtctl-amd64` on vendored/virtctl-src (git archive of c3d19093f9c7), with the
# vendored Bazel repository cache (RPMs, Go SDK, rules, distroless base, libssl3 .deb: every download by sha256, none
# made here). virtctl is KubeVirt's static linux/amd64 binary; the final stage holds it
# and its deterministic tarball (sorted, mtime = SOURCE_DATE_EPOCH, owner 0:0, gzip -n) with the tarball's sha256.
# Dockerfile and Dockerfile.offline are byte copies of this file. Written by
# product-kits/kubevirt-stack/kubevirt/mk-kits.py from strategies/virtctl.json; never edit by hand.
# =====================================================================================================================
FROM quay.io/kubevirt/builder:2606231619-4fe2cd536f@sha256:a48a7dd5a1b80602269b8c714fdaa54f729a9a4a4d096f7ee0d15c94cef343e8 AS kubevirt-build
# the commit's date as the default (as every kit declares it): assemble_kit's scratch build passes no build arguments,
# and kubevirt-build.sh refuses to build without it; the canonical build and BUILD_OFFLINE.sh pass the same value
ARG SOURCE_DATE_EPOCH=1791523273
ARG KUBEVIRT_VERSION=v1.9.1
COPY vendored/virtctl-src/ /root/go/src/kubevirt.io/kubevirt/
COPY vendored/bazel-repository-cache/ /kvs/cache/repo/
COPY patches/ /kvs/kit/patches/
COPY vendor/ /kvs/kit/vendor/
COPY kubevirt-build.sh oci-rootfs.py gen_rpmdb.py gomod-sbom.py gomod-virtctl.txt kubevirt-pins.env Dockerfile.offline.pinned /kvs/kit/
# no ldconfig in a scratch image: there is no /var/cache/ldconfig/aux-cache
RUN bash /kvs/kit/kubevirt-build.sh build virtctl

FROM scratch
COPY --from=kubevirt-build /out/virtctl/ /
USER 65532
ENTRYPOINT ["/virtctl"]
ARG SOURCE_DATE_EPOCH=1791523273
# >>> readystack OCI labels: strategies/virtctl.json image_labels plus the standard OCI labels,
# the set a generated kit carries (gen_dockerfile.label_lines). Written by scripts/kit_migrations.py;
# scripts/retarget.py re-renders it with every retarget. Never edit it by hand.
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.title="virtctl"
LABEL org.opencontainers.image.description="KubeVirt v1.9.1 virtctl, built offline and bit for bit by KubeVirt's own Bazel build: the KubeVirt command-line client as a static linux/amd64 binary, in an image and as a deterministic tarball."
LABEL org.opencontainers.image.source="https://github.com/kubevirt/kubevirt"
LABEL org.opencontainers.image.version="v1.9.1-CE-scratch-r2"
LABEL org.opencontainers.image.revision="c3d19093f9c7b843b3879b18dc088911c081c39e"
# <<< readystack OCI labels
