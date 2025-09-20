# BlindTest-auto

Cet outil automatise la création d'un blind test vidéo ou audio à partir de contenus YouTube.

## Prérequis

- Python 3.10 ou supérieur
- [ffmpeg](https://ffmpeg.org/) disponible dans le `PATH`
- Bibliothèques Python : `requests`, `moviepy`, `pytube` (ou `youtube_dl`) et `pytest` pour les tests

Installez-les via :

```bash
pip install -r requirements.txt
```

> **Remarque** : seuls `requests` et `pytest` sont nécessaires pour exécuter les tests unitaires. `moviepy` et les téléchargeurs ne sont requis que pour la génération réelle des médias.

## Variables d'environnement

Définissez votre clé API YouTube Data v3 :

```bash
export YOUTUBE_API_KEY="votre_clef_api"
```

## Utilisation

```bash
python -m blindtest.main "recherche youtube"
```

Options principales :

- `--max-results` : nombre de vidéos à récupérer (défaut : 5)
- `--clip-duration` : durée de chaque extrait en secondes (défaut : 10)
- `--output` : fichier de sortie (défaut : `blindtest.mp4`)
- `--audio-only` : génère un blind test audio (`.mp3`)
- `--silence-duration` : durée des transitions silencieuses entre clips (défaut : 1 seconde)
- `--no-random` : conserve l'ordre renvoyé par l'API YouTube

Le script télécharge les vidéos dans un dossier temporaire, génère des extraits, assemble le blind test final puis nettoie les fichiers intermédiaires.

## Tests

Lancez la suite de tests avec :

```bash
pytest
```

Les tests simulant l'API et `moviepy` s'assurent que la sélection de clips et l'ordre de concaténation sont corrects sans nécessiter de ressources multimédias réelles.
