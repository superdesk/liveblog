/* eslint-disable curly */
import * as Cookies from 'js-cookie';

const COOKIE_NAME = '__lb_consent_cookie__';
const COOKIE_LIFE_DAYS = 365;
const CONSENT_SUBJECTS_SELECTOR = 'template.lb_consent--awaiting';
const CONSENT_PLACEHOLDER_TMPL = 'template#lb_consent--placeholder-tmpl';
const PLACEHOLDER_SELECTOR = 'lb_consent--placeholder';


const wireCookiesEnabler = () => {
    if (isConsentGiven())
        return;

    const acceptBtns = document.getElementsByClassName('lb_consent--accept');

    if (acceptBtns.length > 0) {
        Array.from(acceptBtns).forEach((btn) => {
            btn.addEventListener('click', (ev) => {
                ev.preventDefault();

                Cookies.set(COOKIE_NAME, 'Y', {
                    expires: COOKIE_LIFE_DAYS,
                    sameSite: 'lax'
                });
                checkAndHandlePlaceholders();
            });
        });
    }
};

const isConsentGiven = () => Cookies.get(COOKIE_NAME) === 'Y';

const getNodesAwaitingConsent = () => document.querySelectorAll(CONSENT_SUBJECTS_SELECTOR);

const domainRequiresConsent = (providerUrl) => {
    if (!providerUrl)
        return false;

    let domains = LB.settings.gdprConsentDomains;

    if (domains.length > 0) {
        // get domains and remove possible blank spaces
        domains = domains.split(',');
        domains = domains.map((x) => x.trim().toLowerCase());

        let embedDomain = new URL(providerUrl).hostname;

        embedDomain = embedDomain.replace('www.', '');

        return domains.indexOf(embedDomain) !== -1;
    }

    return false;
};

const exposeContent = (embedNode) => {
    const prev = embedNode.previousElementSibling;

    if (prev && prev.classList.contains(PLACEHOLDER_SELECTOR))
        prev.remove();

    embedNode.replaceWith(embedNode.content);
};

const checkAndHandlePlaceholders = () => {
    const embedNodes = getNodesAwaitingConsent();

    if (LB.settings.enableGdprConsent && !isConsentGiven()) {
        const placeholder = document.querySelector(CONSENT_PLACEHOLDER_TMPL);

        embedNodes.forEach((embed) => {
            const providerUrl = embed.getAttribute('data-provider-url');

            if (!domainRequiresConsent(providerUrl)) {
                exposeContent(embed);
                return;
            }

            const clone = placeholder.content.cloneNode(true);
            const parent = embed.parentNode;
            const prev = embed.previousElementSibling;

            // if placeholder is already there or if skip is provided
            if (prev && prev.classList.contains(PLACEHOLDER_SELECTOR) || embed.hasAttribute('data-no-placeholder'))
                return;

            parent.insertBefore(clone, embed);
        });

        wireCookiesEnabler();
    } else {
        embedNodes.forEach(exposeContent);

        setTimeout(() => {
            instgrm.Embeds.process();
            twttr.widgets.load();
        }, 500);
    }
};

module.exports = {
    init: () => {
        wireCookiesEnabler();
        checkAndHandlePlaceholders();
    },

    wireCookiesEnabler: wireCookiesEnabler
};