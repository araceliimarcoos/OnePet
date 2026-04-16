document.addEventListener('DOMContentLoaded', () => {


// ─────── FILTRADO ───────────────────────────────────────────────────────────
    const filtroEstado = document.getElementById('filterEstado');
    const filtroRol = document.getElementById('filterRol');

    function aplicarFiltros() {
        const valorEstado = filtroEstado ? filtroEstado.value : 'todos';
        const valorRol = filtroRol ? filtroRol.value : '';

        const filas = document.querySelectorAll('#usuariosBody tr');

        filas.forEach(fila => {
            const estado = fila.dataset.estado;
            const rol = fila.dataset.rol;

            const coincideEstado = (valorEstado === 'todos' || estado === valorEstado);
            const coincideRol = (valorRol === '' || rol === valorRol);

            fila.style.display = (coincideEstado && coincideRol) ? '' : 'none';
        });
    }

    if (filtroEstado) filtroEstado.addEventListener('change', aplicarFiltros);
    if (filtroRol)    filtroRol.addEventListener('change', aplicarFiltros);
    aplicarFiltros();


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

    // ─── ESCAPE ───────────────────────────────────────────────────────────────

    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        cerrarDropdowns();
        if (overlayDetalles?.classList.contains('visible')) cerrarOverlay(overlayDetalles);
        if (overlayEditar?.classList.contains('visible'))   cerrarOverlay(overlayEditar, formEditar);
        if (overlayBaja?.classList.contains('visible'))     cerrarOverlay(overlayBaja);
    });

    document.addEventListener('scroll', cerrarDropdowns, true);


    // ─── MODAL: VER DETALLES ──────────────────────────────────────────────────

    const overlayDetalles = document.getElementById('modalVerDetalles');

    function abrirDetalles(d) {
        const nombre = d.nombre || '';
        const partes   = nombre.trim().split(' ');
        const iniciales = partes.length >= 2
            ? (partes[0][0] + partes[1][0]).toUpperCase()
            : nombre.slice(0, 2).toUpperCase();

        const avatar = document.getElementById('det-avatar');
        if (avatar) avatar.textContent = iniciales || '—';

        document.getElementById('det-nombre-real').textContent = d.nombre  || '—';
        document.getElementById('det-estado').textContent      = d.estado  || '—';
        document.getElementById('det-rol').textContent         = d.rol     || '—';
        document.getElementById('det-contrasena').textContent  = '********';

        abrirOverlay(overlayDetalles);
    }

    document.getElementById('btnCerrarDetalles')
        ?.addEventListener('click', () => cerrarOverlay(overlayDetalles));
    document.getElementById('btnCerrarDetalles2')
        ?.addEventListener('click', () => cerrarOverlay(overlayDetalles));
    overlayDetalles?.addEventListener('click', (e) => {
        if (e.target === overlayDetalles) cerrarOverlay(overlayDetalles);
    });


    // ─── MODAL: EDITAR USUARIO (SOLO CONTRASEÑA) ────────────────────────────

    const overlayEditar = document.getElementById('modalEditarUsuario');
    const formEditar    = document.getElementById('formEditarUsuario');

    function abrirEditar(d) {
        document.getElementById('editar_usuario_mostrar').value = d.usuario || '';
        document.getElementById('editar_usuario_nombre').value  = d.nombre  || '';
        document.getElementById('editar-usuario-id').value      = d.usuario || '';
        document.getElementById('editar_contrasena').value      = '';

        // Poblar la tarjeta visual del modal
        const nombre   = d.nombre || '';
        const partes   = nombre.trim().split(' ');
        const iniciales = partes.length >= 2
            ? (partes[0][0] + partes[1][0]).toUpperCase()
            : nombre.slice(0, 2).toUpperCase();

        const elIniciales = document.getElementById('editar_avatar_iniciales');
        const elNombre    = document.getElementById('editar_usuario_nombre_display');
        const elUsuario   = document.getElementById('editar_usuario_mostrar_display');
        if (elIniciales) elIniciales.textContent = iniciales || '??';
        if (elNombre)    elNombre.textContent    = nombre    || '—';
        if (elUsuario)   elUsuario.textContent   = d.usuario || '—';

        // Reset toggle de visibilidad
        const inputPass = document.getElementById('editar_contrasena');
        const eyeIcon   = document.getElementById('eyeIcon');
        if (inputPass) inputPass.type = 'password';
        if (eyeIcon)   eyeIcon.textContent = 'visibility';

        abrirOverlay(overlayEditar);
    }

    document.getElementById('btnCerrarEditar')
        ?.addEventListener('click', () => cerrarOverlay(overlayEditar, formEditar));
    document.getElementById('btnCancelarEditar')
        ?.addEventListener('click', () => cerrarOverlay(overlayEditar, formEditar));
    overlayEditar?.addEventListener('click', (e) => {
        if (e.target === overlayEditar) cerrarOverlay(overlayEditar, formEditar);
    });


    // ─── SUBMIT EDITAR CONTRASEÑA ────────────────────────────────────────────

    formEditar?.addEventListener('submit', async (e) => {
        e.preventDefault();
        limpiarError(overlayEditar);

        const usuario       = document.getElementById('editar-usuario-id').value;
        const btnGuardar    = formEditar.querySelector('[type=submit]');
        const textoOriginal = btnGuardar.innerHTML;

        btnGuardar.disabled  = true;
        btnGuardar.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span> Guardando...';

        try {
            const resp = await fetch(`/usuarios/${usuario}/cambiar-password/`, {
                method:  'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
                body:    new FormData(formEditar)
            });

            const data = await resp.json();

            if (data.ok) {
                cerrarOverlay(overlayEditar, formEditar);
                mostrarToast('Contraseña actualizada', `Usuario: ${usuario}`);
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

    // Toggle mostrar/ocultar contraseña
    const inputPass = document.getElementById('editar_contrasena');
    const toggleBtn = document.getElementById('togglePassword');
    const eyeIcon   = document.getElementById('eyeIcon');

    toggleBtn?.addEventListener('click', () => {
        const isHidden = inputPass.type === 'password';
        inputPass.type = isHidden ? 'text' : 'password';
        if (eyeIcon) eyeIcon.textContent = isHidden ? 'visibility_off' : 'visibility';
    });


    // ─── MODAL: CONFIRMAR BAJA ────────────────────────────────────────────────

    const overlayBaja = document.getElementById('modalConfirmarBaja');
    let usuarioParaBaja = null;
    let nombreParaBaja  = null;
    let filaParaBaja    = null;   // ← referencia a la <tr> para actualizar el DOM

    function abrirBaja(d) {
        usuarioParaBaja = d.usuario;
        nombreParaBaja  = d.nombre || d.usuario || 'este usuario';

        // Guardar referencia a la fila de la tabla
        const btn = document.querySelector(`.menu-btn[data-usuario="${d.usuario}"]`);
        filaParaBaja = btn ? btn.closest('tr') : null;

        document.getElementById('baja-usuario').textContent = nombreParaBaja;
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
        if (!usuarioParaBaja) return;

        const btn           = document.getElementById('btnConfirmarBaja');
        const textoOriginal = btn.innerHTML;
        btn.disabled        = true;
        btn.innerHTML       = '<span class="material-symbols-outlined">hourglass_top</span> Procesando...';

        try {
            const resp = await fetch(`/usuarios/${usuarioParaBaja}/baja/`, {
                method:  'POST',
                headers: { 'X-CSRFToken': getCsrfToken() }
            });

            const data = await resp.json();

            if (data.ok) {
                cerrarOverlay(overlayBaja);

                // ── Actualizar fila en el DOM sin recargar ──────────────────
                if (filaParaBaja) {
                    // Actualizar data-estado para que el filtro funcione
                    filaParaBaja.dataset.estado = 'inactivo';

                    // Reemplazar el badge de estado
                    const statusCell = filaParaBaja.querySelector('.status-cell');
                    if (statusCell) {
                        statusCell.innerHTML = `
                            <span class="status-dot status-inactive"></span>
                            <span class="status-text inactive">Inactive</span>
                        `;
                    }

                    // Animación sutil de fade en la fila
                    filaParaBaja.style.transition = 'opacity 0.4s ease';
                    filaParaBaja.style.opacity = '0.55';
                }

                mostrarToast('Usuario dado de baja', nombreParaBaja);

                // Re-aplicar filtros por si el filtro activo oculta inactivos
                setTimeout(aplicarFiltros, 400);

            } else {
                cerrarOverlay(overlayBaja);
                mostrarToast('Error', data.error || 'No se pudo dar de baja', 'error');
            }

        } catch (err) {
            console.error(err);
            cerrarOverlay(overlayBaja);
            mostrarToast('Error', 'No se pudo conectar con el servidor', 'error');
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
            abrirBaja(dangerBtn.dataset);
            return;
        }

        cerrarDropdowns();
    });


    // ─── TOAST ────────────────────────────────────────────────────────────────

    /**
     * @param {string} titulo
     * @param {string} mensaje
     * @param {'success'|'error'} tipo
     * @param {number} duracion  ms
     */
    function mostrarToast(titulo, mensaje = '', tipo = 'success', duracion = 4000) {
        const contenedor = document.getElementById('toast-container');
        const toast      = document.createElement('div');
        toast.className  = `toast toast-${tipo}`;

        const icono   = tipo === 'error' ? 'error'         : 'check_circle';
        const bgIcono = tipo === 'error' ? '#fdecea'       : '#EAF3DE';
        const color   = tipo === 'error' ? '#c0392b'       : '#3B6D11';
        const barColor= tipo === 'error' ? '#c0392b'       : '#1D9E75';
        const border  = tipo === 'error' ? '#c0392b'       : '#1D9E75';

        toast.innerHTML = `
            <div class="toast-icon" style="background:${bgIcono}">
                <span class="material-symbols-outlined" style="color:${color}">${icono}</span>
            </div>
            <div style="flex:1; min-width:0;">
                <p class="toast-title">${titulo}</p>
                ${mensaje ? `<p class="toast-msg">${mensaje}</p>` : ''}
            </div>
            <button class="toast-close" aria-label="Cerrar">
                <span class="material-symbols-outlined" style="font-size:17px;">close</span>
            </button>
            <div class="toast-bar" style="background:${barColor}"></div>
        `;

        // Borde izquierdo según tipo
        toast.style.borderLeftColor = border;

        contenedor.appendChild(toast);
        requestAnimationFrame(() => toast.classList.add('show'));

        const bar   = toast.querySelector('.toast-bar');
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