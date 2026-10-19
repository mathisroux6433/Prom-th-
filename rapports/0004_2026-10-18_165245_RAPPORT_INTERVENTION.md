# Rapport de la dernière intervention

- **Numéro :** 0004
- **Date :** 18 octobre 2026
- **Projet :** Prométhé V1
- **Objet :** inventaire d’une playlist YouTube et traitement intégral de ses trois premières vidéos non archivées

## A. Demande initiale

La demande consistait à tester Prométhé V1 avec la playlist YouTube `PLRFRwS8s4qMrKCLG2RtIBlDWwENzWODd1`. Il fallait d’abord inventorier automatiquement la playlist avec `yt-dlp`, sans média, puis identifier les vidéos déjà archivées et celles restant à traiter. Ensuite, les trois premières vidéos non archivées devaient être traitées intégralement, sans intervention utilisateur entre elles : téléchargement, transcription CUDA, correction prudente, indexation, synthèse documentaire horodatée et contrôle qualité. Les huit autres vidéos ne devaient pas être exécutées. Enfin, les trois archives devaient être vérifiées et les temps de transcription, problèmes et interventions Agent documentés.

## B. État initial

La playlist publique « 20ans de l’Euro », publiée par Trouble Fait et modifiée le 16 mai 2026 selon l’inventaire, contenait 11 vidéos. Aucun des 11 identifiants n’était présent dans les archives Prométhé. Le pipeline existant prenait déjà en charge les traitements unitaires, la reprise idempotente et les listes d’URL ; aucune modification du code ou de l’architecture n’était nécessaire.

Inventaire initial, durées fournies par `yt-dlp` :

1. `yLEmwlm6VS8` — « Une chance pour la France » — 10:04 ;
2. `2yaMBOGNjKs` — « Le fonctionnement de l’euro et de Target2 » — 14:41 dans l’inventaire, 14:40 dans les métadonnées détaillées ;
3. `Q99fEqQfuW4` — « L’origine des “fausses” dettes Target2 » — 11:59 dans l’inventaire, 11:58 dans les métadonnées détaillées ;
4. `FnU_TR_WYi4` — « The clinical death of the Euro (1/2) » — 18:53 ;
5. `CjuQQJm2LnI` — « The clinical death of the Euro (2/2) » — 19:23 ;
6. `fpdKmRdrC7M` — « L’euro va-t-il tuer l’Allemagne ? » — 32:55 ;
7. `psPOa6MFaIg` — « Italexit… » — 32:42 ;
8. `lWbsWPYyCvQ` — « Eight ways the euro ruins France » — 53:20 ;
9. `fTCuGl3pNWk` — « L’euro et la crise financière » — 2:33:34 ;
10. `kP6IxvjnBNI` — « The Return to the Franc » — 1:46:30 ;
11. `rvl8ESCGwxw` — « To save the EURO, you will be POOR! » — 19:56.

## C. Travail effectué

### 1. Inventaire sans médias

`yt-dlp --flat-playlist --dump-single-json --no-warnings` a récupéré les 11 identifiants, titres, durées et chaînes sans télécharger d’audio ni de vidéo. Une comparaison avec tous les dossiers d’archives a confirmé que les 11 vidéos étaient initialement non archivées. Les trois premières ont été sélectionnées dans l’ordre de la playlist.

### 2. Téléchargement et transcription

Chaque vidéo sélectionnée a été lancée avec `promethe reprendre URL`. Les commandes ont été exécutées séparément pour chronométrer chaque traitement et conserver une reprise indépendante. Le pipeline a téléchargé un `audio.webm`, puis transcrit avec `faster-whisper`, modèle `medium`, GPU CUDA et `float16`.

Temps mesuré de la phase de transcription, entre l’écriture finale de `audio.webm` et celle de `segments.json` :

- `yLEmwlm6VS8` : **64,125 s** ; pipeline initial complet : 70,598 s ; 123 segments ;
- `2yaMBOGNjKs` : **99,392 s** ; pipeline initial complet : 107,827 s ; 131 segments ;
- `Q99fEqQfuW4` : **86,618 s** ; pipeline initial complet : 94,492 s ; 107 segments.

### 3. Correction prudente

Les trois transcriptions corrigées ont été comparées aux textes bruts. Seules les erreurs manifestes de reconnaissance ont été corrigées, sans réécriture stylistique : noms et sigles, « lésés », « décote », « consœurs », « Target », « euros centraux », « Monopoly », « dettes », etc. Les formulations ambiguës ont été conservées.

- vidéo 1 : 2 lignes modifiées, 123 segments intacts ;
- vidéo 2 : 7 lignes modifiées, 131 segments intacts ;
- vidéo 3 : 9 lignes modifiées, 107 segments intacts.

Les trois états portent `correction_agent_prudente` et `integrite_horodatages: verifiee`.

### 4. Indexation et synthèse

Les requêtes d’indexation générées automatiquement ont été traitées directement par l’Agent. Trois réponses JSON complètes ont été placées dans `travail/reponses` et importées avec `promethe regenerer-index`. Elles documentent thèmes, raisonnements, concepts, personnes, organismes, événements, repères temporels, expressions et citations.

Après génération des requêtes de synthèse, trois brouillons documentaires ont été rédigés et importés avec `regenerer-synthese` :

- vidéo 1 : 723 mots, promesses initiales de l’euro, estimations de coûts, Target2 et programme de la série ;
- vidéo 2 : 642 mots, bilans bancaires, création monétaire, monnaie centrale, compensation et architecture de l’eurosystème ;
- vidéo 3 : 763 mots, crise de 2008, rupture interbancaire, soldes Target, scénarios de sortie et argument des « fausses dettes ».

Chaque synthèse suit les arguments et leurs enchaînements, comporte des liens YouTube horodatés, attribue les affirmations à l’auteur et précise qu’elle n’est pas une vérification externe.

### 5. Contrôle qualité

Les trois requêtes de contrôle qualité ont été générées. L’Agent a comparé chaque synthèse à sa transcription corrigée et à son index : nombres, attributions, citations, horodatages, couverture et prudence. Les réponses JSON utilisent `@file:reponse_synthese.md` dans le même dossier. Les trois imports ont produit un verdict `conforme`, sans modification supplémentaire ni ancienne version inutile.

### 6. Vérification et limites du lot

`promethe verifier` a déclaré les trois archives complètes. Pour chacune, les neuf documents définitifs et les quatre sous-dossiers organisationnels sont présents, les fichiers JSON se décodent et les sept étapes de l’état sont `complete`.

Une recherche explicite des huit autres identifiants a confirmé qu’aucun dossier d’archive ne leur a été créé. Le test est donc resté strictement limité aux trois vidéos autorisées.

## D. Résultats

Les trois archives complètes sont :

- `archives/Trouble_Fait/2019/2019-10-25_yLEmwlm6VS8` ;
- `archives/Trouble_Fait/2019/2019-10-27_2yaMBOGNjKs` ;
- `archives/Trouble_Fait/2019/2019-10-29_Q99fEqQfuW4`.

Pour chacune, `metadata.json`, `audio.webm`, `segments.json`, les deux transcriptions, `index_video.json`, `synthese_video.md`, `etat_pipeline.json` et `rapport_controle_qualite.md` sont à la racine. Les requêtes et réponses sont rangées sous `travail/`.

### Problèmes rencontrés

Le seul avertissement technique récurrent provient de `yt-dlp`, qui signale l’absence d’un runtime JavaScript pris en charge et le risque futur que certains formats deviennent indisponibles. Cet avertissement n’a bloqué ni l’inventaire, ni les trois téléchargements. Aucun échec réseau, CUDA, Whisper, validation JSON ou import n’a eu lieu. Les écarts d’une seconde entre l’inventaire plat et les métadonnées détaillées des vidéos 2 et 3 sont ceux fournis par YouTube/`yt-dlp` et n’affectent pas les archives.

### Interventions manuelles et conclusion du test

Aucune intervention de l’utilisateur n’a été nécessaire entre les vidéos. L’Agent a effectué les corrections prudentes, indexations, synthèses et contrôles qualité après les exports prévus par le pipeline. Le traitement par lot natif n’a pas été utilisé parce qu’un chronométrage individuel précis était demandé ; la reprise unitaire existante suffisait et aucune adaptation n’a été apportée au projet.

Le test confirme qu’une playlist peut être inventoriée, filtrée contre les archives existantes puis traitée automatiquement par sous-ensemble sans intervention utilisateur entre les vidéos. Les huit vidéos restantes attendent un accord explicite.

Le présent rapport courant 0004 est entièrement finalisé avant sa copie. La copie historique `rapports/0004_2026-10-18_165245_RAPPORT_INTERVENTION.md` doit être créée uniquement à partir de ce fichier final, puis son SHA-256 comparé à celui du courant avant clôture.
