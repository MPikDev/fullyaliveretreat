/* Site-wide behaviour.
 *
 * All application JavaScript now lives in files like this one rather than
 * inline in templates, so the pages can be served under a Content-Security-
 * Policy without `unsafe-inline`, and the browser can cache it.
 *
 * Every element lookup is guarded. The previous inline scripts called
 * `document.getElementById(...).onclick = ...` unconditionally on elements that
 * were inside a Django `{% if %}` or commented out entirely, which threw a
 * TypeError and killed the rest of the script block.
 */
(function () {
    "use strict";

    /* ---------------------------------------------------------------------
     * Mobile navigation
     * ------------------------------------------------------------------- */
    function initNav() {
        var toggle = document.querySelector(".nav-toggle");
        var nav = document.getElementById("site-nav");
        if (!toggle || !nav) {
            return;
        }

        function setOpen(open) {
            toggle.setAttribute("aria-expanded", String(open));
            nav.setAttribute("data-open", String(open));
        }

        toggle.addEventListener("click", function () {
            setOpen(toggle.getAttribute("aria-expanded") !== "true");
        });

        // Close when focus or a click leaves the menu, and on Escape.
        document.addEventListener("click", function (event) {
            if (!nav.contains(event.target) && !toggle.contains(event.target)) {
                setOpen(false);
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                setOpen(false);
            }
        });
    }

    /* ---------------------------------------------------------------------
     * Countdown
     *
     * The target is read from a data attribute holding an ISO-8601 timestamp
     * with an explicit UTC offset, rendered from CampSeason.starts_at. The old
     * version parsed the string "August 21 2026 18:00", which has no timezone,
     * so every visitor saw a countdown to 6pm in their own timezone.
     * ------------------------------------------------------------------- */
    function initCountdown() {
        var root = document.getElementById("countdown");
        if (!root) {
            return;
        }

        var target = Date.parse(root.getAttribute("data-target"));
        if (isNaN(target)) {
            return;
        }

        var outputs = {
            days: root.querySelector('[data-unit="days"]'),
            hours: root.querySelector('[data-unit="hours"]'),
            minutes: root.querySelector('[data-unit="minutes"]'),
            seconds: root.querySelector('[data-unit="seconds"]')
        };

        function pad(value, size) {
            var text = String(value);
            while (text.length < size) {
                text = "0" + text;
            }
            return text;
        }

        function set(node, value, size) {
            if (node && node.textContent !== value) {
                node.textContent = pad(value, size);
            }
        }

        function tick() {
            var remaining = target - Date.now();

            if (remaining <= 0) {
                set(outputs.days, 0, 2);
                set(outputs.hours, 0, 2);
                set(outputs.minutes, 0, 2);
                set(outputs.seconds, 0, 2);
                clearInterval(timer);
                return;
            }

            var totalSeconds = Math.floor(remaining / 1000);
            set(outputs.days, Math.floor(totalSeconds / 86400), 2);
            set(outputs.hours, Math.floor(totalSeconds / 3600) % 24, 2);
            set(outputs.minutes, Math.floor(totalSeconds / 60) % 60, 2);
            set(outputs.seconds, totalSeconds % 60, 2);
        }

        tick();
        var timer = setInterval(tick, 1000);
    }

    function init() {
        initNav();
        initCountdown();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
