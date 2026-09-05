"""Modelli dati del vault e regole di validazione dello schema.

Ogni elemento chimico è descritto da un file YAML in ``data/elements/``.
Questi modelli ne definiscono la struttura e i vincoli di integrità, così che
un dato malformato venga intercettato prima della generazione del vault.
"""

from datetime import date
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator

# Anno prima del quale una data di scoperta è necessariamente una stima
# convenzionale: gli elementi noti fin dall'antichità non hanno una data certa.
ANNO_SOGLIA_STIMA = 1500


class Sezione(StrEnum):
    """Sezione della nota a cui appartiene un beat narrativo."""

    INCIPIT = "incipit"
    STORIA = "storia"
    CARATTERISTICHE = "caratteristiche"
    USI = "usi"
    CURIOSITA = "curiosita"


class Attendibilita(StrEnum):
    """Grado di attendibilità storica di un beat narrativo.

    Serve a distinguere i fatti documentati dagli aneddoti tramandati, per non
    presentare come certo ciò che è tradizione o leggenda.
    """

    DOCUMENTATO = "documentato"
    TRADIZIONALE = "tradizionale"
    LEGGENDARIO = "leggendario"


class Categoria(StrEnum):
    """Categoria chimica dell'elemento, normalizzata in italiano."""

    METALLO_ALCALINO = "metallo_alcalino"
    METALLO_ALCALINO_TERROSO = "metallo_alcalino_terroso"
    METALLO_DI_TRANSIZIONE = "metallo_di_transizione"
    METALLO_POST_TRANSIZIONE = "metallo_post_transizione"
    SEMIMETALLO = "semimetallo"
    NON_METALLO = "non_metallo"
    ALOGENO = "alogeno"
    GAS_NOBILE = "gas_nobile"
    LANTANIDE = "lantanide"
    ATTINIDE = "attinide"


class Beat(BaseModel):
    """Unità narrativa minima: una sola idea, autonoma e leggibile da sola.

    I beat sono concatenati in prosa continua nella nota Markdown. La
    segmentazione resta nei dati per consentire riusi del vault in altri formati.
    """

    id: str
    sezione: Sezione
    testo: str
    visual: str | None = None
    attendibilita: Attendibilita = Attendibilita.DOCUMENTATO


class Pronuncia(BaseModel):
    """Pronuncia di un nome proprio straniero, in notazione IPA."""

    termine: str
    ipa: str
    nota: str | None = None


class Contenuti(BaseModel):
    """Contenuti redazionali di un elemento, organizzati in beat narrativi."""

    hook: str
    beats: list[Beat] = Field(default_factory=list)
    pronuncia: list[Pronuncia] = Field(default_factory=list)

    @model_validator(mode="after")
    def _verifica_id_beat_univoci(self) -> Self:
        """Verifica che non esistano beat con id duplicato nello stesso elemento."""
        visti: set[str] = set()
        for beat in self.beats:
            if beat.id in visti:
                raise ValueError(f"identificativo di beat duplicato: {beat.id!r}")
            visti.add(beat.id)
        return self

    def beats_per_sezione(self, sezione: Sezione) -> list[Beat]:
        """Restituisce i beat della sezione indicata, nell'ordine dichiarato."""
        return [beat for beat in self.beats if beat.sezione is sezione]


class Scoperta(BaseModel):
    """Circostanze storiche della scoperta di un elemento."""

    anno: int
    anno_stimato: bool
    scopritori: list[str] = Field(default_factory=list)
    luogo: str | None = None
    epoca: str
    isolamento_anno: int | None = None
    note_cronologia: str | None = None
    controversia: str | None = None

    @model_validator(mode="after")
    def _verifica_stima_per_date_antiche(self) -> Self:
        """Impone il flag di stima sulle date anteriori alla soglia convenzionale.

        Gli elementi noti fin dall'antichità non hanno una data di scoperta
        certa: dichiararla come esatta sarebbe fuorviante.
        """
        if self.anno < ANNO_SOGLIA_STIMA and not self.anno_stimato:
            raise ValueError(
                f"l'anno {self.anno} è anteriore al {ANNO_SOGLIA_STIMA}: richiede anno_stimato=True"
            )
        return self


class Proprieta(BaseModel):
    """Proprietà fisico-chimiche dell'elemento.

    Le temperature sono espresse in Kelvin; la conversione in gradi Celsius
    avviene soltanto in fase di rendering.
    """

    gruppo: int | None = Field(default=None, ge=1, le=18)
    periodo: int = Field(ge=1, le=7)
    blocco: str = Field(pattern="^[spdf]$")
    categoria: Categoria
    massa_atomica: float = Field(gt=0)
    configurazione_elettronica: str
    gusci: list[int]
    punto_fusione_k: float | None = None
    punto_ebollizione_k: float | None = None
    densita: float | None = None
    stati_ossidazione: list[int] = Field(default_factory=list)


class Composto(BaseModel):
    """Composto rilevante dell'elemento, con i suoi principali impieghi."""

    nome: str
    formula: str
    usi: list[str] = Field(default_factory=list)


class Fonte(BaseModel):
    """Riferimento bibliografico consultato per la stesura della nota."""

    url: str
    titolo: str
    consultata: date


class Elemento(BaseModel):
    """Un elemento chimico con la sua storia, le sue proprietà e le sue fonti."""

    numero_atomico: int = Field(ge=1, le=118)
    simbolo: str = Field(min_length=1, max_length=3)
    nome: str
    nome_en: str
    scoperta: Scoperta
    proprieta: Proprieta
    approfondimento: bool = False
    contenuti: Contenuti | None = None
    contenuti_estesi: Contenuti | None = None
    composti_principali: list[Composto] = Field(default_factory=list)
    fonti: list[Fonte] = Field(default_factory=list)

    @model_validator(mode="after")
    def _verifica_coerenza_gusci(self) -> Self:
        """Verifica che gli elettroni distribuiti nei gusci diano il numero atomico."""
        totale = sum(self.proprieta.gusci)
        if totale != self.numero_atomico:
            raise ValueError(
                f"i gusci sommano a {totale} elettroni ma il numero atomico è {self.numero_atomico}"
            )
        return self


class Ritratto(BaseModel):
    """Ritratto di uno scopritore, con la provenienza e la licenza d'uso."""

    file: str
    licenza: str
    autore: str
    fonte: str


class Scopritore(BaseModel):
    """Scienziato a cui è attribuita la scoperta di uno o più elementi."""

    id: str
    nome: str
    nato: int | None = None
    morto: int | None = None
    nazionalita: str | None = None
    elementi: list[int] = Field(default_factory=list)
    ritratto: Ritratto | None = None


class Epoca(BaseModel):
    """Periodo storico in cui si raggruppano le scoperte degli elementi."""

    id: str
    nome: str
    anno_inizio: int
    anno_fine: int
    descrizione: str


class Tappa(BaseModel):
    """Tappa dell'itinerario guidato di lettura.

    Risiede fra i modelli di dominio, e non nel pacchetto di rendering, perché
    è caricata da ``caricamento`` e usata da ``render``: definirla altrove
    creerebbe una dipendenza circolare fra i due.
    """

    titolo: str
    elemento: str
    descrizione: str
