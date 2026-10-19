# Prométhé

Prométhé crée des archives documentaires autonomes à partir de vidéos YouTube. La V1 télécharge l'audio, transcrit en français sur GPU NVIDIA, conserve les segments horodatés et prépare une requête d'indexation. Elle ne fabrique jamais d'index si aucun modèle d'IA n'est configuré.

## Choix et environnement constaté

- GPU : NVIDIA GeForce RTX 3060 Laptop, 6 Go, pilote 555.97, capacité CUDA 8.6.
- Python visible : 3.14.6, mais sans PyTorch, Whisper, faster-whisper ni yt-dlp. Cette version est volontairement exclue du projet car les roues de calcul nécessaires peuvent ne pas la prendre en charge.
- FFmpeg/FFprobe 4.4.4 sont fournis par Krita dans `C:\Program Files\Krita (x64)\bin`, mais ne sont pas dans le `PATH`. Prométhé détecte et réutilise automatiquement cette installation.
- Aucun environnement virtuel Python réutilisable et aucun serveur de modèle local détecté.
- L'abonnement Cursor n'est pas une clé API utilisable par un script. Sans API payante (non autorisée) ni modèle local, l'indexation est donc un échange de fichiers explicite : export du prompt, traitement dans Cursor/une IA autorisée, puis import du JSON validé.

Le pipeline utilise `faster-whisper`/CTranslate2 en CUDA `float16`. Si CUDA n'est pas disponible dans cet environnement, il s'arrête avec une erreur : aucun passage silencieux sur CPU.

Sous Windows, les bibliothèques NVIDIA restent isolées dans `.venv` : cuBLAS 12.5.3.2, cuDNN 9.3.0.75 et NVRTC 12.5.82. Prométhé ajoute leurs dossiers `bin` à la recherche des DLL et au `PATH` du seul processus Python en cours. Le registre, le `PATH` utilisateur et le `PATH` système ne sont pas modifiés. Cette branche CUDA 12.5 correspond au pilote 555.97 installé.

## Installation à effectuer avant le premier essai

Installer ou sélectionner Python 3.12, puis créer un environnement isolé. Ces commandes installent uniquement les deux dépendances d'exécution nécessaires ; CTranslate2 apporte le moteur GPU. Le FFmpeg déjà livré avec Krita est réutilisé et ne doit pas être réinstallé.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .
python -m pip install -r requirements.txt
```

Sur la machine préparée, Python 3.12.10 est installé côte à côte avec Python 3.14 et l'environnement `.venv` contient déjà ces dépendances.

## Utilisation

```powershell
# Une vidéo (reprend automatiquement les étapes achevées)
promethe traiter "URL_YOUTUBE"

# Reprise explicite (même comportement idempotent)
promethe reprendre "URL_YOUTUBE"

# Plusieurs URL, une par ligne (# autorise les commentaires)
promethe lot urls.txt

# État d'une archive ou de toutes les archives
promethe verifier ID_YOUTUBE
promethe verifier

# Préparer/régénérer l'index sans téléchargement ni transcription
promethe regenerer-index ID_YOUTUBE

# Après traitement du prompt par une IA réellement accessible
promethe regenerer-index ID_YOUTUBE --importer reponse_index.json
```

La synthèse documentaire se génère ou se remplace indépendamment selon le même principe :

```powershell
promethe exporter-synthese ID_YOUTUBE
promethe regenerer-synthese ID_YOUTUBE
promethe regenerer-synthese ID_YOUTUBE --importer reponse_synthese.md
```

Ces commandes utilisent `requete_synthese.txt` et valident une réponse Markdown structurée avant d'écrire `synthese_video.md`. Une archive antérieure reste lisible ; son état reçoit simplement une étape `synthesis` en attente lors du prochain chargement.

## Contrôle qualité facultatif

Après une synthèse terminée, `traiter` et `reprendre` proposent une relecture IA. Le choix `Oui` prépare la requête, `Plus tard` laisse l'étape en attente et `Non` la marque comme refusée. La commande `lot` ne pose jamais cette question et conserve simplement l'état facultatif `pending`.

La relecture peut être réalisée dans une autre session sans téléchargement ni transcription :

```powershell
promethe exporter-controle ID_YOUTUBE
promethe relire-synthese ID_YOUTUBE
promethe relire-synthese ID_YOUTUBE --importer reponse_controle.json
```

Les deux premières commandes écrivent `requete_controle_qualite.txt`. La réponse attendue est un JSON conforme au schéma indiqué dans cette requête. Après validation, Prométhé écrit `rapport_controle_qualite.md`, remplace la synthèse seulement si elle a changé et conserve sa version précédente sous `synthese_video_avant_relecture.md` (puis avec un suffixe numérique pour les relectures suivantes). Le contrôle compare uniquement les sources archivées et n'effectue aucun fact-checking externe.

La commande de régénération sans `--importer` écrit `requete_indexation.txt`. Fournir ce texte à Cursor Agent ou à un modèle autorisé, enregistrer sa réponse JSON seule, puis l'importer. Le programme contrôle le schéma, la version et l'identifiant avant de remplacer `index_video.json`.

## Archive produite

Le nouveau document dérivé attendu est `synthese_video.md`, aux côtés de l'index et des transcriptions. Son absence dans une ancienne archive n'empêche pas la lecture des autres documents, mais la vérification la signale comme incomplète.

`archives/Nom_de_chaine/Année/Date_ID_YouTube/` contient `metadata.json`, `segments.json`, `transcription_brute.txt`, `transcription_corrigee.txt`, `index_video.json` et `etat_pipeline.json`. Tant que l'IA n'a pas répondu, `index_video.json` est légitimement absent et l'état indique `waiting_manual`. La correction est initialement une copie intégrale et horodatée, marquée `copie_identique_non_corrigee` ; aucune correction incertaine n'est inventée.

Les écritures JSON critiques sont atomiques. Les étapes achevées, l'audio existant et l'identifiant YouTube empêchent téléchargements et calculs répétés. Les transcriptions restent la source permanente ; l'index est remplaçable.

## Organisation des archives V1

Les documents définitifs restent à la racine de chaque archive : métadonnées, audio, segments, transcriptions, index, synthèse, état du pipeline et rapport de contrôle qualité. Les artefacts intermédiaires sont rangés sous `travail/requetes`, `travail/reponses` et `travail/candidates`. Les versions remplacées sont conservées sous `historique/anciennes_versions`.

Les exports sans `--sortie` utilisent automatiquement `travail/requetes`. Pour une réponse JSON contenant `@file:nom.md`, le JSON et le fichier Markdown référencé doivent impérativement se trouver dans le même dossier, normalement `travail/reponses`. Une ancienne archive reste lisible et sa reprise crée les sous-dossiers manquants sans retélécharger ni retranscrire les étapes déjà achevées.

Une archive existante peut être rangée explicitement. La commande copie chaque fichier, contrôle son contenu par SHA-256, puis retire seulement l'ancien chemin validé :

```powershell
promethe migrer-archive ID_YOUTUBE
```

## Tests sans vidéo ni réseau

```powershell
python -m unittest discover -s tests -v
```

Ils couvrent le chemin d'archive, les horodatages, la vérification des fichiers, l'export/import validé de l'index et la reprise sans doublon.
