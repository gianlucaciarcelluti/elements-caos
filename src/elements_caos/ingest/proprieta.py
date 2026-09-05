"""Estrazione delle proprietà fisico-chimiche dal dataset Periodic-Table-JSON.

Il dataset è distribuito con licenza CC BY-SA 3.0 e va attribuito. Contiene 119
voci: l'ultima, l'ununennio, è un elemento ipotetico non ancora sintetizzato e
viene scartata.
"""

import json
from pathlib import Path
from typing import Any

import requests

from elements_caos.models import Categoria, Proprieta

URL_DATASET = (
    "https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/"
    "master/PeriodicTableJSON.json"
)

# L'ununennio (Z=119) è previsto dalla teoria ma non è mai stato sintetizzato.
NUMERO_ATOMICO_MASSIMO = 118

# Corrispondenza fra le categorie del dataset e quelle normalizzate italiane.
# Le forme "unknown, ..." indicano elementi sintetici le cui proprietà sono
# predette e non misurate: si riconducono comunque alla categoria di base.
MAPPA_CATEGORIE = {
    "alkali metal": Categoria.METALLO_ALCALINO,
    "alkaline earth metal": Categoria.METALLO_ALCALINO_TERROSO,
    "transition metal": Categoria.METALLO_DI_TRANSIZIONE,
    "post-transition metal": Categoria.METALLO_POST_TRANSIZIONE,
    "metalloid": Categoria.SEMIMETALLO,
    "polyatomic nonmetal": Categoria.NON_METALLO,
    "diatomic nonmetal": Categoria.NON_METALLO,
    "nonmetal": Categoria.NON_METALLO,
    "halogen": Categoria.ALOGENO,
    "noble gas": Categoria.GAS_NOBILE,
    "lanthanide": Categoria.LANTANIDE,
    "actinide": Categoria.ATTINIDE,
    "unknown, probably transition metal": Categoria.METALLO_DI_TRANSIZIONE,
    "unknown, probably post-transition metal": Categoria.METALLO_POST_TRANSIZIONE,
    "unknown, probably metalloid": Categoria.SEMIMETALLO,
    "unknown, predicted to be noble gas": Categoria.GAS_NOBILE,
    "unknown, but predicted to be an alkali metal": Categoria.METALLO_ALCALINO,
}


class ErroreIngest(Exception):
    """Errore nell'acquisizione o nell'interpretazione dei dati esterni."""


def scarica_dataset(destinazione: Path) -> Path:
    """Scarica il dataset delle proprietà e lo salva nel percorso indicato."""
    try:
        risposta = requests.get(URL_DATASET, timeout=60)
        risposta.raise_for_status()
    except requests.RequestException as errore:
        raise ErroreIngest(f"impossibile scaricare il dataset: {errore}") from errore

    destinazione.parent.mkdir(parents=True, exist_ok=True)
    destinazione.write_bytes(risposta.content)
    return destinazione


def leggi_dataset(percorso: Path) -> list[dict[str, Any]]:
    """Legge il dataset scartando le voci oltre il numero atomico 118."""
    if not percorso.exists():
        raise ErroreIngest(f"dataset non trovato: {percorso}")

    try:
        contenuto = json.loads(percorso.read_text(encoding="utf-8"))
    except json.JSONDecodeError as errore:
        raise ErroreIngest(f"dataset non leggibile: {errore}") from errore

    voci: list[dict[str, Any]] = contenuto["elements"]
    return [voce for voce in voci if voce["number"] <= NUMERO_ATOMICO_MASSIMO]


def mappa_categoria(categoria_inglese: str) -> Categoria:
    """Traduce la categoria del dataset nella categoria italiana normalizzata."""
    normalizzata = categoria_inglese.strip().lower()
    if normalizzata not in MAPPA_CATEGORIE:
        raise ErroreIngest(f"categoria non riconosciuta: {categoria_inglese!r}")
    return MAPPA_CATEGORIE[normalizzata]


def estrai_proprieta(voce: dict[str, Any]) -> Proprieta:
    """Costruisce le proprietà di un elemento a partire da una voce del dataset.

    I campi assenti nel dataset (fusione, ebollizione e densità di molti
    elementi sintetici) restano nulli: non sono un errore ma un dato mancante.
    """
    try:
        return Proprieta(
            gruppo=voce.get("group"),
            periodo=voce["period"],
            blocco=voce["block"],
            categoria=mappa_categoria(voce["category"]),
            massa_atomica=float(voce["atomic_mass"]),
            configurazione_elettronica=voce["electron_configuration_semantic"],
            gusci=list(voce["shells"]),
            punto_fusione_k=voce.get("melt"),
            punto_ebollizione_k=voce.get("boil"),
            densita=voce.get("density"),
            stati_ossidazione=[],
        )
    except KeyError as errore:
        raise ErroreIngest(
            f"campo mancante nella voce {voce.get('number', '?')}: {errore}"
        ) from errore
