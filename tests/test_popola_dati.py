"""Test dello script di popolamento: fusione fra dataset, cronologia e dati esistenti."""

import sys
from pathlib import Path

from elements_caos.ingest.cronologia import VoceCronologia
from elements_caos.models import Categoria, Proprieta

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from popola_dati import costruisci_documento  # noqa: E402


def _proprieta_fosforo() -> Proprieta:
    """Costruisce le proprietà del fosforo come le restituirebbe estrai_proprieta.

    ``stati_ossidazione`` è sempre lista vuota qui: è il valore reale che il
    dataset esterno restituisce, perché non fornisce questo dato.
    """
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
        stati_ossidazione=[],
    )


def _voce_cronologia_fosforo() -> VoceCronologia:
    return VoceCronologia(15, 1669, False, ["hennig-brand"], "alchimia", isolamento_anno=1669)


def _voce_dataset_fosforo() -> dict:
    return {"symbol": "P", "name": "Phosphorus", "number": 15}


def test_stati_ossidazione_gia_compilati_sopravvivono_al_ripopolamento() -> None:
    """Gli stati di ossidazione redazionali non devono essere azzerati da un rilancio.

    Riproduce esattamente il difetto segnalato: un file esistente ha già
    ``proprieta.stati_ossidazione`` compilato a mano (dato redazionale, Ruling
    23/36), ma ``estrai_proprieta`` restituisce sempre lista vuota per quel
    campo perché il dataset esterno non lo fornisce. Il documento fuso deve
    preservare il valore esistente, non quello (vuoto) del dataset.
    """
    esistente = {
        "nome": "Fosforo",
        "proprieta": {"stati_ossidazione": [-3, -2, -1, 1, 3, 4, 5]},
    }

    documento = costruisci_documento(
        15,
        _voce_dataset_fosforo(),
        _voce_cronologia_fosforo(),
        _proprieta_fosforo(),
        esistente,
    )

    assert documento["proprieta"]["stati_ossidazione"] == [-3, -2, -1, 1, 3, 4, 5]


def test_stati_ossidazione_assenti_restano_lista_vuota() -> None:
    """Un elemento senza stati di ossidazione compilati resta a lista vuota.

    Non deve comparire alcun valore inventato: la lista vuota è il segnale
    corretto — e distinguibile solo dal fatto che non c'è nulla da
    preservare — che il dato redazionale non è ancora stato scritto.
    """
    documento = costruisci_documento(
        15,
        _voce_dataset_fosforo(),
        _voce_cronologia_fosforo(),
        _proprieta_fosforo(),
        esistente={},
    )

    assert documento["proprieta"]["stati_ossidazione"] == []


def test_altri_campi_di_proprieta_vengono_comunque_aggiornati_dal_dataset() -> None:
    """Solo stati_ossidazione è preservato: il resto di proprieta resta automatico.

    Se il dataset cambiasse la massa atomica (aggiornamento a monte), il
    documento fuso deve riflettere il nuovo valore, non quello del file
    esistente: la preservazione è mirata al solo campo redazionale.
    """
    esistente = {
        "proprieta": {
            "stati_ossidazione": [-3, -2, -1, 1, 3, 4, 5],
            "massa_atomica": 999.0,
        }
    }

    documento = costruisci_documento(
        15,
        _voce_dataset_fosforo(),
        _voce_cronologia_fosforo(),
        _proprieta_fosforo(),
        esistente,
    )

    assert documento["proprieta"]["massa_atomica"] == 30.974
