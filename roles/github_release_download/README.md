# GitHub Release Download Role

An Ansible role that downloads files from GitHub releases with version tracking. It only downloads when the file is missing or when a newer version is available. Optionally installs a cron job for automatic updates.

## How it works

1. Checks if the target file exists
2. Checks the version file (e.g., `curl.ver`) next to the downloaded file
3. Queries the GitHub API for the latest release version
4. Downloads the file only if:
   - The file doesn't exist, OR
   - The version file shows an older version than the latest release
5. (Optional) Installs a standalone bash script and cron job to automatically check for and download updates

## Requirements

- Ansible 2.14+
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

For executable assets, pin a version and configure one of these verification options:

| Variable | Default | Description |
|----------|---------|-------------|
| `github_release_download_checksum` | (unset) | Fixed checksum in `sha256:<digest>` form |
| `github_release_download_checksum_asset` | (unset) | Release asset containing standard `sha256sum` entries |

### Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `github_release_download_token` | (unset) | Optional GitHub token for API and release-asset requests. Required for private repositories and recommended when running against many hosts in parallel. |
| `github_release_download_api_url` | `https://api.github.com/repos` | GitHub-compatible releases API base URL |
| `github_release_download_token_file` | `/etc/github-release-updater/github.token` | Root-only token file read by the cron updater |

### File Permissions

| Variable | Default | Description |
|----------|---------|-------------|
| `github_release_download_mode` | `0755` | File permissions (`0755` = executable) |
| `github_release_download_owner` | (unset) | File owner |
| `github_release_download_group` | (unset) | File group |

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
| `github_release_download_cron_post_update_command` | (unset) | Command to run after update (e.g., restart service) |

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
        github_release_download_cron_post_update_command: "systemctl restart my-app"
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
└── github-release-update-moparisthebest-static-curl-curl-amd64.sh

/var/log/
└── github-release-updater.log            # Update logs

# Cron entry (crontab -l):
# 30 3 * * * /opt/github-release-updater/github-release-update-moparisthebest-static-curl-curl-amd64.sh
```

## How the Cron Update Works

When `github_release_download_cron_enabled: true`, the role:

1. Creates a standalone bash script that:
   - Queries the GitHub API for the latest release
   - Compares with the current version file
   - Downloads the new version if needed
   - Sets the correct permissions
   - Logs all activity
   - Optionally runs a post-update command

2. Installs a cron job to run this script on your specified schedule

The script is standalone after deployment and does not require Ansible or Python. It uses `curl`, `jq`, and `sha256sum`; the role installs the first two when cron updates are enabled. API tokens are stored separately in a root-only file rather than embedded in the script.

## License

MIT
