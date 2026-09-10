"""Test del controllo sui link delle fonti.

Le regole di classificazione sono la sostanza del controllo: un 403 non è un
link morto, un 404 sì, e un host che non risolve va distinto da un server
temporaneamente giù. Sbagliarle produce o falsi allarmi settimanali o silenzio
su fonti sparite, e in entrambi i casi il presidio smette di servire.
"""

import socket
import sys
from pathlib import Path
from typing import Any

import pytest
import requests
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from verifica_fonti import interroga, main, raccogli_url  # noqa: E402


class RispostaFinta:
    def __init__(self, codice: int) -> None:
        self.status_code = codice

    @property
    def ok(self) -> bool:
        return self.status_code < 400


def _rispondi(
    monkeypatch: pytest.MonkeyPatch, esiti: list[int | Exception]
) -> list[tuple[str, str]]:
    """Fa rispondere `requests.request` con la sequenza data, e registra le chiamate."""
    chiamate: list[tuple[str, str]] = []
    coda = list(esiti)

    def finta(metodo: str, url: str, **_: Any) -> RispostaFinta:
        chiamate.append((metodo, url))
        esito = coda.pop(0) if coda else 200
        if isinstance(esito, Exception):
            raise esito
        return RispostaFinta(esito)

    monkeypatch.setattr(requests, "request", finta)
    return chiamate


def test_duecento_e_vivo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Una pagina che risponde è viva, e basta la richiesta HEAD."""
    chiamate = _rispondi(monkeypatch, [200])

    assert interroga("https://esempio.it/a") == (True, "200")
    assert chiamate == [("HEAD", "https://esempio.it/a")]


def test_quattrocentotre_e_vivo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un 403 significa che il server rifiuta il bot, non che la pagina non ci sia.

    Host come Academia.edu e JSTOR rispondono così a qualunque richiesta
    automatica: trattarli da link morti riempirebbe il rapporto settimanale di
    fonti perfettamente vive.
    """
    _rispondi(monkeypatch, [403, 403])

    vivo, esito = interroga("https://esempio.it/b")

    assert vivo is True
    assert esito == "403"


def test_quattrocentoquattro_e_morto(monkeypatch: pytest.MonkeyPatch) -> None:
    """404 e 410 sono gli unici codici che dicono davvero «non c'è più»."""
    _rispondi(monkeypatch, [404])

    assert interroga("https://esempio.it/c") == (False, "404")


def test_head_rifiutato_ripiega_su_get(monkeypatch: pytest.MonkeyPatch) -> None:
    """Diversi server rifiutano HEAD pur servendo la pagina: si riprova con GET."""
    chiamate = _rispondi(monkeypatch, [405, 200])

    vivo, esito = interroga("https://esempio.it/d")

    assert vivo is True
    assert esito == "200"
    assert [metodo for metodo, _ in chiamate] == ["HEAD", "GET"]


def test_host_che_non_risolve_e_morto(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un nome di host sparito è un link morto quanto un 404."""
    errore = requests.ConnectionError("nome non risolto")
    errore.__cause__ = socket.gaierror(-2, "Name or service not known")
    _rispondi(monkeypatch, [errore] * 4)

    assert interroga("https://sparito.invalid/e") == (False, "host non risolto")


def test_timeout_ripetuto_non_e_morto(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un server giù non è una fonte sparita: si segnala come non verificabile.

    È la differenza che tiene il controllo utile: bloccare o allarmare su un
    timeout occasionale lo renderebbe rumore da ignorare.
    """
    _rispondi(monkeypatch, [requests.Timeout("scaduto")] * 4)

    vivo, esito = interroga("https://lento.example/f")

    assert vivo is True
    assert esito.startswith("non verificabile")


def test_si_riprova_prima_di_arrendersi(monkeypatch: pytest.MonkeyPatch) -> None:
    """Il primo errore non basta: un secondo giro evita i falsi positivi."""
    scaduto = requests.Timeout("scaduto")
    chiamate = _rispondi(monkeypatch, [scaduto, scaduto, 200])

    assert interroga("https://esempio.it/g") == (True, "200")
    assert len(chiamate) == 3


def test_raccogli_url_indicizza_gli_elementi_che_citano(tmp_path: Path) -> None:
    """Il rapporto deve dire quali note vanno corrette, non solo quale URL è morto.

    L'ordine segue quello dei file, cioè il numero atomico: è l'ordine in cui
    chi corregge aprirà i file, non quello alfabetico dei nomi.
    """
    elementi = tmp_path / "elements"
    elementi.mkdir()
    for numero, nome in ((1, "Idrogeno"), (2, "Elio")):
        (elementi / f"00{numero}-{nome.lower()}.yaml").write_text(
            yaml.safe_dump(
                {
                    "nome": nome,
                    "fonti": [{"url": "https://condivisa.example/x", "titolo": "X"}],
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )

    citazioni = raccogli_url(tmp_path)

    assert citazioni == {"https://condivisa.example/x": ["Idrogeno", "Elio"]}


def test_il_controllo_non_blocca_mai(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Anche con tutte le fonti morte il comando esce con zero.

    La pubblicazione del vault non deve dipendere dalla salute di server terzi.
    """
    elementi = tmp_path / "elements"
    elementi.mkdir()
    (elementi / "001-idrogeno.yaml").write_text(
        yaml.safe_dump(
            {"nome": "Idrogeno", "fonti": [{"url": "https://morta.example/y", "titolo": "Y"}]},
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    _rispondi(monkeypatch, [404])

    assert main(["--dati", str(tmp_path)]) == 0
