"""Test dell'indice di ricerca, dell'RSS, della sitemap e della 404.

Sono le quattro cose che Quartz dava per scontate e che ora vanno costruite.
L'indice ha un tetto di peso: oltre una certa soglia la ricerca client-side
smette di essere una buona idea, e va ripensata invece che subita.
"""

import json
import xml.etree.ElementTree as ElementTree
from pathlib import Path

from elements_caos.caricamento import (
    carica_elementi,
    carica_epoche,
    carica_itinerario,
    carica_scopritori,
)
from elements_caos.sito.indice import (
    BASE_URL,
    PESO_MASSIMO_INDICE,
    URL_404,
    URL_INDICE,
    URL_RSS,
    URL_SITEMAP,
    costruisci_indice,
    rendi_404,
    rendi_rss,
    rendi_sitemap,
    voci_indice,
)

DATI = Path(__file__).resolve().parents[1] / "data"


def _dati() -> tuple:
    """Carica tutto ciò che entra nell'indice."""
    return (
        carica_elementi(DATI / "elements"),
        carica_epoche(DATI / "epoche.yaml"),
        carica_scopritori(DATI / "scopritori.yaml"),
    )


def _voci() -> list[dict]:
    """Le voci dell'indice sui dati reali."""
    elementi, epoche, scopritori = _dati()
    return voci_indice(elementi, epoche, scopritori)


# --- L'indice ----------------------------------------------------------------


def test_l_indice_copre_tutte_le_pagine_cercabili() -> None:
    """118 elementi, 100 scopritori, 6 epoche: tutto ciò che ha un nome."""
    elementi, epoche, scopritori = _dati()

    assert len(_voci()) == len(elementi) + len(scopritori) + len(epoche)


def test_ogni_voce_ha_titolo_e_indirizzo() -> None:
    """Una voce senza indirizzo non è raggiungibile, e quindi non serve."""
    for voce in _voci():
        assert voce["t"], "voce senza titolo"
        assert voce["u"], f"voce senza indirizzo: {voce['t']}"


def test_l_elemento_si_trova_per_simbolo_nome_inglese_anno_e_scopritore() -> None:
    """Sono i quattro modi in cui si cerca un elemento senza saperne il nome."""
    fosforo = next(v for v in _voci() if v["t"] == "Fosforo")
    cercabile = " ".join([fosforo["t"], fosforo.get("k", "")]).lower()

    assert "p" in cercabile.split()
    assert "phosphorus" in cercabile
    assert "1669" in cercabile
    assert "brand" in cercabile


def test_l_indice_e_json_valido_e_compatto() -> None:
    """Il JSON viaggia a ogni ricerca: le chiavi sono corte di proposito."""
    elementi, epoche, scopritori = _dati()

    grezzo = costruisci_indice(elementi, epoche, scopritori)
    dati = json.loads(grezzo)

    assert isinstance(dati, list)
    assert ", " not in grezzo, "il JSON non è compatto"


def test_l_indice_resta_sotto_il_tetto_di_peso() -> None:
    """Oltre la soglia la ricerca client-side va ripensata, non subita.

    Il tetto è dichiarato nel codice: se un giorno viene superato, questo test
    lo dice prima che il sito cominci a servire mezzo megabyte a ogni visita.
    """
    elementi, epoche, scopritori = _dati()

    peso = len(costruisci_indice(elementi, epoche, scopritori).encode("utf-8"))

    assert peso <= PESO_MASSIMO_INDICE, (
        f"l'indice pesa {peso / 1024:.0f} KB, oltre il tetto di {PESO_MASSIMO_INDICE / 1024:.0f} KB"
    )


# --- RSS ---------------------------------------------------------------------


def test_l_rss_e_xml_valido() -> None:
    """Un feed malformato è peggio di nessun feed."""
    elementi, epoche, scopritori = _dati()

    radice = ElementTree.fromstring(rendi_rss(elementi))

    assert radice.tag == "rss"
    assert radice.find("channel") is not None


def test_l_rss_segue_l_ordine_della_scoperta() -> None:
    """È l'ordine del progetto: il più recente per primo, come vuole un feed.

    «Recente» qui significa scoperto per ultimo, non pubblicato per ultimo: il
    vault non ha una data di pubblicazione, e inventarla sarebbe falso.
    """
    elementi, epoche, scopritori = _dati()

    canale = ElementTree.fromstring(rendi_rss(elementi)).find("channel")
    titoli = [voce.find("title").text for voce in canale.findall("item")]

    assert titoli[0].startswith("Tennesso")
    assert titoli[-1].startswith("Oro")


def test_l_rss_usa_indirizzi_assoluti() -> None:
    """Un feed si legge fuori dal sito: i collegamenti relativi non funzionano."""
    elementi, epoche, scopritori = _dati()

    canale = ElementTree.fromstring(rendi_rss(elementi)).find("channel")

    for voce in canale.findall("item"):
        assert voce.find("link").text.startswith(BASE_URL)


# --- Sitemap -----------------------------------------------------------------


def test_la_sitemap_e_xml_valido_e_completa() -> None:
    """Ogni pagina indicizzabile deve comparire."""
    elementi, epoche, scopritori = _dati()
    tappe = carica_itinerario(DATI / "itinerario.yaml")

    grezzo = rendi_sitemap(elementi, epoche, scopritori, tappe)
    spazio = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    radice = ElementTree.fromstring(grezzo)

    indirizzi = [u.find(f"{spazio}loc").text for u in radice.findall(f"{spazio}url")]

    assert len(indirizzi) == len(elementi) + len(scopritori) + len(epoche) + 5
    assert f"{BASE_URL}/" in indirizzi
    assert all(i.startswith(BASE_URL) for i in indirizzi)


def test_la_sitemap_non_elenca_la_404() -> None:
    """Una pagina d'errore nella sitemap è una richiesta di indicizzarla."""
    elementi, epoche, scopritori = _dati()
    tappe = carica_itinerario(DATI / "itinerario.yaml")

    assert "404" not in rendi_sitemap(elementi, epoche, scopritori, tappe)


# --- 404 ---------------------------------------------------------------------


def test_la_404_offre_una_via_d_uscita() -> None:
    """Chi arriva su una pagina che non c'è deve poter ripartire."""
    pagina = rendi_404()

    assert 'href="/elements-caos/cronologia-degli-elementi.html"' in pagina
    assert "intelligenza artificiale" in pagina


def test_la_404_usa_indirizzi_assoluti() -> None:
    """La 404 risponde a qualsiasi profondità: i relativi punterebbero a vuoto.

    Una richiesta a /elementi/inesistente riceve la stessa pagina di una a
    /inesistente, e i collegamenti devono funzionare in entrambi i casi.
    """
    pagina = rendi_404()

    assert 'href="statico/' not in pagina
    assert 'href="../' not in pagina


# --- Il comando li emette ----------------------------------------------------


def test_il_comando_emette_indice_feed_e_sitemap(tmp_path: Path) -> None:
    """I quattro file devono arrivare nella cartella pubblicata."""
    from elements_caos.cli import main

    uscita = tmp_path / "pubblico"
    assert main(["sito", "--dati", str(DATI), "--uscita", str(uscita)]) == 0

    for percorso in (URL_INDICE, URL_RSS, URL_SITEMAP, URL_404):
        assert (uscita / percorso).is_file(), f"manca {percorso}"

    assert (uscita / "statico" / "ricerca.js").is_file()


def test_la_ricerca_non_compare_senza_javascript(tmp_path: Path) -> None:
    """Un campo di ricerca che non cerca è peggio di nessun campo."""
    from elements_caos.cli import main

    uscita = tmp_path / "pubblico"
    main(["sito", "--dati", str(DATI), "--uscita", str(uscita)])

    pagina = (uscita / "index.html").read_text(encoding="utf-8")
    inizio = pagina.index('id="ricerca"')

    assert "hidden" in pagina[max(0, inizio - 300) : inizio + 200]


def test_il_simbolo_ha_un_campo_proprio() -> None:
    """Il simbolo va pesato più delle altre parole cercabili.

    Chi digita «P» cerca il fosforo, non il palladio né i tre scopritori il cui
    nome comincia per p. Misurato nel browser prima di questa correzione: il
    fosforo non compariva fra i primi risultati.
    """
    fosforo = next(v for v in _voci() if v["t"] == "Fosforo")

    assert fosforo["s"] == "P"


def test_solo_gli_elementi_hanno_il_simbolo() -> None:
    """Scopritori ed epoche non ne hanno: il campo non va riempito a vuoto."""
    per_categoria = {v["c"]: v for v in _voci()}

    assert "s" not in per_categoria["scopritore"]
    assert "s" not in per_categoria["epoca"]
