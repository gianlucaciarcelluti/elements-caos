"""Test della composizione della nota Markdown di un elemento."""

from datetime import date
from pathlib import Path

import pytest
import yaml

from elements_caos.caricamento import carica_elementi, carica_epoche, carica_scopritori
from elements_caos.models import Contenuti, Elemento
from elements_caos.render.note import (
    _tag_periodo_storico,
    costruisci_contesto,
    formatta_configurazione_elettronica,
    formatta_decimale,
    kelvin_in_celsius,
    nome_file_nota,
    rendi_nota,
)

DATI_PROVA = Path(__file__).parent / "dati_prova"


def _nota_di(elemento: Elemento, elementi: list[Elemento]) -> str:
    """Genera la nota di un elemento nel contesto dell'intero elenco fornito."""
    scopritori = carica_scopritori(DATI_PROVA / "scopritori.yaml")
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")
    contesto = costruisci_contesto(elemento, elementi, scopritori, epoche)
    return rendi_nota(contesto)


def _nota_fosforo() -> str:
    """Genera la nota del fosforo a partire dai dati di prova."""
    elementi = carica_elementi(DATI_PROVA / "elements")
    return _nota_di(elementi[0], elementi)


def _frontmatter(nota: str) -> dict[str, object]:
    """Estrae e deserializza il frontmatter YAML della nota."""
    assert nota.startswith("---\n")
    chiusura = nota.index("\n---\n", 4)
    return yaml.safe_load(nota[4:chiusura])


def test_nota_inizia_con_frontmatter() -> None:
    """La nota deve aprirsi con un frontmatter YAML delimitato da tre trattini."""
    nota = _nota_fosforo()

    assert nota.startswith("---\n")
    assert "\n---\n" in nota


def test_frontmatter_contiene_i_campi_previsti() -> None:
    """Il frontmatter espone i campi piatti richiesti da Dataview."""
    dati = _frontmatter(_nota_fosforo())

    assert dati["titolo"] == "Fosforo"
    assert dati["simbolo"] == "P"
    assert dati["numero_atomico"] == 15
    assert dati["anno_scoperta"] == 1669
    assert dati["anno_stimato"] is False
    assert dati["scopritori"] == ["Hennig Brand"]
    assert dati["epoca"] == "Alchimia e primo moderno"
    assert dati["categoria"] == "non_metallo"
    assert dati["gruppo"] == 15
    assert dati["periodo"] == 3
    assert dati["ha_approfondimento"] is True


def test_frontmatter_calcola_tempo_lettura() -> None:
    """Il tempo di lettura è calcolato dalle parole reali, non stimato a priori."""
    dati = _frontmatter(_nota_fosforo())

    assert isinstance(dati["tempo_lettura"], int)
    assert dati["tempo_lettura"] >= 1


def test_frontmatter_contiene_tag_di_epoca_e_secolo() -> None:
    """I tag includono la categoria, l'epoca e il secolo di scoperta."""
    dati = _frontmatter(_nota_fosforo())
    tags = dati["tags"]

    assert "elemento" in tags
    assert "epoca/alchimia" in tags
    assert "secolo/XVII" in tags


@pytest.mark.parametrize(
    ("nome", "anno", "atteso"),
    [
        ("Oro", -40000, "millennio/40aC"),
        ("Rame", -9000, "millennio/9aC"),
        ("Stagno", -3500, "millennio/4aC"),
        ("Mercurio", -1500, "secolo/XVaC"),
        ("Platino", -600, "secolo/VIaC"),
        ("Arsenico", 300, "secolo/III"),
        ("Fosforo", 1669, "secolo/XVII"),
    ],
)
def test_tag_periodo_storico_sui_casi_reali(nome: str, anno: int, atteso: str) -> None:
    """Il tag cronologico usa i millenni per la preistoria, i secoli altrimenti.

    Gli anni scelti coprono elementi realmente presenti nel vault, dall'oro
    dell'antichità più remota (-40000) al fosforo del 1669: la soglia dei
    3000 a.C. separa le date preistoriche, dove il secolo in cifre romane
    produce numerali illeggibili, da quelle storiche, dove il secolo resta
    la convenzione naturale.
    """
    assert _tag_periodo_storico(anno) == atteso, nome


def test_tag_periodo_storico_soglia_millennio() -> None:
    """La soglia dei 3000 a.C. si comporta correttamente sui due lati.

    Esattamente 3000 a.C. non è "anteriore" al 3000 a.C.: resta nel ramo dei
    secoli. Un anno di poco più antico (3001 a.C.) passa invece ai millenni.
    """
    assert _tag_periodo_storico(-3000) == "secolo/XXXaC"
    assert _tag_periodo_storico(-3001) == "millennio/4aC"


def test_frontmatter_include_alias() -> None:
    """Gli alias permettono di raggiungere la nota dal simbolo e dal nome inglese."""
    dati = _frontmatter(_nota_fosforo())

    assert "P" in dati["aliases"]
    assert "Phosphorus" in dati["aliases"]


def test_nota_contiene_tre_diagrammi_mermaid_e_lo_svg_atomico() -> None:
    """Tre diagrammi restano Mermaid; la struttura atomica è un embed SVG.

    Il diagramma atomico è stato sostituito da un SVG generato (Task 12b):
    Mermaid non ha un tipo di diagramma a cerchi concentrici, necessario per
    rappresentare i gusci elettronici. L'SVG va referenziato come file
    (``![[...]]``), mai incorporato inline: GitHub ignora l'SVG inline nel
    Markdown.
    """
    nota = _nota_fosforo()

    assert nota.count("```mermaid") == 3
    assert "![[atomo-Fosforo.svg]]" in nota


def test_nota_contiene_le_sezioni_previste() -> None:
    """La nota espone le intestazioni delle sezioni narrative."""
    nota = _nota_fosforo()

    for intestazione in ("## Storia della scoperta", "## Curiosità"):
        assert intestazione in nota


def test_nota_riporta_il_testo_dei_beat() -> None:
    """Il testo dei beat compare nel corpo della nota."""
    nota = _nota_fosforo()

    assert "Ad Amburgo, nel 1669" in nota


def test_nota_marca_i_beat_tradizionali() -> None:
    """Un beat tradizionale è introdotto dalla formula di cautela."""
    assert "*Per tradizione:*" in _nota_fosforo()


def test_nota_converte_le_temperature_in_celsius() -> None:
    """Le temperature, in Kelvin nei dati, sono mostrate anche in gradi Celsius.

    Il punto di fusione del fosforo nei dati di prova è 317.3 K, che
    corrisponde esattamente a 44.15 °C: un valore a metà fra due decimi, che
    con arrotondamento corretto (ROUND_HALF_UP) diventa 44,2 °C, non 44,1.
    Il valore atteso è verificato per intero, unità compresa, e non come
    sottostringa: "44,1" o "44.1" sarebbero passati anche per un valore come
    "144,1" comparso altrove nella nota, senza verificare davvero la
    conversione.
    """
    nota = _nota_fosforo()

    assert "| Punto di fusione | 44,2 °C |" in nota


def test_kelvin_in_celsius_arrotonda_un_valore_esatto_a_meta() -> None:
    """Un valore Kelvin la cui differenza è esattamente a metà fra due decimi.

    317.3 K vale esattamente 44.15 °C. Sottraendo in virgola mobile puro,
    l'errore di rappresentazione (317.3 - 273.15 = 44.150000000000034 in
    float) sposta il valore oltre la soglia nella direzione sbagliata e lo fa
    arrotondare a 44,1 anziché 44,2. Il calcolo su ``Decimal`` costruito dalla
    rappresentazione testuale del dato sorgente, con ROUND_HALF_UP, deve dare
    la cifra corretta.
    """
    assert kelvin_in_celsius(317.3) == "44,2 °C"


def test_kelvin_in_celsius_gestisce_temperature_negative() -> None:
    """Una temperatura sotto lo zero Celsius (punto di ebollizione dell'azoto).

    77.36 K corrisponde a -195.79 °C, che arrotondato con ROUND_HALF_UP deve
    dare -195,8 °C: verifica che l'arrotondamento funzioni correttamente
    anche quando il valore Celsius è negativo, non solo per i positivi.
    """
    assert kelvin_in_celsius(77.36) == "-195,8 °C"


def test_kelvin_in_celsius_dato_assente() -> None:
    """L'assenza del dato deve produrre un messaggio esplicito, non un errore."""
    assert kelvin_in_celsius(None) == "dato non disponibile"


def test_nota_mostra_i_numeri_decimali_con_la_virgola() -> None:
    """Massa atomica e densità devono usare la virgola come separatore decimale.

    In italiano il separatore decimale è la virgola, e la stessa tabella dei
    dati fisico-chimici mostra già le temperature in questo formato: un altro
    separatore per massa atomica o densità sarebbe un'incoerenza visibile a
    poche righe di distanza, nella stessa tabella.
    """
    nota = _nota_fosforo()

    assert "| Massa atomica | 30,974 u |" in nota
    assert "| Densità | 1,823 g/cm³ |" in nota
    assert "30.974" not in nota
    assert "1.823" not in nota


def test_formatta_decimale_non_altera_un_numero_intero() -> None:
    """Un numero senza parte decimale non deve acquisire una virgola spuria."""
    assert formatta_decimale(15) == "15"


def test_formatta_configurazione_elettronica_esponente_singola_cifra() -> None:
    """Un esponente a una cifra diventa il corrispondente apice Unicode."""
    assert formatta_configurazione_elettronica("[Ne] 3s2 3p3") == "[Ne] 3s² 3p³"


def test_formatta_configurazione_elettronica_esponente_doppia_cifra() -> None:
    """Un esponente a due cifre (es. 14 elettroni in un sottolivello f).

    La configurazione del dubnio, [Rn] 5f14 6d3 7s2, verifica che la regex
    catturi l'intero numero di elettroni e non solo la prima cifra.
    """
    assert formatta_configurazione_elettronica("[Rn] 5f14 6d3 7s2") == "[Rn] 5f¹⁴ 6d³ 7s²"


def test_nota_riporta_le_fonti() -> None:
    """Le fonti consultate sono elencate in fondo alla nota."""
    nota = _nota_fosforo()

    assert "## Fonti" in nota
    assert "https://esempio.it/fosforo" in nota


def test_nota_codifica_le_parentesi_negli_url_delle_fonti() -> None:
    """Un URL con parentesi non deve spezzare il collegamento Markdown.

    Wikipedia usa le parentesi per disambiguare i titoli omonimi
    (``Henry_Roscoe_(chemist)``): lasciate com'erano chiudevano in anticipo la
    destinazione del link, e metà dell'indirizzo finiva stampata come testo.
    """
    from elements_caos.models import Fonte

    elementi = carica_elementi(DATI_PROVA / "elements")
    fosforo = elementi[0].model_copy(deep=True)
    fosforo.fonti = [
        Fonte(
            url="https://en.wikipedia.org/wiki/Henry_Roscoe_(chemist)",
            titolo="Sir Henry Enfield Roscoe",
            consultata=date(2026, 9, 8),
        )
    ]

    nota = _nota_di(fosforo, elementi)

    assert "https://en.wikipedia.org/wiki/Henry_Roscoe_%28chemist%29" in nota
    assert "Henry_Roscoe_(chemist)" not in nota


def test_nota_non_collega_approfondimento_senza_contenuti_estesi() -> None:
    """``approfondimento=True`` da solo non basta: senza ``contenuti_estesi``
    scritti la nota non deve linkare una pagina che non esiste ancora.

    Il fosforo dei dati di prova ha ``approfondimento: true`` ma nessun
    ``contenuti_estesi``: è esattamente il caso che, prima di questa
    correzione, produceva un wikilink rotto in ogni vault generato prima che
    l'approfondimento venisse effettivamente scritto.
    """
    elementi = carica_elementi(DATI_PROVA / "elements")
    assert elementi[0].approfondimento is True
    assert elementi[0].contenuti_estesi is None

    assert "[[Fosforo — storia estesa]]" not in _nota_fosforo()


def test_nota_collega_l_approfondimento_quando_scritto() -> None:
    """Quando ``contenuti_estesi`` è valorizzato, la nota base vi rimanda.

    Il link segue il fatto (l'approfondimento è stato scritto), non
    l'intenzione dichiarata da ``approfondimento``.
    """
    elementi = carica_elementi(DATI_PROVA / "elements")
    con_estesi = elementi[0].model_copy(
        update={"contenuti_estesi": Contenuti(hook="Un approfondimento più lungo.")}
    )
    elementi_aggiornati = [con_estesi, *elementi[1:]]

    assert "[[Fosforo — storia estesa]]" in _nota_di(con_estesi, elementi_aggiornati)


def test_nota_collega_lo_scopritore() -> None:
    """La nota rimanda alla pagina dello scopritore tramite wikilink."""
    assert "[[Hennig Brand]]" in _nota_fosforo()


def test_nota_collega_l_epoca() -> None:
    """La nota rimanda alla pagina dell'epoca storica."""
    assert "[[Alchimia e primo moderno]]" in _nota_fosforo()


def test_nome_file_nota() -> None:
    """Il nome del file della nota corrisponde al nome italiano dell'elemento."""
    elementi = carica_elementi(DATI_PROVA / "elements")

    assert nome_file_nota(elementi[0]) == "Fosforo.md"


def test_nota_e_deterministica() -> None:
    """Due generazioni consecutive devono produrre esattamente lo stesso testo.

    È la proprietà su cui si regge il controllo di CI che impedisce le
    modifiche a mano alle note generate.
    """
    assert _nota_fosforo() == _nota_fosforo()


def test_stato_di_ossidazione_zero_si_stampa_senza_segno() -> None:
    """Lo zero si stampa "0": non ha segno, e "+0" non è notazione valida.

    Il formato ``{:+d}`` applicato indistintamente produceva "+0" (Ruling 46b).
    Lo stato zero non è un caso di scuola: compare per esempio nei metalli dei
    complessi carbonilici e nella fascia completa del carbonio.
    """
    elementi = carica_elementi(DATI_PROVA / "elements")
    fosforo = elementi[0]
    fosforo.proprieta.stati_ossidazione = [-1, 0, 1]

    nota = _nota_di(fosforo, elementi)

    assert "| Stati di ossidazione | -1, 0, +1 |" in nota


def test_riquadro_della_controversia_si_intitola_questione_aperta() -> None:
    """L'intestazione del riquadro copre sia le paternità sia le datazioni.

    Il campo ``controversia`` è previsto dalla spec per entrambi gli usi, ma
    nei dati reali è sempre e solo una datazione discussa: intitolare il
    riquadro "Paternità contesa" nominava l'unico dei due casi che non si
    verifica mai (Ruling 48).
    """
    elementi = carica_elementi(DATI_PROVA / "elements")
    fosforo = elementi[0]
    fosforo.scoperta.controversia = "Le fonti divergono sulla datazione."

    nota = _nota_di(fosforo, elementi)

    assert "> [!warning] Questione aperta" in nota
    assert "Paternità contesa" not in nota


def test_nota_accorda_l_etichetta_degli_scopritori_al_numero() -> None:
    """L'etichetta segue il numero dei nomi: "Scopritore" con uno, "Scopritori" con più.

    Trentatré elementi su 118 hanno più di uno scopritore, e il numero cresce
    man mano che si espandono le attribuzioni compresse in «et al.»: il boro
    ne elenca quattro, e "Scopritore: A, B, C, D" è un errore grammaticale
    nella riga di chiusura di ogni nota a paternità multipla.
    """
    from elements_caos.models import Scopritore

    elementi = carica_elementi(DATI_PROVA / "elements")
    fosforo = elementi[0]
    assert len(fosforo.scoperta.scopritori) == 1
    assert "· Scopritore: " in _nota_di(fosforo, elementi)

    condiviso = fosforo.model_copy(deep=True)
    condiviso.scoperta.scopritori = ["hennig-brand", "seconda-persona"]
    scopritori = carica_scopritori(DATI_PROVA / "scopritori.yaml")
    scopritori["seconda-persona"] = Scopritore(id="seconda-persona", nome="Seconda Persona")
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")

    nota = rendi_nota(costruisci_contesto(condiviso, elementi, scopritori, epoche))

    assert "· Scopritori: " in nota
    assert "· Scopritore: " not in nota
