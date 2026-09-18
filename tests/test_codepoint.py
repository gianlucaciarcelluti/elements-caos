"""Controlla che nessuna parola mescoli alfabeto latino e non latino.

Nel sodio (2026-09-17) dei caratteri cirillici si erano infiltrati dentro una
parola italiana: «usciva» scritto «usc-и-в-а». A vedersi sono identici alle
lettere latine corrispondenti, quindi superano qualunque rilettura, e non li
trova nessun `grep` scritto in alfabeto latino. L'unico modo per accorgersene è
guardare i codepoint.

Il controllo NON vieta il greco o il cirillico in sé: le etimologie sono
contenuto legittimo e frequente in questo vault (λίθος per il litio, ζωτικός
per l'azoto, δυσπρόσιτος per il disprosio, ἥλιος e ἀργόν in greco politonico),
così come i simboli della fisica (π, θ, ρ, μ) e i simboli IPA delle
pronunce (ˈsmɪθsən per Smithson). Vieta la *mescolanza dentro la stessa
parola*, che è la firma dell'errore e non ha mai un uso legittimo.

Costa millisecondi e l'errore si crea mentre si scrive, quindi sta nei test e
non negli script lenti di verifica.
"""

import re
import unicodedata
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parents[1]
DATI = RADICE / "data"

# Alfabeti che contengono lettere visivamente identiche a quelle latine.
# Il greco comprende anche l'Extended (politonico): ἥλιος, ἀργόν, ἀζωτικός
# mescolano le due zone, e senza l'Extended una parola greca intera
# risulterebbe "mista" e darebbe un falso positivo.
INTERVALLI_NON_LATINI = (
    (0x0370, 0x03FF, "greco"),
    (0x1F00, 0x1FFF, "greco"),
    (0x0400, 0x04FF, "cirillico"),
)

# Estensioni IPA: le pronunce (ˈsmɪθsən) usano legittimamente θ insieme a
# lettere latine, quindi una parola che contiene simboli IPA non è un errore.
INTERVALLI_IPA = ((0x0250, 0x02AF, "ipa"), (0x02B0, 0x02FF, "modificatori"))

# Una "parola" ai fini del controllo: lettere, eventualmente unite da apostrofi
# o trattini interni, che è l'unità in cui l'errore si nasconde.
PAROLA = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE)


def _alfabeto(carattere: str) -> str:
    """Classifica il carattere come 'latino' o come alfabeto non latino noto."""
    codice = ord(carattere)
    for inizio, fine, nome in INTERVALLI_NON_LATINI:
        if inizio <= codice <= fine:
            return nome
    return "latino"


def _e_trascrizione_ipa(parola: str) -> bool:
    """Vero se la parola contiene simboli IPA, cioè è una pronuncia."""
    return any(inizio <= ord(c) <= fine for c in parola for inizio, fine, _ in INTERVALLI_IPA)


def trova_parole_miste(testo: str) -> list[tuple[str, set[str]]]:
    """Elenca le parole che mescolano latino e alfabeti non latini."""
    miste = []
    for parola in PAROLA.findall(testo):
        if _e_trascrizione_ipa(parola):
            continue
        alfabeti = {_alfabeto(c) for c in parola if c.isalpha()}
        if "latino" in alfabeti and len(alfabeti) > 1:
            miste.append((parola, alfabeti - {"latino"}))
    return miste


def test_riconosce_la_parola_del_sodio() -> None:
    """«uscива», con tre lettere cirilliche dentro una parola italiana, è mista."""
    miste = trova_parole_miste("Il sale uscива dalle saline.")

    assert miste == [("uscива", {"cirillico"})]


def test_riconosce_una_sola_lettera_greca_infiltrata() -> None:
    """Basta una «ο» greca dentro una parola latina perché scatti il controllo."""
    miste = trova_parole_miste("il sοdio e i suoi composti")

    assert miste == [("sοdio", {"greco"})]


def test_accetta_le_etimologie_greche_intere() -> None:
    """Una parola greca per intero è contenuto legittimo, non un errore."""
    testo = "dal greco λίθος, pietra, e da ζωτικός, che dà la vita"

    assert trova_parole_miste(testo) == []


def test_accetta_i_simboli_della_fisica() -> None:
    """I simboli greci isolati non sono parole miste."""
    testo = "la particella α, il legame π e l'angolo θ della struttura"

    assert trova_parole_miste(testo) == []


def test_accetta_il_greco_politonico() -> None:
    """Le parole in greco politonico stanno a cavallo di due blocchi Unicode.

    «ἥλιος» ha lo spirito aspro nel blocco Greek Extended e le altre lettere nel
    blocco greco di base: vanno riconosciute come un unico alfabeto, altrimenti
    ogni etimologia del vault risulta «mista».
    """
    testo = "dal greco ἥλιος, il Sole, e da ἀργόν, inerte"

    assert trova_parole_miste(testo) == []


def test_accetta_le_trascrizioni_ipa() -> None:
    """La pronuncia di Smithson usa θ come simbolo IPA, non come lettera greca."""
    testo = "Smithson Tennant, pronunciato ˈsmɪθsən"

    assert trova_parole_miste(testo) == []


def test_accetta_la_prosa_italiana() -> None:
    """Accenti, apostrofi e trattini italiani non producono falsi positivi."""
    testo = "Perché l'elemento è «raro» — così si racconta, nell'Ottocento."

    assert trova_parole_miste(testo) == []


@pytest.mark.parametrize(
    "percorso",
    sorted(DATI.rglob("*.yaml")),
    ids=lambda p: p.name,
)
def test_i_dati_non_contengono_parole_miste(percorso: Path) -> None:
    """Nessun file di dati mescola alfabeti dentro una stessa parola."""
    testo = percorso.read_text(encoding="utf-8")

    miste = trova_parole_miste(testo)

    if miste:
        dettaglio = "; ".join(
            f"{parola!r} ({', '.join(sorted(alfabeti))}: "
            + ", ".join(
                f"U+{ord(c):04X} {unicodedata.name(c, 'senza nome')}"
                for c in parola
                if _alfabeto(c) != "latino"
            )
            + ")"
            for parola, alfabeti in miste
        )
        pytest.fail(f"{percorso.name}: parole ad alfabeto misto — {dettaglio}")
