---
id: elec-tariffs-fr.api
version: 0.1.0
status: draft
last_updated: 2025-11-11
---

# 📡 API (extrait OpenAPI)
```yaml
openapi: 3.0.3
info: { title: Elec Tariffs FR API, version: 0.1.0 }
paths:
  /v1/tariffs:
    get:
      summary: Derniers tarifs (fresh par défaut)
      parameters:
        - name: option
          in: query
          schema: { enum: [BASE, HPHC, TEMPO] }
        - name: puissance
          in: query
          schema: { type: integer, enum: [3,6,9,12,15,18,24,30,36] }
        - name: include_stale
          in: query
          schema: { type: boolean, default: false }
      responses:
        "200": { description: OK }
  /v1/tariffs/history:
    get:
      summary: Historique insert-only
      parameters:
        - name: supplier
          in: query
          schema: { type: string }
        - name: option
          in: query
          schema: { enum: [BASE, HPHC, TEMPO] }
        - name: puissance
          in: query
          schema: { type: integer }
        - name: since
          in: query
          schema: { type: string, format: date }
        - name: until
          in: query
          schema: { type: string, format: date }
  /v1/guards/trve-diff:
    get:
      summary: Écart vs TRVE (dernier tarif)
```
