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


def test_cronologia_collega_tavola_e_attribuzioni() -> None:
    """La cronologia, spina dorsale del vault, irradia verso le altre pagine indice.

    Senza questi collegamenti, ``Tavola periodica`` e ``Attribuzioni`` non
    sarebbero raggiungibili da nessun'altra pagina di navigazione generata da
    questo modulo: isole nel grafo, trovabili solo nel file-explorer.
    """
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")

    risultato = rendi_cronologia(_elementi(), epoche, [], _scopritori())

    assert "[[Tavola periodica]]" in risultato
    assert "[[Attribuzioni]]" in risultato


def test_cronologia_collega_l_epoca_con_un_wikilink() -> None:
    """L'intestazione dell'epoca nella cronologia è un wikilink, non solo testo.

    Senza il wikilink la pagina dell'epoca sarebbe raggiungibile solo "in
    discesa" dalle note dei singoli elementi, mai dagli indici: esattamente
    la percorribilità che questo task deve creare.
    """
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")

    risultato = rendi_cronologia(_elementi(), epoche, [], _scopritori())

    assert "[[Alchimia e primo moderno]]" in risultato


def test_cronologia_collega_lo_scopritore_con_un_wikilink() -> None:
    """La colonna scopritore della cronologia contiene un wikilink al suo nome."""
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")

    risultato = rendi_cronologia(_elementi(), epoche, [], _scopritori())

    assert "[[Hennig Brand]]" in risultato


def test_epoca_collega_lo_scopritore_con_un_wikilink() -> None:
    """La colonna scopritore della tabella di un'epoca contiene un wikilink."""
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")

    risultato = rendi_epoca(epoche["alchimia"], _elementi(), _scopritori())

    assert "[[Hennig Brand]]" in risultato


def test_scopritore_non_produce_un_autowikilink_verso_se_stesso() -> None:
    """La pagina di uno scopritore non deve linkare se stessa nella sua tabella.

    ``_voci`` è condivisa con ``rendi_cronologia``/``rendi_epoca``, dove il
    nome dello scopritore va wikilinkato: qui invece il nome coincide con il
    titolo della pagina corrente, e un wikilink sarebbe un auto-riferimento.
    """
    scopritori = _scopritori()

    risultato = rendi_scopritore(scopritori["hennig-brand"], _elementi(), scopritori)

    assert "[[Hennig Brand]]" not in risultato


def test_voci_elemento_senza_scopritori_non_produce_wikilink_ignoto() -> None:
    """Un elemento senza scopritori mostra 'ignoto' come testo, non come wikilink.

    Un wikilink verso una nota inesistente (``[[ignoto]]``) sarebbe un
    collegamento rotto: il caso va distinto da quello con scopritori noti.
    """
    from elements_caos.models import Categoria, Elemento, Proprieta, Scoperta
    from elements_caos.render.navigazione import _voci

    elemento_senza_scopritori = Elemento(
        numero_atomico=26,
        simbolo="Fe",
        nome="Ferro",
        nome_en="Iron",
        scoperta=Scoperta(
            anno=-3000,
            anno_stimato=True,
            scopritori=[],
            epoca="antichita",
        ),
        proprieta=Proprieta(
            gruppo=8,
            periodo=4,
            blocco="d",
            categoria=Categoria.METALLO_DI_TRANSIZIONE,
            massa_atomica=55.845,
            configurazione_elettronica="[Ar] 3d6 4s2",
            gusci=[2, 8, 14, 2],
            stati_ossidazione=[2, 3],
        ),
        approfondimento=False,
        fonti=[],
    )

    voci = _voci([elemento_senza_scopritori], _scopritori())

    assert voci[0].scopritori == "ignoto"
    assert "[[ignoto]]" not in voci[0].scopritori


def test_attribuzioni_senza_ritratti_mostra_messaggio_esplicito() -> None:
    """Se nessuno scopritore ha un ritratto, la pagina mostra un messaggio.

    Coerente con lo stile di ``epoca.md.j2`` e ``scopritore.md.j2``, che in
    casi analoghi (nessun elemento/nessuna scoperta) mostrano un messaggio
    esplicito invece di una tabella vuota con la sola intestazione.
    """
    from elements_caos.models import Scopritore

    scopritori_senza_ritratto = {
        "senza-ritratto": Scopritore(id="senza-ritratto", nome="Anonimo"),
    }

    risultato = rendi_attribuzioni(scopritori_senza_ritratto)

    assert "Nessuna immagine" in risultato
    assert "| Anonimo |" not in risultato
