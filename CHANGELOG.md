# Journal des versions

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/). Les numéros suivent [SemVer](https://semver.org/lang/fr/), et la version de `pyproject.toml` est égale au tag.

## [Non publié]

### Ajouté
- Règles de protection versionnées `.github/branch-protection/{main,dev}.json` (relevées sur la protection réelle du 22/10/2026), vérifiées par le workflow `branch-protection.yml` (push sur main/dev, chaque jour) et `scripts/check_branch_protection.py` (socle Mathilde-Team/.github#1, #83).
- **`drop {}` natif** dans un pipeline `.conf` (#34) : `if [x] == "bruit" { drop { } }` écarte le document (`apply()` renvoie `None`, comme un step `"drop"` de `filters_json`) ; option `percentage` honorée comme dans Logstash.
- **Step `"date"` dans `--filters`** (#34) : `match`, `target`, `timezone`, `tag_on_failure`, comme le plugin `date` des `.conf`. Les deux mécanismes partagent désormais `filters.DateFilter` (logique déplacée d'`interpreter.py`). Un `match` mal formé est refusé dès le chargement de `--filters` (`ValueError`), et reste ignoré dans un `.conf`.

## [0.9.0] - 2026-10-22

Première version publiée sous forme de release GitHub.

### Ajouté
- **Workflow de release** (#78) : `.github/workflows/release.yml` publie une release GitHub au push d'un tag `vX.Y.Z` sur `main` (tag = version de `pyproject.toml`, notes tirées de la section `## [X.Y.Z]` de ce journal, archive des sources jointe).
