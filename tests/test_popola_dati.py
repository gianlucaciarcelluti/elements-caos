"""Test dello script di popolamento: fusione fra dataset, cronologia e dati esistenti."""

import sys
from pathlib import Path

import yaml

from elements_caos.ingest.cronologia import VoceCronologia
from elements_caos.models import Categoria, Proprieta

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from popola_dati import _nome_file, costruisci_documento  # noqa: E402


def _proprieta_fosforo(
    *, punto_fusione_k: float | None = 317.3, punto_ebollizione_k: float | None = 553.7
) -> Proprieta:
    """Costruisce le proprietà del fosforo come le restituirebbe estrai_proprieta.

    ``stati_ossidazione`` è sempre lista vuota qui: è il valore reale che il
    dataset esterno restituisce, perché non fornisce questo dato. Fusione ed
    ebollizione sono parametrizzabili: nel dataset reale, alla data di
    verifica, il fosforo ha entrambi i valori a ``None`` (Ruling 37) — il
    default qui riproduce comunque un dataset con valori, e i singoli test
    passano ``None`` esplicitamente dove serve riprodurre quel caso.
    """
    return Proprieta(
        gruppo=15,
        periodo=3,
        blocco="p",
        categoria=Categoria.NON_METALLO,
        massa_atomica=30.974,
        configurazione_elettronica="[Ne] 3s2 3p3",
        gusci=[2, 8, 5],
        punto_fusione_k=punto_fusione_k,
        punto_ebollizione_k=punto_ebollizione_k,
        densita=1.823,
        stati_ossidazione=[],
    )


def _voce_cronologia_fosforo() -> VoceCronologia:
    return VoceCronologia(
        15, 1669, False, ["hennig-brand"], "alchimia", nome="Fosforo", isolamento_anno=1669
    )


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


def test_punto_fusione_esistente_sopravvive_se_il_dataset_riporta_null() -> None:
    """Ruling 37: un valore verificato non viene cancellato da una lacuna del dataset.

    Riproduce esattamente il caso reale del fosforo: il dataset esterno
    riporta ``melt: None`` (non "non esiste", ma "il dataset non lo sa"),
    mentre il file esistente ha già 317.3 K, un valore verificato e
    correttamente compilato in fase redazionale prima che esistesse
    l'ingest automatico. Il documento fuso deve preservare 317.3, non
    sovrascriverlo con null.
    """
    esistente = {"proprieta": {"punto_fusione_k": 317.3}}

    documento = costruisci_documento(
        15,
        _voce_dataset_fosforo(),
        _voce_cronologia_fosforo(),
        _proprieta_fosforo(punto_fusione_k=None),
        esistente,
    )

    assert documento["proprieta"]["punto_fusione_k"] == 317.3


def test_punto_ebollizione_esistente_sopravvive_se_il_dataset_riporta_null() -> None:
    """Stesso criterio della Ruling 37, applicato al punto di ebollizione."""
    esistente = {"proprieta": {"punto_ebollizione_k": 553.7}}

    documento = costruisci_documento(
        15,
        _voce_dataset_fosforo(),
        _voce_cronologia_fosforo(),
        _proprieta_fosforo(punto_ebollizione_k=None),
        esistente,
    )

    assert documento["proprieta"]["punto_ebollizione_k"] == 553.7


def test_densita_esistente_sopravvive_se_il_dataset_riporta_null() -> None:
    """Stesso criterio della Ruling 37, applicato alla densità."""
    proprieta_senza_densita = Proprieta(
        gruppo=15,
        periodo=3,
        blocco="p",
        categoria=Categoria.NON_METALLO,
        massa_atomica=30.974,
        configurazione_elettronica="[Ne] 3s2 3p3",
        gusci=[2, 8, 5],
        punto_fusione_k=317.3,
        punto_ebollizione_k=553.7,
        densita=None,
        stati_ossidazione=[],
    )
    esistente = {"proprieta": {"densita": 1.823}}

    documento = costruisci_documento(
        15,
        _voce_dataset_fosforo(),
        _voce_cronologia_fosforo(),
        proprieta_senza_densita,
        esistente,
    )

    assert documento["proprieta"]["densita"] == 1.823


def test_il_dataset_vince_quando_riporta_un_valore_diverso_da_quello_esistente() -> None:
    """Il verso opposto della Ruling 37 resta invariato: il dataset vince se ha un dato.

    Fondamentale quanto il caso di preservazione: la regola vale solo per
    riempire i buchi (dataset null), mai per far vincere sempre il valore
    già scritto nello YAML. Se il dataset porta un valore aggiornato, quel
    valore deve sostituire quello esistente, non l'inverso.
    """
    esistente = {
        "proprieta": {
            "punto_fusione_k": 999.0,
            "punto_ebollizione_k": 888.0,
            "densita": 777.0,
        }
    }

    documento = costruisci_documento(
        15,
        _voce_dataset_fosforo(),
        _voce_cronologia_fosforo(),
        _proprieta_fosforo(punto_fusione_k=317.3, punto_ebollizione_k=553.7),
        esistente,
    )

    assert documento["proprieta"]["punto_fusione_k"] == 317.3
    assert documento["proprieta"]["punto_ebollizione_k"] == 553.7
    assert documento["proprieta"]["densita"] == 1.823


def test_nome_italiano_viene_da_cronologia_non_dal_file_esistente() -> None:
    """Ruling 39: il nome italiano è un dato di CRONOLOGIA, non del file YAML.

    Anche quando il file esistente porta un nome diverso (residuo di un
    errore precedente, o semplicemente vuoto), il documento fuso deve usare
    ``voce_cronologia.nome``, mai un valore letto da ``esistente``.
    """
    documento = costruisci_documento(
        15,
        _voce_dataset_fosforo(),
        _voce_cronologia_fosforo(),
        _proprieta_fosforo(),
        esistente={"nome": "NomeSbagliato"},
    )

    assert documento["nome"] == "Fosforo"


def test_nome_italiano_sopravvive_quando_il_file_non_esiste() -> None:
    """Riproduce esattamente il difetto segnalato: file cancellato, poi rigenerato.

    Prima della Ruling 39 il nome italiano viveva solo nel file YAML che lo
    script stesso scriveva: se il file veniva cancellato, l'unico ripiego
    era il nome inglese del dataset (``esistente.get("nome",
    voce_dataset["name"])``), e il file rinasceva con un nome sbagliato.
    Con ``esistente={}`` (file assente, come dopo una cancellazione), il
    documento deve comunque avere il nome italiano corretto, letto da
    CRONOLOGIA.
    """
    documento = costruisci_documento(
        15,
        _voce_dataset_fosforo(),
        _voce_cronologia_fosforo(),
        _proprieta_fosforo(),
        esistente={},
    )

    assert documento["nome"] == "Fosforo"
    assert documento["nome"] != _voce_dataset_fosforo()["name"]


def test_nome_file_ricostruito_dal_nome_italiano_di_cronologia(tmp_path: Path) -> None:
    """Test end-to-end: cancella il file, riesegue la logica di popolamento, verifica.

    Riproduce lo scenario esatto segnalato dal controller (tennesso
    cancellato, rinato come "117-tennessine.yaml" con nome inglese) in
    forma controllata: scrive un file YAML preesistente con nome e
    contenuti corretti, lo cancella, poi applica la stessa logica di
    ``main()`` (individua il percorso via glob, costruisce il documento,
    scrive nel percorso ricostruito da ``_nome_file``) e verifica che il
    file rinasca con il nome italiano giusto nello YAML e nel nome del
    file — non con il nome inglese.
    """
    cartella = tmp_path / "elements"
    cartella.mkdir()
    percorso_originale = cartella / "015-fosforo.yaml"
    percorso_originale.write_text(
        yaml.safe_dump({"numero_atomico": 15, "nome": "Fosforo"}, allow_unicode=True),
        encoding="utf-8",
    )

    # Simula la cancellazione del file, come nello scenario segnalato.
    percorso_originale.unlink()

    # Stessa logica di main(): cerca un file esistente per quel numero
    # atomico (non lo trova, perché è stato cancellato), quindi costruisce
    # il documento e scrive nel percorso ricostruito dal nome di CRONOLOGIA.
    percorso_trovato = next(cartella.glob("015-*.yaml"), None)
    assert percorso_trovato is None, "il file deve risultare assente dopo la cancellazione"

    esistente: dict = {}
    documento = costruisci_documento(
        15,
        _voce_dataset_fosforo(),
        _voce_cronologia_fosforo(),
        _proprieta_fosforo(),
        esistente,
    )

    destinazione = percorso_trovato or cartella / _nome_file(15, documento["nome"])
    destinazione.write_text(yaml.safe_dump(documento, allow_unicode=True), encoding="utf-8")

    assert destinazione.name == "015-fosforo.yaml"
    rigenerato = yaml.safe_load(destinazione.read_text(encoding="utf-8"))
    assert rigenerato["nome"] == "Fosforo"
