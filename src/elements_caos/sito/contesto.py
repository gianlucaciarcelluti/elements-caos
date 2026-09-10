"""Pagine di contesto del sito: home, epoche, scopritori e attribuzioni.

Sono le pagine che il piano di ridisegno aveva saltato e che il sito costruito
con Quartz pubblica dal Task 23: senza, la sostituzione romperebbe 108
collegamenti già raggiungibili.
"""

from typing import Any

from elements_caos.caricamento import ordina_per_scoperta
from elements_caos.models import Categoria, Elemento, Epoca, Scopritore, Tappa
from elements_caos.render.diagrammi import formatta_anno, preposizione_articolata
from elements_caos.render.note import ETICHETTE_CATEGORIA
from elements_caos.sito.pagina import (
    ambiente_sito,
    url_elemento,
    url_epoca,
    url_scopritore,
)

URL_HOME = "index.html"
URL_ATTRIBUZIONI = "attribuzioni.html"

# Indici di cartella. Quartz li pubblicava e sono navigazione vera: senza,
# /elementi, /epoche e /scopritori risponderebbero 404 dopo la sostituzione.
URL_INDICE_ELEMENTI = "elementi/index.html"
URL_INDICE_EPOCHE = "epoche/index.html"
URL_INDICE_SCOPRITORI = "scopritori/index.html"


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


def voci_scopritori(
    scopritori: dict[str, Scopritore], elementi: list[Elemento]
) -> list[dict[str, Any]]:
    """Elenca gli scopritori in ordine alfabetico, con quanti elementi hanno trovato.

    Cento nomi si scorrono per lettera: l'ordine alfabetico è l'unico che
    permette di trovarne uno che si sta cercando.
    """
    return [
        {
            "scopritore": scopritore,
            "url": url_scopritore(scopritore),
            "quanti": sum(1 for e in elementi if scopritore.id in e.scoperta.scopritori),
        }
        for scopritore in sorted(scopritori.values(), key=lambda s: s.nome.lower())
    ]


def rendi_indice_elementi(elementi: list[Elemento]) -> str:
    """Compone l'indice di tutti gli elementi, raggruppati per categoria chimica.

    È ciò che le pagine di tag di Quartz facevano di utile: scorrere gli
    elementi per famiglia. La tassonomia dei tag non viene replicata, la
    possibilità di scorrere sì, sotto un indirizzo più sensato.
    """
    gruppi: dict[Categoria, list[Elemento]] = {}
    for elemento in sorted(elementi, key=lambda e: e.numero_atomico):
        gruppi.setdefault(elemento.proprieta.categoria, []).append(elemento)

    modello = ambiente_sito().get_template("indice-elementi.html.j2")
    return modello.render(
        totale=len(elementi),
        gruppi=[
            {
                "nome": ETICHETTE_CATEGORIA[categoria],
                "voci": _voci_elementi(voci),
            }
            for categoria, voci in sorted(
                gruppi.items(), key=lambda voce: ETICHETTE_CATEGORIA[voce[0]]
            )
        ],
    )


def rendi_indice_epoche(epoche: dict[str, Epoca], elementi: list[Elemento]) -> str:
    """Compone l'indice delle sei epoche, in ordine storico."""
    conteggi: dict[str, int] = {}
    for elemento in elementi:
        conteggi[elemento.scoperta.epoca] = conteggi.get(elemento.scoperta.epoca, 0) + 1

    modello = ambiente_sito().get_template("indice-epoche.html.j2")
    return modello.render(
        voci=[
            {
                "epoca": epoca,
                "url": url_epoca(epoca.nome),
                "quanti": conteggi.get(epoca.id, 0),
                "inizio": formatta_anno(epoca.anno_inizio),
                "fine": formatta_anno(epoca.anno_fine),
            }
            for epoca in sorted(epoche.values(), key=lambda e: e.anno_inizio)
        ]
    )


def rendi_indice_scopritori(scopritori: dict[str, Scopritore], elementi: list[Elemento]) -> str:
    """Compone l'indice alfabetico degli scopritori."""
    modello = ambiente_sito().get_template("indice-scopritori.html.j2")
    return modello.render(voci=voci_scopritori(scopritori, elementi), totale=len(scopritori))


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
