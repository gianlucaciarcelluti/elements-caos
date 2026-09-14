# Onboarding

Guida di ingresso al progetto per chi ci lavora la prima volta. Serve a capire
**com'è fatto** `elements-caos` e **dove mettere le mani**: la mappa del codice,
il modello dei dati, la pipeline di generazione e i controlli automatici.

Non sostituisce gli altri due documenti, li presuppone:

| documento | risponde a |
|---|---|
| [README.md](../README.md) | cos'è il progetto e perché l'ordine è cronologico |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | **come si scrive** un contenuto: beat, fonti, budget di parole |
| questo documento | **come è costruito** e come ci si muove dentro |

Percorso consigliato: leggi il README (10 minuti), poi questa guida fino a
«Primo contributo», poi CONTRIBUTING quando devi scrivere davvero.

---

## 1. L'idea da cui discende tutto il resto

Il vault Obsidian e il sito **non si scrivono**: si **generano** da un dataset
di file YAML, uno per elemento.

```
                         ┌─►  vault/**/*.md    (vault Obsidian)
data/elements/*.yaml  ───┤
data/*.yaml              └─►  public/**/*.html (sito GitHub Pages)
```

La generazione è **deterministica**: dagli stessi dati esce sempre lo stesso
output, byte per byte. Da qui la regola d'oro:

> **Le note in `vault/` non si modificano a mano.** Una correzione si applica
> allo YAML in `data/` e il vault si rigenera.

Non è una convenzione sulla fiducia: il job `vault` della CI rigenera tutto e
fallisce se `git status --porcelain -- vault` non è vuoto. Una modifica manuale
a una nota viene rifiutata dalla pipeline.

Vault e sito sono **due emettitori indipendenti** che leggono lo stesso dataset.
Il vault ha wikilink e grafo; il sito ha la tavola periodica animata, la linea
del tempo e l'avanzamento di lettura. Cambiare il sito non muove il vault di un
byte, e viceversa.

---

## 2. Ambiente in cinque minuti

Servono [uv](https://docs.astral.sh/uv/) e Python 3.12 (fissato in
`.python-version`).

```bash
git clone https://github.com/gianlucaciarcelluti/elements-caos.git
cd elements-caos
uv sync                                                  # crea .venv e installa tutto
uv run pytest -q                                         # la suite deve passare
uv run elements-caos genera --dati data --vault vault    # rigenera il vault
git status --porcelain -- vault                          # DEVE essere vuoto
```

L'ultima riga è il test di sanità dell'installazione: se il vault appena
rigenerato è identico a quello committato, l'ambiente è a posto.

Per il sito serve anche Node 22 (solo per i controlli, non per la generazione):

```bash
uv run elements-caos sito --dati data --uscita public
python3 -m http.server --directory public                # http://localhost:8000
```

**Per aprire il vault in Obsidian**: apri la cartella `vault/`, non la radice
del progetto (che contiene anche il codice). Punto di partenza: la nota
*Cronologia degli elementi*.

---

## 3. Mappa del repository

```
data/                     ← LA SORGENTE DI VERITÀ: qui si modifica
  elements/*.yaml           118 file, uno per elemento (001-idrogeno.yaml …)
  epoche.yaml               6 epoche storiche
  scopritori.yaml           100 schede di scopritori
  itinerario.yaml           le 12 tappe del percorso guidato
  images/                   immagini + <nome>.license.yaml affiancato

src/elements_caos/        ← IL GENERATORE (codice Python)
  models.py                 modelli Pydantic: lo schema dei dati
  caricamento.py            legge gli YAML → oggetti, ordina per scoperta
  validazione.py            i controlli d'integrità del comando `valida`
  cli.py                    i sottocomandi: genera / sito / valida
  ingest/                   acquisizione dati esterni (cronologia, proprietà, ritratti)
  render/                   emettitore VAULT (note .md, diagrammi, SVG atomico)
  sito/                     emettitore SITO (pagine .html, tavola, itinerario)

vault/                    ← IL PRODOTTO: è ciò che la gente legge.
                            Generato: non si modifica a mano (ma è committato)
public/                   ← il sito, stesso prodotto in HTML.
                            Generato e ignorato da git: si ricostruisce
tests/                    ← 26 file di test, uno per modulo
scripts/                  ← utilità: verifica fonti, mermaid, sito, popolamento
docs/fonti/               ← trascrizioni delle fonti usate per costruire il dataset
.github/workflows/        ← i tre workflow di CI
```

Due cartelle da tenere a mente: `vault/` **è versionato** benché generato
(perché è il prodotto che si consulta in Obsidian), `public/` **non lo è**
(si ricostruisce a ogni pubblicazione).

---

## 4. Il modello dei dati

Lo schema è definito con Pydantic in `src/elements_caos/models.py`: è il posto
dove guardare quando un campo non è chiaro, perché i vincoli sono espressi nel
codice e validati al caricamento.

### Anatomia di un elemento

`data/elements/<Z>-<nome>.yaml` — il nome del file porta il numero atomico a tre
cifre, ma **l'ordine di lettura del vault è quello di scoperta**, non quello di Z.

| blocco | contenuto |
|---|---|
| identità | `numero_atomico`, `simbolo`, `nome`, `nome_en` |
| `scoperta` | `anno`, `anno_stimato`, `scopritori` (id), `luogo`, `epoca`, `isolamento_anno`, `note_cronologia`, `controversia` |
| `proprieta` | gruppo, periodo, blocco, categoria, massa, configurazione elettronica, `gusci`, punti di fusione/ebollizione, densità, stati di ossidazione |
| `contenuti` | `hook` + `beats` + `pronuncia` → la **nota base** |
| `contenuti_estesi` | idem, ma per l'**approfondimento** (solo se `approfondimento: true`) |
| `composti_principali` | nome, formula, usi |
| `fonti` | url, titolo, data di consultazione |

### I beat

Il testo non è prosa continua: è una sequenza di **beat**, unità narrative da
una sola idea. Il generatore li concatena in prosa scorrevole, ma la
segmentazione resta nei dati e permette di riusare il vault in altri formati.

Ogni beat ha `id` (univoco nell'elemento), `sezione`, `testo`, `visual` e
`attendibilita` (`documentato` / `tradizionale` / `leggendario` / `discusso`).

- **Nota base**: sezioni `incipit`, `storia`, `caratteristiche`, `usi`, `curiosita`
- **Approfondimento**: sezioni `contesto`, `vicenda`, `impatto`, `controversie`, `eredita`

Le regole di scrittura (una idea per beat, leggibilità isolata, gradi di
attendibilità che non si mescolano) sono in
[CONTRIBUTING.md](../CONTRIBUTING.md#come-si-scrive-un-beat).

### I vincoli che la validazione fa rispettare

Sono costanti in `src/elements_caos/validazione.py`, e `valida` fallisce fuori
da questi limiti:

| vincolo | nota base | approfondimento |
|---|---|---|
| parole (beat + hook) | 800 – 1300 | 7000 – 11000 |
| fonti minime | 2 | 4 |

Il budget di parole non è un capriccio del linter: tiene la nota nel formato
«una lettura, una sera», ed è la ragione per cui gli elementi che meritano più
spazio ottengono un approfondimento separato invece di una nota lunga il doppio
([CONTRIBUTING.md](../CONTRIBUTING.md#il-budget-di-parole)).

A questi si aggiunge una convenzione redazionale **non imposta dal codice**: una
nota base ha fra 12 e 18 beat. Non è un controllo automatico, è ciò che serve
per stare dentro il budget di parole raccontando la storia.

Altri controlli di `valida`: wikilink interni risolti, catena cronologica senza
buchi né duplicati, licenze delle immagini presenti e ammesse (solo pubblico
dominio o CC0), coerenza dei dati redazionali.

---

## 5. La pipeline, passo per passo

```
data/*.yaml
    │
    ├─ caricamento.py      → valida lo schema Pydantic, risolve gli id,
    │                        ordina gli elementi per anno di scoperta
    │
    ├─ render/*            → vault/Elementi/, Approfondimenti/, Epoche/,
    │   (emettitore vault)   Scopritori/, Immagini/ + note di navigazione
    │                        (Cronologia, Tavola periodica, Attribuzioni)
    │
    └─ sito/*              → public/**.html + sitemap, feed RSS, 404,
        (emettitore sito)    reindirizzamenti
```

I tre comandi che contano:

```bash
uv run elements-caos genera --dati data --vault vault    # emette il vault
uv run elements-caos sito   --dati data --uscita public  # emette il sito
uv run elements-caos valida --dati data --vault vault    # controlla l'integrità
```

Il generatore **possiede** i file che scrive: `genera` rimuove anche le note
orfane, quelle che nessun dato produce più (utile quando si rinomina un
elemento). Le sottocartelle create a mano vengono sempre ignorate.

Ogni elemento ha quattro figure generate: tre diagrammi Mermaid (linea del
tempo, posizione nella tavola, composti e usi) e uno schema SVG della struttura
a gusci, prodotto da `render/atomo_svg.py` a partire dal campo `gusci`.

---

## 6. I controlli automatici

Tre workflow in `.github/workflows/`:

**`validate.yml`** — su ogni push a `main` e su ogni PR. Quattro job:

| job | cosa fa |
|---|---|
| `qualita` | `pytest -v`, `ruff check`, `ruff format --check`, `mypy src` |
| `vault` | rigenera il vault e **fallisce se differisce** da quello committato, poi `valida` |
| `diagrammi` | compila tutti i diagrammi Mermaid (`scripts/verifica_mermaid.sh`) |
| `sito` | costruisce il sito e lo apre in un browser headless |

**`pages.yml`** — pubblica su GitHub Pages a ogni push su `main`. Controlla che
siano state costruite almeno 229 pagine, per non pubblicare un sito monco.

**`fonti.yml`** — settimanale (lunedì 06:00 UTC). Verifica che gli URL delle
fonti siano raggiungibili. **Deliberatamente non bloccante**: un server terzo
giù non deve fermare la pipeline.

### I controlli del sito

`scripts/verifica_sito.mjs` apre otto tipi di pagina a 390 e 1280 px e fallisce
se: un elemento esce dal viewport, una pagina supera l'altezza dichiarata, pesa
più di 250 KB senza immagini, la console riporta un errore, o un comando è più
piccolo di quanto richiede WCAG 2.5.8. In locale serve
`npm install --no-save puppeteer@23.11.1` (versione fissata di proposito).

---

## 7. Cosa rende buona una nota

Fin qui si è parlato della macchina. Ma il prodotto di questo progetto non è la
pipeline: sono 118 racconti che qualcuno deve avere voglia di leggere. Vale la
pena sapere, prima di scrivere la prima riga, qual è il metro di giudizio.

**Una nota è riuscita quando fa capire perché quella scoperta è avvenuta proprio
allora.** Non «nel 1868 fu scoperto l'elio», ma cosa rendeva possibile nel 1868
riconoscere un elemento guardando un'eclissi — e perché prima non lo era. È
questa la ragione per cui il vault è ordinato per scoperta e non per numero
atomico: l'ordine cronologico rende visibile che ogni strumento nuovo apre una
stagione di scoperte, e la griglia per Z lo nasconde.

**E quando si legge senza sapere di chimica**, restando esatta per chi la sa. Il
lettore di questo progetto non ha studiato chimica e non deve averlo fatto: un
termine tecnico entra solo se serve e si spiega nella frase stessa, la scena
viene prima della definizione, le cifre hanno un termine di paragone.

Le regole di scrittura stanno in
[CONTRIBUTING.md](../CONTRIBUTING.md#la-voce-si-scrive-per-chi-non-sa-di-chimica);
qui basta sapere che esistono e che sono la parte difficile del lavoro. Il resto
— YAML, comandi, CI — si impara in un pomeriggio.

---

## 8. Primo contributo

### Correggere un dato o una frase

1. Trova l'elemento: `data/elements/<Z>-<nome>.yaml`.
2. Correggi **lì**, mai nella nota in `vault/`.
3. Se cambi un fatto, aggiorna o aggiungi la `fonte` che lo sostiene.
4. Rigenera e verifica:

```bash
uv run elements-caos genera --dati data --vault vault
uv run elements-caos valida --dati data --vault vault
uv run pytest -q
```

5. Committa **sia** lo YAML **sia** le note rigenerate — altrimenti il job
   `vault` fallisce.

### Prima di aprire la pull request

```bash
uv run pytest -q
uv run elements-caos genera --dati data --vault vault
uv run elements-caos valida --dati data --vault vault
uv run ruff check src tests && uv run ruff format --check src tests
uv run mypy src
git status --porcelain -- vault    # dev'essere vuoto DOPO il commit
```

### Lavorare sul codice

- **Test prima** (TDD): la suite ha un file per modulo in `tests/`, con dati di
  prova in `tests/dati_prova/`.
- `mypy` gira in modalità **strict**: le annotazioni di tipo sono obbligatorie.
- `ruff` con `line-length = 100`; `docs/` è escluso dal lint (contiene blocchi
  di codice illustrativi, non sorgenti).
- I test marcati `integration` scaricano dataset reali e **sono esclusi di
  default**; per eseguirli: `uv run pytest -m integration`.

---

## 9. Convenzioni del progetto

**Lingua.** Tutto è in italiano: contenuti, nomi di funzioni e variabili,
commenti, messaggi di commit, documentazione. Anche le eccezioni seguono la
convenzione (`ErroreCaricamento`, `ErroreIngest` — con *prefisso* `Errore`, per
cui la regola ruff `N818` è disattivata di proposito).

**Nessuna pagina è scritta a mano**, nemmeno la home del sito: modificarne una
significa modificare il suo template in `src/elements_caos/sito/` o i dati da
cui nasce.

**Le immagini** sono solo pubblico dominio o CC0, ciascuna con il file
`<nome>.license.yaml` affiancato **in `data/images/`** — è lì che `valida`
controlla, non nella copia generata in `vault/Immagini/`. Un'immagine CC BY o
CC BY-NC non entra, per quanto adatta.

**Le licenze** sono doppie: contenuti (`data/`, `vault/`, docs) in
[CC BY-SA 4.0](../LICENSE) — obbligata, perché il progetto attinge a fonti
share-alike — e codice (`src/`, `tests/`, `scripts/`) in
[MIT](../LICENSE-CODE).

**Avvertenza sull'IA.** Il progetto è stato realizzato con assistenza di sistemi
di IA; ogni affermazione è verificata sulle fonti citate, ma l'avvertenza
compare in fondo a ogni pagina ed è una scelta di trasparenza, non una
formalità.

---

## 10. Errori tipici del primo giorno

| sintomo | causa | rimedio |
|---|---|---|
| la CI fallisce su «Il vault committato non corrisponde ai dati» | hai modificato una nota a mano, o non hai committato le note rigenerate | correggi lo YAML, `genera`, committa anche `vault/` |
| `valida` fallisce sul budget di parole | la nota è fuori da 800–1300 parole | taglia ciò che non serve al racconto, oppure sposta il materiale in un approfondimento |
| `valida` fallisce su un wikilink | il link punta a una nota che non esiste | controlla il nome esatto della nota di destinazione |
| `valida` fallisce sulle licenze immagini | manca il `<nome>.license.yaml` in `data/images/` | aggiungilo **lì** (non in `vault/Immagini/`), oppure rimuovi l'immagine |
| il job `sito` fallisce in locale | manca puppeteer | `npm install --no-save puppeteer@23.11.1` |
| ho aperto Obsidian e vedo il codice | hai aperto la radice | apri `vault/` come vault |
| ho rinominato un elemento e resta una nota fantasma | — | `genera` rimuove da solo le orfane: rigenera e ricommitta |

I guasti qui sopra li intercetta la CI. Questi invece **non li prende nessun
controllo automatico**, ed è per questo che vale la pena conoscerli in anticipo:

| errore editoriale | perché succede | rimedio |
|---|---|---|
| ho riassunto la fonte invece di leggerla | le sintesi automatiche sbagliano attribuzioni e cifre in modo plausibile | apri la pagina e cerca la frase che sostiene *quella* affermazione |
| ho scritto «il primo», «l'unico», «il più» | i superlativi sono la forma in cui l'errore si nasconde meglio | conta prima di scriverlo; diverse affermazioni di questo tipo sembravano vere e non lo erano |
| non trovavo la data di nascita e ne ho messa una plausibile | il modello ammette `null`, ma a freddo sembra un buco da riempire | lascia `null`: diverse anagrafiche di scopritori sono ignote, e inventarle è peggio che non averle |

Il dettaglio è in
[CONTRIBUTING.md](../CONTRIBUTING.md#il-requisito-delle-fonti).

---

## 11. Dove chiedere

- **Segnalare senza correggere**: apri una issue con uno dei tre template
  (*errore storico*, *dato errato*, *proponi un approfondimento*). In tutti e
  tre i casi **serve una fonte**: una segnalazione non verificabile non è
  utilizzabile.
- **Capire una scelta di dataset**: `docs/fonti/` contiene le trascrizioni delle
  fonti usate per costruirlo — con le loro avvertenze, incluse quelle sugli
  errori noti.
- **Capire una scelta di schema**: `src/elements_caos/models.py`, dove i vincoli
  sono espressi nel codice e i commenti spiegano il perché.
