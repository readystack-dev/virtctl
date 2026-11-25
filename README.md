# virtctl: ReadyStack build kit

The offline build kit for the Docker image `readystack/virtctl:v1.9.1-CE-scratch-r2`. It holds what the image is built from (upstream source, base images, toolchain, pinned dependencies) and the documents, so the image can be rebuilt with no network access (`docker build --network=none`).

- Release: [v1.9.1-CE-scratch-r2](https://github.com/readystack-dev/virtctl/releases/tag/v1.9.1-CE-scratch-r2)
- Image: [`docker.io/readystack/virtctl:v1.9.1-CE-scratch-r2`](https://hub.docker.com/r/readystack/virtctl/tags), manifest digest `sha256:a927e490ae9fb76f338ab6ba3aa61e653a37084b4a2eb7076bac76751bdd302a`
- Product page: https://readystack.dev/products/virtctl
- Defects: this repository's Issues (defects recorded from 25 November 2026 on) and https://readystack.dev/defects.html?product=virtctl

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
