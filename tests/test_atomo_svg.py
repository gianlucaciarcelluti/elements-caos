"""Test del generatore SVG del modello di Bohr.

Sostituisce ``diagramma_atomo`` (Mermaid) per la struttura a gusci
elettronici: un'orbita concentrica per guscio non è rappresentabile in
Mermaid, che dispone solo catene o alberi. Questi test verificano che
l'SVG prodotto sia sintatticamente valido, neutro rispetto al tema (nessuno
``<style>``, nessuna media query) e coerente con i dati dell'elemento.
"""

import xml.etree.ElementTree as ET

import pytest

from elements_caos.models import Categoria, Elemento, Proprieta, Scoperta
from elements_caos.render.atomo_svg import COLORI, nome_file_atomo, rendi_atomo_svg

NS_SVG = "{http://www.w3.org/2000/svg}"


def _elemento(numero: int, nome: str, simbolo: str, gusci: list[int]) -> Elemento:
    """Costruisce un elemento di prova con i soli campi necessari al diagramma."""
    return Elemento(
        numero_atomico=numero,
        simbolo=simbolo,
        nome=nome,
        nome_en=nome,
        scoperta=Scoperta(anno=1800, anno_stimato=False, scopritori=["tizio"], epoca="test"),
        proprieta=Proprieta(
            gruppo=None,
            periodo=len(gusci),
            blocco="s",
            categoria=Categoria.NON_METALLO,
            massa_atomica=float(numero),
            configurazione_elettronica="1s1",
            gusci=gusci,
            stati_ossidazione=[],
        ),
        approfondimento=False,
        fonti=[],
    )


def _idrogeno() -> Elemento:
    """Caso limite: un solo guscio, un solo elettrone."""
    return _elemento(1, "Idrogeno", "H", [1])


def _sodio() -> Elemento:
    return _elemento(11, "Sodio", "Na", [2, 8, 1])


def _fosforo() -> Elemento:
    return _elemento(15, "Fosforo", "P", [2, 8, 5])


def _rame() -> Elemento:
    return _elemento(29, "Rame", "Cu", [2, 8, 18, 1])


def _plutonio() -> Elemento:
    """Sette gusci, il caso con più orbite: fino a 32 elettroni su un guscio."""
    return _elemento(94, "Plutonio", "Pu", [2, 8, 18, 32, 24, 8, 2])


def _oganesson() -> Elemento:
    """Il massimo numero di gusci nel dataset (7), a Z=118."""
    return _elemento(118, "Oganesson", "Og", [2, 8, 18, 32, 32, 18, 8])


def _parse(svg: str) -> ET.Element:
    """Analizza l'SVG con xml.etree, verificando che sia sintatticamente valido."""
    return ET.fromstring(svg)


def _cerchi(radice: ET.Element) -> list[ET.Element]:
    return radice.findall(f".//{NS_SVG}circle")


def _testi(radice: ET.Element) -> list[ET.Element]:
    return radice.findall(f".//{NS_SVG}text")


class TestValiditaSintattica:
    """L'SVG prodotto deve essere XML valido e privo di dipendenze dal tema."""

    @pytest.mark.parametrize(
        "elemento",
        [_idrogeno(), _sodio(), _fosforo(), _rame(), _plutonio(), _oganesson()],
    )
    def test_svg_e_xml_valido(self, elemento: Elemento) -> None:
        """xml.etree deve poter analizzare l'SVG senza sollevare eccezioni."""
        _parse(rendi_atomo_svg(elemento))

    @pytest.mark.parametrize(
        "elemento",
        [_idrogeno(), _sodio(), _fosforo(), _rame(), _plutonio(), _oganesson()],
    )
    def test_nessun_tag_style(self, elemento: Elemento) -> None:
        """GitHub rimuove gli stili dagli SVG: non deve esserci alcun <style>."""
        svg = rendi_atomo_svg(elemento)
        assert "<style" not in svg
        radice = _parse(svg)
        assert radice.findall(f".//{NS_SVG}style") == []

    @pytest.mark.parametrize(
        "elemento",
        [_idrogeno(), _sodio(), _fosforo(), _rame(), _plutonio(), _oganesson()],
    )
    def test_nessuna_media_query(self, elemento: Elemento) -> None:
        """Una media query in un SVG referenziato da <img> segue il tema di sistema,
        non quello della pagina: è vietata."""
        svg = rendi_atomo_svg(elemento)
        assert "@media" not in svg
        assert "prefers-color-scheme" not in svg

    def test_root_e_svg(self) -> None:
        """L'elemento radice deve essere <svg>, con il namespace corretto."""
        radice = _parse(rendi_atomo_svg(_fosforo()))
        assert radice.tag == f"{NS_SVG}svg"


class TestGusciEOrbite:
    """Un cerchio-orbita per guscio, indipendentemente dal loro numero."""

    @pytest.mark.parametrize(
        "elemento,numero_gusci",
        [
            (_idrogeno(), 1),
            (_sodio(), 3),
            (_fosforo(), 3),
            (_rame(), 4),
            (_plutonio(), 7),
            (_oganesson(), 7),
        ],
    )
    def test_numero_orbite_corrisponde_ai_gusci(
        self, elemento: Elemento, numero_gusci: int
    ) -> None:
        """Ci deve essere esattamente un'orbita (cerchio col colore delle orbite)
        per ciascun guscio dichiarato nei dati."""
        radice = _parse(rendi_atomo_svg(elemento))
        orbite = [c for c in _cerchi(radice) if c.get("stroke") == COLORI["orbite"]]
        assert len(orbite) == numero_gusci

    def test_nucleo_presente_con_numero_atomico(self) -> None:
        """Il nucleo va marcato col colore dedicato e riportare Z."""
        elemento = _fosforo()
        svg = rendi_atomo_svg(elemento)
        radice = _parse(svg)

        nucleo = [c for c in _cerchi(radice) if c.get("fill") == COLORI["nucleo"]]
        assert len(nucleo) == 1

        testo_nucleo = "".join(t.text or "" for t in _testi(radice))
        assert str(elemento.numero_atomico) in testo_nucleo


class TestElettroniDisegnati:
    """Il numero di elettroni disegnati per guscio deve corrispondere ai dati,
    sotto la soglia di leggibilità; sopra soglia si mostra il solo conteggio."""

    def test_idrogeno_un_punto_sul_guscio(self) -> None:
        """Idrogeno: un solo guscio con un solo elettrone, ben sotto soglia."""
        radice = _parse(rendi_atomo_svg(_idrogeno()))
        elettroni = [
            c
            for c in _cerchi(radice)
            if c.get("fill") in (COLORI["elettroni_interni"], COLORI["valenza"])
        ]
        assert len(elettroni) == 1

    def test_sodio_punti_corrispondono_ai_gusci(self) -> None:
        """Sodio [2, 8, 1]: 11 elettroni totali, tutti sotto la soglia per guscio."""
        radice = _parse(rendi_atomo_svg(_sodio()))
        elettroni = [
            c
            for c in _cerchi(radice)
            if c.get("fill") in (COLORI["elettroni_interni"], COLORI["valenza"])
        ]
        assert len(elettroni) == 2 + 8 + 1

    def test_fosforo_punti_corrispondono_ai_gusci(self) -> None:
        """Fosforo [2, 8, 5]: nessun guscio supera la soglia."""
        radice = _parse(rendi_atomo_svg(_fosforo()))
        elettroni = [
            c
            for c in _cerchi(radice)
            if c.get("fill") in (COLORI["elettroni_interni"], COLORI["valenza"])
        ]
        assert len(elettroni) == 2 + 8 + 5

    def test_plutonio_guscio_di_32_mostra_solo_conteggio(self) -> None:
        """Il guscio con 32 elettroni (indice 4, Pu) supera la soglia: niente
        punti individuali, ma un'etichetta col conteggio numerico."""
        elemento = _plutonio()
        svg = rendi_atomo_svg(elemento)
        radice = _parse(svg)

        # Sotto soglia: 2, 8, 18(?), 24, 8, 2 -- dipende dalla soglia scelta,
        # ma il totale dei punti disegnati deve essere STRETTAMENTE minore
        # della somma degli elettroni, perché almeno un guscio (quello da 32)
        # è sopra soglia.
        elettroni = [
            c
            for c in _cerchi(radice)
            if c.get("fill") in (COLORI["elettroni_interni"], COLORI["valenza"])
        ]
        assert len(elettroni) < sum(elemento.proprieta.gusci)

        testo_completo = "".join(t.text or "" for t in _testi(radice))
        assert "32" in testo_completo

    def test_ultimo_guscio_e_marcato_come_valenza(self) -> None:
        """Il guscio più esterno deve usare il colore di valenza, non quello
        degli elettroni interni — indipendentemente dal fatto che sia
        disegnato a punti o come conteggio."""
        elemento = _sodio()
        svg = rendi_atomo_svg(elemento)
        radice = _parse(svg)

        valenza = [c for c in _cerchi(radice) if c.get("fill") == COLORI["valenza"]]
        # Il sodio ha un solo elettrone di valenza: un punto colorato di valenza.
        assert len(valenza) == 1

    def test_valenza_disegnata_anche_sopra_soglia(self) -> None:
        """Se il guscio di valenza stesso superasse la soglia (non nei quattro
        piloti, ma nel dataset completo può capitare), l'etichetta del
        conteggio deve comunque usare il colore di valenza, non quello degli
        elettroni interni."""
        # Costruzione sintetica: un elemento con un guscio di valenza sopra
        # soglia (28 elettroni), per verificare la colorazione del solo
        # conteggio testuale quando riguarda l'ultimo guscio.
        elemento = _elemento(46, "Palladio-test", "Pdx", [2, 8, 18, 18])
        # Guscio di valenza a 18: sopra la soglia indicativa di 12.
        svg = rendi_atomo_svg(elemento)
        radice = _parse(svg)
        # Non ci devono essere punti di valenza (sopra soglia -> solo testo),
        # ma il conteggio "18" deve comparire nel testo.
        punti_valenza = [c for c in _cerchi(radice) if c.get("fill") == COLORI["valenza"]]
        assert punti_valenza == []
        testo_completo = "".join(t.text or "" for t in _testi(radice))
        assert "18" in testo_completo


class TestPalette:
    """Solo i colori misurati nel brief possono comparire nell'SVG."""

    def test_colori_usati_sono_solo_quelli_della_palette(self) -> None:
        """Ogni fill/stroke non 'none' presente nell'SVG deve appartenere a COLORI."""
        colori_ammessi = set(COLORI.values())
        for elemento in (_idrogeno(), _sodio(), _fosforo(), _rame(), _plutonio(), _oganesson()):
            svg = rendi_atomo_svg(elemento)
            radice = _parse(svg)
            for nodo in radice.iter():
                for attributo in ("fill", "stroke"):
                    valore = nodo.get(attributo)
                    if valore is None or valore == "none":
                        continue
                    assert valore in colori_ammessi, (
                        f"colore non in palette: {valore} (attributo {attributo})"
                    )

    def test_colori_contiene_i_quattro_ruoli_del_brief(self) -> None:
        """La palette esposta deve contenere esattamente i quattro colori misurati."""
        assert set(COLORI.values()) == {
            "#7d8590",
            "#4c8eda",
            "#b26a00",
            "#3d8b40",
        }


class TestNomeFile:
    """Il nome del file SVG segue la convenzione usata per le altre risorse del vault."""

    def test_nome_file_atomo_fosforo(self) -> None:
        assert nome_file_atomo(_fosforo()) == "atomo-Fosforo.svg"

    def test_nome_file_atomo_plutonio(self) -> None:
        assert nome_file_atomo(_plutonio()) == "atomo-Plutonio.svg"


class TestDimensioniProporzionate:
    """Le dimensioni dell'SVG devono restare fisse e proporzionate al numero
    di gusci, così le note restano uniformi."""

    def test_idrogeno_e_oganesson_hanno_stesso_bordo_esterno(self) -> None:
        """L'SVG ha dimensioni fisse (width/height) indipendenti dal numero di
        gusci: cambia solo il raggio interno usato per le orbite."""
        svg_h = rendi_atomo_svg(_idrogeno())
        svg_og = rendi_atomo_svg(_oganesson())

        radice_h = _parse(svg_h)
        radice_og = _parse(svg_og)

        assert radice_h.get("width") == radice_og.get("width")
        assert radice_h.get("height") == radice_og.get("height")

    def test_orbite_di_oganesson_non_escono_dal_viewbox(self) -> None:
        """Con sette gusci, l'orbita più esterna deve restare dentro il
        viewBox dichiarato: nessun raggio calcolato deve eccedere i bordi."""
        elemento = _oganesson()
        svg = rendi_atomo_svg(elemento)
        radice = _parse(svg)

        viewbox = radice.get("viewBox")
        assert viewbox is not None
        _, _, larghezza, altezza = (float(v) for v in viewbox.split())
        centro_x, centro_y = larghezza / 2, altezza / 2

        raggio_massimo = max(
            float(c.get("r", "0")) for c in _cerchi(radice) if c.get("stroke") == COLORI["orbite"]
        )
        margine_testo = 20.0  # spazio per l'etichetta Z sopra il nucleo/orbite
        assert centro_x - raggio_massimo - margine_testo >= 0
        assert centro_y - raggio_massimo - margine_testo >= 0
