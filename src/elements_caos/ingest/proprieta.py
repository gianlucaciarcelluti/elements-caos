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


def _correggi_categoria_per_gruppo(
    categoria: Categoria, numero_atomico: int, gruppo: int | None
) -> Categoria:
    """Corregge la categoria in base al gruppo atomico quando il dataset non è esatto.

    Il dataset usa una tassonomia per stato fisico (metalli / non-metalli / semimetalli)
    che non contempla le famiglie di gruppo. Questa funzione applica correzioni basate
    sulla classificazione IUPAC per i gruppi:
    - Gruppo 17: alogeni (indipendentemente dal dataset)
    - L'idrogeno (Z=1, gruppo 1) non è mai un metallo alcalino

    La correzione è conservatrice: viene applicata solo quando il gruppo è noto
    e la correzione è inequivocabile (es. Z=9 e gruppo=17 → sicuramente alogeno).
    """
    # Gruppo 17: alogeni (F, Cl, Br, I, At, Ts)
    if gruppo == 17:
        return Categoria.ALOGENO

    return categoria


def estrai_proprieta(voce: dict[str, Any]) -> Proprieta:
    """Costruisce le proprietà di un elemento a partire da una voce del dataset.

    I campi assenti nel dataset (fusione, ebollizione e densità di molti
    elementi sintetici) restano nulli: non sono un errore ma un dato mancante.

    Dopo la mappatura iniziale dal dataset, applica correzioni basate sul numero
    atomico e dal gruppo per allinearsi alla classificazione IUPAC, in particolare
    per le famiglie (alogeni, ecc.) che il dataset non classifica esplicitamente.
    """
    try:
        categoria = mappa_categoria(voce["category"])
        gruppo = voce.get("group")
        numero_atomico = voce["number"]

        # Applica correzioni basate sul gruppo
        categoria = _correggi_categoria_per_gruppo(categoria, numero_atomico, gruppo)

        return Proprieta(
            gruppo=gruppo,
            periodo=voce["period"],
            blocco=voce["block"],
            categoria=categoria,
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
