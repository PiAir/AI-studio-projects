# Weefgetouw Digitale Geletterdheid

Een interactieve, dynamische webapplicatie voor het in kaart brengen, ontwerpen en weven van leerdoelen binnen het curriculum van digitale geletterdheid.

## 📋 Beschrijving

Het Weefgetouw is een flexibele tool die scholen en docenten ondersteunt bij het concreet maken van digitale geletterdheid in hun onderwijsprogramma. Oorspronkelijk ontstaan als een Miro-bord, is deze versie nu beschikbaar als standalone webapplicatie voor een eenvoudigere en interactievere ervaring. 

De tool is nu volledig geschikt en geüpdatet voor de nieuwste onderwijskaders:
- **Nieuwe SLO Concept-kerndoelen Digitale Geletterdheid (po/vo)**
- **Nieuwe DigComp 3.0 Europees Referentiekader**

Door gebruik te maken van flexibele JSON-bestanden kan de content en het onderliggende raamwerk eenvoudig worden gewisseld of aangepast via de dropdown in de header van de applicatie.

## 🎯 Doel

Het Weefgetouw helpt docenten, curriculumontwerpers en onderwijsinstellingen om:
- Leerdoelen visueel te koppelen aan bestaande vakken en leerjaren (het "weven" van het curriculum)
- Duidelijke leerlijnen en verbanden te leggen tussen verschillende domeinen van digitale geletterdheid
- Zowel de SLO-kerndoelen (primair- en voortgezet onderwijs) als het Europese DigComp 3.0-kader direct toe te passen
- Een exporteerbaar en printbaar curriculumoverzicht te genereren voor teams en partners

## 📚 Ondersteunde Raamwerken

Het Weefgetouw bevat standaard twee up-to-date raamwerken die eenvoudig via de dropdown in de header geselecteerd kunnen worden:

### 1. SLO Concept-kerndoelen (po/vo)
Gebaseerd op de nieuwste concept-kerndoelen van SLO voor Digitale Geletterdheid in het primair onderwijs (po) en voortgezet onderwijs (vo). Dit raamwerk is opgebouwd rond de bekende inhoudslijnen:
*   **Praktische kennis en vaardigheden**
*   **De gedigitaliseerde wereld**
*   **Ontwerpen en maken**
*   **Informatie**

### 2. DigComp 3.0
Het vernieuwde Europese referentiekader voor digitale competenties van burgers (vertaald naar het Nederlands). Dit kader deelt digitale competenties in over 5 competentiegebieden met 21 competenties, verdeeld over 4 heldere beheersingsniveaus (weergegeven als Fase 1 t/m 4):
*   **Basis**
*   **Gemiddeld**
*   **Gevorderd**
*   **Zeer gevorderd**

## 🚀 Gebruik & Lokaal Testen

⚠️ **Belangrijk bij lokaal gebruik**: Vanwege browserbeveiliging (CORS-beperkingen) kunnen de JSON-bestanden met leerdoelen niet direct vanaf het lokale bestandssysteem (`file://`) worden geladen. Start een eenvoudige lokale webserver om de volledige functionaliteit te ervaren.

### Een lokale server starten

Start een webserver in de map van het Weefgetouw met een van de volgende commando's:

```bash
# Met Python 3
python -m http.server 8000

# Of met Node.js / npx
npx serve
```
Open vervolgens `http://localhost:8000` (of de poort die `serve` aangeeft) in je browser.

## 🔗 Links en Bronnen

- **Live Demo**: [Weefgetouw bij iXperium](https://www.ixperium.nl/ixperiumtools/weefgetouw-digitale-geletterdheid-digcomp/)
- **Achtergrond & Uitleg**: [Blogpost](https://ictoblog.nl/2025/07/14/weefgetouw-digitale-geletterdheidgeletterdheid)
- **SLO Informatie**: [SLO Digitale Geletterdheid](https://www.slo.nl/)
- **DigComp 3.0**: [Nederlandse vertaling (iXperium)](https://www.ixperium.nl/publicaties/digcomp-3-0-nederlandse-vertaling/)

## 🛠️ Technische Details

- **Type**: Single-page HTML5/CSS3/JavaScript-applicatie
- **Frameworks**: Vue.js v3 (via CDN, voor state management en reactivity) en Tailwind CSS (voor responsive en modern design)
- **Dependencies**: Geen (geheel standalone, draait volledig in de browser)
- **Configuratie**: Volledig gestuurd door JSON-data, waardoor makkelijk uit te breiden met eigen leerdoelen of vakkenstructuren.

## 📁 Bestanden

- `index.html` - De hoofdpagina van het Weefgetouw met alle UI en logica.
- `weefgetouw_slo_full_v11.json` - Het complete databestand met de SLO concept-kerndoelen (po/vo) en initiële plaatsingen.
- `weefgetouw_digcomp_v1.json` - Het complete databestand met het DigComp 3.0-raamwerk (vertaald naar het Nederlands).
- `leerdoelen.csv` & `leerdoelen.xlsx` - Referentiebestanden/legacy data met leerdoelen.

## 📝 Licentie en Ontwikkeling

Het Weefgetouw is ontwikkeld door de **Werkgroep Digitale Geletterdheid van iXperium Nijmegen** in samenwerking met diverse regionale scholen, besturen (o.a. SPOG, Optimus, Kans en Kleur, Stichting St. Josephscholen), de HAN Pabo, en onderzoekers van het iXperium.

Beschikbaar onder licentie **Creative Commons Naamsvermelding-NietCommercieel 4.0 Internationaal (CC BY-NC 4.0)**.

Gegenereerd en verfijnd met behulp van **AI Studio (Google)**.
