# Ridgeline app — Hiking Loadout Recommender

A local-first, LAN-only hiking loadout recommendation web application.

This repository is the **application codebase**. Deployment into the homelab
is handled by the `nixos-infra` repository, which owns the NixOS service
module, the Proxmox LXC, and the Obsidian vault bind-mount.

## Repo layout (proposed)

```
ridgeline-app/
├── app/                  # application package
│   ├── __init__.py
│   ├── server.py         # web server entry point
│   ├── routes/           # route/GPX domain
│   ├── recommendation/   # recommendation engine
│   ├── obsidian/         # read-only Obsidian gear reader
│   └── history/          # completions, field reports
├── tests/
├── pyproject.toml
├── uv.lock               # if using uv
└── README.md
```

## Deployment (handled by nixos-infra)

The application is deployed as a native NixOS systemd service inside an
unprivileged Proxmox LXC, following the existing service pattern in
`nixos-infra/nixos/modules/services/`.

### Service module (to be added to nixos-infra)

See `nixos/modules/services/ridgeline.nix` in this worktree for the
skeleton. It declares:

- `options.homelab.services.ridgeline` with `enable`, `port`, `userUid`,
  `obsidianMount`, `stateDir`
- A dedicated unprivileged service user `ridgeline`
- A systemd unit with `StateDirectory = ridgeline`, `ProtectSystem = strict`,
  `ProtectHome = true`, `ReadWritePaths` for state, and an open firewall port

### Host config (to be added to nixos-infra)

See `nixos/hosts/ridgeline/configuration.nix` in this worktree for the
stub. It sets hostname, static LAN IP, enables the service, and enables
beszel-agent for monitoring.

### Obsidian vault

The Obsidian gear notes are read-only. The Proxmox host mounts
`\\10.10.10.150\obsidian` (CIFS or NFS), and Terraform bind-mounts that
host path into the LXC read-only. The app reads gear notes from the mounted
path and never writes to it.

## State

App-owned state lives in `/var/lib/ridgeline` inside the LXC:

- SQLite database (routes, revisions, completions, field reports,
  recommendation runs, forecast snapshots)
- Managed GPX files (copied on import, content-hashed)

## Runtime

TBD — either a Python project run via `uv`, packaged as a Nix derivation,
or vendored. The NixOS module should not over-commit to the packaging
approach until the app repo settles on one.

## Access

LAN-only, no MVP login. Firewall policy is the access boundary.
