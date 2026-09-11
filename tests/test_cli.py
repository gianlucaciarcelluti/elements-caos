"""Test dell'interfaccia a riga di comando."""

import shutil
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import pytest
import yaml

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


def test_immagine_senza_licenza_non_viene_copiata(
    ambiente: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """Un'immagine priva del file di licenza affiancato non entra nel vault.

    Il presidio sulla licenza deve stare nel punto in cui il file entra nel
    vault, non solo nella validazione successiva: chi esegue genera a mano e
    pubblica senza validare non deve poter portare nel repository pubblico
    un'immagine di provenienza ignota.
    """
    dati, vault = ambiente
    (dati / "images" / "hennig-brand.jpg.license.yaml").unlink()

    main(["genera", "--dati", str(dati), "--vault", str(vault)])

    assert not (vault / "Immagini" / "hennig-brand.jpg").exists()
    assert "hennig-brand.jpg" in capsys.readouterr().out


def test_immagine_con_licenza_non_ammessa_non_viene_copiata(
    ambiente: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """Un'immagine con licenza fuori allowlist non entra nel vault."""
    dati, vault = ambiente
    (dati / "images" / "hennig-brand.jpg.license.yaml").write_text(
        "file: hennig-brand.jpg\nlicenza: CC BY-SA 4.0\nautore: Tizio\nfonte: https://x.it\n",
        encoding="utf-8",
    )

    main(["genera", "--dati", str(dati), "--vault", str(vault)])

    assert not (vault / "Immagini" / "hennig-brand.jpg").exists()
    assert "hennig-brand.jpg" in capsys.readouterr().out


def test_immagine_con_licenza_ammessa_viene_copiata(ambiente: tuple[Path, Path]) -> None:
    """Un'immagine di pubblico dominio, con licenza registrata, entra nel vault
    insieme al proprio file di licenza."""
    dati, vault = ambiente

    main(["genera", "--dati", str(dati), "--vault", str(vault)])

    assert (vault / "Immagini" / "hennig-brand.jpg").exists()
    assert (vault / "Immagini" / "hennig-brand.jpg.license.yaml").exists()


def test_sottocartella_in_immagini_non_viene_rimossa(ambiente: tuple[Path, Path]) -> None:
    """Una sottocartella creata a mano dentro Immagini/ non è un file orfano.

    Il generatore possiede solo i file che ha scritto lui al primo livello:
    una sottocartella (es. per organizzare varianti di un ritratto) non gli
    appartiene e la rigenerazione non deve né rimuoverla né fallire nel
    tentativo.
    """
    dati, vault = ambiente
    main(["genera", "--dati", str(dati), "--vault", str(vault)])

    sottocartella = vault / "Immagini" / "varianti"
    sottocartella.mkdir(parents=True)
    (sottocartella / "nota.txt").write_text("appunto personale", encoding="utf-8")

    codice = main(["genera", "--dati", str(dati), "--vault", str(vault)])

    assert codice == 0
    assert sottocartella.is_dir()
    assert (sottocartella / "nota.txt").exists()


def test_errore_di_scrittura_produce_messaggio_e_codice_dedicato(
    ambiente: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """Un errore di sistema durante la scrittura produce un messaggio in
    italiano e un codice di uscita dedicato, non un traceback.

    È un comando che l'utente esegue a mano: un traceback grezzo non gli dice
    dove intervenire, un messaggio in italiano sì.
    """
    dati, vault = ambiente
    vault.mkdir(parents=True)
    cartella_bloccata = vault / "Elementi"
    cartella_bloccata.mkdir()
    cartella_bloccata.chmod(0o444)

    try:
        codice = main(["genera", "--dati", str(dati), "--vault", str(vault)])
    finally:
        cartella_bloccata.chmod(0o755)

    assert codice == 3
    errore = capsys.readouterr().err
    assert "Elementi" in errore


def test_cronologia_include_le_tappe_dell_itinerario(ambiente: tuple[Path, Path]) -> None:
    """L'itinerario definito nei dati compare nella nota cronologica."""
    dati, vault = ambiente
    (dati / "itinerario.yaml").write_text(
        "- titolo: L'alchimista e la luce fredda\n"
        "  elemento: Fosforo\n"
        "  descrizione: La prima scoperta documentata.\n",
        encoding="utf-8",
    )

    main(["genera", "--dati", str(dati), "--vault", str(vault)])

    cronologia = (vault / "Cronologia degli elementi.md").read_text(encoding="utf-8")

    assert "Itinerario guidato" in cronologia
    assert "L'alchimista e la luce fredda" in cronologia
    assert "[[Fosforo]]" in cronologia


def test_cronologia_senza_itinerario_non_mostra_la_sezione(ambiente: tuple[Path, Path]) -> None:
    """L'itinerario è facoltativo: senza il file la cronologia si genera lo stesso.

    Il vault deve restare generabile da un dataset minimo, e chi forka il
    progetto per raccontare un'altra collezione di elementi non è tenuto a
    scrivere un percorso di lettura.
    """
    dati, vault = ambiente
    assert not (dati / "itinerario.yaml").exists()

    codice = main(["genera", "--dati", str(dati), "--vault", str(vault)])

    assert codice == 0
    cronologia = (vault / "Cronologia degli elementi.md").read_text(encoding="utf-8")
    assert "Itinerario guidato" not in cronologia


# --- Approfondimenti -------------------------------------------------------


def _modifica_fosforo(dati: Path, modifica: Callable[[dict[str, Any]], None]) -> None:
    """Applica una modifica al fosforo di prova passando dal parser YAML."""
    fosforo = dati / "elements" / "015-fosforo.yaml"
    documento = yaml.safe_load(fosforo.read_text(encoding="utf-8"))
    modifica(documento)
    fosforo.write_text(yaml.safe_dump(documento, allow_unicode=True), encoding="utf-8")


def _aggiungi_contenuti_estesi(dati: Path, parole_per_beat: int = 10, beat: int = 4) -> None:
    """Innesta nel fosforo di prova un blocco ``contenuti_estesi`` di lunghezza controllata."""
    testo = " ".join(["parola"] * parole_per_beat)

    def _innesta(documento: dict[str, Any]) -> None:
        documento["contenuti_estesi"] = {
            "hook": "Una storia più lunga.",
            "beats": [
                {"id": f"beat-{i}", "sezione": "contesto", "testo": testo} for i in range(beat)
            ],
        }

    _modifica_fosforo(dati, _innesta)


def _aggiungi_fonti(dati: Path, quante: int) -> None:
    """Aggiunge al fosforo di prova il numero richiesto di fonti fittizie."""

    def _innesta(documento: dict[str, Any]) -> None:
        documento["fonti"].extend(
            {
                "url": f"https://esempio.it/extra-{i}",
                "titolo": f"Fonte extra {i}",
                "consultata": date(2026, 9, 5),
            }
            for i in range(quante)
        )

    _modifica_fosforo(dati, _innesta)


def test_genera_non_crea_approfondimenti_senza_contenuti_estesi(
    ambiente: tuple[Path, Path],
) -> None:
    """``approfondimento: true`` da solo non produce alcuna nota estesa."""
    dati, vault = ambiente

    main(["genera", "--dati", str(dati), "--vault", str(vault)])

    assert not (vault / "Approfondimenti").exists()


def test_genera_crea_l_approfondimento_quando_scritto(ambiente: tuple[Path, Path]) -> None:
    """Con ``contenuti_estesi`` la nota estesa compare in ``Approfondimenti/`` e la
    nota base la linka; il vault resta integro (nessun wikilink rotto)."""
    dati, vault = ambiente
    _aggiungi_contenuti_estesi(dati)
    _aggiungi_fonti(dati, 2)

    codice = main(["genera", "--dati", str(dati), "--vault", str(vault)])

    assert codice == 0
    estesa = vault / "Approfondimenti" / "Fosforo — storia estesa.md"
    assert estesa.exists()
    assert "[[Fosforo — storia estesa]]" in (vault / "Elementi" / "Fosforo.md").read_text(
        encoding="utf-8"
    )
    assert main(["valida", "--dati", str(dati), "--vault", str(vault), "--salta-budget"]) == 0


def test_genera_rimuove_gli_approfondimenti_orfani(ambiente: tuple[Path, Path]) -> None:
    """Un approfondimento che i dati non generano più viene tolto dal vault."""
    dati, vault = ambiente
    _aggiungi_contenuti_estesi(dati)
    main(["genera", "--dati", str(dati), "--vault", str(vault)])

    orfana = vault / "Approfondimenti" / "Elemento Inventato — storia estesa.md"
    orfana.write_text("residuo", encoding="utf-8")

    main(["genera", "--dati", str(dati), "--vault", str(vault)])

    assert not orfana.exists()


def test_valida_applica_il_budget_esteso(
    ambiente: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """Un approfondimento troppo corto è un errore, con il nome della nota estesa."""
    dati, vault = ambiente
    _aggiungi_contenuti_estesi(dati)
    _aggiungi_fonti(dati, 2)
    main(["genera", "--dati", str(dati), "--vault", str(vault)])

    codice = main(["valida", "--dati", str(dati), "--vault", str(vault)])

    uscita = capsys.readouterr().out
    assert codice == 1
    assert "Fosforo — storia estesa: 40 parole, sotto il minimo di 7000" in uscita


def test_valida_richiede_quattro_fonti_all_approfondimento(
    ambiente: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """Con l'approfondimento scritto, le due fonti della nota base non bastano più."""
    dati, vault = ambiente
    _aggiungi_contenuti_estesi(dati)
    main(["genera", "--dati", str(dati), "--vault", str(vault)])

    codice = main(["valida", "--dati", str(dati), "--vault", str(vault), "--salta-budget"])

    uscita = capsys.readouterr().out
    assert codice == 1
    assert "Fosforo — storia estesa: 2 fonti, minimo richiesto 4" in uscita
