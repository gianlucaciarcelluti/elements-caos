"""Test delle pagine che il sito deve avere per non perdere URL già pubblicati.

Il piano di ridisegno saltava epoche, scopritori, attribuzioni e la home: sono
108 pagine che il sito costruito con Quartz pubblica dal Task 23, e senza le
quali la sostituzione romperebbe altrettanti collegamenti. Qui si verifica che
ci siano e che portino il loro contenuto.
"""

from pathlib import Path

from elements_caos.caricamento import (
    carica_elementi,
    carica_epoche,
    carica_itinerario,
    carica_scopritori,
)
from elements_caos.sito.contesto import (
    URL_ATTRIBUZIONI,
    URL_HOME,
    rendi_attribuzioni_sito,
    rendi_epoca_sito,
    rendi_home,
    rendi_scopritore_sito,
)
from elements_caos.sito.pagina import url_epoca, url_scopritore

DATI = Path(__file__).resolve().parents[1] / "data"


def _tutto() -> tuple:
    """Carica gli ingredienti comuni a tutte le pagine di contesto."""
    return (
        carica_elementi(DATI / "elements"),
        carica_epoche(DATI / "epoche.yaml"),
        carica_scopritori(DATI / "scopritori.yaml"),
    )


# --- URL: sono già pubblicati e non possono cambiare ------------------------


def test_gli_url_seguono_lo_schema_pubblicato() -> None:
    """Gli stessi percorsi che Quartz serve oggi."""
    elementi, epoche, scopritori = _tutto()

    assert url_epoca("Era nucleare") == "epoche/era-nucleare.html"
    assert url_scopritore(scopritori["hennig-brand"]) == "scopritori/hennig-brand.html"
    assert URL_ATTRIBUZIONI == "attribuzioni.html"
    assert URL_HOME == "index.html"


# --- Epoche ------------------------------------------------------------------


def test_la_pagina_d_epoca_porta_descrizione_ed_estremi() -> None:
    """L'epoca è contesto storico: senza la descrizione è solo un elenco."""
    elementi, epoche, scopritori = _tutto()

    pagina = rendi_epoca_sito(epoche["nucleare"], elementi, scopritori)

    assert "Era nucleare" in pagina
    assert "si fabbricano" in pagina
    assert "1940" in pagina


def test_la_pagina_d_epoca_elenca_i_suoi_elementi_in_ordine() -> None:
    """Gli elementi dell'epoca, in ordine di scoperta."""
    elementi, epoche, scopritori = _tutto()

    pagina = rendi_epoca_sito(epoche["antichita"], elementi, scopritori)

    assert pagina.index("Oro") < pagina.index("Arsenico")
    assert 'href="../elementi/oro.html"' in pagina


def test_ogni_elemento_appartiene_a_un_epoca_esistente() -> None:
    """Un'epoca citata e non definita sarebbe una pagina mancante."""
    elementi, epoche, _ = _tutto()

    for elemento in elementi:
        assert elemento.scoperta.epoca in epoche


# --- Scopritori --------------------------------------------------------------


def test_la_pagina_dello_scopritore_porta_i_suoi_elementi() -> None:
    """Chi ha scoperto cosa: è il senso della pagina."""
    elementi, epoche, scopritori = _tutto()

    pagina = rendi_scopritore_sito(scopritori["hennig-brand"], elementi)

    assert "Hennig Brand" in pagina
    assert 'href="../elementi/fosforo.html"' in pagina


def test_l_anagrafica_ignota_non_si_inventa() -> None:
    """Quattro scopritori hanno date sconosciute: la pagina non deve riempirle.

    È la regola del progetto: ciò che non si sa resta a null e non compare.
    """
    elementi, epoche, scopritori = _tutto()

    senza_date = [s for s in scopritori.values() if s.nato is None and s.morto is None]
    assert senza_date, "nessuno scopritore senza date: la fixture è cambiata"

    pagina = rendi_scopritore_sito(senza_date[0], elementi)

    assert "None" not in pagina


def test_il_ritratto_compare_solo_se_c_e() -> None:
    """Uno scopritore senza ritratto non deve produrre un'immagine rotta."""
    elementi, epoche, scopritori = _tutto()

    senza = next(s for s in scopritori.values() if s.ritratto is None)

    assert "<img" not in rendi_scopritore_sito(senza, elementi)


# --- Attribuzioni ------------------------------------------------------------


def test_le_attribuzioni_elencano_autore_licenza_e_fonte() -> None:
    """È l'obbligo verso chi riusa, e la pagina esiste per quello."""
    elementi, epoche, scopritori = _tutto()

    pagina = rendi_attribuzioni_sito(scopritori)

    con_ritratto = [s for s in scopritori.values() if s.ritratto is not None]
    primo = sorted(con_ritratto, key=lambda s: s.nome)[0]

    assert primo.nome in pagina
    assert primo.ritratto.licenza in pagina
    assert primo.ritratto.fonte in pagina


# --- Home --------------------------------------------------------------------


def test_la_home_indirizza_alle_tre_porte_d_ingresso() -> None:
    """Itinerario, cronologia e tavola: sono i tre modi di entrare nel vault."""
    elementi, epoche, scopritori = _tutto()
    tappe = carica_itinerario(DATI / "itinerario.yaml")

    pagina = rendi_home(elementi, epoche, tappe)

    assert 'href="itinerario.html"' in pagina
    assert 'href="cronologia-degli-elementi.html"' in pagina
    assert 'href="tavola-periodica.html"' in pagina


def test_la_home_non_promette_numeri_sbagliati() -> None:
    """I conteggi in pagina sono calcolati, non scritti a mano."""
    elementi, epoche, scopritori = _tutto()
    tappe = carica_itinerario(DATI / "itinerario.yaml")

    pagina = rendi_home(elementi, epoche, tappe)

    assert "118" in pagina
    assert f"{len(tappe)} tappe" in pagina


def test_ogni_pagina_di_contesto_porta_l_avvertenza() -> None:
    """Vale per tutte, nessuna esclusa."""
    elementi, epoche, scopritori = _tutto()
    tappe = carica_itinerario(DATI / "itinerario.yaml")

    pagine = [
        rendi_home(elementi, epoche, tappe),
        rendi_epoca_sito(epoche["alchimia"], elementi, scopritori),
        rendi_scopritore_sito(scopritori["hennig-brand"], elementi),
        rendi_attribuzioni_sito(scopritori),
    ]

    for pagina in pagine:
        assert "intelligenza artificiale" in pagina


# --- Il comando emette tutto -------------------------------------------------


def test_il_comando_emette_tutte_le_pagine(tmp_path: Path) -> None:
    """Nessun URL pubblicato deve restare senza pagina."""
    from elements_caos.cli import main

    uscita = tmp_path / "pubblico"
    assert main(["sito", "--dati", str(DATI), "--uscita", str(uscita)]) == 0

    attesi = [
        "index.html",
        "cronologia-degli-elementi.html",
        "tavola-periodica.html",
        "itinerario.html",
        "attribuzioni.html",
        "elementi/fosforo.html",
        "epoche/era-nucleare.html",
        "scopritori/hennig-brand.html",
    ]
    for percorso in attesi:
        assert (uscita / percorso).is_file(), f"manca {percorso}"

    # Il totale si deriva dai dati invece di essere una costante: così, se un
    # elemento o uno scopritore viene aggiunto, il test dice cosa manca invece
    # di limitarsi a un numero diverso da quello atteso.
    elementi, epoche, scopritori = _tutto()
    servizio = 5  # home, cronologia, tavola, itinerario, attribuzioni
    atteso = len(elementi) + len(scopritori) + len(epoche) + servizio

    emesse = sorted(p.relative_to(uscita).as_posix() for p in uscita.rglob("*.html"))
    assert len(emesse) == atteso, f"emesse {len(emesse)}, attese {atteso}"
