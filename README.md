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

## Langzeit-Archiv: mehr als 30 Tage sehen

Claude Code löscht die Session-Transkripte nach `cleanupPeriodDays` — **standardmässig 30 Tage**.
Danach ist die Datenquelle weg, und keine Auswertung der Welt bringt sie zurück. Wer nach einem Jahr
wissen will, wie sich die Nutzung entwickelt hat, muss vorher archivieren:

```bash
claude-usage --snapshot     # Aggregatzeilen sichern (Fenster: 20 Tage)
claude-usage --history --since 20260101 --monthly   # aus dem Archiv lesen
```

Das Archiv liegt in `~/.config/claude-usage/history.csv` und enthält **nur die Aggregate** —
eine Zeile pro Tag und Rechner (`date,host,cost_usd,tokens`). Ein Jahr sind rund 45 KB.
Die Transkripte selbst werden nicht angefasst; das Fenster hochzudrehen wäre die teure Variante
(Grössenordnung mehrere Dutzend GB pro Jahr).

Der Snapshot ist idempotent: Tage, die schon im Archiv stehen, werden nur aktualisiert, und
angebrochene Tage korrigieren sich beim nächsten Lauf von selbst. Liefert ein Rechner nichts —
SSH tot oder `ccusage` kaputt —, bleiben seine bestehenden Archivzeilen unangetastet und es gibt
eine Warnung. Ein stiller Messausfall darf keine Historie löschen.

**Regelmässig laufen lassen.** Wöchentlich reicht: das 20-Tage-Fenster überlappt die 30-Tage-Löschung
dreifach, also sind zwei ausgefallene Läufe folgenlos. Die Tagesgranularität im Archiv hängt nicht an
der Laufhäufigkeit — `ccusage` liefert Tageszeilen, egal wann man fragt.

<details>
<summary>macOS: wöchentlicher launchd-Job</summary>

`~/Library/LaunchAgents/com.example.claude-usage-snapshot.plist` anlegen, `USER` ersetzen, dann
`launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.claude-usage-snapshot.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.example.claude-usage-snapshot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/USER/bin/claude-usage</string>
        <string>--snapshot</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key><integer>1</integer>
        <key>Hour</key><integer>10</integer>
        <key>Minute</key><integer>15</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/USER/.config/claude-usage/snapshot.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/USER/.config/claude-usage/snapshot.log</string>
</dict>
</plist>
```

Verpasste Termine holt launchd beim Aufwachen nach — auf einem Laptop, der nicht durchläuft,
ist genau dafür das grosszügige Fenster da. Nach dem Einrichten einmal
`launchctl kickstart -k gui/$(id -u)/com.example.claude-usage-snapshot` und in die Logdatei schauen:
SSH zu den Remote-Rechnern verhält sich unter launchd anders als in der interaktiven Shell.
</details>

## Optional: schicker Graph

Die Zahlen lassen sich leicht als Graph rendern. Empfohlen 2026: eine kleine
HTML-Seite mit [Chart.js](https://www.chartjs.org/) (öffnet im Browser, keine Installation nötig).
Frag deinen Claude Code: *„erzeug mir aus `claude-usage --days 30` einen gestapelten Balken-Graph
pro Rechner als HTML mit Chart.js und öffne ihn."*

## Lizenz

MIT — nimm's, pass es an, teile es.
