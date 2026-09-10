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

from elements_caos.models import Elemento, Scopritore, Sezione
from elements_caos.render.avvertenza import AVVERTENZA_IA
from elements_caos.render.note import ContestoNota
from elements_caos.render.prosa import componi_sezione, conta_parole, tempo_lettura_minuti

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
        url_elemento=url_elemento,
        url_scopritore=url_scopritore,
        url_epoca=url_epoca,
    )
