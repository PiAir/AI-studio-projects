// background.js
const OFFSCREEN_DOCUMENT_PATH = 'offscreen.html';

async function hasOffscreenDocument(path) {
  const offscreenUrl = chrome.runtime.getURL(path);
  const contexts = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT'],
    documentUrls: [offscreenUrl]
  });
  return contexts.length > 0;
}

async function ensureOffscreenDocument() {
  if (await hasOffscreenDocument(OFFSCREEN_DOCUMENT_PATH)) {
    return;
  }
  await chrome.offscreen.createDocument({
    url: OFFSCREEN_DOCUMENT_PATH,
    reasons: [chrome.offscreen.Reason.DOM_PARSER],
    justification: 'To parse lnkd.in interstitial pages for the final URL.',
  });
}

async function resolveShortUrl(shortUrl) {
  let finalUrl = shortUrl;
  let attemptOffscreen = false;

  try {
    console.log("Attempting to resolve:", shortUrl);
    const response = await fetch(shortUrl, { method: 'HEAD', redirect: 'follow', cache: 'no-store' });
    if (response && response.url && response.url !== shortUrl && !response.url.includes("linkedin.com/authwall")) {
      finalUrl = response.url;
      console.log("Fetch HEAD resolved to:", finalUrl);
    } else {
      const getResponse = await fetch(shortUrl, { method: 'GET', redirect: 'follow', cache: 'no-store' });
      if (getResponse && getResponse.url && getResponse.url !== shortUrl && !getResponse.url.includes("linkedin.com/authwall")) {
        finalUrl = getResponse.url;
        console.log("Fetch GET resolved to:", finalUrl);
      }
    }

    if (shortUrl.includes('lnkd.in/') || // Always try offscreen for lnkd.in if fetch wasn't definitive
        finalUrl.includes('linkedin.com/safety/go') ||
        finalUrl.includes('linkedin.com/authwall') ||
        finalUrl === shortUrl ||
        (finalUrl.includes('lnkd.in/') && finalUrl !== shortUrl) ) {
      attemptOffscreen = true;
    }

    if (attemptOffscreen) {
      console.log(`URL ${shortUrl} (resolved by fetch to ${finalUrl}) will be processed by offscreen document.`);
      await ensureOffscreenDocument();
      const originalUrlFromOffscreen = await chrome.runtime.sendMessage({
          action: 'unshortenViaOffscreenDOM',
          targetUrl: finalUrl, // Use the URL fetch resolved to, or original if fetch didn't change it
          originalShortUrl: shortUrl
      });

      if (originalUrlFromOffscreen &&
          originalUrlFromOffscreen !== shortUrl &&
          originalUrlFromOffscreen !== finalUrl &&
          !originalUrlFromOffscreen.includes('linkedin.com/authwall') &&
          !originalUrlFromOffscreen.includes('linkedin.com/safety/go') &&
          !originalUrlFromOffscreen.includes('lnkd.in') // Ensure it's not another lnkd.in
          ) {
        console.log("Offscreen document resolved to:", originalUrlFromOffscreen);
        finalUrl = originalUrlFromOffscreen;
      } else {
        console.log("Offscreen did not provide a better URL. Using previous result:", finalUrl);
      }
    }
    console.log("Final resolved URL for", shortUrl, "is", finalUrl);
    return finalUrl;

  } catch (error) {
    console.warn(`Error unshortening ${shortUrl} via fetch: ${error.message}. Attempting offscreen as fallback.`);
    try {
        await ensureOffscreenDocument();
        const originalUrlFromOffscreen = await chrome.runtime.sendMessage({
            action: 'unshortenViaOffscreenDOM',
            targetUrl: shortUrl,
            originalShortUrl: shortUrl
        });
        if (originalUrlFromOffscreen && originalUrlFromOffscreen !== shortUrl &&
            !originalUrlFromOffscreen.includes('linkedin.com/authwall') &&
            !originalUrlFromOffscreen.includes('linkedin.com/safety/go') &&
            !originalUrlFromOffscreen.includes('lnkd.in')) {
            console.log("Offscreen fallback resolved to:", originalUrlFromOffscreen);
            return originalUrlFromOffscreen;
        }
     } catch (offscreenError) {
        console.error(`Offscreen unshortening also failed for ${shortUrl}: ${offscreenError.message}`);
     }
    console.log("All methods failed for", shortUrl, ". Returning original.");
    return shortUrl;
  }
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "unshortenLinks" && request.linksMap) {
    const linkPromises = Object.entries(request.linksMap).map(async ([shortUrl, placeholder]) => {
      const originalUrl = await resolveShortUrl(shortUrl);
      return { placeholder, shortUrl, originalUrl };
    });

    Promise.all(linkPromises)
      .then(results => {
        sendResponse({ unshortenedLinks: results });
      })
      .catch(error => {
        console.error("Error during bulk unshortening:", error);
        sendResponse({ error: error.message, unshortenedLinks: [] });
      });
    return true;
  }

  if (request.action === "downloadImage" && request.imageUrl) {
    chrome.downloads.download({
      url: request.imageUrl,
    }, (downloadId) => {
      if (chrome.runtime.lastError) {
        console.error("Download failed:", chrome.runtime.lastError.message);
        sendResponse({ success: false, error: chrome.runtime.lastError.message });
      } else {
        if (downloadId !== undefined) {
            sendResponse({ success: true, downloadId: downloadId });
        } else {
            sendResponse({ success: false, error: "Download could not be initiated (no ID)." });
        }
      }
    });
    return true;
  }
});