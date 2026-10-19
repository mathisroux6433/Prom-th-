# Consigne permanente de rapport d'intervention

À la fin de toute demande de travail exécutée dans ce dépôt par Cursor Agent ou un autre agent de développement :

1. Rédiger et terminer entièrement `RAPPORT_DERNIERE_INTERVENTION.md` à la racine. Toutes les opérations et validations de l'intervention doivent déjà y figurer avant l'étape suivante.
2. Y décrire au minimum : A. demande initiale ; B. état initial ; C. travail effectué ; D. résultats. Mentionner précisément les fichiers créés, modifiés, déplacés ou supprimés, les décisions d'architecture, les commandes utilisateur touchées, les validations réalisées et les limites restantes.
3. Pour une vidéo, inclure la durée et l'état de la transcription, de l'indexation, de la synthèse, du contrôle qualité et des fichiers produits.
4. Une fois seulement le rapport courant entièrement terminé, le copier dans `rapports/` sous la forme `NNNN_AAAA-MM-JJ_HHMMSS_RAPPORT_INTERVENTION.md`. Le numéro est le prochain entier disponible, sur quatre chiffres. Ne jamais créer la copie avant la finalisation du courant et ne jamais écraser une copie historique.
5. Calculer le SHA-256 des deux fichiers et vérifier qu'ils sont strictement identiques. Une différence de hash rend l'intervention inachevée et doit être corrigée avant sa clôture.
6. Le rapport doit être autonome : une IA sans accès à la conversation doit pouvoir reconstituer la demande, l'état antérieur, les opérations, les décisions, les résultats et ce qui reste à faire.

Cette mise à jour fait partie de la définition de fin de chaque intervention, même si la demande ne concerne pas le code.
