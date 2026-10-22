# Journal des versions

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/). Les numéros suivent [SemVer](https://semver.org/lang/fr/), et la version de `pyproject.toml` est égale au tag.

## [Non publié]

### Ajouté
- **`drop {}` natif** dans un pipeline `.conf` (#34) : `if [x] == "bruit" { drop { } }` écarte le document (`apply()` renvoie `None`, comme un step `"drop"` de `filters_json`) ; option `percentage` honorée comme dans Logstash.

## [0.9.0] - 2026-10-22

Première version publiée sous forme de release GitHub.

### Ajouté
- **Workflow de release** (#78) : `.github/workflows/release.yml` publie une release GitHub au push d'un tag `vX.Y.Z` sur `main` (tag = version de `pyproject.toml`, notes tirées de la section `## [X.Y.Z]` de ce journal, archive des sources jointe).
