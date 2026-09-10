#!/usr/bin/env bash
# Compila ogni blocco Mermaid del vault per intercettare gli errori di sintassi
# prima che raggiungano il lettore. I diagrammi sono generati dal codice, ma il
# testo che ci finisce dentro viene dai dati: un nome di elemento con un
# carattere che Mermaid interpreta rompe il diagramma senza rompere nulla
# d'altro, e nessun altro controllo se ne accorge.
#
# Senza argomenti controlla tutte le note del vault; con argomenti controlla
# soltanto i file indicati, così chi lavora in locale può limitarsi a ciò che
# ha appena cambiato.
set -euo pipefail

PARALLELISMO=${PARALLELISMO:-4}
LAVORO=$(mktemp -d)
trap 'rm -rf "$LAVORO"' EXIT

# mermaid-cli avvia un browser headless a ogni invocazione, e risolvere il
# pacchetto con "npx --yes" per ciascuna delle 118 note con diagrammi costa più
# della compilazione stessa: lo si installa una volta sola in una cartella
# temporanea, a meno che non sia già disponibile.
if command -v mmdc >/dev/null 2>&1; then
  MMDC=$(command -v mmdc)
else
  echo "Installazione di mermaid-cli..."
  npm install --silent --no-save --prefix "$LAVORO" @mermaid-js/mermaid-cli@11 >/dev/null
  MMDC="$LAVORO/node_modules/.bin/mmdc"
fi

# Nei runner di CI e nei container il browser headless non può usare il
# sandbox del kernel, e senza questa configurazione fallirebbe su ogni file.
cat > "$LAVORO/puppeteer.json" <<'JSON'
{ "args": ["--no-sandbox", "--disable-dev-shm-usage"] }
JSON

cat > "$LAVORO/compila.sh" <<COMPILA
#!/usr/bin/env bash
nota="\$1"
if ! "$MMDC" -p "$LAVORO/puppeteer.json" -i "\$nota" -o "$LAVORO/uscita-\$\$.md" >/dev/null 2>&1; then
  echo "\$nota"
fi
COMPILA
chmod +x "$LAVORO/compila.sh"

if [ "$#" -gt 0 ]; then
  printf '%s\0' "$@" > "$LAVORO/candidate"
else
  find vault -name '*.md' -print0 > "$LAVORO/candidate"
fi

# Solo le 118 note degli elementi contengono diagrammi: le pagine di
# navigazione, le epoche e gli scopritori sono le altre 109 del vault, e
# avviare un browser headless per ciascuna costerebbe quasi metà del tempo di
# questo controllo senza compilare nulla.
: > "$LAVORO/note"
while IFS= read -r -d '' nota; do
  if grep -q '```mermaid' "$nota"; then
    printf '%s\0' "$nota" >> "$LAVORO/note"
  fi
done < "$LAVORO/candidate"

TOTALE=$(tr -dc '\0' < "$LAVORO/note" | wc -c)
if [ "$TOTALE" -eq 0 ]; then
  echo "Nessuna nota contiene diagrammi Mermaid."
  exit 0
fi
xargs -0 -P "$PARALLELISMO" -n1 "$LAVORO/compila.sh" < "$LAVORO/note" > "$LAVORO/rotti"

if [ -s "$LAVORO/rotti" ]; then
  echo "Diagrammi non compilabili:"
  sed 's/^/  /' "$LAVORO/rotti"
  echo "$(wc -l < "$LAVORO/rotti") note su $TOTALE contengono diagrammi non validi."
  exit 1
fi

echo "Tutti i diagrammi Mermaid sono validi ($TOTALE note)."
