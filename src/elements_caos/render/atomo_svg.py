"""Generatore del modello di Bohr in SVG per la struttura atomica.

Sostituisce il diagramma Mermaid ``diagramma_atomo`` (che dispone i gusci
come una catena orizzontale di riquadri, inadatta a rappresentare qualcosa
di concentrico): qui ogni guscio elettronico diventa un'orbita circolare
intorno al nucleo, con gli elettroni disposti sull'orbita.

Vincoli non negoziabili, verificati nel brief del Task 12b:

- Un solo file per diagramma, colori neutri, **nessuna** media query e
  nessun tag ``<style>``: GitHub rimuove gli stili dagli SVG, e una media
  query dentro un SVG referenziato via ``<img>`` si valuta sul tema di
  sistema, non su quello della pagina che lo incorpora.
- Solo i colori della palette ``COLORI``, misurata per stare sopra la
  soglia WCAG di contrasto (3.0) sia su sfondo bianco sia su sfondo nero.
- L'SVG va sempre referenziato come file (``nome_file_atomo``), mai
  incorporato inline nel Markdown: GitHub ignora l'SVG inline.
"""

import math

from elements_caos.models import Elemento

# Palette misurata su bianco (#ffffff) e nero (#0d1117): ogni colore supera
# la soglia WCAG 3.0 per elementi grafici su entrambi i fondi. Non usare
# altri colori nell'SVG: romperebbero la leggibilità su uno dei due temi.
COLORI: dict[str, str] = {
    "orbite": "#7d8590",
    "elettroni_interni": "#4c8eda",
    "nucleo": "#b26a00",
    "valenza": "#3d8b40",
}

# Sopra questa soglia di elettroni in un singolo guscio, disegnarli tutti
# come punti distinti produce un anello illeggibile (i punti si accavallano
# geometricamente sulla circonferenza). Scelta provando sul plutonio
# ([2, 8, 18, 32, 24, 8, 2], il caso con più gusci sopra soglia
# contemporaneamente): a soglia 20 il guscio da 18 elettroni resta a punti,
# ma affollati — visibili come punti solo ravvicinandosi molto all'immagine;
# a soglia 12 anche i due gusci da 8 (interno e di valenza) passerebbero a
# conteggio, perdendo inutilmente informazione visiva su un numero che sta
# comunque bene a punti. 16 è la soglia dove i gusci piccoli (2, 8) restano
# leggibili a punti e i gusci grandi (18, 24, 32) diventano conteggio pulito,
# senza zona grigia intermedia.
SOGLIA_CONTEGGIO = 16

# Lato del riquadro SVG (quadrato), fisso indipendentemente dal numero di
# gusci: le note del vault restano uniformi. Cambia solo il passo fra
# un'orbita e la successiva.
_LATO = 320.0
_CENTRO = _LATO / 2

# Raggio del nucleo e dell'orbita più interna: spazio fisso riservato al
# centro prima che inizino le orbite elettroniche.
_RAGGIO_NUCLEO = 22.0
_RAGGIO_PRIMA_ORBITA = 48.0

# Margine fra l'orbita più esterna e il bordo del riquadro, per lasciare
# spazio all'eventuale etichetta del conteggio sopra l'orbita.
_MARGINE_ESTERNO = 26.0

# Raggio dei punti-elettrone, distinto da quello dei punti-nucleo per
# leggibilità.
_RAGGIO_ELETTRONE = 5.0


def _passo_orbita(numero_gusci: int) -> float:
    """Calcola la distanza fra orbite successive, dato il numero di gusci.

    Il raggio disponibile fra la prima orbita e il bordo del riquadro è
    fisso: dividerlo per il numero di gusci mantiene l'intero diagramma
    dentro il ``viewBox`` anche nel caso limite di sette gusci (plutonio,
    oganesson), mentre con un solo guscio (idrogeno) l'orbita usa l'intero
    spazio disponibile invece di restare artificiosamente piccola.
    """
    raggio_disponibile = _CENTRO - _MARGINE_ESTERNO - _RAGGIO_PRIMA_ORBITA
    if numero_gusci <= 1:
        return raggio_disponibile
    return raggio_disponibile / (numero_gusci - 1)


def _raggio_orbita(indice: int, numero_gusci: int) -> float:
    """Raggio della circonferenza del guscio ``indice`` (a partire da 0)."""
    return _RAGGIO_PRIMA_ORBITA + indice * _passo_orbita(numero_gusci)


def _cerchio(cx: float, cy: float, r: float, fill: str, stroke: str | None = None) -> str:
    """Serializza un elemento ``<circle>`` con attributi di colore inline."""
    attributo_stroke = f' stroke="{stroke}" stroke-width="2"' if stroke else ""
    return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}"{attributo_stroke}/>'


def _testo(x: float, y: float, contenuto: str, colore: str, dimensione: float = 13.0) -> str:
    """Serializza un elemento ``<text>`` centrato orizzontalmente sul punto dato."""
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" fill="{colore}" font-size="{dimensione:.1f}" '
        'font-family="sans-serif" text-anchor="middle">'
        f"{contenuto}</text>"
    )


def _punti_elettrone(indice_guscio: int, numero_gusci: int, elettroni: int, e_valenza: bool) -> str:
    """Disegna gli elettroni di un guscio come punti distinti sull'orbita.

    I punti sono distribuiti a intervalli angolari regolari, a partire da
    "ore 12" (angolo -90°), per restare simmetrici e prevedibili in ogni
    caso, incluso il guscio con un solo elettrone.
    """
    raggio_orbita = _raggio_orbita(indice_guscio, numero_gusci)
    colore = COLORI["valenza"] if e_valenza else COLORI["elettroni_interni"]

    frammenti = []
    for i in range(elettroni):
        angolo = -math.pi / 2 + (2 * math.pi * i / elettroni)
        x = _CENTRO + raggio_orbita * math.cos(angolo)
        y = _CENTRO + raggio_orbita * math.sin(angolo)
        frammenti.append(_cerchio(x, y, _RAGGIO_ELETTRONE, colore))
    return "".join(frammenti)


def _angolo_etichetta(ordine_fra_conteggi: int) -> float:
    """Angolo, in radianti, a cui posizionare l'etichetta del conteggio.

    ``ordine_fra_conteggi`` è la posizione del guscio nella sola sequenza
    dei gusci renderizzati come conteggio (non l'indice assoluto del
    guscio): alternare in base all'indice assoluto del guscio fallisce
    quando due gusci sopra soglia hanno la stessa parità pur non essendo
    adiacenti fra i soli conteggi (l'oganesson [2, 8, 18, 32, 32, 18, 8] ha
    i conteggi agli indici 2, 3, 4, 5 — parità 0,1,0,1 — che con
    l'alternanza sull'indice assoluto metterebbe gli indici 3 e 5 allo
    stesso angolo, sovrapponendo le etichette "32" e "18"). Alternando
    invece sulla posizione relativa fra i soli conteggi (0,1,2,3 in
    quell'esempio), ogni conteggio consecutivo cade sempre all'angolo
    opposto rispetto al precedente.
    """
    return -math.pi / 2 if ordine_fra_conteggi % 2 == 0 else 0.0


def _conteggio_guscio(
    indice_guscio: int, numero_gusci: int, elettroni: int, e_valenza: bool, ordine_fra_conteggi: int
) -> str:
    """Disegna il solo conteggio numerico, per un guscio sopra la soglia di leggibilità.

    Nessun cerchio di sfondo dietro al numero: un cerchio pieno del colore
    del guscio richiederebbe un testo bianco sopra per restare leggibile, e
    il bianco non fa parte della palette misurata (romperebbe il vincolo "un
    solo file, solo colori neutri della palette" su un fondo che può essere
    sia chiaro sia scuro). Il numero è quindi scritto direttamente nel
    colore del guscio, in grassetto per distinguerlo dal resto del testo, e
    un piccolo anello scoperto (solo stroke, stesso colore) lo racchiude per
    marcare visivamente "qui c'è un guscio compresso", coerente col
    linguaggio a punti usato sotto soglia. La posizione angolare alterna fra
    conteggi consecutivi (``_angolo_etichetta``) per non impilare più
    etichette sullo stesso raggio quando più gusci sono sopra soglia.
    """
    raggio_orbita = _raggio_orbita(indice_guscio, numero_gusci)
    colore = COLORI["valenza"] if e_valenza else COLORI["elettroni_interni"]
    angolo = _angolo_etichetta(ordine_fra_conteggi)
    x = _CENTRO + raggio_orbita * math.cos(angolo)
    y = _CENTRO + raggio_orbita * math.sin(angolo)
    anello = _cerchio(x, y, _RAGGIO_ELETTRONE + 9.0, "none", stroke=colore)
    testo = (
        f'<text x="{x:.2f}" y="{y + 4.5:.2f}" fill="{colore}" font-size="12.0" '
        'font-family="sans-serif" font-weight="bold" text-anchor="middle">'
        f"{elettroni}</text>"
    )
    return anello + testo


def rendi_atomo_svg(elemento: Elemento) -> str:
    """Genera il modello di Bohr dell'elemento come SVG completo.

    Nucleo al centro con il numero atomico, un'orbita circolare per guscio,
    gli elettroni come punti sull'orbita. Sopra ``SOGLIA_CONTEGGIO``
    elettroni in un guscio, disegna il solo conteggio numerico al posto dei
    punti: oltre quella soglia i punti si accavallerebbero sulla
    circonferenza e il disegno diventerebbe illeggibile. Il guscio più
    esterno (di valenza) usa sempre il colore dedicato, sia disegnato a
    punti sia come conteggio.

    Dimensioni del riquadro fisse (``_LATO``  x ``_LATO``): variano solo il
    passo fra le orbite, in modo che le note restino visivamente uniformi a
    prescindere dal numero di gusci dell'elemento.
    """
    gusci = elemento.proprieta.gusci
    numero_gusci = len(gusci)

    frammenti: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_LATO:.0f}" height="{_LATO:.0f}" '
        f'viewBox="0 0 {_LATO:.0f} {_LATO:.0f}">'
    ]

    # Orbite: un cerchio non riempito (solo contorno) per ciascun guscio,
    # disegnate per prime così restano sotto nucleo ed elettroni.
    for indice in range(numero_gusci):
        raggio = _raggio_orbita(indice, numero_gusci)
        frammenti.append(
            f'<circle cx="{_CENTRO:.2f}" cy="{_CENTRO:.2f}" r="{raggio:.2f}" '
            f'fill="none" stroke="{COLORI["orbite"]}" stroke-width="1.5"/>'
        )

    # Elettroni (o conteggio) per ciascun guscio, guscio di valenza escluso
    # (l'ultimo) marcato col colore dedicato. ``ordine_fra_conteggi`` conta
    # solo i gusci renderizzati come conteggio, non l'indice assoluto: serve
    # a ``_angolo_etichetta`` per alternare la posizione fra conteggi
    # consecutivi anche quando non sono adiacenti come indice di guscio.
    ordine_fra_conteggi = 0
    for indice, elettroni in enumerate(gusci):
        e_valenza = indice == numero_gusci - 1
        if elettroni > SOGLIA_CONTEGGIO:
            frammenti.append(
                _conteggio_guscio(indice, numero_gusci, elettroni, e_valenza, ordine_fra_conteggi)
            )
            ordine_fra_conteggi += 1
        else:
            frammenti.append(_punti_elettrone(indice, numero_gusci, elettroni, e_valenza))

    # Nucleo, disegnato sopra le orbite ma sotto nulla: è il punto focale.
    # L'etichetta Z sta SOTTO il cerchio del nucleo, non sovrapposta: un
    # numero bianco sopra il fondo arancione richiederebbe un colore fuori
    # palette, e il grigio della palette (pensato per testo secondario) non
    # si leggerebbe abbastanza sopra l'arancione del nucleo (i due colori
    # della palette non sono stati misurati l'uno contro l'altro, solo
    # ciascuno contro bianco e nero).
    frammenti.append(_cerchio(_CENTRO, _CENTRO, _RAGGIO_NUCLEO, COLORI["nucleo"]))
    frammenti.append(
        _testo(
            _CENTRO,
            _CENTRO + _RAGGIO_NUCLEO + 14.0,
            f"Z={elemento.numero_atomico}",
            COLORI["orbite"],
            dimensione=12.0,
        )
    )

    frammenti.append("</svg>")
    return "\n".join(frammenti)


def nome_file_atomo(elemento: Elemento) -> str:
    """Restituisce il nome del file SVG del diagramma atomico dell'elemento.

    Segue la stessa convenzione di ``nome_file_nota``: nome proprio
    dell'elemento come identificatore, qui prefissato da ``atomo-`` e con
    estensione ``.svg`` per distinguerlo dalla nota Markdown.
    """
    return f"atomo-{elemento.nome}.svg"
