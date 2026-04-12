document.addEventListener('DOMContentLoaded', () => {

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }

    // ── Búsqueda ──────────────────────────────────────────────────────────────
    document.getElementById('pagoSearch')?.addEventListener('input', function() {
        const q = this.value.toLowerCase();
        document.querySelectorAll('#pagosBody tr').forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    });

    // ── Modal generar pago ────────────────────────────────────────────────────
    const overlayPago = document.getElementById('modalNuevoPago');
    const overlayConf = document.getElementById('modalConfirmacionFinal');

    let tipoActual  = 'consulta';
    let idActual    = null;
    let totalActual = 0;

    function abrirPago() {
        overlayPago.classList.add('visible');
        document.body.style.overflow = 'hidden';
    }
    function cerrarPago() {
        overlayPago.classList.remove('visible');
        document.body.style.overflow = '';
        resetDesglose();
    }

    document.getElementById('btnNuevoPago')?.addEventListener('click', abrirPago);
    document.getElementById('btnCerrarPago')?.addEventListener('click', cerrarPago);
    document.getElementById('btnCancelarPago')?.addEventListener('click', cerrarPago);
    overlayPago?.addEventListener('click', (e) => { if (e.target === overlayPago) cerrarPago(); });

    // Tabs tipo
    document.querySelectorAll('.tipo-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tipo-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            tipoActual = btn.dataset.tipo;
            document.getElementById('panelConsulta').style.display = tipoActual === 'consulta' ? 'block' : 'none';
            document.getElementById('panelHosp').style.display = tipoActual === 'hospitalizacion' ? 'block' : 'none';
            resetDesglose();
        });
    });

    // Cargar desglose al seleccionar
    document.getElementById('selectConsulta')?.addEventListener('change', function() {
        if (this.value) cargarDesglose('consulta', this.value);
        else resetDesglose();
    });

    document.getElementById('selectHosp')?.addEventListener('change', function() {
        if (this.value) cargarDesglose('hospitalizacion', this.value);
        else resetDesglose();
    });

    function resetDesglose() {
        document.getElementById('desglose').style.display = 'none';
        document.getElementById('cargandoDesglose').style.display = 'none';
        document.getElementById('desgloseBody').innerHTML = '';
        document.getElementById('btnConfirmarPago').disabled = true;
        idActual = null; totalActual = 0;
    }

    async function cargarDesglose(tipo, id) {
        resetDesglose();
        document.getElementById('cargandoDesglose').style.display = 'block';

        try {
            const resp = await fetch(`/pagos/previsualizar/?tipo=${tipo}&id=${id}`);
            const data = await resp.json();

            document.getElementById('cargandoDesglose').style.display = 'none';

            if (!data.ok) { alert(data.error); return; }

            idActual    = id;
            totalActual = data.total;

            const tbody = document.getElementById('desgloseBody');
            tbody.innerHTML = '';

            const iconos = { 
                base: 'local_hospital', 
                servicio: 'menu_book', 
                medicamento: 'medication', 
            };

            data.items.forEach(item => {
                const tr = document.createElement('tr');
                tr.style.borderBottom = '1px solid var(--border)';
                tr.innerHTML = `
                    <td style="padding:8px 12px;">
                        <div style="display:flex; align-items:center; gap:6px; font-weight:600; font-size:0.85rem; color:var(--text);">
                            <span class="material-symbols-outlined" style="color:var(--blue); font-size:16px; line-height:1; flex-shrink:0;">${iconos[item.tipo] || 'receipt'}</span>
                            ${item.nombre}
                        </div>
                        ${item.descripcion ? `<div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px; padding-left:22px;">${item.descripcion}</div>` : ''}
                    </td>
                    <td style="padding:8px 12px; text-align:right; color:var(--text-muted); font-size:0.83rem;">
                        ${item.cantidad}
                    </td>
                    <td style="padding:8px 12px; text-align:right; font-weight:600; color:var(--text);">
                        $${parseFloat(item.subtotal).toFixed(2)}
                    </td>
                `;
                tbody.appendChild(tr);
            });

            document.getElementById('desgloseTotal').textContent = `$${data.total.toFixed(2)}`;
            document.getElementById('desglose').style.display = 'block';
            document.getElementById('btnConfirmarPago').disabled = false;

        } catch {
            document.getElementById('cargandoDesglose').style.display = 'none';
            alert('Error al cargar el desglose');
        }
    }

    // Abrir confirmación final
    document.getElementById('btnConfirmarPago')?.addEventListener('click', () => {
        document.getElementById('cfTotal').textContent = `$${totalActual.toFixed(2)}`;
        overlayConf.classList.add('visible');
    });

    document.getElementById('btnCerrarConfirmacion')?.addEventListener('click', () => {
        overlayConf.classList.remove('visible');
    });
    document.getElementById('btnCancelarConfirmacion')?.addEventListener('click', () => {
        overlayConf.classList.remove('visible');
    });

    // Confirmar y crear pago
    document.getElementById('btnPagarFinal')?.addEventListener('click', async () => {
        const btn = document.getElementById('btnPagarFinal');
        btn.disabled = true;
        btn.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span> Procesando...';

        const body = new FormData();
        body.append('tipo', tipoActual);
        body.append('id', idActual);

        try {
            const resp = await fetch('/pagos/confirmar/', {
                method: 'POST',
                headers: { 'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '' },
                body,
            });
            const data = await resp.json();

            if (data.ok) {
                window.location.href = `/pagos/${data.codigo}/recibo/`;
            } else {
                alert(data.error || 'Error al procesar el pago');
                btn.disabled = false;
                btn.innerHTML = '<span class="material-symbols-outlined">check_circle</span> Confirmar y Pagar';
            }
        } catch {
            alert('Error de conexión');
            btn.disabled = false;
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        cerrarPago();
        overlayConf.classList.remove('visible');
    });

});