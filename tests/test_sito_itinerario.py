"""Test dell'itinerario guidato con stato di lettura.

Le dodici tappe scritte al Task 20 diventano una pagina propria, con il tempo
di lettura per tappa e quello che resta. Lo stato di avanzamento vive nel
browser di chi legge: qui si verifica che la pagina sia completa anche senza,
perché è la condizione che rende la funzione una comodità e non un requisito.
"""

from pathlib import Path

from elements_caos.caricamento import carica_elementi, carica_itinerario
from elements_caos.sito.itinerario import (
    URL_ITINERARIO,
    minuti_di_lettura,
    rendi_itinerario_sito,
    tappe_con_elemento,
)

DATI_REALI = Path(__file__).resolve().parents[1] / "data"


def _elementi() -> list:
    """Gli elementi veri: le tappe rimandano a note reali."""
    return carica_elementi(DATI_REALI / "elements")


def _tappe() -> list:
    """Le dodici tappe dell'itinerario."""
    return carica_itinerario(DATI_REALI / "itinerario.yaml")


def _pagina() -> str:
    """Genera la pagina dell'itinerario."""
    return rendi_itinerario_sito(_tappe(), _elementi())


# --- Le tappe ----------------------------------------------------------------


def test_url_dedicato() -> None:
    """L'itinerario ha una pagina propria, che con Quartz non aveva."""
    assert URL_ITINERARIO == "itinerario.html"


def test_ci_sono_tutte_e_dodici_le_tappe() -> None:
    """Dodici tappe, nessuna persa per strada."""
    assert len(tappe_con_elemento(_tappe(), _elementi())) == 12


def test_ogni_tappa_trova_il_suo_elemento() -> None:
    """Una tappa che punta a un elemento inesistente è un collegamento rotto."""
    for voce in tappe_con_elemento(_tappe(), _elementi()):
        assert voce["elemento"] is not None, f"tappa senza elemento: {voce['tappa'].titolo}"


def test_l_ordine_delle_tappe_e_quello_dei_dati() -> None:
    """L'ordine è redazionale e non cronologico: non va riordinato.

    L'uranio è nella tavola dal 1789 ma la sua tappa riguarda il 1896, e per
    questo viene dopo l'argon. Ordinare per anno romperebbe il racconto.
    """
    voci = tappe_con_elemento(_tappe(), _elementi())

    assert [voce["tappa"].elemento for voce in voci] == [t.elemento for t in _tappe()]


def test_la_prima_tappa_e_il_rame_e_l_ultima_l_oganesson() -> None:
    """Gli estremi del percorso: da ciò che si raccoglie a ciò che si costruisce."""
    voci = tappe_con_elemento(_tappe(), _elementi())

    assert voci[0]["elemento"].nome == "Rame"
    assert voci[-1]["elemento"].nome == "Oganesson"


# --- I tempi -----------------------------------------------------------------


def test_ogni_tappa_dichiara_i_suoi_minuti() -> None:
    """Il tempo per tappa è quello della nota che la tappa fa leggere."""
    voci = tappe_con_elemento(_tappe(), _elementi())

    for voce in voci:
        assert voce["minuti"] >= 1


def test_il_totale_si_avvicina_all_ora_promessa() -> None:
    """L'itinerario è presentato come «circa un'ora»: dev'essere vero.

    Se il totale uscisse dalla forbice, o si cambia la promessa o si cambia il
    percorso — ma le due cose non possono divergere in silenzio.
    """
    totale = minuti_di_lettura(_tappe(), _elementi())

    assert 40 <= totale <= 80, f"{totale} minuti: non è più «circa un'ora»"


# --- La pagina ---------------------------------------------------------------


def test_la_pagina_e_completa_senza_javascript() -> None:
    """Senza stato salvato si vedono tutte le tappe, non una pagina vuota."""
    pagina = _pagina()

    assert pagina.count('class="tappa"') == 12
    assert "Rame" in pagina
    assert "Oganesson" in pagina


def test_le_tappe_rimandano_alle_note() -> None:
    """Una tappa senza il suo collegamento non fa leggere nulla."""
    assert 'href="elementi/rame.html"' in _pagina()


def test_lo_stato_di_lettura_e_locale() -> None:
    """Lo stato resta nel browser: non esiste un server a cui mandarlo."""
    pagina = _pagina()

    assert "fetch(" not in pagina
    assert "navigator.sendBeacon" not in pagina


def test_porta_l_avvertenza() -> None:
    """Nessuna pagina ne è priva."""
    assert "intelligenza artificiale" in _pagina()


# --- Lo script dell'avanzamento ---------------------------------------------


def _script() -> str:
    """Legge lo script dell'itinerario."""
    return (
        Path(__file__).resolve().parents[1]
        / "src"
        / "elements_caos"
        / "sito"
        / "statico"
        / "itinerario.js"
    ).read_text(encoding="utf-8")


def test_lo_storage_e_sempre_protetto() -> None:
    """In navigazione privata l'accesso a localStorage può sollevare eccezione.

    Ogni lettura e ogni scrittura devono stare in try/catch: senza, la pagina
    smette di funzionare proprio per chi ha alzato le difese del browser.
    """
    script = _script()

    assert script.count("try {") >= 2
    assert script.count("catch") >= 2


def test_lo_script_non_manda_nulla_fuori() -> None:
    """Nessun tracciamento: il sito ha dichiarato di non raccogliere nulla."""
    script = _script()

    assert "fetch(" not in script
    assert "XMLHttpRequest" not in script
    assert "sendBeacon" not in script
