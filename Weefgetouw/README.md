# Weefgetouw Digitale Geletterdheid

Een interactieve tool voor het in kaart brengen van leerdoelen binnen het raamwerk van digitale geletterdheid.

## 📋 Beschrijving

Een tool die al een tijdje in Miro beschikbaar is, maar nu als webapplicatie beschikbaar is voor eenvoudigere deling met partners. Deze versie gebruikt CSS en JavaScript met een extern JSON-bestand voor de leerdoelen, waardoor de content flexibel aangepast kan worden.

## 🎯 Doel

Het Weefgetouw helpt docenten en onderwijsinstellingen om:
- Leerdoelen in kaart te brengen volgens verschillende inhoudslijnen
- Verbanden te leggen tussen verschillende aspecten van digitale geletterdheid
- Een visueel overzicht te creëren van het curriculum

## 🚀 Gebruik

⚠️ **Let op**: Het laden van de JSON lijkt bij lokaal gebruik niet te werken door CORS-beperkingen. Draai de applicatie op een webserver of in een leeromgeving voor volledige functionaliteit.

### Lokaal testen

Voor lokaal gebruik kun je een eenvoudige webserver starten, bijvoorbeeld met Python:

```bash
# Python 3
python -m http.server 8000

# Of via Node.js
npx serve
```

## 🔗 Links

- [Live demo](https://ictoblog.com/html/Weefgetouw/)
- [Blogpost](https://ictoblog.nl/2025/07/14/weefgetouw-digitale-geletterdheidgeletterdheid)

## 🛠️ Technische Details

- **Type**: Single-page HTML applicatie
- **Technologie**: HTML, CSS, JavaScript, JSON (extern bestand)
- **Dependencies**: Geen externe libraries
- **Hosting**: Vereist webserver voor JSON loading

## 📁 Bestanden

- `index.html` - Hoofdbestand met de applicatie
- `inhoudslijnen.json` - Configuratie van de inhoudslijnen
- `leerdoelen.csv` - Leerdoelen (mogelijk niet meer in gebruik)

## 📝 Gegenereerd met

AI Studio (Google)
