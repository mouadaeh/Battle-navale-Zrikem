# Battle-navale-Zrikem

Jeu de la bataille navale en Python, avec intelligence artificielle, animations et mode multijoueur.

## Prérequis

- **Python 3.8 ou supérieur**  
  Téléchargez et installez Python depuis : https://www.python.org/downloads/

- **Pip** (généralement inclus avec Python)
- (Optionnel) **Un environnement virtuel** pour isoler les dépendances :
  ```bash
  python -m venv venv
  source venv/bin/activate  # Sous Windows : venv\Scripts\activate
  ```

## Installation des dépendances

Le projet ne semble pas inclure de fichier `requirements.txt` par défaut.  
Par défaut, pour les jeux et l'interface graphique en Python, la bibliothèque la plus probable est **pygame**.

Installez-la avec cette commande :
```bash
pip install pygame
```

Si d'autres dépendances sont nécessaires, ajoutez-les dans `requirements.txt` et installez-les avec :
```bash
pip install -r requirements.txt
```

## Lancement du jeu

Placez-vous dans le dossier `src` puis lancez le fichier principal :
```bash
cd src
python main.py
```

## Structure du projet

- `src/` : Code source principal (logique du jeu, IA, interface, etc.)
- `assets/` : Ressources graphiques et sons
- `SFX/`, `Ships/`, `models/` : Ressources supplémentaires pour le jeu
- `src/ui/` : Interface utilisateur
- `src/utils/` : Fonctions utilitaires

## Fonctionnalités

- Mode solo contre l'IA
- Mode multijoueur
- Animations et effets visuels/sonores
- Gestion avancée des états de jeu

## À faire / Personnalisation

- Ajouter ou compléter un fichier `requirements.txt` si d'autres modules sont nécessaires.
- Modifier les ressources graphiques ou sonores dans les dossiers correspondants.
- Adapter le code dans `src/` pour personnaliser les règles ou l'IA.

## Problèmes connus ou limitations

- Ce README est basé sur la structure du projet. Si des instructions spécifiques existent dans le code, merci de les ajouter ici.

## Liens utiles

- [Voir le dossier src complet sur GitHub](https://github.com/mouadaeh/Battle-navale-Zrikem/tree/main/src)
