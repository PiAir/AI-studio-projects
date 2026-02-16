# Chrome Extension voor LinkedIn

Chrome extensie voor het gestructureerd ophalen van LinkedIn berichten.

## 📋 Beschrijving

Een Chrome extensie die LinkedIn berichten kan lezen en gestructureerd ophalen voor verdere verwerking. De extensie kan content extraheren maar heeft beperkingen bij het omzetten van URLs naar hun oorspronkelijke vorm.

## 🎯 Doel

De extensie helpt bij:
- Het automatisch ophalen van LinkedIn berichten
- Het structureren van LinkedIn content
- Het verzamelen van posts voor analyse

## ⚠️ Bekende Beperkingen

De extensie kan helaas niet de LinkedIn tracking-URLs correct omzetten naar de oorspronkelijke URL's. LinkedIn gebruikt aangepaste URL-formaten die moeilijk te reverse-engineeren zijn.

## 🚀 Gebruik

### Installatie
1. Open Chrome en ga naar `chrome://extensions/`
2. Schakel "Developer mode" in (rechtsboven)
3. Klik op "Load unpacked"
4. Selecteer deze map

### Gebruik
Na installatie verschijnt het extensie-icoon in de Chrome toolbar. Details over het gebruik staan in de extensie zelf.

## 🛠️ Technische Details

- **Type**: Chrome Extension (Manifest V3)
- **Technologie**: JavaScript, Chrome Extension API
- **Permissions**: Toegang tot LinkedIn (zie manifest.json)
- **Background**: Service worker voor achtergrondprocessen
- **Offscreen**: Offscreen document voor specifieke taken

## 📁 Bestanden

- `manifest.json` - Extensie configuratie
- `background.js` - Service worker
- `content_script.js` - Script dat draait op LinkedIn pagina's
- `popup.html` / `popup.js` - Popup interface
- `offscreen.html` / `offscreen.js` - Offscreen document
- `icons/` - Extensie iconen
- `log/` - Log bestanden

## 📝 Ontwikkeld met

Deze extensie is (deels) ontwikkeld met hulp van AI Studio (Google).

## 🔒 Privacy

De extensie werkt alleen op LinkedIn en verwerkt data lokaal. Geen data wordt verzonden naar externe servers.
