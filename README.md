# elements-caos

Un vault [Obsidian](https://obsidian.md) in italiano che racconta i 118 elementi
chimici **nell'ordine in cui l'umanità li ha scoperti**, non in quello del numero
atomico.

È una storia che parte dall'oro raccolto in un letto di fiume quarantamila anni
prima di Cristo e arriva agli atomi sintetizzati in laboratorio, vissuti per
pochi millisecondi e mai visti da occhio umano. Letta in quest'ordine, la tavola
periodica smette di essere una griglia da memorizzare e diventa il racconto di
come abbiamo imparato a riconoscere la materia di cui è fatto il mondo.

## Perché l'ordine cronologico

Il numero atomico è un ordine che nessuno ha percorso. Nella tavola periodica
l'idrogeno viene per primo, ma è il sedicesimo elemento a essere riconosciuto, nel
1671; l'oro, che apre davvero la storia, sta nella sesta riga. Disporre gli
elementi per Z significa raccontare il risultato senza il procedimento.

In ordine di scoperta, invece, emergono cose che la griglia nasconde. Che per
duemila anni «elemento» ha significato *terra, acqua, aria, fuoco*, e che il
primo elemento con una data e un luogo certi — il fosforo, 1669 — arriva da un
alchimista che bolliva urina cercando l'oro. Che ogni volta che nasce uno
strumento nuovo la tavola si riempie a scatti: l'elettrolisi aggiunge sei
elementi in due anni, lo spettroscopio permette di annunciare un elemento senza
averne isolato un granello, il ciclotrone costruisce ciò che in natura non
esiste. E che l'elio è stato riconosciuto nel Sole ventisette anni prima che
sulla Terra.

## Cosa contiene

- **118 note**, una per elemento, in ordine di scoperta: la storia di chi lo ha
  trovato e come, i dati fisico-chimici, gli usi, le curiosità.
- **Quattro figure per nota**: tre diagrammi
  [Mermaid](https://mermaid.js.org/) — la linea del tempo della scoperta, la
  posizione nella tavola periodica, i composti e gli usi — più uno schema SVG
  della struttura atomica a gusci.
- **Un itinerario guidato in 12 tappe**, circa un'ora di lettura, per seguire il
  filo della storia senza leggere tutte le note.
- **Sei note d'epoca** — antichità, alchimia, chimica pneumatica, elettrolisi,
  spettroscopia e radioattività, era nucleare — e **100 schede di scopritori**,
  collegate alle note degli elementi che hanno trovato.
- **136 immagini** di pubblico dominio o CC0, ciascuna con la propria
  attribuzione.

## Come aprirlo

Clona il repository e apri la cartella `vault/` come vault in Obsidian — non la
radice del progetto, che contiene anche il codice.

```bash
git clone https://github.com/gianlucaciarcelluti/elements-caos.git
```

Il punto di partenza è la nota **Cronologia degli elementi**: contiene
l'itinerario guidato e l'elenco completo in ordine di scoperta, raggruppato per
epoca storica.

## Com'è fatto

Il vault non si scrive a mano: si **genera** da un dataset di file YAML, uno per
elemento.

```
data/elements/*.yaml   →   generatore   →   vault/Elementi/*.md
```

La generazione è deterministica: dagli stessi dati esce sempre lo stesso vault,
byte per byte. La conseguenza pratica è **la regola d'oro del progetto**:

> **Le note in `vault/` non vanno modificate a mano.** Una correzione si applica
> al file YAML corrispondente e il vault si rigenera.

È una scelta che tiene insieme 118 note senza che divergano fra loro, che
permette di correggere il formato una volta sola invece che centodiciotto, e che
l'integrazione continua fa rispettare: rigenera il vault a ogni push e rifiuta
ogni differenza che non derivi dai dati.

## Come si rigenera

Serve [uv](https://docs.astral.sh/uv/) e Python 3.12.

```bash
uv sync
uv run elements-caos genera --dati data --vault vault
uv run elements-caos valida --dati data --vault vault
```

Il comando `valida` verifica l'integrità del vault: collegamenti interni, budget
di lettura delle note, catena cronologica senza buchi né duplicati, licenze delle
immagini.

Se vuoi contribuire, il documento da leggere è [CONTRIBUTING.md](CONTRIBUTING.md).

## Licenze

- **Contenuti** (`data/`, `vault/`, documentazione): [CC BY-SA 4.0](LICENSE)
- **Codice** (`src/`, `tests/`, `scripts/`): [MIT](LICENSE-CODE)
- **Immagini**: solo pubblico dominio e CC0, con attribuzione in ogni file

La licenza dei contenuti non è una scelta ma un obbligo: il progetto attinge a
[Periodic-Table-JSON](https://github.com/Bowserinator/Periodic-Table-JSON)
(CC BY-SA 3.0) e a [Wikipedia](https://en.wikipedia.org/wiki/Timeline_of_chemical_element_discoveries)
(CC BY-SA 4.0), entrambe licenze *share-alike*. Le attribuzioni complete sono
nel file [LICENSE](LICENSE); i crediti delle immagini stanno nella nota
**Attribuzioni** del vault.

Il codice resta invece con licenza MIT, così chiunque voglia costruire un vault
analogo su un altro dominio può partire da qui senza vincoli.
