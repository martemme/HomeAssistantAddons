#!/usr/bin/env python3
"""
Aggiorna repository.json con i metadati degli addon buildati con successo.
Upserta ogni addon (match su slug). Il file viene creato se non esiste.

Uso: python3 update_repo.py <gitea_user> <addon1> [addon2 ...]

Variabili d'ambiente richieste:
  REGISTRY        es. registry.mt-home.uk
  GITEA_BASE_URL  es. https://git.mt-home.uk
"""
import json
import os
import sys

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

REGISTRY       = os.environ['REGISTRY']
GITEA_BASE_URL = os.environ['GITEA_BASE_URL']
GITEA_USER     = sys.argv[1]
addons_arg     = sys.argv[2:]

REPO_FILE = 'repository.json'
skeleton  = {
    'name':       f'HA Add-ons by {GITEA_USER}',
    'url':        f'{GITEA_BASE_URL}/{GITEA_USER}/HomeAssistantAddons',
    'maintainer': GITEA_USER,
    'addons':     [],
}

repo = skeleton.copy()
if os.path.exists(REPO_FILE):
    with open(REPO_FILE) as f:
        repo = json.load(f)
repo.setdefault('addons', [])


def load_cfg(addon_dir):
    for name, use_yaml in [('config.yaml', True), ('config.json', False)]:
        p = os.path.join(addon_dir, name)
        if not os.path.exists(p):
            continue
        with open(p) as f:
            return yaml.safe_load(f) if (use_yaml and HAS_YAML) else json.load(f)
    return {}


changed = False
for addon in addons_arg:
    cfg = load_cfg(addon)
    if not cfg:
        print(f'[WARN] Nessuna config trovata per {addon}, skip', flush=True)
        continue

    slug    = cfg.get('slug', addon)
    version = str(cfg.get('version', 'latest'))
    entry   = {
        'slug':        slug,
        'name':        cfg.get('name', addon),
        'description': cfg.get('description', ''),
        'version':     version,
        'url':         cfg.get('url', ''),
        'arch':        cfg.get('arch', ['amd64']),
        'image':       f'{REGISTRY}/hassio-addons/{slug}:{version}',
    }

    idx = next((i for i, a in enumerate(repo['addons']) if a.get('slug') == slug), None)
    if idx is not None:
        old_ver = repo['addons'][idx].get('version', '?')
        repo['addons'][idx] = entry
        print(f'[UPDATE] {slug}: {old_ver} → {version}', flush=True)
    else:
        repo['addons'].append(entry)
        print(f'[ADD]    {slug} v{version}', flush=True)
    changed = True

if changed:
    with open(REPO_FILE, 'w') as f:
        json.dump(repo, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('[OK] repository.json aggiornato', flush=True)
else:
    print('[INFO] Nessuna modifica a repository.json', flush=True)
