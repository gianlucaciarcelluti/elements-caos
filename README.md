# elements-caos

Un vault [Obsidian](https://obsidian.md) in italiano che racconta i 118 elementi
chimici **nell'ordine in cui l'umanità li ha scoperti**, non in quello del numero
atomico.

È una storia che parte dal rame raccolto in una grotta novemila anni prima di
Cristo e arriva agli atomi sintetizzati in laboratorio, vissuti per pochi
millisecondi e mai visti da occhio umano. Letta in quest'ordine, la tavola
periodica smette di essere una griglia da memorizzare e diventa il racconto di
come abbiamo imparato a riconoscere la materia di cui è fatto il mondo.

> **Stato: in costruzione.** L'infrastruttura è completa e funzionante; i
> contenuti sono in corso di scrittura. Al momento sono presenti quattro
> elementi pilota su 118. Questo README verrà ampliato quando il vault sarà
> popolato.

## Com'è fatto

Il vault non si scrive a mano: si **genera** da un dataset di file YAML, uno per
elemento. Ogni nota contiene la storia della scoperta, i dati fisico-chimici,
quattro diagrammi [Mermaid](https://mermaid.js.org/) e i collegamenti agli
elementi precedente e successivo *nell'ordine cronologico*.

```
data/elements/*.yaml   →   generatore   →   vault/Elementi/*.md
```

La conseguenza pratica: **le note non vanno modificate a mano**. Una correzione
si applica al file YAML corrispondente e il vault si rigenera. È una scelta che
tiene insieme 118 note senza che divergano fra loro, e che permette di
correggere il formato una volta sola invece che centodiciotto.

## Come aprirlo

Clona il repository e apri la cartella `vault/` come vault in Obsidian — non la
radice del progetto, che contiene anche il codice.

```bash
git clone https://github.com/gianlucaciarcelluti/elements-caos.git
```

Il punto di partenza è la nota **Cronologia degli elementi**: contiene l'elenco
completo in ordine di scoperta, raggruppato per epoca storica, e un itinerario
di lettura guidato.

## Come si rigenera

Serve [uv](https://docs.astral.sh/uv/) e Python 3.12.

```bash
uv sync
uv run elements-caos genera --dati data --vault vault
uv run elements-caos valida --dati data --vault vault
```

Il comando `valida` verifica l'integrità del vault: collegamenti interni, budget
di lettura delle note, catena cronologica senza buchi, licenze delle immagini.

## Licenze

- **Contenuti** (`data/`, `vault/`, documentazione): [CC BY-SA 4.0](LICENSE)
- **Codice** (`src/`, `tests/`, `scripts/`): [MIT](LICENSE-CODE)
- **Immagini**: solo pubblico dominio e CC0, con attribuzione in ogni file

La licenza dei contenuti non è una scelta ma un obbligo: il progetto attinge a
[Periodic-Table-JSON](https://github.com/Bowserinator/Periodic-Table-JSON)
(CC BY-SA 3.0) e a [Wikipedia](https://en.wikipedia.org/wiki/Timeline_of_chemical_element_discoveries)
(CC BY-SA 4.0), entrambe licenze *share-alike*. Le attribuzioni complete sono
nel file [LICENSE](LICENSE).

Il codice resta invece con licenza MIT, così chiunque voglia costruire un vault
analogo su un altro dominio può partire da qui senza vincoli.
