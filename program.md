# program.md — Auto Research transposé à A'Space OS V5

**Doctrine humaine. Code original, écrit depuis le design D-N047 (Clara, 2026-11-09).**
**Ce fichier remplace la doctrine amont du dépôt forké. Le fork `Amdkn/autoresearch` est une référence seule : aucune copie du code amont n'entre dans un artefact A'Space (D12).**

## 1. But

Trouver, par expériences bornées, les fusions qui font baisser le nombre de modules en état 0 et de doublons dans `Amdkn/Aspace_OS_V5`, sans jamais casser un hold-out.

## 2. Entrée fixe — lue, jamais modifiée

- L'inventaire vérifié `@45c5221` : 120 sous-modules, 111 distincts, 21 pointeurs amont non souverains, 9 doublons.
- La doctrine : ce `program.md` + le design D-N047 + le registre `01_Forkable/FUSIONS-REGISTRY.md` (V5).
- L'entrée est fixe comme `prepare.py` l'était chez l'amont : elle se lit, elle ne se modifie pas pendant une expérience.

## 3. Métrique — triple (H, C, D)

Mesurée **avant et après** chaque expérience par le runner :

- **H = hold-outs verts / total** (de la fusion expérimentée).
- **C = compteur d'état 0** (global, V5).
- **D = doublons restants** (global, V5).

**Règle d'acceptation : H = 100 % ET (C baisse OU D baisse)** par rapport aux valeurs pré-expérience.
**H est le veto** : un hold-out rouge rejette toujours, même si C ou D baisse.
Un candidat vert en H mais sans progrès sur C ni D est rejeté comme **no-op** (enregistré, non appliqué).
**Aucun humain ne tranche l'acceptation** — la règle tranche. Les seules exceptions (hold-out lui-même erroné) remontent à Clara par **amendement**, jamais à l'exécutant.

## 4. Budget — triple plafond, coupé mécaniquement

Par expérience :

- **5 minutes** horloge fixe (la comparabilité des expériences l'exige).
- **1 modification** par expérience.
- **Cadence hebdomadaire** (inventaire) **+ à chaque ajout de fork**.

**L'acte qui coupe : la minuterie du runner** (mécanique, pas une décision humaine).
Budget épuisé = expérience enregistrée « budget épuisé, non mesurée » — ni succès, ni échec.
**Coût monétaire : zéro** (Runtime local, PC / VPS ; ni GPU, ni entraînement, ni appel payant). Tout besoin futur d'appel payant est une nouvelle décision de design, hors périmètre.

## 5. Candidat de fusion

- **Une seule modification à la fois**, traçable — portée comme **PR** sur le repo cible.
- **Le runner propose, jamais ne merge.** Aucune fusion appliquée avant le vert des hold-outs d'étape 0 (H-C0) quand elle touche Cordis ou dépend de l'adapter.
- Les vagues V0–V9 au-delà de la première mesure sont hors de ce design : leur exécution est un design ultérieur.

## 6. États

**États d'une fusion (registre) :** `proposée` → `en cours` → `mesurée` → `acceptée` / `rejetée`.

**États d'un module :**
- **0 Basique** — fork Amdkn non adapté.
- **1 Adapté** — fiche + adapter + manifeste, tests verts.
- **2 Vérifié** — hold-outs verts + validation 13e.
- **3 Publié** — état 2 + registre à jour.

**Doctrine : zéro module en publication basique.**

**Règle de comptage du compteur d'état 0 :** un module est en état 0 si son fork est **Amdkn** ET qu'**aucune fiche d'adaptation n'existe** ET qu'il n'est pas déjà en état > 0. **Les 21 pointeurs amont non souverains ne comptent pas** (problème de souveraineté, pas d'état 0) ; un doublon compte **une fois** (le module distinct compte, le pointeur en double alimente D).

## 7. Séquençage

Les actes préparatoires (création du fork, création du registre, écriture de cette doctrine) courent en parallèle de l'étape 0 — périmètre disjoint. **La première expérience de fusion attend le vert des hold-outs d'étape 0 (H-C0).** Le gate est nommé, pas implicite.

## 8. Licence — statut du fork

`karpathy/autoresearch` est **sans licence** (`license: null`, aucun fichier LICENSE). Ce fork est une **référence seule** : étudier le mécanisme, vérifier les lectures — jamais copier. **Repli nommé :** si l'auteur s'oppose, le fork est supprimé ; si une licence apparaît, le design est **amendé** pour autoriser la réutilisation sous cette licence.

---

*Doctrine posée par Ryan (Factory), dispatch D-N047, Phase A2. Autorité de design : Clara. Validation : 13e.*
