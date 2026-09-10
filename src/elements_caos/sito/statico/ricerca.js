/* Ricerca nel sito, interamente nel browser.
 *
 * L'indice è un file JSON scaricato al primo uso e poi tenuto in memoria: per
 * duecentoventiquattro voci non serve un servizio di ricerca, e non averlo
 * significa niente richieste verso terzi mentre qualcuno cerca.
 *
 * Il campo nasce nascosto e lo mostra questo script: senza JavaScript non
 * cercherebbe nulla, e un campo che non cerca è peggio di un campo assente.
 */
(function () {
  "use strict";

  var MASSIMI_RISULTATI = 12;

  /* Toglie gli accenti e passa a minuscolo: chi cerca "antichita" deve
   * trovare "Antichità", e chi scrive "Ytterbio" o "ytterbio" lo stesso. */
  function normalizza(testo) {
    return testo
      .toLowerCase()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "");
  }

  document.addEventListener("DOMContentLoaded", function () {
    var contenitore = document.getElementById("ricerca");
    var campo = document.getElementById("campo-ricerca");
    var esiti = document.getElementById("esiti-ricerca");
    if (!contenitore || !campo || !esiti) {
      return;
    }

    contenitore.hidden = false;

    var voci = null;
    var caricamento = null;

    function carica() {
      if (caricamento === null) {
        caricamento = fetch(contenitore.dataset.indice)
          .then(function (risposta) {
            return risposta.ok ? risposta.json() : [];
          })
          .then(function (dati) {
            voci = dati.map(function (voce) {
              voce._n = normalizza(voce.t + " " + (voce.k || ""));
              return voce;
            });
          })
          .catch(function () {
            // Indice non raggiungibile: la ricerca resta muta invece di
            // mostrare un errore che il lettore non può risolvere.
            voci = [];
          });
      }
      return caricamento;
    }

    function punteggio(voce, cercato) {
      var titolo = normalizza(voce.t);
      if (titolo === cercato) return 0;
      // Il simbolo esatto batte il titolo che comincia per la stessa lettera:
      // chi digita "P" cerca il fosforo, non il palladio.
      if (voce.s && normalizza(voce.s) === cercato) return 1;
      if (titolo.indexOf(cercato) === 0) return 2;
      if (titolo.indexOf(cercato) !== -1) return 3;
      return voce._n.indexOf(cercato) !== -1 ? 4 : -1;
    }

    function mostra(cercato) {
      var normalizzato = normalizza(cercato.trim());
      if (normalizzato.length < 1 || voci === null) {
        esiti.hidden = true;
        esiti.innerHTML = "";
        return;
      }

      var trovate = [];
      for (var i = 0; i < voci.length; i += 1) {
        var p = punteggio(voci[i], normalizzato);
        if (p !== -1) {
          trovate.push({ voce: voci[i], p: p });
        }
      }
      trovate.sort(function (a, b) {
        return a.p - b.p || a.voce.t.localeCompare(b.voce.t, "it");
      });

      esiti.innerHTML = "";
      if (trovate.length === 0) {
        var vuoto = document.createElement("li");
        vuoto.className = "esito esito--vuoto";
        vuoto.textContent = "Nessun risultato per «" + cercato.trim() + "»";
        esiti.appendChild(vuoto);
        esiti.hidden = false;
        return;
      }

      trovate.slice(0, MASSIMI_RISULTATI).forEach(function (trovata) {
        var riga = document.createElement("li");
        riga.className = "esito";
        var collegamento = document.createElement("a");
        collegamento.href = contenitore.dataset.radice + trovata.voce.u;
        collegamento.textContent = trovata.voce.t;
        var tipo = document.createElement("span");
        tipo.className = "esito__tipo";
        tipo.textContent = trovata.voce.c;
        riga.appendChild(collegamento);
        riga.appendChild(tipo);
        esiti.appendChild(riga);
      });
      esiti.hidden = false;
    }

    campo.addEventListener("focus", carica);
    campo.addEventListener("input", function () {
      carica().then(function () {
        mostra(campo.value);
      });
    });

    campo.addEventListener("keydown", function (evento) {
      if (evento.key === "Escape") {
        campo.value = "";
        mostra("");
        campo.blur();
        return;
      }
      if (evento.key === "ArrowDown") {
        var primo = esiti.querySelector("a");
        if (primo) {
          evento.preventDefault();
          primo.focus();
        }
      }
    });

    // Un clic fuori chiude i risultati, che altrimenti resterebbero aperti
    // sopra il contenuto.
    document.addEventListener("click", function (evento) {
      if (!contenitore.contains(evento.target)) {
        esiti.hidden = true;
      }
    });
  });
})();
