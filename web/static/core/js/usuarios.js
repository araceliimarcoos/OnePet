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

            if (coincideEstado && coincideRol) {
                fila.style.display = '';
            } else {
                fila.style.display = 'none';
            }
        });
    }

    // Eventos
    if (filtroEstado) {
        filtroEstado.addEventListener('change', aplicarFiltros);
    }

    if (filtroRol) {
        filtroRol.addEventListener('change', aplicarFiltros);
    }

    // Aplicar al cargar
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
        if (overlayNuevo?.classList.contains('visible'))    cerrarOverlay(overlayNuevo, formNuevo);
        if (overlayDetalles?.classList.contains('visible')) cerrarOverlay(overlayDetalles);
        if (overlayEditar?.classList.contains('visible'))   cerrarOverlay(overlayEditar, formEditar);
        if (overlayBaja?.classList.contains('visible'))     cerrarOverlay(overlayBaja);
        if (overlayEsp?.classList.contains('visible'))      cerrarOverlay(overlayEsp, formEsp);
    });

    document.addEventListener('scroll', cerrarDropdowns, true);


    // ─── MODAL: VER DETALLES ──────────────────────────────────────────────────

    const overlayDetalles = document.getElementById('modalVerDetalles');

    function abrirDetalles(d) {
        console.log(d);
        const nombre = d.nombre || '';
        // Iniciales para el avatar: primera letra de nombre y primer apellido
        const partes   = nombre.trim().split(' ');
        const iniciales = partes.length >= 2
            ? (partes[0][0] + partes[1][0]).toUpperCase()
            : nombre.slice(0, 2).toUpperCase();

        const avatar = document.getElementById('det-avatar');
        if (avatar) avatar.textContent = iniciales || '—';

        document.getElementById('det-nombre-real').textContent = d.nombre || '—';
        document.getElementById('det-estado').textContent = d.estado      || '—';
        document.getElementById('det-rol').textContent = d.rol            || '—';
        document.getElementById('det-contrasena').textContent = '********'|| '—';

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
        const overlay = document.getElementById('modalEditarUsuario');

        document.getElementById('editar_usuario_mostrar').value = d.usuario || '';
        document.getElementById('editar_usuario_nombre').value = d.nombre || '';
        document.getElementById('editar-usuario-id').value = d.usuario || '';
        document.getElementById('editar_contrasena').value = '';

        abrirOverlay(overlay);
    }

    // cerrar modal
    document.getElementById('btnCerrarEditar')
        ?.addEventListener('click', () => cerrarOverlay(overlayEditar, formEditar));

    document.getElementById('btnCancelarEditar')
        ?.addEventListener('click', () => cerrarOverlay(overlayEditar, formEditar));

    overlayEditar?.addEventListener('click', (e) => {
        if (e.target === overlayEditar) {
            cerrarOverlay(overlayEditar, formEditar);
        }
    });


    // ─── SUBMIT EDITAR CONTRASEÑA ────────────────────────────────────────────

    formEditar?.addEventListener('submit', async (e) => {
        e.preventDefault();

        limpiarError(overlayEditar);

        const usuario       = document.getElementById('editar-usuario-id').value;
        const btnGuardar    = formEditar.querySelector('[type=submit]');
        const textoOriginal = btnGuardar.innerHTML;

        btnGuardar.disabled = true;
        btnGuardar.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span> Guardando...';

        try {
            const resp = await fetch(`/usuarios/${usuario}/cambiar-password/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken()
                },
                body: new FormData(formEditar)
            });

            const data = await resp.json();

            if (data.ok) {
                cerrarOverlay(overlayEditar, formEditar);
                mostrarToast('Contraseña actualizada', `Usuario ${usuario}`);
                setTimeout(() => window.location.reload(), 2000);
            } else {
                mostrarError(overlayEditar, data.error || 'Error al guardar');
            }

        } catch (err) {
            mostrarError(overlayEditar, 'No se pudo conectar con el servidor');
        } finally {
            btnGuardar.disabled  = false;
            btnGuardar.innerHTML = textoOriginal;
        }
    });




    function leerDatosEditar(btn) {
        return {
            usuario: btn.getAttribute('data-usuario')
        };
    }

    const inputPass = document.getElementById('editar_contrasena');
    const toggleBtn = document.getElementById('togglePassword');

    toggleBtn.addEventListener('click', () => {
        const isHidden = inputPass.type === 'password';
        inputPass.type = isHidden ? 'text' : 'password';
        toggleBtn.textContent = isHidden ? 'NO VER' : 'VER';
    });


    // ─── MODAL: CONFIRMAR BAJA ────────────────────────────────────────────────

    const overlayBaja = document.getElementById('modalConfirmarBaja');
    let usuarioParaBaja = null;

    function abrirBaja(d) {
        usuarioParaBaja = d.usuario;  // ✔ correcto

        document.getElementById('baja-usuario').textContent =
            d.nombre || d.usuario || 'este usuario';

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

        console.log("CLICK BAJA FUNCIONA");

        if (!usuarioParaBaja) return;

        const btn = document.getElementById('btnConfirmarBaja');

        try {
            const resp = await fetch(`/usuarios/${usuarioParaBaja}/baja/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            });

            const data = await resp.json();

            if (data.ok) {
                cerrarOverlay(overlayBaja);
                mostrarToast('Usuario dado de baja', d.nombre || usuarioParaBaja);
                setTimeout(() => location.reload(), 1500);
            } else {
                mostrarToast('Error', data.error);
            }

        } catch (e) {
            console.error(e);
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


});

    