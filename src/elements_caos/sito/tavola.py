"""Composizione della tavola periodica che si riempie nell'ordine della scoperta.

È la pagina che dice la tesi del progetto in un gesto: si trascina un anno e le
caselle si accendono nell'ordine in cui l'umanità ha riempito la tavola, non in
quello del numero atomico.

La tavola statica, con tutte e 118 le caselle, è già nell'HTML: lo scorrevole è
una miglioria, non una condizione per vedere qualcosa.
"""

from typing import Any

from elements_caos.caricamento import ordina_per_scoperta
from elements_caos.models import Elemento, Epoca
from elements_caos.render.diagrammi import formatta_anno, preposizione_articolata
from elements_caos.sito.pagina import ambiente_sito, url_elemento

URL_TAVOLA = "tavola-periodica.html"

# Le due file del blocco f, staccate sotto la tavola principale. Nei dati i
# ventotto elementi che le compongono dichiarano tutti gruppo 3 e periodo 6 o 7:
# lasciarli lì significherebbe impilarne quattordici in una sola casella.
RIGA_LANTANIDI = 9
RIGA_ATTINIDI = 10

# Primo elemento di ciascuna fila del blocco f, e colonna da cui parte.
# Nel dataset il blocco f va da lantanio a itterbio e da attinio a nobelio:
# lutezio e laurenzio sono blocco d e restano in gruppo 3 nella tavola
# principale, che è la convenzione IUPAC.
_PRIMO_LANTANIDE = 57
_PRIMO_ATTINIDE = 89
_COLONNA_INIZIALE_BLOCCO_F = 3


def posizione_griglia(elemento: Elemento) -> tuple[int, int]:
    """Colonna e riga dell'elemento nella griglia della tavola periodica.

    Gli elementi del blocco f vanno nelle due file separate: nel dataset
    dichiarano gruppo 3, come tutta la serie, e senza questa estrazione
    finirebbero quattordici per casella. Lutezio e laurenzio non sono blocco f
    nei dati e restano quindi nella tavola principale, in gruppo 3.
    """
    proprieta = elemento.proprieta
    if proprieta.blocco == "f":
        if elemento.numero_atomico >= _PRIMO_ATTINIDE:
            partenza, riga = _PRIMO_ATTINIDE, RIGA_ATTINIDI
        else:
            partenza, riga = _PRIMO_LANTANIDE, RIGA_LANTANIDI
        colonna = _COLONNA_INIZIALE_BLOCCO_F + (elemento.numero_atomico - partenza)
        return colonna, riga

    # Fuori dal blocco f gruppo e periodo bastano, e il modello li garantisce
    # entrambi presenti per ogni elemento del dataset.
    assert proprieta.gruppo is not None
    return proprieta.gruppo, proprieta.periodo


def caselle(elementi: list[Elemento]) -> list[dict[str, Any]]:
    """Descrive le 118 caselle della tavola, con la loro posizione cronologica.

    La posizione cronologica è quella della catena di scoperta: è il valore su
    cui agisce lo scorrevole, e deve coincidere con l'ordine reale, altrimenti
    la tavola si riempirebbe raccontando una storia diversa da quella vera.
    """
    posizioni = {
        elemento.numero_atomico: indice
        for indice, elemento in enumerate(ordina_per_scoperta(elementi), start=1)
    }

    voci: list[dict[str, Any]] = []
    for elemento in sorted(elementi, key=lambda e: e.numero_atomico):
        colonna, riga = posizione_griglia(elemento)
        anno = formatta_anno(elemento.scoperta.anno)
        voci.append(
            {
                "elemento": elemento,
                "numero_atomico": elemento.numero_atomico,
                "simbolo": elemento.simbolo,
                "nome": elemento.nome,
                "anno": anno,
                "colonna": colonna,
                "riga": riga,
                "epoca": elemento.scoperta.epoca,
                "posizione": posizioni[elemento.numero_atomico],
                "descrizione": f"{elemento.nome} ({elemento.simbolo}), scoperto nel {anno}",
                "url": url_elemento(elemento),
            }
        )
    return voci


def rendi_tavola_sito(elementi: list[Elemento], epoche: dict[str, Epoca]) -> str:
    """Compone la pagina HTML della tavola periodica."""
    cronologia = ordina_per_scoperta(elementi)

    modello = ambiente_sito().get_template("tavola.html.j2")
    return modello.render(
        caselle=caselle(elementi),
        totale=len(elementi),
        primo=cronologia[0],
        ultimo=cronologia[-1],
        anno_primo=formatta_anno(cronologia[0].scoperta.anno),
        anno_ultimo=formatta_anno(cronologia[-1].scoperta.anno),
        epoche=[epoche[identificativo] for identificativo in _epoche_in_ordine(cronologia)],
        preposizione=preposizione_articolata,
        riga_lantanidi=RIGA_LANTANIDI,
        riga_attinidi=RIGA_ATTINIDI,
    )


def _epoche_in_ordine(cronologia: list[Elemento]) -> list[str]:
    """Identificativi delle epoche nell'ordine in cui compaiono nella storia."""
    viste: list[str] = []
    for elemento in cronologia:
        if elemento.scoperta.epoca not in viste:
            viste.append(elemento.scoperta.epoca)
    return viste
