# Smart-me Integration für Home Assistant

Bindet alle Geräte aus einem [smart-me](https://smart-me.com)-Konto (Strom, Wasser warm/kalt, Gas, Wärme) automatisch in Home Assistant ein – inklusive Kompatibilität mit dem Energie-Dashboard.

Die Zuordnung (Strom vs. Wasser vs. Wärme, warm/kalt) erfolgt automatisch anhand der von der smart-me-API gemeldeten Gerätetypen – es müssen keine Geräte-Rollen manuell zugewiesen werden.

## Installation über HACS

Damit HACS dieses Repository erkennt, muss `custom_components/` im **Root** des GitHub-Repositorys liegen, das du bei HACS einträgst. Konkret bedeutet das:

1. Erstelle ein **eigenes GitHub-Repository** nur für diesen Ordner (z.B. `Smart-Me-Integration`) und push den Inhalt dieses Ordners (`hacs.json`, `custom_components/`, `README.md`) dorthin – nicht das ganze `smart-home-raspberry`-Repo.
2. In Home Assistant: **HACS → drei Punkte oben rechts → Benutzerdefinierte Repositories**
3. URL deines neuen Repos eintragen, Kategorie **Integration**
4. Über HACS die Integration suchen und installieren
5. Home Assistant neu starten

## Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen** → "Smart-me" suchen
2. Benutzername (E-Mail) und Passwort deines smart-me-Kontos eingeben
3. Im zweiten Schritt die gewünschten Geräte auswählen (Vorauswahl: alle)
4. Fertig – die Zähler erscheinen als Entitäten und können im **Energie-Dashboard** hinzugefügt werden

Die Geräteauswahl kann später jederzeit über die Integrations-Optionen (Zahnrad-Symbol) angepasst werden, z.B. wenn ein neues Gerät im smart-me-Konto dazukommt.

## Erzeugte Entitäten

Pro ausgewähltem Gerät:
- **Zählerstand** – kumulativer Wert (`state_class: total_increasing`), energie-dashboard-tauglich
- **Leistung** – Momentanwert (Strom: Watt, Wasser/Gas: Durchfluss), sofern von der API geliefert
