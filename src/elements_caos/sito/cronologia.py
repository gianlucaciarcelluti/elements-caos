"""Composizione della linea del tempo, la pagina d'ingresso del sito.

Sostituisce le sei tabelle che nella versione costruita con Quartz rendevano la
cronologia alta 19.143 px — circa ventitré schermate su un telefono. Qui gli
elementi sono pastiglie compatte disposte in griglia, raggruppate per epoca, e
sopra a tutto un istogramma che mostra dove la storia accelera.
"""

from typing import Any

from elements_caos.caricamento import ordina_per_scoperta
from elements_caos.models import Elemento, Epoca
from elements_caos.render.avvertenza import AVVERTENZA_IA  # noqa: F401  (usata dai template)
from elements_caos.render.diagrammi import formatta_anno
from elements_caos.sito.pagina import ambiente_sito, url_elemento, url_epoca

URL_CRONOLOGIA = "cronologia-degli-elementi.html"

# Confine fra le scoperte senza data certa e quelle datate. Il fosforo (1669) è
# il primo elemento con luogo e data precisi: tutto ciò che viene prima è
# arrivato all'uomo senza che nessuno ne registrasse l'istante, e distribuirlo
# su millenni di barre vuote renderebbe illeggibile tutto il resto.
INIZIO_ISTOGRAMMA = 1650

# Ampiezza dei secchielli. Venticinque anni è la finestra che tiene distinti i
# due picchi del racconto — l'elettrolisi e la stagione dello spettroscopio —
# senza frammentare il resto in barre da uno o zero.
AMPIEZZA_SECCHIELLO = 25


def voci_per_epoca(elementi: list[Elemento], epoche: dict[str, Epoca]) -> list[dict[str, Any]]:
    """Raggruppa gli elementi per epoca, in ordine di scoperta.

    L'ordine delle epoche non viene dai dati né dall'alfabeto ma dalla storia:
    si ordinano per l'anno del loro primo elemento.
    """
    cronologia = ordina_per_scoperta(elementi)

    gruppi: dict[str, list[Elemento]] = {}
    for elemento in cronologia:
        gruppi.setdefault(elemento.scoperta.epoca, []).append(elemento)

    return [
        {
            "epoca": epoche[identificativo],
            "elementi": voci,
            "primo": formatta_anno(voci[0].scoperta.anno),
            "ultimo": formatta_anno(voci[-1].scoperta.anno),
        }
        for identificativo, voci in sorted(
            gruppi.items(), key=lambda voce: voce[1][0].scoperta.anno
        )
    ]


def densita_scoperte(elementi: list[Elemento]) -> list[dict[str, Any]]:
    """Conta le scoperte per periodo, per l'istogramma della pagina.

    I periodi senza scoperte restano nell'elenco con quantità zero: i vuoti
    sono informazione. Fra il 1675 e il 1725 non si scopre nulla, e comprimere
    quel silenzio darebbe l'impressione di una storia continua, che è
    esattamente il contrario di quello che è successo.
    """
    anni = [elemento.scoperta.anno for elemento in elementi]
    ultimo = max(anni) if anni else INIZIO_ISTOGRAMMA

    secchielli: list[dict[str, Any]] = [
        {
            "inizio": None,
            "fine": INIZIO_ISTOGRAMMA - 1,
            "etichetta": f"fino al {INIZIO_ISTOGRAMMA}",
            "quantita": sum(1 for anno in anni if anno < INIZIO_ISTOGRAMMA),
        }
    ]

    for inizio in range(INIZIO_ISTOGRAMMA, ultimo + 1, AMPIEZZA_SECCHIELLO):
        fine = inizio + AMPIEZZA_SECCHIELLO - 1
        secchielli.append(
            {
                "inizio": inizio,
                "fine": fine,
                "etichetta": f"{inizio}-{fine}",
                "quantita": sum(1 for anno in anni if inizio <= anno <= fine),
            }
        )

    return secchielli


def rendi_cronologia_sito(elementi: list[Elemento], epoche: dict[str, Epoca]) -> str:
    """Compone la pagina HTML della linea del tempo."""
    secchielli = densita_scoperte(elementi)
    massimo = max((s["quantita"] for s in secchielli), default=0) or 1

    modello = ambiente_sito().get_template("cronologia.html.j2")
    return modello.render(
        gruppi=voci_per_epoca(elementi, epoche),
        secchielli=secchielli,
        massimo=massimo,
        totale=len(elementi),
        formatta_anno=formatta_anno,
        url_elemento=url_elemento,
        url_epoca=url_epoca,
    )
