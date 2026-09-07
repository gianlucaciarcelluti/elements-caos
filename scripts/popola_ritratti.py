"""Popola i ritratti degli scopritori a partire da Wikidata e Wikimedia Commons.

Per ogni scopritore in ``data/scopritori.yaml`` cerca l'entità corrispondente
su Wikidata, ne recupera l'immagine associata (proprietà P18), verifica la
licenza su Wikimedia Commons e scarica il ritratto solo se la licenza rientra
nell'allowlist (pubblico dominio o CC0). Lo script è tollerante ai fallimenti
di rete o di dati mancanti su un singolo scopritore: un errore isolato non
interrompe l'elaborazione degli altri, ma viene riportato nel riepilogo
finale.

Il rate limiting (``PAUSA_FRA_RICHIESTE`` in ``elements_caos.ingest.ritratti``)
rende il processo lento con decine di scopritori: è un compromesso
deliberato per non sovraccaricare le API pubbliche di Wikimedia.
"""

import sys
from pathlib import Path

import yaml

from elements_caos.ingest.ritratti import (
    cerca_entita_wikidata,
    interroga_licenza_commons,
    licenza_ammessa,
    recupera_immagine_wikidata,
    scarica_ritratto,
)
from elements_caos.models import Ritratto, Scopritore

PERCORSO_SCOPRITORI = Path("data/scopritori.yaml")
CARTELLA_IMMAGINI = Path("data/images")


def _estensione(nome_file_commons: str) -> str:
    """Ricava l'estensione del file immagine, in minuscolo."""
    return Path(nome_file_commons).suffix.lower()


def popola_ritratto(scopritore: Scopritore) -> tuple[str, str, Ritratto | None]:
    """Cerca e scarica il ritratto di uno scopritore, se disponibile e ammesso.

    Restituisce una tripla (esito, dettaglio, ritratto) dove esito è uno fra
    "scaricato", "nessuna_immagine", "licenza_scartata", "entita_non_trovata"
    o "errore", pensata per essere aggregata nel riepilogo finale. Il terzo
    elemento è il ``Ritratto`` scaricato solo quando l'esito è "scaricato",
    altrimenti ``None``: il chiamante lo scrive in ``scopritori.yaml``, senza
    il quale il ritratto scaricato non verrebbe mai collegato dal rendering
    (che legge il campo ``ritratto`` dello scopritore, non la sola presenza
    del file su disco).
    """
    qid = cerca_entita_wikidata(scopritore.nome)
    if qid is None:
        return "entita_non_trovata", scopritore.nome, None

    nome_file_commons = recupera_immagine_wikidata(qid)
    if nome_file_commons is None:
        return "nessuna_immagine", scopritore.nome, None

    info = interroga_licenza_commons(nome_file_commons)
    if info is None:
        return "nessuna_immagine", scopritore.nome, None

    if not licenza_ammessa(info.licenza):
        return "licenza_scartata", f"{scopritore.nome}: {info.licenza!r}", None

    destinazione = CARTELLA_IMMAGINI / f"{scopritore.id}{_estensione(nome_file_commons)}"
    ritratto = scarica_ritratto(info, destinazione)
    return "scaricato", scopritore.nome, ritratto


def main() -> int:
    """Elabora tutti gli scopritori, scrive i ritratti trovati e stampa il riepilogo.

    Il file ``scopritori.yaml`` viene riscritto solo se almeno un ritratto è
    stato scaricato, e solo con il campo ``ritratto`` aggiunto alle voci
    interessate: gli altri campi (incluso l'ordine delle voci) restano
    invariati, così da non introdurre differenze superflue nel diff.
    """
    dati = yaml.safe_load(PERCORSO_SCOPRITORI.read_text(encoding="utf-8")) or []
    scopritori = [Scopritore.model_validate(voce) for voce in dati]

    esiti: dict[str, list[str]] = {
        "scaricato": [],
        "nessuna_immagine": [],
        "licenza_scartata": [],
        "entita_non_trovata": [],
        "errore": [],
    }
    ritratti_trovati: dict[str, Ritratto] = {}

    for scopritore in scopritori:
        try:
            esito, dettaglio, ritratto = popola_ritratto(scopritore)
        except Exception as errore:  # noqa: BLE001 — un errore isolato non deve fermare il ciclo
            esito, dettaglio, ritratto = "errore", f"{scopritore.nome}: {errore}", None
        esiti[esito].append(dettaglio)
        if ritratto is not None:
            ritratti_trovati[scopritore.id] = ritratto
        print(f"[{esito}] {dettaglio}")

    if ritratti_trovati:
        for voce in dati:
            ritratto = ritratti_trovati.get(voce["id"])
            if ritratto is not None:
                voce["ritratto"] = ritratto.model_dump()
        PERCORSO_SCOPRITORI.write_text(
            yaml.safe_dump(dati, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    print()
    print("Riepilogo:")
    print(f"  Ritratti scaricati: {len(esiti['scaricato'])}")
    print(f"  Nessuna immagine su Wikidata: {len(esiti['nessuna_immagine'])}")
    print(f"  Licenza non ammessa: {len(esiti['licenza_scartata'])}")
    print(f"  Entità non trovata su Wikidata: {len(esiti['entita_non_trovata'])}")
    print(f"  Errori: {len(esiti['errore'])}")
    print(f"  Totale scopritori elaborati: {len(scopritori)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
