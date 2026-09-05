"""Test dell'acquisizione dei ritratti e del filtro sulle licenze."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from elements_caos.ingest.ritratti import (
    InfoLicenza,
    interroga_licenza_commons,
    licenza_ammessa,
    scarica_ritratto,
)


@pytest.mark.parametrize(
    "licenza",
    ["PD-old-100-expired", "PD-US", "PD-old-70", "pd-art", "CC0", "cc0"],
)
def test_licenze_ammesse(licenza: str) -> None:
    """Le licenze di pubblico dominio e CC0 sono ammesse nel vault."""
    assert licenza_ammessa(licenza) is True


@pytest.mark.parametrize(
    "licenza",
    [
        "CC BY-SA 3.0",
        "CC BY 4.0",
        "CC BY-SA 4.0",
        "GFDL",
        "Fair use",
        "All rights reserved",
        "CC BY-NC",
        "",
    ],
)
def test_licenze_rifiutate(licenza: str) -> None:
    """Ogni licenza diversa da pubblico dominio o CC0 viene rifiutata.

    Il filtro è volutamente rigoroso: le licenze share-alike vincolerebbero
    qualsiasi riuso del vault in altri formati.
    """
    assert licenza_ammessa(licenza) is False


def test_licenza_ammessa_ignora_spazi_e_maiuscole() -> None:
    """Il confronto sulle licenze non dipende da spazi o maiuscole."""
    assert licenza_ammessa("  PD-old-100  ") is True


def test_interroga_licenza_commons_estrae_i_metadati() -> None:
    """I metadati della licenza vengono estratti dalla risposta dell'API."""
    risposta = MagicMock()
    risposta.json.return_value = {
        "query": {
            "pages": {
                "123": {
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/x/Brand.jpg",
                            "descriptionurl": "https://commons.wikimedia.org/wiki/File:Brand.jpg",
                            "extmetadata": {
                                "LicenseShortName": {"value": "PD-old-100-expired"},
                                "Artist": {"value": "Joseph Wright of Derby"},
                            },
                        }
                    ]
                }
            }
        }
    }
    risposta.raise_for_status.return_value = None

    with patch("elements_caos.ingest.ritratti.requests.get", return_value=risposta):
        info = interroga_licenza_commons("Brand.jpg")

    assert info is not None
    assert info.licenza == "PD-old-100-expired"
    assert info.autore == "Joseph Wright of Derby"
    assert info.url_file == "https://upload.wikimedia.org/x/Brand.jpg"


def test_interroga_licenza_commons_ripulisce_html_dell_autore() -> None:
    """Il campo autore di Commons contiene HTML che va rimosso."""
    risposta = MagicMock()
    risposta.json.return_value = {
        "query": {
            "pages": {
                "123": {
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/x/A.jpg",
                            "descriptionurl": "https://commons.wikimedia.org/wiki/File:A.jpg",
                            "extmetadata": {
                                "LicenseShortName": {"value": "CC0"},
                                "Artist": {"value": '<a href="/wiki/User:Tizio">Tizio Caio</a>'},
                            },
                        }
                    ]
                }
            }
        }
    }
    risposta.raise_for_status.return_value = None

    with patch("elements_caos.ingest.ritratti.requests.get", return_value=risposta):
        info = interroga_licenza_commons("A.jpg")

    assert info is not None
    assert info.autore == "Tizio Caio"


def test_interroga_licenza_commons_file_assente() -> None:
    """Un file inesistente su Commons restituisce None, non un errore."""
    risposta = MagicMock()
    risposta.json.return_value = {"query": {"pages": {"-1": {"missing": ""}}}}
    risposta.raise_for_status.return_value = None

    with patch("elements_caos.ingest.ritratti.requests.get", return_value=risposta):
        assert interroga_licenza_commons("Inesistente.jpg") is None


def test_scarica_ritratto_rifiuta_licenza_non_ammessa(tmp_path: Path) -> None:
    """Un ritratto con licenza non ammessa non viene scaricato."""
    info = InfoLicenza(
        licenza="CC BY-SA 4.0",
        autore="Tizio",
        url_file="https://esempio.it/x.jpg",
        url_pagina="https://commons.wikimedia.org/wiki/File:X.jpg",
    )

    with pytest.raises(ValueError, match="licenza non ammessa"):
        scarica_ritratto(info, tmp_path / "x.jpg")


def test_scarica_ritratto_salva_file_e_licenza(tmp_path: Path) -> None:
    """Un ritratto ammesso viene salvato insieme al suo file di licenza."""
    info = InfoLicenza(
        licenza="PD-old-100-expired",
        autore="Joseph Wright of Derby",
        url_file="https://esempio.it/brand.jpg",
        url_pagina="https://commons.wikimedia.org/wiki/File:Brand.jpg",
    )
    risposta = MagicMock()
    risposta.content = b"contenuto-immagine"
    risposta.raise_for_status.return_value = None

    destinazione = tmp_path / "hennig-brand.jpg"
    with patch("elements_caos.ingest.ritratti.requests.get", return_value=risposta):
        ritratto = scarica_ritratto(info, destinazione)

    assert destinazione.read_bytes() == b"contenuto-immagine"
    assert (tmp_path / "hennig-brand.jpg.license.yaml").exists()
    assert ritratto.licenza == "PD-old-100-expired"
    assert ritratto.file == "hennig-brand.jpg"


def test_file_licenza_contiene_i_metadati(tmp_path: Path) -> None:
    """Il file di licenza riporta autore, licenza e fonte in formato YAML."""
    import yaml

    info = InfoLicenza(
        licenza="CC0",
        autore="Anonimo",
        url_file="https://esempio.it/y.jpg",
        url_pagina="https://commons.wikimedia.org/wiki/File:Y.jpg",
    )
    risposta = MagicMock()
    risposta.content = b"x"
    risposta.raise_for_status.return_value = None

    destinazione = tmp_path / "y.jpg"
    with patch("elements_caos.ingest.ritratti.requests.get", return_value=risposta):
        scarica_ritratto(info, destinazione)

    dati = yaml.safe_load((tmp_path / "y.jpg.license.yaml").read_text(encoding="utf-8"))

    assert dati["licenza"] == "CC0"
    assert dati["autore"] == "Anonimo"
    assert dati["fonte"] == "https://commons.wikimedia.org/wiki/File:Y.jpg"
