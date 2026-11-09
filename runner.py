#!/usr/bin/env python3
"""runner.py — harnais Auto Research transposé à A'Space OS V5.

Code original, écrit depuis le design D-N047 (Clara, 2026-11-09).
Rôle : proposer, mesurer avant/après, enregistrer, couper le budget.
Le runner propose, jamais ne merge. Aucune copie du code amont (D12).

Usage :
    python3 runner.py measure --v5 <chemin V5>
        Mesure (H, C, D) : H = hold-outs de la fusion (via --holdouts),
        C = compteur d'état 0, D = doublons restants.
    python3 runner.py run --fusion F1 --v5 <chemin V5> --holdouts <cmd>
        Une expérience : une seule modification, budget 5 min coupé par
        minuterie. Enregistre le résultat dans experiments.jsonl et
        propose une transition de registre (jamais appliquée ici).
"""

import argparse
import configparser
import glob
import json
import os
import subprocess
import sys
import time

BUDGET_SECONDS = 300  # D8 : 5 minutes horloge fixe
JOURNAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "experiments.jsonl")

# D13 : un module est en état 0 si son fork est Amdkn ET qu'aucune fiche
# d'adaptation n'existe ET qu'il n'est pas déjà en état > 0. Les pointeurs
# amont non souverains ne comptent pas ; un doublon compte une fois.
SOVEREIGN_HOSTS = ("github.com/Amdkn/", "huggingface.co/Amdkn7/")
# Amendement D13 (jugement 13e, journal 407, D-N048 V2) : le runner scanne
# TOUS les domiciles 01_Forkable/<FKB>/00_A0_Core/ (§D7), pas FKB00 seul.
# Avant : ADAPTATION_GLOB = ("01_Forkable", "FKB00_Runtime", "00_A0_Core")
# — les fiches FKB04/FKB03 n'étaient pas comptées (C surévalué de 2 :
# 92 mesuré, vrai C 90). Le registre reste la source D10.
ADAPTATION_GLOB = ("01_Forkable", "*", "00_A0_Core")


def _deadline(started_at):
    return started_at + BUDGET_SECONDS


def _check_budget(deadline, label):
    """Coupe mécanique du budget (D8) : passée la minuterie, on arrête."""
    if time.monotonic() > deadline:
        raise TimeoutError(f"budget épuisé à {label} — expérience non mesurée")


def parse_gitmodules(v5_path):
    """Lit .gitmodules : liste des (chemin, url) des sous-modules."""
    path = os.path.join(v5_path, ".gitmodules")
    if not os.path.exists(path):
        raise FileNotFoundError(f".gitmodules absent : {path}")
    cfg = configparser.ConfigParser()
    cfg.read(path)
    entries = []
    for section in cfg.sections():
        entries.append((cfg.get(section, "path", fallback=""),
                        cfg.get(section, "url", fallback="")))
    return entries


def adaptation_sheets(v5_path):
    """Noms de modules disposant d'une fiche d'adaptation (état > 0).

    Scan de tous les domiciles 01_Forkable/<FKB>/00_A0_Core/ (§D7,
    amendement D13, journal 407) — un module adapté dans n'importe
    quel FKB sort de C.
    """
    sheets = set()
    for base in glob.glob(os.path.join(v5_path, *ADAPTATION_GLOB)):
        if not os.path.isdir(base):
            continue
        for name in os.listdir(base):
            if name.endswith("-ADAPTATION.md"):
                sheets.add(name[:-len("-ADAPTATION.md")].lower())
    return sheets


def _norm_url(url):
    """Normalise une URL de sous-module pour la comparaison de doublons."""
    return url.strip().rstrip("/").lower().removesuffix(".git")


def measure_c_d(v5_path):
    """Compteur d'état 0 (C) et doublons (D), règle D13.

    Distinct = URL normalisée (un même dépôt à deux chemins = un module,
    le second pointeur alimente D). Souverain = URL Amdkn / Amdkn7.
    """
    entries = parse_gitmodules(v5_path)
    urls = [_norm_url(u) for _, u in entries]
    distinct_urls = sorted(set(urls))
    duplicates = len(entries) - len(distinct_urls)
    sovereign_urls = sorted({u for u in distinct_urls
                             if any(h.lower() in u for h in SOVEREIGN_HOSTS)})
    sheets = adaptation_sheets(v5_path)
    state0 = [u for u in sovereign_urls
              if u.rsplit("/", 1)[-1] not in sheets]
    return {
        "C": len(state0),
        "D": duplicates,
        "state0_modules": state0,
        "total_entries": len(entries),
        "distinct": len(distinct_urls),
        "sovereign_distinct": len(sovereign_urls),
    }


def run_holdouts(command, deadline):
    """Exécute la commande de hold-outs de la fusion ; retourne (verts, total)."""
    _check_budget(deadline, "hold-outs")
    if not command:
        return None, None
    proc = subprocess.run(command, shell=True, capture_output=True, text=True,
                          timeout=max(1, int(deadline - time.monotonic())))
    # Convention : la commande imprime "HOLDOUTS <verts>/<total>" sur stdout.
    for line in proc.stdout.splitlines():
        if line.startswith("HOLDOUTS "):
            try:
                green, total = line[len("HOLDOUTS "):].split("/")
                return int(green), int(total)
            except ValueError:
                pass
    # Sans convention, le code de sortie tranche : 0 = tous verts, sinon 0/total.
    return (0, 0) if proc.returncode != 0 else (None, None)


def decide(h_green, h_total, before, after):
    """Règle d'acceptation D7. H = veto ; no-op enregistré, non appliqué."""
    if h_green is None or h_total is None:
        return "non mesurée"
    if h_green != h_total:
        return "rejetée (H veto : hold-out rouge)"
    if after["C"] < before["C"] or after["D"] < before["D"]:
        return "acceptée"
    return "rejetée (no-op : H vert sans progrès C ni D)"


def record(entry):
    with open(JOURNAL, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def cmd_measure(args):
    result = measure_c_d(args.v5)
    h_green, h_total = run_holdouts(args.holdouts, time.monotonic() + BUDGET_SECONDS)
    print(json.dumps({"H": [h_green, h_total], "C": result["C"], "D": result["D"],
                      "state0_modules": result["state0_modules"]},
                     ensure_ascii=False, indent=2))
    return 0


def cmd_run(args):
    started = time.monotonic()
    deadline = _deadline(started)
    before = measure_c_d(args.v5)
    h_before = run_holdouts(args.holdouts, deadline)
    _check_budget(deadline, "avant modification")
    # Une seule modification : le candidat est un patch appliqué ici par
    # l'exécutant, jamais par le runner. Le runner mesure, il ne modifie pas.
    # (Le patch est passé par --patch, appliqué hors du runner, ou déjà présent.)
    after = measure_c_d(args.v5)
    h_after = run_holdouts(args.holdouts, deadline)
    h_green, h_total = h_after if h_after[0] is not None else h_before
    verdict = decide(h_green, h_total, before, after)
    entry = {
        "fusion": args.fusion,
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "before": {"H": list(h_before), "C": before["C"], "D": before["D"]},
        "after": {"H": [h_green, h_total], "C": after["C"], "D": after["D"]},
        "verdict": verdict,
        "budget_seconds": BUDGET_SECONDS,
    }
    try:
        _check_budget(deadline, "enregistrement")
    except TimeoutError:
        entry["verdict"] = "budget épuisé, non mesurée"
    record(entry)
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    # Proposition de transition de registre : écrite, jamais appliquée ici.
    print(f"PROPOSITION: {args.fusion} -> {entry['verdict']} "
          f"(à consigner au registre par l'exécution, jamais par le runner)")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    m = sub.add_parser("measure", help="mesurer (H, C, D)")
    m.add_argument("--v5", required=True, help="chemin du checkout Aspace_OS_V5")
    m.add_argument("--holdouts", default=None,
                   help="commande de hold-outs (imprime 'HOLDOUTS v/t')")
    m.set_defaults(func=cmd_measure)
    r = sub.add_parser("run", help="une expérience : 1 modification, budget 5 min")
    r.add_argument("--fusion", required=True, help="id de la fusion (F1..F10)")
    r.add_argument("--v5", required=True, help="chemin du checkout Aspace_OS_V5")
    r.add_argument("--holdouts", default=None,
                   help="commande de hold-outs (imprime 'HOLDOUTS v/t')")
    r.set_defaults(func=cmd_run)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
