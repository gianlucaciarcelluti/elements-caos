#!/usr/bin/env bash
# Costruisce il sito pubblico a partire dal vault, con Quartz.
#
# Quartz si usa normalmente clonandone il repository e mettendo le note in
# content/. Qui il repository esiste già ed è il contrario: il contenuto è
# nostro e Quartz è lo strumento. Quindi Quartz non viene incorporato nel
# repository — porta con sé quindici megabyte di quartz/util/emojimap.json, che
# non comprimono, contro i dodici dell'intera storia di questo progetto — ma
# viene clonato a una versione fissata, riempito con vault/ e con la nostra
# configurazione, e costruito lì dentro.
#
# Il risultato finisce in public/, che .gitignore già esclude.
#
# Uso:
#   scripts/costruisci_sito.sh              costruisce in public/
#   SERVI=1 scripts/costruisci_sito.sh      costruisce e serve in locale
set -euo pipefail

# La versione di Quartz è fissata a un commit preciso: senza pin il sito si
# costruirebbe con qualunque cosa sia sul ramo quel giorno, e una rottura
# arriverebbe in produzione senza che nulla in questo repository sia cambiato.
#
# Il pin NON è il tag v5.0.0: a quella versione "npm run install-plugins" muore
# su quartz/styles/custom.scss ("Unknown file extension .scss") e la
# costruzione non parte nemmeno. Sul ramo v5 il difetto è corretto, e questo è
# il commit verificato — l'unico modo di avere insieme un Quartz funzionante e
# una versione fissata.
QUARTZ_COMMIT="${QUARTZ_COMMIT:-f1fba3fc55cbf60a60a5d09c95a49c042cdab63a}"
QUARTZ_REPO="https://github.com/jackyzha0/quartz.git"

RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COSTRUZIONE="${COSTRUZIONE:-$RADICE/.quartz-build}"

if [[ ! -d "$RADICE/vault" ]]; then
  echo "vault/ non trovato: lo script va lanciato dal repository" >&2
  exit 1
fi

# Il clone si riusa fra una costruzione e l'altra, ma solo se è al commit
# giusto: altrimenti si rifà, perché un clone rimasto a una versione precedente
# costruirebbe in silenzio con i plugin sbagliati.
if [[ -d "$COSTRUZIONE/.git" ]]; then
  ATTUALE="$(git -C "$COSTRUZIONE" rev-parse HEAD 2>/dev/null || echo "")"
  if [[ "$ATTUALE" != "$QUARTZ_COMMIT" ]]; then
    echo "clone di Quartz a '${ATTUALE:-nessuno}' invece di $QUARTZ_COMMIT: lo rifaccio"
    rm -rf "$COSTRUZIONE"
  fi
fi

if [[ ! -d "$COSTRUZIONE/.git" ]]; then
  echo "clono Quartz $QUARTZ_COMMIT"
  # Un commit preciso non si clona con --branch: si prende con un fetch mirato,
  # che resta comunque superficiale e scarica solo quella revisione.
  mkdir -p "$COSTRUZIONE"
  git -C "$COSTRUZIONE" init -q
  git -C "$COSTRUZIONE" remote add origin "$QUARTZ_REPO"
  git -C "$COSTRUZIONE" fetch -q --depth 1 origin "$QUARTZ_COMMIT"
  git -C "$COSTRUZIONE" checkout -q FETCH_HEAD
fi

# Il contenuto di esempio di Quartz non deve finire nel sito.
rm -rf "$COSTRUZIONE/content"
mkdir -p "$COSTRUZIONE/content"

# --delete tiene allineate le cancellazioni: una nota rimossa dal vault deve
# sparire anche dal sito, non sopravvivere nel clone riusato.
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete --exclude '.obsidian' "$RADICE/vault/" "$COSTRUZIONE/content/"
else
  cp -R "$RADICE/vault/." "$COSTRUZIONE/content/"
  rm -rf "$COSTRUZIONE/content/.obsidian"
fi

# La home del sito non sta nel vault: in Obsidian il punto di ingresso e la
# nota "Cronologia degli elementi", e una nota "index" li sarebbe solo rumore.
# Senza questo file pero la radice del sito risponde 404, perche Quartz emette
# index.html soltanto se trova content/index.md.
cp "$RADICE/sito/index.md" "$COSTRUZIONE/content/index.md"

cp "$RADICE/quartz.config.yaml" "$COSTRUZIONE/quartz.config.yaml"

cd "$COSTRUZIONE"
npm ci

# I plugin dichiarati in quartz.config.yaml vengono scaricati e cablati in
# .quartz/ da questo passo. In Quartz è agganciato a "prebuild", che scatta
# solo con "npm run build": invocando "npx quartz build" non parte, e la
# costruzione fallisce su un import di ../../.quartz/plugins irrisolvibile.
npm run install-plugins
if [[ "${SERVI:-}" == "1" ]]; then
  npx quartz build --serve -o "$RADICE/public"
else
  npx quartz build -o "$RADICE/public"
fi

echo "sito costruito in $RADICE/public"
