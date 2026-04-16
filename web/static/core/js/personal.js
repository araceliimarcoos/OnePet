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

    // ─── MODAL: NUEVO VETERINARIO ─────────────────────────────────────────────

    const overlayNuevo = document.getElementById('modalNuevoVeterinario');
    const formNuevo    = document.getElementById('formNuevoVeterinario');

    document.getElementById('btnNuevoVeterinario')
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
            const resp = await fetch('/personal/nuevo/', {
                method:  'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
                body:    new FormData(formNuevo),
            });
            const data = await resp.json();
            if (data.ok) {
                cerrarOverlay(overlayNuevo, formNuevo);
                mostrarToast('Veterinario registrado', `${data.nombre} — ${data.folio}`);
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
        const nombre = d.nombre || '';
        // Iniciales para el avatar: primera letra de nombre y primer apellido
        const partes   = nombre.trim().split(' ');
        const iniciales = partes.length >= 2
            ? (partes[0][0] + partes[1][0]).toUpperCase()
            : nombre.slice(0, 2).toUpperCase();

        const avatar = document.getElementById('det-avatar');
        if (avatar) avatar.textContent = iniciales || '—';

        document.getElementById('det-folio').textContent        = d.folio        || '—';
        document.getElementById('det-nombre').textContent       = nombre         || '—';
        document.getElementById('det-correo').textContent       = d.correo       || '—';
        document.getElementById('det-telefono').textContent     = d.telefono     || '—';
        document.getElementById('det-cedula').textContent       = d.cedula       || '—';
        document.getElementById('det-especialidad').textContent = d.especialidad || '—';
        abrirOverlay(overlayDetalles);
    }

    document.getElementById('btnCerrarDetalles')
        ?.addEventListener('click', () => cerrarOverlay(overlayDetalles));
    document.getElementById('btnCerrarDetalles2')
        ?.addEventListener('click', () => cerrarOverlay(overlayDetalles));
    overlayDetalles?.addEventListener('click', (e) => {
        if (e.target === overlayDetalles) cerrarOverlay(overlayDetalles);
    });

    // ─── MODAL: EDITAR VETERINARIO ────────────────────────────────────────────

    const overlayEditar = document.getElementById('modalEditarVeterinario');
    const formEditar    = document.getElementById('formEditarVeterinario');

    function abrirEditar(d) {
        document.getElementById('editar-folio').value          = d.folio          || '';
        document.getElementById('editar-nombre').value         = d.nombrepila     || '';
        document.getElementById('editar-apellido-pat').value   = d.apellidoPat    || '';
        document.getElementById('editar-apellido-mat').value   = d.apellidoMat    || '';
        document.getElementById('editar-correo').value         = d.correo         || '';
        document.getElementById('editar-telefono').value       = d.telefono       || '';
        document.getElementById('editar-cedula').value         = d.cedula         || '';

        const selEsp = document.getElementById('editar-especialidad');
        [...selEsp.options].forEach(o => {
            o.selected = o.value === d.especialidadClave;
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

    formEditar?.addEventListener('submit', async (e) => {
        e.preventDefault();
        limpiarError(overlayEditar);
        const folio         = document.getElementById('editar-folio').value;
        const btnGuardar    = formEditar.querySelector('[type=submit]');
        const textoOriginal = btnGuardar.innerHTML;
        btnGuardar.disabled = true;
        btnGuardar.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span> Guardando...';
        try {
            const resp = await fetch(`/personal/${folio}/editar/`, {
                method:  'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
                body:    new FormData(formEditar),
            });
            const data = await resp.json();
            if (data.ok) {
                cerrarOverlay(overlayEditar, formEditar);
                mostrarToast('Veterinario actualizado', `${data.nombre} — ${data.folio}`);
                setTimeout(() => window.location.reload(), 2500);
            } else {
                mostrarError(overlayEditar, data.error || 'Error al guardar');
            }
        } catch {
            mostrarError(overlayEditar, 'No se pudo conectar con el servidor');
        } finally {
            btnGuardar.disabled  = false;
            btnGuardar.innerHTML = textoOriginal;
        }
    });

    // ─── MODAL: NUEVA ESPECIALIDAD ────────────────────────────────────────────

    const overlayEsp = document.getElementById('modalNuevaEspecialidad');
    const formEsp    = document.getElementById('formNuevaEspecialidad');

    document.getElementById('btnNuevaEspecialidad')
        ?.addEventListener('click', () => abrirOverlay(overlayEsp));
    document.getElementById('btnCerrarEsp')
        ?.addEventListener('click', () => cerrarOverlay(overlayEsp, formEsp));
    document.getElementById('btnCancelarEsp')
        ?.addEventListener('click', () => cerrarOverlay(overlayEsp, formEsp));
    overlayEsp?.addEventListener('click', (e) => {
        if (e.target === overlayEsp) cerrarOverlay(overlayEsp, formEsp);
    });

    formEsp?.addEventListener('submit', async (e) => {
        e.preventDefault();
        limpiarError(overlayEsp);
        const btnGuardar    = formEsp.querySelector('[type=submit]');
        const textoOriginal = btnGuardar.innerHTML;
        btnGuardar.disabled = true;
        btnGuardar.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span> Guardando...';
        try {
            const resp = await fetch('/personal/especialidades/nueva/', {
                method:  'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
                body:    new FormData(formEsp),
            });
            const data = await resp.json();
            if (data.ok) {
                cerrarOverlay(overlayEsp, formEsp);
                mostrarToast('Especialidad agregada', `${data.nombre}`);
                setTimeout(() => window.location.reload(), 2500);
            } else {
                mostrarError(overlayEsp, data.error || 'Error al guardar');
            }
        } catch {
            mostrarError(overlayEsp, 'No se pudo conectar con el servidor');
        } finally {
            btnGuardar.disabled  = false;
            btnGuardar.innerHTML = textoOriginal;
        }
    });

    // ─── MODAL: CONFIRMAR BAJA ────────────────────────────────────────────────

    const overlayBaja = document.getElementById('modalConfirmarBaja');
    let folioParaBaja = null;

    function abrirBaja(d) {
        folioParaBaja = d.id;
        document.getElementById('baja-nombre').textContent = d.nombre || 'este veterinario';
        abrirOverlay(overlayBaja);
    }

    document.getElementById('btnCerrarBaja')
        ?.addEventListener('click', () => cerrarOverlay(overlayBaja));
    document.getElementById('btnCancelarBaja')
        ?.addEventListener('click', () => cerrarOverlay(overlayBaja));
    overlayBaja?.addEventListener('click', (e) => {
        if (e.target === overlayBaja) cerrarOverlay(overlayBaja);
    });

    document.getElementById('btnConfirmarBaja')?.addEventListener('click', async () => {
        if (!folioParaBaja) return;
        const btn           = document.getElementById('btnConfirmarBaja');
        const textoOriginal = btn.innerHTML;
        btn.disabled        = true;
        btn.innerHTML       = '<span class="material-symbols-outlined">hourglass_top</span> Procesando...';
        try {
            const resp = await fetch(`/personal/${folioParaBaja}/baja/`, {
                method:  'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
            });
            const data = await resp.json();
            if (data.ok) {
                cerrarOverlay(overlayBaja);
                mostrarToast('Veterinario dado de baja', '');
                setTimeout(() => window.location.reload(), 2500);
            } else {
                cerrarOverlay(overlayBaja);
                mostrarToast('Error', data.error || 'No se pudo dar de baja');
            }
        } catch {
            cerrarOverlay(overlayBaja);
            mostrarToast('Error', 'No se pudo conectar con el servidor');
        } finally {
            btn.disabled  = false;
            btn.innerHTML = textoOriginal;
        }
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
        if (itemDetalles) { cerrarDropdowns(); abrirDetalles(leerDatosFila(itemDetalles)); return; }
        const itemEditar = e.target.closest('.dropdown-item[data-accion="editar"]');
        if (itemEditar)   { cerrarDropdowns(); abrirEditar(leerDatosFila(itemEditar)); return; }
        const dangerBtn = e.target.closest('.dropdown-item.danger');
        if (dangerBtn)    { cerrarDropdowns(); abrirBaja(dangerBtn.dataset); return; }
        cerrarDropdowns();
    });

    // ─── ESCAPE ───────────────────────────────────────────────────────────────

    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        cerrarDropdowns();
        if (overlayNuevo?.classList.contains('visible'))    cerrarOverlay(overlayNuevo, formNuevo);
        if (overlayDetalles?.classList.contains('visible')) cerrarOverlay(overlayDetalles);
        if (overlayEditar?.classList.contains('visible'))   cerrarOverlay(overlayEditar, formEditar);
        if (overlayBaja?.classList.contains('visible'))     cerrarOverlay(overlayBaja);
        if (overlayEsp?.classList.contains('visible'))      cerrarOverlay(overlayEsp, formEsp);
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
                ${mensaje ? `<p class="toast-msg">${mensaje}</p>` : ''}
            </div>
            <button class="toast-close" aria-label="Cerrar">
                <span class="material-symbols-outlined" style="font-size:17px;">close</span>
            </button>
            <div class="toast-bar"></div>
        `;
        contenedor.appendChild(toast);
        requestAnimationFrame(() => toast.classList.add('show'));
        const bar = toast.querySelector('.toast-bar');
        bar.animate([{ transform: 'scaleX(1)' }, { transform: 'scaleX(0)' }],
            { duration: duracion, easing: 'linear', fill: 'forwards' });
        const timer = setTimeout(() => cerrarToast(toast), duracion);
        toast.querySelector('.toast-close').addEventListener('click', () => {
            clearTimeout(timer); cerrarToast(toast);
        });
    }

    function cerrarToast(toast) {
        toast.classList.remove('show');
        toast.classList.add('hide');
        toast.addEventListener('transitionend', () => toast.remove(), { once: true });
    }


    const buscador = document.querySelector("input[name='q']");
    const filtro = document.getElementById("filterEspecialidad");
    const filas = document.querySelectorAll("#personalBody tr");

    function filtrar() {
        const texto = buscador.value.toLowerCase();
        const especialidad = filtro.value.toLowerCase();

        filas.forEach(fila => {
            const nombre = fila.innerText.toLowerCase();
            const esp = fila.dataset.especialidad;

            const coincideTexto = nombre.includes(texto);
            const coincideEspecialidad = !especialidad || esp === especialidad;

            if (coincideTexto && coincideEspecialidad) {
                fila.style.display = "";
            } else {
                fila.style.display = "none";
            }
        });
    }

    buscador.addEventListener("input", filtrar);
    filtro.addEventListener("change", filtrar);

});