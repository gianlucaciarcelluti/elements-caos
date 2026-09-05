"""Test dell'interfaccia a riga di comando."""

import shutil
from pathlib import Path

import pytest

from elements_caos.cli import main

DATI_PROVA = Path(__file__).parent / "dati_prova"


@pytest.fixture
def ambiente(tmp_path: Path) -> tuple[Path, Path]:
    """Prepara una copia dei dati di prova e una cartella di vault vuota."""
    dati = tmp_path / "data"
    shutil.copytree(DATI_PROVA, dati)
    (dati / "periodic_table_ridotto.json").unlink(missing_ok=True)
    vault = tmp_path / "vault"
    return dati, vault


def test_genera_crea_le_note_degli_elementi(ambiente: tuple[Path, Path]) -> None:
    """Il comando genera produce una nota per ciascun elemento."""
    dati, vault = ambiente

    codice = main(["genera", "--dati", str(dati), "--vault", str(vault)])

    assert codice == 0
    assert (vault / "Elementi" / "Fosforo.md").exists()


def test_genera_crea_le_note_di_navigazione(ambiente: tuple[Path, Path]) -> None:
    """Il comando genera produce anche le pagine di navigazione del vault."""
    dati, vault = ambiente

    main(["genera", "--dati", str(dati), "--vault", str(vault)])

    assert (vault / "Cronologia degli elementi.md").exists()
    assert (vault / "Tavola periodica.md").exists()
    assert (vault / "Attribuzioni.md").exists()
    assert (vault / "Epoche" / "Alchimia e primo moderno.md").exists()
    assert (vault / "Scopritori" / "Hennig Brand.md").exists()


def test_genera_e_idempotente(ambiente: tuple[Path, Path]) -> None:
    """Due generazioni consecutive producono file identici byte per byte.

    È la proprietà su cui si regge il controllo di CI contro le modifiche a mano.
    """
    dati, vault = ambiente

    main(["genera", "--dati", str(dati), "--vault", str(vault)])
    primo = (vault / "Elementi" / "Fosforo.md").read_bytes()

    main(["genera", "--dati", str(dati), "--vault", str(vault)])
    secondo = (vault / "Elementi" / "Fosforo.md").read_bytes()

    assert primo == secondo


def test_genera_rimuove_le_note_orfane(ambiente: tuple[Path, Path]) -> None:
    """Una nota rimasta da una generazione precedente viene rimossa.

    Senza questa pulizia, rinominare un elemento lascerebbe nel vault una nota
    fantasma che nessun dato genera più.
    """
    dati, vault = ambiente
    main(["genera", "--dati", str(dati), "--vault", str(vault)])

    orfana = vault / "Elementi" / "Elemento Inventato.md"
    orfana.write_text("residuo di una generazione precedente", encoding="utf-8")

    main(["genera", "--dati", str(dati), "--vault", str(vault)])

    assert not orfana.exists()


def test_valida_vault_integro_restituisce_zero(ambiente: tuple[Path, Path]) -> None:
    """La validazione di un vault appena generato non rileva problemi strutturali."""
    dati, vault = ambiente
    main(["genera", "--dati", str(dati), "--vault", str(vault)])

    codice = main(["valida", "--dati", str(dati), "--vault", str(vault), "--salta-budget"])

    assert codice == 0


def test_valida_rileva_wikilink_rotto(ambiente: tuple[Path, Path]) -> None:
    """La validazione segnala un collegamento interno rotto."""
    dati, vault = ambiente
    main(["genera", "--dati", str(dati), "--vault", str(vault)])
    (vault / "Elementi" / "Rotta.md").write_text("[[Non Esiste]]", encoding="utf-8")

    codice = main(["valida", "--dati", str(dati), "--vault", str(vault), "--salta-budget"])

    assert codice == 1


def test_dati_inesistenti_restituisce_due(tmp_path: Path) -> None:
    """Una cartella dati inesistente produce il codice di uscita dedicato."""
    codice = main(["genera", "--dati", str(tmp_path / "assente"), "--vault", str(tmp_path / "v")])

    assert codice == 2
