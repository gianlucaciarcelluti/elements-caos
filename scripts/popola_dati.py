"""Popola i file YAML degli elementi unendo cronologia e proprietà.

Lo script è idempotente e non distruttivo: i blocchi ``contenuti`` già
compilati non vengono mai sovrascritti. Rilanciarlo aggiorna solo i dati di
base.

**Nota sul nome italiano (Ruling 39)**: il nome italiano dell'elemento viene
letto da ``voce_cronologia.nome``, non più dal file YAML esistente con
ripiego sul nome inglese del dataset. La versione precedente
(``esistente.get("nome", voce_dataset["name"])``) creava una dipendenza
circolare: se il file YAML veniva cancellato, l'unico posto dove il nome
italiano era scritto spariva con lui, e lo script ripiegava in silenzio sul
nome inglese, rigenerando un file con nome sbagliato invece di segnalare il
problema. Il nome italiano è ora un dato di riferimento in
``CRONOLOGIA``, come anno, scopritori ed epoca: sopravvive alla cancellazione
di un file perché non dipende da esso.

**Nota sulla preservazione di ``scoperta.luogo`` e ``scoperta.controversia``**:
questi due sottocampi sono dati redazionali (narrativi/storiografici) al pari
dei blocchi ``contenuti*``, non dati strutturali della cronologia. Se già
presenti in un file esistente vengono sempre mantenuti, anche quando lo
script aggiorna gli altri sottocampi di ``scoperta`` (anno, epoca,
scopritori, ecc.): sovrascriverli incondizionatamente cancellerebbe il
lavoro redazionale già svolto sui 4 elementi pilota (rame, fosforo, sodio,
plutonio), che il Task 13 deve preservare per requisito esplicito.

**Nota sulla preservazione di ``proprieta.stati_ossidazione``**: come da
Ruling 23 e Ruling 36 del progetto, gli stati di ossidazione non sono forniti
dal dataset esterno (``estrai_proprieta`` restituisce sempre lista vuota) e
sono un dato REDAZIONALE compilato a mano nei Task 14-19, esattamente come
``contenuti`` o ``fonti``. Anche se il campo vive dentro il blocco
``proprieta``, che per il resto è interamente rigenerato dal dataset a ogni
esecuzione, questo singolo sottocampo va preservato quando è già stato
compilato: senza questa eccezione lo script non sarebbe realmente
idempotente/non distruttivo come dichiara, e un rilancio dopo i Task 14-19
azzererebbe in silenzio il lavoro fatto su tutti e 118 gli elementi (la
validazione segnala "non compilati" in modo indistinguibile da "mai
scritti", quindi la perdita non sarebbe nemmeno visibile a un controllo
superficiale).

**Nota sulla preservazione di ``punto_fusione_k``, ``punto_ebollizione_k`` e
``densita`` (Ruling 37)**: stessa causa della Ruling 36, applicata a tre
campi diversi con una semantica leggermente diversa. Questi tre NON sono dati
redazionali in generale: sono dichiaratamente dataset-driven, e quando il
dataset porta un valore quel valore vince sempre, anche se diverso da quello
già scritto (è la fonte automatica dichiarata, e un suo aggiornamento deve
propagarsi). La sola eccezione è quando il dataset riporta ``null`` mentre lo
YAML esistente ha già un valore: lì il ``null`` del dataset significa "il
dataset non lo sa", non "il dato non esiste", e non può cancellare un valore
verificato in fase redazionale (caso reale: il fosforo pilota aveva
``punto_fusione_k: 317.3`` / ``punto_ebollizione_k: 553.7`` scritti a mano
prima che esistesse l'ingest automatico; il dataset esterno riporta ``None``
per entrambi, e senza questa eccezione un rilancio li cancellava,
sostituendo un'affermazione vera con un'affermazione falsa nella nota
generata — "dato non disponibile" per un valore notissimo). La regola vale
solo per riempire i buchi (dataset null → valore esistente), mai per far
vincere sempre lo YAML esistente sul dataset.

**Nota sulla doppia sorgente di ``scoperta.note_cronologia`` (Ruling 41)**:
questo campo ha DUE sorgenti legittime, non una sola come potrebbe
suggerire il resto del blocco ``scoperta`` (dove CRONOLOGIA è sempre
autorevole). La prima è la trascrizione automatica: il testo di
``voce_cronologia.note`` in ``cronologia.py``, scritto durante la verifica
storica della fonte. La seconda è la rifinitura redazionale: un testo
scritto o riscritto a mano su un file YAML esistente durante il lavoro sui
contenuti (Task 12 sui 4 piloti, Task 14-19 su tutti gli altri), spesso più
ricco o più preciso del testo automatico perché frutto di una ricerca
mirata su quell'elemento specifico. **La rifinitura redazionale vince
sempre**, esattamente come per ``contenuti``, ``fonti`` e
``stati_ossidazione``: se invertissimo questa precedenza, il prossimo
rilancio dell'ingest cancellerebbe silenziosamente il lavoro fatto sui
piloti, lo stesso difetto già corretto due volte in questo task (Ruling 36
e Ruling 37) ma applicato a un campo diverso. La riga
``scoperta_esistente.get("note_cronologia") or voce_cronologia.note`` più
sotto implementa esattamente questa precedenza: il valore esistente (la
rifinitura) vince quando c'è, il testo di CRONOLOGIA (la trascrizione)
riempie il buco solo quando il file non ne ha ancora uno. Non è un
dimenticare-di-aggiornare: è la scelta corretta, resa esplicita qui perché
prima non lo era abbastanza da distinguersi da un mancato aggiornamento.
"""

import sys
from pathlib import Path
from typing import Any

import yaml

from elements_caos.ingest.cronologia import CRONOLOGIA
from elements_caos.ingest.proprieta import estrai_proprieta, leggi_dataset, scarica_dataset
from elements_caos.models import Proprieta

CARTELLA_DATI = Path("data/elements")
CACHE_DATASET = Path(".cache/periodic-table.json")


def _nome_file(numero: int, nome: str) -> str:
    """Costruisce il nome del file YAML di un elemento."""
    return f"{numero:03d}-{nome.lower().replace(' ', '-')}.yaml"


def costruisci_documento(
    numero: int,
    voce_dataset: dict[str, Any],
    voce_cronologia: Any,
    proprieta: Proprieta,
    esistente: dict[str, Any],
) -> dict[str, Any]:
    """Unisce dataset, cronologia e dati esistenti nel documento YAML di un elemento.

    Funzione pura, senza I/O: isolata così da poter essere testata senza
    passare da file su disco. Riceve ``esistente`` già deserializzato (il
    contenuto del file YAML corrente, o un dizionario vuoto se il file non
    esiste ancora) e restituisce il nuovo documento da scrivere.
    """
    scoperta_esistente = esistente.get("scoperta") or {}
    proprieta_esistente = esistente.get("proprieta") or {}
    proprieta_dict = proprieta.model_dump(mode="json")

    # Gli stati di ossidazione sono un dato redazionale (Ruling 23/36): se già
    # compilati a mano su un file esistente, sopravvivono SEMPRE alla
    # rigenerazione del resto del blocco proprieta, indipendentemente da cosa
    # dice il dataset (che per questo campo restituisce sempre lista vuota).
    stati_ossidazione_esistenti = proprieta_esistente.get("stati_ossidazione")
    if stati_ossidazione_esistenti:
        proprieta_dict["stati_ossidazione"] = stati_ossidazione_esistenti

    # Punto di fusione, punto di ebollizione e densità (Ruling 37): a
    # differenza degli stati di ossidazione, questi sono dati dataset-driven
    # e il dataset vince quando ha un valore, ANCHE se diverso da quello
    # esistente (aggiornamento della fonte). Solo quando il dataset riporta
    # null e lo YAML esistente ha già un valore, quel valore sopravvive: un
    # null del dataset è una lacuna della fonte, non un'informazione che il
    # dato non esista, e non deve cancellare un valore verificato.
    for campo in ("punto_fusione_k", "punto_ebollizione_k", "densita"):
        if proprieta_dict.get(campo) is None and proprieta_esistente.get(campo) is not None:
            proprieta_dict[campo] = proprieta_esistente[campo]

    # note_cronologia ha due sorgenti legittime (Ruling 41): il testo della
    # trascrizione automatica (voce_cronologia.note, da CRONOLOGIA) e
    # un'eventuale rifinitura redazionale già scritta a mano sul file
    # esistente. La seconda, quando c'è, vince sempre — stessa precedenza di
    # contenuti, fonti e stati_ossidazione — perché nasce da una ricerca
    # mirata su quell'elemento e non deve essere cancellata da un rilancio
    # dell'ingest automatico. Il testo di CRONOLOGIA riempie il campo solo
    # quando il file non ne ha ancora uno proprio.
    note_cronologia = scoperta_esistente.get("note_cronologia") or voce_cronologia.note

    documento = {
        "numero_atomico": numero,
        "simbolo": voce_dataset["symbol"],
        "nome": voce_cronologia.nome,
        "nome_en": voce_dataset["name"],
        "scoperta": {
            "anno": voce_cronologia.anno,
            "anno_stimato": voce_cronologia.anno_stimato,
            "scopritori": voce_cronologia.scopritori,
            # Luogo e controversia sono dati redazionali: mai generati qui,
            # sempre preservati se già scritti a mano su un file esistente.
            "luogo": scoperta_esistente.get("luogo"),
            "epoca": voce_cronologia.epoca,
            "isolamento_anno": voce_cronologia.isolamento_anno,
            "note_cronologia": note_cronologia,
            "controversia": scoperta_esistente.get("controversia"),
        },
        "proprieta": proprieta_dict,
        "approfondimento": esistente.get("approfondimento", False),
    }

    # I contenuti redazionali non vengono mai toccati dallo script.
    for chiave in ("contenuti", "contenuti_estesi", "composti_principali", "fonti"):
        if chiave in esistente:
            documento[chiave] = esistente[chiave]

    return documento


def main() -> int:
    """Genera o aggiorna i file YAML di tutti gli elementi."""
    if not CACHE_DATASET.exists():
        scarica_dataset(CACHE_DATASET)

    per_numero = {voce["number"]: voce for voce in leggi_dataset(CACHE_DATASET)}
    CARTELLA_DATI.mkdir(parents=True, exist_ok=True)

    creati = aggiornati = 0
    for voce_cronologia in sorted(CRONOLOGIA, key=lambda v: v.numero_atomico):
        numero = voce_cronologia.numero_atomico
        voce_dataset = per_numero[numero]
        proprieta = estrai_proprieta(voce_dataset)

        # Il nome del file si ricostruisce dal nome italiano in CRONOLOGIA,
        # non da un file esistente: se il file è stato cancellato, il glob
        # non lo trova e la sola fonte del nome resta voce_cronologia.nome.
        percorso = next(CARTELLA_DATI.glob(f"{numero:03d}-*.yaml"), None)
        esistente = yaml.safe_load(percorso.read_text(encoding="utf-8")) if percorso else {}

        documento = costruisci_documento(
            numero, voce_dataset, voce_cronologia, proprieta, esistente
        )

        destinazione = percorso or CARTELLA_DATI / _nome_file(numero, documento["nome"])
        destinazione.write_text(
            yaml.safe_dump(documento, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        if percorso is None:
            creati += 1
        else:
            aggiornati += 1

    print(f"File creati: {creati}, aggiornati: {aggiornati}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
