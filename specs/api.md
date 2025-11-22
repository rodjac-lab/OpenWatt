---
id: elec-tariffs-fr.api
version: 0.2.0
status: draft
last_updated: 2025-11-22
---

# 📡 API (extrait OpenAPI)
```yaml
openapi: 3.0.3
info: { title: Elec Tariffs FR API, version: 0.2.0 }
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
  /v1/admin/runs:
    get:
      summary: Historique des jobs ingest (console admin)
  /v1/admin/overrides:
    get:
      summary: Historique des overrides sources
    post:
      summary: Declarer une URL manuelle pour relancer un fetch/parser
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                supplier: { type: string }
                url: { type: string, format: uri }
                observed_at: { type: string, format: date-time }
              required: [supplier, url]
  /v1/admin/inspect:
    post:
      summary: Inspecter un PDF selon un parser YAML (Debug interne)
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                supplier: { type: string, description: "Code du parser (ex: engie)" }
                file_path: { type: string, description: "Chemin local du PDF à analyser" }
                table_hint: { type: integer, description: "Index de table optionnel" }
              required: [supplier, file_path]
      responses:
        "200":
          description: JSON des cellules extraites (preview non persisté)
  /v1/audit/roast:
    post:
      summary: Analyse "Drop & Roast" d'une facture PDF via LLM
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file: { type: string, format: binary }
              required: [file]
      responses:
        "200":
          description: Résultat du roast vs TRVE
          content:
            application/json:
              schema:
                type: object
                properties:
                  verdict: { type: string, enum: [SCAM, SAFE, GENIUS, UNKNOWN] }
                  details:
                    type: object
                    properties:
                      annual_cost_user: { type: number }
                      annual_cost_trv: { type: number }
                      diff_euros: { type: number }
                      supplier_detected: { type: string }
                      offer_detected: { type: string }
                  chart_data:
                    type: array
                    items:
                      type: object
                      properties:
                        month: { type: string, format: date }
                        user_cumul: { type: number }
                        trv_cumul: { type: number }
