# NOLAI Taiwan - Onderwijsinnovatie

Video-presentatie over onderwijsinnovatie in Taiwan met meertalige ondertiteling.

## 📋 Beschrijving

Een interactieve webapplicatie die een video-presentatie toegankelijk maakt over onderwijsinnovatie en het gebruik van technologie in het Taiwanese onderwijs. De applicatie biedt meertalige ondertiteling (Nederlands en Engels) voor een breed publiek.

## 🎯 Doel

De presentatie biedt inzicht in:
- Onderwijsinnovatie in Taiwan
- Het gebruik van technologie in het onderwijs
- Internationale perspectieven op digitale geletterdheid
- Best practices uit het Aziatische onderwijs

## ✨ Features

- **Meertalige ondertiteling**: Nederlands en Engels
- **Video embedding**: Geïntegreerde video player
- **Responsive design**: Werkt op mobiele apparaten en desktop
- **WebVTT ondertitels**: Gesynchroniseerde ondertiteling

## 🚀 Gebruik

Het bestand `index.html` kan direct in een browser worden geopend. Selecteer de gewenste taal voor de ondertiteling.

## 🛠️ Technische Details

- **Type**: Single-page HTML applicatie
- **Technologie**: HTML, CSS, JavaScript, VTT (WebVTT ondertiteling)
- **Dependencies**: Geen externe libraries
- **Hosting**: Kan lokaal draaien of op elke webserver

## 📁 Bestanden

- `index.html` - Hoofdapplicatie
- `subtitles_nl.vtt` - Nederlandse ondertitels
- `subtitles_en.vtt` - Engelse ondertitels

## 📝 Oorspronkelijke Prompt

```
Create a multilingual static website in English and Dutch using the included HTML file as an example for the layout and the JavaScript used to overlay the subtitels.
It contains a selection box for subtitle language, change that to a selection box for the language of the full page.
Create a VTT subtitles file for the included video both in English and in Dutch.
Check the syntax of the VTT after creation to make sure it conforms to the requirements
After that, summarize the video, extract the important topics, questions and answers.
Create the needed HTML file according to the multilingual static website project with a YouTube embed for the video with the VTT file displayed on top of the video. On the left side create tabbed navigation for the topics, selecting them gives an overview of the questions and answers within that topic, the video also jumps to that part of the video. The questions and answers also contain time codes that navigate to that section of the video. Double check the JavaScript code for the YouTube navigation after you have created it so you know it works.
Also make it so that it works on different screen sizes, I want to be able to view it on mobile devices (smartphones) and bigger screens.
The YouTube ID for the video to use in is: lUVy2XIrNqw so link to https://www.youtube.com/watch?v=lUVy2XIrNqw
```

Deze prompt werkte bijna perfect. Het YT-venster was nog wat groot, na het uploaden van een screenshot hiervan kreeg ik een stukje bijgewerkte CSS en complete HTML die wel goed was.

## 🎓 Gegenereerd met

AI Studio (Google) - Inclusief de VTT-ondertitelbestanden
