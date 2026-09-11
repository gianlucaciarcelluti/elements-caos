"""Test dei modelli dati e delle regole di validazione dello schema."""

from datetime import date

import pytest
from pydantic import ValidationError

from elements_caos.models import (
    Attendibilita,
    Beat,
    BeatEsteso,
    Categoria,
    Contenuti,
    ContenutiEstesi,
    Elemento,
    Fonte,
    Proprieta,
    Scoperta,
    Sezione,
    SezioneEstesa,
)


def _proprieta_valide() -> Proprieta:
    """Costruisce proprietà valide di riferimento (fosforo) per i test."""
    return Proprieta(
        gruppo=15,
        periodo=3,
        blocco="p",
        categoria=Categoria.NON_METALLO,
        massa_atomica=30.974,
        configurazione_elettronica="[Ne] 3s2 3p3",
        gusci=[2, 8, 5],
        punto_fusione_k=317.3,
        punto_ebollizione_k=553.7,
        densita=1.823,
        stati_ossidazione=[-3, 3, 5],
    )


def _scoperta_valida() -> Scoperta:
    """Costruisce una scoperta valida di riferimento (fosforo) per i test."""
    return Scoperta(
        anno=1669,
        anno_stimato=False,
        scopritori=["hennig-brand"],
        luogo="Amburgo",
        epoca="alchimia",
    )


def test_elemento_valido() -> None:
    """Un elemento con tutti i campi corretti deve essere accettato."""
    elemento = Elemento(
        numero_atomico=15,
        simbolo="P",
        nome="Fosforo",
        nome_en="Phosphorus",
        scoperta=_scoperta_valida(),
        proprieta=_proprieta_valide(),
        approfondimento=True,
        fonti=[
            Fonte(url="https://esempio.it/a", titolo="Fonte A", consultata=date(2026, 9, 5)),
            Fonte(url="https://esempio.it/b", titolo="Fonte B", consultata=date(2026, 9, 5)),
        ],
    )
    assert elemento.numero_atomico == 15
    assert elemento.nome == "Fosforo"


@pytest.mark.parametrize("numero", [0, -1, 119, 200])
def test_numero_atomico_fuori_intervallo_rifiutato(numero: int) -> None:
    """Il numero atomico deve stare nell'intervallo 1-118."""
    with pytest.raises(ValidationError):
        Elemento(
            numero_atomico=numero,
            simbolo="X",
            nome="Test",
            nome_en="Test",
            scoperta=_scoperta_valida(),
            proprieta=_proprieta_valide(),
            approfondimento=False,
            fonti=[],
        )


def test_anno_antico_richiede_flag_stimato() -> None:
    """Un anno anteriore al 1500 senza anno_stimato=True deve essere rifiutato."""
    with pytest.raises(ValidationError, match="anno_stimato"):
        Scoperta(
            anno=-9000,
            anno_stimato=False,
            scopritori=[],
            epoca="antichita",
        )


def test_anno_antico_con_flag_accettato() -> None:
    """Un anno anteriore al 1500 con anno_stimato=True deve essere accettato."""
    scoperta = Scoperta(
        anno=-9000,
        anno_stimato=True,
        scopritori=[],
        epoca="antichita",
    )
    assert scoperta.anno == -9000
    assert scoperta.anno_stimato is True


def test_blocco_non_valido_rifiutato() -> None:
    """Il blocco deve essere uno fra s, p, d, f."""
    with pytest.raises(ValidationError):
        Proprieta(
            gruppo=15,
            periodo=3,
            blocco="x",
            categoria=Categoria.NON_METALLO,
            massa_atomica=30.974,
            configurazione_elettronica="[Ne] 3s2 3p3",
            gusci=[2, 8, 5],
            stati_ossidazione=[],
        )


def test_punti_fusione_nulli_accettati() -> None:
    """I punti di fusione ed ebollizione possono essere nulli (dato non disponibile)."""
    proprieta = Proprieta(
        gruppo=None,
        periodo=7,
        blocco="d",
        categoria=Categoria.METALLO_DI_TRANSIZIONE,
        massa_atomica=267.0,
        configurazione_elettronica="[Rn] 5f14 6d3 7s2",
        gusci=[2, 8, 18, 32, 32, 11, 2],
        punto_fusione_k=None,
        punto_ebollizione_k=None,
        densita=None,
        stati_ossidazione=[5],
    )
    assert proprieta.punto_fusione_k is None


def test_lantanidi_senza_gruppo_accettati() -> None:
    """Lantanidi e attinidi non appartengono a un gruppo: gruppo=None è valido."""
    proprieta = Proprieta(
        gruppo=None,
        periodo=6,
        blocco="f",
        categoria=Categoria.LANTANIDE,
        massa_atomica=140.116,
        configurazione_elettronica="[Xe] 4f1 5d1 6s2",
        gusci=[2, 8, 18, 19, 9, 2],
        stati_ossidazione=[3, 4],
    )
    assert proprieta.gruppo is None


def test_beat_richiede_sezione_valida() -> None:
    """Un beat deve dichiarare una sezione fra quelle previste."""
    beat = Beat(
        id="contesto",
        sezione=Sezione.STORIA,
        testo="Ad Amburgo, nel 1669, Hennig Brand insegue la pietra filosofale.",
        visual="Ritratto di Brand",
        attendibilita=Attendibilita.DOCUMENTATO,
    )
    assert beat.sezione is Sezione.STORIA


def test_gusci_devono_sommare_al_numero_atomico() -> None:
    """La somma degli elettroni nei gusci deve dare il numero atomico dell'elemento."""
    with pytest.raises(ValidationError, match="gusci"):
        Elemento(
            numero_atomico=15,
            simbolo="P",
            nome="Fosforo",
            nome_en="Phosphorus",
            scoperta=_scoperta_valida(),
            proprieta=Proprieta(
                gruppo=15,
                periodo=3,
                blocco="p",
                categoria=Categoria.NON_METALLO,
                massa_atomica=30.974,
                configurazione_elettronica="[Ne] 3s2 3p3",
                gusci=[2, 8, 4],
                stati_ossidazione=[-3, 3, 5],
            ),
            approfondimento=False,
            fonti=[],
        )


def test_approfondimento_non_impone_contenuti_estesi_al_modello() -> None:
    """Il modello accetta approfondimento=True con contenuti_estesi ancora assente.

    Il vincolo di presenza vale in fase di rendering, non di validazione: gli
    approfondimenti si scrivono in un secondo momento, dopo le note base.
    """
    elemento = Elemento(
        numero_atomico=15,
        simbolo="P",
        nome="Fosforo",
        nome_en="Phosphorus",
        scoperta=_scoperta_valida(),
        proprieta=_proprieta_valide(),
        approfondimento=True,
        fonti=[],
    )
    assert elemento.approfondimento is True
    assert elemento.contenuti_estesi is None


def test_contenuti_concatenano_beat_per_sezione() -> None:
    """I contenuti espongono i beat filtrabili per sezione, nell'ordine dichiarato."""
    contenuti = Contenuti(
        hook="Un alchimista bollì l'urina cercando l'oro.",
        beats=[
            Beat(
                id="b1",
                sezione=Sezione.STORIA,
                testo="Primo.",
                attendibilita=Attendibilita.DOCUMENTATO,
            ),
            Beat(
                id="b2",
                sezione=Sezione.USI,
                testo="Secondo.",
                attendibilita=Attendibilita.DOCUMENTATO,
            ),
            Beat(
                id="b3",
                sezione=Sezione.STORIA,
                testo="Terzo.",
                attendibilita=Attendibilita.DOCUMENTATO,
            ),
        ],
    )
    storia = contenuti.beats_per_sezione(Sezione.STORIA)
    assert [b.id for b in storia] == ["b1", "b3"]


def test_id_beat_duplicati_rifiutati() -> None:
    """Due beat con lo stesso id nello stesso elemento devono essere rifiutati."""
    with pytest.raises(ValidationError, match="duplicat"):
        Contenuti(
            hook="Test.",
            beats=[
                Beat(
                    id="stesso",
                    sezione=Sezione.STORIA,
                    testo="Primo.",
                    attendibilita=Attendibilita.DOCUMENTATO,
                ),
                Beat(
                    id="stesso",
                    sezione=Sezione.USI,
                    testo="Secondo.",
                    attendibilita=Attendibilita.DOCUMENTATO,
                ),
            ],
        )


def test_contenuti_estesi_usano_sezioni_proprie() -> None:
    """L'approfondimento ha una struttura sua, non quella della nota base.

    Le sezioni della nota base (storia, usi, curiosità) non descrivono un
    testo di quarantacinque minuti: l'approfondimento si articola in contesto
    scientifico dell'epoca, vicenda umana, impatto, controversie ed eredità.
    """
    contenuti = ContenutiEstesi(
        hook="Un approfondimento.",
        beats=[
            BeatEsteso(id="c1", sezione=SezioneEstesa.CONTESTO, testo="Primo."),
            BeatEsteso(id="v1", sezione=SezioneEstesa.VICENDA, testo="Secondo."),
            BeatEsteso(id="c2", sezione=SezioneEstesa.CONTESTO, testo="Terzo."),
        ],
    )
    assert [b.id for b in contenuti.beats_per_sezione(SezioneEstesa.CONTESTO)] == ["c1", "c2"]
    assert [s.value for s in SezioneEstesa] == [
        "contesto",
        "vicenda",
        "impatto",
        "controversie",
        "eredita",
    ]


def test_beat_esteso_rifiuta_le_sezioni_della_nota_base() -> None:
    """Una sezione della nota base dentro l'approfondimento è un errore di dati."""
    with pytest.raises(ValidationError, match="sezione"):
        BeatEsteso(id="x", sezione="storia", testo="Fuori posto.")  # type: ignore[arg-type]


def test_id_beat_estesi_duplicati_rifiutati() -> None:
    """La regola degli id univoci vale anche per l'approfondimento."""
    with pytest.raises(ValidationError, match="duplicat"):
        ContenutiEstesi(
            hook="Test.",
            beats=[
                BeatEsteso(id="stesso", sezione=SezioneEstesa.CONTESTO, testo="Primo."),
                BeatEsteso(id="stesso", sezione=SezioneEstesa.VICENDA, testo="Secondo."),
            ],
        )


def test_contenuti_estesi_dell_elemento_sono_del_tipo_esteso() -> None:
    """``contenuti_estesi`` accetta solo la struttura dell'approfondimento."""
    with pytest.raises(ValidationError, match="sezione"):
        Elemento(
            numero_atomico=15,
            simbolo="P",
            nome="Fosforo",
            nome_en="Phosphorus",
            scoperta=_scoperta_valida(),
            proprieta=_proprieta_valide(),
            approfondimento=True,
            contenuti_estesi={  # type: ignore[arg-type]
                "hook": "x",
                "beats": [{"id": "b", "sezione": "storia", "testo": "y"}],
            },
            fonti=[],
        )
