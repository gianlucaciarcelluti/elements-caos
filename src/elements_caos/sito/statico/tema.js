/* Scelta esplicita del tema.
 *
 * Il tema di default è quello scuro per tutti: è il buio prima della scoperta,
 * una scelta di progetto e non un rispecchiamento del sistema (Ruling 107).
 * Chi preferisce il chiaro lo sceglie qui, e la scelta resta. Senza
 * JavaScript il pulsante non compare e il sito resta scuro: il tema è una
 * comodità in più, non una condizione per leggere.
 */
(function () {
  "use strict";

  var CHIAVE = "elements-caos:tema";
  var radice = document.documentElement;

  function leggi() {
    // In navigazione privata l'accesso a localStorage può sollevare
    // eccezione: senza preferenza salvata si segue il sistema, ed è corretto.
    try {
      return localStorage.getItem(CHIAVE);
    } catch (errore) {
      return null;
    }
  }

  function salva(tema) {
    try {
      localStorage.setItem(CHIAVE, tema);
    } catch (errore) {
      /* La preferenza non si conserva: la pagina resta comunque usabile. */
    }
  }

  function applica(tema) {
    radice.setAttribute("data-tema", tema);
    var pulsante = document.getElementById("scelta-tema");
    if (pulsante) {
      var passaAScuro = tema === "chiaro";
      pulsante.setAttribute("aria-pressed", String(tema === "scuro"));
      pulsante.setAttribute(
        "aria-label",
        passaAScuro ? "Passa al tema scuro" : "Passa al tema chiaro"
      );
      pulsante.textContent = passaAScuro ? "Scuro" : "Chiaro";
    }
  }

  var salvato = leggi();
  applica(salvato === "chiaro" ? "chiaro" : "scuro");

  document.addEventListener("DOMContentLoaded", function () {
    var pulsante = document.getElementById("scelta-tema");
    if (!pulsante) {
      return;
    }
    pulsante.hidden = false;
    applica(radice.getAttribute("data-tema"));
    pulsante.addEventListener("click", function () {
      var nuovo = radice.getAttribute("data-tema") === "scuro" ? "chiaro" : "scuro";
      applica(nuovo);
      salva(nuovo);
    });
  });
})();
