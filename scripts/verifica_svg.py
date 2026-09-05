"""Ispeziona un SVG generato: geometria, colori, sovrapposizioni.

Serve al controller per verificare gli SVG senza fidarsi del report.
Uso: uv run python .superpowers/.../verifica-svg.py <file.svg>
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SOGLIA_WCAG = 3.0
BIANCO, NERO = "#ffffff", "#0d1117"


def luminanza(esadecimale: str) -> float:
    """Calcola la luminanza relativa di un colore secondo WCAG."""
    h = esadecimale.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    canali = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lineari = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canali]
    return 0.2126 * lineari[0] + 0.7152 * lineari[1] + 0.0722 * lineari[2]


def contrasto(a: str, b: str) -> float:
    """Rapporto di contrasto fra due colori."""
    la, lb = sorted([luminanza(a), luminanza(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def main(percorso: str) -> int:
    testo = Path(percorso).read_text(encoding="utf-8")
    print(f"=== {percorso} ===")

    try:
        radice = ET.fromstring(testo)
    except ET.ParseError as errore:
        print(f"  XML NON VALIDO: {errore}")
        return 1
    print("  XML valido")

    if "<style" in testo or "prefers-color-scheme" in testo:
        print("  VIOLAZIONE: contiene <style> o media query (vietati)")
        return 1
    print("  nessuno <style>, nessuna media query")

    ns = "{http://www.w3.org/2000/svg}"
    cerchi = radice.iter(f"{ns}circle")
    raggi = sorted({float(c.get("r", 0)) for c in cerchi if float(c.get("r", 0)) > 12})
    print(f"  orbite/nucleo (r>12): {raggi}")
    troppo_vicini = [(a, b) for a, b in zip(raggi, raggi[1:], strict=False) if b - a < 14]
    if troppo_vicini:
        print(f"  ATTENZIONE: orbite a meno di 14px: {troppo_vicini}")
    else:
        print("  distanze fra orbite adeguate")

    colori = sorted(set(re.findall(r"#[0-9a-fA-F]{3,6}", testo)))
    print("  colori usati:")
    for c in colori:
        cb, cn = contrasto(c, BIANCO), contrasto(c, NERO)
        esito = "ok" if min(cb, cn) >= SOGLIA_WCAG else "SOTTO SOGLIA"
        print(f"    {c:9} bianco {cb:5.2f}  nero {cn:5.2f}  {esito}")

    vb = radice.get("viewBox")
    print(f"  viewBox: {vb}")
    if vb:
        _, _, larghezza, altezza = (float(v) for v in vb.split())
        fuori = []
        for elemento in radice.iter():
            cx, cy, r = (
                elemento.get("cx"),
                elemento.get("cy"),
                elemento.get("r"),
            )
            if cx and cy and r:
                x, y, raggio = float(cx), float(cy), float(r)
                esce = (
                    x - raggio < 0
                    or y - raggio < 0
                    or x + raggio > larghezza
                    or y + raggio > altezza
                )
                if esce:
                    fuori.append((x, y, raggio))
        if fuori:
            print(f"  ATTENZIONE: {len(fuori)} elementi escono dal viewBox: {fuori[:3]}")
        else:
            print("  tutti gli elementi dentro il viewBox")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
