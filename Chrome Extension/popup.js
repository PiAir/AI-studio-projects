// popup.js
// ... (variables and setStatus function remain the same) ...
const extractButton = document.getElementById('extractButton');
const postTitleInput = document.getElementById('postTitle');
const postBodyTextarea = document.getElementById('postBody');
const copyTitleButton = document.getElementById('copyTitleButton');
const copyBodyButton = document.getElementById('copyBodyButton');
const imageLinksDiv = document.getElementById('imageLinks');
const originalUrlsDiv = document.getElementById('originalUrls');
const copyResolvedLinksButton = document.getElementById('copyResolvedLinksButton');
const statusMessageDiv = document.getElementById('statusMessage');
const extensionVersionDiv = document.getElementById('extensionVersion');

function setStatus(message, isError = false) {
  statusMessageDiv.textContent = message;
  statusMessageDiv.style.color = isError ? 'red' : '#555';
}

// Display extension version
if (extensionVersionDiv) {
  extensionVersionDiv.textContent = `v${chrome.runtime.getManifest().version}`;
}

extractButton.addEventListener('click', async () => {
  setStatus("Extracting content...");
  postTitleInput.value = '';
  postBodyTextarea.value = '';
  imageLinksDiv.innerHTML = '<p class="status">Extracting images...</p>';
  originalUrlsDiv.innerHTML = '<p class="status">Looking for lnkd.in links...</p>';

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  if (tab && tab.url && (tab.url.includes("linkedin.com/posts/") || tab.url.includes("linkedin.com/feed/update/urn:li:activity:") || tab.url.includes("linkedin.com/feed/update/urn:li:share:"))) {
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content_script.js']
      });
    } catch (e) {
      setStatus(`Error injecting script: ${e.message}`, true);
    }
  } else {
    setStatus("Please navigate to a LinkedIn post page (e.g., linkedin.com/posts/... or feed/update/...).", true);
  }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "scrapedData") {
    setStatus("Content extracted. Processing links...");
    const { body, imageUrls, linksToUnshorten } = request.data;

    postTitleInput.value = body ? body.substring(0, 70).split('\n')[0].trim() + (body.length > 70 ? "..." : "") : "LinkedIn Post";
    let processedBody = body || "Could not extract body content.";

    imageLinksDiv.innerHTML = '';
    if (imageUrls && imageUrls.length > 0) {
      imageUrls.forEach(url => {
        const div = document.createElement('div');
        const textSpan = document.createElement('span');
        textSpan.textContent = url + " ";
        div.appendChild(textSpan);
        const downloadButton = document.createElement('button');
        downloadButton.textContent = "Download";
        downloadButton.classList.add('secondary', 'download-image-btn');
        downloadButton.onclick = () => {
          const imageName = url.substring(url.lastIndexOf('/') + 1).split('?')[0] || "image.jpg";
          setStatus(`Downloading ${imageName}...`);
          chrome.runtime.sendMessage({ action: "downloadImage", imageUrl: url }, (response) => {
            if (chrome.runtime.lastError) {
                setStatus(`Failed to initiate download. ${chrome.runtime.lastError.message}`, true); return;
            }
            if (response && response.success) setStatus(`Download started for ${imageName}.`);
            else setStatus(`Failed to start download. ${response?.error || ''}`, true);
          });
        };
        div.appendChild(downloadButton);
        imageLinksDiv.appendChild(div);
      });
    } else {
      imageLinksDiv.innerHTML = '<p class="status">No direct image URLs found in the post content.</p>';
    }

    if (linksToUnshorten && Object.keys(linksToUnshorten).length > 0) {
      originalUrlsDiv.innerHTML = '<p class="status">Unshortening lnkd.in links...</p>';
      chrome.runtime.sendMessage({ action: "unshortenLinks", linksMap: linksToUnshorten }, (response) => {
        if (chrome.runtime.lastError) {
            setStatus(`Error unshortening links: ${chrome.runtime.lastError.message}`, true);
            originalUrlsDiv.innerHTML = '<p class="status">Error during link unshortening.</p>';
            postBodyTextarea.value = processedBody;
            return;
        }

        let allResolvedLinksForCopy = ""; // For the copy button

        if (response && response.unshortenedLinks && response.unshortenedLinks.length > 0) {
          originalUrlsDiv.innerHTML = '';

          response.unshortenedLinks.forEach(item => {
            const div = document.createElement('div');
            const a = document.createElement('a');
            a.href = item.resolvedUrl;
            a.textContent = item.resolvedUrl;
            a.title = `Original short link: ${item.shortUrl}`;
            a.target = "_blank";
            div.appendChild(a);
            // Add manual resolve button
            const resolveBtn = document.createElement('button');
            resolveBtn.textContent = 'Resolve';
            resolveBtn.className = 'secondary';
            resolveBtn.style.marginLeft = '8px';
            resolveBtn.onclick = () => {
              chrome.runtime.sendMessage({ action: 'openLinkInTab', url: item.resolvedUrl });
            };
            div.appendChild(resolveBtn);
            originalUrlsDiv.appendChild(div);

            allResolvedLinksForCopy += `${item.resolvedUrl}\n`;

            const placeholderRegex = new RegExp(item.placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
            processedBody = processedBody.replace(placeholderRegex, item.resolvedUrl);
          });
          copyResolvedLinksButton.dataset.resolvedLinks = allResolvedLinksForCopy.trim();
          setStatus("Extraction complete. Use the Resolve button to manually follow lnkd.in links.", false);

        } else if (response && response.error) {
            setStatus(`Error unshortening links: ${response.error}`, true);
            originalUrlsDiv.innerHTML = `<p class="status">Error: ${response.error}</p>`;
            copyResolvedLinksButton.dataset.resolvedLinks = "";
        } else {
            setStatus("Link unshortening finished; some links may not have resolved or no new links found.", false);
            originalUrlsDiv.innerHTML = '<p class="status">No new links found or some did not resolve.</p>';
            copyResolvedLinksButton.dataset.resolvedLinks = "";
        }
        postBodyTextarea.value = processedBody;
      });
    } else {
      originalUrlsDiv.innerHTML = '<p class="status">No lnkd.in links found to unshorten.</p>';
      postBodyTextarea.value = processedBody;
      copyResolvedLinksButton.dataset.resolvedLinks = "";
      setStatus("Extraction complete. No lnkd.in links to process.", false);
    }
  }
});

// ... (copyTitleButton and copyBodyButton event listeners remain the same) ...
copyTitleButton.addEventListener('click', () => {
  postTitleInput.select();
  try {
    navigator.clipboard.writeText(postTitleInput.value)
      .then(() => setStatus("Title copied!", false))
      .catch(err => setStatus(`Failed to copy title: ${err.message}`, true));
  } catch (err) {
    try { document.execCommand('copy'); setStatus("Title copied (fallback)!", false); }
    catch (fallbackErr) { setStatus(`Failed to copy title (fallback): ${fallbackErr.message}`, true); }
  }
});

copyBodyButton.addEventListener('click', () => {
  postBodyTextarea.select();
   try {
    navigator.clipboard.writeText(postBodyTextarea.value)
      .then(() => setStatus("Body copied!", false))
      .catch(err => setStatus(`Failed to copy body: ${err.message}`, true));
  } catch (err) {
    try { document.execCommand('copy'); setStatus("Body copied (fallback)!", false); }
    catch (fallbackErr) { setStatus(`Failed to copy body (fallback): ${fallbackErr.message}`, true); }
  }
});


copyResolvedLinksButton.addEventListener('click', () => {
  const linksToCopy = copyResolvedLinksButton.dataset.resolvedLinks;
  if (linksToCopy && linksToCopy.trim() !== "") {
    try {
      navigator.clipboard.writeText(linksToCopy)
        .then(() => setStatus("Resolved links copied!", false))
        .catch(err => setStatus(`Failed to copy resolved links: ${err.message}`, true));
    } catch (err) {
        try {
            const textArea = document.createElement("textarea");
            textArea.value = linksToCopy;
            textArea.style.position = "fixed"; document.body.appendChild(textArea);
            textArea.focus(); textArea.select(); document.execCommand('copy');
            document.body.removeChild(textArea);
            setStatus("Resolved links copied (fallback)!", false);
        } catch (fallbackErr) {
             setStatus(`Failed to copy resolved links (fallback): ${fallbackErr.message}`, true);
        }
    }
  } else {
    setStatus("No resolved links to copy.", false);
  }
});

// Change label to clarify these are lnkd.in links, not resolved links
document.querySelector('label[for="originalUrls"]').textContent = 'lnkd.in Links (manual resolve):';