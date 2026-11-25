# virtctl: ReadyStack build kit

The offline build kit for the Docker image `readystack/virtctl:v1.9.1-CE-scratch-r2`. It holds what the image is built from (upstream source, base images, toolchain, pinned dependencies) and the documents, so the image can be rebuilt with no network access (`docker build --network=none`).

- Release: [v1.9.1-CE-scratch-r2](https://github.com/readystack-dev/virtctl/releases/tag/v1.9.1-CE-scratch-r2)
- Image: [`docker.io/readystack/virtctl:v1.9.1-CE-scratch-r2`](https://hub.docker.com/r/readystack/virtctl/tags), manifest digest `sha256:a927e490ae9fb76f338ab6ba3aa61e653a37084b4a2eb7076bac76751bdd302a`
- Product page: https://readystack.dev/products/virtctl
- Source and build recipe: https://readystack.dev/products/virtctl/recipe
- Build trail: https://readystack.dev/products/virtctl/trail/v1.9.1-CE-scratch-r2
- Defects: this repository's Issues (defects recorded from 25 November 2026 on) and https://readystack.dev/defects.html?product=virtctl

## The image

the command-line client for the admin machine (start, stop, console, VNC, migrate, image upload). The image holds /virtctl and /virtctl-v1.9.1-linux-amd64.tar.gz (with its .sha256); copy them out with docker create + docker cp, or run the image.

## Who uses virtctl and why

Administrators and users who manage KubeVirt virtual machines from the command line.

virtctl is KubeVirt's command-line client. It adds what plain kubectl cannot do, such as serial and graphical console access, and shortcuts to start, stop and migrate virtual machines and upload disk images.

A typical use: An administrator's virtual machine stops answering on the network. With virtctl they open its serial console to see what the guest is doing, restart it if needed, and live-migrate it to another node before that node goes down for maintenance.

From the upstream project's own description: https://kubevirt.io/user-guide/user_workloads/virtctl_client_tool/, https://github.com/kubevirt/kubevirt.

## This release

- Docker Scout policy grade at release: **A** (100%), graded 2026-11-09 with `docker scout policy` (CLI 1.26.0, docker-default configuration).
- Signed with ReadyStack's release key (fingerprint `04daa92344a52dbc`): https://readystack.dev/keys/cosign.pub.
- Runs as a non-root user (`65532`).
- Attestations on the image: an SPDX SBOM and SLSA provenance v1.
- Rebuilt from this kit with network egress blocked on 2026-11-08; the rebuilt image digest is the published one.
- Base: scratch.

The current grade, measured again every day, is on https://readystack.dev/products/virtctl.

virtctl is distributed under its upstream licence (Apache-2.0); the kit contains upstream's source under that licence, and each vendored component under its own.

## Download

From the [v1.9.1-CE-scratch-r2 release](https://github.com/readystack-dev/virtctl/releases/tag/v1.9.1-CE-scratch-r2): `ReadyStack-virtctl-v1.9.1-CE-scratch-r2.tar.gz` (1.1 GB), SHA-256 `4b03455194985da190c240a791f756ea7e6c1ccb2333ef0788a51fa3dcfd75d1`.

```sh
sha256sum --check --ignore-missing SHA256SUMS
```

## Verify and rebuild

The rebuild statement is signed with the ReadyStack release key. Check the signature before you rely on it:

```sh
cosign verify-blob --key https://readystack.dev/keys/cosign.pub \
  --bundle ReadyStack-virtctl-v1.9.1-CE-scratch-r2.rebuild.json.sigstore ReadyStack-virtctl-v1.9.1-CE-scratch-r2.rebuild.json
```

Unpack with `-p` so file modes are kept, then follow the kit's own README.md and docs/REBUILD.md:

```sh
tar -xpzf ReadyStack-virtctl-v1.9.1-CE-scratch-r2.tar.gz
cd v1.9.1-CE-scratch-r2
less README.md docs/REBUILD.md
```

The build trail (`ReadyStack-virtctl-v1.9.1-CE-scratch-r2.trail.json`, signed the same way, and its Markdown copy) records how this release was built and checked.

## This repository

`recipe/` holds the kit's recipe files (Dockerfiles, build scripts, pins) as published at https://readystack.dev/products/virtctl/recipe. The complete kit is the release download. Each release is a tag here.

— ReadyStack · https://readystack.dev
