# zsh

Installs zsh, deploys a monolithic server-focused profile, and configures it as
the login shell for selected existing users.

The managed profile provides:

- completion without an external plugin framework
- private, timestamped command history shared across active sessions
- case-insensitive completion matching
- `user@hostname`, current directory, and Git branch in the prompt
- the previous command's exit status when non-zero
- a bold red identity when running as root
- a small set of familiar directory-listing aliases

The prompt deliberately avoids querying Docker or other services so it remains
responsive while debugging an unhealthy host. Prefix a command with a space to
exclude it from history when it contains sensitive values.

## Variables

| Variable | Default | Description |
| --- | --- | --- |
| `zsh_package` | `zsh` | Package that provides zsh |
| `zsh_shell` | `/usr/bin/zsh` | Login shell path |
| `zsh_users` | `[ansible_user]` | Existing users whose login shell is changed |

The role resolves each user's home directory from the local passwd database and
manages `.zshrc` there. Local changes to that file are overwritten. Command
history is stored in `.zsh_history` with mode `0600`.

Override `zsh_users` to configure more than the Ansible connection user:

```yaml
zsh_users:
  - ansible
  - root
```
