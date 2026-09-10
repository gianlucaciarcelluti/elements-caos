"""Test dello script che verifica il sito nel browser.

Il controllo vero gira in CI con un browser headless e non da pytest: non si
vuole un browser fra le dipendenze dei test. Qui si verifica che lo script
esista, che copra le pagine giuste e — soprattutto — che non ripeta i due
errori di misura già commessi, perché sono errori che non si vedono: uno fa
sembrare rotto un sito sano, l'altro darebbe un falso allarme a ogni esecuzione.
"""

from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
SCRIPT = RADICE / "scripts" / "verifica_sito.mjs"
WORKFLOW = RADICE / ".github" / "workflows" / "validate.yml"


def _script() -> str:
    """Legge lo script di verifica."""
    return SCRIPT.read_text(encoding="utf-8")


def test_lo_script_esiste() -> None:
    """Senza, il Task 32 non ha prodotto nulla di eseguibile."""
    assert SCRIPT.is_file()


# --- I due errori di misura già commessi ------------------------------------


def test_la_larghezza_si_imposta_con_setviewport() -> None:
    """`--window-size` non produce un viewport da 390 px.

    Chrome headless su Linux ha una larghezza minima di finestra intorno ai
    500: chiedendone 390 si ottiene una pagina renderizzata a 500 e una foto
    ritagliata, che sembra un sito con il testo tagliato. È successo, e la
    diagnosi sbagliata che ne è seguita ha quasi fatto nascere un piano di
    refactoring per un difetto inesistente.
    """
    script = _script()

    assert "setViewport" in script
    # Il confronto cerca la stringa fra virgolette, cioè l'uso come argomento:
    # lo script NOMINA `--window-size` nel commento che spiega di non usarlo, e
    # quel commento è la cosa più utile del file.
    assert '"--window-size' not in script


def test_gli_elementi_dentro_un_contenitore_che_scorre_sono_esclusi() -> None:
    """Un antenato che scorre ritaglia i suoi discendenti.

    `getBoundingClientRect` riporta la posizione non ritagliata: senza questa
    esclusione la tavola periodica — che scorre in orizzontale di proposito —
    darebbe un falso allarme a ogni esecuzione, e il controllo diventerebbe
    rumore da ignorare.
    """
    script = _script()

    assert "overflowX" in script
    assert "scroll" in script


# --- La copertura ------------------------------------------------------------


def test_lo_script_copre_ogni_tipo_di_pagina() -> None:
    """Una pagina per template: verificarle tutte e 230 non aggiungerebbe nulla."""
    script = _script()

    for percorso in (
        "/index.html",
        "/cronologia-degli-elementi.html",
        "/tavola-periodica.html",
        "/itinerario.html",
        "/elementi/",
        "/scopritori/",
        "/epoche/",
        "/404.html",
    ):
        assert percorso in script, f"lo script non verifica {percorso}"


def test_lo_script_misura_entrambe_le_larghezze() -> None:
    """Telefono e scrivania: un difetto può stare in una sola delle due."""
    script = _script()

    assert "390" in script
    assert "1280" in script


def test_lo_script_controlla_le_cinque_cose_promesse() -> None:
    """Sfondamento, altezza, peso, console e punti di contatto."""
    script = _script()

    for indizio in (
        "larghezzaDocumento",
        "altezzaMax",
        "PESO_MASSIMO",
        "errori in console",
        "CONTATTO_MINIMO",
    ):
        assert indizio in script, f"manca il controllo: {indizio}"


def test_il_sito_si_serve_sotto_il_prefisso_di_produzione() -> None:
    """La 404 usa indirizzi assoluti con il prefisso del progetto.

    Servendo il sito dalla radice quei collegamenti risponderebbero 404 e il
    controllo segnalerebbe errori che in produzione non esistono.
    """
    assert "/elements-caos" in _script()


# --- Il job in CI ------------------------------------------------------------


def test_il_workflow_esegue_la_verifica() -> None:
    """Uno script che nessuno lancia non protegge nulla."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "verifica_sito.mjs" in workflow
    assert "elements-caos sito" in workflow


def test_la_versione_di_puppeteer_e_fissata() -> None:
    """Senza pin il controllo si romperebbe da solo a un aggiornamento a monte.

    È la stessa lezione del pin di Quartz: una dipendenza non fissata nel
    percorso di verifica produce rotture che non corrispondono a nessuna
    modifica del progetto.
    """
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "puppeteer@" in workflow


def test_le_eccezioni_non_catturate_vengono_rilevate() -> None:
    """Un'eccezione JS non passa da «console»: arriva su «pageerror».

    Verificato rompendo apposta una pagina: con il solo ascoltatore su console,
    uno script che si spacca a metà passava il controllo in silenzio.
    """
    assert "pageerror" in _script()
