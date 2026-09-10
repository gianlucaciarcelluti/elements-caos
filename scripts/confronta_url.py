"""Confronta gli URL di un sito pubblicato con quelli di uno costruito.

Serve prima di sostituire un generatore con un altro: ogni indirizzo che il
sito serve oggi deve continuare a rispondere, o essere una perdita dichiarata.

Uso:
    uv run python scripts/confronta_url.py <sitemap-vecchia.xml> <cartella-nuova>

Il confronto normalizza il percent-encoding: `/epoche/antichit%C3%A0` e
`/epoche/antichità` sono lo stesso indirizzo, e confrontarli alla lettera
produce sedici falsi allarmi.

Le pagine si confrontano senza estensione perché GitHub Pages serve `foo.html`
anche su `/foo`: è così che gli URL di Quartz, tutti senza estensione,
continuano a funzionare su un sito che emette file `.html`.
"""

import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

BASE = "https://gianlucaciarcelluti.github.io/elements-caos"


def indirizzi_pubblicati(sitemap: Path) -> set[str]:
    """Legge gli indirizzi dalla sitemap del sito attualmente pubblicato."""
    testo = sitemap.read_text(encoding="utf-8")
    trovati = re.findall(r"<loc>(.*?)</loc>", testo)
    return {unquote(url.removeprefix(BASE)).strip("/") or "/" for url in trovati}


def indirizzi_costruiti(cartella: Path) -> set[str]:
    """Ricava gli indirizzi serviti da una cartella di file HTML."""
    indirizzi = set()
    for percorso in cartella.rglob("*.html"):
        relativo = percorso.relative_to(cartella).as_posix()
        if relativo == "index.html":
            indirizzi.add("/")
        elif relativo.endswith("/index.html"):
            indirizzi.add(relativo.removesuffix("/index.html"))
        else:
            indirizzi.add(relativo.removesuffix(".html"))
    return indirizzi


def main(argomenti: list[str]) -> int:
    """Confronta e riporta le differenze, raggruppate per famiglia."""
    if len(argomenti) != 2:
        print(__doc__, file=sys.stderr)
        return 2

    vecchi = indirizzi_pubblicati(Path(argomenti[0]))
    nuovi = indirizzi_costruiti(Path(argomenti[1]))

    persi = sorted(vecchi - nuovi)
    aggiunti = sorted(nuovi - vecchi)

    print(f"pubblicati: {len(vecchi)}   costruiti: {len(nuovi)}")
    print(f"conservati: {len(vecchi & nuovi)}   persi: {len(persi)}   nuovi: {len(aggiunti)}")

    if persi:
        famiglie = Counter(u.split("/")[0] if "/" in u else "(radice)" for u in persi)
        print("\nIndirizzi che smetterebbero di rispondere:")
        for famiglia, quanti in famiglie.most_common():
            print(f"  {famiglia}: {quanti}")
        for indirizzo in persi[:10]:
            print(f"    - {indirizzo}")
        if len(persi) > 10:
            print(f"    ... e altri {len(persi) - 10}")

    if aggiunti:
        print(f"\nIndirizzi nuovi: {len(aggiunti)}")
        for indirizzo in aggiunti[:6]:
            print(f"    + {indirizzo}")

    return 1 if persi else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
