/* La scheda come capitolo: avanzamento di lettura e rivelazione morbida.
 *
 * La barra in alto si riempie mentre si legge e i minuti che restano scendono;
 * le sezioni sotto la piega entrano con un piccolo movimento. Sono migliorie:
 * senza script la barra resta vuota e i minuti sono quelli totali, le sezioni
 * sono già visibili — la classe che le attenua si applica solo da qui, e solo
 * a chi non ha chiesto meno animazioni.
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var capitolo = document.getElementById("capitolo");
    var barra = document.getElementById("capitolo-progresso");
    var lettura = document.getElementById("capitolo-lettura");
    if (!capitolo || !barra || !lettura) {
      return;
    }

    var minuti = Number(capitolo.dataset.minuti) || 1;
    var ridotto =
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function aggiorna() {
      var rettangolo = capitolo.getBoundingClientRect();
      var finestra = window.innerHeight;
      // Frazione del capitolo già passata sopra il bordo inferiore della
      // finestra: 0 all'arrivo, 1 quando il capitolo è tutto sopra.
      var letto = (finestra - rettangolo.top) / (rettangolo.height + finestra * 0.2);
      var frazione = Math.min(1, Math.max(0, letto));
      barra.style.setProperty("--avanzamento", (frazione * 100).toFixed(1) + "%");
      var restano = Math.ceil(minuti * (1 - frazione));
      lettura.textContent = restano <= 0 ? "letto" : restano + " min";
    }

    window.addEventListener("scroll", aggiorna, { passive: true });
    window.addEventListener("resize", aggiorna);
    aggiorna();

    if (ridotto || !("IntersectionObserver" in window)) {
      return;
    }
    var osservatore = new IntersectionObserver(
      function (voci) {
        voci.forEach(function (voce) {
          if (voce.isIntersecting) {
            voce.target.classList.add("rivela--visto");
            osservatore.unobserve(voce.target);
          }
        });
      },
      { rootMargin: "0px 0px -10% 0px" }
    );
    // Solo le sezioni ancora sotto la piega si attenuano: quelle già in vista
    // all'arrivo restano com'erano, così la pagina a riposo è tutta leggibile.
    Array.prototype.forEach.call(capitolo.querySelectorAll(".rivela"), function (sezione) {
      if (sezione.getBoundingClientRect().top > window.innerHeight) {
        sezione.classList.add("rivela--attesa");
        osservatore.observe(sezione);
      }
    });
  });
})();
