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

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }

    // ─── BÚSQUEDA EN TABLA ────────────────────────────────────────────────────
 
    document.getElementById('especieSearch')?.addEventListener('input', function () {
        const q = this.value.toLowerCase();
        document.querySelectorAll('#especiesBody tr').forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    });

    // Modal de Nuevo Especie ──────────────────────────────────────────────────
    const overlayNuevo = document.getElementById('modalNuevaEspecie');
    const formNuevo    = document.getElementById('formNuevaEspecie');

    document.getElementById('btnNuevaEspecie')
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

        const btnGuardar = formNuevo.querySelector('[type=submit]');
        const textoOriginal  = btnGuardar.innerHTML;
        btnGuardar.disabled  = true;
        btnGuardar.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span> Guardando...';

        try {
            const resp = await fetch('/especies/nueva/', {
                method:  'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
                body:    new FormData(formNuevo),
            });

            const data = await resp.json();

            if (data.ok) {
                cerrarOverlay(overlayNuevo, formNuevo);
                mostrarToast('Especie agregada', `${data.nombre} — ${data.clave}`);
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

    // ─── ESCAPE ────────────────────────────────────────────────────

    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        if (overlayNuevo?.classList.contains('visible')) cerrarOverlay(overlayNuevo, formNuevo);
    });

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