# Guide de Setup Monitoring & Observabilité

**Status**: 📋 Infrastructure à déployer
**Code**: ✅ Prêt (Sprint 2 complété)
**Infrastructure**: ❌ À configurer

---

## 🎯 Contexte

Le code de monitoring est **déjà implémenté** dans le projet (Sprint 2):

- ✅ Logs structurés JSON (structlog)
- ✅ Request-ID tracking
- ✅ Sentry SDK intégré
- ✅ Prometheus /metrics endpoint
- ✅ Retry logic + Rate limiting

**Ce guide explique comment déployer l'infrastructure pour exploiter ces outils.**

---

## 📊 État Actuel

| Composant        | Code | Infrastructure   | Action Requise       |
| ---------------- | ---- | ---------------- | -------------------- |
| Logs structurés  | ✅   | ⚠️ Pas de viewer | Setup ELK/Datadog    |
| Request-ID       | ✅   | ✅               | Aucune               |
| Sentry           | ✅   | ❌               | Créer compte gratuit |
| Prometheus       | ✅   | ❌               | Setup Grafana        |
| Retry/Rate limit | ✅   | ✅               | Aucune               |

---

## 🚀 Options de Déploiement

### Option 1: Stack Gratuite Locale (Développement)

**Coût**: Gratuit
**Temps setup**: 30 minutes
**Idéal pour**: Tests, dev local

```bash
# 1. Sentry.io (gratuit 5000 events/mois)
# 2. Prometheus + Grafana (Docker local)
# 3. Logs JSON → jq (temporaire)
```

---

### Option 2: Stack Cloud Économique (Production)

**Coût**: ~$10-15/mois
**Temps setup**: 1 heure
**Idéal pour**: Petit projet en production

```bash
# 1. Sentry.io gratuit (errors)
# 2. Grafana Cloud gratuit tier (métriques)
# 3. CloudWatch Logs AWS ($0.50/GB)
```

---

### Option 3: Stack Tout-en-un (Production Pro)

**Coût**: ~$60/mois
**Temps setup**: 30 minutes
**Idéal pour**: Projet avec budget

```bash
# Datadog: Logs + Metrics + APM + Errors ($15/host/mois)
# Better Uptime: Monitoring + Alertes ($20/mois)
```

---

## 📦 Setup Détaillé

### 1️⃣ Sentry Error Tracking (PRIORITAIRE)

**Pourquoi**: Capture toutes les erreurs production automatiquement

#### Étapes

```bash
# 1. Créer compte gratuit
https://sentry.io/signup/
# Plan gratuit: 5000 errors/mois (largement suffisant)

# 2. Créer nouveau projet
Name: openwatt
Platform: Python

# 3. Copier le DSN fourni
# Format: https://xxx@o123.ingest.sentry.io/456

# 4. Ajouter dans .env
echo "OPENWATT_SENTRY_DSN=https://xxx@o123.ingest.sentry.io/456" >> .env
echo "OPENWATT_ENVIRONMENT=production" >> .env

# 5. Redémarrer API
uvicorn api.app.main:app --reload

# 6. Tester
curl http://localhost:8000/v1/tariffs
# Les erreurs apparaissent automatiquement dans Sentry dashboard!
```

#### Configuration Avancée

**Alertes Sentry**:

```
Settings → Alerts → New Alert Rule

Conditions:
- When: Error count > 10 in 1 minute
- Action: Send email + Slack notification

Conditions:
- When: Error rate > 5%
- Action: PagerDuty (si configuré)
```

**Filtres**:

```python
# Déjà configuré dans api/app/core/sentry.py
# Ignore automatiquement:
- /health checks
- HTTPException (4xx errors)
- ValidationError
```

---

### 2️⃣ Prometheus + Grafana (Métriques)

**Pourquoi**: Visualiser latence, throughput, erreurs

#### Setup Docker Local

**Fichier**: `docker-compose.monitoring.yaml`

```yaml
version: "3.9"

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: openwatt-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--web.console.libraries=/usr/share/prometheus/console_libraries"
      - "--web.console.templates=/usr/share/prometheus/consoles"

  grafana:
    image: grafana/grafana:latest
    container_name: openwatt-grafana
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - prometheus

volumes:
  prometheus-data:
  grafana-data:
```

**Fichier**: `prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "openwatt-api"
    static_configs:
      - targets: ["host.docker.internal:8000"] # Windows/Mac
        # Pour Linux: ['172.17.0.1:8000']
    scrape_interval: 15s
```

**Lancer**:

```bash
# Créer dossier Grafana provisioning
mkdir -p grafana/provisioning/datasources
mkdir -p grafana/provisioning/dashboards

# Créer datasource Prometheus
cat > grafana/provisioning/datasources/prometheus.yml <<EOF
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

# Lancer stack
docker-compose -f docker-compose.monitoring.yaml up -d

# Accès
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
```

#### Dashboard Grafana Pré-configuré

**Fichier**: `grafana/dashboards/openwatt-overview.json`

```json
{
  "title": "OpenWatt API - Overview",
  "panels": [
    {
      "title": "Requests per Second",
      "targets": [
        {
          "expr": "rate(http_requests_total[5m])"
        }
      ]
    },
    {
      "title": "Latency P99",
      "targets": [
        {
          "expr": "histogram_quantile(0.99, http_request_duration_seconds_bucket)"
        }
      ]
    },
    {
      "title": "Error Rate",
      "targets": [
        {
          "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))"
        }
      ]
    }
  ]
}
```

**Import dans Grafana**:

```
Grafana → Dashboards → Import → Upload JSON file
```

---

### 3️⃣ Logs Structurés Viewer

**Pourquoi**: Exploiter les logs JSON pour debugging

#### Option A: ELK Stack (Local, Gratuit)

**Fichier**: `docker-compose.elk.yaml`

```yaml
version: "3.9"

services:
  elasticsearch:
    image: elasticsearch:8.11.0
    container_name: openwatt-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data

  kibana:
    image: kibana:8.11.0
    container_name: openwatt-kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

  logstash:
    image: logstash:8.11.0
    container_name: openwatt-logstash
    ports:
      - "5000:5000/tcp"
      - "5000:5000/udp"
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

volumes:
  elasticsearch-data:
```

**Fichier**: `logstash.conf`

```ruby
input {
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  # Logs déjà en JSON, pas de parsing nécessaire
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "openwatt-%{+YYYY.MM.dd}"
  }
  stdout { codec => rubydebug }
}
```

**Configurer l'API pour envoyer logs vers Logstash**:

```python
# api/app/core/logging.py
import logging
from pythonjsonlogger import jsonlogger

# Ajouter handler TCP vers Logstash
logstash_handler = logging.handlers.SocketHandler('localhost', 5000)
logstash_handler.setFormatter(jsonlogger.JsonFormatter())
logging.getLogger().addHandler(logstash_handler)
```

**Lancer**:

```bash
docker-compose -f docker-compose.elk.yaml up -d
# Kibana: http://localhost:5601
```

#### Option B: CloudWatch Logs (AWS, Payant)

**Prérequis**: API déployée sur AWS EC2/ECS

**Configuration**:

```bash
# 1. Installer CloudWatch Agent sur EC2
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# 2. Configurer agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json <<EOF
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/openwatt/api.log",
            "log_group_name": "/aws/openwatt/api",
            "log_stream_name": "{instance_id}",
            "timestamp_format": "%Y-%m-%dT%H:%M:%S"
          }
        ]
      }
    }
  }
}
EOF

# 3. Démarrer agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json \
  -s
```

**Queries CloudWatch Insights**:

```sql
# Trouver toutes les erreurs
fields @timestamp, event, level, exc_info
| filter level = "error"
| sort @timestamp desc
| limit 100

# Tracer une requête spécifique
fields @timestamp, event, request_id
| filter request_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
| sort @timestamp asc

# Erreurs par endpoint
stats count(*) as error_count by path
| filter level = "error"
| sort error_count desc
```

#### Option C: Datadog (Payant, $15/mois)

**Setup le plus simple**:

```bash
# 1. Créer compte Datadog
https://www.datadoghq.com/free-trial/

# 2. Installer agent
DD_API_KEY=xxx DD_SITE="datadoghq.com" bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script.sh)"

# 3. Configurer log collection
sudo vim /etc/datadog-agent/conf.d/python.d/conf.yaml
```

**conf.yaml**:

```yaml
logs:
  - type: file
    path: /var/log/openwatt/*.log
    service: openwatt-api
    source: python
    sourcecategory: sourcecode
```

**Redémarrer agent**:

```bash
sudo systemctl restart datadog-agent
```

**Dashboard Datadog**: Automatiquement créé, très complet.

---

## 🎯 Scénarios d'Usage

### Scénario 1: Debugging Production

```
1. User signale erreur
2. Demander request_id (dans response header X-Request-ID)
3. CloudWatch/ELK/Datadog → filter request_id
4. Voir toute la trace de cette requête
5. Identifier root cause
6. Fix + deploy
```

### Scénario 2: Performance Monitoring

```
1. Ouvrir Grafana dashboard
2. Vérifier P99 latency par endpoint
3. Si /v1/tariffs > 2s → investigate
4. Optimiser requête SQL
5. Deploy
6. Vérifier amélioration dans Grafana
```

### Scénario 3: Alerting

```
1. Configurer Sentry alert: error rate > 5%
2. Recevoir notification Slack
3. Check Sentry pour stack trace
4. Check Grafana pour métriques
5. Check logs pour contexte
6. Fix + deploy
```

---

## 📈 Métriques Clés à Suivre

### SLIs (Service Level Indicators)

```promql
# 1. Availability (uptime)
avg_over_time(up[7d]) * 100
# Target: >99.9%

# 2. Latency P99
histogram_quantile(0.99, http_request_duration_seconds_bucket)
# Target: <1s

# 3. Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
# Target: <1%

# 4. Throughput
rate(http_requests_total[5m])
# Baseline: à mesurer
```

### Alertes Recommandées

```yaml
# Grafana alerts
groups:
  - name: openwatt_critical
    rules:
      - alert: HighErrorRate
        expr: (sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) > 0.05
        for: 5m
        annotations:
          summary: "Error rate > 5% for 5 minutes"

      - alert: HighLatency
        expr: histogram_quantile(0.99, http_request_duration_seconds_bucket) > 2
        for: 5m
        annotations:
          summary: "P99 latency > 2s for 5 minutes"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        annotations:
          summary: "API is down!"
```

---

## 🔧 Configuration Production

### Variables d'Environnement

```bash
# .env.production
OPENWATT_SENTRY_DSN=https://xxx@o123.ingest.sentry.io/456
OPENWATT_ENVIRONMENT=production
OPENWATT_LOG_LEVEL=INFO  # DEBUG pour dev, INFO pour prod
```

### Rotation Logs

**Logrotate config** (`/etc/logrotate.d/openwatt`):

```
/var/log/openwatt/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 openwatt openwatt
    sharedscripts
    postrotate
        systemctl reload openwatt-api
    endscript
}
```

---

## 📚 Ressources

### Documentation

- [Structlog](https://www.structlog.org/)
- [Sentry Python](https://docs.sentry.io/platforms/python/)
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)

### Dashboards Grafana Publics

- [FastAPI Observability](https://grafana.com/grafana/dashboards/16234)
- [Prometheus 2.0 Stats](https://grafana.com/grafana/dashboards/3662)

### Tutoriels

- [ELK Stack Setup](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
- [Datadog Python](https://docs.datadoghq.com/logs/log_collection/python/)

---

## ✅ Checklist Setup Production

**Avant déploiement**:

- [ ] Créer compte Sentry.io
- [ ] Configurer OPENWATT_SENTRY_DSN
- [ ] Setup Prometheus + Grafana (local ou cloud)
- [ ] Importer dashboard Grafana
- [ ] Configurer alertes (errors > 5%, latency > 2s)
- [ ] Tester logs structurés (CloudWatch/ELK/Datadog)
- [ ] Vérifier /metrics endpoint accessible
- [ ] Configurer rotation logs (logrotate)
- [ ] Documenter runbook incidents

**Après déploiement**:

- [ ] Vérifier dashboard Grafana affiche données
- [ ] Tester alerte Sentry (générer erreur volontaire)
- [ ] Vérifier logs arrivent dans viewer
- [ ] Baseline métriques (latency, throughput)
- [ ] Configurer notifications Slack/Email

---

## 💰 Coûts Estimés

### Stack Gratuite (Dev/Hobby)

```
Sentry.io free tier: $0/mois (5000 events)
Prometheus + Grafana local: $0/mois
Logs jq local: $0/mois
Total: $0/mois
```

### Stack Cloud Économique (Petit Projet)

```
Sentry.io free tier: $0/mois
Grafana Cloud free tier: $0/mois (10k metrics)
CloudWatch Logs: ~$5/mois (10 GB)
Total: ~$5/mois
```

### Stack Production Pro

```
Sentry Business: $26/mois
Datadog Pro: $15/host/mois
Better Uptime: $20/mois
Total: ~$60/mois
```

---

## 🎓 Formation Équipe

### Sessions Recommandées

1. **Introduction Logs Structurés** (1h)
   - Différence logs texte vs JSON
   - Comment logger avec structlog
   - Recherche dans CloudWatch/Kibana

2. **Sentry Deep Dive** (1h)
   - Dashboard Sentry
   - Stack traces
   - Breadcrumbs
   - Release tracking

3. **Grafana & Prometheus** (2h)
   - Requêtes PromQL
   - Création dashboards
   - Configuration alertes
   - Interprétation métriques

---

## 📝 Notes Importantes

1. **Logs structurés sont déjà actifs** dès que tu lances l'API
2. **Sentry s'active uniquement** si OPENWATT_SENTRY_DSN est configuré
3. **/metrics est déjà accessible** sur http://localhost:8000/metrics
4. **Retry logic + rate limiting** sont dans le code mais doivent être utilisés explicitement dans les scripts d'ingestion

---

**Prochaine étape recommandée**: Setup Sentry gratuit (5 minutes) pour commencer à capturer les erreurs.

---

**Dernière mise à jour**: 2025-11-15
**Auteur**: Claude Code (Sprint 2)
**Related**: docs/sprint-2-summary.md, docs/logging.md
