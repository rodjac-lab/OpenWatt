# Guide d'infrastructure auto-hébergée (Self-Hosted)

**Date :** 29 décembre 2025
**Objectif :** Contourner le blocage IP des fournisseurs (EDF, Engie) avec une infrastructure à IP résidentielle

---

## 🎯 Problème à résoudre

**GitHub Actions est bloqué par EDF et Engie** car les IPs des datacenters (AWS, Azure, GitHub) sont blacklistées.

**Solution :** Exécuter l'ingestion depuis une machine avec **IP résidentielle** (non-datacenter).

---

## 📊 Comparatif des solutions

| Solution | Coût | Complexité | Fiabilité | IP résidentielle | Recommandé pour |
|----------|------|------------|-----------|------------------|-----------------|
| **Raspberry Pi** | 50-100€ one-time | Moyenne | Haute | ✅ Oui (domicile) | MVP/Hobby |
| **Ordinateur personnel** | 0€ (déjà possédé) | Faible | Moyenne | ✅ Oui (domicile) | Test rapide |
| **VPS résidentiel** | 50-100€/mois | Faible | Haute | ✅ Oui (datacenter avec IP résidentielle) | Production |
| **Proxy résidentiel** | 50-150€/mois | Faible | Haute | ✅ Oui (pool d'IPs) | Production |
| **Serveur dédié Kimsufi** | 10-30€/mois | Moyenne | Haute | ⚠️ Dépend de l'IP | Production budget |

---

## 🏗️ Option 1 : Raspberry Pi (Recommandé MVP)

### Pourquoi Raspberry Pi ?

- ✅ Coût one-time ~100€
- ✅ IP résidentielle (connexion domicile)
- ✅ Faible consommation électrique (~5W)
- ✅ Silencieux, petit
- ✅ Linux complet (Ubuntu/Raspbian)
- ✅ GitHub self-hosted runner natif

### Matériel requis

| Composant | Modèle recommandé | Prix estimé |
|-----------|-------------------|-------------|
| **Raspberry Pi** | Pi 5 (8GB RAM) | ~80€ |
| **Carte microSD** | 64GB Class 10 | ~15€ |
| **Alimentation** | USB-C 5V/3A officielle | ~10€ |
| **Boîtier** | Boîtier avec ventilateur | ~10€ |
| **Total** | | **~115€** |

**Alternatives moins chères :**
- Raspberry Pi 4 (4GB) : ~60€ (suffisant pour OpenWatt)
- Pi Zero 2 W : ~15€ (possible mais limite)

### Installation pas à pas

#### Étape 1 : Installation système

```bash
# 1. Télécharger Raspberry Pi Imager
# https://www.raspberrypi.com/software/

# 2. Flasher Ubuntu Server 22.04 LTS (64-bit) sur la carte SD
# Configurer :
# - Nom d'hôte : openwatt-runner
# - Utilisateur : openwatt / mot de passe sécurisé
# - WiFi (ou Ethernet recommandé)
# - SSH activé

# 3. Insérer la carte SD et démarrer le Pi
```

#### Étape 2 : Configuration initiale

```bash
# Se connecter en SSH
ssh openwatt@openwatt-runner.local

# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer les dépendances
sudo apt install -y \
    python3.11 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    postgresql-client

# Installer Docker (optionnel, pour les tests)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker openwatt
```

#### Étape 3 : Installer GitHub Actions Runner

```bash
# Créer un dossier pour le runner
mkdir ~/actions-runner && cd ~/actions-runner

# Télécharger le runner (vérifier la dernière version sur GitHub)
curl -o actions-runner-linux-arm64-2.321.0.tar.gz \
  -L https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-linux-arm64-2.321.0.tar.gz

# Extraire
tar xzf ./actions-runner-linux-arm64-2.321.0.tar.gz

# Aller sur GitHub : Settings > Actions > Runners > New self-hosted runner
# Copier le token d'enregistrement

# Configurer le runner
./config.sh --url https://github.com/rodjac-lab/OpenWatt --token VOTRE_TOKEN

# Démarrer le runner en tant que service
sudo ./svc.sh install
sudo ./svc.sh start
```

#### Étape 4 : Installer les dépendances Python

```bash
# Cloner le repo OpenWatt
cd ~
git clone https://github.com/rodjac-lab/OpenWatt.git
cd OpenWatt

# Créer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installer les requirements
pip install -r requirements.txt

# Installer Playwright (si nécessaire pour futurs fournisseurs)
playwright install-deps
playwright install chromium
```

#### Étape 5 : Configurer les workflows GitHub Actions

Modifier `.github/workflows/ingest-live.yml` :

```yaml
jobs:
  ingest-edf-engie:
    runs-on: self-hosted  # ← Utilise le Raspberry Pi
    strategy:
      fail-fast: false
      matrix:
        supplier: [edf, engie]  # ← Ajouter EDF et Engie

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run ingest
        run: |
          python -m ingest.pipeline ${{ matrix.supplier }} --fetch --persist
        env:
          OPENWATT_DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

#### Étape 6 : Vérifier l'IP

```bash
# Vérifier que l'IP est bien résidentielle
curl https://api.ipify.org

# Tester l'accès EDF
curl -I https://particulier.edf.fr/content/dam/2-Actifs/Documents/Offres/Grille_prix_Tarif_Bleu.pdf
# Devrait retourner HTTP 200 OK

# Tester l'accès Engie
curl -I https://particuliers.engie.fr/content/dam/pdf/fiches-descriptives/fiche-descriptive-elec-reference-3-ans.pdf
# Devrait retourner HTTP 200 OK
```

### Maintenance

```bash
# Redémarrer le runner
sudo systemctl restart actions.runner.rodjac-lab-OpenWatt.openwatt-runner.service

# Voir les logs
sudo journalctl -u actions.runner.rodjac-lab-OpenWatt.openwatt-runner.service -f

# Mettre à jour le runner
cd ~/actions-runner
sudo ./svc.sh stop
./config.sh remove --token VOTRE_TOKEN
# Télécharger nouvelle version
# Re-configurer
sudo ./svc.sh install
sudo ./svc.sh start
```

### Avantages / Inconvénients

**Avantages :**
- ✅ Coût fixe one-time (~100€)
- ✅ Pas de frais mensuels
- ✅ IP résidentielle garantie
- ✅ Contrôle total
- ✅ Apprentissage intéressant

**Inconvénients :**
- ❌ Dépend de votre connexion internet domicile
- ❌ Nécessite maintenance manuelle
- ❌ Pas de SLA/garantie de disponibilité
- ❌ Coupure si déménagement/panne internet

---

## 💻 Option 2 : Ordinateur personnel (Test rapide)

**Pour tester rapidement avant d'investir dans un Raspberry Pi.**

### Installation GitHub Runner sur Windows/Mac/Linux

```bash
# Windows (PowerShell) : Télécharger depuis GitHub
# Mac/Linux : Même procédure que Raspberry Pi mais avec l'archive x64

# 1. Créer un dossier
mkdir actions-runner && cd actions-runner

# 2. Télécharger le runner
# Windows : https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-win-x64-2.321.0.zip
# Mac : https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-osx-x64-2.321.0.tar.gz
# Linux : https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-linux-x64-2.321.0.tar.gz

# 3. Configurer
./config.sh --url https://github.com/rodjac-lab/OpenWatt --token VOTRE_TOKEN

# 4. Démarrer (mode interactif pour test)
./run.sh  # ou run.cmd sur Windows
```

**Avantages :**
- ✅ 0€ (machine déjà possédée)
- ✅ Test immédiat
- ✅ Puissance de calcul élevée

**Inconvénients :**
- ❌ Ordinateur doit rester allumé 24/7
- ❌ Consommation électrique élevée
- ❌ Bruit (ventilateurs)
- ❌ Non scalable pour production

---

## 🌐 Option 3 : VPS résidentiel (Production)

### Fournisseurs recommandés

| Fournisseur | Type | Prix/mois | Avantages |
|-------------|------|-----------|-----------|
| **Bright Data** | Proxies résidentiels | ~75€ | Pool d'IPs, API simple |
| **GCORE** | VPS IP résidentielle | ~50€ | VPS complet avec IP résidentielle |
| **Leaseweb** | VPS IP clean | ~30€ | IP datacenter "propre" (peut fonctionner) |

### Setup avec Bright Data (proxy)

```python
# Dans ingest/core/fetcher.py
import os
import requests

def fetch_pdf(url: str) -> bytes:
    proxies = None

    # Utiliser proxy si configuré
    if os.getenv("BRIGHTDATA_PROXY_URL"):
        proxies = {
            "http": os.getenv("BRIGHTDATA_PROXY_URL"),
            "https": os.getenv("BRIGHTDATA_PROXY_URL")
        }

    response = requests.get(url, proxies=proxies, timeout=30)
    response.raise_for_status()
    return response.content
```

```yaml
# GitHub Actions secrets
# BRIGHTDATA_PROXY_URL=http://username:password@proxy.brightdata.com:22225
```

**Avantages :**
- ✅ Aucune infrastructure à gérer
- ✅ Disponibilité garantie (SLA)
- ✅ Pool d'IPs résidentielles
- ✅ Scalable

**Inconvénients :**
- ❌ Coût récurrent (50-150€/mois)
- ❌ Dépendance à un tiers
- ❌ Peut être bloqué si détecté comme proxy

---

## 🖥️ Option 4 : Serveur dédié Kimsufi/So You Start

### Configuration

```bash
# Louer un serveur Kimsufi (10-30€/mois)
# Vérifier l'IP avec https://www.abuseipdb.com/

# Installer Ubuntu 22.04
# Configurer GitHub self-hosted runner (même que Raspberry Pi)
```

**Avantages :**
- ✅ Coût mensuel modéré (10-30€)
- ✅ Disponibilité 24/7
- ✅ IP potentiellement "propre"
- ✅ Puissance de calcul élevée

**Inconvénients :**
- ❌ IP datacenter (peut être bloquée)
- ❌ Nécessite test préalable
- ⚠️ Pas toujours résidentielle

---

## 🔧 Configuration workflow pour self-hosted

### Workflow hybride (GitHub + Self-hosted)

```yaml
# .github/workflows/ingest-live.yml
name: ingest-live

on:
  schedule:
    - cron: "30 3 * * *"

jobs:
  # Fournisseurs sans blocage IP → GitHub Actions (gratuit)
  ingest-standard:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        supplier: [mint_indexe_trv, mint_classic_green, total_heures_eco]
    steps:
      - uses: actions/checkout@v4
      - run: python -m ingest.pipeline ${{ matrix.supplier }} --fetch --persist

  # Fournisseurs avec blocage IP → Self-hosted (Raspberry Pi)
  ingest-blocked:
    runs-on: self-hosted
    strategy:
      matrix:
        supplier: [edf, engie]
    steps:
      - uses: actions/checkout@v4
      - run: python -m ingest.pipeline ${{ matrix.supplier }} --fetch --persist
```

---

## 📊 Recommandations par contexte

### MVP / Projet perso / Apprentissage
→ **Raspberry Pi 5** (115€ one-time)

### Startup / Production légère
→ **VPS résidentiel GCORE** (50€/mois) ou **Raspberry Pi**

### Production scalable
→ **Bright Data proxy** (75€/mois) + monitoring

### Test rapide (avant décision)
→ **Ordinateur personnel** (gratuit, temporaire)

---

## ✅ Checklist de mise en production

- [ ] Infrastructure choisie et installée
- [ ] GitHub self-hosted runner configuré et actif
- [ ] Test `curl` EDF/Engie réussi (HTTP 200)
- [ ] Workflow modifié pour utiliser `runs-on: self-hosted`
- [ ] Test d'ingestion manuel réussi : `python -m ingest.pipeline edf --fetch --persist`
- [ ] Workflow automatique déclenché et réussi
- [ ] Issues GitHub #18-#37 (EDF) fermées
- [ ] Monitoring mis en place (uptime, logs)
- [ ] Documentation à jour

---

## 🆘 Dépannage

### Le runner ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u actions.runner.* -f

# Redémarrer le service
sudo systemctl restart actions.runner.*

# Vérifier la connexion GitHub
curl -I https://github.com
```

### HTTP 403 toujours présent

```bash
# Vérifier l'IP publique
curl https://api.ipify.org

# Tester depuis le runner
curl -I https://particulier.edf.fr/content/dam/2-Actifs/Documents/Offres/Grille_prix_Tarif_Bleu.pdf

# Si 403 :
# - Vérifier que le runner utilise bien l'IP résidentielle (pas de VPN)
# - Tester depuis un navigateur sur la même machine
# - Contacter le support EDF si blocage persistant
```

### Runner "offline" sur GitHub

```bash
# Vérifier que le service tourne
sudo systemctl status actions.runner.*

# Vérifier la connexion internet
ping 8.8.8.8

# Re-enregistrer le runner
cd ~/actions-runner
./config.sh remove --token OLD_TOKEN
./config.sh --url https://github.com/rodjac-lab/OpenWatt --token NEW_TOKEN
sudo ./svc.sh install
sudo ./svc.sh start
```

---

## 📚 Ressources

- **GitHub Actions Self-Hosted Runners** : https://docs.github.com/en/actions/hosting-your-own-runners
- **Raspberry Pi Documentation** : https://www.raspberrypi.com/documentation/
- **Bright Data Proxies** : https://brightdata.com/products/residential-proxies
- **GCORE VPS** : https://gcore.com/cloud/virtual-servers

---

**Document créé le 29 décembre 2025.**
**Pour questions :** ouvrir une issue avec le tag `[self-hosted]`
