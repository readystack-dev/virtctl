# virtctl v1.9.1 — ReadyStack release `v1.9.1-CE-scratch-r2`

Generated 2026-11-09 from this release's build records and strategy. Statements that come from a single record name it in brackets; the others come from this release's strategy and build log.

## Release

- **Image:** `readystack/virtctl:v1.9.1-CE-scratch-r2` (linux/amd64). Index digest `sha256:b95c5d1eb381990e1c4c5c5c6362dbcaee083125a3de20b084deab9d45edb93d` [`docs/provenance/LOCKED_DIGEST.txt`].
- **Image manifest digest:** `sha256:a927e490ae9fb76f338ab6ba3aa61e653a37084b4a2eb7076bac76751bdd302a` [`TARGET_DIGEST.txt`].
- **Upstream:** virtctl v1.9.1 built from source at `v1.9.1` of https://github.com/kubevirt/kubevirt — upstream notes: https://github.com/kubevirt/kubevirt/releases/tag/v1.9.1 [`docs/provenance/BUILD_RECIPE.json`].
- **Build:** `source-rebuild-go`, compiled offline with `--network=none`.
- **Supersedes:** ReadyStack release `v1.9.1-CE-scratch-r1`.

## What changed in this release

- Upstream version unchanged (v1.9.1); ReadyStack rebuild.
- KubeVirt v1.9.1's virtctl is unchanged from the release this supersedes (v1.9.1-CE-scratch-r1); this release rebuilds it. Changes: golang.org/x/net moves from v0.60.0 to v0.62.0 in every binary it links (GO-2026-6860, GO-2026-6866: CVE-2026-78661, high), with the versions it requires: golang.org/x/crypto v0.58.0, golang.org/x/sys v0.49.0, golang.org/x/text v0.43.0, golang.org/x/term v0.47.0 and golang.org/x/tools v0.51.0 (patch 0006, made with KubeVirt's own dependency-update path; google.golang.org/grpc stays at v1.83.2). The image's version label now names this release. Settings, ports and data are those of v1.9.1-CE-scratch-r1: replace it with this image as before.

## Security status at release (measured 2026-11-08)

- **Docker Scout:** 0 fixable critical/high vulnerabilities; runs as `65532` (non-root); SBOM + provenance attestations present (SPDX SBOM + SLSA v1) [`docs/provenance/SCOUT_VERDICT.json`].
- **OSV cross-check:** no fixable critical/high vulnerability beyond Docker Scout's findings.
- **Signature:** cosign signature verified by ReadyStack's release gate before publishing; check it yourself with `cosign verify --key https://readystack.dev/keys/cosign.pub readystack/virtctl:v1.9.1-CE-scratch-r2` (signatures are recorded in the public Sigstore transparency log).
- **ReadyStack release check at release:** passed (ReadyStack's own test, not a Docker Scout grade). Vulnerabilities are disclosed every day and the image never changes, so it is re-checked daily, beside Docker Scout's own dated grade, at https://readystack.dev/queue.

## Reproducibility

Rebuilds offline from this archive to the identical image digest `sha256:a927e490ae9fb76f338ab6ba3aa61e653a37084b4a2eb7076bac76751bdd302a`: run `./BUILD_OFFLINE.sh`, then `./VERIFY_OFFLINE.sh` (add `--online` to confirm the Docker Hub tag holds the same digest). Before publishing, ReadyStack rebuilt the kit with `./BUILD_OFFLINE.sh` and compared the result with the published digest [`docs/provenance/REPRO_VERIFICATION.json`], then ran `./BUILD_OFFLINE.sh` and `./VERIFY_OFFLINE.sh` from this archive (without `--online`).

## Validation

- 1 of 1 runbook checks passed (1 authored) on the stack's 3-node integration cluster, recorded 2026-10-29T02:34:55Z [`docs/validation/test-results.json`, from the run's record `docs/stack/RUNBOOK_EVIDENCE.json`]. They are the checks of the stack's operator runbook that name this component; no container of this image was started on its own for them. The record does not show this release's image (`sha256:a927e490ae9fb76f338ab6ba3aa61e653a37084b4a2eb7076bac76751bdd302a`) in that run: it lists the component's images as they were then, an earlier build or a tag, so the checks describe the component, not this digest.
- Failed cases are listed in `docs/validation/FAILED_TESTS.md`.

## Known issues

- **low** (ReadyStack package): REBUILD.md: Second site of the same defect (RSD-virtctl-95a6cf8e03 / 00cc1cf699), still present. [`RSD-virtctl-00cc1cf699`]
- **low** (ReadyStack package): REBUILD.md: Calls virtctl a cluster component that runs only inside a cluster; recorded in round 1 (RSD-virtctl-95a6cf8e03, 364415c465) and still present. [`RSD-virtctl-364415c465`]

## Defects fixed

- 3 problems found before release and fixed before it shipped (3 by review); each is listed in `docs/defects/defects.json`.

## Verify this archive

```
sha256sum -c CHECKSUMS.sha256
./BUILD_OFFLINE.sh && ./VERIFY_OFFLINE.sh --online
cosign verify --key https://readystack.dev/keys/cosign.pub readystack/virtctl:v1.9.1-CE-scratch-r2
```

ReadyStack records every signature in the public Sigstore transparency log (Rekor), so the command needs no extra flags.

