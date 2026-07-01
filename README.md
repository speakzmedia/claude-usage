# claude-usage

Miss, **wie viel du mit Claude Code gearbeitet hast — über mehrere Rechner und alle Accounts zusammen**.

Claude Code speichert für jede Session ein Transkript unter `~/.claude/`. Das populäre Tool
[`ccusage`](https://github.com/ryoppippi/ccusage) liest diese Transkripte und zeigt Token-Verbrauch
+ (äquivalente) API-Kosten pro Tag. Zwei wichtige Eigenschaften:

- Die Transkripte hängen an der **Maschine**, nicht am Login-Account → ein `ccusage`-Lauf pro Rechner
  erfasst automatisch **alle** Claude-Accounts, die dort genutzt wurden.
- Getrennt sind nur die **Maschinen** (z. B. Laptop vs. Desktop).

`claude-usage` ruft `ccusage` lokal **und** auf jedem deiner Remote-Rechner (per SSH) auf und
**addiert** die Ergebnisse zu einer Gesamtübersicht (Sessions sind rechnerlokal → keine Doppelzählung).

> Die Zahlen sind **äquivalente API-Preise** als Volumen-/Aktivitätsmaß — **nicht** der reale Betrag,
> den du auf einem Abo (Pro/Max) zahlst. Erfasst wird nur **Claude Code (CLI)**, nicht claude.ai im Browser.

## Voraussetzungen

- [Claude Code](https://claude.com/claude-code) auf jedem Rechner benutzt (erzeugt die Transkripte)
- `node` / `npx` auf jedem Rechner (für `ccusage`)
- Python 3 auf dem Rechner, von dem du das Tool startest
- **Schlüsselbasiertes SSH** zu jedem Remote-Rechner (kein Passwort-Prompt).
  [Tailscale-SSH](https://tailscale.com/kb/1193/tailscale-ssh) ist dafür ideal.

## Installation

```bash
# Script in einen PATH-Ordner legen (z. B. ~/bin) und ausführbar machen
mkdir -p ~/bin
curl -fsSL https://raw.githubusercontent.com/vincentborko/claude-usage/main/claude-usage -o ~/bin/claude-usage
chmod +x ~/bin/claude-usage
# sicherstellen, dass ~/bin im PATH ist (in ~/.zshrc):  export PATH="$HOME/bin:$PATH"
```

## Konfiguration

Nur die **Remote**-Rechner eintragen — der lokale zählt automatisch mit:

```bash
mkdir -p ~/.config/claude-usage
# Vorlage kopieren und anpassen:
curl -fsSL https://raw.githubusercontent.com/vincentborko/claude-usage/main/hosts.example -o ~/.config/claude-usage/hosts
$EDITOR ~/.config/claude-usage/hosts
```

Format (eine Zeile pro Remote-Rechner, `label=ssh_ziel`):

```
laptop=deinuser@100.x.y.z
desktop=deinuser@100.a.b.c
```

Ohne Config läuft es einfach nur für den lokalen Rechner.

## Verwendung

```bash
claude-usage                # letzte 7 Tage, täglich
claude-usage --days 30      # letzte 30 Tage
claude-usage --monthly      # monatlich statt täglich
claude-usage --since 20260601
```

Beispiel-Ausgabe:

```
Zeitraum    laptop-* $   desktop $   Summe $   Tokens Mio
------------------------------------------------------------
2026-06-30         421         357       779        971.3
...
------------------------------------------------------------
TOTAL             13103      10098     23201        28652
```

Ist ein Remote-Rechner offline, gibt's eine Warnung und der lokale zählt trotzdem — nichts hängt.

## Optional: schicker Graph

Die Zahlen lassen sich leicht als Graph rendern. Empfohlen 2026: eine kleine
HTML-Seite mit [Chart.js](https://www.chartjs.org/) (öffnet im Browser, keine Installation nötig).
Frag deinen Claude Code: *„erzeug mir aus `claude-usage --days 30` einen gestapelten Balken-Graph
pro Rechner als HTML mit Chart.js und öffne ihn."*

## Lizenz

MIT — nimm's, pass es an, teile es.
