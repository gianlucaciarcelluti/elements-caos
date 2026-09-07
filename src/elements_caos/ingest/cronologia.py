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
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class VoceCronologia:
    """Riga della cronologia di riferimento delle scoperte."""

    numero_atomico: int
    anno: int
    anno_stimato: bool
    scopritori: list[str]
    epoca: str
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
    ),
    VoceCronologia(6, -26000, True, [], "antichita"),
    VoceCronologia(
        29,
        -9000,
        True,
        [],
        "antichita",
        note="Rame nativo lavorato per martellamento a freddo, non ancora metallurgia.",
    ),
    VoceCronologia(82, -7000, True, [], "antichita"),
    VoceCronologia(47, -5000, True, [], "antichita"),
    VoceCronologia(26, -5000, True, [], "antichita", note="Ferro meteoritico."),
    VoceCronologia(50, -3500, True, [], "antichita"),
    VoceCronologia(51, -3000, True, [], "antichita"),
    VoceCronologia(16, -2000, True, [], "antichita"),
    VoceCronologia(80, -1500, True, [], "antichita"),
    VoceCronologia(30, -1000, True, [], "antichita", note="Metallurgisti indiani."),
    VoceCronologia(78, -600, True, [], "antichita", note="Sud America precolombiana."),
    VoceCronologia(33, 300, True, [], "antichita"),
    VoceCronologia(
        83,
        1500,
        True,
        [],
        "antichita",
        note="Data convenzionale degli alchimisti europei, come le altre dell'antichità.",
    ),
    # --- Scoperte moderne, 1669-1879 ---
    VoceCronologia(15, 1669, False, ["hennig-brand"], "alchimia", isolamento_anno=1669),
    VoceCronologia(1, 1671, False, ["robert-boyle"], "alchimia", isolamento_anno=1671),
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
    ),
    VoceCronologia(27, 1735, False, ["georg-brandt"], "alchimia", isolamento_anno=1735),
    VoceCronologia(
        20,
        1739,
        False,
        ["johann-heinrich-pott"],
        "alchimia",
        isolamento_anno=1808,
        note="Isolato come elemento puro solo nel 1808, per elettrolisi, da Humphry Davy.",
    ),
    VoceCronologia(
        14,
        1739,
        False,
        ["johann-heinrich-pott"],
        "alchimia",
        isolamento_anno=1823,
        note="Isolato in forma amorfa pura nel 1823 da Jöns Jacob Berzelius.",
    ),
    VoceCronologia(
        13,
        1746,
        False,
        ["johann-heinrich-pott"],
        "alchimia",
        isolamento_anno=1825,
        note="Isolato nel 1825 da Hans Christian Ørsted.",
    ),
    VoceCronologia(28, 1751, False, ["axel-cronstedt"], "pneumatica", isolamento_anno=1751),
    VoceCronologia(
        12,
        1755,
        False,
        ["joseph-black"],
        "pneumatica",
        isolamento_anno=1808,
        note="Isolato come elemento puro solo nel 1808, per elettrolisi, da Humphry Davy.",
    ),
    VoceCronologia(
        25,
        1770,
        False,
        ["torbern-bergman"],
        "pneumatica",
        isolamento_anno=1774,
        note="Isolato nel 1774 da Johan Gottlieb Gahn.",
    ),
    VoceCronologia(
        9,
        1771,
        False,
        ["carl-wilhelm-scheele"],
        "pneumatica",
        isolamento_anno=1886,
        note="Isolato oltre un secolo dopo, nel 1886, da Henri Moissan.",
    ),
    VoceCronologia(8, 1771, False, ["carl-wilhelm-scheele"], "pneumatica", isolamento_anno=1771),
    VoceCronologia(7, 1772, False, ["daniel-rutherford"], "pneumatica", isolamento_anno=1772),
    VoceCronologia(
        56,
        1772,
        False,
        ["carl-wilhelm-scheele"],
        "pneumatica",
        isolamento_anno=1808,
        note="Isolato come elemento puro solo nel 1808, per elettrolisi, da Humphry Davy.",
    ),
    VoceCronologia(17, 1774, False, ["carl-wilhelm-scheele"], "pneumatica", isolamento_anno=1774),
    VoceCronologia(
        42,
        1778,
        False,
        ["carl-wilhelm-scheele"],
        "pneumatica",
        isolamento_anno=1788,
        note="Isolato nel 1788 da Peter Jacob Hjelm.",
    ),
    VoceCronologia(
        74,
        1781,
        False,
        ["carl-wilhelm-scheele"],
        "pneumatica",
        isolamento_anno=1783,
        note="Isolato nel 1783 dai fratelli Juan José e Fausto Elhuyar.",
    ),
    VoceCronologia(
        52,
        1782,
        False,
        ["franz-joseph-muller-von-reichenstein"],
        "pneumatica",
        isolamento_anno=1798,
        note="Isolato e nominato nel 1798 da Martin Heinrich Klaproth.",
    ),
    VoceCronologia(
        5,
        1787,
        False,
        ["louis-bernard-guyton-de-morveau"],
        "pneumatica",
        isolamento_anno=1809,
        note="Isolato nel 1809 da Humphry Davy.",
    ),
    VoceCronologia(
        40,
        1789,
        False,
        ["martin-heinrich-klaproth"],
        "pneumatica",
        isolamento_anno=1824,
        note="Isolato nel 1824 da Jöns Jacob Berzelius.",
    ),
    VoceCronologia(
        92,
        1789,
        False,
        ["martin-heinrich-klaproth"],
        "pneumatica",
        isolamento_anno=1841,
        note="Isolato nel 1841 da Eugène-Melchior Péligot.",
    ),
    VoceCronologia(
        38,
        1790,
        False,
        ["adair-crawford"],
        "pneumatica",
        isolamento_anno=1808,
        note="Isolato come elemento puro solo nel 1808, per elettrolisi, da Humphry Davy.",
    ),
    VoceCronologia(
        22,
        1791,
        False,
        ["william-gregor"],
        "pneumatica",
        isolamento_anno=1875,
        note="Isolato in forma quasi pura nel 1875 da Dmitri Kirillovič Kirillov.",
    ),
    VoceCronologia(
        39,
        1794,
        False,
        ["johan-gadolin"],
        "pneumatica",
        isolamento_anno=1843,
        note="Isolato nel 1843 da Heinrich Rose.",
    ),
    VoceCronologia(
        24, 1797, False, ["louis-nicolas-vauquelin"], "pneumatica", isolamento_anno=1798
    ),
    VoceCronologia(
        4,
        1798,
        False,
        ["louis-nicolas-vauquelin"],
        "pneumatica",
        isolamento_anno=1828,
        note="Isolato nel 1828, indipendentemente, da Friedrich Wöhler e Antoine Bussy.",
    ),
    VoceCronologia(
        23,
        1801,
        False,
        ["andres-manuel-del-rio"],
        "elettrolisi",
        isolamento_anno=1867,
        note="Isolato in forma pura nel 1867 da Henry Enfield Roscoe.",
    ),
    VoceCronologia(
        41,
        1801,
        False,
        ["charles-hatchett"],
        "elettrolisi",
        isolamento_anno=1864,
        note="Isolato nel 1864 da Christian Wilhelm Blomstrand.",
    ),
    VoceCronologia(
        73,
        1802,
        False,
        ["anders-gustaf-ekeberg"],
        "elettrolisi",
        isolamento_anno=1864,
        note="Isolato nel 1864 da Jean Charles Galissard de Marignac.",
    ),
    VoceCronologia(
        46, 1802, False, ["william-hyde-wollaston"], "elettrolisi", isolamento_anno=1802
    ),
    VoceCronologia(
        58,
        1803,
        False,
        ["martin-heinrich-klaproth"],
        "elettrolisi",
        isolamento_anno=1875,
        note="Isolato in forma pura nel 1875 da William Francis Hillebrand e Thomas Norton.",
    ),
    VoceCronologia(76, 1803, False, ["smithson-tennant"], "elettrolisi", isolamento_anno=1803),
    VoceCronologia(
        77,
        1803,
        False,
        ["smithson-tennant"],
        "elettrolisi",
        isolamento_anno=1803,
        note="Osservato nello stesso anno anche da Hippolyte-Victor Collet-Descotils.",
    ),
    VoceCronologia(
        45, 1804, False, ["william-hyde-wollaston"], "elettrolisi", isolamento_anno=1804
    ),
    VoceCronologia(53, 1811, False, ["bernard-courtois"], "elettrolisi", isolamento_anno=1811),
    VoceCronologia(
        3,
        1817,
        False,
        ["johan-august-arfwedson"],
        "elettrolisi",
        isolamento_anno=1821,
        note="Isolato in forma metallica nel 1821 da William Thomas Brande.",
    ),
    VoceCronologia(
        48,
        1817,
        False,
        ["karl-samuel-hermann", "friedrich-stromeyer", "johann-carl-heinrich-roloff"],
        "elettrolisi",
        isolamento_anno=1817,
    ),
    VoceCronologia(
        34,
        1817,
        False,
        ["jons-jacob-berzelius", "johan-gottlieb-gahn"],
        "elettrolisi",
        isolamento_anno=1817,
    ),
    VoceCronologia(
        35,
        1825,
        False,
        ["antoine-jerome-balard", "carl-lowig"],
        "elettrolisi",
        isolamento_anno=1825,
    ),
    VoceCronologia(
        90,
        1829,
        False,
        ["jons-jacob-berzelius"],
        "elettrolisi",
        isolamento_anno=1914,
        note="Isolato in forma pura al 99% nel 1914 da Dirk Lely Jr. e Lodewijk Hamburger.",
    ),
    VoceCronologia(
        57,
        1838,
        False,
        ["carl-gustaf-mosander"],
        "elettrolisi",
        isolamento_anno=1904,
        note="Isolato in forma pura nel 1904 da Wilhelm Muthmann e Leopold Weiss.",
    ),
    VoceCronologia(
        60,
        1841,
        False,
        ["carl-gustaf-mosander"],
        "elettrolisi",
        isolamento_anno=1901,
        note="Isolato in forma pura nel 1901 da Wilhelm Muthmann.",
    ),
    VoceCronologia(
        68,
        1843,
        False,
        ["carl-gustaf-mosander"],
        "elettrolisi",
        isolamento_anno=1934,
        note="Isolato in forma pura nel 1934 da Wilhelm Klemm e Heinrich Bommer.",
    ),
    VoceCronologia(
        65,
        1843,
        False,
        ["carl-gustaf-mosander"],
        "elettrolisi",
        isolamento_anno=1937,
        note="Isolato in forma pura nel 1937 da Wilhelm Klemm e Heinrich Bommer.",
    ),
    VoceCronologia(44, 1844, False, ["karl-ernst-claus"], "elettrolisi", isolamento_anno=1844),
    VoceCronologia(
        55,
        1860,
        False,
        ["gustav-kirchhoff", "robert-bunsen"],
        "spettroscopia",
        isolamento_anno=1882,
        note="Isolato in forma metallica pura nel 1882 da Carl Setterberg.",
    ),
    VoceCronologia(
        37,
        1861,
        False,
        ["gustav-kirchhoff", "robert-bunsen"],
        "spettroscopia",
        isolamento_anno=1863,
    ),
    VoceCronologia(
        81,
        1861,
        False,
        ["william-crookes"],
        "spettroscopia",
        isolamento_anno=1862,
        note="Isolato indipendentemente nel 1862 anche da Claude-Auguste Lamy.",
    ),
    VoceCronologia(
        49,
        1863,
        False,
        ["ferdinand-reich", "hieronymus-theodor-richter"],
        "spettroscopia",
        isolamento_anno=1864,
    ),
    VoceCronologia(
        2,
        1868,
        False,
        ["norman-lockyer"],
        "spettroscopia",
        isolamento_anno=1895,
        note="Isolato sulla Terra nel 1895 da William Ramsay, che ne confermò l'identità.",
    ),
    VoceCronologia(
        31, 1875, False, ["paul-emile-lecoq-de-boisbaudran"], "spettroscopia", isolamento_anno=1878
    ),
    VoceCronologia(
        70,
        1878,
        False,
        ["jean-charles-galissard-de-marignac"],
        "spettroscopia",
        isolamento_anno=1936,
        note="Isolato in forma pura nel 1936 da Wilhelm Klemm e Heinrich Bommer.",
    ),
    VoceCronologia(
        67,
        1878,
        False,
        ["jacques-louis-soret", "marc-delafontaine"],
        "spettroscopia",
        isolamento_anno=1939,
        note="Isolato in forma pura nel 1939 da Heinrich Bommer.",
    ),
    VoceCronologia(
        21,
        1879,
        False,
        ["lars-fredrik-nilson"],
        "spettroscopia",
        isolamento_anno=1937,
        note="Isolato in forma metallica pura nel 1937 da Werner Fischer (non 'Willy Fischer').",
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
    ),
    VoceCronologia(62, 1879, False, ["paul-emile-lecoq-de-boisbaudran"], "spettroscopia"),
    # --- Scoperte dal 1880 ---
    VoceCronologia(64, 1880, False, ["jean-charles-galissard-de-marignac"], "spettroscopia"),
    VoceCronologia(66, 1886, False, ["paul-emile-lecoq-de-boisbaudran"], "spettroscopia"),
    VoceCronologia(32, 1886, False, ["clemens-winkler"], "spettroscopia"),
    VoceCronologia(59, 1885, False, ["carl-auer-von-welsbach"], "spettroscopia"),
    VoceCronologia(18, 1894, False, ["william-ramsay", "lord-rayleigh"], "spettroscopia"),
    VoceCronologia(10, 1898, False, ["william-ramsay", "morris-travers"], "spettroscopia"),
    VoceCronologia(36, 1898, False, ["william-ramsay", "morris-travers"], "spettroscopia"),
    VoceCronologia(54, 1898, False, ["william-ramsay", "morris-travers"], "spettroscopia"),
    VoceCronologia(84, 1898, False, ["pierre-curie", "marie-curie"], "spettroscopia"),
    VoceCronologia(88, 1898, False, ["pierre-curie", "marie-curie"], "spettroscopia"),
    VoceCronologia(89, 1899, False, ["andre-louis-debierne"], "spettroscopia"),
    VoceCronologia(86, 1900, False, ["friedrich-ernst-dorn"], "spettroscopia"),
    VoceCronologia(63, 1901, False, ["eugene-anatole-demarcay"], "spettroscopia"),
    VoceCronologia(71, 1907, False, ["georges-urbain", "carl-auer-von-welsbach"], "spettroscopia"),
    VoceCronologia(72, 1923, False, ["dirk-coster", "georg-von-hevesy"], "spettroscopia"),
    VoceCronologia(91, 1913, False, ["kasimir-fajans", "oswald-helmuth-gohring"], "spettroscopia"),
    VoceCronologia(
        75, 1925, False, ["ida-noddack", "walter-noddack", "otto-berg"], "spettroscopia"
    ),
    VoceCronologia(43, 1937, False, ["carlo-perrier", "emilio-segre"], "spettroscopia"),
    VoceCronologia(87, 1939, False, ["marguerite-perey"], "spettroscopia"),
    VoceCronologia(
        85,
        1940,
        False,
        ["dale-corson", "kenneth-mackenzie", "emilio-segre"],
        "nucleare",
    ),
    VoceCronologia(93, 1940, False, ["edwin-mcmillan", "philip-abelson"], "nucleare"),
    VoceCronologia(
        94,
        1940,
        False,
        ["glenn-seaborg", "edwin-mcmillan", "joseph-kennedy", "arthur-wahl"],
        "nucleare",
        isolamento_anno=1941,
    ),
    VoceCronologia(
        61, 1945, False, ["jacob-marinsky", "lawrence-glendenin", "charles-coryell"], "nucleare"
    ),
    VoceCronologia(95, 1944, False, ["glenn-seaborg"], "nucleare"),
    VoceCronologia(96, 1944, False, ["glenn-seaborg"], "nucleare"),
    VoceCronologia(97, 1949, False, ["glenn-seaborg"], "nucleare"),
    VoceCronologia(98, 1950, False, ["glenn-seaborg"], "nucleare"),
    VoceCronologia(99, 1952, False, ["glenn-seaborg"], "nucleare"),
    VoceCronologia(100, 1952, False, ["glenn-seaborg"], "nucleare"),
    VoceCronologia(101, 1955, False, ["glenn-seaborg"], "nucleare"),
    VoceCronologia(102, 1958, False, ["albert-ghiorso"], "nucleare"),
    VoceCronologia(103, 1961, False, ["albert-ghiorso"], "nucleare"),
    VoceCronologia(104, 1969, False, ["georgy-flerov", "albert-ghiorso"], "nucleare"),
    VoceCronologia(105, 1970, False, ["georgy-flerov", "albert-ghiorso"], "nucleare"),
    VoceCronologia(106, 1974, False, ["albert-ghiorso"], "nucleare"),
    VoceCronologia(107, 1981, False, ["peter-armbruster", "gottfried-munzenberg"], "nucleare"),
    VoceCronologia(109, 1982, False, ["peter-armbruster", "gottfried-munzenberg"], "nucleare"),
    VoceCronologia(108, 1984, False, ["peter-armbruster", "gottfried-munzenberg"], "nucleare"),
    VoceCronologia(110, 1994, False, ["sigurd-hofmann"], "nucleare"),
    VoceCronologia(111, 1994, False, ["sigurd-hofmann"], "nucleare"),
    VoceCronologia(112, 1996, False, ["sigurd-hofmann"], "nucleare"),
    VoceCronologia(
        116,
        2000,
        False,
        ["yuri-oganessian", "kenton-moody"],
        "nucleare",
        note="Squadre congiunte russe (Dubna) e americane (Livermore).",
    ),
    VoceCronologia(
        115,
        2003,
        False,
        ["yuri-oganessian", "kenton-moody"],
        "nucleare",
        note="Squadre congiunte russe (Dubna) e americane (Livermore).",
    ),
    VoceCronologia(
        113,
        2004,
        False,
        ["kosuke-morita"],
        "nucleare",
        note="Sintetizzato al RIKEN Nishina Center, Giappone.",
    ),
    VoceCronologia(
        114,
        2006,
        False,
        ["yuri-oganessian", "kenton-moody"],
        "nucleare",
        note="Squadre congiunte russe (Dubna) e americane (Livermore).",
    ),
    VoceCronologia(
        118,
        2006,
        False,
        ["yuri-oganessian", "kenton-moody"],
        "nucleare",
        note="Squadre congiunte russe (Dubna) e americane (Livermore).",
    ),
    VoceCronologia(
        117,
        2010,
        False,
        ["yuri-oganessian", "kenton-moody"],
        "nucleare",
        note="Squadre congiunte russe (Dubna, Oak Ridge, Vanderbilt, Livermore).",
    ),
]
