#!/bin/bash
# Garante que o usuário "webapp" (que roda o site) consiga GRAVAR no banco SQLite.
mkdir -p /var/app/data
chown -R webapp:webapp /var/app/data
chmod 775 /var/app/data
[ -f /var/app/data/db.sqlite3 ] && chmod 664 /var/app/data/db.sqlite3
exit 0
