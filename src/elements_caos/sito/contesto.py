"""Pagine di contesto del sito: home, epoche, scopritori e attribuzioni.

Sono le pagine che il piano di ridisegno aveva saltato e che il sito costruito
con Quartz pubblica dal Task 23: senza, la sostituzione romperebbe 108
collegamenti già raggiungibili.
"""

from typing import Any

from elements_caos.caricamento import ordina_per_scoperta
from elements_caos.models import Elemento, Epoca, Scopritore, Tappa
from elements_caos.render.diagrammi import formatta_anno, preposizione_articolata
from elements_caos.sito.pagina import (
    ambiente_sito,
    url_elemento,
    url_epoca,
    url_scopritore,
)

URL_HOME = "index.html"
URL_ATTRIBUZIONI = "attribuzioni.html"


def _voci_elementi(elementi: list[Elemento]) -> list[dict[str, Any]]:
    """Riduce un elenco di elementi alle informazioni che una pagina di contesto mostra."""
    return [
        {
            "elemento": elemento,
            "anno": formatta_anno(elemento.scoperta.anno),
            "url": url_elemento(elemento),
            "epoca": elemento.scoperta.epoca,
        }
        for elemento in elementi
    ]


def rendi_epoca_sito(
    epoca: Epoca, elementi: list[Elemento], scopritori: dict[str, Scopritore]
) -> str:
    """Compone la pagina di un'epoca, con il suo contesto storico e i suoi elementi."""
    suoi = ordina_per_scoperta([e for e in elementi if e.scoperta.epoca == epoca.id])

    modello = ambiente_sito().get_template("epoca.html.j2")
    return modello.render(
        epoca=epoca,
        voci=_voci_elementi(suoi),
        inizio=formatta_anno(epoca.anno_inizio),
        fine=formatta_anno(epoca.anno_fine),
    )


def rendi_scopritore_sito(scopritore: Scopritore, elementi: list[Elemento]) -> str:
    """Compone la pagina di uno scopritore, con gli elementi che gli sono attribuiti.

    L'anagrafica sconosciuta non si inventa: quattro voci hanno nascita e morte
    a ``null``, e in quel caso la riga semplicemente non compare.
    """
    suoi = ordina_per_scoperta([e for e in elementi if scopritore.id in e.scoperta.scopritori])

    modello = ambiente_sito().get_template("scopritore.html.j2")
    return modello.render(
        scopritore=scopritore,
        voci=_voci_elementi(suoi),
        nato=formatta_anno(scopritore.nato) if scopritore.nato is not None else None,
        morto=formatta_anno(scopritore.morto) if scopritore.morto is not None else None,
    )


def rendi_attribuzioni_sito(scopritori: dict[str, Scopritore]) -> str:
    """Compone la pagina dei crediti delle immagini.

    Le immagini sono tutte in pubblico dominio o CC0 e non richiederebbero
    attribuzione: la si fornisce comunque come cortesia verso gli autori e
    verso chi vorrà riusare il materiale.
    """
    con_ritratto = sorted(
        (s for s in scopritori.values() if s.ritratto is not None),
        key=lambda s: s.nome,
    )

    modello = ambiente_sito().get_template("attribuzioni.html.j2")
    return modello.render(voci=con_ritratto, url_scopritore=url_scopritore)


def rendi_home(elementi: list[Elemento], epoche: dict[str, Epoca], tappe: list[Tappa]) -> str:
    """Compone la home del sito.

    I conteggi sono calcolati: una home che promette centodiciotto elementi
    mentre il dataset ne ha altri si smentisce alla prima pagina aperta.
    """
    cronologia = ordina_per_scoperta(elementi)
    ordinate = sorted(epoche.values(), key=lambda epoca: epoca.anno_inizio)

    modello = ambiente_sito().get_template("home.html.j2")
    return modello.render(
        totale=len(elementi),
        totale_tappe=len(tappe),
        totale_epoche=len(ordinate),
        epoche=ordinate,
        primo=cronologia[0],
        ultimo=cronologia[-1],
        anno_primo=formatta_anno(cronologia[0].scoperta.anno),
        anno_ultimo=formatta_anno(cronologia[-1].scoperta.anno),
        preposizione_da=(
            preposizione_articolata("da", cronologia[0].nome) + cronologia[0].nome.lower()
        ),
        url_epoca=url_epoca,
    )
