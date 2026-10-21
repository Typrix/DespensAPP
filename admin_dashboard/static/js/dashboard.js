// ========================================================
// DespensAPP Analytics & Admin Console - Client Logic
// Reactive Telemetry Polling & Chart.js Visualizations
// ========================================================

document.addEventListener("DOMContentLoaded", () => {
    let screenTimeChart = null;
    let screenViewsChart = null;
    let isPolling = true;

    // Colores del sistema de diseño para los gráficos
    const palette = {
        blue: "#3B82F6",
        emerald: "#10B981",
        amber: "#F59E0B",
        purple: "#8B5CF6",
        pink: "#EC4899",
        cyan: "#06B6D4",
        gridLine: "rgba(255, 255, 255, 0.05)",
        textMuted: "#94A3B8"
    };

    // ----------------------------------------------------
    // Actualización de KPIs
    // ----------------------------------------------------
    async function updateKPIs() {
        try {
            const res = await fetch("/api/v1/analytics/kpis");
            if (!res.ok) return;
            const data = await res.json();

            document.getElementById("kpi_users").textContent = data.total_users || 0;
            document.getElementById("kpi_avg_session").textContent = data.avg_session_str || "0m 0s";
            document.getElementById("kpi_sessions").textContent = data.total_sessions || 0;
            document.getElementById("kpi_screen").textContent = data.most_active_screen || "Inicio";
            document.getElementById("kpi_events").textContent = data.total_events || 0;

            const dbStatusEl = document.getElementById("db_status_text");
            if (dbStatusEl) {
                dbStatusEl.textContent = data.db_status || "Conectado";
            }
        } catch (e) {
            console.warn("Error al actualizar KPIs:", e);
        }
    }

    // ----------------------------------------------------
    // Gráficos con Chart.js
    // ----------------------------------------------------
    async function updateCharts() {
        try {
            const res = await fetch("/api/v1/analytics/screen-times");
            if (!res.ok) return;
            const data = await res.json();

            const screenLabelsMap = {
                "home": "Inicio",
                "cart": "Compras",
                "cupboard": "Despensa",
                "lists": "Listas",
                "stats": "Estadísticas",
                "splash": "Bienvenida"
            };

            const labels = data.length > 0 ? data.map(d => screenLabelsMap[d.screen] || d.screen) : ["Inicio", "Despensa", "Compras"];
            const minutes = data.length > 0 ? data.map(d => d.minutes) : [0.5, 0.3, 0.2];
            const views = data.length > 0 ? data.map(d => d.views) : [1, 1, 1];

            const chartColors = [palette.blue, palette.emerald, palette.amber, palette.purple, palette.pink, palette.cyan];

            // 1. Gráfico de Tiempos (Donut)
            const ctxDonut = document.getElementById("screenTimeChart");
            if (ctxDonut) {
                if (screenTimeChart) {
                    screenTimeChart.data.labels = labels;
                    screenTimeChart.data.datasets[0].data = minutes;
                    screenTimeChart.update();
                } else {
                    screenTimeChart = new Chart(ctxDonut, {
                        type: "doughnut",
                        data: {
                            labels: labels,
                            datasets: [{
                                data: minutes,
                                backgroundColor: chartColors,
                                borderWidth: 0,
                                hoverOffset: 6
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: "bottom",
                                    labels: {
                                        color: palette.textMuted,
                                        font: { family: "Plus Jakarta Sans", size: 11, weight: 500 },
                                        padding: 16,
                                        boxWidth: 12,
                                        boxHeight: 12,
                                        borderRadius: 3
                                    }
                                },
                                tooltip: {
                                    callbacks: {
                                        label: function(ctx) {
                                            return ` ${ctx.label}: ${ctx.raw} min acumulados`;
                                        }
                                    }
                                }
                            },
                            cutout: "70%"
                        }
                    });
                }
            }

            // 2. Gráfico de Vistas / Visitas por Pantalla (Barras)
            const ctxBar = document.getElementById("screenViewsChart");
            if (ctxBar) {
                if (screenViewsChart) {
                    screenViewsChart.data.labels = labels;
                    screenViewsChart.data.datasets[0].data = views;
                    screenViewsChart.update();
                } else {
                    screenViewsChart = new Chart(ctxBar, {
                        type: "bar",
                        data: {
                            labels: labels,
                            datasets: [{
                                label: "Visitas",
                                data: views,
                                backgroundColor: palette.blue,
                                borderRadius: 8,
                                borderSkipped: false,
                                maxBarThickness: 32
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: false },
                                tooltip: {
                                    callbacks: {
                                        label: function(ctx) {
                                            return ` ${ctx.raw} interacciones`;
                                        }
                                    }
                                }
                            },
                            scales: {
                                x: {
                                    grid: { display: false },
                                    ticks: { color: palette.textMuted, font: { family: "Plus Jakarta Sans", size: 11 } }
                                },
                                y: {
                                    beginAtZero: true,
                                    grid: { color: palette.gridLine },
                                    ticks: {
                                        precision: 0,
                                        color: palette.textMuted,
                                        font: { family: "Plus Jakarta Sans", size: 10 }
                                    }
                                }
                            }
                        }
                    });
                }
            }
        } catch (e) {
            console.warn("Error al actualizar gráficos:", e);
        }
    }

    // ----------------------------------------------------
    // Tabla de Eventos en Tiempo Real
    // ----------------------------------------------------
    async function updateRecentEvents() {
        try {
            const res = await fetch("/api/v1/analytics/recent-events?limit=15");
            if (!res.ok) return;
            const events = await res.json();

            const tbody = document.getElementById("events_table_body");
            if (!tbody) return;

            if (events.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 32px;">
                            Sin eventos registrados aún. Abre la aplicación móvil DespensAPP para registrar actividad.
                        </td>
                    </tr>
                `;
                return;
            }

            function getTagClass(name) {
                if (name.includes("cart")) return "tag-cart";
                if (name.includes("pantry")) return "tag-pantry";
                if (name.includes("screen")) return "tag-screen";
                if (name.includes("auth") || name.includes("user")) return "tag-auth";
                return "tag-default";
            }

            tbody.innerHTML = events.map(ev => `
                <tr>
                    <td style="font-family: monospace; font-size: 0.8rem; color: var(--text-muted);">#${ev.id}</td>
                    <td>
                        <span class="event-tag ${getTagClass(ev.event_name)}">${ev.event_name}</span>
                    </td>
                    <td style="font-weight: 500;">${ev.screen_name}</td>
                    <td style="color: var(--text-secondary);">${ev.user_name}</td>
                    <td style="color: var(--text-muted); font-size: 0.78rem;">${ev.created_at}</td>
                </tr>
            `).join("");
        } catch (e) {
            console.warn("Error al actualizar eventos:", e);
        }
    }

    // ----------------------------------------------------
    // Ciclo de Actualización Periódica
    // ----------------------------------------------------
    async function refreshAll() {
        const btn = document.getElementById("btn_refresh");
        if (btn) btn.classList.add("loading");

        await Promise.all([
            updateKPIs(),
            updateCharts(),
            updateRecentEvents()
        ]);

        if (btn) btn.classList.remove("loading");
    }

    // Botón de refresco manual
    const refreshBtn = document.getElementById("btn_refresh");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            refreshAll();
        });
    }

    // Carga inicial
    refreshAll();

    // Auto-polling cada 3 segundos para reflejar las acciones de la app en vivo
    setInterval(() => {
        if (isPolling) {
            refreshAll();
        }
    }, 3000);
});
