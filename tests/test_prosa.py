"""Test della composizione dei beat narrativi in prosa continua."""

from elements_caos.models import Attendibilita, Beat, Contenuti, Sezione
from elements_caos.render.prosa import (
    componi_sezione,
    conta_parole,
    tempo_lettura_minuti,
)


def _contenuti(*beats: Beat) -> Contenuti:
    """Costruisce contenuti di prova a partire dai beat indicati."""
    return Contenuti(hook="Gancio di prova.", beats=list(beats))


def test_componi_sezione_unisce_i_beat_in_paragrafi() -> None:
    """I beat della stessa sezione diventano paragrafi separati da riga vuota."""
    contenuti = _contenuti(
        Beat(
            id="uno",
            sezione=Sezione.STORIA,
            testo="Primo paragrafo.",
            attendibilita=Attendibilita.DOCUMENTATO,
        ),
        Beat(
            id="due",
            sezione=Sezione.STORIA,
            testo="Secondo paragrafo.",
            attendibilita=Attendibilita.DOCUMENTATO,
        ),
    )

    risultato = componi_sezione(contenuti, Sezione.STORIA)

    assert risultato == "Primo paragrafo.\n\nSecondo paragrafo."


def test_componi_sezione_ignora_le_altre_sezioni() -> None:
    """Solo i beat della sezione richiesta finiscono nella prosa."""
    contenuti = _contenuti(
        Beat(
            id="storia",
            sezione=Sezione.STORIA,
            testo="Testo storico.",
            attendibilita=Attendibilita.DOCUMENTATO,
        ),
        Beat(
            id="usi",
            sezione=Sezione.USI,
            testo="Testo sugli usi.",
            attendibilita=Attendibilita.DOCUMENTATO,
        ),
    )

    assert componi_sezione(contenuti, Sezione.STORIA) == "Testo storico."
    assert componi_sezione(contenuti, Sezione.USI) == "Testo sugli usi."


def test_componi_sezione_vuota_restituisce_stringa_vuota() -> None:
    """Una sezione senza beat produce una stringa vuota, non un errore."""
    contenuti = _contenuti()

    assert componi_sezione(contenuti, Sezione.STORIA) == ""


def test_componi_sezione_normalizza_spazi_interni() -> None:
    """Gli a capo interni al testo di un beat diventano spazi singoli.

    Serve perché gli YAML usano il piegamento su più righe per leggibilità.
    """
    contenuti = _contenuti(
        Beat(
            id="uno",
            sezione=Sezione.STORIA,
            testo="Una frase\nspezzata   su più righe.",
            attendibilita=Attendibilita.DOCUMENTATO,
        ),
    )

    assert componi_sezione(contenuti, Sezione.STORIA) == "Una frase spezzata su più righe."


def test_componi_sezione_marca_i_beat_leggendari() -> None:
    """Un beat non documentato viene introdotto da una formula di cautela.

    Presentare una leggenda come fatto sarebbe scorretto verso il lettore.
    """
    contenuti = _contenuti(
        Beat(
            id="leggenda",
            sezione=Sezione.CURIOSITA,
            testo="Si narra che l'alchimista impazzì.",
            attendibilita=Attendibilita.LEGGENDARIO,
        ),
    )

    risultato = componi_sezione(contenuti, Sezione.CURIOSITA)

    assert risultato.startswith("*Secondo la leggenda:*")
    assert "Si narra che l'alchimista impazzì." in risultato


def test_componi_sezione_marca_i_beat_tradizionali() -> None:
    """Un beat tradizionale viene introdotto da una formula di cautela dedicata."""
    contenuti = _contenuti(
        Beat(
            id="tradizione",
            sezione=Sezione.CURIOSITA,
            testo="Brand vendette il segreto.",
            attendibilita=Attendibilita.TRADIZIONALE,
        ),
    )

    risultato = componi_sezione(contenuti, Sezione.CURIOSITA)

    assert risultato.startswith("*Per tradizione:*")


def test_conta_parole() -> None:
    """Il conteggio delle parole ignora la punteggiatura isolata e gli spazi multipli."""
    assert conta_parole("Una frase di cinque parole.") == 5
    assert conta_parole("") == 0
    assert conta_parole("   spazi    multipli   ") == 2


def test_conta_parole_ignora_il_markup_markdown() -> None:
    """Il conteggio non deve gonfiarsi per gli asterischi del corsivo o del grassetto."""
    assert conta_parole("*Per tradizione:* Brand vendette.") == 4


def test_tempo_lettura_arrotonda_per_eccesso() -> None:
    """Il tempo di lettura è arrotondato al minuto superiore, con minimo di un minuto."""
    assert tempo_lettura_minuti(230) == 1
    assert tempo_lettura_minuti(231) == 2
    assert tempo_lettura_minuti(1000) == 5
    assert tempo_lettura_minuti(0) == 1
