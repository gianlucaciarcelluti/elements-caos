/* La tavola periodica che si riempie nell'ordine della scoperta.
 *
 * Senza questo script la pagina mostra la tavola completa, che è già utile:
 * il comando degli anni nasce nascosto e viene mostrato solo qui.
 *
 * Lo scorrevole agisce sulla POSIZIONE cronologica, non sull'anno. Una scala
 * da 40000 a.C. al 2010 spenderebbe quasi tutta la corsa sulla preistoria e
 * schiaccerebbe negli ultimi pixel i due secoli in cui succede quasi tutto.
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var comando = document.getElementById("comando-anni");
    var cursore = document.getElementById("anno");
    var stato = document.getElementById("stato-anni");
    var tavola = document.querySelector(".tavola");
    if (!comando || !cursore || !stato || !tavola) {
      return;
    }

    var caselle = Array.prototype.slice.call(tavola.querySelectorAll(".casella"));
    // Ordinate per posizione cronologica: serve a sapere qual è l'ultimo
    // elemento entrato senza riscorrere ogni volta tutte e 118 le caselle.
    var perPosizione = caselle.slice().sort(function (a, b) {
      return Number(a.dataset.posizione) - Number(b.dataset.posizione);
    });

    comando.hidden = false;

    function aggiorna(valore) {
      for (var i = 0; i < caselle.length; i += 1) {
        var scoperta = Number(caselle[i].dataset.posizione) <= valore;
        caselle[i].classList.toggle("casella--spenta", !scoperta);
      }
      var ultima = perPosizione[valore - 1];
      var titolo = ultima ? ultima.querySelector("a").getAttribute("title") : "";
      stato.textContent = valore + " elementi su " + perPosizione.length + " — ultimo: " + titolo;
    }

    // "input" copre trascinamento, frecce, Home e Fine: un input di tipo range
    // porta con sé la navigazione da tastiera, non serve gestirla a mano.
    cursore.addEventListener("input", function () {
      fermaAnimazione();
      aggiorna(Number(cursore.value));
    });

    var riavvolgi = document.getElementById("riavvolgi");
    if (riavvolgi) {
      riavvolgi.addEventListener("click", function () {
        fermaAnimazione();
        cursore.value = "1";
        aggiorna(1);
      });
    }

    var anima = document.getElementById("anima");
    var temporizzatore = null;

    function fermaAnimazione() {
      if (temporizzatore !== null) {
        window.clearInterval(temporizzatore);
        temporizzatore = null;
        if (anima) {
          anima.textContent = "Riproduci";
        }
      }
    }

    if (anima) {
      anima.addEventListener("click", function () {
        if (temporizzatore !== null) {
          fermaAnimazione();
          return;
        }
        // Chi ha chiesto meno animazioni non deve riceverne: si va all'inizio
        // e si mostra tutto, senza far lampeggiare 118 caselle.
        var riduci =
          window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        if (riduci) {
          cursore.value = String(perPosizione.length);
          aggiorna(perPosizione.length);
          return;
        }
        cursore.value = "1";
        aggiorna(1);
        anima.textContent = "Ferma";
        temporizzatore = window.setInterval(function () {
          var successivo = Number(cursore.value) + 1;
          if (successivo > perPosizione.length) {
            fermaAnimazione();
            return;
          }
          cursore.value = String(successivo);
          aggiorna(successivo);
        }, 90);
      });
    }

    aggiorna(Number(cursore.value));
  });
})();
