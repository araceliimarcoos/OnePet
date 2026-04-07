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

    // ─── BÚSQUEDA EN TABLA ────────────────────────────────────────────────────

    document.getElementById('razaSearch')?.addEventListener('input', function () {
        const q = this.value.toLowerCase();
        document.querySelectorAll('#razasBody tr').forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    });

    // ─── MODAL: NUEVA RAZA ────────────────────────────────────────────────────

    const overlayRaza = document.getElementById('modalNuevaRaza');
    const formRaza    = document.getElementById('formNuevaRaza');

    document.getElementById('btnNuevaRaza')
        ?.addEventListener('click', () => abrirOverlay(overlayRaza));
    document.getElementById('btnCerrarModalRaza')
        ?.addEventListener('click', () => cerrarOverlay(overlayRaza, formRaza));
    document.getElementById('btnCancelarRaza')
        ?.addEventListener('click', () => cerrarOverlay(overlayRaza, formRaza));
    overlayRaza?.addEventListener('click', (e) => {
        if (e.target === overlayRaza) cerrarOverlay(overlayRaza, formRaza);
    });

    formRaza?.addEventListener('submit', async (e) => {
        e.preventDefault();
        limpiarError(overlayRaza);

        const btnGuardar    = formRaza.querySelector('[type=submit]');
        const textoOriginal = btnGuardar.innerHTML;
        btnGuardar.disabled = true;
        btnGuardar.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span> Guardando...';

        // La URL incluye la clave de especie que está en el input hidden
        const clave_especie = formRaza.querySelector('[name=especie]').value;

        try {
            const resp = await fetch('/especies/razas/nueva/', {
                method:  'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
                body:    new FormData(formRaza),
            });

            const data = await resp.json();

            if (data.ok) {
                cerrarOverlay(overlayRaza, formRaza);
                mostrarToast('Raza agregada', `${data.nombre} — ${data.clave}`);
                setTimeout(() => window.location.reload(), 2500);
            } else {
                mostrarError(overlayRaza, data.error || 'Ocurrió un error al guardar');
            }

        } catch {
            mostrarError(overlayRaza, 'No se pudo conectar con el servidor');
        } finally {
            btnGuardar.disabled  = false;
            btnGuardar.innerHTML = textoOriginal;
        }
    });

    // ─── ESCAPE ───────────────────────────────────────────────────────────────

    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        if (overlayRaza?.classList.contains('visible')) cerrarOverlay(overlayRaza, formRaza);
    });

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