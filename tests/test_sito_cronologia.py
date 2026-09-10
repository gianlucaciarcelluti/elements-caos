"""Test della linea del tempo, che sostituisce le sei tabelle della cronologia.

La pagina che con Quartz era alta 19.143 px — circa ventitré schermate su un
telefono — è quella che il lettore incontra per prima. Qui si verifica che
elenchi tutto, nell'ordine giusto, in una forma che su schermo stretto resti
percorribile.
"""

from pathlib import Path

from elements_caos.caricamento import carica_elementi, carica_epoche
from elements_caos.sito.cronologia import (
    URL_CRONOLOGIA,
    densita_scoperte,
    rendi_cronologia_sito,
    voci_per_epoca,
)

DATI_REALI = Path(__file__).resolve().parents[1] / "data"
DATI_PROVA = Path(__file__).parent / "dati_prova"


def _pagina() -> str:
    """Genera la pagina della cronologia dai dati di prova."""
    elementi = carica_elementi(DATI_PROVA / "elements")
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")
    return rendi_cronologia_sito(elementi, epoche)


def _elementi_reali() -> list:
    """Carica il dataset vero: la cronologia si giudica sui 118 elementi."""
    return carica_elementi(DATI_REALI / "elements")


# --- Struttura ---------------------------------------------------------------


def test_url_invariato() -> None:
    """L'URL è già pubblicato: non può cambiare."""
    assert URL_CRONOLOGIA == "cronologia-degli-elementi.html"


def test_pagina_html_completa() -> None:
    """È un documento, non un frammento."""
    pagina = _pagina()

    assert pagina.startswith("<!DOCTYPE html>")
    assert pagina.count("<h1") == 1


def test_nessuna_tabella() -> None:
    """Le sei tabelle sono ciò che si sta sostituendo."""
    assert "<table" not in _pagina()


def test_porta_l_avvertenza() -> None:
    """Nessuna pagina ne è priva."""
    assert "intelligenza artificiale" in _pagina()


# --- Le epoche ---------------------------------------------------------------


def test_le_epoche_sono_in_ordine_cronologico() -> None:
    """Le sezioni seguono la storia, non l'ordine alfabetico né quello dei dati."""
    elementi = _elementi_reali()
    epoche = carica_epoche(DATI_REALI / "epoche.yaml")

    gruppi = voci_per_epoca(elementi, epoche)
    primi_anni = [gruppo["elementi"][0].scoperta.anno for gruppo in gruppi]

    assert primi_anni == sorted(primi_anni)
    assert [gruppo["epoca"].id for gruppo in gruppi][0] == "antichita"
    assert [gruppo["epoca"].id for gruppo in gruppi][-1] == "nucleare"


def test_ogni_elemento_compare_una_volta_sola() -> None:
    """118 elementi, nessuno perso e nessuno doppio."""
    gruppi = voci_per_epoca(_elementi_reali(), carica_epoche(DATI_REALI / "epoche.yaml"))

    numeri = [e.numero_atomico for gruppo in gruppi for e in gruppo["elementi"]]

    assert len(numeri) == 118
    assert len(set(numeri)) == 118


def test_dentro_l_epoca_l_ordine_e_quello_della_scoperta() -> None:
    """Dentro ogni sezione si legge in ordine di tempo."""
    gruppi = voci_per_epoca(_elementi_reali(), carica_epoche(DATI_REALI / "epoche.yaml"))

    for gruppo in gruppi:
        anni = [e.scoperta.anno for e in gruppo["elementi"]]
        assert anni == sorted(anni), f"epoca {gruppo['epoca'].id} fuori ordine"


# --- La densità delle scoperte ----------------------------------------------


def test_densita_copre_tutti_gli_elementi() -> None:
    """La somma dei secchielli è il totale: nessuna scoperta fuori dall'istogramma."""
    secchielli = densita_scoperte(_elementi_reali())

    assert sum(secchiello["quantita"] for secchiello in secchielli) == 118


def test_densita_conserva_i_periodi_vuoti() -> None:
    """I vuoti sono informazione: fra il 1675 e il 1725 non si scopre nulla.

    Comprimere i periodi senza scoperte darebbe l'impressione di una storia
    continua, che è esattamente il contrario di quello che è successo.
    """
    secchielli = densita_scoperte(_elementi_reali())
    vuoti = [s for s in secchielli if s["quantita"] == 0]

    assert vuoti, "nessun periodo vuoto: i secchielli sono stati compressi"


def test_densita_mostra_i_due_picchi() -> None:
    """L'istogramma deve far vedere dove la storia accelera.

    I due massimi sono l'elettrolisi (1800-1824, quattordici elementi) e la
    stagione dello spettroscopio e della radioattività (1875-1899, diciassette).
    """
    secchielli = {s["inizio"]: s["quantita"] for s in densita_scoperte(_elementi_reali())}

    assert secchielli[1800] == 14
    assert secchielli[1875] == 17


def test_densita_raccoglie_l_antichita_in_un_solo_secchiello() -> None:
    """Quarantamila anni non si dividono in periodi da venticinque.

    Il primo secchiello raccoglie tutto ciò che precede il 1650: sono le
    scoperte senza data certa, e distribuirle su millenni di barre vuote
    renderebbe illeggibile tutto il resto.
    """
    secchielli = densita_scoperte(_elementi_reali())

    assert secchielli[0]["quantita"] == 14
    assert secchielli[0]["inizio"] is None


# --- I collegamenti ----------------------------------------------------------


def test_ogni_voce_rimanda_alla_pagina_dell_elemento() -> None:
    """La cronologia serve a saltare a un elemento: i collegamenti ci devono essere."""
    assert 'href="elementi/fosforo.html"' in _pagina()


def test_le_voci_portano_il_colore_della_loro_epoca() -> None:
    """Il colore d'epoca lega cronologia, scheda e tavola in un solo sistema."""
    pagina = _pagina()

    assert "epoca--alchimia" in pagina


# --- La compattezza è una scelta, e va difesa -------------------------------


def test_le_pastiglie_stanno_almeno_quattro_per_riga() -> None:
    """La griglia deve restare compatta: è ciò che tiene la pagina percorribile.

    Con 118 voci, ogni voce per riga in meno costa circa ottocento pixel di
    scorrimento. Misurato: a 390 px di viewport, con 16 px di margine per lato,
    servono colonne da non più di 4,8rem perché ne stiano quattro.
    """
    foglio = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "elements_caos"
        / "sito"
        / "statico"
        / "base.css"
    ).read_text(encoding="utf-8")

    inizio = foglio.index(".pastiglie {")
    regola = foglio[inizio : foglio.index("}", inizio)]

    import re

    trovata = re.search(r"minmax\(([\d.]+)rem", regola)
    assert trovata, "la griglia delle pastiglie non dichiara una larghezza minima"
    assert float(trovata.group(1)) <= 4.8


def test_i_nomi_lunghi_non_allargano_la_colonna() -> None:
    """«Rutherfordio» e «protoattinio» devono spezzare, non allargare la griglia."""
    foglio = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "elements_caos"
        / "sito"
        / "statico"
        / "base.css"
    ).read_text(encoding="utf-8")

    inizio = foglio.index(".pastiglia__nome {")
    regola = foglio[inizio : foglio.index("}", inizio)]

    assert "overflow-wrap: anywhere" in regola
