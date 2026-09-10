"""Interfaccia a riga di comando per la generazione e la validazione del vault."""

import argparse
import sys
from pathlib import Path

import yaml

from elements_caos.caricamento import (
    ErroreCaricamento,
    carica_elementi,
    carica_epoche,
    carica_itinerario,
    carica_scopritori,
    ordina_per_scoperta,
)
from elements_caos.ingest.ritratti import licenza_ammessa
from elements_caos.models import Sezione
from elements_caos.render.atomo_svg import nome_file_atomo, rendi_atomo_svg
from elements_caos.render.navigazione import (
    rendi_attribuzioni,
    rendi_cronologia,
    rendi_epoca,
    rendi_scopritore,
    rendi_tavola,
)
from elements_caos.render.note import costruisci_contesto, nome_file_nota, rendi_nota
from elements_caos.render.prosa import componi_sezione
from elements_caos.validazione import (
    FONTI_MIN_BASE,
    PAROLE_MAX_BASE,
    PAROLE_MIN_BASE,
    Gravita,
    Problema,
    verifica_budget_parole,
    verifica_catena_cronologica,
    verifica_dati_redazionali,
    verifica_licenze_immagini,
    verifica_wikilink,
)

CODICE_SUCCESSO = 0
CODICE_PROBLEMI = 1
CODICE_ERRORE_DATI = 2
CODICE_ERRORE_SISTEMA = 3


def _scrivi(percorso: Path, contenuto: str) -> None:
    """Scrive un file di testo creando le cartelle intermedie necessarie."""
    percorso.parent.mkdir(parents=True, exist_ok=True)
    percorso.write_text(contenuto, encoding="utf-8")


def _rimuovi_orfane(cartella: Path, attesi: set[str], pattern: str = "*.md") -> None:
    """Elimina dalla cartella i file che nessun dato genera più.

    Senza questa pulizia, rinominare un elemento (o un'immagine) lascerebbe
    nel vault un file fantasma privo di corrispondenza nei dati. Le
    sottocartelle vengono sempre ignorate, anche quando corrispondono al
    pattern: il generatore possiede solo i file che scrive lui al primo
    livello, non le cartelle che un utente crea a mano (ad esempio per
    organizzare varianti di un'immagine) — rimuoverle, oltre a eccedere ciò
    che il comando possiede, solleverebbe comunque un errore, perché
    ``Path.unlink()`` non è pensato per le directory.
    """
    if not cartella.is_dir():
        return
    for percorso in cartella.glob(pattern):
        if percorso.is_dir():
            continue
        if percorso.name not in attesi:
            percorso.unlink()


def _licenza_di(immagine: Path) -> str | None:
    """Legge la licenza dichiarata nel file affiancato a un'immagine.

    Restituisce ``None`` se il file di licenza manca o se il campo licenza è
    assente o vuoto: in entrambi i casi l'immagine non ha una provenienza
    verificabile e non deve entrare nel vault.
    """
    file_licenza = immagine.with_name(f"{immagine.name}.license.yaml")
    if not file_licenza.exists():
        return None
    dati = yaml.safe_load(file_licenza.read_text(encoding="utf-8")) or {}
    # Un campo "licenza:" senza valore diventa None in YAML: str(None) darebbe
    # la stringa "None", che sfuggirebbe al controllo di campo vuoto.
    licenza = str(dati.get("licenza") or "")
    return licenza or None


def _sincronizza_immagini(cartella_immagini_dati: Path, cartella_vault: Path) -> None:
    """Copia nel vault i soli ritratti con licenza nota e ammessa.

    Le note degli scopritori incorporano i ritratti con un wikilink
    ``![[file.jpg]]``: perché Obsidian risolva l'incorporamento — e perché la
    validazione dei wikilink non lo segnali come rotto — il file immagine deve
    esistere fisicamente dentro il vault, non solo nella cartella dati che lo
    ha originato. La copia avviene in ``Immagini/``, sotto lo stesso nome:
    Obsidian risolve un embed per nome file ovunque si trovi nel vault, quindi
    non è necessario replicare alcuna struttura di sottocartelle.

    Il controllo sulla licenza avviene qui, non solo nella validazione
    successiva: un'immagine senza licenza nota o con licenza fuori allowlist
    non deve mai toccare il disco del vault, perché chi esegue ``genera`` a
    mano e pubblica senza eseguire ``valida`` si porterebbe altrimenti
    un'immagine di provenienza incerta in un repository pubblico. La
    validazione (Task 10) resta comunque attiva come rete di sicurezza per le
    immagini aggiunte a mano nel vault, che non passano da questa funzione.
    """
    cartella_destinazione = cartella_vault / "Immagini"
    if not cartella_immagini_dati.is_dir():
        _rimuovi_orfane(cartella_destinazione, set())
        return

    attesi: set[str] = set()
    for origine in sorted(cartella_immagini_dati.iterdir()):
        if not origine.is_file() or origine.suffix == ".yaml":
            continue

        licenza = _licenza_di(origine)
        if licenza is None:
            print(f"Immagine saltata: {origine.name} — licenza assente o non registrata")
            continue
        if not licenza_ammessa(licenza):
            print(f"Immagine saltata: {origine.name} — licenza non ammessa: {licenza}")
            continue

        attesi.add(origine.name)
        destinazione = cartella_destinazione / origine.name
        destinazione.parent.mkdir(parents=True, exist_ok=True)
        destinazione.write_bytes(origine.read_bytes())

        file_licenza = origine.with_name(f"{origine.name}.license.yaml")
        attesi.add(file_licenza.name)
        _scrivi(cartella_destinazione / file_licenza.name, file_licenza.read_text(encoding="utf-8"))
    _rimuovi_orfane(cartella_destinazione, attesi, pattern="*")


def genera_vault(cartella_dati: Path, cartella_vault: Path) -> int:
    """Genera l'intero vault a partire dai dati, sostituendo il contenuto esistente."""
    elementi = carica_elementi(cartella_dati / "elements")
    scopritori = carica_scopritori(cartella_dati / "scopritori.yaml")
    epoche = carica_epoche(cartella_dati / "epoche.yaml")
    itinerario = carica_itinerario(cartella_dati / "itinerario.yaml")

    note_attese: set[str] = set()
    for elemento in elementi:
        contesto = costruisci_contesto(elemento, elementi, scopritori, epoche)
        nome = nome_file_nota(elemento)
        note_attese.add(nome)
        _scrivi(cartella_vault / "Elementi" / nome, rendi_nota(contesto))
    _rimuovi_orfane(cartella_vault / "Elementi", note_attese)

    epoche_attese: set[str] = set()
    for epoca in epoche.values():
        nome = f"{epoca.nome}.md"
        epoche_attese.add(nome)
        _scrivi(cartella_vault / "Epoche" / nome, rendi_epoca(epoca, elementi, scopritori))
    _rimuovi_orfane(cartella_vault / "Epoche", epoche_attese)

    scopritori_attesi: set[str] = set()
    for scopritore in scopritori.values():
        nome = f"{scopritore.nome}.md"
        scopritori_attesi.add(nome)
        _scrivi(
            cartella_vault / "Scopritori" / nome,
            rendi_scopritore(scopritore, elementi, scopritori),
        )
    _rimuovi_orfane(cartella_vault / "Scopritori", scopritori_attesi)

    _scrivi(
        cartella_vault / "Cronologia degli elementi.md",
        rendi_cronologia(elementi, epoche, itinerario, scopritori),
    )
    _scrivi(cartella_vault / "Tavola periodica.md", rendi_tavola(elementi, scopritori))
    _scrivi(cartella_vault / "Attribuzioni.md", rendi_attribuzioni(scopritori))

    _sincronizza_immagini(cartella_dati / "images", cartella_vault)

    # Diagrammi atomici: scritti dopo _sincronizza_immagini, che ripulisce
    # l'intera cartella Immagini dai ritratti orfani con pattern "*" — se gli
    # SVG venissero scritti prima, quella chiamata li cancellerebbe subito
    # dopo, non essendo nel suo set di attesi. La rimozione delle orfane qui
    # usa un pattern ristretto ("atomo-*.svg") per non toccare i ritratti.
    svg_attesi: set[str] = set()
    for elemento in elementi:
        nome_svg = nome_file_atomo(elemento)
        svg_attesi.add(nome_svg)
        _scrivi(cartella_vault / "Immagini" / nome_svg, rendi_atomo_svg(elemento))
    _rimuovi_orfane(cartella_vault / "Immagini", svg_attesi, pattern="atomo-*.svg")

    print(f"Generate {len(elementi)} note di elementi in {cartella_vault}")
    return CODICE_SUCCESSO


def valida_vault(cartella_dati: Path, cartella_vault: Path, salta_budget: bool) -> int:
    """Esegue tutti i controlli di integrità sul vault e ne riporta l'esito."""
    elementi = carica_elementi(cartella_dati / "elements")
    problemi: list[Problema] = []

    problemi.extend(verifica_wikilink(cartella_vault))
    problemi.extend(
        verifica_catena_cronologica(list(range(1, len(ordina_per_scoperta(elementi)) + 1)))
    )

    cartella_immagini = cartella_dati / "images"
    if cartella_immagini.is_dir():
        problemi.extend(verifica_licenze_immagini(cartella_immagini))

    for elemento in elementi:
        problemi.extend(verifica_dati_redazionali(elemento))

        if len(elemento.fonti) < FONTI_MIN_BASE:
            problemi.append(
                Problema(
                    gravita=Gravita.ERRORE,
                    contesto=elemento.nome,
                    messaggio=(f"{len(elemento.fonti)} fonti, minimo richiesto {FONTI_MIN_BASE}"),
                )
            )

        if salta_budget or elemento.contenuti is None:
            continue

        # Il budget si misura sulla PROSA REDAZIONALE, cioe' sui beat, non sul
        # file .md generato: quello contiene frontmatter, diagrammi Mermaid,
        # tabelle e navigazione (circa 325 token) che nessuno legge come testo.
        # Misurarli farebbe sforare il massimo a una nota scritta correttamente.
        # E' anche la stessa base su cui il rendering calcola tempo_lettura:
        # le due misure devono coincidere, altrimenti la nota dichiara un tempo
        # e la validazione ne verifica un altro.
        prosa = "\n\n".join(componi_sezione(elemento.contenuti, sezione) for sezione in Sezione)
        problemi.extend(
            verifica_budget_parole(
                elemento.nome,
                prosa,
                PAROLE_MIN_BASE,
                PAROLE_MAX_BASE,
            )
        )

    errori = [p for p in problemi if p.gravita is Gravita.ERRORE]
    for problema in problemi:
        print(f"[{problema.gravita.value}] {problema.contesto}: {problema.messaggio}")

    if errori:
        print(f"\n{len(errori)} errori rilevati.")
        return CODICE_PROBLEMI

    print("Vault integro: nessun problema rilevato.")
    return CODICE_SUCCESSO


def main(argv: list[str] | None = None) -> int:
    """Punto di ingresso della riga di comando."""
    analizzatore = argparse.ArgumentParser(
        prog="elements-caos",
        description="Genera e valida il vault Obsidian sulla storia degli elementi.",
    )
    sottocomandi = analizzatore.add_subparsers(dest="comando", required=True)

    for nome, aiuto in (
        ("genera", "Genera il vault a partire dai dati YAML."),
        ("valida", "Verifica l'integrità del vault generato."),
    ):
        sotto = sottocomandi.add_parser(nome, help=aiuto)
        sotto.add_argument("--dati", type=Path, default=Path("data"))
        sotto.add_argument("--vault", type=Path, default=Path("vault"))
        if nome == "valida":
            sotto.add_argument(
                "--salta-budget",
                action="store_true",
                help="Non verifica il budget di parole (utile finché i contenuti sono parziali).",
            )

    argomenti = analizzatore.parse_args(argv)

    try:
        if argomenti.comando == "genera":
            return genera_vault(argomenti.dati, argomenti.vault)
        return valida_vault(argomenti.dati, argomenti.vault, argomenti.salta_budget)
    except ErroreCaricamento as errore:
        print(f"Errore nei dati: {errore}", file=sys.stderr)
        return CODICE_ERRORE_DATI
    except OSError as errore:
        # Permessi negati, disco pieno, percorso non scrivibile: sono errori
        # di sistema, non di dati. È un comando eseguito a mano dall'utente:
        # un traceback grezzo non gli direbbe dove intervenire, un messaggio
        # che nomina il percorso coinvolto sì.
        percorso = errore.filename or "percorso non specificato"
        print(f"Errore di sistema su {percorso}: {errore.strerror}", file=sys.stderr)
        return CODICE_ERRORE_SISTEMA


if __name__ == "__main__":
    raise SystemExit(main())
