"""Generatori dei diagrammi Mermaid che corredano ogni nota.

Sono ammessi soltanto i tipi ``flowchart``, ``timeline`` e ``graph``: il
rendering degli altri varia fra Obsidian, GitHub e Quartz, e il vault viene
pubblicato su tutti e tre.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

from elements_caos.models import Elemento

# Caratteri che romperebbero la sintassi Mermaid all'interno di un'etichetta.
_CARATTERI_PROBLEMATICI = re.compile(r'["\';{}|<>]')


@dataclass(frozen=True)
class Vicini:
    """Elementi adiacenti nella tavola periodica lungo gruppo e periodo."""

    sopra: Elemento | None = None
    sotto: Elemento | None = None
    sinistra: Elemento | None = None
    destra: Elemento | None = None


def formatta_anno(anno: int) -> str:
    """Formatta un anno per la lettura, esplicitando le date avanti Cristo."""
    return f"{abs(anno)} a.C." if anno < 0 else str(anno)


def _etichetta(testo: str) -> str:
    """Neutralizza i caratteri che romperebbero un'etichetta Mermaid."""
    return _CARATTERI_PROBLEMATICI.sub("", testo)


def _recinta(corpo: str) -> str:
    """Racchiude il corpo del diagramma nel recinto Markdown di Mermaid."""
    return f"```mermaid\n{corpo.strip()}\n```"


def diagramma_timeline(elemento: Elemento, nomi_scopritori: list[str]) -> str:
    """Genera la cronologia della scoperta dell'elemento.

    La scala temporale varia da millenni per gli elementi antichi a pochi mesi
    per i transuranici: è il diagramma stesso a comunicare il ritmo dell'epoca.

    ``nomi_scopritori`` va passato già risolto dal chiamante: questa funzione
    resta pura sui dati che riceve e non conosce ``scopritori.yaml``.
    ``elemento.scoperta.scopritori`` contiene id (kebab-case), non nomi propri,
    e non va mai mostrato direttamente nel diagramma.
    """
    scoperta = elemento.scoperta
    righe = [
        "timeline",
        f"    title Scoperta del {_etichetta(elemento.nome)}",
    ]

    if scoperta.anno_stimato:
        righe.append(f"    {formatta_anno(scoperta.anno)} : Primo uso documentato (data stimata)")
    else:
        scopritori = ", ".join(_etichetta(nome) for nome in nomi_scopritori) or "ignoto"
        righe.append(f"    {formatta_anno(scoperta.anno)} : Scoperta : {scopritori}")

    if scoperta.isolamento_anno is not None and scoperta.isolamento_anno != scoperta.anno:
        righe.append(f"    {formatta_anno(scoperta.isolamento_anno)} : Isolamento allo stato puro")

    return _recinta("\n".join(righe))


def calcola_vicini(elemento: Elemento, tutti: list[Elemento]) -> Vicini:
    """Individua gli elementi adiacenti nella tavola periodica.

    Sopra e sotto lungo il gruppo, a sinistra e a destra lungo il periodo.
    Lantanidi e attinidi non appartengono a un gruppo: per loro i vicini
    verticali non esistono.
    """
    gruppo = elemento.proprieta.gruppo
    periodo = elemento.proprieta.periodo

    def _cerca(condizione: Callable[[Elemento], bool]) -> Elemento | None:
        for candidato in tutti:
            if candidato.numero_atomico == elemento.numero_atomico:
                continue
            if condizione(candidato):
                return candidato
        return None

    sopra = sotto = None
    if gruppo is not None:
        sopra = _cerca(
            lambda c: c.proprieta.gruppo == gruppo and c.proprieta.periodo == periodo - 1
        )
        sotto = _cerca(
            lambda c: c.proprieta.gruppo == gruppo and c.proprieta.periodo == periodo + 1
        )

    sinistra = _cerca(
        lambda c: c.proprieta.periodo == periodo and c.numero_atomico == elemento.numero_atomico - 1
    )
    destra = _cerca(
        lambda c: c.proprieta.periodo == periodo and c.numero_atomico == elemento.numero_atomico + 1
    )

    return Vicini(sopra=sopra, sotto=sotto, sinistra=sinistra, destra=destra)


def diagramma_posizione(elemento: Elemento, vicini: Vicini) -> str:
    """Genera la croce dei vicini, per rendere visibile la periodicità.

    Un elenco di numeri non trasmette il fatto che le proprietà si ripetano
    lungo il gruppo e varino lungo il periodo: la disposizione spaziale sì.
    """
    righe = ["flowchart TB"]
    nome = _etichetta(elemento.nome)
    simbolo = _etichetta(elemento.simbolo)
    centro = f'    C["{nome}<br/>{simbolo} · Z={elemento.numero_atomico}"]'

    if vicini.sopra is not None:
        righe.append(f'    S["{_etichetta(vicini.sopra.nome)}<br/>{vicini.sopra.simbolo}"]')
        righe.append("    S -->|stesso gruppo| C")

    righe.append(centro)

    if vicini.sinistra is not None:
        righe.append(f'    L["{_etichetta(vicini.sinistra.nome)}<br/>{vicini.sinistra.simbolo}"]')
        righe.append("    L -->|stesso periodo| C")

    if vicini.destra is not None:
        righe.append(f'    R["{_etichetta(vicini.destra.nome)}<br/>{vicini.destra.simbolo}"]')
        righe.append("    C -->|stesso periodo| R")

    if vicini.sotto is not None:
        righe.append(f'    G["{_etichetta(vicini.sotto.nome)}<br/>{vicini.sotto.simbolo}"]')
        righe.append("    C -->|stesso gruppo| G")

    righe.append("    style C fill:#f9a825,stroke:#333,stroke-width:2px")

    return _recinta("\n".join(righe))


def diagramma_atomo(elemento: Elemento) -> str:
    """Genera la struttura a gusci elettronici dell'elemento.

    Il guscio più esterno è marcato come guscio di valenza: è quello che
    determina il comportamento chimico, e collegarlo alla configurazione aiuta
    a capire perché l'elemento reagisce come reagisce.
    """
    gusci = elemento.proprieta.gusci
    righe = [
        "flowchart LR",
        f'    N(("Nucleo<br/>Z={elemento.numero_atomico}"))',
    ]

    precedente = "N"
    for indice, elettroni in enumerate(gusci, start=1):
        e_ultimo = indice == len(gusci)
        etichetta = f"Guscio {indice}<br/>{elettroni} e-"
        if e_ultimo:
            etichetta += "<br/>(valenza)"
        nodo = f"G{indice}"
        righe.append(f'    {nodo}["{etichetta}"]')
        righe.append(f"    {precedente} --> {nodo}")
        precedente = nodo

    righe.append(f"    style G{len(gusci)} fill:#4caf50,stroke:#333,stroke-width:2px")

    return _recinta("\n".join(righe))


def diagramma_composti(elemento: Elemento) -> str:
    """Genera la mappa dai composti principali ai loro impieghi.

    Restituisce una stringa vuota quando non sono noti composti rilevanti:
    meglio nessun diagramma che un diagramma vuoto.
    """
    if not elemento.composti_principali:
        return ""

    righe = ["flowchart LR", f'    E["{_etichetta(elemento.nome)}"]']
    usi_visti: dict[str, str] = {}

    for indice, composto in enumerate(elemento.composti_principali, start=1):
        nodo_composto = f"C{indice}"
        etichetta = _etichetta(f"{composto.nome}<br/>{composto.formula}")
        righe.append(f'    {nodo_composto}["{etichetta}"]')
        righe.append(f"    E --> {nodo_composto}")

        for uso in composto.usi:
            if uso not in usi_visti:
                nodo_uso = f"U{len(usi_visti) + 1}"
                usi_visti[uso] = nodo_uso
                righe.append(f'    {nodo_uso}(["{_etichetta(uso)}"])')
            righe.append(f"    {nodo_composto} --> {usi_visti[uso]}")

    righe.append("    style E fill:#f9a825,stroke:#333,stroke-width:2px")

    return _recinta("\n".join(righe))
