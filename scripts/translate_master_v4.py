#!/usr/bin/env python3
"""
Translation Master Cron v4 – Läuft alle 30 Minuten.
Prüft fehlende Übersetzungen, startet bei Bedarf die nächste Sprache, pusht fertige Sprachen.

Sprachkette: NL → CS → PL → HU → SK → RU
Pro Sprache: 9 Kategorien parallel, Ollama + OpenRouter, kurze Texte 20B, lange 120B
"""
import subprocess, glob, os, sys, json, time
from pathlib import Path

BASE = Path("F:/tiroltourismus")
WORKER = str(BASE / "scripts" / "translate_worker.py")
PYTHON = "C:/HermesPortable/venv/Scripts/python"

LANG_TOTAL = 5240
LANG_CHAIN = ["nl", "cs", "pl", "hu", "sk", "ru"]
CATEGORIES = ["gastro", "unterkuenfte", "orte", "camping", "sehenswuerdigkeiten", "magazin", "regionen", "erlebnisse", "events"]

ENV = os.environ.copy()
ENV["OLLAMA_MODEL_SHORT"] = "gpt-oss:20b"
ENV["OLLAMA_MODEL_LONG"] = "gpt-oss:120b"
ENV["OLLAMA_LONG_TEXT_THRESHOLD"] = "1200"

LOCK = Path("/tmp/translate_master_v4.lock")


def count_lang(lang):
    return len(glob.glob(str(BASE / "src" / "data" / lang / "**" / "index.json"), recursive=True))


def is_worker_running(lang):
    r = subprocess.run(["ps", "-ef"], capture_output=True, text=True)
    for line in r.stdout.split("\n"):
        if "translate_worker" in line and lang in line and "grep" not in line:
            return True
    return False


def git_has_uncommitted(lang):
    r = subprocess.run(
        ["git", "status", "--short", f"src/data/{lang}"],
        capture_output=True, text=True, cwd=str(BASE)
    )
    return len([l for l in r.stdout.split("\n") if l.strip()]) > 0


def git_publish(lang):
    """Commit + Push für fertige Sprache."""
    if not git_has_uncommitted(lang):
        print(f"ℹ️  Keine uncommitteten Änderungen für {lang}")
        return True
    subprocess.run(["git", "add", f"src/data/{lang}"], cwd=str(BASE), check=True)
    r = subprocess.run(["git", "commit", "-m", f"Publish {lang.upper()} translations"], cwd=str(BASE),
                       capture_output=True, text=True)
    if r.returncode != 0 and "nothing to commit" not in r.stdout and "nothing to commit" not in r.stderr:
        print(f"❌ Commit fehlgeschlagen: {r.stderr[:200]}")
        return False
    r = subprocess.run(["git", "push", "origin", "master"], cwd=str(BASE), capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f"❌ Push fehlgeschlagen: {r.stderr[:200]}")
        return False
    print(f"🚀 {lang.upper()} gepusht")
    return True


def start_language(lang):
    """Startet alle 9 Kategorien parallel für eine Sprache."""
    print(f"🔄 Starte {lang} mit 9 Kategorien parallel...")
    procs = []
    for cat in CATEGORIES:
        p = subprocess.Popen(
            [PYTHON, WORKER, cat, lang],
            env=ENV, cwd=str(BASE),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        procs.append(p)
    # Kein wait — läuft asynchron
    return len(procs)


def main():
    # Lock-Check
    if LOCK.exists():
        try:
            pid = int(LOCK.read_text().strip())
            subprocess.run(["kill", "-0", str(pid)], capture_output=True)
            print("⏩ Master läuft bereits – überspringe")
            return
        except (ValueError, subprocess.CalledProcessError):
            LOCK.unlink(missing_ok=True)

    LOCK.write_text(str(os.getpid()))
    try:
        print(f"{'='*60}")
        print(f"🌍 TRANSLATION MASTER V4  {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        for lang in LANG_CHAIN:
            count = count_lang(lang)
            pct = 100 * count / LANG_TOTAL
            running = is_worker_running(lang)
            bar = "█" * int(pct // 2) + "░" * (50 - int(pct // 2))
            print(f"  {lang}: {count:>5}/{LANG_TOTAL} [{bar}] {pct:.1f}%  {'🔄' if running else '⏸'}")

        print()

        # Finde die aktuelle Sprache (erste nicht-100%-ige)
        current_lang = None
        for lang in LANG_CHAIN:
            c = count_lang(lang)
            if c < LANG_TOTAL:
                current_lang = lang
                break

        if current_lang is None:
            print("🎉 ALLE SPRACHEN FERTIG!")
            # Letzten Batch pushen
            for lang in LANG_CHAIN:
                git_publish(lang)
            return

        # Prüfe vorherige Sprachen → pushen
        for lang in LANG_CHAIN:
            if lang == current_lang:
                break
            if count_lang(lang) >= LANG_TOTAL:
                if is_worker_running(lang):
                    print(f"⏳ {lang} fertig aber Worker läuft noch – warten")
                    return
                git_publish(lang)

        c = count_lang(current_lang)
        running = is_worker_running(current_lang)

        if running:
            print(f"⏳ {current_lang} läuft noch ({c}/{LANG_TOTAL}) – überspringe")
            return

        if c >= LANG_TOTAL:
            print(f"✅ {current_lang} fertig! Pushe und starte nächste...")
            git_publish(current_lang)
            # Nächste Sprache finden
            next_lang = None
            for lang in LANG_CHAIN:
                if count_lang(lang) < LANG_TOTAL:
                    next_lang = lang
                    break
            if next_lang:
                start_language(next_lang)
            return

        # Sprache ist weder fertig noch läuft sie → starten
        print(f"🔄 {current_lang}: {c}/{LANG_TOTAL} – starte neu...")
        start_language(current_lang)

    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
