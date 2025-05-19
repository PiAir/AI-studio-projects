// background.js
const OFFSCREEN_DOCUMENT_PATH = 'offscreen.html';
let offscreenDocumentSetupPromise = null;
// Store for the current URL being processed by offscreen document for webNavigation
// Now holds { originalShortUrl: string, targetUrl: string, resolvePromise: function, rejectPromise: function, timeoutId?: number }
let currentOffscreenProcessingDetails = null;
let offscreenCloseTimer = null; // Timer to close the offscreen document after inactivity

const OFFSCREEN_CLOSE_DELAY = 30000; // 30 seconds of inactivity

function clearOffscreenCloseTimer() {
    if (offscreenCloseTimer) {
        clearTimeout(offscreenCloseTimer);
        offscreenCloseTimer = null;
    }
}

function scheduleOffscreenClose() {
    clearOffscreenCloseTimer();
    offscreenCloseTimer = setTimeout(async () => {
        if (currentOffscreenProcessingDetails) {
            console.log("Offscreen close timer: Aborting close, processing active.");
            scheduleOffscreenClose(); // Reschedule if still active
            return;
        }
        console.log("Offscreen close timer: Closing offscreen document due to inactivity.");
        if (chrome.offscreen && await chrome.offscreen.hasDocument()) { // Check if it exists before trying to close
            await chrome.offscreen.closeDocument();
        }
        console.log("Offscreen document closed.");
    }, OFFSCREEN_CLOSE_DELAY);
}


async function hasOffscreenDocument(path) {
  const offscreenUrl = chrome.runtime.getURL(path);
  const clients = await self.clients.matchAll();
  for (const client of clients) {
    if (client.url === offscreenUrl) {
      return true;
    }
  }
  return false;
}

async function ensureOffscreenDocument() {
    try {
        if (chrome.offscreen && await chrome.offscreen.hasDocument()) {
            return;
        }
    } catch (e) {
        // fallback, but we only use chrome.offscreen.hasDocument
    }
    if (!offscreenDocumentSetupPromise) {
        offscreenDocumentSetupPromise = chrome.offscreen.createDocument({
            url: OFFSCREEN_DOCUMENT_PATH,
            reasons: [chrome.offscreen.Reason.DOM_PARSER],
            justification: 'To unshorten lnkd.in URLs by parsing interstitial pages in a DOM environment.'
        }).catch(async (err) => {
            // If doc exists but is broken, close and recreate
            if (err.message && err.message.toLowerCase().includes('only a single offscreen document may be created')) {
                await chrome.offscreen.closeDocument();
                await chrome.offscreen.createDocument({
                    url: OFFSCREEN_DOCUMENT_PATH,
                    reasons: [chrome.offscreen.Reason.DOM_PARSER],
                    justification: 'To unshorten lnkd.in URLs by parsing interstitial pages in a DOM environment.'
                });
            } else {
                throw err;
            }
        }).finally(() => {
            offscreenDocumentSetupPromise = null;
        });
    }
    return offscreenDocumentSetupPromise;
}

function clearOffscreenProcessingState(originalShortUrl) {
    if (currentOffscreenProcessingDetails && currentOffscreenProcessingDetails.originalShortUrl === originalShortUrl) {
        if (currentOffscreenProcessingDetails.timeoutId) {
            clearTimeout(currentOffscreenProcessingDetails.timeoutId);
        }
        console.log(`Background: Clearing currentOffscreenProcessingDetails for ${originalShortUrl}.`);
        currentOffscreenProcessingDetails = null;
        scheduleOffscreenClose(); // Processing done, schedule close
    }
}

let unshortenTabMap = {};

async function resolveShortUrl(shortUrl) {
    let finalUrl = shortUrl;
    let attemptPopup = false;
    try {
        // Try fetch first
        const response = await fetch(shortUrl, { method: 'HEAD', redirect: 'follow', cache: 'no-store' });
        if (response && response.url && response.url !== shortUrl && !response.url.includes("linkedin.com/authwall")) {
            finalUrl = response.url;
        } else {
            const getResponse = await fetch(shortUrl, { method: 'GET', redirect: 'follow', cache: 'no-store' });
            if (getResponse && getResponse.url && getResponse.url !== shortUrl && !getResponse.url.includes("linkedin.com/authwall")) {
                finalUrl = getResponse.url;
            }
        }
        if (shortUrl.includes('lnkd.in/') ||
            finalUrl.includes('linkedin.com/safety/go') ||
            finalUrl.includes('linkedin.com/authwall') ||
            finalUrl === shortUrl ||
            (finalUrl.includes('lnkd.in/') && finalUrl !== shortUrl)) {
            attemptPopup = true;
        }
        if (attemptPopup) {
            return await unshortenViaPopupWindow(finalUrl);
        }
        return finalUrl;
    } catch (error) {
        // fallback: try popup if fetch fails
        try {
            return await unshortenViaPopupWindow(shortUrl);
        } catch (e) {
            return shortUrl;
        }
    }
}

async function unshortenViaPopupWindow(url) {
    return new Promise((resolve, reject) => {
        chrome.windows.create({
            url,
            type: 'popup',
            focused: false,
            width: 400,
            height: 400,
            top: 100,
            left: 100
        }, (win) => {
            if (!win || !win.tabs || !win.tabs[0] || !win.tabs[0].id) {
                reject(new Error('Could not create popup window for unshortening'));
                return;
            }
            const tabId = win.tabs[0].id;
            let lastUrl = url;
            let resolved = false;
            function cleanup(finalUrl) {
                resolved = true;
                chrome.webNavigation.onCommitted.removeListener(navListener);
                chrome.webNavigation.onCompleted.removeListener(navCompletedListener);
                chrome.windows.remove(win.id);
                resolve(finalUrl);
            }
            let timeout = setTimeout(() => {
                if (!resolved) cleanup(lastUrl);
            }, 15000);
            function navListener(details) {
                if (details.tabId === tabId && details.frameId === 0) {
                    lastUrl = details.url;
                    if (!lastUrl.includes('linkedin.com/safety/go') &&
                        !lastUrl.includes('linkedin.com/authwall') &&
                        !lastUrl.includes('lnkd.in')) {
                        clearTimeout(timeout);
                        cleanup(lastUrl);
                    }
                }
            }
            function navCompletedListener(details) {
                if (details.tabId === tabId && details.frameId === 0) {
                    lastUrl = details.url;
                }
            }
            chrome.webNavigation.onCommitted.addListener(navListener);
            chrome.webNavigation.onCompleted.addListener(navCompletedListener);
        });
    });
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  clearOffscreenCloseTimer(); // Activity
  if (request.action === "unshortenLinks" && request.linksMap) {
    // Manual resolve: just return the short links, no unshortening
    const results = Object.entries(request.linksMap).map(([shortUrl, placeholder]) => ({
      placeholder,
      shortUrl,
      resolvedUrl: shortUrl // No automatic resolving
    }));
    sendResponse({ unshortenedLinks: results });
    return false;
  } else if (request.action === "downloadImage" && request.imageUrl) {
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
    return true; // Indicates async response
  } else if (request.action === 'offscreenScriptReady') {
    console.log("Background: 'offscreenScriptReady' message received.");
    sendResponse({ status: "Background acknowledged offscreenScriptReady" });
    scheduleOffscreenClose(); // Activity
    return false; // Synchronous response or no response needed beyond ack.
  } else if (request.action === "openLinkInTab" && request.url) {
    chrome.tabs.create({ url: request.url });
    sendResponse({ success: true });
    return false;
  } else {
    console.log("Background: Received message not handled by specific if/else blocks or already responded to:", request);
  }
  // Default: if an async action returned true, channel is open. Otherwise, it's closed.
  // No explicit return false here to avoid closing channel prematurely for async operations.
});

// Initialize: ensure offscreen document exists on startup if needed, or close if not used.
(async () => {
    try {
        // It's generally better to create it on-demand.
        // However, if you want to ensure it's ready for the first request quickly:
        // await ensureOffscreenDocument();
        // console.log("Initial check/creation of offscreen document on service worker startup complete.");
        // For now, let's rely on on-demand creation and schedule a close if it somehow exists without a timer.
        if (chrome.offscreen && await chrome.offscreen.hasDocument()) {
            console.log("Service worker started. Offscreen document exists. Ensuring close timer is active.");
            scheduleOffscreenClose();
        } else {
            console.log("Service worker started. No offscreen document detected initially.");
        }
    } catch (e) {
        console.error("Error during initial offscreen document check on startup:", e);
    }
})();

// Keep alive for webNavigation listeners, though event-driven should be fine.
// This is more of a failsafe for very short-lived service worker cycles.
// A proper keep-alive would involve connecting to a port from an extension page.
// For now, relying on event listeners and offscreen document activity.
let lifeline;

keepAlive();

async function keepAlive() {
  if (lifeline) return;
  for (const client of await clients.matchAll()) {
    if (client.type === "window") {
      lifeline = client;
      return;
    }
  }
  chrome.windows.create({
    focused: false,
    type: "popup",
    height: 1,
    width: 1,
    top: -1000,
    left: -1000,
    url: "offscreen.html", // Re-using offscreen, or a dedicated keepalive.html
  });
}
// The keepAlive above by creating a window is generally not recommended for MV3.
// The offscreen document itself, when active, should keep the SW alive.
// The webNavigation listeners also act as events that can wake/keep alive the SW.
// Removing the aggressive keepAlive() window creation.
// The offscreen document and its activity (messaging, navigation) are the primary mechanisms.
console.log("Background service worker started/restarted.");