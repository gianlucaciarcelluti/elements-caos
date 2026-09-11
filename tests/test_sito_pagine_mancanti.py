"""Test delle pagine che il sito deve avere per non perdere URL già pubblicati.

Il piano di ridisegno saltava epoche, scopritori, attribuzioni e la home: sono
108 pagine che il sito costruito con Quartz pubblica dal Task 23, e senza le
quali la sostituzione romperebbe altrettanti collegamenti. Qui si verifica che
ci siano e che portino il loro contenuto.
"""

import re
from pathlib import Path

from elements_caos.caricamento import (
    carica_elementi,
    carica_epoche,
    carica_itinerario,
    carica_scopritori,
)
from elements_caos.sito.contesto import (
    URL_ATTRIBUZIONI,
    URL_HOME,
    rendi_attribuzioni_sito,
    rendi_epoca_sito,
    rendi_scopritore_sito,
)
from elements_caos.sito.home import rendi_home
from elements_caos.sito.pagina import url_epoca, url_scopritore

DATI = Path(__file__).resolve().parents[1] / "data"


def _tutto() -> tuple:
    """Carica gli ingredienti comuni a tutte le pagine di contesto."""
    return (
        carica_elementi(DATI / "elements"),
        carica_epoche(DATI / "epoche.yaml"),
        carica_scopritori(DATI / "scopritori.yaml"),
    )


# --- URL: sono già pubblicati e non possono cambiare ------------------------


def test_gli_url_seguono_lo_schema_pubblicato() -> None:
    """Gli stessi percorsi che Quartz serve oggi."""
    elementi, epoche, scopritori = _tutto()

    assert url_epoca("Era nucleare") == "epoche/era-nucleare.html"
    assert url_scopritore(scopritori["hennig-brand"]) == "scopritori/hennig-brand.html"
    assert URL_ATTRIBUZIONI == "attribuzioni.html"
    assert URL_HOME == "index.html"


# --- Epoche ------------------------------------------------------------------


def test_la_pagina_d_epoca_porta_descrizione_ed_estremi() -> None:
    """L'epoca è contesto storico: senza la descrizione è solo un elenco."""
    elementi, epoche, scopritori = _tutto()

    pagina = rendi_epoca_sito(epoche["nucleare"], elementi, scopritori)

    assert "Era nucleare" in pagina
    assert "si fabbricano" in pagina
    assert "1940" in pagina


def test_la_pagina_d_epoca_elenca_i_suoi_elementi_in_ordine() -> None:
    """Gli elementi dell'epoca, in ordine di scoperta."""
    elementi, epoche, scopritori = _tutto()

    pagina = rendi_epoca_sito(epoche["antichita"], elementi, scopritori)

    # L'elenco, non la tavola che lo precede: quella è per numero atomico.
    elenco = pagina[pagina.index('class="contesto__elenco"') :]
    assert elenco.index("Oro") < elenco.index("Arsenico")
    assert 'href="../elementi/oro.html"' in elenco


def test_ogni_elemento_appartiene_a_un_epoca_esistente() -> None:
    """Un'epoca citata e non definita sarebbe una pagina mancante."""
    elementi, epoche, _ = _tutto()

    for elemento in elementi:
        assert elemento.scoperta.epoca in epoche


# --- Scopritori --------------------------------------------------------------


def test_la_pagina_dello_scopritore_porta_i_suoi_elementi() -> None:
    """Chi ha scoperto cosa: è il senso della pagina."""
    elementi, epoche, scopritori = _tutto()

    pagina = rendi_scopritore_sito(scopritori["hennig-brand"], elementi)

    assert "Hennig Brand" in pagina
    assert 'href="../elementi/fosforo.html"' in pagina


def test_l_anagrafica_ignota_non_si_inventa() -> None:
    """Quattro scopritori hanno date sconosciute: la pagina non deve riempirle.

    È la regola del progetto: ciò che non si sa resta a null e non compare.
    """
    elementi, epoche, scopritori = _tutto()

    senza_date = [s for s in scopritori.values() if s.nato is None and s.morto is None]
    assert senza_date, "nessuno scopritore senza date: la fixture è cambiata"

    pagina = rendi_scopritore_sito(senza_date[0], elementi)

    assert "None" not in pagina


def test_il_ritratto_compare_solo_se_c_e() -> None:
    """Uno scopritore senza ritratto non deve produrre un'immagine rotta."""
    elementi, epoche, scopritori = _tutto()

    senza = next(s for s in scopritori.values() if s.ritratto is None)

    assert "<img" not in rendi_scopritore_sito(senza, elementi)


# --- Attribuzioni ------------------------------------------------------------


def test_le_attribuzioni_elencano_autore_licenza_e_fonte() -> None:
    """È l'obbligo verso chi riusa, e la pagina esiste per quello."""
    elementi, epoche, scopritori = _tutto()

    pagina = rendi_attribuzioni_sito(scopritori)

    con_ritratto = [s for s in scopritori.values() if s.ritratto is not None]
    primo = sorted(con_ritratto, key=lambda s: s.nome)[0]

    assert primo.nome in pagina
    assert primo.ritratto.licenza in pagina
    assert primo.ritratto.fonte in pagina


def test_ogni_pagina_di_contesto_porta_l_avvertenza() -> None:
    """Vale per tutte, nessuna esclusa."""
    elementi, epoche, scopritori = _tutto()
    tappe = carica_itinerario(DATI / "itinerario.yaml")

    pagine = [
        rendi_home(elementi, epoche, tappe),
        rendi_epoca_sito(epoche["alchimia"], elementi, scopritori),
        rendi_scopritore_sito(scopritori["hennig-brand"], elementi),
        rendi_attribuzioni_sito(scopritori),
    ]

    for pagina in pagine:
        assert "intelligenza artificiale" in pagina


# --- Il comando emette tutto -------------------------------------------------


def test_il_comando_emette_tutte_le_pagine(tmp_path: Path) -> None:
    """Nessun URL pubblicato deve restare senza pagina."""
    from elements_caos.cli import main

    uscita = tmp_path / "pubblico"
    assert main(["sito", "--dati", str(DATI), "--uscita", str(uscita)]) == 0

    attesi = [
        "index.html",
        "cronologia-degli-elementi.html",
        "tavola-periodica.html",
        "itinerario.html",
        "attribuzioni.html",
        "elementi/fosforo.html",
        "epoche/era-nucleare.html",
        "scopritori/hennig-brand.html",
    ]
    for percorso in attesi:
        assert (uscita / percorso).is_file(), f"manca {percorso}"

    # Il totale si deriva dai dati invece di essere una costante: così, se un
    # elemento o uno scopritore viene aggiunto, il test dice cosa manca invece
    # di limitarsi a un numero diverso da quello atteso.
    elementi, epoche, scopritori = _tutto()
    servizio = 9  # home, cronologia, tavola, itinerario, attribuzioni, 404, 3 indici
    from elements_caos.sito.reindirizzamenti import TAG_PUBBLICATI

    atteso = len(elementi) + len(scopritori) + len(epoche) + servizio + len(TAG_PUBBLICATI)

    emesse = sorted(p.relative_to(uscita).as_posix() for p in uscita.rglob("*.html"))
    assert len(emesse) == atteso, f"emesse {len(emesse)}, attese {atteso}"


# --- Le pagine indice --------------------------------------------------------


def test_gli_indici_di_cartella_esistono() -> None:
    """Quartz pubblicava /elementi, /epoche e /scopritori: erano navigazione.

    Sono URL raggiungibili dal sito già pubblicato, e sostituirlo senza di
    loro li romperebbe.
    """
    from elements_caos.sito.contesto import (
        URL_INDICE_ELEMENTI,
        URL_INDICE_EPOCHE,
        URL_INDICE_SCOPRITORI,
    )

    assert URL_INDICE_ELEMENTI == "elementi/index.html"
    assert URL_INDICE_EPOCHE == "epoche/index.html"
    assert URL_INDICE_SCOPRITORI == "scopritori/index.html"


def test_l_indice_degli_elementi_raggruppa_per_categoria() -> None:
    """Raggruppare per categoria è ciò che le pagine di tag facevano di utile.

    Quartz generava /tags/alogeno, /tags/gas-nobile e così via. Quella
    tassonomia non viene replicata, ma la possibilità di scorrere gli elementi
    per categoria chimica sì, sotto un indirizzo più sensato.
    """
    from elements_caos.sito.contesto import rendi_indice_elementi

    elementi, epoche, scopritori = _tutto()
    pagina = rendi_indice_elementi(elementi)

    assert "Gas nobile" in pagina
    assert "Metallo di transizione" in pagina
    # Il conteggio è su un elemento interno: la classe della pastiglia porta
    # anche il modificatore dell'epoca, e cercarla esatta non troverebbe nulla.
    assert pagina.count("pastiglia__simbolo") == 118


def test_l_indice_degli_scopritori_e_in_ordine_alfabetico() -> None:
    """Cento nomi si scorrono per lettera, non per numero atomico."""
    from elements_caos.sito.contesto import voci_scopritori

    elementi, epoche, scopritori = _tutto()
    nomi = [voce["scopritore"].nome for voce in voci_scopritori(scopritori, elementi)]

    assert nomi == sorted(nomi, key=lambda n: n.lower())


def test_l_indice_degli_scopritori_dice_quanti_elementi() -> None:
    """Quanti elementi ha trovato ciascuno: è l'informazione che ordina la lista."""
    from elements_caos.sito.contesto import voci_scopritori

    elementi, epoche, scopritori = _tutto()
    voci = {v["scopritore"].id: v for v in voci_scopritori(scopritori, elementi)}

    assert voci["hennig-brand"]["quanti"] == 1


# --- Reindirizzamenti dai vecchi indirizzi ----------------------------------


def test_ogni_tag_pubblicato_ha_una_destinazione() -> None:
    """Le pagine di tag di Quartz non esistono più, ma i loro URL sì.

    La regola del piano è «ogni URL prodotto da Quartz deve esistere anche nel
    nuovo sito, o avere un reindirizzamento». La tassonomia dei tag non viene
    replicata — non fa parte del progetto — quindi ognuno di quegli indirizzi
    porta alla pagina che gli somiglia di più.
    """
    from elements_caos.sito.reindirizzamenti import destinazione

    assert destinazione("tags/gas-nobile") == "elementi/index.html"
    assert destinazione("tags/epoca/nucleare") == "epoche/era-nucleare.html"
    assert destinazione("tags/secolo/xvii") == "cronologia-degli-elementi.html"
    assert destinazione("tags/millennio/40ac") == "cronologia-degli-elementi.html"
    assert destinazione("tags/scopritore") == "scopritori/index.html"
    assert destinazione("tags") == "elementi/index.html"


def test_nessun_tag_resta_senza_destinazione() -> None:
    """Tutti e quarantacinque, non quarantaquattro."""
    from elements_caos.sito.reindirizzamenti import TAG_PUBBLICATI, destinazione

    assert len(TAG_PUBBLICATI) == 45
    for tag in TAG_PUBBLICATI:
        assert destinazione(tag), f"{tag} non ha destinazione"


def test_il_reindirizzamento_e_una_pagina_vera() -> None:
    """Chi ci arriva deve capire cos'è successo, non vedere una pagina bianca."""
    from elements_caos.sito.reindirizzamenti import rendi_reindirizzamento

    pagina = rendi_reindirizzamento("tags/gas-nobile", "elementi/index.html")

    assert '<meta http-equiv="refresh"' in pagina
    assert 'rel="canonical"' in pagina
    assert "noindex" in pagina
    assert "elementi/index.html" in pagina


# --- Il tema della tavola accesa (Task 37) ------------------------------------


def test_la_pagina_d_epoca_apre_con_la_sua_porzione_di_tavola() -> None:
    """La tavola intera, con accese solo le caselle che l'epoca ha riempito.

    È lo stesso palco della home fermato su un'epoca: si vede in un colpo
    d'occhio cosa quell'epoca ha aggiunto e cosa mancava ancora.
    """
    elementi, epoche, scopritori = _tutto()
    epoca = epoche["elettrolisi"]

    pagina = rendi_epoca_sito(epoca, elementi, scopritori)

    assert 'class="capitolo-epoca epoca--elettrolisi contesto-epoca"' in pagina
    inizio = pagina.index('class="tavola tavola--palco')
    tavola = pagina[inizio : pagina.index("</ul>", inizio)]
    caselle = re.findall(r'<li class="casella epoca--(\w+)( casella--spenta)?"', tavola)
    assert len(caselle) == 118
    for id_epoca, spenta in caselle:
        assert bool(spenta) == (id_epoca != "elettrolisi"), id_epoca
    assert "21 delle 118 caselle" in pagina


def test_l_istogramma_colora_ogni_periodo_con_la_sua_epoca() -> None:
    """Ogni barra dell'istogramma porta il colore dell'epoca del suo periodo."""
    from elements_caos.sito.cronologia import densita_scoperte

    elementi, epoche, _ = _tutto()

    secchielli = densita_scoperte(elementi, epoche)

    assert secchielli[0]["epoca"] == "antichita"
    per_inizio = {s["inizio"]: s["epoca"] for s in secchielli}
    assert per_inizio[1650] == "alchimia"
    assert per_inizio[1800] == "elettrolisi"
    assert per_inizio[1950] == "nucleare"
    assert all(s["epoca"] in epoche for s in secchielli)


def test_le_tappe_dell_itinerario_portano_il_colore_del_loro_elemento() -> None:
    """La tappa sul fosforo è color alchimia, quella sul plutonio color era nucleare."""
    from elements_caos.sito.itinerario import rendi_itinerario_sito

    elementi, _, _ = _tutto()
    tappe = carica_itinerario(DATI / "itinerario.yaml")

    pagina = rendi_itinerario_sito(tappe, elementi)

    for tappa in tappe:
        elemento = next(e for e in elementi if e.nome == tappa.elemento)
        assert f'class="tappa epoca--{elemento.scoperta.epoca}"' in pagina, tappa.titolo
