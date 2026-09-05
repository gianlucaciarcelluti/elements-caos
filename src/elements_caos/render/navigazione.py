"""Generazione delle note di navigazione del vault.

Cronologia, epoche, scopritori e tavola periodica: le pagine che legano fra
loro le note dei singoli elementi.
"""

from dataclasses import dataclass

from elements_caos.caricamento import ordina_per_scoperta
from elements_caos.models import Categoria, Elemento, Epoca, Scopritore, Tappa
from elements_caos.render.diagrammi import formatta_anno
from elements_caos.render.note import ambiente_template


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


def _voci(
    elementi: list[Elemento],
    scopritori: dict[str, Scopritore],
    scostamento: int = 0,
) -> list[VoceElemento]:
    """Costruisce le righe di tabella per gli elementi indicati.

    Risolve gli id di ``elemento.scoperta.scopritori`` nei nomi propri tramite
    il dizionario ``scopritori`` (Task 3): è l'unico punto che fa questa
    risoluzione, per non doverla ripetere in ogni funzione che compone una
    tabella di navigazione.
    """
    return [
        VoceElemento(
            posizione=indice + scostamento,
            anno=formatta_anno(elemento.scoperta.anno),
            nome=elemento.nome,
            simbolo=elemento.simbolo,
            scopritori=", ".join(
                scopritori[identificativo].nome
                for identificativo in elemento.scoperta.scopritori
                if identificativo in scopritori
            )
            or "ignoto",
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
        voci = [
            VoceElemento(
                posizione=posizioni[elemento.numero_atomico],
                anno=formatta_anno(elemento.scoperta.anno),
                nome=elemento.nome,
                simbolo=elemento.simbolo,
                scopritori=", ".join(
                    scopritori[identificativo].nome
                    for identificativo in elemento.scoperta.scopritori
                    if identificativo in scopritori
                )
                or "ignoto",
            )
            for elemento in della_epoca
        ]
        gruppi.append(GruppoEpoca(epoca=epoca, voci=voci))

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
    return modello.render(scopritore=scopritore, voci=_voci(suoi, scopritori))


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
        "| Immagine | Autore | Licenza | Fonte |",
        "|---|---|---|---|",
    ]

    for scopritore in sorted(scopritori.values(), key=lambda s: s.nome):
        if scopritore.ritratto is None:
            continue
        ritratto = scopritore.ritratto
        righe.append(
            f"| {scopritore.nome} | {ritratto.autore} | {ritratto.licenza} "
            f"| [{ritratto.file}]({ritratto.fonte}) |"
        )

    return "\n".join(righe) + "\n"
