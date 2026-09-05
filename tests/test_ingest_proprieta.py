"""Test dell'estrazione delle proprietà fisico-chimiche dal dataset esterno."""

from pathlib import Path

import pytest

from elements_caos.ingest.proprieta import (
    ErroreIngest,
    estrai_proprieta,
    leggi_dataset,
    mappa_categoria,
)
from elements_caos.models import Categoria

DATASET = Path(__file__).parent / "dati_prova" / "periodic_table_ridotto.json"


def _voce(numero: int) -> dict:
    """Recupera dal dataset di prova la voce con il numero atomico indicato."""
    return next(v for v in leggi_dataset(DATASET) if v["number"] == numero)


def test_leggi_dataset_esclude_elemento_119() -> None:
    """La voce 119 (Ununennium) è ipotetica e non deve entrare nel vault."""
    numeri = [voce["number"] for voce in leggi_dataset(DATASET)]

    assert 119 not in numeri
    assert numeri == [15, 58, 105]


def test_leggi_dataset_inesistente_solleva_errore() -> None:
    """Un dataset mancante produce un errore esplicito."""
    with pytest.raises(ErroreIngest, match="non trovato"):
        leggi_dataset(Path("/percorso/inesistente.json"))


@pytest.mark.parametrize(
    ("inglese", "attesa"),
    [
        ("alkali metal", Categoria.METALLO_ALCALINO),
        ("alkaline earth metal", Categoria.METALLO_ALCALINO_TERROSO),
        ("transition metal", Categoria.METALLO_DI_TRANSIZIONE),
        ("post-transition metal", Categoria.METALLO_POST_TRANSIZIONE),
        ("metalloid", Categoria.SEMIMETALLO),
        ("polyatomic nonmetal", Categoria.NON_METALLO),
        ("diatomic nonmetal", Categoria.NON_METALLO),
        ("noble gas", Categoria.GAS_NOBILE),
        ("lanthanide", Categoria.LANTANIDE),
        ("actinide", Categoria.ATTINIDE),
    ],
)
def test_mappa_categoria_note(inglese: str, attesa: Categoria) -> None:
    """Le categorie note del dataset sono tradotte nelle categorie italiane."""
    assert mappa_categoria(inglese) is attesa


@pytest.mark.parametrize(
    ("inglese", "attesa"),
    [
        ("unknown, probably transition metal", Categoria.METALLO_DI_TRANSIZIONE),
        ("unknown, probably post-transition metal", Categoria.METALLO_POST_TRANSIZIONE),
        ("unknown, probably metalloid", Categoria.SEMIMETALLO),
        ("unknown, predicted to be noble gas", Categoria.GAS_NOBILE),
        ("unknown, but predicted to be an alkali metal", Categoria.METALLO_ALCALINO),
    ],
)
def test_mappa_categoria_predette(inglese: str, attesa: Categoria) -> None:
    """Le categorie previste ma non confermate si riconducono alla categoria base.

    Il dataset usa formule come 'unknown, probably transition metal' per gli
    elementi sintetici le cui proprietà sono state predette ma non misurate.
    """
    assert mappa_categoria(inglese) is attesa


def test_mappa_categoria_sconosciuta_solleva_errore() -> None:
    """Una categoria non prevista deve fallire, non essere silenziosamente ignorata."""
    with pytest.raises(ErroreIngest, match="categoria non riconosciuta"):
        mappa_categoria("qualcosa di inatteso")


def test_estrai_proprieta_fosforo() -> None:
    """Le proprietà del fosforo vengono estratte correttamente dal dataset."""
    proprieta = estrai_proprieta(_voce(15))

    assert proprieta.gruppo == 15
    assert proprieta.periodo == 3
    assert proprieta.blocco == "p"
    assert proprieta.categoria is Categoria.NON_METALLO
    assert proprieta.gusci == [2, 8, 5]
    assert proprieta.punto_fusione_k is None
    assert proprieta.densita == 1.823


def test_estrai_proprieta_lantanide_senza_gruppo() -> None:
    """Un lantanide ha gruppo nullo nel dataset e resta tale nel modello."""
    proprieta = estrai_proprieta(_voce(58))

    assert proprieta.gruppo is None
    assert proprieta.categoria is Categoria.LANTANIDE
    assert proprieta.punto_fusione_k == 1068


def test_estrai_proprieta_transuranico_con_valori_nulli() -> None:
    """Un transuranico privo di dati misurati non deve far fallire l'estrazione."""
    proprieta = estrai_proprieta(_voce(105))

    assert proprieta.punto_fusione_k is None
    assert proprieta.punto_ebollizione_k is None
    assert proprieta.densita is None
    assert proprieta.categoria is Categoria.METALLO_DI_TRANSIZIONE


def test_estrai_proprieta_normalizza_la_configurazione() -> None:
    """La configurazione elettronica viene riportata senza alterazioni."""
    proprieta = estrai_proprieta(_voce(15))

    assert proprieta.configurazione_elettronica == "[Ne] 3s2 3p3"
