"""Composizione della home: la tavola che si accende scorrendo le epoche.

È la tesi del progetto resa come esperienza invece che come paragrafo: un
palco fisso con la tavola periodica spenta, e otto passi — la tavola vuota,
le sei epoche, oggi — che la accendono nell'ordine in cui l'umanità l'ha
riempita. Il testo di ogni epoca è la sua descrizione in ``epoche.yaml``.

Senza JavaScript la tavola è tutta accesa e i passi si leggono come un
articolo: il markup è lo stato completo, spegnere è compito dello script.
"""

from typing import Any

from elements_caos.caricamento import ordina_per_scoperta
from elements_caos.models import Elemento, Epoca, Tappa
from elements_caos.render.diagrammi import formatta_anno, preposizione_articolata
from elements_caos.sito.pagina import ambiente_sito, url_epoca
from elements_caos.sito.tavola import RIGA_ATTINIDI, caselle


def passi_del_racconto(elementi: list[Elemento], epoche: dict[str, Epoca]) -> list[dict[str, Any]]:
    """I passi dello scrollytelling, con il limite di accensione di ciascuno.

    ``fino`` è la posizione cronologica dell'ultimo elemento che il passo
    accende: zero per la tavola vuota, l'ultimo elemento di ciascuna epoca,
    il totale per «oggi». Le epoche sono nell'ordine in cui compaiono nella
    cronologia, che è anche quello di ``anno_inizio``.
    """
    cronologia = ordina_per_scoperta(elementi)
    ordinate = sorted(epoche.values(), key=lambda epoca: epoca.anno_inizio)

    passi: list[dict[str, Any]] = [
        {
            "id": "inizio",
            "fino": 0,
            "occhiello": formatta_anno(cronologia[0].scoperta.anno),
            "epoca": None,
        }
    ]
    for epoca in ordinate:
        posizioni = [i for i, e in enumerate(cronologia, start=1) if e.scoperta.epoca == epoca.id]
        # Un'epoca senza elementi non accende nulla: nessun passo. Capita nei
        # dati di prova, non nel dataset, dove ogni epoca ha i suoi.
        if not posizioni:
            continue
        passi.append(
            {
                "id": epoca.id,
                "fino": max(posizioni),
                "quanti": len(posizioni),
                "occhiello": (
                    f"{formatta_anno(epoca.anno_inizio)} — {formatta_anno(epoca.anno_fine)}"
                ),
                "epoca": epoca,
            }
        )
    passi.append({"id": "oggi", "fino": len(cronologia), "occhiello": "Oggi", "epoca": None})
    return passi


def rendi_home(elementi: list[Elemento], epoche: dict[str, Epoca], tappe: list[Tappa]) -> str:
    """Compone la home del sito.

    I conteggi sono calcolati: una home che promette centodiciotto elementi
    mentre il dataset ne ha altri si smentisce alla prima pagina aperta.
    """
    cronologia = ordina_per_scoperta(elementi)
    primo, ultimo = cronologia[0], cronologia[-1]
    # Arrotondato al migliaio: «42.000 anni» si legge, «42.010» no, e il
    # primo anno è comunque una stima convenzionale.
    millenni = round((ultimo.scoperta.anno - primo.scoperta.anno) / 1000)

    modello = ambiente_sito().get_template("home.html.j2")
    return modello.render(
        totale=len(elementi),
        totale_tappe=len(tappe),
        totale_epoche=len(epoche),
        anni_leggibili=f"{millenni}.000",
        passi=passi_del_racconto(elementi, epoche),
        caselle=caselle(elementi),
        cronologia=cronologia,
        primo=primo,
        ultimo=ultimo,
        anno_primo=formatta_anno(primo.scoperta.anno),
        anno_ultimo=formatta_anno(ultimo.scoperta.anno),
        preposizione_da=preposizione_articolata("da", primo.nome) + primo.nome.lower(),
        riga_attinidi=RIGA_ATTINIDI,
        url_epoca=url_epoca,
        formatta_anno=formatta_anno,
    )
