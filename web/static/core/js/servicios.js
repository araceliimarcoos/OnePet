document.addEventListener('DOMContentLoaded', () => {

    // Reutilizables
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
        const menuBtn = itemDropdown.closest('.dropdown-menu').previousElementSibling;
        return {
            id:          menuBtn?.dataset.id,
            clave:       menuBtn?.dataset.clave,
            nombre:      menuBtn?.dataset.nombre,
            costo:      menuBtn?.dataset.costo,
            descripcion: menuBtn?.dataset.descripcion,
        };
    }

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }

    // Modal de Nuevo Servicio ──────────────────────────────────────────────────
    const overlayNuevo = document.getElementById('modalNuevoServicio');
    const formNuevo    = document.getElementById('formNuevoServicio');

    document.getElementById('btnNuevoServicio')
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

        // Se busca aquí dentro para garantizar que el elemento existe
        const btnGuardar = formNuevo.querySelector('[type=submit]');
        const textoOriginal  = btnGuardar.innerHTML;
        btnGuardar.disabled  = true;
        btnGuardar.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span> Guardando...';

        try {
            const resp = await fetch('/servicios/nuevo/', {
                method:  'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
                body:    new FormData(formNuevo),
            });

            const data = await resp.json();

            if (data.ok) {
                cerrarOverlay(overlayNuevo, formNuevo);
                mostrarToast('Servicio agregado', `${data.nombre} — ${data.clave}`);
                setTimeout(() => window.location.reload(), 2500); // espera a que se vea el toast
            } else {
                mostrarError(overlayNuevo, data.error || 'Ocurrió un error al guardar');
            }

        } catch {
            mostrarError(overlayNuevo, 'No se pudo conectar con el servidor');
        } finally {
            btnGuardar.disabled  = false;
            btnGuardar.innerHTML = textoOriginal;
        }
    });

    // Modal de Ver detalles ──────────────────────────────────────────────────
    const overlayDetalles = document.getElementById('modalVerDetalles');

    function abrirDetalles(datos) {
        document.getElementById('detalle-clave').textContent       = datos.clave       || '—';
        document.getElementById('detalle-nombre').textContent      = datos.nombre      || '—';
        document.getElementById('detalle-costo').textContent      = datos.costo ? `$${datos.costo}` : '—';
        document.getElementById('detalle-descripcion').textContent = datos.descripcion || '—';
        abrirOverlay(overlayDetalles);
    }

    document.getElementById('btnCerrarDetalles')
        ?.addEventListener('click', () => cerrarOverlay(overlayDetalles));
    document.getElementById('btnCerrarDetalles2')
        ?.addEventListener('click', () => cerrarOverlay(overlayDetalles));
    overlayDetalles?.addEventListener('click', (e) => {
        if (e.target === overlayDetalles) cerrarOverlay(overlayDetalles);
    });

    // ─── MODAL: EDITAR MEDICAMENTO ────────────────────────────────────────────

    const overlayEditar = document.getElementById('modalEditarServicio');
    const formEditar    = document.getElementById('formEditarServicio');

    function abrirEditar(datos) {
        document.getElementById('editar-id').value          = datos.id          || '';
        document.getElementById('editar-nombre').value      = datos.nombre      || '';
        document.getElementById('editar-costo').value      = datos.costo      || '';
        document.getElementById('editar-descripcion').value = datos.descripcion || '';
        formEditar.action = `/servicios/${datos.id}/editar/`;
        abrirOverlay(overlayEditar);
    }

    document.getElementById('btnCerrarEditar')
        ?.addEventListener('click', () => cerrarOverlay(overlayEditar, formEditar));
    document.getElementById('btnCancelarEditar')
        ?.addEventListener('click', () => cerrarOverlay(overlayEditar, formEditar));
    overlayEditar?.addEventListener('click', (e) => {
        if (e.target === overlayEditar) cerrarOverlay(overlayEditar, formEditar);
    });


    // ─── MENÚ DE ACCIONES ───────────────────────────────────────────────────

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

        const dangerBtn = e.target.closest('.dropdown-item.danger');
        if (dangerBtn) {
            cerrarDropdowns();
            const { id, nombre } = dangerBtn.dataset;
            if (confirm(`¿Eliminar "${nombre}"? Esta acción no se puede deshacer.`)) {
                window.location.href = `/medicamentos/${id}/eliminar/`;
            }
            return;
        }

        cerrarDropdowns();
    });

    // ─── ESCAPE cierra todo ────────────────────────────────────────────────────

    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        cerrarDropdowns();
        if (overlayNuevo?.classList.contains('visible'))    cerrarOverlay(overlayNuevo, formNuevo);
        if (overlayDetalles?.classList.contains('visible')) cerrarOverlay(overlayDetalles);
        if (overlayEditar?.classList.contains('visible'))   cerrarOverlay(overlayEditar, formEditar);
    });

    document.addEventListener('scroll', cerrarDropdowns, true);

    // ─── TOAST ────────────────────────────────────────────────────
    function mostrarToast(titulo, mensaje, duracion = 8000) {
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