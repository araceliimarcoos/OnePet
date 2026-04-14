// ==========================================
// TOAST
// ==========================================
function mostrarToast(titulo, mensaje = '', duracion = 4000, esError = false) {
    const contenedor = document.getElementById('toast-container');
    if (!contenedor) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        <div class="toast-icon" style="${esError ? 'background:#fff0f0;' : ''}">
            <span class="material-symbols-outlined" style="font-size:17px; color:${esError ? '#c0392b' : '#3B6D11'};">
                ${esError ? 'error' : 'check_circle'}
            </span>
        </div>
        <div>
            <p class="toast-title">${titulo}</p>
            ${mensaje ? `<p class="toast-msg">${mensaje}</p>` : ''}
        </div>
        <button class="toast-close" aria-label="Cerrar">
            <span class="material-symbols-outlined" style="font-size:17px;">close</span>
        </button>
        <div class="toast-bar" style="${esError ? 'background:#c0392b;' : ''}"></div>
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

// ==========================================
// MODAL
// ==========================================
document.addEventListener('DOMContentLoaded', () => {

    const overlay     = document.getElementById('modalNuevoPropietario');
    const btnAbrir    = document.getElementById('btnNuevoPropietario');
    const btnCerrar   = document.getElementById('btnCerrarModal');
    const btnCancelar = document.getElementById('btnCancelar');
    const form        = document.getElementById('formNuevoPropietario');
    const folioInput  = document.getElementById('folioAuto');

    async function cargarFolio() {
        try {
            const response = await fetch('/propietarios/folio/');
            const data     = await response.json();
            if (folioInput) folioInput.value = data.folio;
        } catch (error) {
            console.error('Error al obtener folio:', error);
        }
    }

    function cerrarModal() {
        overlay?.classList.remove('visible');
        document.body.style.overflow = '';
        form?.reset();
    }

    btnAbrir?.addEventListener('click', () => {
        overlay?.classList.add('visible');
        document.body.style.overflow = 'hidden';
        cargarFolio();
    });

    btnCerrar?.addEventListener('click', cerrarModal);
    btnCancelar?.addEventListener('click', cerrarModal);
    overlay?.addEventListener('click', e => { if (e.target === overlay) cerrarModal(); });
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && overlay?.classList.contains('visible')) cerrarModal();
    });

    // ── Enviar formulario ──
    form?.addEventListener('submit', async e => {
        e.preventDefault();

        const btnSubmit     = form.querySelector('[type=submit]');
        const textoOriginal = btnSubmit.innerHTML;
        btnSubmit.disabled  = true;
        btnSubmit.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span> Guardando...';

        const formData = new FormData(form);

        try {
            const response = await fetch('/propietarios/crear/', {
                method:  'POST',
                body:    formData,
                headers: { 'X-CSRFToken': formData.get('csrfmiddlewaretoken') }
            });

            const data = await response.json();

            if (data.ok) {
                cerrarModal();
                mostrarToast('Propietario registrado', data.message || `Folio: ${data.id}`);
                setTimeout(() => location.reload(), 2500);
            } else {
                mostrarToast('Error al guardar', data.error, 5000, true);
            }
        } catch (error) {
            console.error('Error al guardar:', error);
            mostrarToast('Error de conexión', 'No se pudo conectar con el servidor', 5000, true);
        } finally {
            btnSubmit.disabled  = false;
            btnSubmit.innerHTML = textoOriginal;
        }
    });

});