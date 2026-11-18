/*
 * Clickable chart bars.
 *
 * Put data-chart-link="<type>" on any element that contains Plotly charts and every
 * bar (the whole column, not just the coloured part) and every axis label becomes a
 * link to that item's page, keeping the current date range.
 *
 * Types: program, author, output (media channel), output-type, category, platform
 */
(function () {
    const LINK_BUILDERS = {
        'program':     (label) => ({ path: `/program/${encodeURIComponent(label)}` }),
        'author':      (label) => ({ path: `/author/${encodeURIComponent(label)}` }),
        'category':    (label) => ({ path: `/category/${encodeURIComponent(label)}` }),
        'output':      (label) => ({ path: `/output/${encodeURIComponent(label)}`, params: { output: label } }),
        'output-type': (label) => ({ path: `/output-type/${encodeURIComponent(label)}`, params: { type: label } }),
        'platform':    (label) => ({ path: label.toLowerCase() === 'website' ? '/media' : `/social/${encodeURIComponent(label)}` }),
    };

    function currentDates() {
        const params = new URLSearchParams(window.location.search);
        const startEl = document.getElementById('start_date');
        const endEl = document.getElementById('end_date');
        return {
            start: (startEl && startEl.value) || params.get('start_date') || '',
            end: (endEl && endEl.value) || params.get('end_date') || '',
        };
    }

    function buildUrl(type, label) {
        const builder = LINK_BUILDERS[type];
        if (!builder || !label) return null;
        const { path, params = {} } = builder(label);
        const query = new URLSearchParams(params);
        const { start, end } = currentDates();
        if (start) query.set('start_date', start);
        if (end) query.set('end_date', end);
        const qs = query.toString();
        return qs ? `${path}?${qs}` : path;
    }

    function labelFromPoint(point, horizontal) {
        if (!point) return null;
        const axisValue = horizontal ? point.y : point.x;
        if (typeof axisValue === 'string' && axisValue.trim() !== '') return axisValue.trim();

        let val = point.customdata;
        while (Array.isArray(val) && val.length) val = val[0];
        if (val !== undefined && val !== null && String(val).trim() !== '') return String(val).trim();

        if (axisValue !== undefined && axisValue !== null) return String(axisValue).trim();
        return null;
    }

    function go(type, label) {
        const url = buildUrl(type, label);
        if (url) window.location.href = url;
    }

    function bindPlot(plotDiv, type) {
        if (plotDiv.dataset.chartLinkBound) return;
        plotDiv.dataset.chartLinkBound = '1';

        const trace = plotDiv.data && plotDiv.data[0];
        const horizontal = !!trace && trace.orientation === 'h';

        // Hover/click snap to the nearest category, so the whole column is clickable
        Plotly.relayout(plotDiv, { hovermode: horizontal ? 'y' : 'x' });

        plotDiv.on('plotly_hover', () => {
            const drag = plotDiv.querySelector('.nsewdrag');
            if (drag) drag.style.cursor = 'pointer';
        });

        plotDiv.on('plotly_click', (data) => {
            const point = data && data.points && data.points[0];
            go(type, labelFromPoint(point, horizontal));
        });

        // Axis category labels are clickable too (re-applied after every redraw)
        const bindTickLabels = () => {
            plotDiv.querySelectorAll(horizontal ? '.ytick text' : '.xtick text').forEach((t) => {
                t.style.cursor = 'pointer';
                t.style.pointerEvents = 'all';
                t.onclick = () => go(type, t.textContent.trim());
            });
        };
        bindTickLabels();
        plotDiv.on('plotly_afterplot', bindTickLabels);
    }

    function bindAll() {
        let pending = 0;
        document.querySelectorAll('[data-chart-link]').forEach((wrapper) => {
            const type = wrapper.dataset.chartLink;
            wrapper.querySelectorAll('.plotly-graph-div').forEach((plotDiv) => {
                if (plotDiv.classList.contains('js-plotly-plot') && typeof plotDiv.on === 'function') bindPlot(plotDiv, type);
                else pending++;
            });
        });
        return pending;
    }

    document.addEventListener('DOMContentLoaded', () => {
        let attempts = 0;
        const timer = setInterval(() => {
            attempts++;
            if (typeof Plotly === 'undefined') {
                if (attempts > 150) clearInterval(timer);
                return;
            }
            if (bindAll() === 0 || attempts > 150) clearInterval(timer);
        }, 100);
    });

    window.ChartLinks = { buildUrl, bindAll };
})();
