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
    [
        # Forma testuale realmente restituita da Commons in LicenseShortName:
        # osservata in 16 casi su 18 in un campione di scopritori reali
        # (Hennig Brand, Humphry Davy, Marie Curie, Lavoisier, Scheele,
        # Seaborg, Mendeleev, Rutherford, Hahn, Meitner, Ghiorso, Bohr,
        # Segrè, Flerov, Lecoq de Boisbaudran, Ramsay).
        "Public domain",
        "public domain",
        # Codici di template Commons: non osservati nel campione reale
        # dell'API (compaiono solo nell'HTML della pagina di descrizione),
        # ma mantenuti per compatibilità con altre fonti.
        "PD-old-100-expired",
        "PD-US",
        "PD-old-70",
        "pd-art",
        # Template Commons per opere sotto la soglia di originalità (loghi
        # semplici, forme geometriche): pubblico dominio a tutti gli
        # effetti, non un falso positivo del prefisso.
        "PD-ineligible",
        "CC0",
        "cc0",
    ],
)
def test_licenze_ammesse(licenza: str) -> None:
    """Le licenze di pubblico dominio (testuali o a codice) e CC0 sono ammesse."""
    assert licenza_ammessa(licenza) is True


@pytest.mark.parametrize(
    "licenza",
    [
        # Osservate realmente su Commons per scopritori recenti/viventi:
        # Yuri Oganessian ("CC BY-SA 3.0 nl") e Marguerite Perey
        # ("CC BY-SA 4.0"). Lo share-alike vincolerebbe qualsiasi riuso del
        # vault in altri formati: va scartato anche se sembra innocuo.
        "CC BY-SA 3.0 nl",
        "CC BY-SA 4.0",
        "CC BY-SA 3.0",
        "CC BY 4.0",
        "GFDL",
        "Fair use",
        "All rights reserved",
        "CC BY-NC",
        "",
        # Stringhe insidiose: iniziano per "pd" ma non sono affatto pubblico
        # dominio. Un prefisso "pd" senza separatore le ammetterebbe per
        # errore: il filtro deve restare chiuso su "pd-" o "pd" esatto.
        #
        # NOTA: "PD-ineligible" non è in questo elenco nonostante sia stato
        # proposto come stringa insidiosa in revisione. È un template Commons
        # reale (opere sotto la soglia di originalità, es. loghi semplici o
        # forme geometriche): ha il prefisso "pd-" legittimo ed è pubblico
        # dominio a tutti gli effetti, non un falso positivo del prefisso
        # generico. Con "pd-" come separatore obbligatorio resta AMMESSA, ed
        # è la decisione corretta: va nel test delle licenze ammesse (sotto).
        "PDF",
        "PD but restricted",
        "pdm-owner",
        # Contengono la sottostringa "public domain" ma la negano o la
        # condizionano: il confronto sulle forme testuali è per uguaglianza
        # esatta, non per sottostringa, e deve scartarle.
        "Not in the public domain",
        "CC BY-SA (public domain in some countries)",
    ],
)
def test_licenze_rifiutate(licenza: str) -> None:
    """Ogni licenza diversa da pubblico dominio o CC0 viene rifiutata.

    Il filtro è volutamente rigoroso e a lista chiusa: le licenze share-alike
    vincolerebbero qualsiasi riuso del vault in altri formati, e una stringa
    non riconosciuta non ha un fallback permissivo.
    """
    assert licenza_ammessa(licenza) is False


def test_licenza_ammessa_ignora_spazi_e_maiuscole() -> None:
    """Il confronto sulle licenze non dipende da spazi o maiuscole."""
    assert licenza_ammessa("  PD-old-100  ") is True
    assert licenza_ammessa("  Public Domain  ") is True


def test_interroga_licenza_commons_estrae_i_metadati() -> None:
    """I metadati della licenza vengono estratti dalla risposta dell'API.

    La risposta ricalca quella reale osservata per Hennig Brand: Commons
    espone in ``LicenseShortName`` la forma testuale "Public domain", non un
    codice di template come "PD-old-100-expired".
    """
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
                                "LicenseShortName": {"value": "Public domain"},
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
    assert info.licenza == "Public domain"
    assert info.autore == "Joseph Wright of Derby"
    assert info.url_file == "https://upload.wikimedia.org/x/Brand.jpg"


def test_interroga_licenza_commons_estrae_codice_template_pd() -> None:
    """Il campo licenza viene estratto integralmente anche quando è un codice PD-*.

    Questa forma non è mai comparsa nel campione reale di LicenseShortName,
    ma la funzione di estrazione non fa distinzioni: il filtro sulle forme
    ammesse è responsabilità di `licenza_ammessa`, non di questa funzione.
    """
    risposta = MagicMock()
    risposta.json.return_value = {
        "query": {
            "pages": {
                "123": {
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/x/Brand2.jpg",
                            "descriptionurl": "https://commons.wikimedia.org/wiki/File:Brand2.jpg",
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
        info = interroga_licenza_commons("Brand2.jpg")

    assert info is not None
    assert info.licenza == "PD-old-100-expired"


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
    """Un ritratto ammesso viene salvato insieme al suo file di licenza.

    Licenza "Public domain": è la forma esatta restituita da Commons per il
    ritratto reale di Hennig Brand, non un codice di template inventato.
    """
    info = InfoLicenza(
        licenza="Public domain",
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
    assert ritratto.licenza == "Public domain"
    assert ritratto.file == "hennig-brand.jpg"


def test_scarica_ritratto_scrive_prima_la_licenza_poi_immagine(tmp_path: Path) -> None:
    """La licenza va scritta prima dell'immagine, non dopo.

    Se qualcosa fallisce fra le due scritture, l'unico stato transitorio
    possibile deve essere "licenza senza immagine": innocuo, perché la
    validazione del vault controlla che ogni immagine abbia la sua licenza,
    non il contrario. Il contrario ("immagine senza licenza") farebbe
    fallire la validazione senza che sia chiaro il perché.
    """
    info = InfoLicenza(
        licenza="Public domain",
        autore="Joseph Wright of Derby",
        url_file="https://esempio.it/brand.jpg",
        url_pagina="https://commons.wikimedia.org/wiki/File:Brand.jpg",
    )
    risposta = MagicMock()
    risposta.content = b"contenuto-immagine"
    risposta.raise_for_status.return_value = None

    ordine_scritture: list[str] = []
    write_text_originale = Path.write_text
    write_bytes_originale = Path.write_bytes

    def _registra_write_text(self: Path, *args: object, **kwargs: object) -> int:
        ordine_scritture.append("licenza")
        return write_text_originale(self, *args, **kwargs)  # type: ignore[arg-type]

    def _registra_write_bytes(self: Path, *args: object, **kwargs: object) -> int:
        ordine_scritture.append("immagine")
        return write_bytes_originale(self, *args, **kwargs)  # type: ignore[arg-type]

    destinazione = tmp_path / "hennig-brand.jpg"
    with (
        patch("elements_caos.ingest.ritratti.requests.get", return_value=risposta),
        patch.object(Path, "write_text", _registra_write_text),
        patch.object(Path, "write_bytes", _registra_write_bytes),
    ):
        scarica_ritratto(info, destinazione)

    assert ordine_scritture == ["licenza", "immagine"]


def test_scarica_ritratto_rimuove_licenza_orfana_se_immagine_fallisce(
    tmp_path: Path,
) -> None:
    """Se la scrittura dell'immagine fallisce non deve restare alcun file orfano.

    Simula il fallimento della scrittura dell'immagine (la seconda, nel nuovo
    ordine): il file di licenza, scritto per primo, deve essere rimosso.
    """
    info = InfoLicenza(
        licenza="Public domain",
        autore="Joseph Wright of Derby",
        url_file="https://esempio.it/brand.jpg",
        url_pagina="https://commons.wikimedia.org/wiki/File:Brand.jpg",
    )
    risposta = MagicMock()
    risposta.content = b"contenuto-immagine"
    risposta.raise_for_status.return_value = None

    destinazione = tmp_path / "hennig-brand.jpg"
    with (
        patch("elements_caos.ingest.ritratti.requests.get", return_value=risposta),
        patch.object(Path, "write_bytes", side_effect=OSError("disco pieno")),
        pytest.raises(OSError, match="disco pieno"),
    ):
        scarica_ritratto(info, destinazione)

    assert not destinazione.exists()
    assert not (tmp_path / "hennig-brand.jpg.license.yaml").exists()


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
