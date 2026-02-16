# C2PA Viewer

Tool voor het bekijken, analyseren en verwijderen van C2PA metadata in AI-gegenereerde media.

## 📋 Beschrijving

De C2PA Viewer maakt het mogelijk om C2PA (Coalition for Content Provenance and Authenticity) metadata te bekijken die door verschillende bedrijven automatisch wordt toegevoegd aan afbeeldingen, video's en audio die met AI zijn gegenereerd. De tool kan deze metadata ook verwijderen indien gewenst.

## 🎯 Doel

C2PA metadata helpt bij:
- Het herkennen van AI-gegenereerde content
- Het traceren van de oorsprong van media
- Transparantie over bewerkingen en manipulaties
- Bestrijden van desinformatie

Deze tool maakt deze metadata toegankelijk en manipuleerbaar.

## 🏢 Ondersteunde Platforms

Op dit moment (mei 2025) gebruiken deze grote bedrijven C2PA:
- **OpenAI** - Voor AI-gegenereerde afbeeldingen
- **Adobe** - In Creative Cloud applicaties
- **Microsoft** - In diverse tools
- **LinkedIn** - Voor geüploade content

**Let op**: Google is een zichtbare afwezige, hoewel ze wel lid zijn van C2PA.

## ✨ Features

- **Metadata weergeven**: Bekijk alle C2PA informatie in media bestanden
- **Afbeeldingen verwijderen**: Voor afbeeldingen is dit eenvoudig (screenshot maken)
- **Video/Audio**: Vereist conversie naar ander formaat of schermopname

## 🚀 Gebruik

Deze applicatie vereist Docker omdat het een Python/Flask backend gebruikt.

### Installatie

```bash
# Met Docker Compose
docker-compose up -d

# Of handmatig bouwen
docker build -t c2pa-viewer .
docker run -p 5000:5000 c2pa-viewer
```

### Gebruik
1. Open de applicatie in je browser (standaard: http://localhost:5000)
2. Upload een afbeelding (JPG of PNG)
3. Als C2PA metadata aanwezig is, wordt deze weergegeven
4. Download de JSON output voor verdere analyse

## 🔗 Links

- [Live demo](https://c2pa.ictoblog.com/)
- [Blogpost](https://ictoblog.nl/2025/05/30/gaat-c2pa-orde-in-de-ai-generatie-chaos-brengen)

## 🛠️ Technische Details

- **Type**: Webapplicatie met Python backend
- **Technologie**: 
  - Backend: Python, Flask
  - Frontend: HTML, CSS, JavaScript
  - C2PA: c2pa-python library
- **Hosting**: Vereist Docker
- **Ondersteunde formaten**: JPG, PNG (afbeeldingen)

## 📁 Bestanden

### Root
- `docker-compose.yml` - Docker Compose configuratie
- `Dockerfile` - Docker image definitie

### App directory (app/)
- `app.py` - Flask applicatie
- `requirements.txt` - Python dependencies
- `templates/` - HTML templates
- `static/` - CSS, JavaScript, afbeeldingen
- `json_outputs/` - Opslag voor gegenereerde JSON

### Uploads
- `uploads/` - Tijdelijke opslag voor geüploade bestanden

## ⚠️ Beperkingen

- **Video/Audio**: Het verwijderen van metadata uit video en audio is complexer
- Vereist conversie naar ander formaat of het maken van een schermopname
- Nog geen voorbeeldbestand voor audio beschikbaar

## 📖 Over C2PA

C2PA (Coalition for Content Provenance and Authenticity) is een standaard ontwikkeld door een consortium van tech-bedrijven voor het toevoegen van metadata aan digitale content. Dit helpt bij het traceren van de oorsprong en het detecteren van manipulaties.

## 📝 Ontwikkeld met

AI Studio (Google) - Met veel meer dan 1 prompt. Zie het bericht op ictoblog.nl voor uitleg over het ontwikkelproces.
