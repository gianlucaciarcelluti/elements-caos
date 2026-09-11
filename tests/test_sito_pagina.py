"""Test dell'emettitore HTML del sito.

Il sito è un secondo emettitore dallo stesso dataset che produce il vault: qui
si verifica che la pagina di un elemento sia completa, corretta e riproducibile,
non che sia bella. L'aspetto arriva con l'identità visiva.
"""

from pathlib import Path

from elements_caos.caricamento import carica_elementi, carica_epoche, carica_scopritori
from elements_caos.models import Elemento
from elements_caos.render.note import costruisci_contesto
from elements_caos.sito.pagina import (
    URL_ELEMENTI,
    paragrafi_html,
    rendi_elemento,
    slug,
    url_approfondimento,
    url_elemento,
)

DATI_PROVA = Path(__file__).parent / "dati_prova"


def _elementi() -> list[Elemento]:
    """Carica gli elementi dei dati di prova."""
    return carica_elementi(DATI_PROVA / "elements")


def _pagina_fosforo() -> str:
    """Genera la pagina HTML del fosforo a partire dai dati di prova."""
    elementi = _elementi()
    scopritori = carica_scopritori(DATI_PROVA / "scopritori.yaml")
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")
    contesto = costruisci_contesto(elementi[0], elementi, scopritori, epoche)
    return rendi_elemento(contesto)


# --- Struttura del documento -------------------------------------------------


def test_documento_html_ben_formato() -> None:
    """La pagina è un documento HTML completo, non un frammento."""
    pagina = _pagina_fosforo()

    assert pagina.startswith("<!DOCTYPE html>")
    assert pagina.count("<html") == 1
    assert pagina.rstrip().endswith("</html>")


def test_documento_dichiara_lingua_e_viewport() -> None:
    """Senza lingua e viewport la pagina è inservibile su telefono e ai lettori di schermo."""
    pagina = _pagina_fosforo()

    assert '<html lang="it"' in pagina
    assert '<meta name="viewport" content="width=device-width, initial-scale=1"' in pagina
    assert '<meta charset="utf-8"' in pagina


def test_titolo_non_ripete_il_nome_del_sito() -> None:
    """Il titolo della scheda del browser porta l'elemento, non il sito due volte.

    È il difetto misurato sul sito costruito con Quartz, che ripeteva il nome
    dell'elemento come intestazione di pagina e come titolo della nota.
    """
    pagina = _pagina_fosforo()

    assert "<title>Fosforo</title>" in pagina
    assert pagina.count("<title>") == 1


def test_il_nome_compare_una_volta_sola_come_intestazione() -> None:
    """Nessun titolo doppio: una sola h1 in tutta la pagina."""
    pagina = _pagina_fosforo()

    assert pagina.count("<h1") == 1


# --- Contenuto ---------------------------------------------------------------


def test_pagina_contiene_identita_dell_elemento() -> None:
    """Nome, simbolo e numero atomico devono esserci."""
    pagina = _pagina_fosforo()

    assert "Fosforo" in pagina
    assert ">P<" in pagina
    assert "15" in pagina


def test_pagina_contiene_la_prosa_dei_beat() -> None:
    """La prosa è quella composta da prosa.py, non una riscrittura."""
    pagina = _pagina_fosforo()

    assert "insegue la pietra filosofale" in pagina
    assert "Hennig Brand" in pagina


def test_pagina_contiene_le_fonti() -> None:
    """Ogni affermazione è sostenuta dalla fonte citata: le fonti vanno in pagina."""
    pagina = _pagina_fosforo()

    assert "https://esempio.it/brand" in pagina
    assert "Storia del fosforo" in pagina


def test_pagina_porta_l_avvertenza_sull_ia() -> None:
    """Vale per il sito quanto per il vault: nessuna pagina ne è priva."""
    pagina = _pagina_fosforo()

    assert "intelligenza artificiale" in pagina
    assert "imprecisioni" in pagina


def test_nessun_campo_di_frontmatter_nel_corpo() -> None:
    """I metadati grezzi non si mostrano al lettore.

    Il blocco delle proprietà di Quartz esponeva `tags` e `aliases` in cima a
    ogni pagina, con le etichette spezzate lettera per lettera sul telefono.
    """
    pagina = _pagina_fosforo()

    assert "aliases" not in pagina
    assert "tipo: elemento" not in pagina


def test_tempo_di_lettura_concorda_al_singolare() -> None:
    """«1 minuti di lettura» è un refuso che si vede su ogni nota breve."""
    pagina = _pagina_fosforo()

    assert "1 minuti" not in pagina


# --- Determinismo ------------------------------------------------------------


def test_emissione_deterministica() -> None:
    """A parità di dati la pagina è identica byte per byte.

    È lo stesso presidio che regge il vault: senza, la CI non può distinguere
    una modifica reale da un riordino casuale.
    """
    assert _pagina_fosforo() == _pagina_fosforo()


# --- URL ---------------------------------------------------------------------


def test_slug_minuscolo_con_trattini() -> None:
    """Lo slug segue lo schema già pubblicato, che non può cambiare."""
    assert slug("Fosforo") == "fosforo"
    assert slug("Hennig Brand") == "hennig-brand"
    assert slug("Era nucleare") == "era-nucleare"


def test_slug_conserva_accenti_e_apostrofi() -> None:
    """Gli URL pubblicati contengono accenti e apostrofi: vanno conservati.

    Il sito è pubblico dal Task 23 e `epoche/l'età-dell'elettrolisi` è un URL
    che esiste già: normalizzarlo in ASCII romperebbe i link esistenti.
    """
    assert slug("Antichità") == "antichità"
    assert slug("L'età dell'elettrolisi") == "l'età-dell'elettrolisi"


def test_url_elemento_segue_lo_schema_pubblicato() -> None:
    """`/elementi/fosforo.html`, come già pubblicato."""
    elemento = _elementi()[0]

    assert url_elemento(elemento) == f"{URL_ELEMENTI}/fosforo.html"


# --- Prosa in HTML -----------------------------------------------------------


def test_paragrafi_html_separa_i_beat() -> None:
    """Ogni beat diventa un paragrafo."""
    risultato = paragrafi_html("Primo beat.\n\nSecondo beat.")

    assert risultato == "<p>Primo beat.</p>\n<p>Secondo beat.</p>"


def test_paragrafi_html_rende_le_formule_di_cautela() -> None:
    """Le formule di cautela di prosa.py sono in corsivo Markdown: diventano <em>."""
    risultato = paragrafi_html("*Per tradizione:* il fatto è tramandato.")

    assert risultato == "<p><em>Per tradizione:</em> il fatto è tramandato.</p>"


def test_paragrafi_html_neutralizza_l_html_nei_dati() -> None:
    """Il testo dei dati non può iniettare markup nella pagina."""
    risultato = paragrafi_html("Un <script>alert(1)</script> nel testo.")

    assert "<script>" not in risultato
    assert "&lt;script&gt;" in risultato


def test_paragrafi_html_conserva_le_parentesi_quadre() -> None:
    """`[Rn]` è una configurazione elettronica, non un link Markdown."""
    risultato = paragrafi_html("La configurazione risulta [Rn] 5f14 7s2 7p1.")

    assert "[Rn]" in risultato


# --- Il sottocomando ---------------------------------------------------------


def test_comando_sito_emette_le_pagine(tmp_path: Path) -> None:
    """`elements-caos sito` scrive un file per elemento nella cartella indicata."""
    from elements_caos.cli import main

    uscita = tmp_path / "pubblico"
    codice = main(["sito", "--dati", str(DATI_PROVA), "--uscita", str(uscita)])

    assert codice == 0
    assert (uscita / "elementi" / "fosforo.html").is_file()


def test_comando_sito_e_riproducibile(tmp_path: Path) -> None:
    """Due esecuzioni consecutive producono gli stessi byte."""
    from elements_caos.cli import main

    primo, secondo = tmp_path / "a", tmp_path / "b"
    main(["sito", "--dati", str(DATI_PROVA), "--uscita", str(primo)])
    main(["sito", "--dati", str(DATI_PROVA), "--uscita", str(secondo)])

    atteso = (primo / "elementi" / "fosforo.html").read_bytes()
    assert (secondo / "elementi" / "fosforo.html").read_bytes() == atteso


def test_comando_sito_segnala_i_dati_mancanti(tmp_path: Path) -> None:
    """Una cartella dati inesistente è un errore di dati, non un traceback."""
    from elements_caos.cli import main

    codice = main(["sito", "--dati", str(tmp_path / "vuoto"), "--uscita", str(tmp_path / "out")])

    assert codice == 2


# --- La scheda dei dati ------------------------------------------------------


def test_i_dati_sono_coppie_etichetta_valore() -> None:
    """I dati stanno in una lista di descrizione, non in una tabella.

    Una tabella a 390 px o si stringe fino a spezzare le parole o scorre in
    orizzontale: entrambe le cose sono state misurate sul sito con Quartz. Una
    lista di descrizione si impila e basta.
    """
    pagina = _pagina_fosforo()

    assert "<dl" in pagina
    assert "<table" not in pagina
    assert "<dt>Massa atomica</dt>" in pagina


def test_i_dati_riportano_i_valori_formattati() -> None:
    """I valori usano gli stessi formattatori del vault, non una seconda formattazione."""
    pagina = _pagina_fosforo()

    assert "30,974" in pagina  # massa con la virgola decimale italiana
    assert "Non metallo" in pagina  # categoria in italiano leggibile
    assert "3s²" in pagina  # configurazione con gli esponenti in apice


def test_gli_stati_di_ossidazione_portano_il_segno() -> None:
    """«+5» e «-3» sono la convenzione chimica, «5» e «3» no."""
    pagina = _pagina_fosforo()

    assert "+5" in pagina
    assert "-3" in pagina


# --- Le figure ---------------------------------------------------------------


def test_la_posizione_nella_tavola_e_una_griglia_html() -> None:
    """I vicini nella tavola sono testo vero, non un'immagine.

    In HTML sono selezionabili, leggibili da un lettore di schermo e si
    adattano alla larghezza: un diagramma Mermaid non fa nessuna delle tre.

    I dati di prova contengono un solo elemento, che quindi non ha vicini: la
    griglia si verifica sulla funzione che la costruisce.
    """
    from elements_caos.render.diagrammi import Vicini
    from elements_caos.sito.pagina import celle_vicine

    elementi = _elementi()
    celle = celle_vicine(Vicini(sopra=elementi[0], destra=elementi[0]))

    assert [cella["dove"] for cella in celle] == ["sopra", "destra"]
    assert celle[0]["relazione"] == "stesso gruppo"
    assert celle[1]["relazione"] == "stesso periodo"


def test_la_griglia_dei_vicini_ha_la_forma_della_tavola() -> None:
    """Sopra/sotto è il gruppo, sinistra/destra il periodo: la disposizione lo dice."""
    foglio = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "elements_caos"
        / "sito"
        / "statico"
        / "base.css"
    ).read_text(encoding="utf-8")

    assert "grid-template-areas" in foglio
    assert "sinistra centro destra" in foglio


def test_senza_vicini_la_sezione_non_compare() -> None:
    """L'idrogeno non ha nulla sopra: la sezione sparisce invece di restare vuota."""
    pagina = _pagina_fosforo()

    assert 'class="vicini"' not in pagina


def test_la_cronologia_della_scoperta_e_in_pagina() -> None:
    """Anno, luogo e scopritori: la scheda li mostra senza rimandare altrove."""
    pagina = _pagina_fosforo()

    assert "1669" in pagina
    assert "Amburgo" in pagina


def test_la_struttura_atomica_e_una_figura() -> None:
    """Lo schema a gusci è l'unica figura vera della scheda."""
    pagina = _pagina_fosforo()

    assert "atomo-Fosforo.svg" in pagina
    assert "<img" in pagina


def test_i_composti_e_i_loro_usi_sono_in_pagina() -> None:
    """Il diagramma dei composti diventa un elenco leggibile."""
    pagina = _pagina_fosforo()

    assert "Acido fosforico" in pagina
    assert "fertilizzanti" in pagina


def test_nessun_diagramma_da_rendere_nel_browser() -> None:
    """Niente Mermaid: nessuna libreria da scaricare, nessuno sfarfallio."""
    pagina = _pagina_fosforo()

    assert "mermaid" not in pagina.lower()


# --- La scheda è un capitolo (Task 36) ----------------------------------------


def _pagina_di(elemento: Elemento, elementi: list[Elemento]) -> str:
    """Rende la pagina di un elemento nel contesto dell'elenco dato."""
    scopritori = carica_scopritori(DATI_PROVA / "scopritori.yaml")
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")
    return rendi_elemento(costruisci_contesto(elemento, elementi, scopritori, epoche))


def test_il_capitolo_porta_il_colore_della_sua_epoca() -> None:
    """L'articolo dichiara l'epoca e la promuove ad accento della pagina."""
    pagina = _pagina_fosforo()

    assert 'class="capitolo epoca--alchimia contesto-epoca"' in pagina


def test_la_barra_fissa_dice_dove_sei_e_quanto_manca() -> None:
    """Posizione cronologica, epoca e minuti restano in vista mentre si legge."""
    pagina = _pagina_fosforo()

    barra = pagina[pagina.index('class="capitolo__barra"') : pagina.index("<h1")]
    assert "1° elemento scoperto" in barra
    assert "Alchimia e primo moderno" in barra
    assert 'id="capitolo-lettura"' in barra
    assert 'id="capitolo-progresso"' in barra


def test_il_racconto_viene_prima_dei_dati() -> None:
    """Hook, incipit e storia precedono i dati, che si svelano su richiesta."""
    pagina = _pagina_fosforo()

    assert pagina.index('class="elemento__hook"') < pagina.index("Storia della scoperta")
    assert pagina.index("Storia della scoperta") < pagina.index("<details")
    assert "<summary" in pagina
    dati = pagina[pagina.index("<details") :]
    assert "<dt>Massa atomica</dt>" in dati
    assert 'class="atomo"' in dati


def test_i_dati_della_scoperta_stanno_sotto_il_titolo() -> None:
    """Anno, luogo e scopritore sono l'occhiello della scheda, non una sezione a parte."""
    pagina = _pagina_fosforo()

    testa = pagina[pagina.index("<h1") : pagina.index('class="elemento__hook"')]
    assert "1669" in testa
    assert "Amburgo" in testa
    assert "Hennig Brand" in testa
    assert "<h2>La scoperta</h2>" not in pagina


def test_il_riquadro_della_storia_estesa_segue_il_fatto() -> None:
    """Compare solo quando l'approfondimento è scritto, e punta al suo URL."""
    from elements_caos.models import ContenutiEstesi

    elementi = _elementi()
    assert 'class="approfondimento' not in _pagina_di(elementi[0], elementi)

    con_estesi = elementi[0].model_copy(
        update={"contenuti_estesi": ContenutiEstesi(hook="La vicenda completa.")}
    )
    pagina = _pagina_di(con_estesi, [con_estesi, *elementi[1:]])
    assert 'class="approfondimento' in pagina
    assert url_approfondimento(con_estesi) in pagina
    assert url_approfondimento(con_estesi) == "elementi/fosforo-storia-estesa.html"


def test_la_catena_riporta_gli_anni_dei_vicini() -> None:
    """Precedente e successivo portano l'anno: si vede quanto tempo è passato."""
    dati_reali = Path(__file__).resolve().parents[1] / "data"
    elementi = carica_elementi(dati_reali / "elements")
    scopritori = carica_scopritori(dati_reali / "scopritori.yaml")
    epoche = carica_epoche(dati_reali / "epoche.yaml")
    from elements_caos.caricamento import ordina_per_scoperta
    from elements_caos.render.diagrammi import formatta_anno

    cronologia = ordina_per_scoperta(elementi)
    indice = next(i for i, e in enumerate(cronologia) if e.simbolo == "P")
    precedente, successivo = cronologia[indice - 1], cronologia[indice + 1]

    pagina = rendi_elemento(costruisci_contesto(cronologia[indice], elementi, scopritori, epoche))

    catena = pagina[pagina.index('class="elemento__catena"') : pagina.index("</nav>")]
    assert precedente.nome in catena
    assert formatta_anno(precedente.scoperta.anno) in catena
    assert successivo.nome in catena
    assert formatta_anno(successivo.scoperta.anno) in catena


def test_lo_script_del_capitolo_esiste_ed_e_collegato() -> None:
    """Avanzamento di lettura e rivelazione: migliorie, non condizioni."""
    pagina = _pagina_fosforo()
    statici = Path(__file__).resolve().parents[1] / "src" / "elements_caos" / "sito" / "statico"

    assert 'src="../statico/capitolo.js"' in pagina
    script = (statici / "capitolo.js").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in script
    assert "IntersectionObserver" in script
