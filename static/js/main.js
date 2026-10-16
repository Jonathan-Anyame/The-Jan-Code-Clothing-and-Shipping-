document.addEventListener('DOMContentLoaded', function () {
    var hamburger = document.getElementById('hamburger');
    var navMenu = document.getElementById('navMenu');
    var navbar = document.getElementById('navbar');

    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function () {
            navMenu.classList.toggle('active');
            hamburger.classList.toggle('active');
        });

        document.querySelectorAll('.nav-menu a').forEach(function (link) {
            link.addEventListener('click', function () {
                navMenu.classList.remove('active');
                hamburger.classList.remove('active');
            });
        });
    }

    if (navbar) {
        window.addEventListener('scroll', function () {
            navbar.classList.toggle('scrolled', window.scrollY > 20);
        });
    }

    var calc = document.querySelector('.calc');
    if (calc) {
        var input = document.getElementById('calcInput');
        var priceEl = document.getElementById('calcPrice');
        var timeEl = document.getElementById('calcTime');
        var label = document.getElementById('calcLabel');
        var mode = 'sea';
        var sea = Number(calc.getAttribute('data-sea')) || 260;
        var air = Number(calc.getAttribute('data-air')) || 19;
        var seaDays = calc.getAttribute('data-sea-days') || '45-60 days';
        var airDays = calc.getAttribute('data-air-days') || '7-14 days';

        function formatMoney(n) {
            if (!isFinite(n) || n < 0) return '$0';
            return '$' + n.toLocaleString(undefined, {
                minimumFractionDigits: n % 1 === 0 ? 0 : 2,
                maximumFractionDigits: 2
            });
        }

        function update() {
            var qty = parseFloat(input.value) || 0;
            var country = document.getElementById('calcCountry') ? document.getElementById('calcCountry').value : '';
            var includeDoorstep = document.getElementById('includeDoorstep') ? document.getElementById('includeDoorstep').checked : false;
            var doorstepCfg = calc.getAttribute('data-doorstep') ? JSON.parse(calc.getAttribute('data-doorstep')) : {};
            var doorstepCost = 0;
            if (mode === 'sea') {
                priceEl.textContent = formatMoney(qty * sea);
                timeEl.textContent = seaDays;
                if (label) label.textContent = 'Cubic meters (CBM)';
                if (includeDoorstep && country && doorstepCfg[country]) {
                    var cfg = doorstepCfg[country];
                    if (cfg.type === 'flat') doorstepCost = cfg.amount;
                    else if (cfg.type === 'per_cbm') doorstepCost = cfg.amount * qty;
                    else doorstepCost = 0;
                }
            } else {
                priceEl.textContent = formatMoney(qty * air);
                timeEl.textContent = airDays;
                if (label) label.textContent = 'Kilograms (kg)';
                if (includeDoorstep && country && doorstepCfg[country]) {
                    var cfg = doorstepCfg[country];
                    if (cfg.type === 'flat') doorstepCost = cfg.amount;
                    else if (cfg.type === 'per_kg') doorstepCost = cfg.amount * qty;
                    else doorstepCost = 0;
                }
            }
            var total = (parseFloat(priceEl.textContent.replace(/[^0-9.-]+/g, '')) || 0) + doorstepCost;
            document.getElementById('calcDoorstep').textContent = doorstepCost ? formatMoney(doorstepCost) : 'Quoted individually';
            document.getElementById('calcTotal').textContent = formatMoney(total);
        }

        calc.querySelectorAll('.calc-mode').forEach(function (btn) {
            btn.addEventListener('click', function () {
                mode = btn.getAttribute('data-mode');
                calc.querySelectorAll('.calc-mode').forEach(function (b) {
                    b.classList.toggle('active', b === btn);
                });
                update();
            });
        });

        var countryEl = document.getElementById('calcCountry');
        var doorstepEl = document.getElementById('includeDoorstep');
        if (countryEl) countryEl.addEventListener('change', update);
        if (doorstepEl) doorstepEl.addEventListener('change', update);
        input.addEventListener('input', update);
        update();
    }
});
