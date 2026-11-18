// Métricas de DespensAPP: carga /api/v1/analytics/overview y dibuja KPIs, gráfico y listas.
(function () {
    "use strict";

    const THEME_KEY = "despensapp-dash-theme";
    const PERIOD_KEY = "despensapp-dash-days";
    const REFRESH_MS = 60000;
    const $ = (id) => document.getElementById(id);
    const nf = new Intl.NumberFormat("es-CL");
    let activeChart = null;
    let lastData = null;
    let days = 30;

    try {
        const saved = parseInt(localStorage.getItem(PERIOD_KEY), 10);
        if ([7, 30, 90].includes(saved)) days = saved;
    } catch (e) { /* sin almacenamiento: usa 30 días */ }

    const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
    const set = (id, text) => { const el = $(id); if (el) el.textContent = text; };
    const num = (v) => nf.format(v ?? 0);
    const pct = (v) => `${String(v ?? 0).replace(".", ",")} %`;
    const dec = (v) => String(v ?? 0).replace(".", ",");

    function barRow(name, value, share) {
        return `<li><span class="name">${esc(name)}</span><span class="num">${esc(value)}</span>` +
               `<span class="track"><i style="width:${Math.max(2, Math.min(100, share))}%"></i></span></li>`;
    }

    function renderKpis(k) {
        set("k_avg_dau", dec(k.avg_dau));
        set("k_wau", num(k.wau));
        set("k_mau", num(k.mau));
        set("k_users", num(k.total_users));
        set("k_new", num(k.new_users));
        set("k_stick", pct(k.stickiness));
        set("k_spu", dec(k.sessions_per_user));
        set("k_avg_session", k.avg_session);
        set("k_median_session", k.median_session);
        set("k_purchases", num(k.purchases));
        set("k_buyers", num(k.buyers));
        set("k_spend", k.spend_str);
        set("k_ticket", k.avg_ticket_str);
        set("k_pro", num(k.pro_users));
        set("k_pro_rate", pct(k.pro_rate));
        set("k_pantry", dec(k.pantry_per_user));
        set("k_low", pct(k.low_stock_share));
        set("k_lists", dec(k.lists_per_user));
        set("k_items", num(k.list_items_added));
        set("k_restock", num(k.restock_uses));
    }

    function renderRetention(r) {
        const items = [
            ["Al día siguiente", r.d1, "día 1"],
            ["En la segunda semana", r.d7, "días 7 a 13"],
            ["Después de un mes", r.d30, "días 30 a 36"],
        ];
        $("retention").innerHTML = items.map(([title, v, range]) =>
            `<div class="ret"><span>${title}</span><strong>${pct(v.rate)}</strong>` +
            `<small>${num(v.returned)} de ${num(v.eligible)} (${range})</small>` +
            `<div class="meter"><i style="width:${v.rate}%"></i></div></div>`).join("");
    }

    function renderFunnel(steps) {
        $("funnel").innerHTML = steps.map((s, i) =>
            `<li><span class="name">${esc(s.step)}</span>` +
            `<span class="num">${num(s.users)}<small>${pct(s.rate)}</small></span>` +
            `<span class="track"><i style="width:${Math.max(2, s.rate)}%"></i></span>` +
            (i ? `<span class="drop">${pct(s.step_rate)} del paso anterior</span>` : "") + `</li>`).join("");
    }

    function renderScreens(list) {
        const max = Math.max(1, ...list.map((s) => s.minutes));
        $("screens").innerHTML = list.length
            ? list.map((s) => barRow(s.label, `${num(Math.round(s.minutes))} min (${pct(s.share)})`, 100 * s.minutes / max)).join("")
            : `<li class="card-sub">Sin visitas en el periodo.</li>`;
    }

    function renderPlatforms(list) {
        if (!list.length) { $("platforms").innerHTML = `<p class="card-sub">Sin sesiones en el periodo.</p>`; return; }
        const total = list.reduce((a, p) => a + p.users, 0) || 1;
        const split = list.slice(0, 2).map((p) => `<i style="width:${100 * p.users / total}%"></i>`).join("");
        const rows = list.map((p, i) =>
            `<div class="plat-row"><b><i class="sw ${i ? "sw-soft" : "sw-accent"}"></i>${esc(p.platform)}</b>` +
            `<span>${num(p.users)} personas (${pct(p.share)})</span></div>`).join("");
        $("platforms").innerHTML = `<div class="split" role="img" aria-label="Reparto por plataforma">${split}</div>${rows}`;
    }

    function renderEvents(list) {
        const max = Math.max(1, ...list.map((e) => e.count));
        $("events").innerHTML = list.length
            ? list.map((e) => barRow(e.label, num(e.count), 100 * e.count / max)).join("")
            : `<li class="card-sub">Sin eventos en el periodo.</li>`;
    }

    function renderChart(daily) {
        const labels = daily.map((d) => {
            const [y, m, dd] = d.date.split("-");
            return `${dd}-${m}`;
        });
        const accent = css("--accent"), soft = css("--accent-soft"), grid = css("--line"), text = css("--text-3");
        const cfg = {
            data: {
                labels,
                datasets: [
                    { type: "line", label: "Activos", data: daily.map((d) => d.active), borderColor: accent,
                      backgroundColor: accent, borderWidth: 2.5, pointRadius: 0, pointHoverRadius: 4, tension: 0.3, order: 1 },
                    { type: "bar", label: "Nuevos", data: daily.map((d) => d.new), backgroundColor: soft,
                      borderRadius: 4, maxBarThickness: 14, order: 2 },
                ],
            },
            options: {
                responsive: true, maintainAspectRatio: false, animation: false,
                interaction: { mode: "index", intersect: false },
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { title: (items) => daily[items[0].dataIndex].date.split("-").reverse().join("-") } } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: text, maxRotation: 0, autoSkipPadding: 14, font: { family: "Plus Jakarta Sans" } }, border: { display: false } },
                    y: { beginAtZero: true, grid: { color: grid }, ticks: { color: text, precision: 0, font: { family: "Plus Jakarta Sans" } }, border: { display: false } },
                },
            },
        };
        if (activeChart) activeChart.destroy();
        activeChart = new Chart($("activeChart"), cfg);
    }

    function renderRecent(rows) {
        $("recent").innerHTML = rows.length
            ? rows.map((r) => `<tr><td>${esc(r.created_at)}</td><td>#${esc(r.user_id ?? "–")}</td>` +
                               `<td>${esc(r.label)}</td><td>${esc(r.screen)}</td></tr>`).join("")
            : `<tr><td colspan="4" class="muted">Sin eventos todavía.</td></tr>`;
    }

    function render(data) {
        lastData = data;
        const empty = !data.available;
        $("empty_state").hidden = !empty;
        $("content").hidden = empty;
        if (empty) return;
        const fmtDate = (iso) => iso.split("-").reverse().slice(0, 2).join("-");
        set("period_label", `Del ${fmtDate(data.period_start)} al ${fmtDate(data.period_end)}, días completos.`);
        set("generated_at", `Actualizado a las ${data.generated_at.split(" ")[1]}`);
        renderKpis(data.kpis);
        renderRetention(data.retention);
        renderFunnel(data.funnel);
        renderScreens(data.screens);
        renderPlatforms(data.platforms);
        renderEvents(data.top_events);
        if (window.Chart) renderChart(data.daily);
    }

    async function load() {
        const main = $("content");
        main.classList.add("loading");
        $("btn_refresh").classList.add("spinning");
        try {
            const [overview, recent] = await Promise.all([
                fetch(`/api/v1/analytics/overview?days=${days}`).then((r) => r.json()),
                fetch("/api/v1/analytics/recent-events?limit=12").then((r) => r.json()),
            ]);
            render(overview);
            renderRecent(recent);
        } catch (e) {
            set("generated_at", "No se pudo actualizar");
        } finally {
            main.classList.remove("loading");
            setTimeout(() => $("btn_refresh").classList.remove("spinning"), 600);
        }
    }

    function selectPeriod(value) {
        days = value;
        try { localStorage.setItem(PERIOD_KEY, String(value)); } catch (e) { /* opcional */ }
        document.querySelectorAll(".segmented button").forEach((b) =>
            b.setAttribute("aria-checked", String(parseInt(b.dataset.days, 10) === value)));
        load();
    }

    document.querySelectorAll(".segmented button").forEach((b) =>
        b.addEventListener("click", () => selectPeriod(parseInt(b.dataset.days, 10))));
    $("btn_refresh").addEventListener("click", load);
    $("btn_theme").addEventListener("click", () => {
        const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        try { localStorage.setItem(THEME_KEY, next); } catch (e) { /* opcional */ }
        if (lastData && lastData.available && window.Chart) renderChart(lastData.daily);  // colores del tema
    });

    selectPeriod(days);
    setInterval(load, REFRESH_MS);
})();
