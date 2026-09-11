"""Composizione delle pagine HTML del sito pubblico.

Il sito è un secondo emettitore accanto a quello che produce il vault: legge
gli stessi modelli e riusa la stessa prosa, ma emette HTML invece che Markdown.
La ragione della separazione è che il vault serve a chi legge in Obsidian e il
sito a chi legge nel browser, e le due cose hanno bisogni diversi: il primo
vuole wikilink e frontmatter, il secondo URL e struttura semantica.
"""

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup, escape

from elements_caos.models import Elemento, Scopritore, Sezione, SezioneEstesa
from elements_caos.render.atomo_svg import nome_file_atomo
from elements_caos.render.avvertenza import AVVERTENZA_IA
from elements_caos.render.diagrammi import Vicini, formatta_anno, preposizione_articolata
from elements_caos.render.note import (
    ETICHETTE_CATEGORIA,
    TITOLI_SEZIONE_ESTESA,
    ContestoNota,
    formatta_configurazione_elettronica,
    formatta_decimale,
    formatta_stato_ossidazione,
    kelvin_in_celsius,
)
from elements_caos.render.prosa import (
    componi_sezione,
    componi_sezione_estesa,
    conta_parole,
    tempo_lettura_minuti,
)

CARTELLA_TEMPLATE = Path(__file__).parent / "templates"
CARTELLA_STATICI = Path(__file__).parent / "statico"

# Prefissi degli URL. Sono quelli già pubblicati con Quartz al Task 23: il sito
# è pubblico e i collegamenti esistenti non devono rompersi.
URL_ELEMENTI = "elementi"
URL_SCOPRITORI = "scopritori"
URL_EPOCHE = "epoche"

# Le sezioni della nota, nell'ordine in cui si leggono, con il titolo che
# portano nella pagina.
SEZIONI_IN_PAGINA: tuple[tuple[Sezione, str], ...] = (
    (Sezione.STORIA, "Storia della scoperta"),
    (Sezione.CARATTERISTICHE, "Caratteristiche"),
    (Sezione.USI, "Usi e presenza in natura"),
    (Sezione.CURIOSITA, "Curiosità"),
)

_CORSIVO = re.compile(r"\*([^*]+)\*")


def slug(testo: str) -> str:
    """Converte un titolo nello slug usato negli URL del sito.

    Accenti e apostrofi si conservano: ``epoche/l'età-dell'elettrolisi`` è un
    URL già pubblicato, e normalizzarlo in ASCII romperebbe i collegamenti
    esistenti. L'unica trasformazione è il minuscolo con gli spazi in trattini.
    """
    return testo.strip().lower().replace(" ", "-")


def url_elemento(elemento: Elemento) -> str:
    """URL della pagina di un elemento."""
    return f"{URL_ELEMENTI}/{slug(elemento.nome)}.html"


def url_approfondimento(elemento: Elemento) -> str:
    """URL della storia estesa di un elemento (Task 24, Step 6).

    Definito qui perché la scheda vi rimanda già: la pagina nasce con il primo
    approfondimento scritto, e i due devono concordare sull'indirizzo.
    """
    return f"{URL_ELEMENTI}/{slug(elemento.nome)}-storia-estesa.html"


def url_scopritore(scopritore: Scopritore) -> str:
    """URL della pagina di uno scopritore."""
    return f"{URL_SCOPRITORI}/{slug(scopritore.nome)}.html"


def url_epoca(nome_epoca: str) -> str:
    """URL della pagina di un'epoca."""
    return f"{URL_EPOCHE}/{slug(nome_epoca)}.html"


def paragrafi_html(testo: str) -> Markup:
    """Converte in paragrafi HTML la prosa composta da ``prosa.componi_sezione``.

    Il testo dei beat è prosa pura: l'unico markup che ``prosa.py`` introduce
    sono le formule di cautela in corsivo (``*Per tradizione:*``). Tutto il
    resto viene dai dati e va neutralizzato prima di finire in pagina — le
    parentesi quadre invece si conservano, perché in questo dominio sono
    configurazioni elettroniche (``[Rn]``) e non collegamenti.
    """
    paragrafi = []
    for blocco in testo.split("\n\n"):
        blocco = blocco.strip()
        if not blocco:
            continue
        # Si sfugge prima e si applica il corsivo dopo: l'escape non produce
        # asterischi, quindi non può creare corsivi che nei dati non c'erano.
        sicuro = _CORSIVO.sub(r"<em>\1</em>", str(escape(blocco)))
        paragrafi.append(f"<p>{sicuro}</p>")
    return Markup("\n".join(paragrafi))


def dati_elemento(elemento: Elemento) -> list[tuple[str, str]]:
    """Raccoglie i dati fisico-chimici come coppie etichetta/valore.

    Sono gli stessi valori della tabella nella nota del vault, con gli stessi
    formattatori: una seconda formattazione produrrebbe prima o poi due cifre
    diverse per lo stesso dato. Qui però non è una tabella — a 390 px una
    tabella o spezza le parole o scorre in orizzontale — ma una lista di
    descrizione, che si impila.
    """
    proprieta = elemento.proprieta
    voci: list[tuple[str, str]] = [
        ("Numero atomico", str(elemento.numero_atomico)),
        ("Massa atomica", f"{formatta_decimale(proprieta.massa_atomica)} u"),
        ("Categoria", ETICHETTE_CATEGORIA[proprieta.categoria]),
        ("Gruppo", str(proprieta.gruppo) if proprieta.gruppo is not None else "—"),
        ("Periodo", str(proprieta.periodo)),
        ("Blocco", proprieta.blocco),
        (
            "Configurazione elettronica",
            formatta_configurazione_elettronica(proprieta.configurazione_elettronica),
        ),
        ("Punto di fusione", kelvin_in_celsius(proprieta.punto_fusione_k)),
        ("Punto di ebollizione", kelvin_in_celsius(proprieta.punto_ebollizione_k)),
        (
            "Densità",
            f"{formatta_decimale(proprieta.densita)} g/cm³"
            if proprieta.densita is not None
            else "—",
        ),
        (
            "Stati di ossidazione",
            ", ".join(formatta_stato_ossidazione(stato) for stato in proprieta.stati_ossidazione)
            or "—",
        ),
    ]
    return voci


def celle_vicine(vicini: Vicini) -> list[dict[str, object]]:
    """Descrive i vicini nella tavola periodica come celle di una griglia.

    In HTML invece che in un diagramma: il testo resta selezionabile, un
    lettore di schermo lo annuncia e la griglia si adatta alla larghezza.
    """
    posizioni = (
        ("sopra", vicini.sopra, "stesso gruppo"),
        ("sinistra", vicini.sinistra, "stesso periodo"),
        ("destra", vicini.destra, "stesso periodo"),
        ("sotto", vicini.sotto, "stesso gruppo"),
    )
    return [
        {"dove": dove, "elemento": vicino, "relazione": relazione}
        for dove, vicino, relazione in posizioni
        if vicino is not None
    ]


def ambiente_sito() -> Environment:
    """Costruisce l'ambiente Jinja2 delle pagine del sito.

    A differenza di quello del vault, qui l'autoescape è acceso: il Markdown
    tollera un carattere speciale non sfuggito, l'HTML no.
    """
    ambiente = Environment(
        loader=FileSystemLoader(CARTELLA_TEMPLATE),
        undefined=StrictUndefined,
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    ambiente.globals["avvertenza_ia"] = _avvertenza_html()
    return ambiente


def _avvertenza_html() -> Markup:
    """Rende in HTML l'avvertenza sull'uso dell'IA, condivisa con il vault.

    La fonte del testo è una sola (``render.avvertenza``): qui se ne toglie la
    sintassi dei callout di Obsidian, che nel browser non significa nulla.
    """
    righe = [
        riga.lstrip("> ").strip()
        for riga in AVVERTENZA_IA.splitlines()
        if riga.startswith(">") and not riga.startswith("> [!")
    ]
    corpo = " ".join(riga for riga in righe if riga)
    return Markup(str(paragrafi_html(_grassetto_in_html(corpo))))


def _grassetto_in_html(testo: str) -> str:
    """Conserva il grassetto Markdown dell'avvertenza."""
    return testo.replace("**", "*")


def rendi_elemento(contesto: ContestoNota) -> str:
    """Compone la pagina HTML completa di un elemento.

    Il risultato è deterministico: a parità di dati in ingresso i byte emessi
    sono gli stessi, come per le note del vault.
    """
    elemento = contesto.elemento
    # `contenuti` è opzionale nel modello: un elemento può esistere nei dati
    # prima che i suoi testi siano scritti, e la pagina deve reggere lo stesso.
    contenuti = elemento.contenuti
    sezioni = (
        [
            {"titolo": titolo, "corpo": paragrafi_html(componi_sezione(contenuti, sezione))}
            for sezione, titolo in SEZIONI_IN_PAGINA
            if contenuti.beats_per_sezione(sezione)
        ]
        if contenuti
        else []
    )
    incipit = (
        paragrafi_html(componi_sezione(contenuti, Sezione.INCIPIT)) if contenuti else Markup("")
    )
    hook = contenuti.hook if contenuti else ""
    parole = conta_parole(
        " ".join(beat.testo for beat in contenuti.beats) + " " + hook if contenuti else ""
    )

    modello = ambiente_sito().get_template("elemento.html.j2")
    return modello.render(
        elemento=elemento,
        contesto=contesto,
        hook=hook,
        incipit=incipit,
        sezioni=sezioni,
        minuti=tempo_lettura_minuti(parole),
        dati=dati_elemento(elemento),
        vicini=celle_vicine(contesto.vicini),
        anno_leggibile=formatta_anno(elemento.scoperta.anno),
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
        preposizione_del=preposizione_articolata("de", elemento.nome) + elemento.nome.lower(),
        file_atomo=nome_file_atomo(elemento),
        url_elemento=url_elemento,
        url_approfondimento=url_approfondimento,
        url_scopritore=url_scopritore,
        url_epoca=url_epoca,
    )


def rendi_approfondimento_sito(contesto: ContestoNota) -> str:
    """Compone la pagina HTML della storia estesa di un elemento.

    Nasce con il primo approfondimento scritto (Task 24): la scheda vi rimanda
    già tramite ``url_approfondimento``. Le sezioni vuote non compaiono, come
    nel vault. Deterministica come le altre pagine.
    """
    elemento = contesto.elemento
    contenuti = elemento.contenuti_estesi
    if contenuti is None:
        raise ValueError(
            f"{elemento.nome}: contenuti_estesi assenti, nessuna storia estesa da emettere"
        )

    sezioni = [
        {
            "titolo": TITOLI_SEZIONE_ESTESA[sezione],
            "corpo": paragrafi_html(componi_sezione_estesa(contenuti, sezione)),
        }
        for sezione in SezioneEstesa
        if contenuti.beats_per_sezione(sezione)
    ]
    parole = conta_parole(" ".join(beat.testo for beat in contenuti.beats) + " " + contenuti.hook)

    modello = ambiente_sito().get_template("approfondimento.html.j2")
    return modello.render(
        elemento=elemento,
        contesto=contesto,
        hook=contenuti.hook,
        sezioni=sezioni,
        minuti=tempo_lettura_minuti(parole),
        anno_leggibile=formatta_anno(elemento.scoperta.anno),
        preposizione_del=preposizione_articolata("de", elemento.nome) + elemento.nome.lower(),
        url_elemento=url_elemento,
        url_epoca=url_epoca,
    )
