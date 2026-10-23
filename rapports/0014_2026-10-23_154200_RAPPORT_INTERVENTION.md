# Rapport de la dernière intervention

Date de clôture : 2026-10-23 15:42:00 +09:00 (Asia/Tokyo)

## A. Demande initiale

L'utilisateur a fourni l'URL `https://youtu.be/Y2ZmDz3piEk?si=XYzN0XW3dFH7z2Ow` afin d'archiver la vidéo correspondante.

Conformément à `AGENTS.md`, la demande a été interprétée comme l'exécution du pipeline documentaire complet : métadonnées, téléchargement audio, transcription Whisper intégrale et horodatée, correction contextuelle, synthèse approfondie, index sémantique, contrôle qualité et vérification finale.

## B. État initial

- La vidéo `Y2ZmDz3piEk` était absente de la bibliothèque.
- La commande `promethe`, Faster-Whisper, le modèle `medium` et CUDA étaient disponibles.
- Le dépôt comportait déjà des changements et archives produits par les interventions antérieures. Ils ont été préservés.
- L'accès réseau nécessaire à YouTube a été autorisé. La tentative normale a fonctionné ; aucun repli Firefox n'a été nécessaire.

## C. Travail effectué

### Acquisition et transcription

La commande principale exécutée a été :

`promethe traiter "https://youtu.be/Y2ZmDz3piEk?si=XYzN0XW3dFH7z2Ow"`

Le pipeline a récupéré les métadonnées, téléchargé `audio.webm` et transcrit la vidéo avec Faster-Whisper, modèle `medium`, appareil `cuda`. L'archive a été créée dans `archives/Radio_Maudin/2026/2026-10-21_Y2ZmDz3piEk`.

### Correction contextuelle

La requête a été exportée avec `promethe exporter-correction Y2ZmDz3piEk`. Une correction conservatrice a été importée avec `promethe corriger-transcription`, en préservant strictement les segments et horodatages. Aucun changement suffisamment certain n'a été retenu ; l'état enregistre donc une correction terminée avec `changed: false`. `transcription_brute.txt` n'a jamais été modifiée.

### Synthèse documentaire

Une synthèse approfondie, structurée et horodatée a été produite dans `travail/reponses/reponse_synthese.md`, puis importée avec `promethe regenerer-synthese`.

Elle couvre le débat sur la qualification de « dommage collatéral », le cadrage d'un supposé virage idéologique, la distinction entre manifestations, émeutes et pillages, la critique de la gauche et de l'extrême gauche, le rôle de l'État, la comparaison avec les Gilets jaunes et les agriculteurs, la digression sur le 17 octobre 1961 et la rivalité FLN-MNA, ainsi que l'usage du capitalisme ou de la révolution comme explication des violences. Les prises de position sont attribuées à Radio Maudin ou aux participantes et ne sont pas transformées en faits externes établis.

### Indexation sémantique

Un index JSON au schéma 1.1 a été produit dans `travail/reponses/reponse_indexation.json`, puis importé avec `promethe regenerer-index`. Il contient résumé, thèmes, sujets secondaires, arguments, concepts, événements, personnes, organismes, lieux, mots-clés, citations, relations documentaires, variantes lexicales et six repères temporels couvrant toute la vidéo.

### Contrôle qualité

La requête a été exportée avec `promethe exporter-controle Y2ZmDz3piEk`. La synthèse a été contrôlée contre la transcription corrigée et l'index, sans fact-checking externe. Le verdict `conforme` a été importé avec `promethe relire-synthese`, qui a créé `rapport_controle_qualite.md`.

### Fichiers créés ou modifiés

L'archive contient :

- `metadata.json` ;
- `audio.webm` ;
- `segments.json` ;
- `transcription_brute.txt` ;
- `transcription_corrigee.txt` ;
- `synthese_video.md` ;
- `index_video.json` ;
- `etat_pipeline.json` ;
- `rapport_controle_qualite.md` ;
- les dossiers de travail et d'historique attendus.

Hors archive, seul `RAPPORT_DERNIERE_INTERVENTION.md` a été remplacé. Après sa finalisation, il a été copié sous `rapports/0014_2026-10-23_154200_RAPPORT_INTERVENTION.md`. Aucun fichier n'a été déplacé ou supprimé et aucun fichier de programme n'a été modifié.

## D. Résultats

- Identifiant : `Y2ZmDz3piEk`.
- Titre : `CETTE GAUCHISTE VIRE À DROITE EN DIRECT APRÈS LE 17 OCTOBRE`.
- Chaîne : `Radio Maudin`.
- Date de publication : 21 octobre 2026.
- Durée : 00:28:52, soit 1 732 secondes.
- Audio : complet, `audio.webm`, 25 946 452 octets.
- Métadonnées : complètes, 755 octets.
- Segments Whisper : complets, 135 247 octets.
- Transcription brute : complète, 51 842 octets.
- Transcription corrigée : complète, 51 842 octets, sans changement retenu.
- Synthèse : complète, 5 844 octets.
- Index : complet, schéma 1.1, 7 867 octets.
- Contrôle qualité : complet, verdict `conforme`.
- `promethe verifier Y2ZmDz3piEk` retourne `complete: true`, `audio: true`, `validated_steps: true` et confirme tous les fichiers et dossiers attendus.

## Validations réalisées

- Téléchargement YouTube terminé sans erreur.
- Transcription Whisper `medium` sur CUDA terminée.
- Correction validée structurellement par l'importeur.
- Synthèse et index importés dans les fichiers de référence.
- Index JSON validé au schéma 1.1.
- Contrôle qualité importé avec verdict `conforme`.
- Vérification finale réussie avec `promethe verifier Y2ZmDz3piEk`.
- Inventaire final des fichiers et tailles effectué.
- SHA-256 du rapport courant et de sa copie historique calculés après la copie et vérifiés strictement identiques.

## Limites restantes

- Aucun fact-checking externe n'a été effectué. Les interprétations historiques et politiques restent attribuées aux intervenants.
- La correction contextuelle n'a retenu aucun changement certain ; quelques erreurs acoustiques peuvent subsister dans les passages dialogués.
- Le « virage à droite » annoncé par le titre est traité comme le cadrage de Radio Maudin : la vidéo montre surtout une contestation de certains arguments, pas l'adhésion explicite à un programme politique complet.
