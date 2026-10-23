# Prométhé

Prométhé crée des archives documentaires autonomes à partir de vidéos YouTube. Après téléchargement et transcription GPU, la correction contextuelle, l'index descriptif, la synthèse approfondie et le contrôle qualité sont obligatoires. Une archive n'est complète qu'après validation de toutes ces étapes.

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

# Toutes les vidéos d'une playlist, avec reprise indépendante par vidéo
promethe playlist "URL_PLAYLIST"

# État d'une archive ou de toutes les archives
promethe verifier ID_YOUTUBE
promethe verifier

# Préparer/régénérer l'index sans téléchargement ni transcription
promethe regenerer-index ID_YOUTUBE

# Après traitement du prompt par une IA réellement accessible
promethe regenerer-index ID_YOUTUBE --importer reponse_index.json
```

La commande `playlist` accepte aussi une URL YouTube de type `watch?v=VIDEO&list=PLAYLIST` :
Prométhé en extrait automatiquement l'identifiant de playlist.

### Repli automatique lorsque YouTube bloque le téléchargement

Les commandes `traiter`, `reprendre`, `lot` et `playlist` essaient d'abord l'accès normal. Si YouTube
renvoie son contrôle anti-robot ou masque les formats, Prométhé recommence automatiquement avec
les cookies de la session Firefox locale et le client `web_safari`. Les cookies restent dans le profil
Firefox : ils ne sont ni copiés dans le projet ni affichés.

Au premier repli seulement, si Deno n'est pas déjà disponible, sa distribution Windows officielle est
téléchargée dans `.runtime/deno/` et contrôlée par SHA-256. Ce dossier persistant est ignoré par Git,
ce qui évite de réinstaller le moteur JavaScript lors des vidéos suivantes. Il est possible de fournir un
autre exécutable avec `--runtime-js CHEMIN` ou de désactiver ce repli avec `--sans-repli-firefox`.

Lors d'une reprise avec une URL YouTube standard, Prométhé retrouve d'abord l'identifiant dans les
archives locales. Si `metadata.json` existe, il ne sollicite plus YouTube pour refaire cette inspection.

Après correction, la synthèse documentaire est produite avant l'index et se génère ou se remplace indépendamment selon le même principe :

```powershell
promethe exporter-synthese ID_YOUTUBE
promethe regenerer-synthese ID_YOUTUBE
promethe regenerer-synthese ID_YOUTUBE --importer reponse_synthese.md
```

Ces commandes utilisent `requete_synthese.txt` et valident une réponse Markdown structurée avant d'écrire `synthese_video.md`. Une archive antérieure reste lisible ; son état reçoit simplement une étape `synthesis` en attente lors du prochain chargement.

La correction contextuelle est une étape distincte. Une copie brute ne peut pas être déclarée corrigée :

```powershell
promethe exporter-correction ID_YOUTUBE
promethe corriger-transcription ID_YOUTUBE --importer transcription_corrigee.txt
```

L'import vérifie le nombre, l'ordre et la valeur de tous les horodatages avant de remplacer atomiquement le fichier de référence.

## Contrôle qualité obligatoire

Après une synthèse terminée, `traiter` et `reprendre` préparent une relecture IA. Tant que sa réponse n'a pas été importée et validée, l'archive reste incomplète.

La relecture peut être réalisée dans une autre session sans téléchargement ni transcription :

```powershell
promethe exporter-controle ID_YOUTUBE
promethe relire-synthese ID_YOUTUBE
promethe relire-synthese ID_YOUTUBE --importer reponse_controle.json
```

Les deux premières commandes écrivent `requete_controle_qualite.txt`. La réponse attendue est un JSON conforme au schéma indiqué dans cette requête. Après validation, Prométhé écrit `rapport_controle_qualite.md` et remplace atomiquement la synthèse seulement si elle a changé. Git assure l'historique : aucune copie documentaire concurrente n'est créée. Le contrôle compare uniquement les sources archivées et n'effectue aucun fact-checking externe.

La commande de régénération sans `--importer` écrit `requete_indexation.txt`. Fournir ce texte à Cursor Agent ou à un modèle autorisé, enregistrer sa réponse JSON seule, puis l'importer. Le programme contrôle le schéma, la version et l'identifiant avant de remplacer `index_video.json`.

## Archive produite

Le nouveau document dérivé attendu est `synthese_video.md`, aux côtés de l'index et des transcriptions. Son absence dans une ancienne archive n'empêche pas la lecture des autres documents, mais la vérification la signale comme incomplète.

`archives/Nom_de_chaine/Année/Date_ID_YouTube/` contient les sources et un seul fichier de référence pour chaque étape documentaire. Tant qu'un agent IA n'a pas répondu, le document correspondant est absent ou provisoire et l'état indique `waiting_manual`. Une expression incertaine est signalée au lieu d'être inventée.

Les écritures JSON critiques sont atomiques. Les étapes achevées, l'audio existant et l'identifiant YouTube empêchent téléchargements et calculs répétés. Les transcriptions restent la source permanente ; l'index est remplaçable.

## Organisation des archives V1

Les documents définitifs restent à la racine de chaque archive : métadonnées, audio, segments, transcriptions, index, synthèse, état et rapport qualité. Les artefacts intermédiaires sont rangés sous `travail/` et ne constituent jamais des références. Les remplacements sont atomiques et l'historique relève de Git, pas de copies parallèles dans les archives.

Les exports sans `--sortie` utilisent automatiquement `travail/requetes`. Pour une réponse JSON contenant `@file:nom.md`, le JSON et le fichier Markdown référencé doivent impérativement se trouver dans le même dossier, normalement `travail/reponses`. Une ancienne archive reste lisible et sa reprise crée les sous-dossiers manquants sans retélécharger ni retranscrire les étapes déjà achevées.

Une archive existante peut être rangée explicitement. La commande copie chaque fichier, contrôle son contenu par SHA-256, puis retire seulement l'ancien chemin validé :

```powershell
promethe migrer-archive ID_YOUTUBE
```

## Tests sans vidéo ni réseau

```powershell
python -m unittest discover -s tests -v
```

Ils couvrent le chemin d'archive, les horodatages, la vérification des fichiers, les imports validés, l'expansion des playlists et la reprise après interruption sans doublon.
