# JARVIS 2KR — prototype

Assistant web multiplateforme inspiré d'une interface de science-fiction : iPhone + PC, compte partagé, mémoire SQLite, IA en ligne, voix navigateur et confirmation des actions de démonstration.

## Prérequis
Python 3.11+. Une clé API OpenAI est nécessaire pour les réponses IA réelles.

## Installation Windows PowerShell
```powershell
cd jarvis-2kr
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
Modifiez `.env` : définissez `APP_SECRET` avec une longue valeur aléatoire et ajoutez `OPENAI_API_KEY`.

## macOS / Linux
```bash
cd jarvis-2kr
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Lancer
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
PC : http://127.0.0.1:8000. Pour l'iPhone sur le même Wi-Fi, ouvrez `http://IP_LOCALE_DU_PC:8000`. Autorisez le port 8000 sur le réseau privé. La reconnaissance vocale peut nécessiter HTTPS et dépend du navigateur. Ne publiez pas le serveur directement sur Internet.

## Tests
```bash
pytest -q
```

## Limites et sécurité
Ce prototype n'est pas un assistant omnipotent et ne contrôle pas encore les applications natives, n'envoie pas d'e-mails et n'exécute pas de commandes système. Le module d'actions est une démonstration : même après confirmation, aucune action externe n'est exécutée. Les vrais outils doivent être intégrés individuellement avec permissions minimales, confirmation côté serveur et tests. La clé API reste côté serveur. Pour une production publique, utilisez HTTPS, PostgreSQL, limitation de débit, récupération de compte, MFA et journaux de sécurité.
