const overlay       = document.getElementById('modalIniciarConsulta');
const btnAbrir      = document.getElementById('btnIniciarConsulta');
const btnCerrar     = document.getElementById('btnCerrarConsulta');
const btnCancelar   = document.getElementById('btnCancelarConsulta');

if (btnAbrir) {
    btnAbrir.addEventListener('click', () => {
        overlay.classList.add('visible');
        document.body.style.overflow = 'hidden';
    });
}

function cerrarModal() {
    overlay.classList.remove('visible');
    document.body.style.overflow = '';
    inputCita.value = '';
    cerrarDropdown();
}

if (btnCerrar) btnCerrar.addEventListener('click', cerrarModal);
if (btnCancelar) btnCancelar.addEventListener('click', cerrarModal);

overlay?.addEventListener('click', (e) => {
    if (e.target === overlay) cerrarModal();
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('visible')) cerrarModal();
});


// Autocomplete ────────────────────────────────────────────────
const inputCita    = document.getElementById('inputCita');
const dropdown     = document.getElementById('citaDropdown');
const resumen      = document.getElementById('resumenCita');
const btnConfirmar = document.getElementById('btnConfirmarConsulta');

let timeoutId = null;  // para el debounce

// ── Escucha lo que escribe el usuario ──────────────────────────
inputCita.addEventListener('input', () => {
    const query = inputCita.value.trim();

    // Limpiar si borra todo
    if (query.length < 2) {
        cerrarDropdown();
        ocultarResumen();
        return;
    }

    // Debounce: espera 300ms antes de consultar
    // (evita llamar al servidor en cada letra)
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => buscarCitas(query), 100);
});

// ── Consulta al servidor ───────────────────────────────────────
async function buscarCitas(query) {
    // Mostrar loader inmediatamente
    dropdown.innerHTML = '<div class="autocomplete-item no-results">Buscando...</div>';
    dropdown.classList.add('open');

    try {
        const resp = await fetch(`/citas/buscar/?q=${encodeURIComponent(query)}`);
        const citas = await resp.json();
        mostrarSugerencias(citas);
    } catch (err) {
        dropdown.innerHTML = '<div class="autocomplete-item no-results">Error al buscar</div>';
        console.error('Error buscando citas:', err);
    }
}

// ── Renderiza las sugerencias ──────────────────────────────────
function mostrarSugerencias(citas) {
    dropdown.innerHTML = '';

    if (citas.length === 0) {
        dropdown.innerHTML = '<div class="autocomplete-item no-results">Sin resultados</div>';
        dropdown.classList.add('open');
        return;
    }

    citas.forEach(cita => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.innerHTML = `
            <div class="autocomplete-folio">${cita.folio}</div>
            <div class="autocomplete-info">
                <span>${cita.mascota}</span> · 
                <span>${cita.fecha} ${cita.hora}</span> · 
                <span>${cita.veterinario}</span>
            </div>
        `;

        // Al hacer click en una sugerencia
        item.addEventListener('click', () => seleccionarCita(cita));
        dropdown.appendChild(item);
    });

    dropdown.classList.add('open');
}

// ── Cuando selecciona una cita ─────────────────────────────────
function seleccionarCita(cita) {
    // Poner el folio en el input
    inputCita.value = cita.folio;

    // Llenar el resumen
    document.getElementById('r-folio').textContent       = cita.folio;
    document.getElementById('r-fecha').textContent       = `${cita.fecha} — ${cita.hora}`;
    document.getElementById('r-mascota').textContent     = cita.mascota;
    document.getElementById('r-propietario').textContent = cita.propietario;
    document.getElementById('r-veterinario').textContent = cita.veterinario;
    document.getElementById('r-motivo').textContent      = cita.motivo;
    document.getElementById('r-estado').textContent      = cita.estado;

    // Mostrar resumen y habilitar botón
    resumen.style.display = 'block';
    btnConfirmar.disabled = false;

    cerrarDropdown();
}

// ── Cerrar dropdown al hacer click fuera ──────────────────────
document.addEventListener('click', (e) => {
    if (!e.target.closest('.autocomplete-wrapper')) {
        cerrarDropdown();
    }
});

function cerrarDropdown() {
    dropdown.innerHTML = '';
    dropdown.classList.remove('open');
}

function ocultarResumen() {
    resumen.style.display = 'none';
    btnConfirmar.disabled = true;
}


// ===== BÚSQUEDA =====
