"""Composizione dei beat narrativi in prosa continua.

I contenuti sono redatti come sequenza di beat, ciascuno con una sola idea.
Questo modulo li ricompone in paragrafi leggibili: il lettore della nota non
percepisce alcuna frammentazione.
"""

import math
import re

from elements_caos.models import Attendibilita, Contenuti, Sezione

# Velocità di lettura media in italiano, usata per stimare il tempo di lettura.
PAROLE_AL_MINUTO = 230

# Formule che introducono i beat non documentati, per non presentare come
# certo ciò che è tradizione o leggenda.
FORMULE_CAUTELA = {
    Attendibilita.TRADIZIONALE: "*Per tradizione:*",
    Attendibilita.LEGGENDARIO: "*Secondo la leggenda:*",
}

_SPAZI_MULTIPLI = re.compile(r"\s+")
_MARKUP_MARKDOWN = re.compile(r"[*`#\[\]()]")


def _normalizza(testo: str) -> str:
    """Riduce a spazi singoli gli a capo e le spaziature multiple del testo."""
    return _SPAZI_MULTIPLI.sub(" ", testo).strip()


def componi_sezione(contenuti: Contenuti, sezione: Sezione) -> str:
    """Compone in prosa continua i beat appartenenti alla sezione indicata.

    Ogni beat diventa un paragrafo. I beat la cui attendibilità non è
    documentata vengono introdotti da una formula di cautela.
    """
    paragrafi: list[str] = []
    for beat in contenuti.beats_per_sezione(sezione):
        testo = _normalizza(beat.testo)
        formula = FORMULE_CAUTELA.get(beat.attendibilita)
        paragrafi.append(f"{formula} {testo}" if formula else testo)
    return "\n\n".join(paragrafi)


def conta_parole(testo: str) -> int:
    """Conta le parole di un testo, escludendo il markup Markdown.

    Il markup viene rimosso e sostituito con spazi per evitare la fusione di parole
    separate da link o wikilink. I caratteri `_` non vengono rimossi perché usati
    nelle formule chimiche (es. H_2O). Il conteggio esclude il markup perché non è
    testo che il lettore legge: contarlo falserebbe la verifica del budget di lettura.
    """
    ripulito = _MARKUP_MARKDOWN.sub(" ", testo)
    normalizzato = _SPAZI_MULTIPLI.sub(" ", ripulito).strip()
    return len(normalizzato.split())


def tempo_lettura_minuti(parole: int) -> int:
    """Stima il tempo di lettura in minuti, con un minimo di un minuto."""
    return max(1, math.ceil(parole / PAROLE_AL_MINUTO))
