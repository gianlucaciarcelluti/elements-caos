"""Composizione della nota Markdown di un singolo elemento."""

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
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

# Traduce le cifre in apici Unicode, per rendere leggibili gli esponenti
# della configurazione elettronica (es. "3s2" -> "3s²").
_CIFRE_IN_APICI = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

# Intercetta un blocco/sottolivello (s, p, d, f) seguito dal numero di
# elettroni che vi risiedono, per convertire solo quella cifra in apice e
# lasciare inalterato il resto della configurazione (es. "[Ne] 3s2 3p3").
_ESPONENTE_CONFIGURAZIONE = re.compile(r"([spdf])(\d+)")


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


# Soglia, in anni avanti Cristo, sotto la quale il tag cronologico passa da
# secoli a millenni. Non è arbitraria: è dove la storiografia stessa smette
# di parlare di secoli per la preistoria, perché le datazioni non sono
# abbastanza precise da giustificarli. "IX millennio a.C." è un'espressione
# che si usa; "novantesimo secolo a.C." no, anche se matematicamente
# equivalente: nessuno la userebbe per descrivere quell'epoca.
_SOGLIA_MILLENNIO_AC = 3000


def _tag_periodo_storico(anno: int) -> str:
    """Restituisce il tag cronologico di un anno, pronto per il frontmatter.

    Per le date dal 3000 a.C. in poi (comprese quelle dopo Cristo) il tag
    esprime il secolo in cifre romane, come richiede la convenzione
    divulgativa consueta: ``secolo/XVII``. Per le date preistoriche,
    anteriori al 3000 a.C., il secolo in cifre romane produce numerali enormi
    e illeggibili (il rame, con la sua data convenzionale di -9000, darebbe
    "XCaC", il novantesimo secolo avanti Cristo: corretto ma innaturale). La
    storiografia stessa, per queste epoche, ragiona in millenni: il tag
    diventa allora ``millennio/9aC``, con il numero in cifre arabe — le cifre
    romane non aggiungerebbero leggibilità a un millennio, che resta un
    numero piccolo anche per le date più remote del vault.
    """
    if anno < 0 and abs(anno) > _SOGLIA_MILLENNIO_AC:
        millennio = (abs(anno) - 1) // 1000 + 1
        return f"millennio/{millennio}aC"
    if anno < 0:
        return f"secolo/{_in_numeri_romani((abs(anno) - 1) // 100 + 1)}aC"
    return f"secolo/{_in_numeri_romani((anno - 1) // 100 + 1)}"


def kelvin_in_celsius(kelvin: float | None) -> str:
    """Converte una temperatura da Kelvin a gradi Celsius per la lettura.

    Il calcolo passa da ``Decimal`` costruito sulla rappresentazione testuale
    del valore originale: sottraendo direttamente in virgola mobile, errori di
    rappresentazione dell'ordine di 1e-14 spingono valori esatti a metà (come
    317.3 K, cioè 44.15 °C) oltre la soglia di arrotondamento nella direzione
    sbagliata, restituendo una cifra diversa da quella corretta a partire dal
    dato sorgente. L'arrotondamento avviene con ``ROUND_HALF_UP``, la
    convenzione della divulgazione scientifica italiana (317.3 K diventa
    44,2 °C, non 44,1): scartato ``ROUND_HALF_EVEN`` (banker's rounding),
    corretto in contabilità ma inatteso in un testo divulgativo, dove
    mostrerebbe ad esempio 1537,8 °C per un valore esatto di 1537,85.
    """
    if kelvin is None:
        return "dato non disponibile"
    celsius = Decimal(str(kelvin)) - Decimal(str(ZERO_ASSOLUTO_CELSIUS))
    arrotondato = celsius.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{arrotondato} °C".replace(".", ",")


def formatta_decimale(numero: float) -> str:
    """Formatta un numero decimale con la virgola, la convenzione italiana.

    Riceve sempre un valore dichiaratamente decimale (massa atomica,
    densità): un intero passato per errore a questa funzione produrrebbe
    comunque un risultato sensato (nessun punto da sostituire), ma la firma
    resta ``float`` perché i campi a cui si applica lo sono nel modello dati.
    Numero atomico, gruppo, periodo e stati di ossidazione sono ``int`` nel
    modello e non passano da qui: non hanno mai un separatore decimale da
    localizzare.
    """
    return str(numero).replace(".", ",")


def formatta_configurazione_elettronica(configurazione: str) -> str:
    """Converte in apici Unicode gli esponenti di una configurazione elettronica.

    Il dataset la fornisce in notazione piatta (``3s2``), che si legge "tre
    esse due" anziché "tre esse al quadrato": su un vault didattico la
    differenza conta. La conversione si applica solo qui, in fase di
    rendering — negli YAML la configurazione resta piatta, leggibile da
    qualsiasi consumatore dei dati.
    """

    def _converti(corrispondenza: re.Match[str]) -> str:
        sottolivello, elettroni = corrispondenza.groups()
        return sottolivello + elettroni.translate(_CIFRE_IN_APICI)

    return _ESPONENTE_CONFIGURAZIONE.sub(_converti, configurazione)


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


def ambiente_template() -> Environment:
    """Costruisce l'ambiente Jinja2 condiviso da tutti i renderer del vault."""
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
        _tag_periodo_storico(elemento.scoperta.anno),
    ]

    modello = ambiente_template().get_template("elemento.md.j2")
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
        massa_atomica=formatta_decimale(proprieta.massa_atomica),
        configurazione_elettronica=formatta_configurazione_elettronica(
            proprieta.configurazione_elettronica
        ),
        fusione=kelvin_in_celsius(proprieta.punto_fusione_k),
        ebollizione=kelvin_in_celsius(proprieta.punto_ebollizione_k),
        densita=(
            f"{formatta_decimale(proprieta.densita)} g/cm³"
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
