"""Test del caricamento dei dati dagli archivi YAML."""

from pathlib import Path

import pytest

from elements_caos.caricamento import (
    ErroreCaricamento,
    carica_elementi,
    carica_elemento,
    carica_epoche,
    carica_scopritori,
    ordina_per_scoperta,
)
from elements_caos.models import Categoria, Sezione

DATI_PROVA = Path(__file__).parent / "dati_prova"


def test_carica_elemento_singolo() -> None:
    """Un file YAML valido deve produrre un elemento con i campi popolati."""
    elemento = carica_elemento(DATI_PROVA / "elements" / "015-fosforo.yaml")

    assert elemento.numero_atomico == 15
    assert elemento.nome == "Fosforo"
    assert elemento.proprieta.categoria is Categoria.NON_METALLO
    assert elemento.scoperta.anno == 1669
    assert elemento.approfondimento is True


def test_carica_elemento_legge_i_beat() -> None:
    """I beat narrativi devono essere caricati con sezione e attendibilità."""
    elemento = carica_elemento(DATI_PROVA / "elements" / "015-fosforo.yaml")

    assert elemento.contenuti is not None
    storia = elemento.contenuti.beats_per_sezione(Sezione.STORIA)
    assert len(storia) == 1
    assert storia[0].id == "contesto"
    assert storia[0].visual == "Ritratto di Brand"


def test_carica_elemento_inesistente_solleva_errore() -> None:
    """Un percorso inesistente deve produrre un errore esplicito in italiano."""
    with pytest.raises(ErroreCaricamento, match="non trovato"):
        carica_elemento(DATI_PROVA / "elements" / "999-inesistente.yaml")


def test_carica_elemento_malformato_solleva_errore(tmp_path: Path) -> None:
    """Un file YAML che viola lo schema deve produrre un errore che cita il file."""
    file_rotto = tmp_path / "001-rotto.yaml"
    file_rotto.write_text("numero_atomico: 999\nsimbolo: X\n", encoding="utf-8")

    with pytest.raises(ErroreCaricamento, match="001-rotto.yaml"):
        carica_elemento(file_rotto)


def test_carica_elementi_da_cartella() -> None:
    """Il caricamento della cartella deve restituire gli elementi presenti."""
    elementi = carica_elementi(DATI_PROVA / "elements")

    assert len(elementi) == 1
    assert elementi[0].numero_atomico == 15


def test_carica_scopritori_indicizzati_per_id() -> None:
    """Gli scopritori devono essere restituiti in un dizionario indicizzato per id."""
    scopritori = carica_scopritori(DATI_PROVA / "scopritori.yaml")

    assert "hennig-brand" in scopritori
    assert scopritori["hennig-brand"].nome == "Hennig Brand"
    assert scopritori["hennig-brand"].ritratto is not None
    assert scopritori["hennig-brand"].ritratto.licenza == "PD-old-100-expired"


def test_carica_epoche_indicizzate_per_id() -> None:
    """Le epoche devono essere restituite in un dizionario indicizzato per id."""
    epoche = carica_epoche(DATI_PROVA / "epoche.yaml")

    assert set(epoche) == {"antichita", "alchimia"}
    assert epoche["alchimia"].anno_inizio == 1500


def test_carica_scopritori_file_vuoto_solleva_errore(tmp_path: Path) -> None:
    """Un file YAML vuoto (None) deve produrre un ErroreCaricamento che cita il file."""
    file_vuoto = tmp_path / "scopritori-vuoto.yaml"
    file_vuoto.write_text("", encoding="utf-8")

    with pytest.raises(ErroreCaricamento, match="scopritori-vuoto.yaml"):
        carica_scopritori(file_vuoto)


def test_carica_scopritori_mapping_solleva_errore_struttura(tmp_path: Path) -> None:
    """Un file YAML con mapping invece di lista deve produrre un ErroreCaricamento."""
    file_mapping = tmp_path / "scopritori-mapping.yaml"
    file_mapping.write_text("id: test\nnome: Test\n", encoding="utf-8")

    with pytest.raises(ErroreCaricamento, match="atteso un elenco.*scopritori-mapping.yaml.*dict"):
        carica_scopritori(file_mapping)


def test_carica_scopritori_lista_scalari_solleva_errore_validazione(tmp_path: Path) -> None:
    """Una lista di scalari deve fallire nella validazione Pydantic."""
    file_scalari = tmp_path / "scopritori-scalari.yaml"
    file_scalari.write_text("- 1\n- 2\n", encoding="utf-8")

    with pytest.raises(ErroreCaricamento, match="dati non validi.*scopritori-scalari.yaml"):
        carica_scopritori(file_scalari)


def test_carica_epoche_file_vuoto_solleva_errore(tmp_path: Path) -> None:
    """Un file YAML vuoto (None) deve produrre un ErroreCaricamento che cita il file."""
    file_vuoto = tmp_path / "epoche-vuoto.yaml"
    file_vuoto.write_text("", encoding="utf-8")

    with pytest.raises(ErroreCaricamento, match="epoche-vuoto.yaml"):
        carica_epoche(file_vuoto)


def test_carica_epoche_mapping_solleva_errore_struttura(tmp_path: Path) -> None:
    """Un file YAML con mapping invece di lista deve produrre un ErroreCaricamento."""
    file_mapping = tmp_path / "epoche-mapping.yaml"
    file_mapping.write_text("id: test\nnome: Test\n", encoding="utf-8")

    with pytest.raises(ErroreCaricamento, match="atteso un elenco.*epoche-mapping.yaml.*dict"):
        carica_epoche(file_mapping)


def test_carica_epoche_lista_scalari_solleva_errore_validazione(tmp_path: Path) -> None:
    """Una lista di scalari deve fallire nella validazione Pydantic."""
    file_scalari = tmp_path / "epoche-scalari.yaml"
    file_scalari.write_text("- 1\n- 2\n", encoding="utf-8")

    with pytest.raises(ErroreCaricamento, match="dati non validi.*epoche-scalari.yaml"):
        carica_epoche(file_scalari)


def test_ordina_per_scoperta_usa_anno_poi_numero_atomico() -> None:
    """L'ordinamento cronologico usa l'anno; a parità di anno, il numero atomico."""
    from elements_caos.models import Elemento, Proprieta, Scoperta

    def _crea(numero: int, anno: int, gusci: list[int]) -> Elemento:
        return Elemento(
            numero_atomico=numero,
            simbolo="X",
            nome=f"Elemento{numero}",
            nome_en=f"Element{numero}",
            scoperta=Scoperta(
                anno=anno,
                anno_stimato=anno < 1500,
                scopritori=[],
                epoca="test",
            ),
            proprieta=Proprieta(
                gruppo=1,
                periodo=1,
                blocco="s",
                categoria=Categoria.NON_METALLO,
                massa_atomica=1.0,
                configurazione_elettronica="1s1",
                gusci=gusci,
                stati_ossidazione=[],
            ),
            approfondimento=False,
            fonti=[],
        )

    elementi = [
        _crea(3, 1817, [2, 1]),
        _crea(1, 1766, [1]),
        _crea(2, 1766, [2]),
    ]

    ordinati = ordina_per_scoperta(elementi)

    assert [e.numero_atomico for e in ordinati] == [1, 2, 3]


def test_carica_scopritori_lista_vuota_e_accettata(tmp_path: Path) -> None:
    """Un elenco vuoto e' un dato legittimo, non un errore.

    Distingue il file malformato (che va rifiutato) dal file che dichiara
    esplicitamente di non contenere voci: il secondo e' valido e produce un
    dizionario vuoto.
    """
    percorso = tmp_path / "scopritori.yaml"
    percorso.write_text("[]\n", encoding="utf-8")

    assert carica_scopritori(percorso) == {}


def test_carica_epoche_lista_vuota_e_accettata(tmp_path: Path) -> None:
    """Un elenco vuoto di epoche e' un dato legittimo, non un errore."""
    percorso = tmp_path / "epoche.yaml"
    percorso.write_text("[]\n", encoding="utf-8")

    assert carica_epoche(percorso) == {}
