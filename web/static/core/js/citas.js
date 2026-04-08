document.addEventListener('DOMContentLoaded', () => {

    // ─── UTILIDADES ───────────────────────────────────────────────────────────

    function abrirOverlay(overlay) {
        overlay.classList.add('visible');
        document.body.style.overflow = 'hidden';
    }

    function cerrarOverlay(overlay, form = null) {
        overlay.classList.remove('visible');
        document.body.style.overflow = '';
        if (form) form.reset();
        limpiarError(overlay);
    }

    function mostrarError(overlay, mensaje) {
        const el = overlay.querySelector('.modal-error');
        if (!el) return;
        el.textContent = mensaje;
        el.style.display = 'block';
    }

    function limpiarError(overlay) {
        const el = overlay?.querySelector('.modal-error');
        if (el) el.style.display = 'none';
    }

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }

    function cerrarDropdowns() {
        document.querySelectorAll('.dropdown-menu.open').forEach(d => {
            d.classList.remove('open');
            d.removeAttribute('style');
        });
    }

    function abrirDropdown(btn, menu) {
        const rect       = btn.getBoundingClientRect();
        const menuHeight = 140;
        const spaceBelow = window.innerHeight - rect.bottom;
        const abreArriba = spaceBelow < menuHeight + 8;
        menu.classList.add('open');
        menu.style.left = `${rect.right - (menu.offsetWidth || 170)}px`;
        menu.style.top  = abreArriba
            ? `${rect.top - menu.offsetHeight - 4}px`
            : `${rect.bottom + 4}px`;
    }

    function leerDatosFila(itemDropdown) {
        const btn = itemDropdown.closest('.dropdown-menu').previousElementSibling;
        return btn ? { ...btn.dataset } : {};
    }

    // ─── FECHA MÍNIMA: mañana ─────────────────────────────────────────────────

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const minFecha = tomorrow.toISOString().split('T')[0];
    document.getElementById('fecha').min = minFecha;

    // ─── FILTRO DINÁMICO: mascotas por propietario ────────────────────────────

// ✅ json_script ya genera JSON válido, solo parsea el textContent
    const mascotas = JSON.parse(document.getElementById('mascotas-data').textContent) ?? [];    
    const propietarioSel = document.getElementById('propietario');
    const mascotaSel     = document.getElementById('mascota');

    propietarioSel?.addEventListener('change', () => {
        const folio = propietarioSel.value;

        mascotaSel.innerHTML = '';
        mascotaSel.disabled  = !folio;

        const defaultOpt = document.createElement('option');
        defaultOpt.value = '';
        defaultOpt.textContent = folio ? 'Seleccionar mascota...' : 'Seleccione un propietario...';
        mascotaSel.appendChild(defaultOpt);

        if (!folio) return;

        const filtradas = mascotas.filter(m => m['propietario__folio'] === folio);

        if (filtradas.length === 0) {
            const opt = document.createElement('option');
            opt.value = '';
            opt.textContent = 'Este propietario no tiene mascotas';
            mascotaSel.appendChild(opt);
            return;
        }

        filtradas.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.folio;
            opt.textContent = m.nombre;
            mascotaSel.appendChild(opt);
        });
    });

    // ─── MODAL: NUEVA CITA ────────────────────────────────────────────────────

    const overlayNuevo = document.getElementById('modalNuevaCita');
    const formNuevo    = document.getElementById('formNuevaCita');

    document.getElementById('btnNuevaCita')
        ?.addEventListener('click', () => abrirOverlay(overlayNuevo));
    document.getElementById('btnCerrarModal')
        ?.addEventListener('click', () => cerrarOverlay(overlayNuevo, formNuevo));
    document.getElementById('btnCancelar')
        ?.addEventListener('click', () => cerrarOverlay(overlayNuevo, formNuevo));
    overlayNuevo?.addEventListener('click', (e) => {
        if (e.target === overlayNuevo) cerrarOverlay(overlayNuevo, formNuevo);
    });

    formNuevo?.addEventListener('submit', async (e) => {
        e.preventDefault();
        limpiarError(overlayNuevo);

        const btnGuardar    = formNuevo.querySelector('[type=submit]');
        const textoOriginal = btnGuardar.innerHTML;
        btnGuardar.disabled = true;
        btnGuardar.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span> Guardando...';

        try {
            const resp = await fetch('/citas/nueva/', {
                method:  'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
                body:    new FormData(formNuevo),
            });
            const data = await resp.json();

            if (data.ok) {
                cerrarOverlay(overlayNuevo, formNuevo);
                mostrarToast('Cita registrada', `Folio #${data.folio} — ${data.fecha}`);
                setTimeout(() => window.location.reload(), 2500);
            } else {
                mostrarError(overlayNuevo, data.error || 'Error al guardar');
            }
        } catch {
            mostrarError(overlayNuevo, 'No se pudo conectar con el servidor');
        } finally {
            btnGuardar.disabled  = false;
            btnGuardar.innerHTML = textoOriginal;
        }
    });

    // ─── MODAL: VER DETALLES ──────────────────────────────────────────────────

    const overlayDetalles = document.getElementById('modalVerDetalles');

    function abrirDetalles(d) {
        document.getElementById('det-folio').textContent       = `#${d.folio || '—'}`;
        document.getElementById('det-estado').textContent      = d.estado      || '—';
        document.getElementById('det-fecha').textContent       = d.fecha       || '—';
        document.getElementById('det-hora').textContent        = d.hora        || '—';
        document.getElementById('det-propietario').textContent = d.propietario || '—';
        document.getElementById('det-mascota').textContent     = d.mascota     || '—';
        document.getElementById('det-veterinario').textContent = d.veterinario || '—';
        document.getElementById('det-motivo').textContent      = d.motivo      || '—';
        abrirOverlay(overlayDetalles);
    }

    document.getElementById('btnCerrarDetalles')
        ?.addEventListener('click', () => cerrarOverlay(overlayDetalles));
    document.getElementById('btnCerrarDetalles2')
        ?.addEventListener('click', () => cerrarOverlay(overlayDetalles));
    overlayDetalles?.addEventListener('click', (e) => {
        if (e.target === overlayDetalles) cerrarOverlay(overlayDetalles);
    });

    // ─── MODAL: EDITAR CITA ───────────────────────────────────────────────────

    const overlayEditar = document.getElementById('modalEditarCita');
    const formEditar    = document.getElementById('formEditarCita');

    function abrirEditar(d) {
        document.getElementById('editar-folio').value      = d.folio              || '';
        document.getElementById('editar-fecha').value      = d.fecha              || '';
        document.getElementById('editar-hora').value       = d.hora               || '';
        document.getElementById('editar-motivo').value     = d.motivo             || '';

        // Seleccionar veterinario actual en el select
        const selVet = document.getElementById('editar-veterinario');
        [...selVet.options].forEach(o => {
            o.selected = o.value === d.veterinarioFolio;
        });

        abrirOverlay(overlayEditar);
    }

    document.getElementById('btnCerrarEditar')
        ?.addEventListener('click', () => cerrarOverlay(overlayEditar, formEditar));
    document.getElementById('btnCancelarEditar')
        ?.addEventListener('click', () => cerrarOverlay(overlayEditar, formEditar));
    overlayEditar?.addEventListener('click', (e) => {
        if (e.target === overlayEditar) cerrarOverlay(overlayEditar, formEditar);
    });

    // ─── FILTROS DE TABLA ─────────────────────────────────────────────────────

    const searchInput   = document.getElementById('citasSearch');
    const filterEstado  = document.getElementById('filterEstado');
    const filterFecha   = document.getElementById('filterFecha');

    function filtrarTabla() {
        const q      = searchInput?.value.toLowerCase() || '';
        const estado = filterEstado?.value || '';
        const fecha  = filterFecha?.value  || '';

        document.querySelectorAll('#citasBody tr').forEach(row => {
            const texto       = row.textContent.toLowerCase();
            const rowEstado   = row.dataset.estado || '';
            const rowFecha    = row.dataset.fecha  || '';

            const okTexto  = !q      || texto.includes(q);
            const okEstado = !estado || rowEstado === estado;
            const okFecha  = !fecha  || rowFecha === fecha;

            row.style.display = (okTexto && okEstado && okFecha) ? '' : 'none';
        });
    }

    searchInput?.addEventListener('input',  filtrarTabla);
    filterEstado?.addEventListener('change', filtrarTabla);
    filterFecha?.addEventListener('change',  filtrarTabla);

    // ─── MENÚ DE ACCIONES ⋯ ───────────────────────────────────────────────────

    document.addEventListener('click', (e) => {

        const menuBtn = e.target.closest('.menu-btn');
        if (menuBtn) {
            const menu   = menuBtn.nextElementSibling;
            const isOpen = menu.classList.contains('open');
            cerrarDropdowns();
            if (!isOpen) abrirDropdown(menuBtn, menu);
            return;
        }

        const itemDetalles = e.target.closest('.dropdown-item[data-accion="detalles"]');
        if (itemDetalles) {
            cerrarDropdowns();
            abrirDetalles(leerDatosFila(itemDetalles));
            return;
        }

        const itemEditar = e.target.closest('.dropdown-item[data-accion="editar"]');
        if (itemEditar) {
            cerrarDropdowns();
            abrirEditar(leerDatosFila(itemEditar));
            return;
        }

        cerrarDropdowns();
    });

    // ─── ESCAPE ───────────────────────────────────────────────────────────────

    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        cerrarDropdowns();
        if (overlayNuevo?.classList.contains('visible'))    cerrarOverlay(overlayNuevo, formNuevo);
        if (overlayDetalles?.classList.contains('visible')) cerrarOverlay(overlayDetalles);
        if (overlayEditar?.classList.contains('visible'))   cerrarOverlay(overlayEditar, formEditar);
    });

    document.addEventListener('scroll', cerrarDropdowns, true);

    // ─── TOAST ────────────────────────────────────────────────────────────────

    function mostrarToast(titulo, mensaje, duracion = 4000) {
        const contenedor = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.innerHTML = `
            <div class="toast-icon">
                <span class="material-symbols-outlined">check_circle</span>
            </div>
            <div>
                <p class="toast-title">${titulo}</p>
                <p class="toast-msg">${mensaje}</p>
            </div>
            <button class="toast-close" aria-label="Cerrar">
                <span class="material-symbols-outlined" style="font-size:17px;">close</span>
            </button>
            <div class="toast-bar"></div>
        `;
        contenedor.appendChild(toast);
        requestAnimationFrame(() => toast.classList.add('show'));
        const bar = toast.querySelector('.toast-bar');
        bar.animate(
            [{ transform: 'scaleX(1)' }, { transform: 'scaleX(0)' }],
            { duration: duracion, easing: 'linear', fill: 'forwards' }
        );
        const timer = setTimeout(() => cerrarToast(toast), duracion);
        toast.querySelector('.toast-close').addEventListener('click', () => {
            clearTimeout(timer);
            cerrarToast(toast);
        });
    }

    function cerrarToast(toast) {
        toast.classList.remove('show');
        toast.classList.add('hide');
        toast.addEventListener('transitionend', () => toast.remove(), { once: true });
    }

});