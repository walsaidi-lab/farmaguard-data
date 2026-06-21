# farmaguard-data

Données publiques des pharmacies de garde (Casablanca, Rabat, Meknès) pour l'app FarmaGuard.

- `backend/scraper.py` récupère la garde du jour.
- `.github/workflows/update-pharmacies.yml` lance le scraper 2×/jour (cron) et publie `pharmacies.json`.
- L'app FarmaGuard télécharge `pharmacies.json` via son URL brute.

Ce dépôt ne contient **aucun code source de l'app** ni secret — uniquement des données publiques. Le code de l'app reste privé.

URL des données (après activation) :
```
https://raw.githubusercontent.com/<TON_USER>/farmaguard-data/main/pharmacies.json
```
