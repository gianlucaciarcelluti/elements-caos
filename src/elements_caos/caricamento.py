"""Caricamento dei dati del vault dagli archivi YAML.

Gli errori di lettura e di validazione vengono racchiusi in ``ErroreCaricamento``
citando sempre il file di origine, così che un dato malformato sia rintracciabile
senza dover interpretare la traccia di stack.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from elements_caos.models import Elemento, Epoca, Scopritore


class ErroreCaricamento(Exception):
    """Errore nella lettura o nella validazione di un file di dati."""


def _leggi_yaml(percorso: Path) -> Any:
    """Legge un file YAML restituendone il contenuto deserializzato."""
    if not percorso.exists():
        raise ErroreCaricamento(f"file non trovato: {percorso}")
    try:
        with percorso.open(encoding="utf-8") as sorgente:
            return yaml.safe_load(sorgente)
    except yaml.YAMLError as errore:
        raise ErroreCaricamento(f"YAML non valido in {percorso.name}: {errore}") from errore


def carica_elemento(percorso: Path) -> Elemento:
    """Carica e valida un singolo elemento a partire dal suo file YAML."""
    dati = _leggi_yaml(percorso)
    try:
        return Elemento.model_validate(dati)
    except ValidationError as errore:
        raise ErroreCaricamento(f"dati non validi in {percorso.name}: {errore}") from errore


def carica_elementi(cartella: Path) -> list[Elemento]:
    """Carica tutti gli elementi di una cartella, ordinati per numero atomico."""
    if not cartella.is_dir():
        raise ErroreCaricamento(f"cartella non trovata: {cartella}")
    elementi = [carica_elemento(percorso) for percorso in sorted(cartella.glob("*.yaml"))]
    return sorted(elementi, key=lambda elemento: elemento.numero_atomico)


def carica_scopritori(percorso: Path) -> dict[str, Scopritore]:
    """Carica l'anagrafica degli scopritori, indicizzata per identificativo."""
    dati = _leggi_yaml(percorso)
    if not isinstance(dati, list):
        tipo = "nessun contenuto (file vuoto)" if dati is None else type(dati).__name__
        raise ErroreCaricamento(f"atteso un elenco in {percorso.name}, trovato {tipo}")
    try:
        scopritori = [Scopritore.model_validate(voce) for voce in dati]
    except ValidationError as errore:
        raise ErroreCaricamento(f"dati non validi in {percorso.name}: {errore}") from errore
    return {scopritore.id: scopritore for scopritore in scopritori}


def carica_epoche(percorso: Path) -> dict[str, Epoca]:
    """Carica la definizione delle epoche storiche, indicizzata per identificativo."""
    dati = _leggi_yaml(percorso)
    if not isinstance(dati, list):
        tipo = "nessun contenuto (file vuoto)" if dati is None else type(dati).__name__
        raise ErroreCaricamento(f"atteso un elenco in {percorso.name}, trovato {tipo}")
    try:
        epoche = [Epoca.model_validate(voce) for voce in dati]
    except ValidationError as errore:
        raise ErroreCaricamento(f"dati non validi in {percorso.name}: {errore}") from errore
    return {epoca.id: epoca for epoca in epoche}


def ordina_per_scoperta(elementi: list[Elemento]) -> list[Elemento]:
    """Ordina gli elementi cronologicamente per anno di scoperta.

    A parità di anno si usa il numero atomico come criterio secondario, per
    garantire un ordinamento stabile e riproducibile fra le generazioni.
    """
    return sorted(elementi, key=lambda e: (e.scoperta.anno, e.numero_atomico))
