document.addEventListener('DOMContentLoaded', function () {
    const pages = document.querySelectorAll('.page');
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');
    const viewReportButton = document.getElementById('viewReportButton');
    const downloadReportButton = document.getElementById('downloadReportButton');

    const reportOutput = document.getElementById('report-output');
    if (!reportOutput) {
        console.error("Initialization Error: DOM element with ID 'report-output' not found. Report functionality will be impaired.");
        if (viewReportButton) viewReportButton.disabled = true;
        if (downloadReportButton) downloadReportButton.disabled = true;
    }

    let currentPageIndex = 0;
    const formData = {};

    const pageOrder = [
        'page-intro', 'page-rationales', 'page-samr', 'page-karakterisering',
        'page-differentieren', 'page-interactie', 'page-regie',
        'page-zelfregulering', 'page-assessment', 'page-opkomend',
        'page-kerneigenschappen', 'page-end', 'page-report'
    ];

    function showPage(index) {
        pages.forEach(page => page.classList.remove('active'));
        const pageToShow = document.getElementById(pageOrder[index]);
        if (pageToShow) {
             pageToShow.classList.add('active');
        }

        prevButton.style.display = index > 0 && pageOrder[index] !== 'page-intro' ? 'inline-block' : 'none';

        if (pageOrder[index] === 'page-end') {
            nextButton.style.display = 'none';
            viewReportButton.style.display = 'inline-block';
        } else if (pageOrder[index] === 'page-report') {
            nextButton.style.display = 'none';
            viewReportButton.style.display = 'none';
        } else if (pageOrder[index] === 'page-intro') {
             nextButton.style.display = 'inline-block';
             prevButton.style.display = 'none';
             viewReportButton.style.display = 'none';
        }
         else {
            nextButton.style.display = 'inline-block';
            viewReportButton.style.display = 'none';
        }

        if (pageOrder[index] === 'page-intro') {
            nextButton.textContent = 'Start iXscan';
        } else {
             nextButton.textContent = 'Volgende';
        }
    }

    function collectPageData(pageId) {
        const pageElement = document.getElementById(pageId);
        if (!pageElement) return;
        formData[pageId] = {};

        if (pageId === 'page-rationales') {
            formData[pageId].selected = Array.from(pageElement.querySelectorAll('input[name="rationales"]:checked')).map(cb => cb.labels[0].textContent);
            if (pageElement.querySelector('#rat-anders-cb').checked) {
                formData[pageId].anders = pageElement.querySelector('#rat-anders').value;
            }
        }
        if (pageId === 'page-samr') {
            formData[pageId].selected = Array.from(pageElement.querySelectorAll('input[name="samr"]:checked')).map(cb => cb.labels[0].textContent);
        }
        if (pageId === 'page-karakterisering') {
            formData[pageId].selected = Array.from(pageElement.querySelectorAll('input[name="karakterisering"]:checked')).map(cb => cb.labels[0].textContent);
             if (pageElement.querySelector('#kar-anders-cb').checked) {
                formData[pageId].anders = pageElement.querySelector('#kar-anders').value;
            }
        }
        if (pageId === 'page-differentieren') {
            formData[pageId].main = pageElement.querySelector('#diff-main').checked;
            if (formData[pageId].main) {
                formData[pageId].subItems = [];
                pageElement.querySelectorAll('.differentiëren-item').forEach((item) => {
                    const mainCheckbox = item.querySelector(`input[type="checkbox"][id^="diff-sub"]`);
                    if (mainCheckbox.checked) {
                        const neeCheckbox = item.querySelector(`.conditional-input-container input[type="checkbox"]`);
                        const levelInput = item.querySelector(`.conditional-input-container input[type="number"]`);
                        formData[pageId].subItems.push({
                            label: mainCheckbox.dataset.label,
                            isNee: neeCheckbox.checked,
                            level: neeCheckbox.checked ? levelInput.value : null
                        });
                    }
                });
                if (pageElement.querySelector('#diff-anders-cb').checked) {
                   formData[pageId].anders = pageElement.querySelector('#diff-anders').value;
                }
            }
        }
        if (pageId === 'page-interactie') {
            const selectedRadio = pageElement.querySelector('input[name="interactie"]:checked');
            formData[pageId].selected = selectedRadio ? selectedRadio.labels[0].textContent : null;
        }
        if (pageId === 'page-regie') {
            formData[pageId].regie = {};
            pageElement.querySelectorAll('.mate-van-regie-table tbody tr').forEach(row => {
                const questionText = row.cells[0].textContent.trim();
                const checkedBox = row.querySelector('input[type="checkbox"]:checked');
                if (checkedBox) {
                    const columnHeaderIndex = Array.from(row.cells).indexOf(checkedBox.closest('td'));
                    const actor = pageElement.querySelectorAll('.mate-van-regie-table thead th')[columnHeaderIndex].textContent.trim();
                    formData[pageId].regie[questionText] = actor;
                }
            });
        }
        if (pageId === 'page-zelfregulering') {
            formData[pageId].main = pageElement.querySelector('#zelfreg-main').checked;
            if (formData[pageId].main) {
                formData[pageId].fases = Array.from(pageElement.querySelectorAll('input[name="zelfregulering_fase"]:checked')).map(cb => cb.labels[0].textContent);
                if (pageElement.querySelector('#zelfreg-anders-cb').checked) {
                    formData[pageId].anders = pageElement.querySelector('#zelfreg-anders').value;
                }
            }
        }
        if (pageId === 'page-assessment') {
            formData[pageId].main = pageElement.querySelector('#assess-main').checked;
            if (formData[pageId].main) {
                formData[pageId].hoe = Array.from(pageElement.querySelectorAll('input[name="assessment_hoe"]:checked')).map(cb => cb.labels[0].textContent);
                 if (pageElement.querySelector('#assess-anders-cb').checked) {
                    formData[pageId].anders = pageElement.querySelector('#assess-anders').value;
                }
            }
        }
        if (pageId === 'page-opkomend') {
            formData[pageId].selected = Array.from(pageElement.querySelectorAll('input[name="opkomend"]:checked')).map(cb => cb.labels[0].textContent);
        }
        if (pageId === 'page-kerneigenschappen') {
            formData[pageId].selected = Array.from(pageElement.querySelectorAll('input[name="kerneigenschappen"]:checked')).map(cb => cb.labels[0].textContent);
             if (pageElement.querySelector('#kern-anders-cb').checked) {
                formData[pageId].anders = pageElement.querySelector('#kern-anders').value;
            }
        }
    }

    function markdownToHtml(md) {
        if (!md) return "";

        let html = md;
        // ### Headers to <h3>
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');

        // **bold** to <strong>
        html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');

        // - list items to <li>
        // This is a bit more complex if lists are multiline or nested,
        // but for simple lists:
        html = html.replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');

        // Wrap consecutive <li> items in <ul>
        // This regex looks for <li> followed by more <li> or other content not starting with <ul>
        // It's a simplified approach. A more robust parser would be needed for complex cases.
        html = html.replace(/^(<li>.*<\/li>\s*)+/gim, (match) => `<ul>${match}</ul>`);

        // Newlines to <br> (careful with this, as Markdown usually means double newline for paragraph)
        // For this specific report structure, replacing single newlines might be okay
        // If we want proper paragraphs, we'd need to split by \n\n
        html = html.replace(/\n/g, '<br>');

        // Remove <br> inside <ul> or <ol> if they were added incorrectly by the above
        html = html.replace(/<ul><br\s*\/?>/gi, '<ul>');
        html = html.replace(/<\/li><br\s*\/?>/gi, '</li>');


        return html;
    }


    function generateReportAndDisplay() {
        const currentReportOutput = document.getElementById('report-output');
        if (!currentReportOutput) {
            console.error("generateReportAndDisplay Error: DOM element with ID 'report-output' not found.");
            return ""; // Return empty or handle error
        }

        let reportMd = ""; // This will hold the Markdown content

        if (formData['page-rationales']) {
            reportMd += "### Rationales\n";
            let rationalesList = formData['page-rationales'].selected.map(item => `- ${item}`).join("\n");
            if (formData['page-rationales'].anders) {
                rationalesList += (rationalesList ? "\n" : "") + `- Anders: ${formData['page-rationales'].anders}`;
            }
            reportMd += rationalesList ? `Er is gebruikgemaakt van de volgende reden(en) om ict in te zetten:\n${rationalesList}\n\n` : "Geen rationales geselecteerd.\n\n";
        }

        if (formData['page-samr'] && formData['page-samr'].selected.length > 0) {
            reportMd += "### SAMR\n";
            reportMd += formData['page-samr'].selected.map(s => {
                const parts = s.split(':');
                return parts.length > 1 ? `- **${parts[0].trim()}**: ${parts.slice(1).join(':').trim()}` : `- ${s}`;
            }).join("\n") + "\n\n";
        }

        if (formData['page-karakterisering']) {
            reportMd += "### Karakterisering ict-inzet\n";
            let karakteriseringenList = formData['page-karakterisering'].selected.map(item => `- ${item}`).join("\n");
            if (formData['page-karakterisering'].anders) {
                karakteriseringenList += (karakteriseringenList ? "\n" : "") + `- Anders: ${formData['page-karakterisering'].anders}`;
            }
            reportMd += karakteriseringenList ? `De inzet van ICT wordt gekenmerkt door:\n${karakteriseringenList}\n\n` : "Geen karakterisering geselecteerd.\n\n";
        }

        if (formData['page-differentieren']) {
            reportMd += "### Cyclus van differentiëren\n";
            if (formData['page-differentieren'].main) {
                reportMd += "ICT wordt ingezet om te differentiëren.\n";
                if (formData['page-differentieren'].subItems && formData['page-differentieren'].subItems.length > 0) {
                    formData['page-differentieren'].subItems.forEach(item => {
                        reportMd += `- ${item.label}`;
                        if (item.isNee && item.level) {
                            reportMd += ` (Niet voor alle studenten hetzelfde, niveau ${item.level})\n`;
                        } else {
                            reportMd += "\n";
                        }
                    });
                }
                 if (formData['page-differentieren'].anders) {
                    reportMd += `- Anders: ${formData['page-differentieren'].anders}\n`;
                }
            } else {
                reportMd += "ICT wordt niet ingezet om te differentiëren.\n";
            }
            reportMd += "\n";
        }

        if (formData['page-interactie'] && formData['page-interactie'].selected) {
            reportMd += "### Interactie tussen student, docent en ict\n";
            reportMd += `- ${formData['page-interactie'].selected}\n\n`;
        }

        if (formData['page-regie'] && Object.keys(formData['page-regie'].regie).length > 0) {
            reportMd += "### Mate van regie\n";
            for (const [question, actor] of Object.entries(formData['page-regie'].regie)) {
                reportMd += `- ${question}: **${actor}** bepaalt het meest.\n`;
            }
            reportMd += "\n";
        }

        if (formData['page-zelfregulering']) {
            reportMd += "### Zelfregulerende vaardigheden\n";
            if (formData['page-zelfregulering'].main) {
                reportMd += "ICT wordt ingezet om zelfregulerende vaardigheden te bevorderen";
                if (formData['page-zelfregulering'].fases && formData['page-zelfregulering'].fases.length > 0) {
                    reportMd += " in de volgende fase(s):\n";
                    reportMd += formData['page-zelfregulering'].fases.map(f => `- ${f}`).join("\n") + "\n";
                } else {
                    reportMd += ".\n";
                }
                if (formData['page-zelfregulering'].anders) {
                    reportMd += `- Anders: ${formData['page-zelfregulering'].anders}\n`;
                }
            } else {
                reportMd += "ICT wordt niet ingezet voor zelfregulerende vaardigheden.\n";
            }
            reportMd += "\n";
        }

        if (formData['page-assessment']) {
            reportMd += "### Assessment\n";
            if (formData['page-assessment'].main) {
                reportMd += "ICT wordt ingezet voor assessment";
                if (formData['page-assessment'].hoe && formData['page-assessment'].hoe.length > 0) {
                    reportMd += " als volgt:\n";
                    reportMd += formData['page-assessment'].hoe.map(h => `- ${h}`).join("\n") + "\n";
                } else {
                     reportMd += ".\n";
                }
                 if (formData['page-assessment'].anders) {
                    reportMd += `- Anders: ${formData['page-assessment'].anders}\n`;
                }
            } else {
                reportMd += "ICT wordt niet ingezet voor assessment.\n";
            }
            reportMd += "\n";
        }

        if (formData['page-opkomend'] && formData['page-opkomend'].selected.length > 0) {
            reportMd += "### Opkomende technologieën\n";
            reportMd += "De volgende opkomende technologieën zijn van toepassing:\n";
            reportMd += formData['page-opkomend'].selected.map(o => `- ${o}`).join("\n") + "\n\n";
        }

        if (formData['page-kerneigenschappen']) {
            reportMd += "### Kerneigenschappen ict\n";
            let kernEigenschappenList = formData['page-kerneigenschappen'].selected.map(item => `- ${item}`).join("\n");
            if (formData['page-kerneigenschappen'].anders) {
                kernEigenschappenList += (kernEigenschappenList ? "\n" : "") + `- Anders: ${formData['page-kerneigenschappen'].anders}`;
            }
            reportMd += kernEigenschappenList ? `De ICT-tool heeft de volgende kerneigenschappen:\n${kernEigenschappenList}\n\n` : "Geen kerneigenschappen geselecteerd.\n\n";
        }

        const reportHtml = markdownToHtml(reportMd.trim() ? reportMd : "Er zijn nog geen selecties gemaakt.");
        currentReportOutput.innerHTML = reportHtml;
        return reportMd; // Return the raw Markdown for download
    }

    nextButton.addEventListener('click', () => {
        collectPageData(pageOrder[currentPageIndex]);
        if (currentPageIndex < pageOrder.length - 1) {
            if (pageOrder[currentPageIndex] === 'page-end') {
                currentPageIndex = pageOrder.indexOf('page-report');
                generateReportAndDisplay();
            } else {
                currentPageIndex++;
            }
            showPage(currentPageIndex);
        }
    });

    prevButton.addEventListener('click', () => {
        if (currentPageIndex > 0) {
            if (pageOrder[currentPageIndex] === 'page-report') {
                currentPageIndex = pageOrder.indexOf('page-end');
            } else {
                currentPageIndex--;
            }
            showPage(currentPageIndex);
        }
    });

    viewReportButton.addEventListener('click', () => {
        collectPageData(pageOrder[currentPageIndex]);
        currentPageIndex = pageOrder.indexOf('page-report');
        generateReportAndDisplay();
        showPage(currentPageIndex);
    });

    if (downloadReportButton) {
        downloadReportButton.addEventListener('click', () => {
            const reportTextForDownload = generateReportAndDisplay(); // This function now returns Markdown
            if (reportTextForDownload === undefined || reportTextForDownload === "") {
                 console.error("Download Error: Report content is empty or unavailable.");
                 alert("Kon rapport niet downloaden omdat de inhoud leeg of niet beschikbaar is.");
                 return;
            }

            const filename = "iXscan_Resultaten.md";
            const blob = new Blob([reportTextForDownload], { type: 'text/markdown;charset=utf-8' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }

    const diffMainCheckbox = document.getElementById('diff-main');
    const diffSubquestionsDiv = document.getElementById('diff-subquestions');
    const diffSkipMessageDiv = document.getElementById('diff-skip-message');

    if (diffMainCheckbox) {
        diffMainCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            diffSubquestionsDiv.classList.toggle('hidden', !isChecked);
            diffSkipMessageDiv.classList.toggle('hidden', isChecked);
        });
    }

    document.querySelectorAll('.differentiëren-item .conditional-input-container input[type="checkbox"]').forEach(cb => {
        cb.addEventListener('change', function() {
            const levelInput = this.parentElement.querySelector('input[type="number"]');
            levelInput.classList.toggle('hidden', !this.checked);
            if (!this.checked) levelInput.value = '';
        });
    });

    const zelfregMainCheckbox = document.getElementById('zelfreg-main');
    const zelfregSubquestionsDiv = document.getElementById('zelfreg-subquestions');
    const zelfregSkipMessageDiv = document.getElementById('zelfreg-skip-message');

    if (zelfregMainCheckbox) {
        zelfregMainCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            zelfregSubquestionsDiv.classList.toggle('hidden', !isChecked);
            zelfregSkipMessageDiv.classList.toggle('hidden', isChecked);
        });
    }

    const assessMainCheckbox = document.getElementById('assess-main');
    const assessSubquestionsDiv = document.getElementById('assess-subquestions');
    const assessSkipMessageDiv = document.getElementById('assess-skip-message');

    if (assessMainCheckbox) {
        assessMainCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            assessSubquestionsDiv.classList.toggle('hidden', !isChecked);
            assessSkipMessageDiv.classList.toggle('hidden', isChecked);
        });
    }

    document.querySelectorAll('.mate-van-regie-table tbody tr').forEach(row => {
        const checkboxes = row.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => {
            cb.addEventListener('change', function() {
                if (this.checked) {
                    checkboxes.forEach(otherCb => {
                        if (otherCb !== this) otherCb.checked = false;
                    });
                }
            });
        });
    });

    showPage(currentPageIndex);
});