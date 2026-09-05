"""Test della generazione delle note di navigazione del vault."""

from pathlib import Path

from elements_caos.caricamento import carica_elementi, carica_epoche, carica_scopritori
from elements_caos.models import Tappa
from elements_caos.render.navigazione import (
    rendi_attribuzioni,
    rendi_cronologia,
    rendi_epoca,
    rendi_scopritore,
    rendi_tavola,
)

DATI_PROVA = Path(__file__).parent / "dati_prova"


def _elementi():
    """Carica gli elementi dei dati di prova."""
    return carica_elementi(DATI_PROVA / "elements")


def _scopritori():
    """Carica gli scopritori dei dati di prova."""
    return carica_scopritori(DATI_PROVA / "scopritori.yaml")


def test_cronologia_elenca_gli_elementi_in_ordine_di_scoperta() -> None:
    """La cronologia elenca gli elementi con posizione, anno e wikilink."""
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")

    risultato = rendi_cronologia(_elementi(), epoche, [], _scopritori())

    assert "[[Fosforo]]" in risultato
    assert "1669" in risultato


def test_cronologia_mostra_i_nomi_degli_scopritori_non_gli_id() -> None:
    """La tabella della cronologia mostra i nomi propri, non gli id kebab-case."""
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")

    risultato = rendi_cronologia(_elementi(), epoche, [], _scopritori())

    assert "Hennig Brand" in risultato
    assert "hennig-brand" not in risultato


def test_cronologia_include_itinerario_guidato() -> None:
    """Le tappe dell'itinerario compaiono come percorso di lettura consigliato."""
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")
    tappe = [
        Tappa(
            titolo="L'alchimista e la luce fredda",
            elemento="Fosforo",
            descrizione="La prima scoperta documentata di un elemento.",
        ),
    ]

    risultato = rendi_cronologia(_elementi(), epoche, tappe, _scopritori())

    assert "Itinerario guidato" in risultato
    assert "L'alchimista e la luce fredda" in risultato
    assert "[[Fosforo]]" in risultato


def test_cronologia_raggruppa_per_epoca() -> None:
    """Gli elementi sono raggruppati sotto l'intestazione della loro epoca."""
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")

    risultato = rendi_cronologia(_elementi(), epoche, [], _scopritori())

    assert "Alchimia e primo moderno" in risultato


def test_epoca_elenca_i_suoi_elementi() -> None:
    """La nota di un'epoca elenca gli elementi scoperti in quel periodo."""
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")

    risultato = rendi_epoca(epoche["alchimia"], _elementi(), _scopritori())

    assert "[[Fosforo]]" in risultato
    assert "Alchimia e primo moderno" in risultato


def test_epoca_mostra_i_nomi_degli_scopritori_non_gli_id() -> None:
    """La tabella di un'epoca mostra i nomi propri, non gli id kebab-case."""
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")

    risultato = rendi_epoca(epoche["alchimia"], _elementi(), _scopritori())

    assert "Hennig Brand" in risultato
    assert "hennig-brand" not in risultato


def test_epoca_senza_elementi_non_solleva_errore() -> None:
    """Un'epoca priva di elementi produce comunque una nota valida."""
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")

    risultato = rendi_epoca(epoche["antichita"], _elementi(), _scopritori())

    assert "Antichità" in risultato


def test_scopritore_elenca_le_sue_scoperte() -> None:
    """La nota di uno scopritore elenca gli elementi che gli sono attribuiti."""
    scopritori = _scopritori()

    risultato = rendi_scopritore(scopritori["hennig-brand"], _elementi(), scopritori)

    assert "Hennig Brand" in risultato
    assert "[[Fosforo]]" in risultato


def test_scopritore_mostra_il_ritratto_se_presente() -> None:
    """Se il ritratto è disponibile, la nota lo incorpora con l'attribuzione."""
    scopritori = _scopritori()

    risultato = rendi_scopritore(scopritori["hennig-brand"], _elementi(), scopritori)

    assert "hennig-brand.jpg" in risultato
    assert "Joseph Wright of Derby" in risultato


def test_tavola_contiene_tutti_gli_elementi_come_wikilink() -> None:
    """La tavola periodica rimanda a ciascun elemento tramite wikilink.

    Il pipe dell'alias è escapato (``\\|``): la cella vive dentro una riga di
    tabella Markdown, dove un pipe libero verrebbe letto come separatore di
    colonna e spezzerebbe la riga.
    """
    risultato = rendi_tavola(_elementi(), _scopritori())

    assert "[[Fosforo\\|P]]" in risultato


def test_attribuzioni_elenca_le_licenze() -> None:
    """La pagina delle attribuzioni riporta autore, licenza e fonte di ogni immagine."""
    scopritori = carica_scopritori(DATI_PROVA / "scopritori.yaml")

    risultato = rendi_attribuzioni(scopritori)

    assert "Joseph Wright of Derby" in risultato
    assert "PD-old-100-expired" in risultato
    assert "commons.wikimedia.org" in risultato
