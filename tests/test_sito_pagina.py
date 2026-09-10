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
