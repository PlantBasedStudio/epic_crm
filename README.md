# Epic CRM

## Description
Ce projet est un système de gestion de la relation client (CRM) développé pour Epic Events. L'application permet de collecter et de gérer les informations relatives aux clients, contrats et événements.

## Prérequis
Avant de commencer, assurez-vous d'avoir installé :
- [Python 3](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/)
- [PgAdmin](https://www.pgadmin.org/download/)

## Configuration de l'environnement

### 1. Cloner le projet
Clonez ce repository sur votre machine locale :
```bash
git clone <lien_vers_le_repository>
cd epic_crm
```

### 2. Créer un environnement virtuel
Exécutez la commande suivante pour créer un environnement virtuel :

```
python -m venv venv
```

### 3. Activer l'environnement virtuel
Sur Windows :

```
venv\Scripts\activate
```

Sur macOS/Linux :

```
source venv/bin/activate
```

### 4. Installer les dépendances
Avec l'environnement virtuel actif, installez les dépendances requises :

```
pip install -r requirements.txt
```

### 5. Configuration de la base de données
Créer un utilisateur et une base de données dans PostgreSQL (A installer localement sur la machine)
Pour cette démo j'ai utilisé le serveur localhost avec des paramètres admin et j'ai créer un utilisateur, nom de compte et mdp : user/user. A changer en cas de mise en production.
Configurer le fichier .env avec les informations de connexion à la base de données que vous avez configuré en local.
Puis lancer la création des tables : 

```
python db_operations.py

```

### 6. Lancer l'application
Exécutez le fichier principal pour démarrer l'application :


```
python main.py

```