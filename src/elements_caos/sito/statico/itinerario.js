/* Stato di lettura dell'itinerario.
 *
 * Vive nel browser di chi legge e non viene inviato da nessuna parte: il sito
 * ha dichiarato di non raccogliere nulla, e non esiste un server a cui
 * mandarlo. Senza JavaScript la pagina mostra comunque tutte le tappe, che
 * sono già il percorso completo: l'avanzamento è una comodità.
 */
(function () {
  "use strict";

  var CHIAVE = "elements-caos:itinerario";

  function leggi() {
    // In navigazione privata l'accesso può sollevare eccezione: senza stato
    // salvato la pagina si vede intera, ed è il comportamento corretto.
    try {
      var grezzo = localStorage.getItem(CHIAVE);
      var lette = grezzo ? JSON.parse(grezzo) : [];
      return Array.isArray(lette) ? lette : [];
    } catch (errore) {
      return [];
    }
  }

  function salva(lette) {
    try {
      localStorage.setItem(CHIAVE, JSON.stringify(lette));
    } catch (errore) {
      /* Lo stato non si conserva: la pagina resta comunque usabile. */
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var pannello = document.getElementById("avanzamento");
    var stato = document.getElementById("stato-avanzamento");
    var barra = document.getElementById("barra-avanzamento");
    var riprendi = document.getElementById("riprendi");
    var azzera = document.getElementById("azzera");
    var tappe = Array.prototype.slice.call(document.querySelectorAll(".tappa"));
    var segni = Array.prototype.slice.call(document.querySelectorAll(".tappa__segno"));
    if (!pannello || !stato || !barra || tappe.length === 0) {
      return;
    }

    var lette = leggi();

    pannello.hidden = false;
    tappe.forEach(function (tappa) {
      var etichetta = tappa.querySelector(".tappa__letta");
      if (etichetta) {
        etichetta.hidden = false;
      }
    });

    function primaDaLeggere() {
      for (var i = 0; i < tappe.length; i += 1) {
        var numero = Number(tappe[i].dataset.tappa);
        if (lette.indexOf(numero) === -1) {
          return numero;
        }
      }
      return null;
    }

    function aggiorna() {
      tappe.forEach(function (tappa) {
        var numero = Number(tappa.dataset.tappa);
        tappa.classList.toggle("tappa--letta", lette.indexOf(numero) !== -1);
      });
      segni.forEach(function (segno) {
        segno.checked = lette.indexOf(Number(segno.dataset.tappa)) !== -1;
      });

      var quante = lette.length;
      var totale = tappe.length;
      barra.style.width = Math.round((quante / totale) * 100) + "%";

      var prossima = primaDaLeggere();
      if (prossima === null) {
        stato.textContent = "Percorso completato: " + totale + " tappe su " + totale + ".";
        riprendi.hidden = true;
        return;
      }
      riprendi.hidden = false;
      riprendi.setAttribute("href", "#tappa-" + prossima);
      riprendi.textContent = quante === 0 ? "Comincia" : "Riprendi dalla tappa " + prossima;
      stato.textContent = quante + " tappe su " + totale + " lette.";
    }

    segni.forEach(function (segno) {
      segno.addEventListener("change", function () {
        var numero = Number(segno.dataset.tappa);
        var posizione = lette.indexOf(numero);
        if (segno.checked && posizione === -1) {
          lette.push(numero);
        } else if (!segno.checked && posizione !== -1) {
          lette.splice(posizione, 1);
        }
        salva(lette);
        aggiorna();
      });
    });

    if (azzera) {
      azzera.addEventListener("click", function () {
        lette = [];
        salva(lette);
        aggiorna();
      });
    }

    aggiorna();
  });
})();
