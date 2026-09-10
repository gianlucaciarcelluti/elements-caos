"""Test della tavola periodica che si riempie nell'ordine della scoperta.

È la pagina che dice la tesi del progetto meglio di qualunque paragrafo: si
trascina un anno e le caselle si accendono nell'ordine in cui l'umanità le ha
riempite. Qui si verifica che la griglia sia corretta, che i dati coincidano
con la catena cronologica e che la pagina resti utile senza JavaScript.
"""

from pathlib import Path

from elements_caos.caricamento import carica_elementi, carica_epoche, ordina_per_scoperta
from elements_caos.sito.tavola import (
    RIGA_ATTINIDI,
    RIGA_LANTANIDI,
    URL_TAVOLA,
    caselle,
    posizione_griglia,
    rendi_tavola_sito,
)

DATI_REALI = Path(__file__).resolve().parents[1] / "data"


def _elementi() -> list:
    """La tavola periodica si giudica solo sul dataset completo."""
    return carica_elementi(DATI_REALI / "elements")


def _pagina() -> str:
    """Genera la pagina della tavola dai dati reali."""
    return rendi_tavola_sito(_elementi(), carica_epoche(DATI_REALI / "epoche.yaml"))


def _per_numero(numero: int) -> object:
    """Restituisce l'elemento con il numero atomico indicato."""
    return next(e for e in _elementi() if e.numero_atomico == numero)


# --- La griglia --------------------------------------------------------------


def test_url_invariato() -> None:
    """L'URL è già pubblicato con Quartz."""
    assert URL_TAVOLA == "tavola-periodica.html"


def test_gli_estremi_stanno_agli_angoli() -> None:
    """Idrogeno in alto a sinistra, elio in alto a destra, oganesson in fondo."""
    assert posizione_griglia(_per_numero(1)) == (1, 1)
    assert posizione_griglia(_per_numero(2)) == (18, 1)
    assert posizione_griglia(_per_numero(118)) == (18, 7)


def test_lutezio_e_laurenzio_restano_nella_tavola_principale() -> None:
    """Nel dataset lutezio e laurenzio sono blocco d: stanno in gruppo 3.

    È la convenzione IUPAC, e non è universale — molte tavole scolastiche
    mettono lantanio e attinio in gruppo 3 ed estraggono lutezio e laurenzio.
    La griglia segue i dati, non l'abitudine.
    """
    assert posizione_griglia(_per_numero(71)) == (3, 6)
    assert posizione_griglia(_per_numero(103)) == (3, 7)


def test_i_blocchi_f_vanno_nelle_due_righe_separate() -> None:
    """I ventotto del blocco f starebbero tutti in due caselle: vanno estratti.

    Lantanio e attinio aprono le due file dalla terza colonna; itterbio e
    nobelio le chiudono alla sedicesima.
    """
    assert posizione_griglia(_per_numero(57)) == (3, RIGA_LANTANIDI)
    assert posizione_griglia(_per_numero(70)) == (16, RIGA_LANTANIDI)
    assert posizione_griglia(_per_numero(89)) == (3, RIGA_ATTINIDI)
    assert posizione_griglia(_per_numero(102)) == (16, RIGA_ATTINIDI)


def test_nessuna_casella_ospita_due_elementi() -> None:
    """Centodiciotto elementi, centodiciotto posizioni distinte."""
    posizioni = [posizione_griglia(elemento) for elemento in _elementi()]

    assert len(posizioni) == 118
    assert len(set(posizioni)) == 118


# --- Le caselle --------------------------------------------------------------


def test_ci_sono_tutte_e_centodiciotto_le_caselle() -> None:
    """Nessun elemento manca dalla tavola."""
    assert len(caselle(_elementi())) == 118


def test_le_caselle_seguono_la_catena_cronologica() -> None:
    """La posizione cronologica di ogni casella è quella della catena.

    Se le due divergessero, lo scorrevole accenderebbe le caselle in un ordine
    che non è quello della scoperta, cioè direbbe una cosa falsa.
    """
    elementi = _elementi()
    atteso = [e.numero_atomico for e in ordina_per_scoperta(elementi)]

    per_posizione = sorted(caselle(elementi), key=lambda c: c["posizione"])

    assert [c["numero_atomico"] for c in per_posizione] == atteso
    assert [c["posizione"] for c in per_posizione] == list(range(1, 119))


def test_ogni_casella_porta_nome_simbolo_e_anno() -> None:
    """È il nome accessibile che un lettore di schermo annuncia."""
    prima = next(c for c in caselle(_elementi()) if c["numero_atomico"] == 15)

    assert prima["simbolo"] == "P"
    assert "Fosforo" in prima["descrizione"]
    assert "1669" in prima["descrizione"]


# --- La pagina ---------------------------------------------------------------


def test_la_tavola_e_completa_anche_senza_javascript() -> None:
    """Le 118 caselle sono nell'HTML: senza JS la pagina è già utile."""
    pagina = _pagina()

    # Il conteggio è sulla classe esatta: "casella__numero" e gli altri
    # elementi interni cominciano con la stessa stringa.
    assert pagina.count('class="casella epoca--') == 118
    assert "Oganesson" in pagina


def test_lo_scorrevole_e_sulla_posizione_non_sull_anno() -> None:
    """Una scala di anni da -40000 a 2010 è inservibile.

    Il novanta per cento della corsa coprirebbe la preistoria e gli ultimi due
    secoli — dove succede quasi tutto — starebbero negli ultimi pixel.
    """
    pagina = _pagina()

    assert 'type="range"' in pagina
    assert 'min="1"' in pagina
    assert 'max="118"' in pagina


def test_lo_scorrevole_nasce_nascosto() -> None:
    """Senza JS non farebbe nulla, e un comando inerte è peggio di uno assente."""
    pagina = _pagina()

    inizio = pagina.index('type="range"')
    contenitore = pagina[max(0, inizio - 400) : inizio]

    assert "hidden" in contenitore


def test_lo_stato_e_annunciato_ai_lettori_di_schermo() -> None:
    """Trascinando lo scorrevole cambia qualcosa: va detto anche a chi non vede."""
    assert 'aria-live="polite"' in _pagina()


def test_i_dati_cronologici_sono_incorporati_nella_pagina() -> None:
    """Nessuna richiesta di rete: la tavola funziona anche offline."""
    pagina = _pagina()

    assert "data-posizione=" in pagina
    assert "fetch(" not in pagina


def test_porta_l_avvertenza() -> None:
    """Nessuna pagina ne è priva."""
    assert "intelligenza artificiale" in _pagina()


# --- Lingua ------------------------------------------------------------------


def test_le_preposizioni_articolate_seguono_l_italiano() -> None:
    """«all'tennesso» è quello che esce concatenando a mano: serve la regola.

    Le regole sono le stesse per ogni preposizione, cambia solo il prefisso.
    """
    from elements_caos.render.diagrammi import preposizione_articolata

    assert preposizione_articolata("a", "Tennesso") == "al "
    assert preposizione_articolata("a", "Oro") == "all'"
    assert preposizione_articolata("a", "Zolfo") == "allo "
    assert preposizione_articolata("da", "Oro") == "dall'"
    assert preposizione_articolata("da", "Stagno") == "dallo "
    assert preposizione_articolata("de", "Fosforo") == "del "


def test_l_introduzione_non_sbaglia_l_elisione() -> None:
    """Il testo generato deve leggersi in italiano.

    Il confronto è sul testo decodificato: l'autoescape trasforma l'apostrofo
    in `&#39;`, e cercarlo così nel sorgente renderebbe il test illeggibile.
    """
    import html

    testo = html.unescape(_pagina())

    assert "all'tennesso" not in testo
    assert "al tennesso" in testo
    assert "dall'oro" in testo
