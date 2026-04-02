#!/usr/bin/env python3
"""
Legge version e build_from.amd64 dalla config di un addon HA.

Uso: python3 read_meta.py <addon_dir>
Output su stdout: version|build_from_amd64
"""
import json
import os
import sys

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

addon = sys.argv[1]

for filename in ('config.yaml', 'config.json'):
    path = os.path.join(addon, filename)
    if not os.path.exists(path):
        continue
    with open(path) as f:
        cfg = yaml.safe_load(f) if (filename.endswith('.yaml') and HAS_YAML) else json.load(f)
    version    = str(cfg.get('version', 'latest'))
    build_from = (cfg.get('build_from') or {}).get('amd64', '')
    print(f'{version}|{build_from}')
    sys.exit(0)

# Nessuna config trovata
print('latest|')
