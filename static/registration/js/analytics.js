/* Google Analytics 4 bootstrap.
 *
 * The measurement ID arrives on this script tag's own data attribute rather
 * than being interpolated into an inline <script>, so the page needs no
 * script-src 'unsafe-inline'. The tag is only rendered when GA_MEASUREMENT_ID
 * is configured, replacing a Universal Analytics property that stopped
 * collecting data when UA shut down in July 2023.
 */
(function () {
    "use strict";

    var script = document.currentScript;
    if (!script) {
        return;
    }

    var measurementId = script.getAttribute("data-measurement-id");
    if (!measurementId) {
        return;
    }

    window.dataLayer = window.dataLayer || [];

    function gtag() {
        window.dataLayer.push(arguments);
    }

    window.gtag = gtag;
    gtag("js", new Date());
    gtag("config", measurementId);
})();
