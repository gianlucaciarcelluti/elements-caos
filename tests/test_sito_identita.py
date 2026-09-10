"""Test dell'identità visiva del sito.

Il contrasto è calcolabile, quindi si verifica invece di sperarlo. Questi test
leggono i token dai fogli di stile e controllano che ogni coppia testo/sfondo
dichiarata sia leggibile in entrambi i temi: un colore d'epoca che non passa va
corretto, non giustificato.
"""

import re
from pathlib import Path

import pytest

CARTELLA_STATICI = (
    Path(__file__).resolve().parents[1] / "src" / "elements_caos" / "sito" / "statico"
)

# Le sei epoche del progetto, nell'ordine cronologico in cui si incontrano.
EPOCHE = (
    "antichita",
    "alchimia",
    "pneumatica",
    "elettrolisi",
    "spettroscopia",
    "nucleare",
)

# Rapporto minimo richiesto da WCAG 2.1 livello AA per il testo normale.
CONTRASTO_MINIMO = 4.5

_DICHIARAZIONE = re.compile(r"(--[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,8})\s*;")


def _canale(valore: float) -> float:
    """Linearizza un canale di colore secondo la formula di WCAG."""
    return valore / 12.92 if valore <= 0.03928 else ((valore + 0.055) / 1.055) ** 2.4


def luminanza(esadecimale: str) -> float:
    """Luminanza relativa di un colore esadecimale, secondo WCAG 2.1."""
    grezzo = esadecimale.lstrip("#")
    if len(grezzo) == 3:
        grezzo = "".join(carattere * 2 for carattere in grezzo)
    rosso, verde, blu = (int(grezzo[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * _canale(rosso) + 0.7152 * _canale(verde) + 0.0722 * _canale(blu)


def contrasto(primo: str, secondo: str) -> float:
    """Rapporto di contrasto fra due colori, da 1 (identici) a 21 (nero su bianco)."""
    chiaro, scuro = sorted((luminanza(primo), luminanza(secondo)), reverse=True)
    return (chiaro + 0.05) / (scuro + 0.05)


def _token(nome_file: str) -> dict[str, dict[str, str]]:
    """Estrae i token colore di un foglio di stile, raggruppati per tema.

    I temi sono delimitati da un commento ``/* tema: chiaro */``: è la
    convenzione che permette al test di sapere quale valore appartiene a quale
    tema senza interpretare la cascata CSS.
    """
    testo = (CARTELLA_STATICI / nome_file).read_text(encoding="utf-8")
    temi: dict[str, dict[str, str]] = {}
    tema_corrente = "chiaro"
    for riga in testo.splitlines():
        marcatore = re.search(r"/\*\s*tema:\s*(\w+)\s*\*/", riga)
        if marcatore:
            tema_corrente = marcatore.group(1)
            continue
        trovata = _DICHIARAZIONE.search(riga)
        if trovata:
            temi.setdefault(tema_corrente, {})[trovata.group(1)] = trovata.group(2)
    return temi


# --- Il calcolo del contrasto, verificato su valori noti ---------------------


def test_contrasto_di_riferimento() -> None:
    """Nero su bianco vale 21, un colore con sé stesso vale 1."""
    assert round(contrasto("#000000", "#ffffff"), 1) == 21.0
    assert round(contrasto("#777777", "#777777"), 1) == 1.0


# --- I token esistono in entrambi i temi ------------------------------------


def test_entrambi_i_temi_sono_definiti() -> None:
    """Chiaro e scuro sono entrambi dichiarati, non uno derivato dall'altro."""
    temi = _token("temi.css")

    assert "chiaro" in temi
    assert "scuro" in temi


def test_ogni_epoca_ha_il_suo_colore_in_entrambi_i_temi() -> None:
    """Il colore d'epoca lega scheda, cronologia e tavola: non può mancarne uno."""
    temi = _token("temi.css")

    for tema in ("chiaro", "scuro"):
        for epoca in EPOCHE:
            assert f"--epoca-{epoca}-sfondo" in temi[tema], f"{epoca} manca nel tema {tema}"
            assert f"--epoca-{epoca}-testo" in temi[tema], f"{epoca} manca nel tema {tema}"


# --- Il contrasto ------------------------------------------------------------


@pytest.mark.parametrize("tema", ["chiaro", "scuro"])
def test_contrasto_del_testo_sui_fondi(tema: str) -> None:
    """Testo normale e testo tenue devono essere leggibili su fondo e superficie."""
    token = _token("temi.css")[tema]

    coppie = (
        ("--colore-testo", "--colore-fondo"),
        ("--colore-testo", "--colore-superficie"),
        ("--colore-testo-tenue", "--colore-fondo"),
        ("--colore-testo-tenue", "--colore-superficie"),
        ("--colore-accento", "--colore-fondo"),
    )
    for davanti, dietro in coppie:
        rapporto = contrasto(token[davanti], token[dietro])
        assert rapporto >= CONTRASTO_MINIMO, (
            f"tema {tema}: {davanti} su {dietro} è {rapporto:.2f}:1, "
            f"sotto il minimo di {CONTRASTO_MINIMO}"
        )


@pytest.mark.parametrize("tema", ["chiaro", "scuro"])
def test_contrasto_dei_colori_d_epoca(tema: str) -> None:
    """Ogni epoca deve essere leggibile: sei colori, due temi, nessuna eccezione."""
    token = _token("temi.css")[tema]

    for epoca in EPOCHE:
        rapporto = contrasto(token[f"--epoca-{epoca}-testo"], token[f"--epoca-{epoca}-sfondo"])
        assert rapporto >= CONTRASTO_MINIMO, (
            f"tema {tema}: l'epoca {epoca} è {rapporto:.2f}:1, "
            f"sotto il minimo di {CONTRASTO_MINIMO}"
        )


def test_i_colori_d_epoca_sono_distinguibili_fra_loro() -> None:
    """Sei epoche che si somigliano non comunicano nulla.

    Non è un requisito di accessibilità ma di leggibilità dell'informazione: se
    due epoche adiacenti hanno lo stesso colore, la codifica cromatica della
    cronologia e della tavola periodica smette di dire qualcosa.
    """
    token = _token("temi.css")["chiaro"]
    sfondi = [token[f"--epoca-{epoca}-sfondo"] for epoca in EPOCHE]

    assert len(set(sfondi)) == len(EPOCHE), "due epoche condividono lo stesso colore"


# --- Tipografia --------------------------------------------------------------


def test_nessuna_dipendenza_da_font_esterni() -> None:
    """Font di sistema: nessuna chiamata a un CDN nel percorso di rendering.

    Una dipendenza esterna è un punto di rottura e, su un sito che dichiara di
    non raccogliere nulla su chi legge, anche un tracciamento di terze parti.
    """
    for foglio in CARTELLA_STATICI.glob("*.css"):
        testo = foglio.read_text(encoding="utf-8")
        assert "@import" not in testo, f"{foglio.name} importa un foglio esterno"
        assert "fonts.googleapis" not in testo
        assert "http://" not in testo and "https://" not in testo


def test_larghezza_di_lettura_limitata() -> None:
    """La riga non supera i 70 caratteri: è un vincolo di lettura lunga."""
    testo = (CARTELLA_STATICI / "base.css").read_text(encoding="utf-8")

    trovata = re.search(r"--larghezza-lettura\s*:\s*(\d+)ch", testo)
    assert trovata, "manca il token --larghezza-lettura"
    assert int(trovata.group(1)) <= 70


# --- I fogli arrivano davvero nel sito --------------------------------------


def test_gli_statici_vengono_copiati_e_collegati(tmp_path: Path) -> None:
    """Un foglio di stile che non raggiunge l'uscita non serve a nulla."""
    from elements_caos.cli import main

    dati = Path(__file__).parent / "dati_prova"
    uscita = tmp_path / "pubblico"
    main(["sito", "--dati", str(dati), "--uscita", str(uscita)])

    assert (uscita / "statico" / "base.css").is_file()
    assert (uscita / "statico" / "temi.css").is_file()

    pagina = (uscita / "elementi" / "fosforo.html").read_text(encoding="utf-8")
    assert "../statico/temi.css" in pagina
    assert "../statico/base.css" in pagina


def test_il_tema_si_puo_scegliere(tmp_path: Path) -> None:
    """La scelta esplicita del tema deve esistere, altrimenti data-tema è codice morto."""
    from elements_caos.cli import main

    dati = Path(__file__).parent / "dati_prova"
    uscita = tmp_path / "pubblico"
    main(["sito", "--dati", str(dati), "--uscita", str(uscita)])

    pagina = (uscita / "elementi" / "fosforo.html").read_text(encoding="utf-8")
    assert 'id="scelta-tema"' in pagina
    assert (uscita / "statico" / "tema.js").is_file()
