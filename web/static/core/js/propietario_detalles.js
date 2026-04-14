document.addEventListener('DOMContentLoaded', () => {

    // ── TOAST ─────────────────────────────────────────────────────────────────
    function mostrarToast(titulo, mensaje, tipo = 'ok', duracion = 4000) {
        const contenedor = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = 'toast';
        const icono = tipo === 'error' ? 'error' : 'check_circle';
        toast.innerHTML = `
            <div class="toast-icon">
                <span class="material-symbols-outlined">${icono}</span>
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
        toast.querySelector('.toast-bar').animate(
            [{ transform: 'scaleX(1)' }, { transform: 'scaleX(0)' }],
            { duration: duracion, easing: 'linear', fill: 'forwards' }
        );
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

    // ── UTILIDADES ────────────────────────────────────────────────────────────
    function abrirOverlay(el) {
        el.classList.add('visible');
        document.body.style.overflow = 'hidden';
    }
    function cerrarOverlay(el, form = null) {
        el.classList.remove('visible');
        document.body.style.overflow = '';
        if (form) form.reset();
    }
    function getCsrf() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }

    // ── MODAL: EDITAR PROPIETARIO ─────────────────────────────────────────────
    const overlayEditar = document.getElementById('modalEditarPropietario');
    const formEditar    = document.getElementById('formEditarPropietario');
    const errorEditar   = document.getElementById('editError');

    document.getElementById('btnEditarPerfil')?.addEventListener('click', () => {
        const btn = document.getElementById('btnEditarPerfil');
        document.getElementById('editFolio').value     = btn.dataset.folio;
        document.getElementById('editNombre').value    = btn.dataset.nombre;
        document.getElementById('editApellidoP').value = btn.dataset.ap;
        document.getElementById('editApellidoM').value = btn.dataset.am;
        document.getElementById('editCorreo').value    = btn.dataset.correo;
        document.getElementById('editCalle').value     = btn.dataset.calle;
        document.getElementById('editNum').value       = btn.dataset.num;
        document.getElementById('editColonia').value   = btn.dataset.colonia;
        document.getElementById('editTel').value       = btn.dataset.tel;
        document.getElementById('editTel2').value      = btn.dataset.tel2;
        errorEditar.style.display = 'none';
        abrirOverlay(overlayEditar);
    });

    function cerrarEditar() { cerrarOverlay(overlayEditar, formEditar); }
    document.getElementById('btnCerrarEditar')?.addEventListener('click', cerrarEditar);
    document.getElementById('btnCancelarEditar')?.addEventListener('click', cerrarEditar);
    overlayEditar?.addEventListener('click', e => { if (e.target === overlayEditar) cerrarEditar(); });

    formEditar?.addEventListener('submit', async e => {
        e.preventDefault();
        errorEditar.style.display = 'none';
        const folio  = document.getElementById('editFolio').value;
        const btn    = formEditar.querySelector('[type=submit]');
        const orig   = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span> Guardando...';

        try {
            const resp = await fetch(`/propietarios/${folio}/editar/`, {
                method: 'POST',
                body: new FormData(formEditar),
                headers: { 'X-CSRFToken': getCsrf() }
            });
            const data = await resp.json();
            if (data.ok) {
                cerrarEditar();
                mostrarToast('Perfil actualizado', 'Los datos del propietario fueron guardados.');
                setTimeout(() => location.reload(), 2500);
            } else {
                errorEditar.textContent   = data.error;
                errorEditar.style.display = 'block';
            }
        } catch {
            errorEditar.textContent   = 'Error de conexión.';
            errorEditar.style.display = 'block';
        } finally {
            btn.disabled  = false;
            btn.innerHTML = orig;
        }
    });

    // ── MODAL: NUEVA MASCOTA ──────────────────────────────────────────────────
    const overlayMascota = document.getElementById('modalNuevaMascota');
    const formMascota    = document.getElementById('formNuevaMascota');
    const errorMascota   = document.getElementById('mascError');

    async function cargarFolioMascota() {
        try {
            const r = await fetch('/mascotas/folio/');
            const d = await r.json();
            document.getElementById('folioMascotaAuto').value = d.folio;
        } catch {
            document.getElementById('folioMascotaAuto').value = '—';
        }
    }

    document.getElementById('btnNuevaMascota')?.addEventListener('click', () => {
        errorMascota.style.display = 'none';
        cargarFolioMascota();
        abrirOverlay(overlayMascota);
    });

    function cerrarMascota() { cerrarOverlay(overlayMascota, formMascota); }
    document.getElementById('btnCerrarMascota')?.addEventListener('click', cerrarMascota);
    document.getElementById('btnCancelarMascota')?.addEventListener('click', cerrarMascota);
    overlayMascota?.addEventListener('click', e => { if (e.target === overlayMascota) cerrarMascota(); });

    // Filtrar razas por especie
    document.getElementById('mascEspecie')?.addEventListener('change', async function () {
        const razaSelect = document.getElementById('mascRaza');
        razaSelect.innerHTML = '<option value="">Cargando...</option>';
        razaSelect.disabled  = true;

        if (!this.value) {
            razaSelect.innerHTML = '<option value="">— Selecciona una especie —</option>';
            return;
        }

        try {
            const r = await fetch(`/mascotas/obtener-razas/?especie_id=${this.value}`);
            const razas = await r.json();
            razaSelect.innerHTML = '<option value="">Seleccionar raza...</option>';
            razas.forEach(raza => {
                const opt = document.createElement('option');
                opt.value = raza.clave;
                opt.textContent = raza.nombre;
                razaSelect.appendChild(opt);
            });
            razaSelect.disabled = false;
        } catch {
            razaSelect.innerHTML = '<option value="">Error al cargar razas</option>';
        }
    });

    // Fecha máxima: hoy
    const hoy = new Date().toISOString().split('T')[0];
    document.getElementById('mascFecha') && (document.getElementById('mascFecha').max = hoy);

    formMascota?.addEventListener('submit', async e => {
        e.preventDefault();
        errorMascota.style.display = 'none';
        const btn  = document.getElementById('btnGuardarMascota');
        const orig = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span> Guardando...';

        try {
            const resp = await fetch('/mascotas/crear/', {
                method: 'POST',
                body: new FormData(formMascota),
                headers: { 'X-CSRFToken': getCsrf() }
            });
            const data = await resp.json();
            if (data.ok) {
                cerrarMascota();
                mostrarToast('Mascota registrada', `La mascota fue guardada correctamente.`);
                setTimeout(() => location.reload(), 2500);
            } else {
                errorMascota.textContent   = data.error;
                errorMascota.style.display = 'block';
            }
        } catch {
            errorMascota.textContent   = 'Error de conexión.';
            errorMascota.style.display = 'block';
        } finally {
            btn.disabled  = false;
            btn.innerHTML = orig;
        }
    });

    // ── ESCAPE ────────────────────────────────────────────────────────────────
    document.addEventListener('keydown', e => {
        if (e.key !== 'Escape') return;
        if (overlayEditar?.classList.contains('visible'))  cerrarEditar();
        if (overlayMascota?.classList.contains('visible')) cerrarMascota();
    });

});