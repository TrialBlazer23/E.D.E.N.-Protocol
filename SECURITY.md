# Security Policy

## Supported versions

Security fixes are applied to the latest `main` branch and to the latest
tagged release, when releases exist. Older tags and forks are not maintained
as separate supported lines.

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub Security Advisories:
use **Report a vulnerability** on this repository's Security tab. Do not open
a public issue or pull request that describes an exploitable flaw, and do not
include secrets or proof-of-concept exploit code in public discussion.

You should hear back as soon as practical. If the report is accepted, a fix
will be prepared and credited as you prefer. If it is declined, you will get
a short explanation.

## Trust model for remote bootstrap (`EDEN_RAW_BASE`)

`init-eden.sh` and `init-eden.ps1` normally copy files from a local checkout
of this repository. If that checkout is incomplete, they can download the
protocol files from the URL in `EDEN_RAW_BASE` and then execute
`scripts/eden-install.py` from the downloaded tree.

That download path is opt-in and equivalent to running code from wherever the
URL points. Treat `EDEN_RAW_BASE` like an install script:

- Prefer a local clone you have reviewed, or pin the URL to a specific commit
  (for example
  `https://raw.githubusercontent.com/TrialBlazer23/E.D.E.N.-Protocol/<commit-sha>`),
  not a moving branch name, when you use a remote source.
- Optionally set `EDEN_SHA256` to the SHA-256 digest of
  `scripts/eden-install.py` (64 hex digits) or to a path to a
  `sha256sum`-format file listing hashes of downloaded paths. If the digest
  does not match, the wrapper exits before running the installer.
- Do not point `EDEN_RAW_BASE` at an untrusted host. There is no built-in
  signature check beyond the optional `EDEN_SHA256` comparison.
