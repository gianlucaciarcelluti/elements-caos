"""Indice di ricerca, feed RSS, sitemap e pagina 404.

Sono le quattro cose che Quartz forniva e che il generatore proprio deve
costruire. L'indice è l'unica che ha un limite dichiarato: viaggia intero a
ogni prima ricerca, e oltre una certa soglia la ricerca nel browser smette di
essere una buona idea.
"""

import json
from typing import Any

from elements_caos.caricamento import ordina_per_scoperta
from elements_caos.models import Elemento, Epoca, Scopritore, Tappa
from elements_caos.render.diagrammi import formatta_anno
from elements_caos.sito.contesto import URL_ATTRIBUZIONI, URL_HOME
from elements_caos.sito.cronologia import URL_CRONOLOGIA
from elements_caos.sito.itinerario import URL_ITINERARIO
from elements_caos.sito.pagina import (
    ambiente_sito,
    url_approfondimento,
    url_elemento,
    url_epoca,
    url_scopritore,
)
from elements_caos.sito.tavola import URL_TAVOLA

BASE_URL = "https://gianlucaciarcelluti.github.io/elements-caos"

URL_INDICE = "statico/indice.json"
URL_RSS = "feed.xml"
URL_SITEMAP = "sitemap.xml"
URL_404 = "404.html"

# Tetto di peso dell'indice, non compresso. Oltre questa soglia la ricerca
# client-side va ripensata — un indice segmentato, o una ricerca sul server —
# invece che subita: mezzo megabyte servito a ogni visita per cercare fra
# duecento pagine sarebbe sproporzionato.
PESO_MASSIMO_INDICE = 150 * 1024


def voci_indice(
    elementi: list[Elemento],
    epoche: dict[str, Epoca],
    scopritori: dict[str, Scopritore],
) -> list[dict[str, Any]]:
    """Costruisce le voci cercabili del sito.

    Le chiavi sono di una lettera perché il file viaggia intero a ogni prima
    ricerca: ``t`` titolo, ``u`` indirizzo, ``k`` le parole aggiuntive su cui
    si cerca, ``c`` la categoria, ``s`` il simbolo chimico.

    Il simbolo ha un campo suo e non sta fra le parole aggiuntive perché va
    pesato di più: chi digita "P" cerca il fosforo, non il palladio né i tre
    scopritori il cui nome comincia per p. Misurato: senza questo campo il
    fosforo non compariva fra i primi risultati.

    Un elemento si cerca in quattro modi che non sono il suo nome: il simbolo,
    il nome inglese, l'anno e il nome di chi lo ha scoperto. Sono esattamente
    i casi in cui uno cerca senza ricordare come si chiama.
    """
    voci: list[dict[str, Any]] = []

    for elemento in elementi:
        nomi_scopritori = [
            scopritori[identificativo].nome
            for identificativo in elemento.scoperta.scopritori
            if identificativo in scopritori
        ]
        chiavi = [
            elemento.simbolo,
            elemento.nome_en,
            str(elemento.scoperta.anno),
            formatta_anno(elemento.scoperta.anno),
            *nomi_scopritori,
        ]
        voci.append(
            {
                "t": elemento.nome,
                "u": url_elemento(elemento),
                "c": "elemento",
                "s": elemento.simbolo,
                "k": " ".join(parte for parte in chiavi if parte),
            }
        )

    for scopritore in sorted(scopritori.values(), key=lambda s: s.nome):
        voci.append(
            {
                "t": scopritore.nome,
                "u": url_scopritore(scopritore),
                "c": "scopritore",
                "k": scopritore.nazionalita or "",
            }
        )

    for epoca in sorted(epoche.values(), key=lambda e: e.anno_inizio):
        voci.append(
            {
                "t": epoca.nome,
                "u": url_epoca(epoca.nome),
                "c": "epoca",
                "k": f"{epoca.anno_inizio} {epoca.anno_fine}",
            }
        )

    return voci


def costruisci_indice(
    elementi: list[Elemento],
    epoche: dict[str, Epoca],
    scopritori: dict[str, Scopritore],
) -> str:
    """Serializza l'indice in JSON compatto."""
    return json.dumps(
        voci_indice(elementi, epoche, scopritori),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def rendi_rss(elementi: list[Elemento]) -> str:
    """Compone il feed, in ordine di scoperta dal più recente.

    «Recente» significa scoperto per ultimo, non pubblicato per ultimo: il
    progetto non ha date di pubblicazione per nota, e inventarle sarebbe falso.
    """
    cronologia = list(reversed(ordina_per_scoperta(elementi)))

    modello = ambiente_sito().get_template("rss.xml.j2")
    return modello.render(
        base=BASE_URL,
        voci=[
            {
                "elemento": elemento,
                "anno": formatta_anno(elemento.scoperta.anno),
                "url": f"{BASE_URL}/{url_elemento(elemento)}",
                "descrizione": (
                    elemento.contenuti.hook
                    if elemento.contenuti is not None
                    else f"{elemento.nome}, scoperto nel {formatta_anno(elemento.scoperta.anno)}."
                ),
            }
            for elemento in cronologia
        ],
    )


def rendi_sitemap(
    elementi: list[Elemento],
    epoche: dict[str, Epoca],
    scopritori: dict[str, Scopritore],
    tappe: list[Tappa],
) -> str:
    """Compone la sitemap con tutte le pagine indicizzabili.

    La 404 non compare: elencarla equivarrebbe a chiedere che venga indicizzata.
    """
    indirizzi = [f"{BASE_URL}/"]
    indirizzi.extend(
        f"{BASE_URL}/{percorso}" for percorso in (URL_CRONOLOGIA, URL_TAVOLA, URL_ATTRIBUZIONI)
    )
    if tappe:
        indirizzi.append(f"{BASE_URL}/{URL_ITINERARIO}")
    indirizzi.extend(f"{BASE_URL}/{url_elemento(e)}" for e in elementi)
    indirizzi.extend(
        f"{BASE_URL}/{url_approfondimento(e)}" for e in elementi if e.contenuti_estesi is not None
    )
    indirizzi.extend(
        f"{BASE_URL}/{url_scopritore(s)}" for s in sorted(scopritori.values(), key=lambda s: s.nome)
    )
    indirizzi.extend(
        f"{BASE_URL}/{url_epoca(e.nome)}"
        for e in sorted(epoche.values(), key=lambda e: e.anno_inizio)
    )

    modello = ambiente_sito().get_template("sitemap.xml.j2")
    return modello.render(indirizzi=indirizzi)


def rendi_404() -> str:
    """Compone la pagina d'errore.

    Gli indirizzi sono assoluti: la stessa pagina risponde a
    ``/elementi/inesistente`` e a ``/inesistente``, e un percorso relativo
    funzionerebbe solo per una delle due profondità.
    """
    modello = ambiente_sito().get_template("404.html.j2")
    return modello.render(
        radice="/elements-caos/",
        url_cronologia=URL_CRONOLOGIA,
        url_tavola=URL_TAVOLA,
        url_home=URL_HOME,
    )
