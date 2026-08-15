# pve_update_policy

Applies PVE's controlled-update policy. `apt-daily.timer` continues to refresh
package indexes, while the base APT `apt-daily-upgrade.timer` is disabled and
stopped. The install-mode timer is owned by base APT even on hosts where
optional automatic-upgrade tooling has never been installed. Automatic package
downloads and APT autoclean remain disabled. Package installation is performed
only by `pve-maintenance`, using `apt-get update` followed by `apt-get
dist-upgrade --no-remove`. Legacy third-party updater removal is intentionally
outside this role and playbook.

The role fails closed if an automatic APT service, package-manager process, or
unclean dpkg state is found. It never stops an in-progress package transaction;
let it finish or repair dpkg before rerunning the playbook.
