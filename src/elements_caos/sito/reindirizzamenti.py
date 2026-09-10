"""Reindirizzamenti dagli indirizzi che il sito costruito con Quartz pubblicava.

Quartz generava una pagina per ogni tag del frontmatter: quarantacinque
indirizzi che il sito ha servito e che quindi non possono limitarsi a
rispondere 404. La tassonomia dei tag non viene replicata — non fa parte del
progetto, e la parte utile, scorrere gli elementi per famiglia chimica, ora sta
in ``/elementi`` — ma ogni indirizzo porta alla pagina che gli somiglia di più.

Sono file statici perché GitHub Pages non ha regole di riscrittura lato server:
l'unico reindirizzamento possibile è una pagina che si sostituisce da sola.

Quando non serviranno più — quando nessuno seguirà più quei collegamenti —
questo modulo si cancella insieme al suo template, senza toccare altro.
"""

from elements_caos.sito.contesto import (
    URL_INDICE_ELEMENTI,
    URL_INDICE_EPOCHE,
    URL_INDICE_SCOPRITORI,
)
from elements_caos.sito.cronologia import URL_CRONOLOGIA
from elements_caos.sito.pagina import ambiente_sito
from elements_caos.sito.tavola import URL_TAVOLA

# Gli indirizzi di tag effettivamente pubblicati, letti dalla sitemap del sito
# dal vivo prima della sostituzione. L'elenco è esplicito e non ricavato dai
# dati: descrive cosa è STATO pubblicato, che è un fatto storico e non una
# proprietà del dataset di oggi.
TAG_PUBBLICATI: tuple[str, ...] = (
    "tags",
    "tags/alogeno",
    "tags/attinide",
    "tags/cronologia",
    "tags/elemento",
    "tags/epoca",
    "tags/epoca/alchimia",
    "tags/epoca/antichita",
    "tags/epoca/elettrolisi",
    "tags/epoca/nucleare",
    "tags/epoca/pneumatica",
    "tags/epoca/spettroscopia",
    "tags/gas-nobile",
    "tags/indice",
    "tags/lantanide",
    "tags/licenze",
    "tags/metallo-alcalino",
    "tags/metallo-alcalino-terroso",
    "tags/metallo-di-transizione",
    "tags/metallo-post-transizione",
    "tags/millennio",
    "tags/millennio/26ac",
    "tags/millennio/40ac",
    "tags/millennio/4ac",
    "tags/millennio/5ac",
    "tags/millennio/7ac",
    "tags/millennio/9ac",
    "tags/non-metallo",
    "tags/scopritore",
    "tags/secolo",
    "tags/secolo/iii",
    "tags/secolo/viac",
    "tags/secolo/xac",
    "tags/secolo/xix",
    "tags/secolo/xv",
    "tags/secolo/xvac",
    "tags/secolo/xvii",
    "tags/secolo/xviii",
    "tags/secolo/xx",
    "tags/secolo/xxac",
    "tags/secolo/xxi",
    "tags/secolo/xxxac",
    "tags/semimetallo",
    "tags/servizio",
    "tags/tavola",
)

# I sei identificativi d'epoca usati nei tag, con la pagina corrispondente.
# Il tag usa l'identificativo, la pagina il nome: `epoca/nucleare` porta a
# `epoche/era-nucleare`.
_EPOCHE = {
    "alchimia": "epoche/alchimia-e-primo-moderno.html",
    "antichita": "epoche/antichità.html",
    "elettrolisi": "epoche/l'età-dell'elettrolisi.html",
    "nucleare": "epoche/era-nucleare.html",
    "pneumatica": "epoche/chimica-pneumatica.html",
    "spettroscopia": "epoche/spettroscopia-e-radioattività.html",
}

_ESATTI = {
    "tags/scopritore": URL_INDICE_SCOPRITORI,
    "tags/epoca": URL_INDICE_EPOCHE,
    "tags/cronologia": URL_CRONOLOGIA,
    "tags/tavola": URL_TAVOLA,
    "tags/licenze": "attribuzioni.html",
    "tags/servizio": "attribuzioni.html",
}


def destinazione(tag: str) -> str:
    """Indica dove porta un vecchio indirizzo di tag.

    Le famiglie chimiche vanno all'indice degli elementi, che le raggruppa
    esattamente così; le epoche alla loro pagina; secoli e millenni alla
    cronologia, che è l'unica pagina in cui il tempo è l'asse.
    """
    if tag in _ESATTI:
        return _ESATTI[tag]

    if tag.startswith("tags/epoca/"):
        return _EPOCHE.get(tag.removeprefix("tags/epoca/"), URL_INDICE_EPOCHE)

    if tag.startswith(("tags/secolo", "tags/millennio")):
        return URL_CRONOLOGIA

    # Tutto il resto — le famiglie chimiche, "elemento", "indice" e la radice
    # dei tag — è un modo di scorrere gli elementi.
    return URL_INDICE_ELEMENTI


def rendi_reindirizzamento(tag: str, verso: str) -> str:
    """Compone la paginetta che porta dal vecchio indirizzo al nuovo.

    Non è una pagina bianca con un refresh: chi ci arriva con JavaScript
    disattivato, o mentre il rinvio non è ancora scattato, deve capire cos'è
    successo e avere un collegamento da premere.
    """
    modello = ambiente_sito().get_template("reindirizzamento.html.j2")
    # I reindirizzamenti stanno sotto tags/, a una o due cartelle di
    # profondità: la radice relativa si calcola dal numero di segmenti.
    profondita = tag.count("/")
    return modello.render(verso=verso, radice="../" * profondita)
