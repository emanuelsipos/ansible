# GitHub Release Download Role

An Ansible role that downloads files from GitHub releases with version tracking. It only downloads when the file is missing or when a newer version is available. Optionally installs a cron job for automatic updates.

## How it works

1. Checks if the target file exists
2. Checks the version file (e.g., `curl.ver`) next to the downloaded file
3. Queries the GitHub API for the latest release version
4. Downloads the file only if:
   - The file doesn't exist, OR
   - The version file shows an older version than the latest release, OR
   - The installed file no longer matches its expected SHA-256 checksum
5. (Optional) Installs a standalone bash script and cron job to automatically check for and download updates

## Requirements

- Ansible 2.21+
- Network access to GitHub API and releases
- `sha256sum` on the target when cron auto-update is enabled (`curl`, `jq`, and the cron service are installed by the role)

## Role Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `github_release_download_repo` | GitHub repository in `user/repo` format | `moparisthebest/static-curl` |
| `github_release_download_asset` | Asset filename to download | `curl-amd64` |
| `github_release_download_dest` | Full destination path for the file | `/opt/rustic/curl` |

### Version Pinning

| Variable | Default | Description |
|----------|---------|-------------|
| `github_release_download_version` | (unset) | Pin to a specific release tag (e.g. `v8.10.0`). Omit to always track the latest release. |

Release assets are verified with the SHA-256 digest returned by GitHub's API.
For APIs that do not provide asset digests, configure one of these options:

| Variable | Default | Description |
|----------|---------|-------------|
| `github_release_download_checksum` | (unset) | Fixed checksum in `sha256:<digest>` form |
| `github_release_download_checksum_asset` | (unset) | Release asset containing standard `sha256sum` entries |
| `github_release_download_allow_unverified` | `false` | Explicitly allow a download when no SHA-256 source is available |

Expected and calculated SHA-256 values are normalized to lowercase before
comparison, so standard manifests and API digests may use either hex case.

A fixed checksum is accepted only with `github_release_download_version`: the
role rejects an unpinned fixed checksum because it cannot verify a future
release. Use a checksum asset when intentionally tracking the latest release.

### Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `github_release_download_token` | (unset) | Optional GitHub token for API and release-asset requests. Required for private repositories and recommended when running against many hosts in parallel. |
| `github_release_download_api_url` | `https://api.github.com/repos` | GitHub-compatible releases API base URL |
| `github_release_download_token_file` | `/etc/github-release-updater/<repository>-<destination-sha256-prefix>.token` | Destination-specific, root-only token file read by the cron updater; custom names must remain directly under `/etc/github-release-updater` |

### File Permissions

| Variable | Default | Description |
|----------|---------|-------------|
| `github_release_download_mode` | `0755` | File permissions (`0755` = executable) |
| `github_release_download_owner` | (unset) | File owner |
| `github_release_download_group` | (unset) | File group |

When owner or group is omitted, the cron updater preserves that attribute from
an existing destination file.

API and asset URLs must use HTTPS. Loopback HTTP URLs are allowed for local
integration testing only. Authenticated asset URLs must remain on the configured
API origin, authorization headers are never forwarded to a redirect target, and
redirects cannot downgrade a request to HTTP.

### Cron Auto-Update

| Variable | Default | Description |
|----------|---------|-------------|
| `github_release_download_cron_enabled` | `false` | Enable cron-based auto-updates |
| `github_release_download_cron_minute` | `30` | Cron minute |
| `github_release_download_cron_hour` | `3` | Cron hour |
| `github_release_download_cron_day` | `*` | Cron day of month |
| `github_release_download_cron_weekday` | `*` | Cron day of week |
| `github_release_download_cron_month` | `*` | Cron month |
| `github_release_download_cron_user` | `root` | Must be `root`; updater files are root-only |
| `github_release_download_cron_script_dir` | `/opt/github-release-updater` | Where to store update scripts |
| `github_release_download_cron_log_file` | `/var/log/github-release-updater.log` | Log file path |
| `github_release_download_lock_dir` | `/var/lib/github-release-updater/locks` | Root-only directory for destination-specific update locks |
| `github_release_download_lock_wait_seconds` | `30` | Maximum controller wait for the per-destination update lock |
| `github_release_download_post_update_command` | (unset) | Command to run after update (e.g., restart service) |

The post-update command is rendered directly into a root-owned script and must
only contain trusted administrator-supplied configuration. The updater records
the new version only after this command succeeds, so a failed activation is
retried on the next run.

All other values rendered into the updater script are shell-quoted. Repository,
asset, and checksum-asset names cannot contain a slash or whitespace; repository
components are limited to letters, digits, dots, underscores, and hyphens.
Destination, updater, log, and token paths must be absolute, newline-free paths
without `.` or `..` segments; repeated separators are also rejected. Cron fields
use numeric, range, step, list, and `*` forms only, without whitespace or names.
The script directory is root-owned,
and the cron command single-quotes the complete updater path. The updater log is
a root-owned regular file in a trusted root-owned directory. All release updates
require the destination directory to be root-owned, non-symlinked, and not
writable by group or other users. Controller and cron updates share a
destination-specific, SHA-256-named lock in the root-only lock directory. The
controller holder retains the lock until the update and post-update command
finish; if the controller is interrupted, the orphaned holder fails closed
until it is terminated or the host reboots.
Cron script, token, and job identities include the destination, so the same
release asset can be managed at multiple paths. Disabling cron for a destination
removes that destination's updater artifacts without affecting the others.

### Other

| Variable | Default | Description |
|----------|---------|-------------|
| `github_release_download_debug` | `false` | Enable debug output |

## Usage Examples

### Basic usage (executable file)

```yaml
- hosts: servers
  roles:
    - role: github_release_download
      vars:
        github_release_download_repo: "moparisthebest/static-curl"
        github_release_download_asset: "curl-amd64"
        github_release_download_dest: "/opt/rustic/curl"
        github_release_download_mode: "0755"  # +x (this is the default)
```

### With cron auto-update (daily at 3:30 AM)

```yaml
- hosts: servers
  roles:
    - role: github_release_download
      vars:
        github_release_download_repo: "moparisthebest/static-curl"
        github_release_download_asset: "curl-amd64"
        github_release_download_dest: "/opt/rustic/curl"
        github_release_download_mode: "0755"
        github_release_download_cron_enabled: true
```

### With cron auto-update (custom schedule - every 6 hours)

```yaml
- hosts: servers
  roles:
    - role: github_release_download
      vars:
        github_release_download_repo: "moparisthebest/static-curl"
        github_release_download_asset: "curl-amd64"
        github_release_download_dest: "/opt/rustic/curl"
        github_release_download_mode: "0755"
        github_release_download_cron_enabled: true
        github_release_download_cron_minute: "0"
        github_release_download_cron_hour: "*/6"
```

### With cron and post-update command

```yaml
- hosts: servers
  roles:
    - role: github_release_download
      vars:
        github_release_download_repo: "moparisthebest/static-curl"
        github_release_download_asset: "curl-amd64"
        github_release_download_dest: "/opt/rustic/curl"
        github_release_download_cron_enabled: true
        github_release_download_post_update_command: "systemctl restart my-app"
```

### With file ownership

```yaml
- hosts: servers
  roles:
    - role: github_release_download
      vars:
        github_release_download_repo: "moparisthebest/static-curl"
        github_release_download_asset: "curl-amd64"
        github_release_download_dest: "/opt/rustic/curl"
        github_release_download_mode: "0755"
        github_release_download_owner: "appuser"
        github_release_download_group: "appuser"
        github_release_download_cron_enabled: true
```

### Multiple downloads with include_role

```yaml
- hosts: servers
  tasks:
    - name: Download static curl with auto-update
      ansible.builtin.include_role:
        name: github_release_download
      vars:
        github_release_download_repo: "moparisthebest/static-curl"
        github_release_download_asset: "curl-amd64"
        github_release_download_dest: "/opt/rustic/curl"
        github_release_download_cron_enabled: true

    - name: Download another tool
      ansible.builtin.include_role:
        name: github_release_download
      vars:
        github_release_download_repo: "some/other-repo"
        github_release_download_asset: "tool-linux-amd64"
        github_release_download_dest: "/usr/local/bin/tool"
        github_release_download_cron_enabled: true
```

## Output Variables

After the role runs, these facts are set:

| Variable | Description |
|----------|-------------|
| `github_release_download_changed` | `true` if a download occurred |
| `github_release_download_resolved_version` | The resolved version tag from GitHub |

## File Structure

After running without cron:
```
/opt/rustic/
├── curl           # The downloaded binary (executable)
└── curl.ver       # Contains the version tag (e.g., "v8.17.0")
```

After running with cron enabled:
```
/opt/rustic/
├── curl
└── curl.ver

/opt/github-release-updater/
└── github-release-update-moparisthebest-static-curl-curl-amd64-<sha256-prefix>.sh

/var/lib/github-release-updater/locks/
└── <destination-sha256>.lock

/var/log/
└── github-release-updater.log            # Update logs

# Cron entry (crontab -l):
# 30 3 * * * '/opt/github-release-updater/github-release-update-moparisthebest-static-curl-curl-amd64-<sha256-prefix>.sh'
```

## How the Cron Update Works

When `github_release_download_cron_enabled: true`, the role:

1. Creates a standalone bash script that:
    - Queries the GitHub API for the latest release
    - Compares with the current version file
    - Downloads the new version if needed
    - Shares a kernel-managed per-destination `flock` with controller updates
    - Verifies, sets ownership and permissions, then atomically renames a
      same-directory temporary binary into place
    - Atomically writes the version marker after successful activation
   - Logs all activity
   - Optionally runs a post-update command

2. Installs a cron job to run this script on your specified schedule

The script is standalone after deployment and does not require Ansible or Python. It uses `curl`, `flock`, `jq`, and `sha256sum`; the role installs the required packages. Token and script filenames include a short SHA-256 suffix to prevent collisions after name sanitization. API tokens are stored separately in a root-only file rather than embedded in the script.

## License

MIT
