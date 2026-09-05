"""Acquisizione dei ritratti degli scopritori da Wikidata e Wikimedia Commons.

Il filtro sulle licenze è volutamente rigoroso: sono ammesse soltanto le
immagini di pubblico dominio o rilasciate in CC0. Le licenze share-alike
vincolerebbero qualsiasi riuso del vault in altri formati, e per la quasi
totalità degli scopritori — morti da oltre un secolo — il pubblico dominio è
comunque disponibile.

**Nota sulle forme testuali della licenza**: il campo ``LicenseShortName``
restituito dall'API di Commons (``prop=imageinfo&iiprop=extmetadata``) non
riporta il nome del template di licenza (es. ``PD-old-100-expired``, visibile
solo nell'HTML della pagina di descrizione), ma un'etichetta leggibile.
Un'interrogazione reale su un campione di 19 scopritori (incluse figure del
Novecento, più a rischio di copyright ancora attivo) ha restituito nel campo
``LicenseShortName`` soltanto tre valori distinti: ``"Public domain"`` (16
casi su 18 con esito), ``"CC BY-SA 3.0 nl"`` e ``"CC BY-SA 4.0"`` (1 caso
ciascuno, entrambi scartati). Il filtro riconosce quindi ``"public domain"``
come forma di pubblico dominio a pieno titolo, oltre ai codici ``PD-*`` (mai
osservati dall'API in questo campione, ma mantenuti per compatibilità con
altre fonti o con interfacce che li espongono) e ``CC0``.
"""

import re
import time
from dataclasses import dataclass
from pathlib import Path

import requests
import yaml

from elements_caos.models import Ritratto

# Pausa fra le richieste alle API: senza di essa Wikidata risponde 429.
PAUSA_FRA_RICHIESTE = 1.0

INTESTAZIONI = {"User-Agent": "elements-caos/0.1 (vault didattico sugli elementi)"}

API_WIKIDATA = "https://www.wikidata.org/w/api.php"
API_COMMONS = "https://commons.wikimedia.org/w/api.php"

_TAG_HTML = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class InfoLicenza:
    """Metadati di licenza di un'immagine su Wikimedia Commons."""

    licenza: str
    autore: str
    url_file: str
    url_pagina: str


# Forme testuali esatte del pubblico dominio restituite da Commons in
# ``LicenseShortName`` (non codici di template): "Public domain" è di gran
# lunga la più frequente nel campione osservato. È una lista chiusa e va
# ampliata solo dopo aver verificato una nuova forma sull'API reale, non per
# somiglianza testuale con "pubblico dominio".
_FORME_TESTUALI_PD_AMMESSE = {"public domain"}


def licenza_ammessa(licenza: str) -> bool:
    """Stabilisce se una licenza consente l'inclusione dell'immagine nel vault.

    Sono ammessi soltanto il pubblico dominio — sia nella forma dei codici di
    template (``PD-*``) sia nella forma testuale restituita dall'API di
    Commons (``"Public domain"``) — e il CC0. La lista è volutamente chiusa:
    ogni altra licenza, comprese le varianti Creative Commons con obbligo di
    attribuzione o share-alike (CC BY, CC BY-SA, CC BY-NC), GFDL, fair use o
    licenze non dichiarate, viene scartata senza eccezioni. Non esiste un
    fallback permissivo per stringhe non riconosciute: un errore di prudenza
    costa un ritratto in meno, un errore di permissività pubblica un'immagine
    vincolata insieme al vault.
    """
    normalizzata = licenza.strip().lower()
    if not normalizzata:
        return False
    if normalizzata.startswith("pd") or normalizzata == "cc0":
        return True
    return normalizzata in _FORME_TESTUALI_PD_AMMESSE


def _ripulisci_html(testo: str) -> str:
    """Rimuove i tag HTML dai metadati restituiti da Commons."""
    return _TAG_HTML.sub("", testo).strip()


def cerca_entita_wikidata(nome: str) -> str | None:
    """Cerca su Wikidata l'identificativo dell'entità corrispondente al nome."""
    time.sleep(PAUSA_FRA_RICHIESTE)
    risposta = requests.get(
        API_WIKIDATA,
        params={
            "action": "wbsearchentities",
            "search": nome,
            "language": "en",
            "format": "json",
            "limit": "1",
        },
        headers=INTESTAZIONI,
        timeout=30,
    )
    risposta.raise_for_status()
    risultati = risposta.json().get("search", [])
    return risultati[0]["id"] if risultati else None


def recupera_immagine_wikidata(qid: str) -> str | None:
    """Recupera il nome del file immagine associato a un'entità Wikidata."""
    time.sleep(PAUSA_FRA_RICHIESTE)
    risposta = requests.get(
        API_WIKIDATA,
        params={"action": "wbgetclaims", "entity": qid, "property": "P18", "format": "json"},
        headers=INTESTAZIONI,
        timeout=30,
    )
    risposta.raise_for_status()
    dichiarazioni = risposta.json().get("claims", {}).get("P18", [])
    if not dichiarazioni:
        return None
    valore: str = dichiarazioni[0]["mainsnak"]["datavalue"]["value"]
    return valore


def interroga_licenza_commons(nome_file: str) -> InfoLicenza | None:
    """Interroga Commons per conoscere la licenza e l'autore di un'immagine."""
    time.sleep(PAUSA_FRA_RICHIESTE)
    risposta = requests.get(
        API_COMMONS,
        params={
            "action": "query",
            "titles": f"File:{nome_file}",
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "format": "json",
        },
        headers=INTESTAZIONI,
        timeout=30,
    )
    risposta.raise_for_status()

    pagine = risposta.json().get("query", {}).get("pages", {})
    for pagina in pagine.values():
        informazioni = pagina.get("imageinfo")
        if not informazioni:
            continue
        prima = informazioni[0]
        metadati = prima.get("extmetadata", {})
        return InfoLicenza(
            licenza=metadati.get("LicenseShortName", {}).get("value", ""),
            autore=_ripulisci_html(metadati.get("Artist", {}).get("value", "ignoto")),
            url_file=prima["url"],
            url_pagina=prima["descriptionurl"],
        )
    return None


def scarica_ritratto(info: InfoLicenza, destinazione: Path) -> Ritratto:
    """Scarica un ritratto e ne registra la licenza in un file affiancato.

    Il file di licenza è obbligatorio: la validazione del vault rifiuta ogni
    immagine che non lo possieda.
    """
    if not licenza_ammessa(info.licenza):
        raise ValueError(f"licenza non ammessa per {destinazione.name}: {info.licenza!r}")

    risposta = requests.get(info.url_file, headers=INTESTAZIONI, timeout=60)
    risposta.raise_for_status()

    destinazione.parent.mkdir(parents=True, exist_ok=True)
    destinazione.write_bytes(risposta.content)

    ritratto = Ritratto(
        file=destinazione.name,
        licenza=info.licenza,
        autore=info.autore,
        fonte=info.url_pagina,
    )

    file_licenza = destinazione.with_name(f"{destinazione.name}.license.yaml")
    file_licenza.write_text(
        yaml.safe_dump(ritratto.model_dump(), allow_unicode=True, sort_keys=True),
        encoding="utf-8",
    )

    return ritratto
