# Rapport de la dernière intervention

Date de clôture : 2026-10-19 (Asia/Tokyo)  
Objet : archivage documentaire complet de cinq nouvelles vidéos YouTube.

## A. Demande initiale

L'utilisateur a fourni cinq URL YouTube et demandé leur archivage selon la procédure permanente de Prométhé. Cette demande impliquait, pour chaque vidéo, métadonnées, audio, transcription Whisper horodatée, correction contextuelle, synthèse approfondie, index 1.1, contrôle qualité et vérification finale, avec reprise indépendante en cas d'échec.

Identifiants demandés : `8F90IfUcW3w`, `tMkNyXpws_0`, `889I60By4Xc`, `SDcDg6diFUc` et `dT1ZHCA4DLU`.

## B. État initial

- Aucun des cinq identifiants n'existait dans la bibliothèque.
- La bibliothèque comptait 14 archives complètes avant l'intervention.
- Le premier lancement normal de `promethe lot` a réussi uniquement pour `889I60By4Xc`. YouTube a bloqué les quatre autres avant leurs métadonnées avec une vérification anti-robot.
- La session Chrome, autorisée explicitement par l'utilisateur, n'était pas exploitable : base verrouillée puis chiffrement DPAPI/App-Bound indéchiffrable dans l'environnement.
- L'utilisateur a ensuite autorisé l'usage de sa session Firefox. Les cookies étaient lisibles, mais les clients YouTube initiaux ne fournissaient aucun flux audio utilisable sans résolution JavaScript.

## C. Travail effectué

### Acquisition et transcription

- `889I60By4Xc` a été traité par le pipeline normal avec `promethe lot` : métadonnées, `audio.webm`, 371 segments et transcription Whisper `medium` sur CUDA.
- Pour les quatre autres vidéos, la session Firefox autorisée a été transmise directement à `yt-dlp`, sans affichage ni conservation des cookies.
- Un runtime Deno 2.9.7 portable a été téléchargé temporairement depuis la distribution officielle. Son archive a été contrôlée avec le SHA-256 publié : `A0C3101B4158D1DFB7D6A78A7BF0F3DE80C96BB423C152BEEC8BEB22786F2238`.
- Deno et le composant EJS officiel de `yt-dlp` ont résolu les défis JavaScript de YouTube. Les quatre sources ont été téléchargées, puis FFmpeg déjà fourni par Krita a extrait `audio.m4a`.
- Les composants existants de Prométhé ont classé les métadonnées et audios, exécuté Whisper `medium` sur CUDA, produit `segments.json` et `transcription_brute.txt`, puis placé la correction en `waiting_manual`.
- Le runtime Deno, les téléchargements intermédiaires et les scripts temporaires ont été supprimés après ingestion. Aucun `cookies.txt` n'a existé ou été conservé dans le dépôt.

### Traitement documentaire par l'agent

- Les cinq transcriptions ont reçu une correction contextuelle prudente en place. Les corrections ont notamment porté sur ARENH, VNU, *merit order*, Ursula von der Leyen, Stéphane Séjourné, Mercosur, « Made in Europe », noms de médias et institutions, Florence Bergeaud-Blackler, FEMYSO, FIOE, Houria Bouteldja et plusieurs erreurs lexicales manifestes.
- Chaque import de correction a été validé par `promethe corriger-transcription`, qui exige l'identité exacte du nombre, de l'ordre et des valeurs des horodatages.
- Cinq synthèses approfondies ont été produites. Elles distinguent les thèses des chaînes, les propos cités, les objections, les concessions et les limites documentaires.
- Cinq index conformes au schéma 1.1 ont été produits avec résumé, thèmes, sujets secondaires, mots-clés, personnes, organismes, concepts, événements, arguments attribués, lieux/périodes, relations et repères temporels.
- Cinq contrôles qualité ont comparé synthèse, index et transcription corrigée. Les rapports finaux portent le verdict `conforme` et les cinq états marquent toutes les étapes `complete`.
- Tous les candidats, réponses et requêtes intermédiaires ont été supprimés après import. Les dossiers `travail/` normalisés restent vides.

### Fichiers produits

Dans chacun des cinq nouveaux dossiers d'archive :

- `metadata.json` ;
- `audio.webm` pour `889I60By4Xc`, `audio.m4a` pour les quatre autres ;
- `segments.json` ;
- `transcription_brute.txt` ;
- `transcription_corrigee.txt` ;
- `synthese_video.md` ;
- `index_video.json` ;
- `rapport_controle_qualite.md` ;
- `etat_pipeline.json` ;
- arborescence vide `travail/` et `historique/`.

Aucun fichier de code permanent n'a été modifié. Les utilitaires temporaires créés pour l'ingestion, les corrections, les index et les réponses qualité ont été supprimés.

## D. Résultats vidéo par vidéo

| ID | Chaîne et titre | Durée | Segments | État documentaire | Limites |
|---|---|---:|---:|---|---|
| `8F90IfUcW3w` | PRAXIS – *Comment l'Europe sabote EDF pour enrichir les traders* | 32 min 54 s | 738 | métadonnées, audio, transcription, correction, synthèse, index et QC `complete` | chiffres sur ARENH, nucléaire et crise attribués à la vidéo ; réponses adverses peu développées |
| `tMkNyXpws_0` | Juste Milieu – *Made in Europe : la nouvelle escroquerie de l’UE ?* | 14 min 17 s | 261 | toutes étapes `complete` | traitement satirique et partisan ; articles et projet juridique visibles seulement par extraits |
| `889I60By4Xc` | Maudin Malin – *L'arnaque de l'islamophobie* | 29 min 41 s | 371 | toutes étapes `complete` | lecture engagée d'un livre, sans contradiction ni vérification extérieure des filiations alléguées |
| `SDcDg6diFUc` | Le Fil d'Actu – *Bilan 2025-2026 : naufrage français, folie européenne, déni politicien* | 21 min 35 s | 369 | toutes étapes `complete` | réquisitoire éditorial ; projections économiques et de dette à vérifier avant citation factuelle |
| `dT1ZHCA4DLU` | Le Fil d'Actu – *Adhésion de l'Ukraine à l'UE : pourquoi la France doit dire non* | 20 min 07 s | 368 | toutes étapes `complete` | argumentaire défavorable ; bénéfices invoqués par les partisans de l'adhésion peu développés |

## Validations réalisées

- Nouvel inventaire : 19 archives au total, contre 14 initialement.
- `promethe verifier ID` exécuté avec succès pour chacun des cinq identifiants : fichiers, audio, disposition et étapes validés.
- Horodatages : identité exacte entre transcription brute et corrigée pour les 2 107 segments cumulés (738 + 261 + 371 + 369 + 368).
- Fichiers de travail restants dans les cinq archives : 0.
- Runtime Deno temporaire : supprimé.
- Répertoire de téléchargements temporaires : supprimé.
- Fichier de cookies dans le dépôt : absent.
- Tests techniques : `python -m unittest discover -s tests -v` — 18 tests exécutés, 18 réussis.
- Une erreur de post-traitement initiale due à l'absence du chemin FFmpeg dans la commande temporaire a été corrigée en réutilisant `C:\Program Files\Krita (x64)\bin`; aucun média n'a été retéléchargé lors de cette reprise.

## Limites restantes

- YouTube impose actuellement, pour certaines vidéos, une session authentifiée, un moteur JavaScript et le composant EJS. Le pipeline Python standard ne transmet pas ces paramètres : l'ingestion des quatre vidéos a donc nécessité un adaptateur temporaire, supprimé après usage.
- Les contrôles qualité sont internes au corpus. Ils vérifient fidélité, couverture, attribution et cohérence, mais ne constituent pas un fact-checking externe.
- Les noms propres et termes manifestement reconnaissables ont été corrigés, sans prétendre éliminer toute erreur lexicale résiduelle de Whisper. Toute citation destinée à publication doit être rapprochée de l'audio.
- Les vidéos adoptent toutes une orientation critique envers l'Union européenne ou certaines politiques européennes. Les synthèses et index restituent cette orientation sans la transformer en fait établi.

Conclusion : les cinq vidéos demandées sont archivées jusqu'au contrôle qualité final, sans doublon documentaire ni artefact sensible restant.
