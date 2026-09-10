"""L'avvertenza sull'uso dell'IA deve comparire su ogni pagina generata.

È una dichiarazione verso chi legge, non una nota di stile: se sparisse da una
pagina nessun altro controllo se ne accorgerebbe, quindi il presidio sta qui.
"""

from pathlib import Path

import pytest

from elements_caos.render.avvertenza import AVVERTENZA_IA

CARTELLA_VAULT = Path(__file__).resolve().parents[1] / "vault"


def test_avvertenza_nomina_ia_e_imprecisioni() -> None:
    """Il testo deve dire entrambe le cose: che è stata usata l'IA e che può sbagliare."""
    testo = AVVERTENZA_IA.lower()
    assert "intelligenza artificiale" in testo
    assert "errori" in testo and "imprecisioni" in testo


@pytest.mark.skipif(not CARTELLA_VAULT.exists(), reason="vault non generato")
def test_ogni_nota_del_vault_porta_l_avvertenza() -> None:
    """Nessuna pagina del vault può essere priva dell'avvertenza."""
    corpo = "intelligenza artificiale"
    mancanti = [
        percorso.relative_to(CARTELLA_VAULT).as_posix()
        for percorso in sorted(CARTELLA_VAULT.rglob("*.md"))
        if corpo not in percorso.read_text(encoding="utf-8")
    ]
    assert mancanti == [], f"pagine senza avvertenza: {mancanti}"
