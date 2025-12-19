# Epic Events CRM

## Description

Epic Events CRM est un systeme de gestion de la relation client (Customer Relationship Management) developpe pour Epic Events, une entreprise de conseil et de gestion dans l'evenementiel. L'application permet de collecter et de gerer les informations relatives aux clients, contrats et evenements de maniere securisee.

## Fonctionnalites

### Gestion des utilisateurs
- Authentification securisee avec JWT (JSON Web Token)
- Trois departements avec permissions differenciees :
  - **Commercial** : Gestion des clients et creation d'evenements
  - **Support** : Gestion des evenements assignes
  - **Management** : Administration complete du systeme

### Gestion des clients
- Creation et mise a jour des profils clients
- Association automatique au commercial responsable
- Suivi des contacts et informations de l'entreprise

### Gestion des contrats
- Creation et modification des contrats
- Suivi des montants (total et restant a payer)
- Signature des contrats
- Filtrage par statut (signes/non signes, payes/non payes)

### Gestion des evenements
- Creation d'evenements pour les contrats signes
- Attribution du personnel support
- Suivi des details (lieu, nombre de participants, dates)
- Filtrage des evenements sans support assigne

### Securite
- Mots de passe haches avec PBKDF2-SHA256
- Tokens JWT pour l'authentification persistante
- Principe du moindre privilege pour l'acces aux donnees
- Protection contre les injections SQL via ORM
- Journalisation des actions sensibles avec Sentry

## Prerequis

- Python 3.9 ou superieur
- PostgreSQL 12 ou superieur
- pip (gestionnaire de paquets Python)

## Installation

### 1. Cloner le projet

```bash
git clone <url_du_repository>
cd epic_crm
```

### 2. Creer un environnement virtuel

```bash
python -m venv venv
```

### 3. Activer l'environnement virtuel

**Windows :**
```bash
venv\Scripts\activate
```

**macOS/Linux :**
```bash
source venv/bin/activate
```

### 4. Installer les dependances

```bash
pip install -r requirements.txt
```

### 5. Configurer la base de donnees

1. Installer PostgreSQL sur votre machine
2. Creer un utilisateur et une base de donnees :

```sql
CREATE USER epic_user WITH PASSWORD 'your_password';
CREATE DATABASE epic;
GRANT ALL PRIVILEGES ON DATABASE epic TO epic_user;
```

3. Copier le fichier `.env.example` vers `.env` :

```bash
cp .env.example .env
```

4. Modifier le fichier `.env` avec vos informations :

```
DB_USERNAME=epic_user
DB_PASSWORD=your_password
DB_NAME=epic
DB_PORT=5432
DB_HOST=localhost

JWT_SECRET_KEY=votre-cle-secrete-generee-aleatoirement

SENTRY_DSN=votre-dsn-sentry
ENVIRONMENT=development
APP_VERSION=1.0.0
```

**Important :** Pour generer une cle JWT securisee :
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 6. Initialiser la base de donnees

```bash
python db_operations.py
```

## Utilisation

### Lancer l'application

```bash
python cli.py
```

### Commandes principales

Une fois dans l'interface :

```
=== Epic Events CRM ===

Commandes disponibles :
  login              - Se connecter au systeme
  logout             - Se deconnecter
  whoami             - Afficher les informations de l'utilisateur actuel
  clients            - Gestion des clients
  contracts          - Gestion des contrats
  events             - Gestion des evenements
  users              - Gestion des utilisateurs (Management uniquement)
  help               - Afficher l'aide
  exit/quit          - Quitter l'application
```

### Gestion des clients (menu clients)

```
  list               - Lister tous les clients
  create             - Creer un nouveau client
  update <id>        - Mettre a jour un client
  back               - Retour au menu principal
```

### Gestion des contrats (menu contracts)

```
  list               - Lister tous les contrats
  unsigned           - Lister les contrats non signes
  unpaid             - Lister les contrats non payes
  create             - Creer un nouveau contrat
  update <id>        - Mettre a jour un contrat
  sign <id>          - Signer un contrat
  back               - Retour au menu principal
```

### Gestion des evenements (menu events)

```
  list               - Lister tous les evenements
  no-support         - Lister les evenements sans support
  my-events          - Lister mes evenements (Support uniquement)
  create             - Creer un nouvel evenement
  update <id>        - Mettre a jour un evenement
  assign <id>        - Assigner un support a un evenement
  back               - Retour au menu principal
```

### Gestion des utilisateurs (menu users - Management uniquement)

```
  list               - Lister tous les utilisateurs
  create             - Creer un nouvel utilisateur
  update <id>        - Mettre a jour un utilisateur
  delete <id>        - Supprimer un utilisateur
  back               - Retour au menu principal
```

## Utilisateurs par defaut

Apres l'initialisation, les utilisateurs suivants sont disponibles :

| Email | Mot de passe | Departement |
|-------|--------------|-------------|
| bill.boquet@epic.com | password123 | Commercial |
| kate.hastroff@epic.com | password123 | Support |
| alice.manager@epic.com | admin123 | Management |

## Tests

### Executer les tests

```bash
pytest
```

### Executer les tests avec couverture de code

```bash
pytest --cov=. --cov-report=html
```

Le rapport de couverture sera genere dans le dossier `htmlcov/`.

## Structure du projet

```
epic_crm/
|-- auth.py              # Gestion de l'authentification JWT
|-- cli.py               # Interface en ligne de commande
|-- db_operations.py     # Operations de base de donnees et modeles
|-- main.py              # Point d'entree principal
|-- epicevents.py        # Script executable
|-- sentry_logging.py    # Configuration Sentry
|-- models.py            # Modeles de donnees (legacy)
|-- requirements.txt     # Dependances Python
|-- pytest.ini           # Configuration pytest
|-- .env.example         # Exemple de configuration
|-- .gitignore           # Fichiers ignores par Git
|-- tests/               # Tests unitaires et d'integration
    |-- __init__.py
    |-- test_models.py
    |-- test_auth.py
    |-- test_db_operations.py
```

## Schema de la base de donnees

```
+----------------+       +----------------+       +----------------+
|  departments   |       |     users      |       |    clients     |
+----------------+       +----------------+       +----------------+
| id (PK)        |<------| id (PK)        |<------| id (PK)        |
| name           |       | employee_id    |       | full_name      |
| description    |       | name           |       | email          |
+----------------+       | email          |       | phone          |
                         | password_hash  |       | company_name   |
                         | department_id  |       | creation_date  |
                         | creation_date  |       | last_update    |
                         +----------------+       | commercial_id  |
                                |                 +----------------+
                                |                         |
                                v                         v
                         +----------------+       +----------------+
                         |   contracts    |       |    events      |
                         +----------------+       +----------------+
                         | id (PK)        |<------| id (PK)        |
                         | client_id (FK) |       | contract_id    |
                         | commercial_id  |       | name           |
                         | total_amount   |       | start_date     |
                         | remaining_amt  |       | end_date       |
                         | creation_date  |       | support_id     |
                         | is_signed      |       | location       |
                         +----------------+       | attendees      |
                                                  | notes          |
                                                  +----------------+
```

## Securite

### Bonnes pratiques implementees

1. **Stockage des mots de passe** : Hachage avec PBKDF2-SHA256 et salage automatique
2. **Authentification** : Tokens JWT avec expiration (24h par defaut)
3. **Autorisation** : Verification des permissions par departement
4. **Base de donnees** : Utilisation d'un ORM (SQLAlchemy) pour prevenir les injections SQL
5. **Configuration** : Variables sensibles dans fichier .env (non commite)
6. **Journalisation** : Suivi des actions sensibles avec Sentry

### Variables d'environnement sensibles

Ne jamais commiter les fichiers suivants :
- `.env` (contient les credentials)
- `.epic_events_token` (token d'authentification)

## Journalisation Sentry

Les evenements suivants sont journalises :
- Toutes les exceptions non gerees
- Creation/modification/suppression d'utilisateurs
- Signature de contrats

Pour configurer Sentry :
1. Creer un compte sur [sentry.io](https://sentry.io)
2. Creer un nouveau projet Python
3. Copier le DSN dans le fichier `.env`

## Contribution

1. Forker le projet
2. Creer une branche pour votre fonctionnalite (`git checkout -b feature/ma-fonctionnalite`)
3. Commiter vos changements (`git commit -m 'Ajout de ma fonctionnalite'`)
4. Pousser vers la branche (`git push origin feature/ma-fonctionnalite`)
5. Ouvrir une Pull Request

## Licence

Ce projet est developpe dans le cadre d'un projet de formation OpenClassrooms.
