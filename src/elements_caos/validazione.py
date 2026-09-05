"""Controlli di integrità del vault generato.

I controlli sono eseguiti dalla CI a ogni modifica: un vault che li supera è
internamente coerente, ha i collegamenti integri e rispetta i budget di lettura.
"""

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import yaml

from elements_caos.ingest.ritratti import licenza_ammessa
from elements_caos.models import Elemento
from elements_caos.render.prosa import conta_parole

PAROLE_MIN_BASE = 800
PAROLE_MAX_BASE = 1300
PAROLE_MIN_ESTESO = 7000
PAROLE_MAX_ESTESO = 11000

FONTI_MIN_BASE = 2
FONTI_MIN_ESTESO = 4

ESTENSIONI_IMMAGINE = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}

# Cattura sia i collegamenti [[Nota]] sia gli incorporamenti ![[immagine.jpg]],
# con eventuale alias dopo la barra verticale o àncora dopo il cancelletto.
# Nelle tabelle Markdown il pipe dell'alias è preceduto da un backslash
# (es. "[[Fosforo\|P]]"), altrimenti il carattere chiuderebbe la cella della
# tabella: il gruppo catturato esclude quindi anche "\|", non solo "|".
_WIKILINK = re.compile(r"!?\[\[([^\]|#]+?)(?:\\?[|#][^\]]*)?\]\]")


class Gravita(StrEnum):
    """Gravità di un problema rilevato durante la validazione."""

    ERRORE = "errore"
    AVVISO = "avviso"


@dataclass(frozen=True)
class Problema:
    """Anomalia rilevata durante la validazione del vault."""

    gravita: Gravita
    contesto: str
    messaggio: str


def verifica_budget_parole(
    nome: str,
    testo: str,
    minimo: int,
    massimo: int,
) -> list[Problema]:
    """Verifica che un testo rientri nel budget di lettura previsto.

    Il controllo protegge dalla deriva redazionale, per cui le prime note
    diventano lunghissime e le ultime stitiche. Si misura sulla prosa dei
    beat, non sul file .md: quest'ultimo contiene frontmatter, diagrammi e
    tabelle che non sono testo letto dal lettore.
    """
    parole = conta_parole(testo)
    if parole < minimo:
        return [
            Problema(
                gravita=Gravita.ERRORE,
                contesto=nome,
                messaggio=f"{parole} parole, sotto il minimo di {minimo}",
            )
        ]
    if parole > massimo:
        return [
            Problema(
                gravita=Gravita.ERRORE,
                contesto=nome,
                messaggio=f"{parole} parole, sopra il massimo di {massimo}",
            )
        ]
    return []


def verifica_wikilink(vault: Path) -> list[Problema]:
    """Verifica che ogni collegamento interno punti a una nota o a un file esistente."""
    nomi_disponibili = {percorso.stem for percorso in vault.rglob("*.md")}
    nomi_disponibili |= {percorso.name for percorso in vault.rglob("*") if percorso.is_file()}

    problemi: list[Problema] = []
    for nota in sorted(vault.rglob("*.md")):
        testo = nota.read_text(encoding="utf-8")
        for riferimento in _WIKILINK.findall(testo):
            bersaglio = riferimento.strip()
            if bersaglio not in nomi_disponibili:
                problemi.append(
                    Problema(
                        gravita=Gravita.ERRORE,
                        contesto=nota.name,
                        messaggio=f"collegamento rotto verso {bersaglio!r}",
                    )
                )
    return problemi


def verifica_catena_cronologica(posizioni: list[int]) -> list[Problema]:
    """Verifica che le posizioni cronologiche siano consecutive e senza duplicati.

    La catena è ciò che rende il vault percorribile come racconto: un buco
    interromperebbe la navigazione fra un elemento e il successivo.

    Un caso particolare di buco merita una diagnosi diversa: se le posizioni,
    una volta ordinate, sono già contigue fra loro (nessun buco interno) ma
    non iniziano da 1, il problema non è un elemento mancante ma un offset
    sistematico nella numerazione (es. l'indice parte da 0 anziché da 1). Su
    118 elementi, segnalare "manca la posizione 118" manderebbe il redattore
    a cercare un elemento inesistente invece di correggere la numerazione:
    per questo il caso viene riconosciuto ed espresso con un unico messaggio
    che ne indica la causa, non il sintomo.
    """
    problemi: list[Problema] = []

    duplicate = {p for p in posizioni if posizioni.count(p) > 1}
    for posizione in sorted(duplicate):
        problemi.append(
            Problema(
                gravita=Gravita.ERRORE,
                contesto="cronologia",
                messaggio=f"posizione cronologica duplicata: {posizione}",
            )
        )

    distinte = sorted(set(posizioni))
    e_contigua_con_offset = (
        not duplicate
        and len(distinte) == len(posizioni)
        and distinte == list(range(distinte[0], distinte[0] + len(distinte)))
        and distinte[0] != 1
    )
    if e_contigua_con_offset:
        problemi.append(
            Problema(
                gravita=Gravita.ERRORE,
                contesto="cronologia",
                messaggio=(
                    f"le posizioni vanno da {distinte[0]} a {distinte[-1]} anziché da 1 "
                    f"a {len(posizioni)}: la numerazione parte dall'indice sbagliato"
                ),
            )
        )
        return problemi

    attese = set(range(1, len(posizioni) + 1))
    for mancante in sorted(attese - set(posizioni)):
        problemi.append(
            Problema(
                gravita=Gravita.ERRORE,
                contesto="cronologia",
                messaggio=f"posizione cronologica mancante: {mancante}",
            )
        )

    return problemi


def verifica_dati_redazionali(elemento: Elemento) -> list[Problema]:
    """Segnala i campi che l'ingest non popola e che vanno compilati a mano.

    Gli stati di ossidazione non sono forniti dal dataset delle proprietà e
    vengono scritti in fase redazionale. Senza questo controllo resterebbero
    vuoti su tutti e 118 gli elementi senza che nulla lo segnali, e la tabella
    di ogni nota mostrerebbe un trattino al loro posto.
    """
    if not elemento.proprieta.stati_ossidazione:
        return [
            Problema(
                gravita=Gravita.ERRORE,
                contesto=elemento.nome,
                messaggio="stati di ossidazione non compilati",
            )
        ]
    return []


def verifica_licenze_immagini(cartella: Path) -> list[Problema]:
    """Verifica che ogni immagine abbia una licenza registrata e ammessa.

    Nessuna immagine entra nel vault senza che la sua licenza sia nota e
    compatibile con il riuso: è il presidio che protegge chi userà il materiale.
    """
    problemi: list[Problema] = []

    for immagine in sorted(cartella.rglob("*")):
        if not immagine.is_file() or immagine.suffix.lower() not in ESTENSIONI_IMMAGINE:
            continue

        file_licenza = immagine.with_name(f"{immagine.name}.license.yaml")
        if not file_licenza.exists():
            problemi.append(
                Problema(
                    gravita=Gravita.ERRORE,
                    contesto=immagine.name,
                    messaggio="file di licenza assente",
                )
            )
            continue

        dati = yaml.safe_load(file_licenza.read_text(encoding="utf-8")) or {}
        licenza = str(dati.get("licenza", ""))
        if not licenza:
            problemi.append(
                Problema(
                    gravita=Gravita.ERRORE,
                    contesto=immagine.name,
                    messaggio="campo licenza assente o vuoto nel file di licenza",
                )
            )
        elif not licenza_ammessa(licenza):
            problemi.append(
                Problema(
                    gravita=Gravita.ERRORE,
                    contesto=immagine.name,
                    messaggio=f"licenza non ammessa: {licenza}",
                )
            )

    return problemi
