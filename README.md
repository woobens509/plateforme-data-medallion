# Projet 3 — Plateforme de données medallion : documentation complète

Ce document explique, étape par étape, la construction complète d'une plateforme de données qui ingère deux jeux de données hétérogènes, les organise selon une architecture en couches successives (bronze, silver, gold), les transforme et les teste automatiquement, et met en place une intégration continue qui valide ce travail à chaque modification du code. Il est rédigé pour être compréhensible sans connaissance préalable du domaine, et pour permettre à quiconque de reproduire l'ensemble du projet à l'identique.

---

## 1. Vue d'ensemble : à quoi sert ce projet et comment il fonctionne

Ce projet répond à une situation très courante en entreprise : des données utiles à l'analyse proviennent rarement d'une seule source uniforme. Elles arrivent au contraire sous des formes variées, qu'il faut rassembler, nettoyer et organiser avant de pouvoir en tirer des indicateurs fiables.

Pour illustrer ce problème de façon réaliste, deux jeux de données complètement différents ont été utilisés :

- Un jeu de données représentant des commandes d'un site de commerce en ligne brésilien, réparti sur plusieurs fichiers liés entre eux (clients, commandes, articles commandés, produits, vendeurs).
- Un jeu de données représentant les ventes d'une entreprise de vente au détail américaine, regroupé dans un seul fichier.

L'objectif est de faire cohabiter ces deux sources dans une seule plateforme analytique cohérente, capable de répondre à des questions comme « quel est le chiffre d'affaires total, toutes sources confondues ? », sans que l'utilisateur final n'ait à se soucier du fait que les données proviennent, en coulisses, de deux systèmes totalement différents.

Pour organiser ce travail, une architecture dite medallion a été mise en place, qui décompose le traitement des données en trois couches successives :

- **La couche bronze** contient les données brutes, telles qu'elles ont été reçues, sans aucune transformation. Elle sert de copie de référence immuable, à laquelle on peut toujours revenir si une erreur est découverte plus loin dans le traitement.
- **La couche silver** contient des données nettoyées et correctement typées (par exemple, une date stockée sous forme de texte brut dans la couche bronze devient une véritable date dans la couche silver), mais sans encore de logique métier ajoutée.
- **La couche gold** contient des données organisées spécifiquement pour l'analyse, avec des tables pensées pour répondre à des questions métier précises, en combinant si nécessaire plusieurs sources.

Les outils suivants ont été utilisés :

- **MinIO** : un logiciel de stockage de fichiers qui reproduit le fonctionnement du service Amazon S3, largement utilisé dans l'industrie. Il joue ici le rôle de la couche bronze, en stockant les fichiers bruts.
- **PostgreSQL** : une base de données relationnelle, utilisée ici pour héberger les couches silver et gold, sous forme de tables et de vues interrogeables avec le langage SQL.
- **dbt (data build tool)** : l'outil utilisé pour écrire, organiser et tester les transformations qui font passer les données de la couche bronze vers les couches silver puis gold.
- **Python** : utilisé pour écrire les scripts qui déplacent les données d'un endroit à l'autre (du disque vers MinIO, puis de MinIO vers PostgreSQL).
- **GitHub Actions** : un service qui exécute automatiquement une série de vérifications à chaque modification du code envoyée sur une plateforme de partage de code, afin de détecter rapidement si quelque chose a été cassé.
- **Docker** : comme pour le reste de l'infrastructure, chaque outil (MinIO, PostgreSQL, un outil de visualisation) tourne dans un conteneur isolé.

Un seul dossier principal, `C:\data-projects\projet3-plateforme\`, rassemble l'ensemble du code et de la configuration de ce projet.

---

## 2. Étape 1 — Mise en place de l'infrastructure Docker

### Objectif de cette étape

Faire fonctionner les trois briques d'infrastructure : le stockage de fichiers, la base de données, et l'outil de visualisation.

### Contenu détaillé du fichier `docker-compose.yml`

Ce fichier décrit trois services :

**Le service MinIO** utilise une image publiée sur un registre de conteneurs alternatif, puisque l'éditeur de MinIO a cessé de publier gratuitement ses images sur le registre le plus courant. Le service expose deux ports : l'un pour l'interface de programmation (utilisée par les scripts Python), l'autre pour la console web d'administration.

**Le service PostgreSQL** utilise l'image officielle de PostgreSQL version 16, avec une base de données, un utilisateur et un mot de passe dédiés à ce projet, exposée sur un port spécifique, choisi pour ne pas entrer en conflit avec d'autres bases de données PostgreSQL pouvant tourner sur la même machine.

**Le service Metabase** utilise l'image officielle de cet outil de visualisation, destiné à terme à afficher un tableau de bord s'appuyant sur les données de la couche gold.

---

## 3. Étape 2 — Création de l'environnement Python

### Objectif de cette étape

Mettre en place un environnement isolé contenant toutes les bibliothèques Python nécessaires à ce projet.

### Ce qui a été fait

Un environnement virtuel a été créé avec Python 3.11, puis les bibliothèques suivantes ont été installées :

- **`pandas`** : pour lire et manipuler des fichiers tabulaires (CSV) sous forme de tableaux de données.
- **`boto3`** : la bibliothèque officielle utilisée pour interagir avec un stockage de type S3, donc également compatible avec MinIO.
- **`psycopg2-binary`** : pour permettre à Python de se connecter à une base de données PostgreSQL.
- **`sqlalchemy`** : une bibliothèque qui simplifie l'écriture de données directement depuis un tableau pandas vers une base de données, sans avoir à écrire soi-même les requêtes d'insertion.
- **`python-dotenv`** : pour charger des informations sensibles (comme des identifiants de connexion) depuis un fichier séparé, plutôt que de les écrire directement dans le code.

---

## 4. Étape 3 — Acquisition des jeux de données

### Objectif de cette étape

Se procurer les deux jeux de données qui serviront de matière première à l'ensemble du projet.

### Ce qui a été fait

Le premier jeu de données, représentant des commandes de commerce en ligne, a été téléchargé depuis une plateforme communautaire de jeux de données (nécessitant la création d'un compte gratuit), sous la forme d'une archive contenant neuf fichiers CSV distincts : les informations clients, les commandes elles-mêmes, les articles de chaque commande, les paiements, les avis laissés par les clients, les produits, les vendeurs, des données de géolocalisation, et une table de correspondance des catégories de produits.

Le second jeu de données, représentant des ventes au détail, a été téléchargé directement par lien, sans nécessiter de compte, sous la forme d'un unique fichier CSV regroupant près de dix mille lignes de transactions.

Les deux jeux de données ont été placés dans des sous-dossiers distincts, à l'intérieur d'un dossier `data\`, volontairement exclu du suivi de version (voir la section sur le fichier `.gitignore` plus loin), puisqu'il s'agit de fichiers volumineux destinés à être retéléchargés par quiconque souhaite reproduire le projet, plutôt que d'être conservés dans l'historique du code.

---

## 5. Étape 4 — Ingestion vers la couche bronze

### Objectif de cette étape

Déposer les fichiers bruts téléchargés dans le système de stockage MinIO, sans aucune transformation, afin de matérialiser la couche bronze de l'architecture.

### Préparation : création des espaces de stockage et des identifiants

Trois espaces de stockage, appelés buckets dans la terminologie S3, ont été créés depuis l'interface web de MinIO : un pour chaque couche de l'architecture (bronze, silver, gold), même si seule la couche bronze est effectivement utilisée comme espace de stockage de fichiers dans ce projet, les couches silver et gold étant matérialisées directement dans la base de données plutôt que sous forme de fichiers.

Une paire de clés d'accès a ensuite été générée depuis l'interface de MinIO, destinée à permettre à un programme Python de s'authentifier sans utiliser le compte administrateur principal.

### Contenu détaillé du fichier `ingest_to_bronze.py`

Ce script, placé dans un dossier `ingestion\`, se connecte à MinIO à l'aide de la bibliothèque `boto3`, puis parcourt les fichiers CSV présents localement dans les dossiers correspondant à chaque source de données, et les envoie un par un vers le bucket bronze, en les organisant dans des sous-dossiers logiques (un pour chaque source). Chaque envoi réussi est confirmé par un message affiché dans le terminal.

### Incident rencontré et diagnostic

Lors de la première exécution de ce script, chaque tentative d'envoi de fichier a échoué avec un message d'erreur indiquant que la clé d'accès fournie n'existait pas dans les registres de MinIO, alors que cette même clé avait pourtant été correctement générée et correctement reprise dans la configuration du script. Une première hypothèse, liée à un paramètre technique de la bibliothèque boto3 concernant la manière de construire les adresses de requête, a été testée sans succès. Le diagnostic final a révélé que la cause réelle était une perte de cette clé d'accès secondaire, survenue à la suite d'un redémarrage du conteneur MinIO effectué entre sa création et la première utilisation du script, sans que les données déjà stockées dans les buckets n'aient été affectées par cet incident.

### Solution retenue

En remplacement de la clé d'accès perdue, les identifiants du compte administrateur principal de MinIO (définis directement dans le fichier `docker-compose.yml`) ont été utilisés à la place, ce qui a immédiatement permis au script de fonctionner correctement. Cette solution reste adaptée à un contexte de développement local, mais ne constituerait pas une bonne pratique dans un environnement de production, où l'usage d'un compte disposant de tous les droits administrateur pour une simple tâche d'ingestion de fichiers représenterait un risque de sécurité inutile.

---

## 6. Étape 5 — Chargement de la couche bronze vers PostgreSQL

### Objectif de cette étape

Rendre les données de la couche bronze exploitables par un outil de transformation SQL, en les chargeant depuis MinIO vers des tables PostgreSQL.

### Contenu détaillé du fichier `load_bronze_to_postgres.py`

Ce script se connecte à la fois à MinIO (pour lire les fichiers) et à PostgreSQL (pour y écrire les données). Pour chaque fichier présent dans un sous-dossier donné du bucket bronze, il lit son contenu directement en mémoire (sans l'enregistrer de nouveau sur le disque), le transforme en tableau à l'aide de pandas, puis écrit ce tableau dans une nouvelle table PostgreSQL, nommée automatiquement à partir du nom du fichier d'origine, préfixé par `raw_` pour signaler clairement qu'il s'agit de données non transformées.

### Problème rencontré

Le chargement des neuf fichiers du premier jeu de données s'est déroulé sans incident. Le fichier du second jeu de données a en revanche provoqué une erreur de décodage de caractères, le programme étant incapable d'interpréter certains octets du fichier selon l'encodage de caractères attendu par défaut (UTF-8). La cause de cette erreur est que ce fichier, comme beaucoup de fichiers tabulaires produits à l'origine par des logiciels de bureautique nord-américains, utilise un encodage de caractères plus ancien, communément appelé Latin-1, qui diffère de l'encodage universel devenu la norme actuelle. La correction a consisté à préciser explicitement cet encodage lors de la lecture du fichier, ce qui a résolu le problème sans affecter la lecture des autres fichiers, par ailleurs compatibles avec les deux encodages.

---

## 7. Étape 6 — Initialisation du projet de transformation

### Objectif de cette étape

Mettre en place l'outil de transformation qui va faire passer les données de la couche bronze (les tables préfixées `raw_`) vers les couches silver puis gold.

### Ce qui a été fait

Un projet a été initialisé avec l'outil de transformation, en renseignant les informations de connexion à la base de données PostgreSQL de ce projet. La connexion a été validée avec succès dès la première tentative. Le modèle d'exemple généré automatiquement par l'outil a ensuite été supprimé, afin de ne conserver que du code directement pertinent pour ce projet.

---

## 8. Étape 7 — Construction de la couche silver

### Objectif de cette étape

Nettoyer et typer correctement les données brutes, en vue de leur utilisation ultérieure.

### Contenu détaillé des modèles créés

Avant d'écrire les modèles, la structure exacte des tables brutes a été consultée directement dans PostgreSQL, afin de connaître avec certitude le nom et le type de chaque colonne.

Un fichier de déclaration des sources a d'abord été créé, listant les quatre tables brutes concernées par cette étape (les commandes, les clients, les articles de commande, et les ventes du second jeu de données), afin que l'outil de transformation sache où aller chercher les données d'origine.

Quatre modèles de transformation ont ensuite été écrits :

- Un modèle nettoyant les commandes, qui convertit les différentes colonnes de dates, initialement stockées sous forme de texte brut, en véritables valeurs de date et d'heure exploitables.
- Un modèle nettoyant les informations clients, qui sélectionne les colonnes pertinentes sans modification particulière, les données d'origine étant déjà dans un format correct.
- Un modèle nettoyant les articles de commande, incluant le prix et les frais de port de chaque article, avec la même conversion de date que pour les commandes.
- Un modèle nettoyant les ventes du second jeu de données, qui a nécessité une attention particulière : les noms de colonnes d'origine contenaient des espaces et des majuscules (par exemple, une colonne nommée avec deux mots séparés par un espace), ce qui oblige à les entourer de guillemets doubles dans la requête SQL pour que la base de données les interprète correctement, sans quoi elle les chercherait automatiquement en minuscules et échouerait à les trouver. Ce modèle en a profité pour renommer toutes les colonnes selon une convention plus simple, sans espace ni majuscule.

### Tests de qualité appliqués

Des règles de vérification ont été associées à ces quatre modèles : l'unicité et la non-vacuité des identifiants de commande et de client, ainsi que la non-vacuité de quelques colonnes jugées essentielles comme le prix ou le montant des ventes. L'ensemble de ces vérifications s'est exécuté avec succès.

---

## 9. Étape 8 — Construction de la couche gold

### Objectif de cette étape

Construire une structure de données pensée pour l'analyse, en particulier une modélisation dite en étoile : une table centrale contenant les faits à mesurer (ici, les ventes), entourée de tables apportant le contexte nécessaire à leur interprétation (qui a acheté, quel produit, à quelle date).

### Contenu détaillé des modèles créés

Trois tables de dimension ont été construites :

- Une dimension temporelle, qui recense l'ensemble des dates distinctes observées dans les deux sources de ventes, enrichie de colonnes calculées comme l'année, le mois, le jour, et le jour de la semaine correspondant, utiles pour des regroupements ultérieurs dans un outil de visualisation.
- Une dimension produit, qui rassemble les informations disponibles sur les produits vendus dans les deux sources, en indiquant pour chaque ligne de quelle source elle provient, puisque le niveau de détail disponible diffère entre les deux (le second jeu de données propose une catégorie et un nom de produit, ce qui n'est pas directement disponible de la même manière dans le premier).
- Une dimension client, construite selon le même principe, rassemblant les identifiants clients des deux sources avec leur ville et leur région ou état, lorsque disponibles.

Une table de faits a ensuite été construite, rassemblant chaque transaction de vente des deux sources dans une structure commune : un identifiant de commande, un identifiant de produit, un identifiant de client, une date de vente, un montant, une quantité, et une colonne indiquant explicitement la source d'origine de chaque ligne, ce qui permet de toujours pouvoir distinguer, si besoin, les ventes issues de l'une ou l'autre source, tout en les analysant ensemble lorsque ce n'est pas nécessaire.

### Vérification du résultat

Une requête de vérification, agrégeant le nombre de lignes et le chiffre d'affaires total par source dans cette table de faits, a permis de confirmer que les deux sources étaient correctement représentées, avec des volumes cohérents par rapport aux fichiers d'origine.

### Tests de qualité appliqués et problème rencontré

Des règles de vérification ont été ajoutées sur cette couche : la non-vacuité des identifiants et montants dans la table de faits, ainsi qu'une règle plus spécifique vérifiant que la colonne indiquant la source ne contient jamais qu'une des deux valeurs attendues, aucune autre. Lors de la première exécution de cette dernière règle, un avertissement de dépréciation est apparu, signalant qu'une ancienne manière d'écrire les paramètres de ce type de test allait cesser d'être prise en charge dans une future version de l'outil. La correction a consisté à adapter l'écriture de cette règle selon la nouvelle syntaxe recommandée, ce qui a fait disparaître l'avertissement sans changer le comportement du test lui-même.

---

## 10. Étape 9 — Mise en place de l'intégration continue

### Objectif de cette étape

Mettre en place un mécanisme de vérification automatique, qui s'exécute à chaque modification du code envoyée sur une plateforme de partage de code, afin de détecter rapidement si une modification a cassé quelque chose, sans attendre qu'un humain ne le remarque manuellement.

### Le problème à résoudre avant de commencer

Le service d'intégration continue ne peut évidemment pas accéder à la base de données PostgreSQL installée localement sur l'ordinateur de développement. Il faut donc que chaque exécution automatique dispose de sa propre base de données temporaire, et d'un petit échantillon de données représentatif plutôt que les fichiers complets, inutilement volumineux et lents à traiter pour un simple test de vérification.

### Création des données d'exemple

Des fichiers d'exemple, appelés seeds dans la terminologie de l'outil de transformation, ont été créés pour chacune des quatre tables brutes utilisées par les modèles silver. Chaque fichier contient seulement quelques lignes, suffisantes pour que les transformations et les tests puissent s'exécuter normalement, mais sans commune mesure avec le volume réel des données en production. Ces fichiers portent exactement les mêmes noms que les tables brutes réelles, condition nécessaire pour que l'outil de transformation puisse les charger comme s'il s'agissait des véritables données brutes.

Une mise en garde importante accompagne ces fichiers : la commande qui les charge dans une base de données ne doit jamais être exécutée sur la base de données locale du projet, sous peine de remplacer les véritables tables, contenant des centaines de milliers de lignes, par ces quelques lignes d'exemple. Cette commande n'a vocation à s'exécuter que dans l'environnement temporaire et jetable créé automatiquement par le service d'intégration continue.

### Contenu détaillé du fichier de configuration de l'intégration continue

Un fichier de configuration, placé dans un dossier caché à la racine du projet, décrit deux vérifications distinctes, exécutées automatiquement :

La première vérification contrôle le style d'écriture des scripts Python d'ingestion, à l'aide d'un outil dédié à ce type de contrôle, qui signale par exemple un espacement incorrect entre les fonctions ou l'absence d'une ligne vide à la fin d'un fichier.

La seconde vérification démarre une base de données PostgreSQL temporaire et vide, génère un fichier de configuration de connexion adapté à cette base temporaire, charge les fichiers d'exemple dans cette base pour simuler la présence des données brutes, puis exécute l'ensemble des modèles de transformation ainsi que tous leurs tests de qualité associés, en une seule commande combinée. Si un seul de ces modèles ou un seul de ces tests échoue, l'ensemble de la vérification est considéré comme échoué, ce qui serait visible immédiatement sur la plateforme de partage de code.

### Problèmes rencontrés et corrigés avant la première exécution réelle

Avant même d'envoyer ce code pour la première fois, la vérification de style a été testée localement, révélant plusieurs avertissements mineurs mais systématiques dans les deux scripts d'ingestion : un nombre insuffisant de lignes vides entre certaines fonctions, et l'absence d'un retour à la ligne final après la dernière ligne de code de chaque fichier. Une première tentative de correction, consistant à ajouter directement un retour à la ligne supplémentaire, a corrigé le premier problème mais introduit à sa place une ligne vide excédentaire en fin de fichier, également signalée comme une erreur de style. La correction définitive a consisté à retirer précisément tout espace ou retour à la ligne superflu en fin de fichier, puis à n'ajouter qu'un seul retour à la ligne final, exactement comme l'exige la convention de style attendue.

Un dernier écueil technique, sans lien avec le code du projet lui-même, est à noter : une tentative de corriger ces fichiers à l'aide d'une commande système bas niveau a échoué, cette commande ne tenant pas compte du dossier de travail courant dans le terminal et cherchant les fichiers depuis le dossier personnel de l'utilisateur plutôt que depuis le dossier du projet. La correction a consisté à fournir explicitement le chemin complet des fichiers concernés plutôt qu'un chemin relatif.

---

## 11. Architecture finale détaillée du dossier

```
projet3-plateforme/
├── docker-compose.yml              Définit les conteneurs MinIO, PostgreSQL et l'outil de visualisation
├── .env                             Identifiants de connexion à MinIO (exclu du suivi de version)
├── .gitignore                       Exclusions du suivi de version
├── venv/                            Environnement Python isolé (Python 3.11)
├── data/
│   ├── olist/                       Les neuf fichiers CSV bruts du premier jeu de données
│   └── superstore/                  Le fichier CSV brut du second jeu de données
├── ingestion/
│   ├── ingest_to_bronze.py          Envoie les fichiers bruts locaux vers le stockage MinIO (couche bronze)
│   └── load_bronze_to_postgres.py   Charge les fichiers de MinIO vers des tables brutes PostgreSQL
├── .github/
│   └── workflows/
│       └── ci.yml                   Définit les vérifications automatiques exécutées à chaque modification du code
└── projet3_plateforme/              Le projet de transformation
    ├── dbt_project.yml              Fichier de configuration principal
    ├── seeds/                       Petits fichiers d'exemple utilisés uniquement par l'intégration continue
    ├── models/
    │   ├── staging/                 La couche silver : modèles de nettoyage et fichiers de tests associés
    │   └── marts/                   La couche gold : dimensions, table de faits, et fichiers de tests associés
    ├── macros/, analyses/, snapshots/, tests/   Dossiers standards, non approfondis dans ce projet
    ├── target/                      Fichiers générés automatiquement à chaque exécution
    └── logs/                        Historique des exécutions
```

---

## 12. Récapitulatif des problèmes rencontrés

| Étape | Problème | Cause | Solution |
|---|---|---|---|
| Ingestion vers la couche bronze | Clé d'accès rejetée comme invalide | La clé d'accès secondaire générée avait été perdue après un redémarrage du conteneur de stockage | Utilisation des identifiants administrateur définis directement dans la configuration des conteneurs |
| Chargement vers PostgreSQL | Erreur de décodage de caractères sur un fichier | Le fichier utilisait un encodage de caractères plus ancien que celui attendu par défaut | Spécification explicite de l'encodage approprié lors de la lecture du fichier |
| Modification d'un script existant | Erreur de mélange d'indentation | Une modification partielle dans un éditeur de texte simple a mélangé espaces et tabulations | Remplacement intégral du fichier plutôt qu'une modification partielle |
| Tests de qualité sur la couche gold | Avertissement de dépréciation sur un type de test | Ancienne syntaxe de déclaration des paramètres du test, désormais dépréciée | Adaptation à la nouvelle syntaxe recommandée |
| Mise en place de l'intégration continue | Avertissements de style sur les scripts Python | Espacement insuffisant entre les fonctions et absence de retour à la ligne final | Réécriture complète des fichiers concernés avec un espacement conforme |
| Correction du retour à la ligne final | Nouvelle erreur de style après correction | Une ligne vide excédentaire a été introduite par la première tentative de correction | Suppression précise de tout caractère superflu en fin de fichier avant d'ajouter un seul retour à la ligne |

---

## 13. Résultat final

La plateforme ingère deux sources de données hétérogènes, les organise selon une architecture en trois couches successives, les nettoie et les unifie dans un modèle analytique commun, avec vingt règles de qualité vérifiées automatiquement. Une intégration continue valide désormais l'ensemble de ce travail à chaque modification du code, sur un jeu de données d'exemple indépendant des données réelles, garantissant qu'une évolution future du projet ne puisse pas casser silencieusement une transformation ou un test existant sans que cela ne soit immédiatement visible.
