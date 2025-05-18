// offscreen.js

// Function to find the most prominent external link on LinkedIn's interstitial page
function findInterstitialTargetLink(doc, originalRequestUrl) {
    if (!doc || !doc.body) {
        console.warn("Offscreen: Document or body is not available for parsing.");
        return null;
    }

    // Primary target based on the provided HTML of the interstitial page
    // <a class="artdeco-button artdeco-button--tertiary" data-tracking-control-name="external_url_click" href="TARGET_URL">TARGET_URL_TEXT</a>
    let targetLinkEl = doc.querySelector('a.artdeco-button--tertiary[data-tracking-control-name="external_url_click"]');

    if (targetLinkEl && targetLinkEl.href) {
        const potentialHref = targetLinkEl.href;
        // Ensure it's not a javascript:void(0) or a LinkedIn URL itself
        if (!potentialHref.startsWith('javascript:') &&
            !potentialHref.includes('linkedin.com') &&
            !potentialHref.includes('lnkd.in') &&
            potentialHref !== originalRequestUrl) {
            console.log("Offscreen: Found interstitial link by specific selector:", potentialHref);
            return potentialHref;
        }
    }

    // Fallback: Look for any anchor tag whose href is not a linkedin.com or lnkd.in domain
    // and whose text content also looks like the URL
    const anchors = doc.querySelectorAll('a[href]');
    for (const anchor of anchors) {
        const href = anchor.getAttribute('href'); // Get raw href
        const textContent = anchor.textContent.trim();

        if (href && textContent && (href === textContent || textContent.startsWith(href)) &&
            !href.startsWith('javascript:') &&
            !href.includes('linkedin.com') &&
            !href.includes('lnkd.in') &&
            href !== originalRequestUrl) {
            console.log("Offscreen: Found link where href matches textContent (fallback):", href);
            return href;
        }
    }
    
    // Fallback: Check if the iframe's current location (after potential JS redirect) is the target
    try {
        const iframeLocation = iframe.contentWindow.location.href;
        if (iframeLocation &&
            !iframeLocation.startsWith('javascript:') &&
            !iframeLocation.includes('lnkd.in') &&
            !iframeLocation.includes('linkedin.com/authwall') &&
            !iframeLocation.includes('linkedin.com/safety/go') &&
            iframeLocation !== originalRequestUrl) {
            console.log("Offscreen: Resolved by iframe's final location:", iframeLocation);
            return iframeLocation;
        }
    } catch (e) {
        console.warn("Offscreen: Could not directly access iframe's final location, or it was still a LinkedIn page.");
    }


    console.log("Offscreen: Could not find a clear external link in the iframe DOM for:", originalRequestUrl);
    return null; // No clear external link found
}


chrome.runtime.onMessage.addListener(async (msg, sender, sendResponse) => {
    if (msg.offscreen && msg.action === 'unshortenViaOffscreenDOM') {
        let iframe; // Declare iframe here to be accessible in finally
        try {
            iframe = document.createElement('iframe');
            iframe.style.display = 'none';

            const promise = new Promise(async (resolve) => {
                let resolvedUrl = msg.targetUrl; // This is likely the lnkd.in or linkedin.com/safety/go URL
                const originalShortUrl = msg.originalShortUrl; // The very first lnkd.in URL

                const timeoutId = setTimeout(() => {
                    console.warn("Offscreen: Timeout for", originalShortUrl);
                    if (iframe && document.body.contains(iframe)) {
                        document.body.removeChild(iframe);
                    }
                    resolve(originalShortUrl); // Fallback to original on timeout
                }, 12000);

                iframe.onload = async () => {
                    clearTimeout(timeoutId);
                    try {
                        // Give the interstitial page a moment for JS to potentially modify the DOM or for further redirects
                        await new Promise(r => setTimeout(r, 1500)); // Increased slightly

                        const extractedLink = findInterstitialTargetLink(iframe.contentDocument, originalShortUrl);
                        if (extractedLink) {
                            resolvedUrl = extractedLink;
                        } else {
                            // If DOM parsing failed, check the iframe's final location as a last resort
                            const currentIframeLocation = iframe.contentWindow.location.href;
                            if (currentIframeLocation && currentIframeLocation !== originalShortUrl && currentIframeLocation !== msg.targetUrl &&
                                !currentIframeLocation.includes('linkedin.com/authwall') &&
                                !currentIframeLocation.includes('linkedin.com/safety/go') &&
                                !currentIframeLocation.includes('lnkd.in')) {
                                console.log("Offscreen: DOM parse failed, using iframe's final different location:", currentIframeLocation);
                                resolvedUrl = currentIframeLocation;
                            } else {
                                console.log("Offscreen: DOM parse and iframe location did not yield a better URL for", originalShortUrl, ". Using initial target:", msg.targetUrl);
                                resolvedUrl = msg.targetUrl; // Or potentially originalShortUrl if msg.targetUrl is also an interstitial
                            }
                        }
                    } catch (e) {
                        console.warn("Offscreen: Error processing iframe for", originalShortUrl, ":", e.message);
                        resolvedUrl = originalShortUrl;
                    } finally {
                        if (iframe && document.body.contains(iframe)) {
                           document.body.removeChild(iframe);
                        }
                        resolve(resolvedUrl);
                    }
                };

                iframe.onerror = (err) => {
                    clearTimeout(timeoutId);
                    console.error("Offscreen: Iframe load error for unshortening:", originalShortUrl, err);
                    if (iframe && document.body.contains(iframe)) {
                        document.body.removeChild(iframe);
                    }
                    resolve(originalShortUrl);
                };

                console.log("Offscreen: Loading URL in iframe:", msg.targetUrl);
                iframe.src = msg.targetUrl;
                document.body.appendChild(iframe);
            });

            sendResponse(await promise);

        } catch (e) {
            console.error('Error in offscreen document (outer try-catch):', e);
            if (iframe && document.body.contains(iframe)) {
                document.body.removeChild(iframe);
            }
            sendResponse(msg.originalShortUrl || msg.targetUrl);
        }
        return true;
    }
});