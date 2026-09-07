"""Popola i file YAML degli elementi unendo cronologia e proprietà.

Lo script è idempotente e non distruttivo: i blocchi ``contenuti`` già
compilati non vengono mai sovrascritti. Rilanciarlo aggiorna solo i dati di
base.

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
    proprieta_dict = proprieta.model_dump(mode="json")

    # Gli stati di ossidazione sono un dato redazionale (Ruling 23/36): se già
    # compilati a mano su un file esistente, sopravvivono alla rigenerazione
    # del resto del blocco proprieta, che invece viene sempre ricostruito dal
    # dataset esterno.
    stati_ossidazione_esistenti = (esistente.get("proprieta") or {}).get("stati_ossidazione")
    if stati_ossidazione_esistenti:
        proprieta_dict["stati_ossidazione"] = stati_ossidazione_esistenti

    documento = {
        "numero_atomico": numero,
        "simbolo": voce_dataset["symbol"],
        "nome": esistente.get("nome", voce_dataset["name"]),
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
            "note_cronologia": scoperta_esistente.get("note_cronologia") or voce_cronologia.note,
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

        # Il nome italiano va inserito a mano: il dataset riporta solo l'inglese.
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
