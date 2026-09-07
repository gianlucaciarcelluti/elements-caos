"""Test di integrità della cronologia di riferimento."""

from elements_caos.ingest.cronologia import CRONOLOGIA


def test_cronologia_copre_tutti_gli_elementi() -> None:
    """La cronologia deve contenere esattamente i 118 elementi noti."""
    numeri = sorted(voce.numero_atomico for voce in CRONOLOGIA)

    assert numeri == list(range(1, 119))


def test_cronologia_senza_duplicati() -> None:
    """Nessun elemento può comparire due volte nella cronologia."""
    numeri = [voce.numero_atomico for voce in CRONOLOGIA]

    assert len(numeri) == len(set(numeri))


def test_date_antiche_sono_marcate_come_stimate() -> None:
    """Ogni data anteriore al 1500 deve essere dichiarata come stima."""
    for voce in CRONOLOGIA:
        if voce.anno < 1500:
            assert voce.anno_stimato, f"elemento {voce.numero_atomico}: stima non dichiarata"


def test_epoche_sono_fra_quelle_definite() -> None:
    """Ogni voce deve riferirsi a una delle sei epoche previste."""
    epoche_valide = {
        "antichita",
        "alchimia",
        "pneumatica",
        "elettrolisi",
        "spettroscopia",
        "nucleare",
    }

    for voce in CRONOLOGIA:
        assert voce.epoca in epoche_valide, f"epoca ignota: {voce.epoca}"


def test_isolamento_non_precede_la_scoperta() -> None:
    """L'anno di isolamento, se indicato, non può precedere quello di scoperta."""
    for voce in CRONOLOGIA:
        if voce.isolamento_anno is not None:
            assert voce.isolamento_anno >= voce.anno, (
                f"elemento {voce.numero_atomico}: isolamento prima della scoperta"
            )
