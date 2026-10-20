# FEATURES.md — Fonctionnalités et backlog

## Fonctionnalités implémentées

### Pipeline principal
- **rsyslog omprog** — Réception des messages syslog via asyncio
- **confirmMessages="on"** — Accusé de réception rsyslog (re-émission après perte)
- **Format JSON** — Codec JSON rsyslog (rsyslog → omprog → Python)

### Filtres (module filters.py, --filters)
| Filtre | Options | Session |
|--------|---------|---------|
| **drop** | source, words_file, mode (contains), case_sensitive | 8 |
| **regex** | source, pattern (groupes nommés) | 8 |
| **kv** | source, field_split, value_split, prefix | 8 |
| **mutate** | convert (integer/string), remove_field, prefix | 14 |
| **mutate** | uppercase, lowercase, capitalize, split, join, merge, copy, update, coerce | 20 |
| **geoip** | source, target, tag_on_failure | 24 |

### Enrichissement (module enrichment.py)
- Dictionnaire statique JSON (`enrich-dict.example.json`)
- GeoIP via geoip2/maxminddb (`_build_geoip_record`, session 21)

### Pipeline Logstash (module interpreter.py, --pipeline-conf)
- Parsing des fichiers `.conf` via `logstash-pipeline-parser`
- Exemples : `pipeline.example.d/10_input`, `25_filter`, `30_output`
- tag_on_failure pour date et geoip (sessions 19, 22, 24)

### Indexation OpenSearch (module indexer.py)
- `OpenSearchIndexer` — indexation asynchrone (opensearch-py[async])
- Authentification via variables d'environnement
- Template d'index (`opensearch-index-template.json`)
- Retenue (retry) sur erreurs transitoires (connexion refusée, timeout)

### Dead Letter Queue (module dlq.py, session 13)
- `LocalDeadLetterQueue.write()` — JSONL append-only
- Uniquement pour erreurs permanentes (RequestError/NotFoundError, 400/404)
- Jamais pour erreurs transitoires (retenue inchangée)
- Écriture dans thread séparé (`asyncio.to_thread`)
- Rotation par taille (`max_bytes`) ou par âge de la plus ancienne entrée (`max_age`), compression gzip, purge par nombre (`backups`) et par âge (`retention`), `parse_size`/`parse_duration` pour les options CLI (issue #27)

### Fingerprint (module fingerprint.py, session 17)
- `compute_fingerprint()` — sha256/sha1/md5
- Document entier (fields=None/[]) ou sélection ordonnée de champs
- Séparateur de contrôle `\x1f` anti-collision
- `None` si tous les champs demandés sont absents

### Traçabilité (module tracing.py)
- Décorateur `@traced` — entrée/sortie systématique (loguru)
- Préserve `__name__`/`__doc__`/`__wrapped__` (functools.wraps)
- Compatible méthodes GObject/GTK4

## Items "Proposé" — Statut

| # | Item | Statut | Session |
|---|------|--------|---------|
| 2 | Dead Letter Queue pour échecs permanents | ✅ Fait | 13 |
| 4 | Fingerprint déterministe pour document_id | ✅ Fait | 17 |

## Limites connues

### DLQ (dlq.py)
- Rotation/purge : options `--dlq-max-size`, `--dlq-max-age`, `--dlq-backups`, `--dlq-retention`, `--dlq-no-compress` de `omprog.py` (issue #27)

### Fingerprint (fingerprint.py)
- Pas de mode HMAC (nécessiterait une clé secrète)
- Pas de MURMUR3 (entier 32 bits, format _id différent)
- Pas de IPV4_NETWORK (portée trop spécifique)
- Voir issue #28

### Templates (templates.py)
- Rendu des valeurs aligné sur Logstash 8 (`StringInterpolation`, issue #49) : booléen `true`/`false`, liste jointe par `,`, objet en JSON compact
- **Changement de comportement (#49)** : un `document_id`, un nom d'index ou une empreinte construit à partir d'un booléen (`True` → `true`), d'une liste (`['a', 'b']` → `a,b`) ou d'un objet (repr Python → JSON) change de valeur — à signaler dans les notes de version (doublons possibles dans OpenSearch pour les documents déjà indexés avec l'ancien rendu)
- Références mal formées refusées (`ValueError`) comme par Logstash : `a[b]`, `a]`, `[]`, `[a[b]]`
- Écart assumé : un objet à l'intérieur d'une liste est rendu en JSON (Logstash utilise le `toString()` Java de la map)
- Rendu d'un champ `null` : chaîne vide — écart assumé avec Logstash 8, qui conserve le gabarit `%{champ}` littéral. **Fingerprint (#29, décision Mathilde)** : un champ `null` est distingué d'un champ absent — il compte comme présent (empreinte du contenu vide), `None` uniquement si tous les champs demandés sont absents

### Point d'entrée (omprog.py)
- Reconstruit en 2026 (issue #40) : le fichier d'origine n'a pas été retrouvé
- Sorties `output{}` honorées : `opensearch` et `elasticsearch` (`index`, `document_id`) ; `hosts` du pipeline ignoré (nœuds de `--opensearch-host`)
- `${VAR}` des pipelines `.conf` non substitués (variables d'environnement Logstash)

### Indexer (indexer.py)
- Réponse du serveur aux redirections (imprimante/série/parallèle) traitée côté serveur, jamais remontée à l'API
- **Multi-nœuds et failover (#37)** : le transport opensearch-py retente le nœud suivant en cas d'échec de connexion ; `retry_on_timeout=True` étend le repli aux délais d'attente (défaut de la bibliothèque : False). `health()` (GET /) alimente le health check périodique d'omprog (`--health-check-interval`, défaut 300 s, 0 = désactivé) — un échec journalise un warning, sans jamais interrompre le pont

## Backlog

| Item | Priorité | Issue |
|------|----------|-------|
| Fingerprint HMAC/MURMUR3 | P3 | #28 |
| Packaging package installable | P3 | #31 |
| `--document-id-template` (complément du fingerprint) | P3 | #33 |
| Filtres Logstash avancés (date, grok) | P3 | #34 |
| Métriques et monitoring (Prometheus/Grafana) | P3 | #35 |
| Internationalisation complète | — | #38 |

Terminé : #25 (modules manquants + tests), #26 (README), #29 (null distingué d'absent — décision Mathilde), #30 (test d'intégration bout en bout), #32 (fichiers de suivi), #37 (failover multi-nœuds + health check périodique).
