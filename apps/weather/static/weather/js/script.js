/**
 * Weather App — Frontend interactions
 * - Day / Night theme
 * - City autocomplete dropdowns (search + compare)
 * - Correct live local clock (UTC + city offset only)
 * - Compare form loading state
 */

(function () {
    'use strict';

    var config = window.WEATHER_APP || {};
    var citiesUrl = config.citiesUrl || '/api/cities/';
    var clockTimers = [];

    function $(id) {
        return document.getElementById(id);
    }

    /* ---------- Theme ---------- */
    function setTheme(theme) {
        var next = theme === 'night' ? 'night' : 'day';
        document.documentElement.setAttribute('data-theme', next);
        document.body.classList.remove('theme-day', 'theme-night');
        document.body.classList.add(next === 'night' ? 'theme-night' : 'theme-day');

        var dayBtn = $('theme-day');
        var nightBtn = $('theme-night');
        if (dayBtn) dayBtn.classList.toggle('is-active', next === 'day');
        if (nightBtn) nightBtn.classList.toggle('is-active', next === 'night');

        try {
            localStorage.setItem('weather_theme', next);
        } catch (e) { /* ignore */ }
    }

    function initTheme() {
        var saved = null;
        try {
            saved = localStorage.getItem('weather_theme');
        } catch (e) {
            saved = null;
        }
        if (!saved) {
            saved = document.body.classList.contains('theme-night') ? 'night' : 'day';
        }
        setTheme(saved);

        var dayBtn = $('theme-day');
        var nightBtn = $('theme-night');
        if (dayBtn) dayBtn.addEventListener('click', function () { setTheme('day'); });
        if (nightBtn) nightBtn.addEventListener('click', function () { setTheme('night'); });
    }

    /* ---------- City dropdown (reusable) ---------- */
    function fetchCities(query) {
        var url = citiesUrl + '?q=' + encodeURIComponent(query || '');
        return fetch(url, { headers: { Accept: 'application/json' } })
            .then(function (res) { return res.json(); })
            .then(function (data) { return data.cities || []; })
            .catch(function () { return []; });
    }

    /**
     * Attach autocomplete behaviour to one search-combo block.
     */
    function setupCombo(combo) {
        if (!combo) return;

        var inputId = combo.getAttribute('data-input-id');
        var dropdownId = combo.getAttribute('data-dropdown-id');
        var input = inputId ? $(inputId) : combo.querySelector('.search-input');
        var dropdown = dropdownId ? $(dropdownId) : combo.querySelector('.city-dropdown');
        var toggle = combo.querySelector('.dropdown-toggle');
        if (!input || !dropdown) return;

        var debounceTimer = null;
        var activeIndex = -1;
        var currentOptions = [];

        function setOpen(open) {
            dropdown.hidden = !open;
            if (toggle) {
                toggle.classList.toggle('is-open', open);
                toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
            }
            if (!open) activeIndex = -1;
        }

        function renderCities(cities) {
            dropdown.innerHTML = '';
            currentOptions = cities || [];

            if (!currentOptions.length) {
                var empty = document.createElement('li');
                empty.className = 'dropdown-empty';
                empty.textContent = 'No cities found';
                dropdown.appendChild(empty);
                setOpen(true);
                return;
            }

            var hint = document.createElement('li');
            hint.className = 'dropdown-hint';
            hint.textContent = 'Select a city';
            dropdown.appendChild(hint);

            currentOptions.forEach(function (city, index) {
                var li = document.createElement('li');
                li.setAttribute('role', 'option');

                var btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'city-option';
                btn.dataset.index = String(index);

                btn.appendChild(document.createTextNode(city.label || city.name));
                if (city.country) {
                    var small = document.createElement('small');
                    small.textContent = city.country + (city.state ? ' · ' + city.state : '');
                    btn.appendChild(small);
                }

                btn.addEventListener('click', function () {
                    input.value = city.name;
                    setOpen(false);
                    input.focus();
                });

                li.appendChild(btn);
                dropdown.appendChild(li);
            });

            setOpen(true);
        }

        function scheduleFetch() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function () {
                fetchCities(input.value.trim()).then(renderCities);
            }, 220);
        }

        function highlight(index) {
            var options = dropdown.querySelectorAll('.city-option');
            options.forEach(function (el, i) {
                el.classList.toggle('is-active', i === index);
            });
            activeIndex = index;
            if (options[index]) options[index].scrollIntoView({ block: 'nearest' });
        }

        input.addEventListener('focus', scheduleFetch);
        input.addEventListener('input', scheduleFetch);

        input.addEventListener('keydown', function (event) {
            var open = !dropdown.hidden;
            if (event.key === 'ArrowDown') {
                event.preventDefault();
                if (!open) { scheduleFetch(); return; }
                highlight(Math.min(activeIndex + 1, currentOptions.length - 1));
            } else if (event.key === 'ArrowUp') {
                event.preventDefault();
                if (!open) return;
                highlight(Math.max(activeIndex - 1, 0));
            } else if (event.key === 'Enter' && open && activeIndex >= 0 && currentOptions[activeIndex]) {
                event.preventDefault();
                input.value = currentOptions[activeIndex].name;
                setOpen(false);
            } else if (event.key === 'Escape') {
                setOpen(false);
            }
        });

        if (toggle) {
            toggle.addEventListener('click', function () {
                if (!dropdown.hidden) {
                    setOpen(false);
                } else {
                    fetchCities(input.value.trim()).then(renderCities);
                }
            });
        }

        document.addEventListener('click', function (event) {
            if (!combo.contains(event.target)) setOpen(false);
        });
    }

    function initCityDropdowns() {
        document.querySelectorAll('.search-combo').forEach(setupCombo);
    }

    /* ---------- Correct local clock ---------- */
    /**
     * Convert "now" to a city's local wall clock.
     * OpenWeather timezone = seconds east of UTC.
     * Formula: Date.now() + offsetSeconds*1000, then read with UTC getters.
     * Do NOT also add browser getTimezoneOffset() — that double-shifts the time.
     */
    function formatCityDateTime(offsetSeconds) {
        var shifted = new Date(Date.now() + offsetSeconds * 1000);
        var days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        var months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];

        var dateStr =
            days[shifted.getUTCDay()] + ', ' +
            String(shifted.getUTCDate()).padStart(2, '0') + ' ' +
            months[shifted.getUTCMonth()] + ' ' +
            shifted.getUTCFullYear();

        var timeStr =
            String(shifted.getUTCHours()).padStart(2, '0') + ':' +
            String(shifted.getUTCMinutes()).padStart(2, '0') + ':' +
            String(shifted.getUTCSeconds()).padStart(2, '0');

        return { dateStr: dateStr, timeStr: timeStr };
    }

    function startClock(rootEl, dateEl, timeEl, offset) {
        function tick() {
            var parts = formatCityDateTime(offset);
            if (dateEl) dateEl.textContent = parts.dateStr;
            if (timeEl) timeEl.textContent = parts.timeStr;
        }
        tick();
        var id = setInterval(tick, 1000);
        clockTimers.push(id);
    }

    function initClocks() {
        clockTimers.forEach(clearInterval);
        clockTimers = [];

        // Main single-city clock
        var clock = $('local-clock');
        if (clock) {
            var offset = parseInt(clock.getAttribute('data-offset') || '0', 10);
            if (isNaN(offset)) offset = 0;
            startClock(clock, $('clock-date'), $('clock-time'), offset);
        }

        // Compare mini clocks
        document.querySelectorAll('.compare-clock').forEach(function (el) {
            var off = parseInt(el.getAttribute('data-offset') || '0', 10);
            if (isNaN(off)) off = 0;
            var dateEl = el.querySelector('.mini-date');
            var timeEl = el.querySelector('.mini-time');
            startClock(el, dateEl, timeEl, off);
        });
    }

    /* ---------- Forms ---------- */
    function bindLoadingForm(form, btn, emptyCheck) {
        if (!form || !btn) return;
        form.addEventListener('submit', function (event) {
            if (emptyCheck && !emptyCheck()) {
                event.preventDefault();
                form.classList.remove('shake-form');
                void form.offsetWidth;
                form.classList.add('shake-form');
                return;
            }
            btn.classList.add('is-loading');
            var btnText = btn.querySelector('.btn-text');
            if (btnText) btnText.textContent = 'Loading…';
            btn.disabled = true;
        });
    }

    function initForms() {
        var searchForm = $('search-form');
        var searchBtn = $('search-btn');
        var cityInput = $('city-input');
        bindLoadingForm(searchForm, searchBtn, function () {
            var ok = cityInput && cityInput.value.trim();
            if (!ok && cityInput) cityInput.focus();
            return !!ok;
        });

        var compareForm = $('compare-form');
        var compareBtn = $('compare-btn');
        var cityA = $('city-a-input');
        var cityB = $('city-b-input');
        bindLoadingForm(compareForm, compareBtn, function () {
            var a = cityA && cityA.value.trim();
            var b = cityB && cityB.value.trim();
            if (!a && cityA) cityA.focus();
            else if (!b && cityB) cityB.focus();
            return !!(a && b);
        });
    }

    function init() {
        initTheme();
        initCityDropdowns();
        initClocks();
        initForms();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
