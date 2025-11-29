# Plan : Fiabilité du pipeline d'ingestion

**Objectif** : Savoir en <24h qu'un scraper est cassé, et pouvoir réparer en <30 min.

**Contexte** : OpenWatt est un comparateur de tarifs d'électricité en France. Le pipeline d'ingestion scrape des PDFs de fournisseurs (EDF, Engie, TotalEnergies...) et persiste les tarifs en base. Actuellement, si une URL de PDF change ou si un parser casse, il n'y a pas de détection automatique ni d'alerte.

**Contraintes SpecKit** (voir `specs/constitution.md`) :
- Pas de Selenium/Playwright — on reste sur `requests + BeautifulSoup + pdfplumber`
- Stack : Python 3.11+, PostgreSQL, FastAPI, GitHub Actions
- Alertes : GitHub Issues (pas Slack)

---

## Phase 1 — Monitoring des URLs

### Objectif
Vérifier que les URLs des sources (PDFs) répondent avant de tenter le parsing.

### Livrable
Créer `scripts/check_sources.py`

### Spécifications
- Lire tous les fichiers `parsers/config/*.yaml`
- Pour chaque fichier, extraire `source.url`
- Faire un `HEAD` request (avec timeout 10s, retry 2x)
- Logger le résultat : `{supplier, url, status_code, response_time_ms, timestamp}`
- Code de sortie : 0 si tous OK, 1 si au moins un échec
- Pouvoir être appelé standalone ou importé

### Exemple de sortie
```
2025-05-29T03:15:00Z | EDF | https://particulier.edf.fr/.../Grille_prix.pdf | 200 | 342ms
2025-05-29T03:15:01Z | Engie | https://particuliers.engie.fr/.../fiche.pdf | 404 | 127ms | ERROR
```

### Tests
- Test avec mock requests (succès, 404, timeout)
- Snapshot du format de sortie

---

## Phase 2 — Table `ingest_runs`

### Objectif
Historiser chaque exécution du pipeline pour pouvoir diagnostiquer les problèmes et calculer le `data_status` automatiquement.

### Livrable
1. `db/migrations/003_ingest_runs.sql` (ou ajouter à `db/ddl.sql` selon le pattern actuel)
2. Modifier `ingest/pipeline.py` pour écrire dans cette table

### Schéma de la table
```sql
CREATE TABLE IF NOT EXISTS ingest_runs (
    id SERIAL PRIMARY KEY,
    supplier VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'success', 'failed', 'source_unavailable')),
    rows_inserted INTEGER DEFAULT 0,
    error_message TEXT,
    source_url VARCHAR(500),
    source_checksum VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ingest_runs_supplier_started ON ingest_runs(supplier, started_at DESC);
```

### Modification du pipeline
Dans `ingest/pipeline.py`, encapsuler le run :
1. INSERT au début avec `status='running'`
2. UPDATE à la fin avec `status='success'` ou `status='failed'` + `error_message`
3. Si HEAD échoue avant le fetch → `status='source_unavailable'`

### Tests
- Test d'intégration : run pipeline sur snapshot, vérifier que `ingest_runs` a une ligne

---

## Phase 3 — Endpoint `/v1/health/ingest`

### Objectif
Exposer l'état de santé de chaque fournisseur via l'API.

### Livrable
1. `api/app/routes/health.py` (ou ajouter à un fichier existant)
2. `api/app/services/health_service.py`

### Spécifications
- Route : `GET /v1/health/ingest`
- Pas d'authentification requise
- Réponse JSON :

```json
{
  "generated_at": "2025-05-29T10:00:00Z",
  "suppliers": [
    {
      "supplier": "EDF",
      "last_run_at": "2025-05-29T03:15:00Z",
      "last_run_status": "success",
      "last_success_at": "2025-05-29T03:15:00Z",
      "rows_last_inserted": 12,
      "data_status": "fresh",
      "consecutive_failures": 0
    },
    {
      "supplier": "Engie",
      "last_run_at": "2025-05-29T03:15:30Z",
      "last_run_status": "failed",
      "last_success_at": "2025-05-22T03:15:00Z",
      "error_message": "PDF structure changed - table index out of range",
      "data_status": "stale",
      "consecutive_failures": 7
    }
  ]
}
```

### Logique `data_status`
Dériver de `ingest_runs` :
- `fresh` : dernier run `success` il y a < 7 jours
- `verifying` : dernier run < 48h mais données pas encore validées
- `stale` : dernier `success` > 14 jours
- `broken` : dernier run `failed` ou `source_unavailable`

### Tests
- Test API avec DB mockée
- Snapshot de la réponse JSON

---

## Phase 4 — Alertes GitHub Issues

### Objectif
Créer automatiquement une issue GitHub quand un fournisseur est en échec.

### Livrable
Modifier `.github/workflows/nightly.yml`

### Spécifications
- Si le job d'ingestion échoue → créer une issue
- Titre : `[INGEST BROKEN] {supplier} - {date}`
- Labels : `bug`, `ingest`
- Body : message d'erreur, lien vers le run, étapes du runbook
- Éviter les doublons : chercher si une issue ouverte existe déjà pour ce supplier

### Exemple d'ajout au workflow
```yaml
- name: Create issue on failure
  if: failure()
  uses: actions/github-script@v7
  with:
    script: |
      const title = `[INGEST BROKEN] ${process.env.SUPPLIER} - ${new Date().toISOString().split('T')[0]}`;
      
      // Check for existing open issue
      const issues = await github.rest.issues.listForRepo({
        owner: context.repo.owner,
        repo: context.repo.repo,
        state: 'open',
        labels: 'ingest'
      });
      
      const existing = issues.data.find(i => i.title.includes(process.env.SUPPLIER));
      if (existing) {
        console.log(`Issue already exists: #${existing.number}`);
        return;
      }
      
      await github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: title,
        body: `## Ingest pipeline failed for ${process.env.SUPPLIER}\n\n**Error:** ${process.env.ERROR_MSG || 'See workflow logs'}\n\n**Run:** ${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}\n\n**Runbook:** docs/parsers/${process.env.SUPPLIER.toLowerCase()}.md`,
        labels: ['bug', 'ingest']
      });
```

### Tests
- Test manuel avec `workflow_dispatch` en forçant un échec

---

## Phase 5 — Workflow live fetch

### Objectif
Remplacer le test sur snapshot statique par un vrai fetch des sources pour détecter les changements.

### Livrable
Créer `.github/workflows/ingest-live.yml`

### Spécifications
```yaml
name: ingest-live

on:
  schedule:
    - cron: "30 3 * * *"  # 30 min après le nightly classique
  workflow_dispatch:
    inputs:
      supplier:
        description: 'Supplier to ingest (or "all")'
        required: false
        default: 'all'

jobs:
  ingest:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false  # Continue autres suppliers si un échoue
      matrix:
        supplier: [edf, engie, totalenergies]
    
    services:
      postgres:
        # ... (même config que nightly.yml)
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install deps
        run: pip install -r requirements.txt
      
      - name: Check source availability
        id: check
        run: python scripts/check_sources.py --supplier ${{ matrix.supplier }}
      
      - name: Run live ingest
        id: ingest
        env:
          SUPPLIER: ${{ matrix.supplier }}
        run: |
          python -m ingest.pipeline ${{ matrix.supplier }} --fetch --persist
      
      - name: Create issue on failure
        if: failure()
        uses: actions/github-script@v7
        env:
          SUPPLIER: ${{ matrix.supplier }}
        with:
          script: |
            # ... (même script que Phase 4)
```

### Points d'attention
- `fail-fast: false` : un supplier en échec ne bloque pas les autres
- Le check des sources avant l'ingest permet de distinguer "URL cassée" vs "parsing cassé"
- Garder le workflow `nightly.yml` existant pour les tests de non-régression sur snapshots

---

## Phase 6 — Mise à jour de la constitution

### Objectif
Corriger la spec pour refléter GitHub Issues au lieu de Slack.

### Livrable
Modifier `specs/constitution.md`

### Changements
Remplacer :
```markdown
- Alertes : Slack Webhook.
```

Par :
```markdown
- Alertes : GitHub Issues auto-créées par les workflows CI.
```

Et dans la section "Alerting & traçabilité" :
```markdown
- Slack alert si `parse_error`, `prix_anomal`, ou `structure_changed`.
```

Par :
```markdown
- GitHub Issue auto-créée si `parse_error`, `prix_anomal`, ou `structure_changed`.
- Notifications via l'app GitHub mobile.
```

---

## Ordre d'implémentation recommandé

1. **Phase 6** (5 min) — Mettre à jour la constitution d'abord (spec-driven)
2. **Phase 1** (1-2h) — Script check_sources.py
3. **Phase 2** (2-3h) — Table ingest_runs + modification pipeline
4. **Phase 4** (1h) — Alertes GitHub Issues dans nightly.yml
5. **Phase 5** (1-2h) — Workflow ingest-live.yml
6. **Phase 3** (2h) — Endpoint /v1/health/ingest

Rationale : on veut d'abord la détection et les alertes (valeur immédiate), l'endpoint health est un "nice to have" pour visualiser.

---

## Critères de succès

- [ ] Si une URL de PDF retourne 404, une issue GitHub est créée en <24h
- [ ] Si un parsing échoue, une issue GitHub est créée avec le message d'erreur
- [ ] `/v1/health/ingest` montre l'état de chaque fournisseur
- [ ] Les runbooks existants (`docs/parsers/*.md`) sont suffisants pour réparer en <30 min
- [ ] Pas de régression sur les tests existants

---

## Fichiers impactés

```
scripts/
  check_sources.py          # NOUVEAU

db/
  ddl.sql                   # MODIFIER (ajouter table ingest_runs)

ingest/
  pipeline.py               # MODIFIER (écrire dans ingest_runs)

api/app/
  routes/health.py          # NOUVEAU ou MODIFIER
  services/health_service.py # NOUVEAU

.github/workflows/
  nightly.yml               # MODIFIER (alertes)
  ingest-live.yml           # NOUVEAU

specs/
  constitution.md           # MODIFIER (Slack → GitHub Issues)
```

---

## Notes pour l'implémentation

- Utiliser le logger structuré existant (`api.app.core.logging`)
- Suivre le pattern async existant pour les accès DB
- Les tests doivent passer avant chaque commit
- Chaque phase peut être un commit/PR séparé
