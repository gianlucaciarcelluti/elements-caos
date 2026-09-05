"""Test dell'estrazione delle proprietà fisico-chimiche dal dataset esterno."""

from pathlib import Path

import pytest

from elements_caos.ingest.proprieta import (
    ErroreIngest,
    estrai_proprieta,
    leggi_dataset,
    mappa_categoria,
    scarica_dataset,
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
    assert numeri == [15, 58, 9, 1, 105]


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


def test_estrai_proprieta_corregge_gruppo_17_ad_alogeno() -> None:
    """Un elemento del gruppo 17 è sempre un alogeno, indipendentemente dal dataset.

    Il dataset classifica gli alogeni come 'diatomic nonmetal' per i comuni (F, Cl, Br, I)
    e 'metalloid' per i sintetici (At, Ts). La correzione basata sul gruppo garantisce
    che tutti ricevano la categoria ALOGENO, che è la classificazione IUPAC corretta.
    """
    proprieta = estrai_proprieta(_voce(9))  # Fluorine, gruppo 17

    # Il dataset direbbe "diatomic nonmetal" → NON_METALLO
    # Ma la correzione per gruppo 17 deve produrre ALOGENO
    assert proprieta.categoria is Categoria.ALOGENO
    assert proprieta.gruppo == 17


def test_estrai_proprieta_idrogeno_non_alcalino() -> None:
    """L'idrogeno nel gruppo 1 non è un metallo alcalino.

    Anche se nel gruppo 1 (come i metalli alcalini), l'idrogeno è un non-metallo
    e resta tale dopo l'estrazione, senza essere "corretto" a metallo alcalino.
    Questa è una verifica che la correzione per gruppo 1 non viene mai applicata.
    """
    proprieta = estrai_proprieta(_voce(1))  # Hydrogen, gruppo 1

    assert proprieta.gruppo == 1
    assert proprieta.categoria is Categoria.NON_METALLO  # Non METALLO_ALCALINO


def test_leggi_dataset_contiene_alogeno_e_idrogeno() -> None:
    """Il dataset di prova contiene ora elementi per testare il gruppo 17 e 1."""
    numeri = [voce["number"] for voce in leggi_dataset(DATASET)]

    # Dopo il filtro deve contenere 1 (H), 9 (F), 15 (P), 58 (Ce), 105 (Db)
    assert 1 in numeri  # Hydrogen
    assert 9 in numeri  # Fluorine
    assert 119 not in numeri  # Ununennium escluso
    assert len(numeri) == 5


@pytest.mark.integration
def test_tutte_le_categorie_sono_assegnate_nei_118_elementi_reali(tmp_path: Path) -> None:
    """Verifica che nessuna categoria italiana resti orfana sul dataset reale.

    Questo test scarica il dataset vero da GitHub e verifica che tutte e 10 le
    categorie italiane siano assegnate ad almeno un elemento dei 118. È un test
    di integrazione che intercetta regressioni come il bug degli alogeni (orfani).

    **Esecuzione:** Per default, `pytest` **non esegue** questo test perché richiede
    la rete. Eseguirlo esplicitamente con:

        uv run pytest -m integration tests/test_ingest_proprieta.py -v

    Se il test fallisce per errore di rete (dataset non disponibile), è un problema
    esterno, non un bug del codice. La CI lo esclude di default.
    """
    # Scarica il dataset reale in una directory temporanea isolata
    dataset_reale = tmp_path / "periodic_table_reale.json"
    scarica_dataset(dataset_reale)

    voci = leggi_dataset(dataset_reale)
    assert len(voci) == 118, f"Attesi 118 elementi, trovati {len(voci)}"

    # Conta gli elementi per categoria
    categorie_assegnate = {cat: 0 for cat in Categoria}
    for voce in voci:
        proprieta = estrai_proprieta(voce)
        categorie_assegnate[proprieta.categoria] += 1

    # Verifica che tutte le 10 categorie siano assegnate (nessuna orfana)
    orfane = [cat for cat, count in categorie_assegnate.items() if count == 0]
    assert not orfane, f"Categorie orfane (senza elementi): {[c.name for c in orfane]}"

    # Verifica che i conteggi siano plausibili: ALOGENO deve avere almeno i comuni
    assert categorie_assegnate[Categoria.ALOGENO] >= 4, "Alogeni: attesi almeno 4 elementi comuni"
