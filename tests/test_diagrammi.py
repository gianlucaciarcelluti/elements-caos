"""Test dei generatori di diagrammi Mermaid."""

import pytest

from elements_caos.models import (
    Categoria,
    Composto,
    Elemento,
    Proprieta,
    Scoperta,
)
from elements_caos.render.diagrammi import (
    calcola_vicini,
    diagramma_atomo,
    diagramma_composti,
    diagramma_posizione,
    diagramma_timeline,
    formatta_anno,
)

TIPI_AMMESSI = ("flowchart", "timeline", "graph")


def _elemento(
    numero: int,
    nome: str,
    simbolo: str,
    gruppo: int | None,
    periodo: int,
    gusci: list[int],
    anno: int = 1800,
    blocco: str = "p",
    categoria: Categoria = Categoria.NON_METALLO,
    composti: list[Composto] | None = None,
    isolamento: int | None = None,
) -> Elemento:
    """Costruisce un elemento di prova con i campi minimi necessari."""
    return Elemento(
        numero_atomico=numero,
        simbolo=simbolo,
        nome=nome,
        nome_en=nome,
        scoperta=Scoperta(
            anno=anno,
            anno_stimato=anno < 1500,
            scopritori=["tizio"],
            epoca="test",
            isolamento_anno=isolamento,
        ),
        proprieta=Proprieta(
            gruppo=gruppo,
            periodo=periodo,
            blocco=blocco,
            categoria=categoria,
            massa_atomica=float(numero) * 2,
            configurazione_elettronica="[Ne] 3s2",
            gusci=gusci,
            stati_ossidazione=[],
        ),
        approfondimento=False,
        composti_principali=composti or [],
        fonti=[],
    )


def _fosforo() -> Elemento:
    """Elemento di riferimento per i test: il fosforo."""
    return _elemento(15, "Fosforo", "P", 15, 3, [2, 8, 5], anno=1669, isolamento=1669)


def _blocco_mermaid_valido(testo: str) -> bool:
    """Verifica che il testo sia un blocco Mermaid recintato di tipo ammesso."""
    righe = testo.strip().splitlines()
    if righe[0].strip() != "```mermaid" or righe[-1].strip() != "```":
        return False
    return righe[1].strip().startswith(TIPI_AMMESSI)


def test_timeline_e_blocco_mermaid_valido() -> None:
    """Il diagramma della scoperta è un blocco Mermaid recintato di tipo ammesso."""
    assert _blocco_mermaid_valido(diagramma_timeline(_fosforo(), ["Tizio"]))


def test_timeline_contiene_anno_di_scoperta() -> None:
    """La timeline riporta l'anno di scoperta dell'elemento."""
    assert "1669" in diagramma_timeline(_fosforo(), ["Tizio"])


def test_timeline_di_elemento_antico_usa_avanti_cristo() -> None:
    """Per gli elementi antichi la timeline mostra gli anni in forma 'a.C.'."""
    rame = _elemento(29, "Rame", "Cu", 11, 4, [2, 8, 18, 1], anno=-9000)

    risultato = diagramma_timeline(rame, ["Tizio"])

    assert "9000 a.C." in risultato


def test_timeline_distingue_scoperta_e_isolamento() -> None:
    """Se isolamento e scoperta differiscono, la timeline mostra due tappe distinte."""
    berillio = _elemento(4, "Berillio", "Be", 2, 2, [2, 2], anno=1798, isolamento=1828)

    risultato = diagramma_timeline(berillio, ["Tizio"])

    assert "1798" in risultato
    assert "1828" in risultato


def test_timeline_usa_i_nomi_degli_scopritori_non_gli_id() -> None:
    """La timeline mostra i nomi propri passati esplicitamente, non gli id kebab-case.

    ``scoperta.scopritori`` contiene identificativi (es. ``hennig-brand``), che
    rimandano a ``scopritori.yaml``: il diagramma non deve mai stamparli, deve
    ricevere e mostrare i nomi già risolti dal chiamante. È il test che avrebbe
    intercettato il difetto: con ``scopritori=["tizio"]`` id e nome sono
    indistinguibili, qui invece divergono esplicitamente.
    """
    fosforo = _elemento(15, "Fosforo", "P", 15, 3, [2, 8, 5], anno=1669, isolamento=1669)
    fosforo.scoperta.scopritori = ["hennig-brand"]

    risultato = diagramma_timeline(fosforo, ["Hennig Brand"])

    assert "Hennig Brand" in risultato
    assert "hennig-brand" not in risultato


def test_formatta_anno() -> None:
    """Gli anni negativi diventano 'a.C.', i positivi restano nudi."""
    assert formatta_anno(1669) == "1669"
    assert formatta_anno(-9000) == "9000 a.C."
    assert formatta_anno(300) == "300"


def test_posizione_e_blocco_mermaid_valido() -> None:
    """Il diagramma di posizione è un blocco Mermaid recintato di tipo ammesso."""
    fosforo = _fosforo()
    azoto = _elemento(7, "Azoto", "N", 15, 2, [2, 5])
    arsenico = _elemento(33, "Arsenico", "As", 15, 4, [2, 8, 18, 5])
    silicio = _elemento(14, "Silicio", "Si", 14, 3, [2, 8, 4])
    zolfo = _elemento(16, "Zolfo", "S", 16, 3, [2, 8, 6])

    vicini = calcola_vicini(fosforo, [fosforo, azoto, arsenico, silicio, zolfo])

    assert _blocco_mermaid_valido(diagramma_posizione(fosforo, vicini))


def test_calcola_vicini_trova_gruppo_e_periodo() -> None:
    """I vicini sono l'elemento sopra e sotto nel gruppo, a sinistra e destra nel periodo."""
    fosforo = _fosforo()
    azoto = _elemento(7, "Azoto", "N", 15, 2, [2, 5])
    arsenico = _elemento(33, "Arsenico", "As", 15, 4, [2, 8, 18, 5])
    silicio = _elemento(14, "Silicio", "Si", 14, 3, [2, 8, 4])
    zolfo = _elemento(16, "Zolfo", "S", 16, 3, [2, 8, 6])

    vicini = calcola_vicini(fosforo, [fosforo, azoto, arsenico, silicio, zolfo])

    assert vicini.sopra is not None and vicini.sopra.simbolo == "N"
    assert vicini.sotto is not None and vicini.sotto.simbolo == "As"
    assert vicini.sinistra is not None and vicini.sinistra.simbolo == "Si"
    assert vicini.destra is not None and vicini.destra.simbolo == "S"


def test_calcola_vicini_idrogeno_non_ha_nulla_sopra() -> None:
    """L'idrogeno apre la tavola: non ha vicini sopra né a sinistra."""
    idrogeno = _elemento(1, "Idrogeno", "H", 1, 1, [1])
    elio = _elemento(2, "Elio", "He", 18, 1, [2])
    litio = _elemento(3, "Litio", "Li", 1, 2, [2, 1])

    vicini = calcola_vicini(idrogeno, [idrogeno, elio, litio])

    assert vicini.sopra is None
    assert vicini.sinistra is None
    assert vicini.sotto is not None and vicini.sotto.simbolo == "Li"


def test_calcola_vicini_lantanide_senza_gruppo() -> None:
    """Un lantanide non ha gruppo: i vicini verticali non esistono, ma il codice regge."""
    cerio = _elemento(
        58,
        "Cerio",
        "Ce",
        None,
        6,
        [2, 8, 18, 19, 9, 2],
        blocco="f",
        categoria=Categoria.LANTANIDE,
    )

    vicini = calcola_vicini(cerio, [cerio])

    assert vicini.sopra is None
    assert vicini.sotto is None


def test_posizione_con_vicini_mancanti_non_solleva_errore() -> None:
    """Il diagramma si genera anche quando alcuni vicini non esistono."""
    idrogeno = _elemento(1, "Idrogeno", "H", 1, 1, [1])
    vicini = calcola_vicini(idrogeno, [idrogeno])

    risultato = diagramma_posizione(idrogeno, vicini)

    assert _blocco_mermaid_valido(risultato)
    assert "Idrogeno" in risultato


def test_atomo_e_blocco_mermaid_valido() -> None:
    """Il diagramma della struttura atomica è un blocco Mermaid recintato valido."""
    assert _blocco_mermaid_valido(diagramma_atomo(_fosforo()))


def test_atomo_mostra_tutti_i_gusci() -> None:
    """Il diagramma atomico riporta il conteggio di elettroni di ciascun guscio."""
    risultato = diagramma_atomo(_fosforo())

    assert "2" in risultato
    assert "8" in risultato
    assert "5" in risultato


def test_atomo_evidenzia_gli_elettroni_di_valenza() -> None:
    """L'ultimo guscio è marcato come guscio di valenza."""
    assert "valenza" in diagramma_atomo(_fosforo()).lower()


def test_atomo_idrogeno_guscio_singolo() -> None:
    """Un elemento con un solo guscio genera comunque un diagramma valido."""
    idrogeno = _elemento(1, "Idrogeno", "H", 1, 1, [1])

    assert _blocco_mermaid_valido(diagramma_atomo(idrogeno))


def test_composti_e_blocco_mermaid_valido() -> None:
    """Il diagramma dei composti è un blocco Mermaid recintato valido."""
    fosforo = _fosforo()
    fosforo.composti_principali = [
        Composto(nome="Acido fosforico", formula="H3PO4", usi=["fertilizzanti"]),
    ]

    assert _blocco_mermaid_valido(diagramma_composti(fosforo))


def test_composti_collega_elemento_composto_uso() -> None:
    """Il diagramma collega l'elemento ai composti e questi ai loro impieghi."""
    fosforo = _fosforo()
    fosforo.composti_principali = [
        Composto(nome="Acido fosforico", formula="H3PO4", usi=["fertilizzanti", "bevande"]),
    ]

    risultato = diagramma_composti(fosforo)

    assert "Acido fosforico" in risultato
    assert "fertilizzanti" in risultato
    assert "bevande" in risultato
    assert "-->" in risultato


def test_composti_assenti_restituisce_stringa_vuota() -> None:
    """Senza composti noti non si genera un diagramma vuoto ma nessun diagramma."""
    assert diagramma_composti(_fosforo()) == ""


@pytest.mark.parametrize(
    "nome_pericoloso",
    ["Piombo (II) solfuro", 'Composto "citato"', "Ossido di ferro; nota"],
)
def test_composti_neutralizza_i_caratteri_speciali(nome_pericoloso: str) -> None:
    """I caratteri che romperebbero la sintassi Mermaid vengono neutralizzati."""
    fosforo = _fosforo()
    fosforo.composti_principali = [Composto(nome=nome_pericoloso, formula="X", usi=["uso"])]

    risultato = diagramma_composti(fosforo)

    corpo = risultato.split("```mermaid")[1].split("```")[0]
    assert '"' not in corpo.replace('["', "").replace('"]', "")
