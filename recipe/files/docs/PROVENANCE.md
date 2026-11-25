# Provenance — virtctl (`v1.9.1-CE-scratch-r2`)

Every item below is copied from a record in this archive; the record is named in brackets.

## Source

- Upstream repository: https://github.com/kubevirt/kubevirt
- Revision built: `v1.9.1` (commit `c3d19093f9c7b843b3879b18dc088911c081c39e`)
- Source tree: `de7abf04e51b6cf004d0365dfe6d8c5251edeeb69bfa0caa3d8b366b85fe6f36` over 12717 files [`docs/provenance/SOURCE_TREE_HASH.json`]
- Community Edition only: enterprise code is removed or refused before the build (CE audit at acquire).

## Build

- Method: `source-rebuild-go`; base image `scratch`
- Compiled with `--network=none` from vendored source, dependencies and base images; BuildKit pinned to `moby/buildkit:v0.31.2` (shipped in `toolchain/`).
- SOURCE_DATE_EPOCH: `1791523273` [`SOURCE_DATE_EPOCH.txt`]
- Frozen inputs: [`docs/provenance/FREEZE_MANIFEST.json`], build recipe: [`docs/provenance/BUILD_RECIPE.json`].

## Output

- Published image: `readystack/virtctl:v1.9.1-CE-scratch-r2` — index digest `sha256:b95c5d1eb381990e1c4c5c5c6362dbcaee083125a3de20b084deab9d45edb93d` [`docs/provenance/LOCKED_DIGEST.txt`]
- linux/amd64 image digest `sha256:a927e490ae9fb76f338ab6ba3aa61e653a37084b4a2eb7076bac76751bdd302a` — reproduced from this archive before publishing [`docs/provenance/REPRO_VERIFICATION.json`].

## Attestations and signature

- SBOM + SLSA provenance attached to the image: attached: an SPDX SBOM and SLSA v1 provenance [`docs/provenance/SCOUT_VERDICT.json`]
- cosign signature by the ReadyStack release key: verified before publishing. Check it: `cosign verify --key https://readystack.dev/keys/cosign.pub readystack/virtctl:v1.9.1-CE-scratch-r2`

## Pinned inputs, and why

- 16 pinned inputs, each with where it came from, why this one, how it was checked and when it was decided: `docs/PINS.md` [`docs/provenance/PINS.json`] (upstream source 2, base and build images 3, image digests 1, language runtimes and toolchains 1, dependency versions readystack sets 5, pins in the kit's dockerfiles 1, readystack's build engine 1, dependencies upstream chose 2).

## Build trail

- How this release passed through the ReadyStack harness, record by record (every chain, drive, stage, review round, defect and check, each naming the record it is copied from): `ReadyStack-virtctl-v1.9.1-CE-scratch-r2.trail.json`, published beside this archive and signed with the release key (`ReadyStack-virtctl-v1.9.1-CE-scratch-r2.trail.json.sigstore`), and readable at https://readystack.dev/products/virtctl/trail/v1.9.1-CE-scratch-r2.

