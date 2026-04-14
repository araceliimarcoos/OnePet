// ==========================================
// 0. ELEMENTOS DOM
// ==========================================
const overlay     = document.getElementById('modalNuevaMascota');
const btnAbrir    = document.getElementById('btnNuevaMascota');
const btnCerrar   = document.getElementById('btnCerrarModal');
const btnCancelar = document.getElementById('btnCancelar');
const form        = document.getElementById('formNuevaMascota'); // ID vital para el submit

const folioInput  = document.getElementById('folioAuto');

// Búsqueda de propietario dentro del modal
const inputFolio   = document.getElementById('folio_propietario');
const inputNombre  = document.getElementById('nombre_propietario');
const inputHidden  = document.getElementById('propietario_id');

// Filtros de la tabla
const inputBusqueda = document.getElementById('mascotaSearch');
const selEspecie    = document.getElementById('filterEspecie');
const selRaza       = document.getElementById('filterRaza');
const selEstado     = document.getElementById('filterEstado');

// ==========================================
// 1. MODAL Y CONTROL DE FOLIO
// ==========================================

// Buscar propietario por folio al perder el foco (blur)
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
            alert('Propietario no encontrado');
        }
    } catch (error) {
        console.error('Error al buscar propietario:', error);
    }
});

// Cargar folio automático
async function cargarFolio() {
    try {
        const response = await fetch('/mascotas/folio/');
        const data = await response.json();
        if (folioInput) folioInput.value = data.folio;
    } catch (error) {
        console.error('Error folio:', error);
    }
}

// Abrir modal
btnAbrir?.addEventListener('click', () => {
    overlay?.classList.add('visible');
    document.body.style.overflow = 'hidden';
    cargarFolio();
});

// Cerrar modal
function cerrarModal() {
    overlay?.classList.remove('visible');
    form?.reset();
    document.body.style.overflow = '';
    if (inputNombre) inputNombre.value = '';
}

btnCerrar?.addEventListener('click', cerrarModal);
btnCancelar?.addEventListener('click', cerrarModal);

overlay?.addEventListener('click', (e) => {
    if (e.target === overlay) cerrarModal();
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay?.classList.contains('visible')) {
        cerrarModal();
    }
});

// ==========================================
// 2. ENVÍO DEL FORMULARIO (Mismo flujo que Propietarios)
// ==========================================
form?.addEventListener('submit', async (e) => {
    // ESTO EVITA LA PANTALLA BLANCA CON EL JSON
    e.preventDefault();

    const formData = new FormData(form);

    try {
        const response = await fetch('/mascotas/crear/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        });

        const data = await response.json();

        if (data.ok) {
            cerrarModal();
            // El alert pausa la ejecución, así el usuario lee el mensaje
            alert(data.message); 
            // Al dar OK, se recarga la página
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }

    } catch (error) {
        console.error('Error al guardar:', error);
        alert('Ocurrió un error crítico al intentar guardar.');
    }
});

// ==========================================
// 3. LÓGICA ESPECIE -> RAZA (Cascada AJAX)
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    const especieModal = document.getElementById('especieModal');
    const razaModal = document.getElementById('razaModal');

    if (!especieModal || !razaModal) return;

    especieModal.addEventListener('change', async function() {
        const especieClave = this.value; 
        razaModal.innerHTML = '<option value="">Seleccionar...</option>';

        if (!especieClave) {
            razaModal.innerHTML = '<option value="">-- Selecciona una especie primero --</option>';
            return;
        }

        razaModal.innerHTML = '<option value="">Cargando razas...</option>';

        try {
            const response = await fetch(`/mascotas/obtener-razas/?especie_id=${encodeURIComponent(especieClave)}`);
            const data = await response.json();

            razaModal.innerHTML = '<option value="">Seleccionar...</option>';

            if (data && data.length > 0) {
                const fragment = document.createDocumentFragment();
                data.forEach(raza => {
                    const option = document.createElement('option');
                    option.value = raza.clave || raza.id;
                    option.textContent = raza.nombre;
                    fragment.appendChild(option);
                });
                razaModal.appendChild(fragment);
            } else {
                razaModal.innerHTML = '<option value="">Sin razas registradas</option>';
            }
        } catch (error) {
            console.error("Error al cargar razas:", error);
        }
    });
});

// ==========================================
// 4. FILTROS DE LA TABLA PRINCIPAL
// ==========================================
function filtrarTabla() {
    const filas = document.querySelectorAll('#mascotasBody tr');
    const busqueda = inputBusqueda?.value.toLowerCase() || "";
    const espEleg  = selEspecie?.value || "";
    const razaEleg = selRaza?.value || "";
    const estEleg  = selEstado?.value?.toLowerCase() || "";

    filas.forEach(fila => {
        const texto = fila.innerText.toLowerCase();
        const fEsp  = fila.getAttribute('data-especie') || "";
        const fRaza = fila.getAttribute('data-raza') || "";
        const fEst = fila.getAttribute('data-estado') || "";

        const ok = texto.includes(busqueda) &&
                   (espEleg === "" || fEsp === espEleg) &&
                   (razaEleg === "" || fRaza === razaEleg) &&
                   (estEleg === "" || fEst === estEleg);

        fila.style.display = ok ? "" : "none";
    });
}

inputBusqueda?.addEventListener('input', filtrarTabla);
selEstado?.addEventListener('change', filtrarTabla);
selRaza?.addEventListener('change', filtrarTabla);
selEspecie?.addEventListener('change', function() {
    // Reset de razas en el filtro
    if (selRaza) selRaza.value = "";
    filtrarTabla();
});