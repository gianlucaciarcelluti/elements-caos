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


def test_componi_sezione_non_premette_nulla_ai_beat_discussi() -> None:
    """Un beat `discusso` non riceve formula di cautela: la contiene già nel testo.

    I beat che *smontano* una tradizione non vanno introdotti da "Per
    tradizione:", che li capovolgerebbe annunciando come sapere tramandato un
    testo che dice il contrario. Un beat di confutazione non è documentato
    (non asserisce un fatto), non è tradizionale (non tramanda) e non è
    leggendario (non racconta la leggenda come tale): è discussione
    storiografica, e la cautela sta già nella sua formulazione.
    """
    contenuti = _contenuti(
        Beat(
            id="confutazione",
            sezione=Sezione.CURIOSITA,
            testo="Si racconta spesso che sia andata così, ma non è mai stato dimostrato.",
            attendibilita=Attendibilita.DISCUSSO,
        ),
    )

    risultato = componi_sezione(contenuti, Sezione.CURIOSITA)

    assert risultato.startswith("Si racconta spesso")
    assert "*Per tradizione:*" not in risultato
    assert "*Secondo la leggenda:*" not in risultato


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


def test_conta_parole_con_link_markdown() -> None:
    """Il conteggio deve separare correttamente il testo da un URL in link.

    Senza la sostituzione con spazi anziché stringa vuota, il testo visibile
    "[Storia del fosforo]" e l'URL "(https://...)" verrebbero fusi in un'unica parola.
    Con la sostituzione, rimangono separati.
    """
    testo = "Fonte: [Storia del fosforo](https://esempio.it/fosforo)."
    # Parole: Fonte, :, Storia, del, fosforo, https://esempio.it/fosforo, .
    assert conta_parole(testo) == 6


def test_conta_parole_con_wikilink_semplice() -> None:
    """Il conteggio deve separare il testo da un wikilink semplice.

    A parità di contesto, `[[Fosforo]]` introduce una separazione fra il testo
    antecedente e il successivo.
    """
    testo = "Vedi [[Fosforo]] per la storia."
    # Parole visibili: Vedi Fosforo per la storia
    assert conta_parole(testo) == 5


def test_conta_parole_con_wikilink_alias() -> None:
    """Il conteggio deve contare solo il testo visibile del wikilink, non il collegamento.

    Nel formato [[collegamento|testo visibile]], il conteggio coglie solo il testo.
    """
    testo = "[[Fosforo|P]] brilla al buio."
    # Parole visibili: P brilla al buio (il "Fosforo" non appare al lettore)
    assert conta_parole(testo) == 4


def test_conta_parole_preserva_formule_chimiche_con_underscore() -> None:
    """Le formule chimiche con underscore (es. H_2O) non devono essere alterate.

    L'underscore non viene rimosso dal markup, quindi rimane intatto e il
    conteggio lo preserva: H_2O conta come una parola.
    """
    testo = "La molecola H_2O è composta di idrogeno e ossigeno."
    # Parole: La, molecola, H_2O, è, composta, di, idrogeno, e, ossigeno
    assert conta_parole(testo) == 9
