"""Composizione della nota Markdown di un singolo elemento."""

from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from elements_caos.caricamento import ordina_per_scoperta
from elements_caos.models import Categoria, Elemento, Epoca, Scopritore, Sezione
from elements_caos.render.diagrammi import (
    Vicini,
    calcola_vicini,
    diagramma_atomo,
    diagramma_composti,
    diagramma_posizione,
    diagramma_timeline,
    formatta_anno,
)
from elements_caos.render.prosa import componi_sezione, conta_parole, tempo_lettura_minuti

CARTELLA_TEMPLATE = Path(__file__).parent / "templates"

# Differenza fra la scala Kelvin e la scala Celsius.
ZERO_ASSOLUTO_CELSIUS = 273.15

ETICHETTE_CATEGORIA = {
    Categoria.METALLO_ALCALINO: "Metallo alcalino",
    Categoria.METALLO_ALCALINO_TERROSO: "Metallo alcalino terroso",
    Categoria.METALLO_DI_TRANSIZIONE: "Metallo di transizione",
    Categoria.METALLO_POST_TRANSIZIONE: "Metallo post-transizione",
    Categoria.SEMIMETALLO: "Semimetallo",
    Categoria.NON_METALLO: "Non metallo",
    Categoria.ALOGENO: "Alogeno",
    Categoria.GAS_NOBILE: "Gas nobile",
    Categoria.LANTANIDE: "Lantanide",
    Categoria.ATTINIDE: "Attinide",
}

_NUMERI_ROMANI = [
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
]


@dataclass(frozen=True)
class ContestoNota:
    """Tutto ciò che serve a comporre la nota di un elemento."""

    elemento: Elemento
    vicini: Vicini
    precedente_cronologico: Elemento | None
    successivo_cronologico: Elemento | None
    posizione_cronologica: int
    scopritori: list[Scopritore]
    epoca: Epoca


def _in_numeri_romani(numero: int) -> str:
    """Converte un numero intero positivo nella corrispondente cifra romana."""
    risultato = ""
    resto = numero
    for valore, simbolo in _NUMERI_ROMANI:
        while resto >= valore:
            risultato += simbolo
            resto -= valore
    return risultato


def _secolo(anno: int) -> str:
    """Restituisce il secolo di un anno in cifre romane, con suffisso per le date a.C."""
    if anno < 0:
        return f"{_in_numeri_romani((abs(anno) - 1) // 100 + 1)}aC"
    return _in_numeri_romani((anno - 1) // 100 + 1)


def _kelvin_in_celsius(kelvin: float | None) -> str:
    """Converte una temperatura da Kelvin a gradi Celsius per la lettura.

    Il calcolo passa da ``Decimal`` costruito sulla rappresentazione testuale
    del valore originale: sottraendo direttamente in virgola mobile, errori di
    rappresentazione dell'ordine di 1e-14 spingono valori esatti a metà (come
    317.3 K, cioè 44.15 °C) oltre la soglia di arrotondamento, restituendo una
    cifra diversa da quella attesa a partire dal dato sorgente. Il troncamento
    (anziché l'arrotondamento) rende il risultato indipendente da quale lato
    della soglia capiti il valore esatto a metà.
    """
    if kelvin is None:
        return "dato non disponibile"
    celsius = Decimal(str(kelvin)) - Decimal(str(ZERO_ASSOLUTO_CELSIUS))
    troncato = celsius.quantize(Decimal("0.1"), rounding=ROUND_DOWN)
    return f"{troncato} °C".replace(".", ",")


def costruisci_contesto(
    elemento: Elemento,
    tutti: list[Elemento],
    scopritori: dict[str, Scopritore],
    epoche: dict[str, Epoca],
) -> ContestoNota:
    """Raccoglie i dati contestuali necessari alla nota di un elemento.

    Include i vicini nella tavola, la posizione nell'ordine cronologico di
    scoperta e i rimandi all'elemento precedente e successivo.
    """
    cronologia = ordina_per_scoperta(tutti)
    indice = next(
        i for i, e in enumerate(cronologia) if e.numero_atomico == elemento.numero_atomico
    )

    return ContestoNota(
        elemento=elemento,
        vicini=calcola_vicini(elemento, tutti),
        precedente_cronologico=cronologia[indice - 1] if indice > 0 else None,
        successivo_cronologico=(cronologia[indice + 1] if indice < len(cronologia) - 1 else None),
        posizione_cronologica=indice + 1,
        scopritori=[
            scopritori[identificativo]
            for identificativo in elemento.scoperta.scopritori
            if identificativo in scopritori
        ],
        epoca=epoche[elemento.scoperta.epoca],
    )


def _ambiente() -> Environment:
    """Costruisce l'ambiente Jinja2 usato per il rendering delle note."""
    return Environment(
        loader=FileSystemLoader(CARTELLA_TEMPLATE),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def rendi_nota(contesto: ContestoNota) -> str:
    """Compone la nota Markdown completa di un elemento.

    Il risultato è deterministico: a parità di dati in ingresso il testo
    prodotto è identico byte per byte, proprietà su cui si regge il controllo
    di integrità eseguito dalla CI.
    """
    elemento = contesto.elemento
    contenuti = elemento.contenuti
    proprieta = elemento.proprieta

    sezioni = {
        "incipit": componi_sezione(contenuti, Sezione.INCIPIT) if contenuti else "",
        "storia": componi_sezione(contenuti, Sezione.STORIA) if contenuti else "",
        "caratteristiche": (
            componi_sezione(contenuti, Sezione.CARATTERISTICHE) if contenuti else ""
        ),
        "usi": componi_sezione(contenuti, Sezione.USI) if contenuti else "",
        "curiosita": componi_sezione(contenuti, Sezione.CURIOSITA) if contenuti else "",
    }

    parole = sum(conta_parole(testo) for testo in sezioni.values())
    nomi_scopritori = [scopritore.nome for scopritore in contesto.scopritori]

    tags = [
        "elemento",
        proprieta.categoria.value.replace("_", "-"),
        f"epoca/{elemento.scoperta.epoca}",
        f"secolo/{_secolo(elemento.scoperta.anno)}",
    ]

    modello = _ambiente().get_template("elemento.md.j2")
    return modello.render(
        elemento=elemento,
        epoca=contesto.epoca,
        posizione_cronologica=contesto.posizione_cronologica,
        tempo_lettura=tempo_lettura_minuti(parole),
        tags=tags,
        nomi_scopritori=nomi_scopritori,
        wikilink_scopritori=[f"[[{nome}]]" for nome in nomi_scopritori],
        anno_leggibile=formatta_anno(elemento.scoperta.anno),
        categoria_leggibile=ETICHETTE_CATEGORIA[proprieta.categoria],
        fusione=_kelvin_in_celsius(proprieta.punto_fusione_k),
        ebollizione=_kelvin_in_celsius(proprieta.punto_ebollizione_k),
        densita=(
            f"{proprieta.densita} g/cm³"
            if proprieta.densita is not None
            else "dato non disponibile"
        ),
        stati_ossidazione=(
            ", ".join(f"{s:+d}" for s in proprieta.stati_ossidazione)
            if proprieta.stati_ossidazione
            else "—"
        ),
        diagramma_timeline=diagramma_timeline(elemento, nomi_scopritori),
        diagramma_posizione=diagramma_posizione(elemento, contesto.vicini),
        diagramma_atomo=diagramma_atomo(elemento),
        diagramma_composti=diagramma_composti(elemento),
        precedente=contesto.precedente_cronologico,
        successivo=contesto.successivo_cronologico,
        anno_precedente=(
            formatta_anno(contesto.precedente_cronologico.scoperta.anno)
            if contesto.precedente_cronologico
            else ""
        ),
        anno_successivo=(
            formatta_anno(contesto.successivo_cronologico.scoperta.anno)
            if contesto.successivo_cronologico
            else ""
        ),
        **sezioni,
    )


def nome_file_nota(elemento: Elemento) -> str:
    """Restituisce il nome del file Markdown della nota di un elemento."""
    return f"{elemento.nome}.md"
