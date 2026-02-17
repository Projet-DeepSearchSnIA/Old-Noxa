# 📜 OLD - Version NOXA

⚠️ Cette version de **NOXA** est ancienne et n’est plus maintenue.  
👉 Merci de vous référer à la **nouvelle version de NOXA** pour les mises à jour et améliorations.

---
🔗 [Lien vers la nouvelle version de NOXA]([https://github.com/ton-org/noxa](https://github.com/Projet-DeepSearchSnIA/Noxa))

[![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2-green?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📖 Présentation

NOXA est une plateforme web permettant aux utilisateurs de déposer et partager leurs travaux d’études, mémoires et documents académiques.  
Le projet est développé en Django avec une architecture modulaire et une interface responsive.

---

## 🚀 Lancement en mode développement

### Prérequis

- Python 3.10 ou supérieur
- pip (gestionnaire de paquets Python)
- Git

### Installation des dépendances

Le projet utilise un fichier `requirements.txt` pour gérer les dépendances Python.  

Pour installer ou mettre à jour les packages nécessaires :

```bash
pip install -r requirements.txt
````

Créer un nouvel environnement virtuel (fortement recommandé) :

```bash
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
pip install -r requirements.txt
```

### Lancement du serveur en mode développement

1. Cloner le dépôt :

```bash
git clone https://github.com/Projet-DeepSearchSnIA/Noxa
cd noxa
```

2. Se positionner sur la branche souhaitée 

3. Lancer les migrations :

```bash
python manage.py migrate
```

4. Créer un super-utilisateur (admin) :

```bash
python manage.py createsuperuser
```

5. Lancer le serveur de développement :

```bash
python manage.py runserver
```

Ouvrir ensuite dans le navigateur : `http://localhost:8000`

---

## 🌿 Gestion des branches

* **main** : branche stable contenant la version prête à être déployée en production
* **dev** : branche de développement principale où les nouvelles fonctionnalités sont intégrées
* **feat/**\* : branches de fonctionnalités spécifiques, créées à partir de `dev` et fusionnées dans `dev` une fois terminées
* **bugfix/**\* : branches pour corrections de bugs, à fusionner dans `dev` et parfois `main` selon la criticité

**Workflow recommandé :**

* Pour travailler sur une fonctionnalité, créer une branche `feat/nom-fonctionnalité` à partir de `dev`
* Après tests, faire une Pull Request vers `dev`
* Une fois la version stable, fusionner `dev` dans `main`

---

## 📁 Structure du projet

* `noxa/` : code Django
* `templates/` : fichiers HTML
* `static/` : fichiers CSS, JS, images
* `requirements.txt` : dépendances Python
* `README.md` : description du projet

---

## 🤝 Contribution

Les contributions sont les bienvenues !
Merci de respecter le workflow Git et de documenter les changements dans les Pull Requests.

---

## 📞 Contact

Pour toute question ou bug, ouvrir une issue sur GitHub ou contacter l’équipe de développement.

---

*Développé avec ❤️ par l’équipe NOXA*




