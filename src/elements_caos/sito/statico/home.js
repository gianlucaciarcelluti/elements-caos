/* La home: la tavola si accende mentre si scorrono le epoche.
 *
 * Il markup è lo stato finale — tutte le caselle accese. Questo script lo
 * porta allo stato iniziale (tavola vuota) e poi lo fa avanzare passo per
 * passo, seguendo il passo che sta al centro della finestra. Senza script la
 * pagina resta com'è: completa e leggibile.
 *
 * Le caselle non si accendono tutte insieme ma in ordine cronologico, con un
 * piccolo ritardo l'una dall'altra: è quello che rende visibile l'ordine, che
 * è l'unica cosa che questa pagina vuole dire. Chi ha chiesto meno animazioni
 * le vede accendersi in blocco.
 */
(function () {
  "use strict";

  if (!("IntersectionObserver" in window)) {
    return;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var tavola = document.getElementById("palco-tavola");
    var striscia = document.getElementById("palco-striscia");
    var anno = document.getElementById("palco-anno");
    var quanti = document.getElementById("palco-quanti");
    var ultimo = document.getElementById("palco-ultimo");
    var passi = Array.prototype.slice.call(document.querySelectorAll(".passo"));
    if (!tavola || !striscia || !anno || !quanti || !ultimo || passi.length === 0) {
      return;
    }

    var caselle = Array.prototype.slice.call(tavola.querySelectorAll(".casella"));
    var tacche = Array.prototype.slice.call(striscia.querySelectorAll(".tacca"));
    var perPosizione = {};
    caselle.forEach(function (casella) {
      perPosizione[Number(casella.dataset.posizione)] = casella;
    });
    var annoIniziale = anno.textContent;
    var ridotto =
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var corrente = -1;
    // Oltre questo numero di caselle il ritardo non cresce più: un'epoca da
    // trenta elementi si accende in poco più di un secondo, non in tre.
    var RITARDO_MASSIMO = 40;
    var PASSO_RITARDO_MS = 28;

    function applica(fino) {
      if (fino === corrente) {
        return;
      }
      var inAvanti = fino > corrente;
      var precedente = corrente < 0 ? 0 : corrente;
      corrente = fino;

      caselle.forEach(function (casella) {
        var posizione = Number(casella.dataset.posizione);
        var ordine = inAvanti ? posizione - precedente : fino - posizione;
        var ritardo = ridotto ? 0 : Math.max(0, Math.min(ordine, RITARDO_MASSIMO)) * PASSO_RITARDO_MS;
        casella.style.setProperty("--ritardo", ritardo + "ms");
        casella.classList.toggle("casella--spenta", posizione > fino);
        casella.classList.toggle("casella--ultima", posizione === fino);
      });
      tacche.forEach(function (tacca) {
        var posizione = Number(tacca.dataset.posizione);
        tacca.classList.toggle("tacca--spenta", posizione > fino);
        tacca.classList.toggle("tacca--ultima", posizione === fino);
      });

      var entrata = perPosizione[fino];
      quanti.textContent = String(fino);
      if (entrata) {
        anno.textContent = entrata.dataset.anno;
        ultimo.textContent = "ultimo entrato: " + entrata.dataset.nome;
        // L'accento della pagina segue l'epoca del passo: è così che la home
        // cambia colore lungo il racconto.
        document.documentElement.style.setProperty(
          "--colore-accento",
          "var(--epoca-" + entrata.dataset.epoca + "-testo)"
        );
      } else {
        anno.textContent = annoIniziale;
        ultimo.textContent = "nessuna scoperta";
        document.documentElement.style.removeProperty("--colore-accento");
      }
    }

    var osservatore = new IntersectionObserver(
      function (voci) {
        voci.forEach(function (voce) {
          if (!voce.isIntersecting) {
            return;
          }
          passi.forEach(function (passo) {
            passo.classList.toggle("passo--attivo", passo === voce.target);
          });
          applica(Number(voce.target.dataset.fino));
        });
      },
      // Una fascia stretta al centro della finestra: il passo attivo è quello
      // che la attraversa, uno solo per volta.
      { rootMargin: "-45% 0px -45% 0px", threshold: 0 }
    );

    // Lo stato iniziale è la tavola vuota, e l'anno del primo passo.
    anno.textContent = passi[0].querySelector(".passo__occhiello").textContent;
    annoIniziale = anno.textContent;
    tavola.classList.add("tavola--viva");
    applica(0);
    passi[0].classList.add("passo--attivo");
    passi.forEach(function (passo) {
      osservatore.observe(passo);
    });
  });
})();
