"""Verifica che gli URL dichiarati in `fonti:` rispondano ancora.

Le fonti sono il presidio di attendibilità di un vault storico pubblico, e un
link morto ne vanifica la funzione. Il controllo è deliberatamente non
bloccante: gli URL muoiono dopo la pubblicazione, non prima, e la salute di
server terzi non deve fermare una pipeline che non c'entra.

Uso: uv run python scripts/verifica_fonti.py [--dati data]
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
from collections import defaultdict
from pathlib import Path

import requests
import yaml

# Un'attesa generosa: la lentezza di un archivio storico non è un difetto della
# fonte, e un timeout stretto produrrebbe soltanto falsi allarmi.
ATTESA = 20
TENTATIVI = 2

# Molti host rispondono 403 o 401 a una richiesta automatica pur essendo vivi,
# e un 429 dice soltanto che stiamo chiedendo troppo in fretta. Gli unici
# codici che dicono davvero "questa pagina non c'è più" sono 404 e 410.
CODICI_MORTI = {404, 410}

INTESTAZIONI = {
    "User-Agent": (
        "elements-caos/1.0 (verifica dei link delle fonti; "
        "https://github.com/gianlucaciarcelluti/elements-caos)"
    )
}


def raccogli_url(cartella_dati: Path) -> dict[str, list[str]]:
    """Raccoglie gli URL delle fonti, ciascuno con gli elementi che lo citano."""
    citazioni: dict[str, list[str]] = defaultdict(list)
    for percorso in sorted(cartella_dati.glob("elements/*.yaml")):
        dati = yaml.safe_load(percorso.read_text(encoding="utf-8"))
        for fonte in dati.get("fonti") or []:
            citazioni[fonte["url"]].append(dati["nome"])
    return dict(citazioni)


def _e_dns(errore: BaseException) -> bool:
    """Dice se l'errore è un nome di host che non risolve.

    Un host che non esiste più è un link morto quanto un 404, mentre un
    timeout o una connessione rifiutata possono essere il server giù per
    mezz'ora: le due cose vanno distinte, e requests le presenta entrambe
    come ConnectionError.
    """
    visti: set[int] = set()
    causa: BaseException | None = errore
    while causa is not None and id(causa) not in visti:
        visti.add(id(causa))
        if isinstance(causa, socket.gaierror) or type(causa).__name__ == "NameResolutionError":
            return True
        causa = causa.__cause__ or causa.__context__
    return False


def interroga(url: str) -> tuple[bool, str]:
    """Dice se l'URL è ancora raggiungibile, e con quale esito.

    Prova prima con HEAD, che non scarica il corpo della pagina, e ripiega su
    GET perché diversi server rispondono a HEAD con un errore pur servendo
    regolarmente la pagina.
    """
    ultimo = "nessuna risposta"
    dns_fallito = False
    for tentativo in range(TENTATIVI):
        for metodo in ("HEAD", "GET"):
            try:
                risposta = requests.request(
                    metodo,
                    url,
                    timeout=ATTESA,
                    allow_redirects=True,
                    headers=INTESTAZIONI,
                )
            except requests.RequestException as errore:
                ultimo = type(errore).__name__
                dns_fallito = _e_dns(errore)
                continue
            if risposta.status_code in CODICI_MORTI:
                return False, str(risposta.status_code)
            if risposta.ok or metodo == "GET":
                return True, str(risposta.status_code)
        if tentativo + 1 < TENTATIVI:
            ultimo = f"{ultimo} (dopo {tentativo + 1} tentativi)"
    if dns_fallito:
        return False, "host non risolto"
    # Un errore di rete ripetuto non prova che la pagina sia sparita: potrebbe
    # essere il runner o il server temporaneamente giù. Si segnala come non
    # verificabile, non come morto.
    return True, f"non verificabile: {ultimo}"


def main(argomenti: list[str] | None = None) -> int:
    analizzatore = argparse.ArgumentParser(description=__doc__)
    analizzatore.add_argument("--dati", type=Path, default=Path("data"))
    opzioni = analizzatore.parse_args(argomenti)

    citazioni = raccogli_url(opzioni.dati)
    morti: list[tuple[str, str, list[str]]] = []
    non_verificabili: list[tuple[str, str]] = []

    for url in sorted(citazioni):
        vivo, esito = interroga(url)
        if not vivo:
            morti.append((url, esito, citazioni[url]))
            print(f"[morto {esito}] {url} — citato da: {', '.join(citazioni[url])}")
        elif esito.startswith("non verificabile"):
            non_verificabili.append((url, esito))
            print(f"[{esito}] {url}")

    righe = [
        f"Controllati {len(citazioni)} URL distinti.",
        f"Link morti (404, 410 o host che non risolve): {len(morti)}.",
        f"Non verificabili: {len(non_verificabili)}.",
    ]
    for url, esito, elementi in morti:
        righe.append(f"- `{url}` ({esito}) — {', '.join(elementi)}")
    riepilogo = "\n".join(righe)
    print("\n" + riepilogo)

    riepilogo_ci = os.environ.get("GITHUB_STEP_SUMMARY")
    if riepilogo_ci:
        with open(riepilogo_ci, "a", encoding="utf-8") as file:
            file.write("## Fonti\n\n" + riepilogo + "\n")

    # Sempre zero: il controllo informa, non blocca.
    return 0


if __name__ == "__main__":
    sys.exit(main())
