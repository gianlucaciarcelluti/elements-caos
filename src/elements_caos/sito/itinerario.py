"""Composizione dell'itinerario guidato, con il tempo di lettura per tappa.

Le dodici tappe hanno una pagina propria, che nella versione costruita con
Quartz non avevano: erano un blocco in cima alla cronologia, la parte più utile
di quella pagina e anche la più facile da scorrere senza vedere.
"""

from typing import Any

from elements_caos.models import Elemento, Tappa
from elements_caos.render.prosa import conta_parole, tempo_lettura_minuti
from elements_caos.sito.pagina import ambiente_sito, url_elemento

URL_ITINERARIO = "itinerario.html"


def _minuti_elemento(elemento: Elemento | None) -> int:
    """Tempo di lettura della nota di un elemento, in minuti.

    Si misura sulla prosa dei beat più l'apertura, come il budget di parole:
    è il testo che il lettore legge davvero, senza dati né diagrammi.
    """
    if elemento is None or elemento.contenuti is None:
        return 1
    contenuti = elemento.contenuti
    testo = " ".join(beat.testo for beat in contenuti.beats) + " " + contenuti.hook
    return tempo_lettura_minuti(conta_parole(testo))


def tappe_con_elemento(tappe: list[Tappa], elementi: list[Elemento]) -> list[dict[str, Any]]:
    """Associa a ogni tappa il suo elemento e il tempo di lettura.

    L'ordine è quello dei dati e non va riordinato: è redazionale, non
    cronologico. L'uranio è nella tavola dal 1789 ma la sua tappa riguarda il
    1896, e per questo viene dopo l'argon.
    """
    per_nome = {elemento.nome: elemento for elemento in elementi}

    voci: list[dict[str, Any]] = []
    for numero, tappa in enumerate(tappe, start=1):
        elemento = per_nome.get(tappa.elemento)
        voci.append(
            {
                "numero": numero,
                "tappa": tappa,
                "elemento": elemento,
                "minuti": _minuti_elemento(elemento),
                "url": url_elemento(elemento) if elemento else "",
            }
        )
    return voci


def minuti_di_lettura(tappe: list[Tappa], elementi: list[Elemento]) -> int:
    """Tempo complessivo dell'itinerario, in minuti."""
    return sum(voce["minuti"] for voce in tappe_con_elemento(tappe, elementi))


def rendi_itinerario_sito(tappe: list[Tappa], elementi: list[Elemento]) -> str:
    """Compone la pagina HTML dell'itinerario guidato."""
    voci = tappe_con_elemento(tappe, elementi)
    totale = sum(voce["minuti"] for voce in voci)

    modello = ambiente_sito().get_template("itinerario.html.j2")
    return modello.render(
        voci=voci,
        totale_tappe=len(voci),
        totale_minuti=totale,
    )
