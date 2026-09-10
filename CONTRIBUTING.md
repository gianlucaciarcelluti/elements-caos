# Contribuire a elements-caos

Grazie per l'interesse. Questo documento spiega come si corregge e come si
scrive per questo progetto. Prima di tutto il resto, però, c'è una regola che
determina il modo in cui si tocca qualsiasi cosa.

> ## La regola d'oro: si modificano gli YAML in `data/`, mai le note in `vault/`.
>
> Le note sono **generate**. L'integrazione continua rigenera il vault a ogni
> push e rifiuta ogni modifica che non derivi dai dati: una correzione applicata
> direttamente a un file in `vault/` non verrà accettata, e andrebbe comunque
> persa alla prima rigenerazione.

La conseguenza pratica: individuata la frase da correggere in una nota, si apre
`data/elements/<Z>-<nome>.yaml`, si corregge lì, si rigenera e si committa il
risultato.

```bash
uv sync
uv run elements-caos genera --dati data --vault vault
uv run elements-caos valida --dati data --vault vault
uv run pytest -q
```

Il commit deve includere **sia** lo YAML modificato **sia** le note rigenerate,
altrimenti il controllo di allineamento del vault fallisce.

## Segnalare un errore senza correggerlo

Se non vuoi aprire una pull request va benissimo: apri una issue con il template
adatto e ce ne occupiamo noi.

- **Errore storico** — la nota racconta un fatto in modo scorretto, attribuisce
  una scoperta alla persona sbagliata, sbaglia una data o un luogo.
- **Dato errato** — un valore fisico-chimico non torna: massa atomica, punto di
  fusione, configurazione elettronica, stati di ossidazione.
- **Proponi un approfondimento** — un elemento la cui vicenda meriterebbe più
  spazio di quello che ha.

In tutti e tre i casi **serve una fonte**. Una segnalazione senza fonte non è
verificabile, e questo progetto ha imparato a sue spese che le affermazioni non
verificate sopravvivono a lungo prima che qualcuno se ne accorga.

## Proporre una correzione

1. Fai un fork e crea un branch.
2. Modifica lo YAML dell'elemento in `data/elements/`.
3. Rigenera il vault e lancia i controlli (i comandi qui sopra).
4. Apri una pull request che dica **cosa** cambia e **su quale fonte** si basa,
   con il link.

## Come si scrive un beat

I contenuti di ogni elemento non sono un testo continuo: sono una sequenza di
**beat**, unità narrative da una sola idea ciascuna. Il generatore li concatena
in prosa scorrevole, quindi chi legge la nota non percepisce alcuna
frammentazione, ma la segmentazione resta nei dati.

```yaml
- id: alchimista
  sezione: storia
  testo: >-
    Hennig Brand è un mercante di vetro caduto in disgrazia, ad Amburgo, che
    nella seconda metà del Seicento decide di reinventarsi alchimista.
  visual: Ritratto immaginario di Brand nel suo laboratorio ad Amburgo
  attendibilita: documentato
```

Le regole che contano:

- **Una sola idea per beat.** Se nel testo compare un «e inoltre», quasi sempre
  sono due beat.
- **`sezione`** vale `incipit`, `storia`, `caratteristiche`, `usi` o
  `curiosita`, e determina sotto quale titolo il beat finisce nella nota.
- **`id` univoco** all'interno dell'elemento.
- Ogni elemento ha **fra 12 e 18 beat**. Non è un limite imposto dal codice: è
  quello che serve per stare dentro il budget di parole raccontando la storia.
- Il beat dev'essere **leggibile da solo**: niente «come si è detto», niente
  «quest'ultimo» riferito al beat precedente.

### I quattro gradi di attendibilità

Il campo `attendibilita` distingue i fatti documentati dagli aneddoti
tramandati, perché un vault pubblico non deve presentare come certo ciò che è
tradizione.

| valore | quando si usa |
|---|---|
| `documentato` | il fatto è attestato da fonti; è il default |
| `tradizionale` | è sapere tramandato, non verificabile alla fonte |
| `leggendario` | è un aneddoto che circola e che non reggerebbe una verifica |
| `discusso` | il beat **esamina** una rivendicazione invece di riportarla |

Due vincoli:

- **Un beat non mescola gradi diversi.** Se una frase è documentata e la
  successiva è leggendaria, sono due beat.
- `discusso` è l'unico grado non documentato che non riceve una formula di
  cautela in prosa: la cautela è già nel testo del beat, e premettergli «Per
  tradizione:» lo capovolgerebbe.

## Il budget di parole

Ogni nota base sta fra **800 e 1300 parole**, misurate sui beat più l'hook. Il
comando `valida` lo verifica e fallisce fuori dall'intervallo.

Non è una formalità di stile: è quello che tiene la nota nel formato «una
lettura, una sera», ed è la ragione per cui gli elementi che meritano di più
ottengono un approfondimento separato invece di una nota lunga il doppio.

## Il requisito delle fonti

**Ogni affermazione dev'essere sostenuta dalla fonte che linki.** Non «una fonte
che parla dell'argomento»: la fonte che sostiene *quella* frase.

```yaml
fonti:
- url: https://en.wikipedia.org/wiki/Hennig_Brand
  titolo: Hennig Brand
  consultata: 2026-09-05
```

Tre cose che in questo progetto sono costate correzioni, e che vale la pena
sapere prima di scrivere:

- **Il riassunto di una fonte non è la fonte.** Le sintesi automatiche sbagliano
  attribuzioni e cifre in modo plausibile. Apri la pagina e cerca la frase.
- **I superlativi sono la forma in cui l'errore si nasconde meglio.** Prima di
  scrivere «l'unico», «il primo», «il più»: conta. Diverse affermazioni di
  questo tipo sono state scritte, sembravano vere e non lo erano.
- **Quello che non si sa si lascia a `null`.** Diverse anagrafiche di
  scopritori sono ignote: il modello lo prevede, e inventare una data di nascita
  plausibile è peggio che non averla.

Un controllo schedulato verifica settimanalmente che gli URL delle fonti siano
ancora raggiungibili, e apre un rapporto senza bloccare nulla.

## I campi `hook`, `visual` e `pronuncia`

Tre campi non compaiono nella nota generata, e per questo capita che chi
contribuisce li salti. **Vanno compilati comunque**: servono a possibili riusi
del vault in altri formati, e recuperarli a posteriori su 118 elementi sarebbe
un lavoro enorme.

- **`hook`** — l'apertura che trattiene nei primi secondi, una frase. Nasce
  naturale mentre scrivi la storia; inventarla a freddo mesi dopo è
  difficilissimo.
- **`visual`** (per beat) — cosa si mostrerebbe accanto a questo passaggio. Chi
  scrive ha già in mente l'immagine: basta scriverla.
- **`pronuncia`** (IPA) — per i nomi propri stranieri. Scheele, Berzelius,
  Klaproth, Ytterby: chiunque legga ad alta voce, umano o sintetico, li sbaglia.

## Immagini

Solo **pubblico dominio o CC0**. Ogni immagine in `vault/Immagini/` ha accanto
un file `<nome>.license.yaml` con autore, fonte e licenza, e `valida` fallisce
se manca. Un'immagine CC BY o CC BY-NC, per quanto adatta, non entra.

## Prima di aprire la pull request

```bash
uv run pytest -q
uv run elements-caos genera --dati data --vault vault
uv run elements-caos valida --dati data --vault vault
uv run ruff check src tests && uv run ruff format --check src tests
uv run mypy src
git status --porcelain -- vault    # dev'essere vuoto dopo il commit
```

Il codice e la prosa dei commenti sono in **italiano**, come tutto il resto del
progetto.

## Licenze dei contributi

Aprendo una pull request accetti che il tuo contributo sia rilasciato con le
licenze del progetto: [CC BY-SA 4.0](LICENSE) per i contenuti e
[MIT](LICENSE-CODE) per il codice.
