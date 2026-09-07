"""Cronologia di riferimento delle scoperte degli elementi.

Trascritta dalla voce "Timeline of chemical element discoveries" di Wikipedia
(CC BY-SA 4.0) e verificata elemento per elemento. È la fonte cronologica del
progetto: Wikidata è stata scartata perché contiene errori di attribuzione
verificati (berillio a Wöhler, boro datato 1892).

**Criterio scopritori vs isolatori**: quando la tabella di Wikipedia riporta
un anno di osservazione e un anno di isolamento distinti, lo "scopritore"
riconosciuto è la persona che ha OSSERVATO l'elemento per prima (è così che
la stessa tabella di Wikipedia, e la quasi totalità delle fonti secondarie,
attribuiscono la scoperta): l'isolatore compare solo in ``isolamento_anno``,
senza credito nominale, salvo quando è la stessa persona. L'unica eccezione
è la coppia sodio/potassio (vedi punto 5 sotto), dove l'"osservazione" del
1702 non individuò l'elemento ma solo il sale: lì lo scopritore riconosciuto
è l'isolatore.

La trascrizione iniziale (``docs/fonti/cronologia-scoperte.md``) conteneva
cinque famiglie di errori, corretti qui dopo verifica su Wikipedia e fonti
di settore (dettaglio completo nel report del Task 13):

1. iniziali abbreviate in modo incoerente (es. "W. Scheele" invece di
   "C. W. Scheele", il chimico si chiamava Carl Wilhelm) per fluoro,
   ossigeno, azoto, cloro, molibdeno, tungsteno, bario;
2. "N. Vauquelin" corretto in Louis Nicolas Vauquelin (cromo, berillio);
3. le due grafie di Wollaston ("W. H." e "H.") ricondotte a William Hyde
   Wollaston (palladio, rodio);
4. samario: la contraddizione fra "1879" e "dal 1880" risolta in favore di
   1879, l'anno riportato dalla tabella di Wikipedia;
5. sodio e potassio: l'osservazione del 1702 è di Georg Ernst Stahl, che
   distinse i SALI di sodio e potassio ma non isolò gli elementi. L'anno di
   scoperta riconosciuto per il vault è il 1807 (Humphry Davy, elettrolisi);
   il 1702 resta come nota di contesto storico, non come anno di scoperta.

Gli otto elementi recuperati separatamente dalla fonte (neon, argon,
cripton, xenon, germanio, afnio, praseodimio, promezio) sono stati
riverificati singolarmente su Wikipedia e risultano corretti così come
trascritti.

**Errore aggiuntivo trovato in verifica** (non fra i cinque segnalati dalla
fonte): per il tulio (Z=69) la trascrizione originale attribuiva
l'isolamento del 1911 a "H. Nilson", ma la ricostruzione storica indica
Charles James come primo isolatore del tulio puro. Poiché qui gli isolatori
non ricevono credito nominale (vedi criterio sopra), la correzione non
cambia lo scopritore (resta Cleve, autore dell'osservazione del 1879), ma è
comunque documentata perché il nome errato non deve comparire da nessuna
parte nel vault. Per lo scandio (Z=21), la fonte scriveva "W. Fischer" per
l'isolamento del 1937: il nome corretto è Werner Fischer, non Willy — anche
qui il correttivo non cambia lo scopritore (Nilson, osservazione del 1879),
ma la nota lo segnala per completezza. Infine, l'osservatore di calcio (Z=20),
silicio (Z=14) e alluminio (Z=13) nel 1739-1746 non è "Johan Gottschalk Pott"
(nome inesistente, frutto di una confusione fra due chimici svedesi distinti)
ma **Johann Heinrich Pott**, chimico prussiano: corretto qui e nell'id
``johann-heinrich-pott``.

**Elio (Z=2), Ruling 40**: la fonte del progetto riportava il solo "N.
Lockyer", ma la storiografia riconosce una paternità condivisa fra Pierre
Janssen e Norman Lockyer, che osservarono indipendentemente la stessa riga
gialla nello spettro solare nello stesso 1868 (Janssen il 18 agosto, durante
un'eclissi in India; Lockyer il 20 ottobre, dal proprio osservatorio, primo a
concludere correttamente che si trattava di un elemento nuovo). Non è
un'attribuzione contesa in senso stretto — sono due osservazioni
indipendenti, entrambe riconosciute, non una disputa di priorità — quindi il
dettaglio è raccontato in ``note_cronologia``, non nel campo ``controversia``
(che ``VoceCronologia`` non espone: non è stato necessario aggiungerlo per
questo caso, ma servirà nei Task 14-19 per le paternità realmente contese).
L'omissione di Janssen era ereditata dalla trascrizione originale, non
introdotta in questo modulo.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class VoceCronologia:
    """Riga della cronologia di riferimento delle scoperte.

    ``nome`` è il nome italiano dell'elemento (Ruling 39): vive qui, non solo
    nel file YAML che ``popola_dati.py`` scrive, perché un dato di
    riferimento non può avere come unica sede il file generato che dovrebbe
    riceverlo — esattamente come già valeva per anno, scopritori ed epoca.
    Prima di questa correzione, se un file YAML veniva cancellato lo script
    non aveva più modo di recuperare il nome italiano e ripiegava sul nome
    inglese del dataset, rigenerando un dato sbagliato in silenzio.
    """

    numero_atomico: int
    anno: int
    anno_stimato: bool
    scopritori: list[str]
    epoca: str
    nome: str = ""
    isolamento_anno: int | None = None
    note: str | None = None


CRONOLOGIA: list[VoceCronologia] = [
    # --- Elementi noti dall'antichità (14): date convenzionali, nessuno scopritore ---
    VoceCronologia(
        79,
        -40000,
        True,
        [],
        "antichita",
        note="Oro nativo rinvenuto in grotte del Paleolitico superiore.",
        nome="Oro",
    ),
    VoceCronologia(6, -26000, True, [], "antichita", nome="Carbonio"),
    VoceCronologia(
        29,
        -9000,
        True,
        [],
        "antichita",
        note="Rame nativo lavorato per martellamento a freddo, non ancora metallurgia.",
        nome="Rame",
    ),
    VoceCronologia(82, -7000, True, [], "antichita", nome="Piombo"),
    VoceCronologia(47, -5000, True, [], "antichita", nome="Argento"),
    VoceCronologia(26, -5000, True, [], "antichita", note="Ferro meteoritico.", nome="Ferro"),
    VoceCronologia(50, -3500, True, [], "antichita", nome="Stagno"),
    VoceCronologia(51, -3000, True, [], "antichita", nome="Antimonio"),
    VoceCronologia(16, -2000, True, [], "antichita", nome="Zolfo"),
    VoceCronologia(80, -1500, True, [], "antichita", nome="Mercurio"),
    VoceCronologia(
        30,
        -1000,
        True,
        [],
        "antichita",
        isolamento_anno=1746,
        note="Metallurgisti indiani. Isolato in Europa nel 1746 da Andreas Sigismund Marggraf.",
        nome="Zinco",
    ),
    VoceCronologia(
        78,
        -600,
        True,
        [],
        "antichita",
        isolamento_anno=1752,
        note="Sud America precolombiana. Riconosciuto come metallo distinto nel 1752 da "
        "Henrik Teofilus Scheffer.",
        nome="Platino",
    ),
    VoceCronologia(
        33,
        300,
        True,
        [],
        "antichita",
        isolamento_anno=1250,
        note="Isolamento tradizionalmente attribuito ad Alberto Magno, intorno al 1250.",
        nome="Arsenico",
    ),
    VoceCronologia(
        83,
        1500,
        True,
        [],
        # Cade in `alchimia` e non in `antichita`: i confini delle epoche sono
        # `inizio <= anno < fine` e alchimia parte proprio dal 1500. È anche
        # la collocazione storicamente giusta, perché il bismuto è materia
        # d'alchimia europea, non un metallo incontrato nella preistoria.
        "alchimia",
        isolamento_anno=1753,
        note="Data convenzionale degli alchimisti europei: il bismuto fu a lungo confuso "
        "con piombo, stagno e antimonio. La dimostrazione sperimentale che non è né "
        "piombo né stagno è di Claude François Geoffroy, nel 1753.",
        nome="Bismuto",
    ),
    # --- Scoperte moderne, 1669-1879 ---
    VoceCronologia(
        15, 1669, False, ["hennig-brand"], "alchimia", isolamento_anno=1669, nome="Fosforo"
    ),
    VoceCronologia(
        1, 1671, False, ["robert-boyle"], "alchimia", isolamento_anno=1671, nome="Idrogeno"
    ),
    VoceCronologia(
        11,
        1807,
        False,
        ["humphry-davy"],
        "elettrolisi",
        isolamento_anno=1807,
        note=(
            "Georg Ernst Stahl distinse chimicamente il sale di sodio già nel 1702, ma "
            "non isolò l'elemento: la scoperta riconosciuta è l'elettrolisi di Davy."
        ),
        nome="Sodio",
    ),
    VoceCronologia(
        19,
        1807,
        False,
        ["humphry-davy"],
        "elettrolisi",
        isolamento_anno=1807,
        note=(
            "Georg Ernst Stahl distinse chimicamente il sale di potassio già nel 1702, ma "
            "non isolò l'elemento: la scoperta riconosciuta è l'elettrolisi di Davy."
        ),
        nome="Potassio",
    ),
    VoceCronologia(
        27, 1735, False, ["georg-brandt"], "alchimia", isolamento_anno=1735, nome="Cobalto"
    ),
    VoceCronologia(
        20,
        1739,
        False,
        ["johann-heinrich-pott"],
        "alchimia",
        isolamento_anno=1808,
        note="Isolato come elemento puro solo nel 1808, per elettrolisi, da Humphry Davy.",
        nome="Calcio",
    ),
    VoceCronologia(
        14,
        1739,
        False,
        ["johann-heinrich-pott"],
        "alchimia",
        isolamento_anno=1823,
        note="Isolato in forma amorfa pura nel 1823 da Jöns Jacob Berzelius.",
        nome="Silicio",
    ),
    VoceCronologia(
        13,
        1746,
        False,
        ["johann-heinrich-pott"],
        "alchimia",
        isolamento_anno=1825,
        note="Isolato nel 1825 da Hans Christian Ørsted.",
        nome="Alluminio",
    ),
    VoceCronologia(
        28, 1751, False, ["axel-cronstedt"], "pneumatica", isolamento_anno=1751, nome="Nichel"
    ),
    VoceCronologia(
        12,
        1755,
        False,
        ["joseph-black"],
        "pneumatica",
        isolamento_anno=1808,
        note="Isolato come elemento puro solo nel 1808, per elettrolisi, da Humphry Davy.",
        nome="Magnesio",
    ),
    VoceCronologia(
        25,
        1770,
        False,
        ["torbern-bergman"],
        "pneumatica",
        isolamento_anno=1774,
        note="Isolato nel 1774 da Johan Gottlieb Gahn.",
        nome="Manganese",
    ),
    VoceCronologia(
        9,
        1771,
        False,
        ["carl-wilhelm-scheele"],
        "pneumatica",
        isolamento_anno=1886,
        note="Isolato oltre un secolo dopo, nel 1886, da Henri Moissan.",
        nome="Fluoro",
    ),
    VoceCronologia(
        8,
        1771,
        False,
        ["carl-wilhelm-scheele"],
        "pneumatica",
        isolamento_anno=1771,
        nome="Ossigeno",
    ),
    VoceCronologia(
        7, 1772, False, ["daniel-rutherford"], "pneumatica", isolamento_anno=1772, nome="Azoto"
    ),
    VoceCronologia(
        56,
        1772,
        False,
        ["carl-wilhelm-scheele"],
        "pneumatica",
        isolamento_anno=1808,
        note="Isolato come elemento puro solo nel 1808, per elettrolisi, da Humphry Davy.",
        nome="Bario",
    ),
    VoceCronologia(
        17, 1774, False, ["carl-wilhelm-scheele"], "pneumatica", isolamento_anno=1774, nome="Cloro"
    ),
    VoceCronologia(
        42,
        1778,
        False,
        ["carl-wilhelm-scheele"],
        "pneumatica",
        isolamento_anno=1781,
        # La trascrizione originale riportava 1788, anno che non compare in
        # nessuna delle fonti consultate durante la stesura della nota.
        note="Isolato nel 1781 da Peter Jacob Hjelm.",
        nome="Molibdeno",
    ),
    VoceCronologia(
        74,
        1781,
        False,
        ["carl-wilhelm-scheele"],
        "pneumatica",
        isolamento_anno=1783,
        note="Isolato nel 1783 dai fratelli Juan José e Fausto Elhuyar.",
        nome="Tungsteno",
    ),
    VoceCronologia(
        52,
        1782,
        False,
        ["franz-joseph-muller-von-reichenstein"],
        "pneumatica",
        isolamento_anno=1798,
        note="Isolato e nominato nel 1798 da Martin Heinrich Klaproth.",
        nome="Tellurio",
    ),
    VoceCronologia(
        5,
        1787,
        False,
        # Primo dei 22 casi in cui la fonte comprimeva più scopritori in un
        # nome solo seguito da «et al.» (Ruling 42): i quattro sono i
        # firmatari della «Méthode de nomenclature chimique» del 1787, che
        # applicando la teoria di Lavoisier all'acido borico dedussero un
        # «radicale borico» mai visto e gli diedero un nome.
        [
            "louis-bernard-guyton-de-morveau",
            "antoine-laurent-lavoisier",
            "claude-louis-berthollet",
            "antoine-francois-de-fourcroy",
        ],
        "pneumatica",
        isolamento_anno=1809,
        note="Battezzato su previsione teorica nel 1787, ventun anni prima di essere "
        "ottenuto: isolato nel 1809 da Humphry Davy.",
        nome="Boro",
    ),
    VoceCronologia(
        40,
        1789,
        False,
        ["martin-heinrich-klaproth"],
        "pneumatica",
        isolamento_anno=1824,
        note="Isolato nel 1824 da Jöns Jacob Berzelius.",
        nome="Zirconio",
    ),
    VoceCronologia(
        92,
        1789,
        False,
        ["martin-heinrich-klaproth"],
        "pneumatica",
        isolamento_anno=1841,
        note="Isolato nel 1841 da Eugène-Melchior Péligot.",
        nome="Uranio",
    ),
    VoceCronologia(
        38,
        1790,
        False,
        ["adair-crawford"],
        "pneumatica",
        isolamento_anno=1808,
        note="Isolato come elemento puro solo nel 1808, per elettrolisi, da Humphry Davy.",
        nome="Stronzio",
    ),
    VoceCronologia(
        22,
        1791,
        False,
        ["william-gregor"],
        "pneumatica",
        isolamento_anno=1875,
        note="Isolato in forma quasi pura nel 1875 da Dmitri Kirillovič Kirillov.",
        nome="Titanio",
    ),
    VoceCronologia(
        39,
        1794,
        False,
        ["johan-gadolin"],
        "pneumatica",
        isolamento_anno=1828,
        # La trascrizione originale dava 1843 e Heinrich Rose, fondendo due
        # vicende distinte: il 1843 è l'anno in cui Mosander separa erbio e
        # terbio dall'ittria, non quello dell'isolamento dell'ittrio.
        note="Isolato nel 1828 da Friedrich Wöhler.",
        nome="Ittrio",
    ),
    VoceCronologia(
        24,
        1797,
        False,
        ["louis-nicolas-vauquelin"],
        "pneumatica",
        isolamento_anno=1798,
        nome="Cromo",
    ),
    VoceCronologia(
        4,
        1798,
        False,
        ["louis-nicolas-vauquelin"],
        "pneumatica",
        isolamento_anno=1828,
        note="Isolato nel 1828, indipendentemente, da Friedrich Wöhler e Antoine Bussy.",
        nome="Berillio",
    ),
    VoceCronologia(
        23,
        1801,
        False,
        ["andres-manuel-del-rio"],
        "elettrolisi",
        isolamento_anno=1867,
        note="Isolato in forma pura nel 1867 da Henry Enfield Roscoe.",
        nome="Vanadio",
    ),
    VoceCronologia(
        41,
        1801,
        False,
        ["charles-hatchett"],
        "elettrolisi",
        isolamento_anno=1864,
        note="Isolato nel 1864 da Christian Wilhelm Blomstrand.",
        nome="Niobio",
    ),
    VoceCronologia(
        73,
        1802,
        False,
        ["anders-gustaf-ekeberg"],
        "elettrolisi",
        isolamento_anno=1864,
        note="Isolato nel 1864 da Jean Charles Galissard de Marignac.",
        nome="Tantalio",
    ),
    VoceCronologia(
        46,
        1802,
        False,
        ["william-hyde-wollaston"],
        "elettrolisi",
        isolamento_anno=1802,
        nome="Palladio",
    ),
    VoceCronologia(
        58,
        1803,
        False,
        ["martin-heinrich-klaproth"],
        "elettrolisi",
        isolamento_anno=1875,
        note="Isolato in forma pura nel 1875 da William Francis Hillebrand e Thomas Norton.",
        nome="Cerio",
    ),
    VoceCronologia(
        76, 1803, False, ["smithson-tennant"], "elettrolisi", isolamento_anno=1803, nome="Osmio"
    ),
    VoceCronologia(
        77,
        1803,
        False,
        ["smithson-tennant"],
        "elettrolisi",
        isolamento_anno=1803,
        note="Osservato nello stesso anno anche da Hippolyte-Victor Collet-Descotils.",
        nome="Iridio",
    ),
    VoceCronologia(
        45,
        1804,
        False,
        ["william-hyde-wollaston"],
        "elettrolisi",
        isolamento_anno=1804,
        nome="Rodio",
    ),
    VoceCronologia(
        53, 1811, False, ["bernard-courtois"], "elettrolisi", isolamento_anno=1811, nome="Iodio"
    ),
    VoceCronologia(
        3,
        1817,
        False,
        ["johan-august-arfwedson"],
        "elettrolisi",
        isolamento_anno=1821,
        note="Isolato in forma metallica nel 1821 da William Thomas Brande.",
        nome="Litio",
    ),
    VoceCronologia(
        48,
        1817,
        False,
        ["karl-samuel-hermann", "friedrich-stromeyer", "johann-carl-heinrich-roloff"],
        "elettrolisi",
        isolamento_anno=1817,
        nome="Cadmio",
    ),
    VoceCronologia(
        34,
        1817,
        False,
        ["jons-jacob-berzelius", "johan-gottlieb-gahn"],
        "elettrolisi",
        isolamento_anno=1817,
        nome="Selenio",
    ),
    VoceCronologia(
        35,
        1825,
        False,
        ["antoine-jerome-balard", "carl-lowig"],
        "elettrolisi",
        isolamento_anno=1825,
        nome="Bromo",
    ),
    VoceCronologia(
        90,
        1829,
        False,
        ["jons-jacob-berzelius"],
        "elettrolisi",
        isolamento_anno=1914,
        note="Isolato in forma pura al 99% nel 1914 da Dirk Lely Jr. e Lodewijk Hamburger.",
        nome="Torio",
    ),
    VoceCronologia(
        57,
        1838,
        False,
        ["carl-gustaf-mosander"],
        "elettrolisi",
        isolamento_anno=1904,
        note="Isolato in forma pura nel 1904 da Wilhelm Muthmann e Leopold Weiss.",
        nome="Lantanio",
    ),
    VoceCronologia(
        60,
        1841,
        False,
        ["carl-gustaf-mosander"],
        "elettrolisi",
        isolamento_anno=1901,
        note="Isolato in forma pura nel 1901 da Wilhelm Muthmann.",
        nome="Neodimio",
    ),
    VoceCronologia(
        68,
        1843,
        False,
        ["carl-gustaf-mosander"],
        "elettrolisi",
        isolamento_anno=1934,
        note="Isolato in forma pura nel 1934 da Wilhelm Klemm e Heinrich Bommer.",
        nome="Erbio",
    ),
    VoceCronologia(
        65,
        1843,
        False,
        ["carl-gustaf-mosander"],
        "elettrolisi",
        isolamento_anno=1937,
        note="Isolato in forma pura nel 1937 da Wilhelm Klemm e Heinrich Bommer.",
        nome="Terbio",
    ),
    VoceCronologia(
        44, 1844, False, ["karl-ernst-claus"], "elettrolisi", isolamento_anno=1844, nome="Rutenio"
    ),
    VoceCronologia(
        55,
        1860,
        False,
        ["gustav-kirchhoff", "robert-bunsen"],
        "spettroscopia",
        isolamento_anno=1882,
        note="Isolato in forma metallica pura nel 1882 da Carl Setterberg.",
        nome="Cesio",
    ),
    VoceCronologia(
        37,
        1861,
        False,
        ["gustav-kirchhoff", "robert-bunsen"],
        "spettroscopia",
        isolamento_anno=1863,
        nome="Rubidio",
    ),
    VoceCronologia(
        81,
        1861,
        False,
        ["william-crookes"],
        "spettroscopia",
        isolamento_anno=1862,
        note="Isolato indipendentemente nel 1862 anche da Claude-Auguste Lamy.",
        nome="Tallio",
    ),
    VoceCronologia(
        49,
        1863,
        False,
        ["ferdinand-reich", "hieronymus-theodor-richter"],
        "spettroscopia",
        isolamento_anno=1864,
        nome="Indio",
    ),
    VoceCronologia(
        2,
        1868,
        False,
        ["pierre-janssen", "norman-lockyer"],
        "spettroscopia",
        isolamento_anno=1895,
        note=(
            "Osservato indipendentemente da entrambi nello stesso 1868: Janssen il 18 "
            "agosto, durante l'eclissi solare a Guntur, in India, notò una riga gialla "
            "nello spettro della cromosfera; Lockyer osservò la stessa riga il 20 "
            "ottobre, dal proprio osservatorio, e per primo concluse correttamente che "
            "apparteneva a un elemento nuovo, non ancora noto sulla Terra, a cui diede "
            "il nome elio. La paternità condivisa è quella riconosciuta dalla "
            "storiografia. Isolato sulla Terra nel 1895 da William Ramsay, che ne "
            "confermò l'identità."
        ),
        nome="Elio",
    ),
    VoceCronologia(
        31,
        1875,
        False,
        ["paul-emile-lecoq-de-boisbaudran"],
        "spettroscopia",
        isolamento_anno=1878,
        nome="Gallio",
    ),
    VoceCronologia(
        70,
        1878,
        False,
        ["jean-charles-galissard-de-marignac"],
        "spettroscopia",
        isolamento_anno=1936,
        note="Isolato in forma pura nel 1936 da Wilhelm Klemm e Heinrich Bommer.",
        nome="Itterbio",
    ),
    VoceCronologia(
        67,
        1878,
        False,
        ["jacques-louis-soret", "marc-delafontaine"],
        "spettroscopia",
        isolamento_anno=1939,
        note="Isolato in forma pura nel 1939 da Heinrich Bommer.",
        nome="Olmio",
    ),
    VoceCronologia(
        21,
        1879,
        False,
        ["lars-fredrik-nilson"],
        "spettroscopia",
        isolamento_anno=1937,
        note="Isolato in forma metallica pura nel 1937 da Werner Fischer (non 'Willy Fischer').",
        nome="Scandio",
    ),
    VoceCronologia(
        69,
        1879,
        False,
        ["per-teodor-cleve"],
        "spettroscopia",
        isolamento_anno=1911,
        note=(
            "Isolato in forma pura nel 1911 da Charles James. La trascrizione originale "
            "attribuiva questo isolamento a 'H. Nilson': verificato e corretto."
        ),
        nome="Tulio",
    ),
    VoceCronologia(
        62, 1879, False, ["paul-emile-lecoq-de-boisbaudran"], "spettroscopia", nome="Samario"
    ),
    # --- Scoperte dal 1880 ---
    VoceCronologia(
        64, 1880, False, ["jean-charles-galissard-de-marignac"], "spettroscopia", nome="Gadolinio"
    ),
    VoceCronologia(
        66, 1886, False, ["paul-emile-lecoq-de-boisbaudran"], "spettroscopia", nome="Disprosio"
    ),
    VoceCronologia(32, 1886, False, ["clemens-winkler"], "spettroscopia", nome="Germanio"),
    VoceCronologia(
        59, 1885, False, ["carl-auer-von-welsbach"], "spettroscopia", nome="Praseodimio"
    ),
    VoceCronologia(
        18, 1894, False, ["william-ramsay", "lord-rayleigh"], "spettroscopia", nome="Argon"
    ),
    VoceCronologia(
        10, 1898, False, ["william-ramsay", "morris-travers"], "spettroscopia", nome="Neon"
    ),
    VoceCronologia(
        36, 1898, False, ["william-ramsay", "morris-travers"], "spettroscopia", nome="Cripton"
    ),
    VoceCronologia(
        54, 1898, False, ["william-ramsay", "morris-travers"], "spettroscopia", nome="Xenon"
    ),
    VoceCronologia(
        84, 1898, False, ["pierre-curie", "marie-curie"], "spettroscopia", nome="Polonio"
    ),
    VoceCronologia(88, 1898, False, ["pierre-curie", "marie-curie"], "spettroscopia", nome="Radio"),
    VoceCronologia(89, 1899, False, ["andre-louis-debierne"], "spettroscopia", nome="Attinio"),
    VoceCronologia(86, 1900, False, ["friedrich-ernst-dorn"], "spettroscopia", nome="Radon"),
    VoceCronologia(63, 1901, False, ["eugene-anatole-demarcay"], "spettroscopia", nome="Europio"),
    VoceCronologia(
        71,
        1907,
        False,
        ["georges-urbain", "carl-auer-von-welsbach"],
        "spettroscopia",
        nome="Lutezio",
    ),
    VoceCronologia(
        72, 1923, False, ["dirk-coster", "georg-von-hevesy"], "spettroscopia", nome="Afnio"
    ),
    VoceCronologia(
        91,
        1913,
        False,
        ["kasimir-fajans", "oswald-helmuth-gohring"],
        "spettroscopia",
        nome="Protoattinio",
    ),
    VoceCronologia(
        75,
        1925,
        False,
        ["ida-noddack", "walter-noddack", "otto-berg"],
        "spettroscopia",
        nome="Renio",
    ),
    VoceCronologia(
        43, 1937, False, ["carlo-perrier", "emilio-segre"], "spettroscopia", nome="Tecnezio"
    ),
    VoceCronologia(87, 1939, False, ["marguerite-perey"], "spettroscopia", nome="Francio"),
    VoceCronologia(
        85,
        1940,
        False,
        ["dale-corson", "kenneth-mackenzie", "emilio-segre"],
        "nucleare",
        nome="Astato",
    ),
    VoceCronologia(
        93, 1940, False, ["edwin-mcmillan", "philip-abelson"], "nucleare", nome="Nettunio"
    ),
    VoceCronologia(
        94,
        1940,
        False,
        ["glenn-seaborg", "edwin-mcmillan", "joseph-kennedy", "arthur-wahl"],
        "nucleare",
        isolamento_anno=1941,
        nome="Plutonio",
    ),
    VoceCronologia(
        61,
        1945,
        False,
        ["jacob-marinsky", "lawrence-glendenin", "charles-coryell"],
        "nucleare",
        nome="Promezio",
    ),
    VoceCronologia(95, 1944, False, ["glenn-seaborg"], "nucleare", nome="Americio"),
    VoceCronologia(96, 1944, False, ["glenn-seaborg"], "nucleare", nome="Curio"),
    VoceCronologia(97, 1949, False, ["glenn-seaborg"], "nucleare", nome="Berkelio"),
    VoceCronologia(98, 1950, False, ["glenn-seaborg"], "nucleare", nome="Californio"),
    VoceCronologia(99, 1952, False, ["glenn-seaborg"], "nucleare", nome="Einsteinio"),
    VoceCronologia(100, 1952, False, ["glenn-seaborg"], "nucleare", nome="Fermio"),
    VoceCronologia(101, 1955, False, ["glenn-seaborg"], "nucleare", nome="Mendelevio"),
    VoceCronologia(102, 1958, False, ["albert-ghiorso"], "nucleare", nome="Nobelio"),
    VoceCronologia(103, 1961, False, ["albert-ghiorso"], "nucleare", nome="Laurenzio"),
    VoceCronologia(
        104, 1969, False, ["georgy-flerov", "albert-ghiorso"], "nucleare", nome="Rutherfordio"
    ),
    VoceCronologia(
        105, 1970, False, ["georgy-flerov", "albert-ghiorso"], "nucleare", nome="Dubnio"
    ),
    VoceCronologia(106, 1974, False, ["albert-ghiorso"], "nucleare", nome="Seaborgio"),
    VoceCronologia(
        107, 1981, False, ["peter-armbruster", "gottfried-munzenberg"], "nucleare", nome="Bohrio"
    ),
    VoceCronologia(
        109, 1982, False, ["peter-armbruster", "gottfried-munzenberg"], "nucleare", nome="Meitnerio"
    ),
    VoceCronologia(
        108, 1984, False, ["peter-armbruster", "gottfried-munzenberg"], "nucleare", nome="Hassio"
    ),
    VoceCronologia(110, 1994, False, ["sigurd-hofmann"], "nucleare", nome="Darmstadtio"),
    VoceCronologia(111, 1994, False, ["sigurd-hofmann"], "nucleare", nome="Roentgenio"),
    VoceCronologia(112, 1996, False, ["sigurd-hofmann"], "nucleare", nome="Copernicio"),
    VoceCronologia(
        116,
        2000,
        False,
        ["yuri-oganessian", "kenton-moody"],
        "nucleare",
        note="Squadre congiunte russe (Dubna) e americane (Livermore).",
        nome="Livermorio",
    ),
    VoceCronologia(
        115,
        2003,
        False,
        ["yuri-oganessian", "kenton-moody"],
        "nucleare",
        note="Squadre congiunte russe (Dubna) e americane (Livermore).",
        nome="Moscovio",
    ),
    VoceCronologia(
        113,
        2004,
        False,
        ["kosuke-morita"],
        "nucleare",
        note="Sintetizzato al RIKEN Nishina Center, Giappone.",
        nome="Nihonio",
    ),
    VoceCronologia(
        114,
        2006,
        False,
        ["yuri-oganessian", "kenton-moody"],
        "nucleare",
        note="Squadre congiunte russe (Dubna) e americane (Livermore).",
        nome="Flerovio",
    ),
    VoceCronologia(
        118,
        2006,
        False,
        ["yuri-oganessian", "kenton-moody"],
        "nucleare",
        note="Squadre congiunte russe (Dubna) e americane (Livermore).",
        nome="Oganesson",
    ),
    VoceCronologia(
        117,
        2010,
        False,
        ["yuri-oganessian", "kenton-moody"],
        "nucleare",
        note="Squadre congiunte russe (Dubna, Oak Ridge, Vanderbilt, Livermore).",
        nome="Tennesso",
    ),
]
