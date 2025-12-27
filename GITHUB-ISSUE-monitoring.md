# Contenu pour Issue GitHub

Crée une issue dans ton repo avec ces informations :

---

## Titre

```
[FEATURE] Fiabilité du pipeline d'ingestion — Monitoring & Alertes
```

## Labels

```
enhancement, priority:high
```

## Body (copie tout ce qui suit)

```markdown
## Contexte

Le pipeline d'ingestion scrape des PDFs de fournisseurs et persiste les tarifs. Actuellement, si une URL change ou si un parser casse, il n'y a pas de détection automatique.

**Problème** : Un utilisateur de l'API peut recevoir des données périmées sans le savoir.

**Objectif** : Savoir en <24h qu'un scraper est cassé, pouvoir réparer en <30 min.

## Plan d'implémentation

Voir `PLAN-monitoring.md` à la racine du repo pour les détails.

### Phases

- [ ] **Phase 6** — Mise à jour constitution (Slack → GitHub Issues)
- [ ] **Phase 1** — Script `check_sources.py` (vérification URLs)
- [ ] **Phase 2** — Table `ingest_runs` + modification pipeline
- [ ] **Phase 4** — Alertes GitHub Issues dans `nightly.yml`
- [ ] **Phase 5** — Workflow `ingest-live.yml` (vrai fetch)
- [ ] **Phase 3** — Endpoint `/v1/health/ingest`

### Critères de succès

- Si une URL de PDF retourne 404 → issue créée en <24h
- Si un parsing échoue → issue créée avec message d'erreur
- `/v1/health/ingest` montre l'état de chaque fournisseur
- Pas de régression sur les tests existants

## Fichiers impactés

- `scripts/check_sources.py` (nouveau)
- `db/ddl.sql` (modifier)
- `ingest/pipeline.py` (modifier)
- `api/app/routes/health.py` (nouveau)
- `.github/workflows/nightly.yml` (modifier)
- `.github/workflows/ingest-live.yml` (nouveau)
- `specs/constitution.md` (modifier)

## Références

- Runbooks existants : `docs/parsers/*.md`
- Constitution : `specs/constitution.md`
```

---

## Comment créer l'issue

1. Va sur https://github.com/rodjac-lab/OpenWatt/issues
2. Clique "New issue"
3. Copie le titre, ajoute les labels, colle le body
4. "Submit new issue"

Ou depuis la CLI GitHub :

```bash
gh issue create --title "[FEATURE] Fiabilité du pipeline d'ingestion — Monitoring & Alertes" --body-file GITHUB-ISSUE-monitoring.md --label "enhancement"
```
