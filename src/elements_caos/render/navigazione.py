"""Generazione delle note di navigazione del vault.

Cronologia, epoche, scopritori e tavola periodica: le pagine che legano fra
loro le note dei singoli elementi.
"""

from dataclasses import dataclass

from elements_caos.caricamento import ordina_per_scoperta
from elements_caos.models import Categoria, Elemento, Epoca, Scopritore, Tappa
from elements_caos.render.avvertenza import AVVERTENZA_IA
from elements_caos.render.diagrammi import formatta_anno
from elements_caos.render.note import ambiente_template, url_per_markdown


@dataclass(frozen=True)
class VoceElemento:
    """Riga di una tabella di navigazione che rimanda a un elemento."""

    posizione: int
    anno: str
    nome: str
    simbolo: str
    scopritori: str


@dataclass(frozen=True)
class GruppoEpoca:
    """Insieme degli elementi scoperti in una determinata epoca."""

    epoca: Epoca
    voci: list[VoceElemento]


def _wikilink_scopritori(
    elemento: Elemento,
    scopritori: dict[str, Scopritore],
    escludi: str | None,
) -> str:
    """Risolve gli id degli scopritori di un elemento in wikilink ai loro nomi.

    È l'unico punto del modulo che risolve ``elemento.scoperta.scopritori`` in
    testo per una cella di tabella: nessun'altra funzione duplica questa
    logica. Due eccezioni deliberate non producono un wikilink:

    - l'id in ``escludi`` (il titolo della pagina corrente in
      ``rendi_scopritore``: linkarlo sarebbe un auto-riferimento a se stessa);
    - il caso senza scopritori noti, dove il testo resta "ignoto" anziché
      diventare ``[[ignoto]]``, un wikilink verso una nota inesistente.
    """
    nomi = [
        f"[[{scopritori[identificativo].nome}]]"
        if identificativo != escludi
        else scopritori[identificativo].nome
        for identificativo in elemento.scoperta.scopritori
        if identificativo in scopritori
    ]
    return ", ".join(nomi) or "ignoto"


def _voci(
    elementi: list[Elemento],
    scopritori: dict[str, Scopritore],
    posizioni: dict[int, int] | None = None,
    escludi: str | None = None,
) -> list[VoceElemento]:
    """Costruisce le righe di tabella per gli elementi indicati.

    ``posizioni`` mappa il numero atomico alla posizione nell'ordine
    cronologico globale (usata da ``rendi_cronologia``, dove la numerazione
    deve restare quella dell'intero vault anche dentro il raggruppamento per
    epoca); se assente, la posizione è l'indice locale nella lista ricevuta
    (adeguato per le tabelle di un'epoca o di uno scopritore, che non
    dichiarano una posizione globale). ``escludi`` è propagato a
    ``_wikilink_scopritori`` per evitare l'auto-wikilink di uno scopritore
    verso la propria pagina.
    """
    return [
        VoceElemento(
            posizione=(posizioni[elemento.numero_atomico] if posizioni is not None else indice),
            anno=formatta_anno(elemento.scoperta.anno),
            nome=elemento.nome,
            simbolo=elemento.simbolo,
            scopritori=_wikilink_scopritori(elemento, scopritori, escludi),
        )
        for indice, elemento in enumerate(elementi, start=1)
    ]


def rendi_cronologia(
    elementi: list[Elemento],
    epoche: dict[str, Epoca],
    tappe: list[Tappa],
    scopritori: dict[str, Scopritore],
) -> str:
    """Genera l'indice cronologico, spina dorsale del vault.

    Gli elementi sono raggruppati per epoca e ordinati per anno di scoperta;
    l'itinerario guidato propone un percorso di lettura di circa un'ora.
    """
    cronologia = ordina_per_scoperta(elementi)
    posizioni = {e.numero_atomico: i for i, e in enumerate(cronologia, start=1)}

    gruppi: list[GruppoEpoca] = []
    for identificativo, epoca in sorted(epoche.items(), key=lambda voce: voce[1].anno_inizio):
        della_epoca = [e for e in cronologia if e.scoperta.epoca == identificativo]
        if not della_epoca:
            continue
        gruppi.append(
            GruppoEpoca(epoca=epoca, voci=_voci(della_epoca, scopritori, posizioni=posizioni))
        )

    modello = ambiente_template().get_template("cronologia.md.j2")
    return modello.render(totale=len(elementi), tappe=tappe, gruppi=gruppi)


def rendi_epoca(epoca: Epoca, elementi: list[Elemento], scopritori: dict[str, Scopritore]) -> str:
    """Genera la nota di contesto storico di un'epoca."""
    della_epoca = ordina_per_scoperta([e for e in elementi if e.scoperta.epoca == epoca.id])
    modello = ambiente_template().get_template("epoca.md.j2")
    return modello.render(epoca=epoca, voci=_voci(della_epoca, scopritori))


def rendi_scopritore(
    scopritore: Scopritore, elementi: list[Elemento], scopritori: dict[str, Scopritore]
) -> str:
    """Genera la nota di uno scopritore, con i suoi elementi e il suo ritratto."""
    suoi = ordina_per_scoperta([e for e in elementi if scopritore.id in e.scoperta.scopritori])
    modello = ambiente_template().get_template("scopritore.md.j2")
    return modello.render(
        scopritore=scopritore, voci=_voci(suoi, scopritori, escludi=scopritore.id)
    )


def rendi_tavola(elementi: list[Elemento], scopritori: dict[str, Scopritore]) -> str:
    """Genera la tavola periodica navigabile, con ogni casella come wikilink."""
    per_posizione = {
        (e.proprieta.periodo, e.proprieta.gruppo): e
        for e in elementi
        if e.proprieta.gruppo is not None
    }

    righe = []
    for periodo in range(1, 8):
        celle = []
        for gruppo in range(1, 19):
            elemento = per_posizione.get((periodo, gruppo))
            celle.append(f"[[{elemento.nome}\\|{elemento.simbolo}]]" if elemento else "")
        righe.append({"periodo": periodo, "celle": celle})

    blocchi_f = []
    for categoria, nome in (
        (Categoria.LANTANIDE, "Lantanidi"),
        (Categoria.ATTINIDE, "Attinidi"),
    ):
        voci = sorted(
            (e for e in elementi if e.proprieta.categoria is categoria),
            key=lambda e: e.numero_atomico,
        )
        if voci:
            blocchi_f.append({"nome": nome, "voci": _voci(voci, scopritori)})

    modello = ambiente_template().get_template("tavola.md.j2")
    return modello.render(righe=righe, blocchi_f=blocchi_f)


def rendi_attribuzioni(scopritori: dict[str, Scopritore]) -> str:
    """Genera la pagina dei crediti delle immagini usate nel vault.

    Le immagini sono tutte in pubblico dominio o CC0 e non richiederebbero
    attribuzione: la si fornisce comunque come buona pratica verso chi riusa.
    """
    righe_tabella = []
    for scopritore in sorted(scopritori.values(), key=lambda s: s.nome):
        if scopritore.ritratto is None:
            continue
        ritratto = scopritore.ritratto
        righe_tabella.append(
            f"| {scopritore.nome} | {ritratto.autore} | {ritratto.licenza} "
            f"| [{ritratto.file}]({url_per_markdown(ritratto.fonte)}) |"
        )

    righe = [
        "---",
        "titolo: Attribuzioni",
        "tipo: servizio",
        "tags: [servizio, licenze]",
        "---",
        "",
        "# Attribuzioni delle immagini",
        "",
        "Tutte le immagini del vault sono in pubblico dominio o rilasciate in CC0.",
        "L'attribuzione qui riportata non è dovuta per licenza: è una cortesia",
        "verso gli autori e verso chi vorrà riusare questo materiale.",
        "",
    ]

    if righe_tabella:
        righe.append("| Immagine | Autore | Licenza | Fonte |")
        righe.append("|---|---|---|---|")
        righe.extend(righe_tabella)
    else:
        righe.append("*Nessuna immagine con attribuzione registrata.*")

    righe.extend(["", AVVERTENZA_IA])

    return "\n".join(righe) + "\n"
