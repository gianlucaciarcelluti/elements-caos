"""Test della home: la tavola che si accende scorrendo le epoche.

La home è la tesi del progetto resa come esperienza: un palco fisso con la
tavola periodica, e otto passi — vuota, sei epoche, oggi — che la accendono
nell'ordine della scoperta. I test fissano ciò che deve restare vero anche
quando il CSS cambia: l'ordine di accensione è quello della catena
cronologica, i passi coincidono con le epoche dei dati, e senza JavaScript la
pagina mostra lo stato completo.
"""

import html
import re
from functools import cache
from pathlib import Path

from elements_caos.caricamento import (
    carica_elementi,
    carica_epoche,
    carica_itinerario,
    ordina_per_scoperta,
)
from elements_caos.sito.home import passi_del_racconto, rendi_home

DATI = Path(__file__).resolve().parents[1] / "data"
STATICI = Path(__file__).resolve().parents[1] / "src" / "elements_caos" / "sito" / "statico"


@cache
def _ingredienti() -> tuple:
    """Gli ingredienti della home, caricati una volta sola per il modulo."""
    return (
        carica_elementi(DATI / "elements"),
        carica_epoche(DATI / "epoche.yaml"),
        carica_itinerario(DATI / "itinerario.yaml"),
    )


@cache
def _home() -> str:
    elementi, epoche, tappe = _ingredienti()
    return rendi_home(elementi, epoche, tappe)


def _solo_testo(pagina: str) -> str:
    """Il testo della pagina senza i tag: i numeri si leggono, non si marcano."""
    return html.unescape(re.sub(r"<[^>]+>", "", pagina))


# --- Le porte restano ---------------------------------------------------------


def test_la_home_indirizza_alle_tre_porte_d_ingresso() -> None:
    """Itinerario, cronologia e tavola: sono i tre modi di entrare nel vault."""
    pagina = _home()

    assert 'href="itinerario.html"' in pagina
    assert 'href="cronologia-degli-elementi.html"' in pagina
    assert 'href="tavola-periodica.html"' in pagina


def test_la_home_non_promette_numeri_sbagliati() -> None:
    """I conteggi in pagina sono calcolati, non scritti a mano."""
    elementi, epoche, tappe = _ingredienti()
    pagina = rendi_home(elementi, epoche, tappe)

    testo = _solo_testo(pagina)
    assert "118 elementi" in testo
    assert f"{len(tappe)} tappe" in testo
    assert f"{len(epoche)} epoche" in testo


# --- Il palco -----------------------------------------------------------------


def test_il_palco_porta_le_caselle_nell_ordine_della_catena_cronologica() -> None:
    """Le 118 caselle dichiarano la posizione cronologica della catena.

    È il valore su cui la pagina accende le caselle: se divergesse dall'ordine
    reale, la tavola racconterebbe una storia diversa da quella del vault.
    """
    elementi, _, _ = _ingredienti()
    pagina = _home()

    palco = pagina[pagina.index('class="palco"') : pagina.index('class="passi"')]
    posizioni = re.findall(r'data-posizione="(\d+)"[^>]*data-numero="(\d+)"', palco)
    assert len(posizioni) == 118

    attese = {e.numero_atomico: i for i, e in enumerate(ordina_per_scoperta(elementi), start=1)}
    for posizione, numero in posizioni:
        assert int(posizione) == attese[int(numero)], f"Z={numero} in posizione {posizione}"


def test_senza_javascript_nessuna_casella_e_spenta() -> None:
    """Il markup è lo stato completo: spegnere le caselle è compito del JS."""
    pagina = _home()

    assert "casella--spenta" not in pagina
    assert "118 / 118 elementi" in _solo_testo(pagina)


def test_la_striscia_ha_una_tacca_per_elemento_in_ordine() -> None:
    """La striscia sotto la tavola è la densità della storia sull'asse del progetto."""
    pagina = _home()

    striscia = pagina[pagina.index('class="striscia"') : pagina.index('class="passi"')]
    tacche = re.findall(r'class="tacca epoca--(\w+)" data-posizione="(\d+)"', striscia)
    assert [int(p) for _, p in tacche] == list(range(1, 119))


# --- I passi ------------------------------------------------------------------


def test_i_passi_sono_vuota_sei_epoche_e_oggi() -> None:
    """Otto passi, e il limite di ciascuno è l'ultimo elemento della sua epoca."""
    elementi, epoche, _ = _ingredienti()
    cronologia = ordina_per_scoperta(elementi)

    passi = passi_del_racconto(elementi, epoche)

    assert [p["id"] for p in passi] == [
        "inizio",
        "antichita",
        "alchimia",
        "pneumatica",
        "elettrolisi",
        "spettroscopia",
        "nucleare",
        "oggi",
    ]
    assert passi[0]["fino"] == 0
    assert passi[-1]["fino"] == 118
    for passo in passi[1:-1]:
        della_epoca = [
            i for i, e in enumerate(cronologia, start=1) if e.scoperta.epoca == passo["id"]
        ]
        ultimo = max(della_epoca)
        assert passo["fino"] == ultimo, passo["id"]
        assert passo["quanti"] == sum(1 for e in cronologia if e.scoperta.epoca == passo["id"])


def test_i_passi_delle_epoche_usano_la_descrizione_dei_dati() -> None:
    """Il testo di un'epoca sta in epoche.yaml, non nel template."""
    elementi, epoche, _ = _ingredienti()
    pagina = _home()

    testo = _solo_testo(pagina)
    for epoca in epoche.values():
        assert epoca.descrizione.split(".")[0] in testo, epoca.id
    assert 'data-fino="0"' in pagina
    assert 'data-fino="118"' in pagina


def test_ogni_passo_dichiara_la_sua_epoca_per_il_colore() -> None:
    """Il colore d'epoca del passo è l'accento della pagina mentre lo si legge."""
    pagina = _home()

    epoche = ("antichita", "alchimia", "pneumatica", "elettrolisi", "spettroscopia", "nucleare")
    for epoca in epoche:
        assert f'class="passo epoca--{epoca}"' in pagina


# --- Lo script ----------------------------------------------------------------


def test_lo_script_della_home_esiste_ed_e_collegato() -> None:
    """Senza, la tavola resta accesa: utile, ma non è la home promessa."""
    pagina = _home()

    assert (STATICI / "home.js").is_file()
    assert 'src="statico/home.js"' in pagina
    script = (STATICI / "home.js").read_text(encoding="utf-8")
    assert "IntersectionObserver" in script
    assert "prefers-reduced-motion" in script
