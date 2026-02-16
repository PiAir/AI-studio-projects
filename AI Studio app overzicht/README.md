# AI Studio App Overzicht

Landingspagina voor alle AI Studio applicaties met JSON-configuratie.

## 📋 Beschrijving

Een meta-applicatie die zelf ook door AI Studio is gegenereerd. Deze landingspagina toont een overzicht van alle applicaties in deze repository en wordt dynamisch gegenereerd op basis van een JSON-configuratiebestand.

## 🎯 Doel

De landingspagina biedt:
- Een visueel overzicht van alle beschikbare applicaties
- Links naar live demo's en blogposts
- Automatische navigatiestructuur voor grote aantallen apps (>6)
- Eenvoudig beheer via JSON-configuratie

## ✨ Features

- **Dynamische content**: Alle app-informatie wordt ingeladen uit `sites.json`
- **Automatische paginering**: Bij meer dan 6 apps wordt navigatie automatisch getoond
- **Responsive design**: Werkt op desktop en mobiele apparaten
- **Eenvoudig uitbreiden**: Voeg een app toe aan de JSON en hij verschijnt automatisch

## 🚀 Gebruik

1. Open `index.html` in een browser
2. Browse door de beschikbare applicaties
3. Klik op een app om de live demo te openen

### App toevoegen

Voeg een nieuw object toe aan `sites.json`:

```json
{
  "volgnummer": 12,
  "url": "https://example.com/app/",
  "afbeeldingUrl": "images/app12.png",
  "titel": "App Titel",
  "omschrijving": "Beschrijving van de app",
  "blogpost-url": "https://blog.com/post"
}
```

## 🔗 Links

- [Live demo](https://ictoblog.com/html/)
- [Blogpost](https://ictoblog.nl/2025/05/27/krijgen-we-door-ai-straks-wegwerpapplicaties-in-het-onderwijs)

## 🛠️ Technische Details

- **Type**: Single-page HTML applicatie met JSON data
- **Technologie**: HTML, CSS (embedded), JavaScript (embedded), JSON
- **Dependencies**: Geen
- **Hosting**: Kan lokaal draaien of op elke webserver

## 📁 Bestanden

- `index.html` - Hoofdapplicatie
- `sites.json` - Configuratie met alle app-informatie
- `images/` - Screenshots van de apps

## 📝 TODO

Het is nog niet mogelijk om hyperlinks in de beschrijvingen op te nemen, terwijl dat handig kan zijn om bijvoorbeeld naar een blogpost over een pagina te verwijzen.

## 🎨 Gegenereerd met

AI Studio (Google) - Om meteen maar even helemaal meta te gaan: deze pagina met apps is ook door AI Studio gegenereerd!
