// content_script.js

function scrapeLinkedInPost() {
  let bodyText = '';
  const imageUrls = new Set();
  const linksToUnshorten = {}; // { "shortUrl": "placeholder" }

  // --- Post Body Selector based on provided HTML ---
  let postBodyElement = document.querySelector('.feed-shared-update-v2__description .update-components-text.update-components-update-v2__commentary > .break-words > span[dir="ltr"]');

  if (!postBodyElement) {
    postBodyElement = document.querySelector('.feed-shared-update-v2__description .update-components-text');
  }
  if (!postBodyElement) {
    postBodyElement = document.querySelector('.update-components-text.feed-shared-update-v2__commentary');
  }
  if (!postBodyElement) {
      const articleUpdate = document.querySelector('article div.feed-shared-update-v2__description-wrapper');
      if (articleUpdate) {
          postBodyElement = articleUpdate.querySelector('.update-components-text.feed-shared-update-v2__commentary');
      }
  }
  if (!postBodyElement) {
    postBodyElement = document.querySelector('.break-words.hyphens-auto');
  }


  if (postBodyElement) {
    const clonedPostElement = postBodyElement.cloneNode(true);
    clonedPostElement.querySelectorAll('.feed-shared-inline-show-more-text__see-more-less-toggle, .lt-line-clamp__ellipsis, [role="button"][aria-expanded], .see-more, .truncate-text-multiline__see-more-less-toggle').forEach(el => el.remove());

    clonedPostElement.querySelectorAll('a').forEach((link, index) => {
      let href = link.getAttribute('href');
      if (href) {
        try {
          href = new URL(href, document.baseURI).href;
        } catch (e) {
          if (href.startsWith('/')) {
            href = `https://www.linkedin.com${href}`;
          } else {
            return;
          }
        }

        if (href.includes('lnkd.in/')) {
          const placeholder = `__LINK_LN_${Date.now()}_${index}__`;
          linksToUnshorten[href] = placeholder;
          link.replaceWith(document.createTextNode(placeholder));
        } else {
          const linkText = link.textContent ? link.textContent.trim() : href;
          if (linkText === href || link.href === link.textContent || link.href.endsWith(linkText)) {
            link.replaceWith(document.createTextNode(linkText));
          } else {
            link.replaceWith(document.createTextNode(`${linkText} (${href})`));
          }
        }
      } else {
        const linkText = link.textContent ? link.textContent.trim() : "";
        if (linkText) {
            if (linkText.startsWith('#') || (link.classList.contains('feed-shared-hashtag') && !linkText.startsWith('#'))) {
                 const hashtagText = linkText.startsWith('#') ? linkText : `#${linkText}`;
                 link.replaceWith(document.createTextNode(hashtagText));
            } else {
                link.replaceWith(document.createTextNode(linkText));
            }
        } else {
            link.remove();
        }
      }
    });

    let rawHtml = clonedPostElement.innerHTML;
    rawHtml = rawHtml.replace(/<br\s*\/?>/gi, '\n');
    rawHtml = rawHtml.replace(/<\/p\s*>/gi, '\n');
    rawHtml = rawHtml.replace(/<\/div\s*>/gi, '\n');

    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = rawHtml;
    bodyText = tempDiv.textContent || tempDiv.innerText || "";

    bodyText = bodyText.split('\n').map(line => line.trim()).filter(line => line.length > 0).join('\n');
    bodyText = bodyText.replace(/\n\s*\n+/g, '\n\n').trim();

  } else {
    bodyText = "Main post content not found. LinkedIn's HTML structure might have changed, or this is not a standard post page.";
  }

  const postWrapper = document.querySelector('div.feed-shared-update-v2[data-urn^="urn:li:activity:"]');
  if (postWrapper) {
    const imageElements = postWrapper.querySelectorAll(
        '.update-components-image__container img.update-components-image__image, ' +
        '.feed-shared-image__image-view img, ' +
        '.feed-shared-article__images img, ' +
        '.feed-shared-carousel__image-container img, ' +
        'img[data-delayed-url]'
    );
    imageElements.forEach(img => {
      const src = img.getAttribute('data-delayed-url') || img.src;
      if (src && !src.startsWith('data:') && !src.startsWith('blob:')) {
        try {
          const absoluteSrc = new URL(src, document.baseURI).href;
          imageUrls.add(absoluteSrc);
        } catch (e) {
          console.warn("Could not parse image src as URL:", src, e);
        }
      }
    });
  }

  return {
    body: bodyText,
    imageUrls: Array.from(imageUrls),
    linksToUnshorten: linksToUnshorten
  };
}

chrome.runtime.sendMessage({
  action: "scrapedData",
  data: scrapeLinkedInPost()
});