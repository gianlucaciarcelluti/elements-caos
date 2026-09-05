"""Test dei controlli di integrità del vault."""

from pathlib import Path

from elements_caos.models import Categoria, Elemento, Fonte, Proprieta, Scoperta
from elements_caos.validazione import (
    Gravita,
    verifica_budget_parole,
    verifica_catena_cronologica,
    verifica_dati_redazionali,
    verifica_licenze_immagini,
    verifica_wikilink,
)


def _elemento_di_prova(stati_ossidazione: list[int]) -> Elemento:
    """Costruisce un elemento minimo (fosforo) per testare i dati redazionali."""
    return Elemento(
        numero_atomico=15,
        simbolo="P",
        nome="Fosforo",
        nome_en="Phosphorus",
        scoperta=Scoperta(
            anno=1669,
            anno_stimato=False,
            scopritori=["hennig-brand"],
            epoca="alchimia",
        ),
        proprieta=Proprieta(
            gruppo=15,
            periodo=3,
            blocco="p",
            categoria=Categoria.NON_METALLO,
            massa_atomica=30.974,
            configurazione_elettronica="[Ne] 3s2 3p3",
            gusci=[2, 8, 5],
            stati_ossidazione=stati_ossidazione,
        ),
        fonti=[
            Fonte(url="https://esempio.it/a", titolo="Fonte A", consultata="2026-09-05"),
        ],
    )


def test_budget_rispettato_non_produce_problemi() -> None:
    """Un testo dentro il budget previsto non genera segnalazioni."""
    testo = " ".join(["parola"] * 1000)

    assert verifica_budget_parole("Fosforo", testo, 800, 1300) == []


def test_budget_troppo_corto_produce_errore() -> None:
    """Un testo sotto il minimo genera un errore che cita il conteggio."""
    testo = " ".join(["parola"] * 500)

    problemi = verifica_budget_parole("Fosforo", testo, 800, 1300)

    assert len(problemi) == 1
    assert problemi[0].gravita is Gravita.ERRORE
    assert "500" in problemi[0].messaggio
    assert "Fosforo" in problemi[0].contesto


def test_budget_troppo_lungo_produce_errore() -> None:
    """Un testo sopra il massimo genera un errore."""
    testo = " ".join(["parola"] * 2000)

    problemi = verifica_budget_parole("Fosforo", testo, 800, 1300)

    assert len(problemi) == 1
    assert problemi[0].gravita is Gravita.ERRORE


def test_wikilink_valido_non_produce_problemi(tmp_path: Path) -> None:
    """Un wikilink che punta a una nota esistente non genera segnalazioni."""
    (tmp_path / "Fosforo.md").write_text("Vedi [[Zolfo]].", encoding="utf-8")
    (tmp_path / "Zolfo.md").write_text("Nota dello zolfo.", encoding="utf-8")

    assert verifica_wikilink(tmp_path) == []


def test_wikilink_rotto_produce_errore(tmp_path: Path) -> None:
    """Un wikilink verso una nota inesistente genera un errore."""
    (tmp_path / "Fosforo.md").write_text("Vedi [[Inesistente]].", encoding="utf-8")

    problemi = verifica_wikilink(tmp_path)

    assert len(problemi) == 1
    assert "Inesistente" in problemi[0].messaggio


def test_wikilink_con_alias_viene_risolto(tmp_path: Path) -> None:
    """Un wikilink con alias punta al nome prima della barra verticale."""
    (tmp_path / "Tavola.md").write_text("[[Fosforo|P]]", encoding="utf-8")
    (tmp_path / "Fosforo.md").write_text("Nota.", encoding="utf-8")

    assert verifica_wikilink(tmp_path) == []


def test_wikilink_a_immagine_viene_risolto(tmp_path: Path) -> None:
    """Un incorporamento di immagine punta a un file esistente nel vault."""
    (tmp_path / "Brand.md").write_text("![[brand.jpg]]", encoding="utf-8")
    (tmp_path / "brand.jpg").write_bytes(b"x")

    assert verifica_wikilink(tmp_path) == []


def test_wikilink_con_ancora_viene_risolto(tmp_path: Path) -> None:
    """Un wikilink con àncora di sezione punta al nome prima del cancelletto."""
    (tmp_path / "Tavola.md").write_text("[[Fosforo#Storia]]", encoding="utf-8")
    (tmp_path / "Fosforo.md").write_text("Nota.", encoding="utf-8")

    assert verifica_wikilink(tmp_path) == []


def test_wikilink_con_pipe_escaped_in_tabella_viene_risolto(tmp_path: Path) -> None:
    """In una tabella Markdown il pipe dell'alias è preceduto da un backslash."""
    (tmp_path / "Tavola.md").write_text(
        "| Simbolo | Elemento |\n| --- | --- |\n| P | [[Fosforo\\|P]] |\n",
        encoding="utf-8",
    )
    (tmp_path / "Fosforo.md").write_text("Nota.", encoding="utf-8")

    assert verifica_wikilink(tmp_path) == []


def test_catena_cronologica_completa_non_produce_problemi() -> None:
    """Posizioni cronologiche consecutive e senza duplicati non generano problemi."""
    assert verifica_catena_cronologica([1, 2, 3, 4]) == []


def test_catena_cronologica_con_buco_produce_errore() -> None:
    """Un salto nella numerazione cronologica genera un errore."""
    problemi = verifica_catena_cronologica([1, 2, 4])

    assert len(problemi) == 1
    assert "3" in problemi[0].messaggio


def test_catena_cronologica_con_duplicato_produce_errore() -> None:
    """Una posizione cronologica ripetuta genera un errore."""
    problemi = verifica_catena_cronologica([1, 2, 2, 3])

    assert any("duplicat" in p.messaggio.lower() for p in problemi)


def test_immagine_senza_file_licenza_produce_errore(tmp_path: Path) -> None:
    """Un'immagine priva del file di licenza affiancato genera un errore."""
    (tmp_path / "brand.jpg").write_bytes(b"x")

    problemi = verifica_licenze_immagini(tmp_path)

    assert len(problemi) == 1
    assert "licenza" in problemi[0].messaggio.lower()


def test_immagine_con_licenza_non_ammessa_produce_errore(tmp_path: Path) -> None:
    """Un'immagine con licenza fuori allowlist genera un errore."""
    (tmp_path / "brand.jpg").write_bytes(b"x")
    (tmp_path / "brand.jpg.license.yaml").write_text(
        "file: brand.jpg\nlicenza: CC BY-SA 4.0\nautore: Tizio\nfonte: https://x.it\n",
        encoding="utf-8",
    )

    problemi = verifica_licenze_immagini(tmp_path)

    assert len(problemi) == 1
    assert "CC BY-SA 4.0" in problemi[0].messaggio


def test_immagine_con_licenza_ammessa_non_produce_problemi(tmp_path: Path) -> None:
    """Un'immagine di pubblico dominio con licenza registrata è accettata."""
    (tmp_path / "brand.jpg").write_bytes(b"x")
    (tmp_path / "brand.jpg.license.yaml").write_text(
        "file: brand.jpg\nlicenza: PD-old-100-expired\nautore: Wright\n"
        "fonte: https://commons.wikimedia.org/x\n",
        encoding="utf-8",
    )

    assert verifica_licenze_immagini(tmp_path) == []


def test_elemento_senza_stati_ossidazione_produce_errore() -> None:
    """Un elemento privo di stati di ossidazione genera un errore redazionale."""
    elemento = _elemento_di_prova(stati_ossidazione=[])

    problemi = verifica_dati_redazionali(elemento)

    assert len(problemi) == 1
    assert problemi[0].gravita is Gravita.ERRORE
    assert "ossidazione" in problemi[0].messaggio.lower()


def test_elemento_con_stati_ossidazione_non_produce_problemi() -> None:
    """Un elemento con stati di ossidazione compilati non genera problemi."""
    elemento = _elemento_di_prova(stati_ossidazione=[3, 5])

    assert verifica_dati_redazionali(elemento) == []
