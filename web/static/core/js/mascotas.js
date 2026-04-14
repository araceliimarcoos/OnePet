// ==========================================
// 0. ELEMENTOS DOM
// ==========================================
const overlay     = document.getElementById('modalNuevaMascota');
const btnAbrir    = document.getElementById('btnNuevaMascota');
const btnCerrar   = document.getElementById('btnCerrarModal');
const btnCancelar = document.getElementById('btnCancelar');
const form        = document.getElementById('formNuevaMascota');
const folioInput  = document.getElementById('folioAuto');

const inputFolio  = document.getElementById('folio_propietario');
const inputNombre = document.getElementById('nombre_propietario');
const inputHidden = document.getElementById('propietario_id');

const inputBusqueda = document.getElementById('mascotaSearch');
const selEspecie    = document.getElementById('filterEspecie');
const selRaza       = document.getElementById('filterRaza');
const selEstado     = document.getElementById('filterEstado');

// ==========================================
// 1. TOAST
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
// 2. MODAL Y CONTROL DE FOLIO
// ==========================================
inputFolio?.addEventListener('blur', async () => {
    const folio = inputFolio.value.trim();
    if (!folio) return;

    try {
        const response = await fetch(`/buscar-propietario/?folio=${encodeURIComponent(folio)}`);
        const data = await response.json();

        if (data.ok) {
            inputNombre.value = data.nombre;
            inputHidden.value = data.folio;
        } else {
            inputNombre.value = '';
            inputHidden.value = '';
            mostrarToast('Propietario no encontrado', `No existe el folio "${folio}"`, 4000, true);
        }
    } catch (error) {
        console.error('Error al buscar propietario:', error);
        mostrarToast('Error de conexión', 'No se pudo verificar el propietario', 4000, true);
    }
});

async function cargarFolio() {
    try {
        const response = await fetch('/mascotas/folio/');
        const data = await response.json();
        if (folioInput) folioInput.value = data.folio;
    } catch (error) {
        console.error('Error folio:', error);
    }
}

btnAbrir?.addEventListener('click', () => {
    overlay?.classList.add('visible');
    document.body.style.overflow = 'hidden';
    cargarFolio();
});

function cerrarModal() {
    overlay?.classList.remove('visible');
    form?.reset();
    document.body.style.overflow = '';
    if (inputNombre) inputNombre.value = '';
}

btnCerrar?.addEventListener('click', cerrarModal);
btnCancelar?.addEventListener('click', cerrarModal);
overlay?.addEventListener('click', (e) => { if (e.target === overlay) cerrarModal(); });
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay?.classList.contains('visible')) cerrarModal();
});

// ==========================================
// 3. ENVÍO DEL FORMULARIO
// ==========================================
form?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const btnSubmit     = form.querySelector('[type=submit]');
    const textoOriginal = btnSubmit.innerHTML;
    btnSubmit.disabled  = true;
    btnSubmit.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span> Guardando...';

    const formData = new FormData(form);

    try {
        const response = await fetch('/mascotas/crear/', {
            method:  'POST',
            body:    formData,
            headers: { 'X-CSRFToken': formData.get('csrfmiddlewaretoken') }
        });

        const data = await response.json();

        if (data.ok) {
            cerrarModal();
            mostrarToast('Mascota registrada', data.message || `${data.nombre} — ${data.folio}`);
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

// ==========================================
// 4. ESPECIE → RAZA (cascada AJAX)
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    const especieModal = document.getElementById('especieModal');
    const razaModal    = document.getElementById('razaModal');

    if (!especieModal || !razaModal) return;

    especieModal.addEventListener('change', async function () {
        const especieClave = this.value;
        razaModal.innerHTML = '<option value="">Seleccionar...</option>';

        if (!especieClave) {
            razaModal.innerHTML = '<option value="">-- Selecciona una especie primero --</option>';
            return;
        }

        razaModal.innerHTML = '<option value="">Cargando razas...</option>';

        try {
            const response = await fetch(`/mascotas/obtener-razas/?especie_id=${encodeURIComponent(especieClave)}`);
            const data     = await response.json();

            razaModal.innerHTML = '<option value="">Seleccionar...</option>';

            if (data && data.length > 0) {
                const fragment = document.createDocumentFragment();
                data.forEach(raza => {
                    const option      = document.createElement('option');
                    option.value      = raza.clave || raza.id;
                    option.textContent = raza.nombre;
                    fragment.appendChild(option);
                });
                razaModal.appendChild(fragment);
            } else {
                razaModal.innerHTML = '<option value="">Sin razas registradas</option>';
            }
        } catch (error) {
            console.error('Error al cargar razas:', error);
            razaModal.innerHTML = '<option value="">Error al cargar</option>';
        }
    });
});

// ==========================================
// 5. FILTROS DE LA TABLA
// ==========================================
function filtrarTabla() {
    const filas    = document.querySelectorAll('#mascotasBody tr');
    const busqueda = inputBusqueda?.value.toLowerCase() || '';
    const espEleg  = selEspecie?.value || '';
    const razaEleg = selRaza?.value    || '';
    const estEleg  = selEstado?.value?.toLowerCase() || '';

    filas.forEach(fila => {
        const texto = fila.innerText.toLowerCase();
        const fEsp  = fila.getAttribute('data-especie') || "";
        const fRaza = fila.getAttribute('data-raza') || "";
        const fEst = fila.getAttribute('data-estado') || "";

        const ok = texto.includes(busqueda) &&
                   (espEleg  === '' || fEsp  === espEleg) &&
                   (razaEleg === '' || fRaza === razaEleg) &&
                   (estEleg  === '' || fEst  === estEleg);

        fila.style.display = ok ? '' : 'none';
    });
}

inputBusqueda?.addEventListener('input', filtrarTabla);
selEstado?.addEventListener('change', filtrarTabla);
selRaza?.addEventListener('change', filtrarTabla);
selEspecie?.addEventListener('change', () => {
    if (selRaza) selRaza.value = '';
    filtrarTabla();
});