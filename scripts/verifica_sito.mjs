/* Verifiche automatiche del sito costruito: layout, peso, console e
 * dimensione dei punti di contatto.
 *
 * Uso:
 *   node scripts/verifica_sito.mjs <cartella-del-sito>
 *
 * Serve il sito da un server locale invece di aprirlo con file://: la ricerca
 * scarica l'indice con fetch, che da file:// verrebbe bloccato, e il peso
 * delle pagine si misura solo su richieste vere.
 *
 * DUE ERRORI GIÀ COMMESSI, che questo script non deve ripetere:
 *
 * 1. La larghezza NON si imposta con --window-size. Chrome headless su Linux
 *    ha una larghezza minima di finestra intorno ai 500 px: chiedendo 390 si
 *    ottiene una pagina renderizzata a 500 e una foto ritagliata, che sembra
 *    un sito rotto. Serve setViewport con isMobile.
 *
 * 2. Un elemento dentro un contenitore che scorre NON sfora, anche se
 *    getBoundingClientRect dice il contrario: il rettangolo riporta la
 *    posizione non ritagliata. Senza saltare quegli elementi, la tavola
 *    periodica — che scorre di proposito — darebbe un falso allarme a ogni
 *    esecuzione.
 */

import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { extname, join, normalize } from "node:path";
import puppeteer from "puppeteer";

const CARTELLA = process.argv[2] || "public";

// Il sito si serve sotto lo stesso prefisso che avrà in produzione: su GitHub
// Pages il progetto sta in /elements-caos/, e la 404 usa indirizzi assoluti che
// da un server montato sulla radice punterebbero a vuoto.
const PREFISSO = "/elements-caos";

// Le pagine campione: una per tipo. Verificarle tutte e 230 costerebbe minuti
// senza aggiungere nulla, perché ogni tipo condivide il proprio template.
const PAGINE = [
  { percorso: "/index.html", nome: "home", altezzaMax: 3000 },
  { percorso: "/cronologia-degli-elementi.html", nome: "cronologia", altezzaMax: 5000 },
  { percorso: "/tavola-periodica.html", nome: "tavola", altezzaMax: 2600 },
  { percorso: "/itinerario.html", nome: "itinerario", altezzaMax: 5400 },
  { percorso: "/elementi/oganesson.html", nome: "elemento", altezzaMax: 8000 },
  { percorso: "/scopritori/hennig-brand.html", nome: "scopritore", altezzaMax: 2600 },
  { percorso: "/epoche/era-nucleare.html", nome: "epoca", altezzaMax: 3400 },
  { percorso: "/404.html", nome: "404", altezzaMax: 2400 },
];

const LARGHEZZE = [
  { nome: "telefono", width: 390, height: 844, isMobile: true },
  { nome: "scrivania", width: 1280, height: 900, isMobile: false },
];

// Peso massimo di una pagina, immagini escluse. Le immagini hanno un budget a
// parte perché un ritratto è contenuto, non impalcatura.
const PESO_MASSIMO = 250 * 1024;

// Dimensione minima di un punto di contatto, secondo WCAG 2.5.8 livello AA.
//
// Non 44 px, che è il livello AAA: applicato a tutto darebbe caselle della
// tavola periodica grandi il doppio del necessario e collegamenti in linea
// trasformati in pulsanti. I comandi veri — pulsanti, scorrevoli, pastiglie —
// stanno comunque a 44, ed è una scelta di progetto: qui si fissa il minimo
// sotto il quale è un difetto.
const CONTATTO_MINIMO = 24;

const TIPI = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".xml": "application/xml",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".png": "image/png",
};

function avviaServer(radice) {
  const server = createServer(async (richiesta, risposta) => {
    let percorso = decodeURIComponent(new URL(richiesta.url, "http://x").pathname);
    if (percorso.startsWith(PREFISSO)) {
      percorso = percorso.slice(PREFISSO.length) || "/";
    }
    // normalize() impedisce che un ".." nella richiesta esca dalla cartella.
    const file = join(radice, normalize(percorso).replace(/^(\.\.[/\\])+/, ""));
    if (!existsSync(file) || file.endsWith("/")) {
      risposta.writeHead(404).end("non trovato");
      return;
    }
    try {
      const contenuto = await readFile(file);
      risposta.writeHead(200, { "content-type": TIPI[extname(file)] || "application/octet-stream" });
      risposta.end(contenuto);
    } catch (errore) {
      risposta.writeHead(500).end(String(errore));
    }
  });
  return new Promise((risolvi) => {
    server.listen(0, "127.0.0.1", () => risolvi({ server, porta: server.address().port }));
  });
}

async function misura(pagina, url, larghezza) {
  const errori = [];
  const pesi = { totale: 0, immagini: 0 };

  const suConsole = (messaggio) => {
    if (messaggio.type() === "error") {
      errori.push(messaggio.text());
    }
  };
  // Un'eccezione non catturata NON passa da "console": arriva su "pageerror".
  // Senza questo ascoltatore uno script che si rompe a metà passerebbe il
  // controllo in silenzio, ed è esattamente il difetto che si vuole prendere.
  const suEccezione = (errore) => {
    errori.push("eccezione non catturata: " + errore.message);
  };
  const suRisposta = async (risposta) => {
    try {
      const corpo = await risposta.buffer();
      const tipo = risposta.headers()["content-type"] || "";
      if (tipo.startsWith("image/") || tipo.startsWith("font/")) {
        pesi.immagini += corpo.length;
      } else {
        pesi.totale += corpo.length;
      }
    } catch {
      /* Risposta senza corpo leggibile: non pesa. */
    }
  };

  pagina.on("console", suConsole);
  pagina.on("pageerror", suEccezione);
  pagina.on("response", suRisposta);

  await pagina.setViewport(larghezza);
  await pagina.goto(url, { waitUntil: "networkidle0", timeout: 60000 });
  await new Promise((r) => setTimeout(r, 400));

  const risultato = await pagina.evaluate((contattoMinimo) => {
    const vw = document.documentElement.clientWidth;

    // Un antenato che scorre ritaglia i suoi discendenti: quegli elementi non
    // sfondano la pagina, anche se il loro rettangolo dice il contrario.
    const dentroUnContenitoreCheScorre = (elemento) => {
      let corrente = elemento.parentElement;
      while (corrente && corrente !== document.body) {
        const stile = getComputedStyle(corrente);
        if (stile.overflowX === "auto" || stile.overflowX === "scroll" || stile.overflowX === "hidden") {
          return true;
        }
        corrente = corrente.parentElement;
      }
      return false;
    };

    const sforano = [];
    const contattiPiccoli = [];
    document.querySelectorAll("*").forEach((elemento) => {
      const r = elemento.getBoundingClientRect();
      if (r.width > 0 && r.right > vw + 1 && !dentroUnContenitoreCheScorre(elemento)) {
        sforano.push(elemento.tagName + (elemento.className ? "." + String(elemento.className).trim().split(/\s+/)[0] : ""));
      }
    });

    document.querySelectorAll("a, button, input, [role=button]").forEach((elemento) => {
      // Un collegamento dentro una frase o un titolo non è un bersaglio da
      // pollice: è testo. La regola sulla dimensione riguarda i comandi.
      // Un collegamento dentro una frase, un titolo o una voce bibliografica
      // è testo, non un comando: la fonte di una nota si legge, e attorno ha
      // altro testo ("consultata il ..."). Ingrandirla non la renderebbe più
      // usabile, la renderebbe un pulsante in mezzo a una citazione.
      if (elemento.closest("p, h1, h2, h3, figcaption, .elemento__fonti li, .attribuzione")) {
        return;
      }
      // Una casella di spunta dentro un'etichetta si preme premendo
      // l'etichetta: il bersaglio vero è quella, non il quadratino.
      const etichetta = elemento.closest("label");
      const bersaglio = etichetta || elemento;
      const r = bersaglio.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) {
        return;
      }
      if (r.height < contattoMinimo || r.width < contattoMinimo) {
        contattiPiccoli.push(
          (elemento.id || elemento.className || elemento.tagName) +
            " " + Math.round(r.width) + "×" + Math.round(r.height) + "px"
        );
      }
    });

    return {
      larghezzaDocumento: document.documentElement.scrollWidth,
      viewport: vw,
      altezza: document.body.scrollHeight,
      sforano: sforano.slice(0, 6),
      contattiPiccoli: contattiPiccoli.slice(0, 6),
    };
  }, CONTATTO_MINIMO);

  pagina.off("console", suConsole);
  pagina.off("pageerror", suEccezione);
  pagina.off("response", suRisposta);

  return { ...risultato, errori, pesi };
}

const { server, porta } = await avviaServer(CARTELLA);
const browser = await puppeteer.launch({ args: ["--no-sandbox", "--disable-dev-shm-usage"] });
const problemi = [];

for (const voce of PAGINE) {
  for (const larghezza of LARGHEZZE) {
    const pagina = await browser.newPage();
    const url = `http://127.0.0.1:${porta}${PREFISSO}${voce.percorso}`;
    let esito;
    try {
      esito = await misura(pagina, url, larghezza);
    } catch (errore) {
      problemi.push(`${voce.nome} @${larghezza.nome}: la pagina non si è caricata — ${errore.message}`);
      await pagina.close();
      continue;
    }
    await pagina.close();

    const etichetta = `${voce.nome} @${larghezza.nome}`;

    if (esito.larghezzaDocumento > esito.viewport + 1) {
      problemi.push(
        `${etichetta}: il documento è largo ${esito.larghezzaDocumento}px su un viewport da ${esito.viewport}`
      );
    }
    if (esito.sforano.length > 0) {
      problemi.push(`${etichetta}: elementi oltre il viewport — ${esito.sforano.join(", ")}`);
    }
    if (larghezza.isMobile && esito.altezza > voce.altezzaMax) {
      problemi.push(
        `${etichetta}: alta ${esito.altezza}px, oltre il limite di ${voce.altezzaMax}`
      );
    }
    if (esito.pesi.totale > PESO_MASSIMO) {
      problemi.push(
        `${etichetta}: ${Math.round(esito.pesi.totale / 1024)} KB senza immagini, oltre il limite di ${PESO_MASSIMO / 1024}`
      );
    }
    if (esito.errori.length > 0) {
      problemi.push(`${etichetta}: errori in console — ${esito.errori.join(" | ")}`);
    }
    if (esito.contattiPiccoli.length > 0) {
      problemi.push(`${etichetta}: comandi sotto i ${CONTATTO_MINIMO}px — ${esito.contattiPiccoli.join(", ")}`);
    }

    console.log(
      `${etichetta.padEnd(26)} altezza ${String(esito.altezza).padStart(5)}px  ` +
        `pagina ${String(Math.round(esito.pesi.totale / 1024)).padStart(3)} KB  ` +
        `immagini ${String(Math.round(esito.pesi.immagini / 1024)).padStart(4)} KB`
    );
  }
}

await browser.close();
server.close();

if (problemi.length > 0) {
  console.error("\nProblemi rilevati:");
  problemi.forEach((problema) => console.error("  - " + problema));
  process.exit(1);
}
console.log("\nNessun problema rilevato.");
