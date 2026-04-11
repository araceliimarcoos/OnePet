document.addEventListener('DOMContentLoaded', () => {

    // ── Modal iniciar consulta ───────────────────────────────────────────────
    const overlay      = document.getElementById('modalIniciarConsulta');
    const btnAbrir     = document.getElementById('btnIniciarConsulta');
    const btnCerrar    = document.getElementById('btnCerrarConsulta');
    const btnCancelar  = document.getElementById('btnCancelarConsulta');
    const btnConfirmar = document.getElementById('btnConfirmarConsulta');
    const selectCita   = document.getElementById('selectCita');
    const resumen      = document.getElementById('resumenCita');

    // Datos de las citas pendientes embebidos en el select — los leemos con fetch
    // para obtener el detalle completo al seleccionar.
    selectCita?.addEventListener('change', async () => {
        const folio = selectCita.value;

        if (!folio) {
            resumen.style.display = 'none';
            btnConfirmar.disabled = true;
            return;
        }

        // Buscar detalles de la cita seleccionada
        try {
            const resp  = await fetch(`/citas/buscar/?q=${encodeURIComponent(folio)}`);
            const citas = await resp.json();
            const cita  = citas.find(c => c.folio === folio);

            if (cita) {
                document.getElementById('r-folio').textContent      = cita.folio;
                document.getElementById('r-fecha').textContent      = `${cita.fecha} ${cita.hora}`;
                document.getElementById('r-mascota').textContent    = cita.mascota;
                document.getElementById('r-propietario').textContent = cita.propietario;
                document.getElementById('r-motivo').textContent     = cita.motivo;
                resumen.style.display = 'block';
                btnConfirmar.disabled = false;
            }
        } catch {
            resumen.style.display = 'none';
        }
    });

    function abrirModal() {
        overlay.classList.add('visible');
        document.body.style.overflow = 'hidden';
    }

    function cerrarModal() {
        overlay.classList.remove('visible');
        document.body.style.overflow = '';
        selectCita.value = '';
        resumen.style.display = 'none';
        btnConfirmar.disabled = true;
    }

    btnAbrir?.addEventListener('click', abrirModal);
    btnCerrar?.addEventListener('click', cerrarModal);
    btnCancelar?.addEventListener('click', cerrarModal);
    overlay?.addEventListener('click', (e) => { if (e.target === overlay) cerrarModal(); });

    // Al confirmar → navega al template de iniciar consulta con el folio
    btnConfirmar?.addEventListener('click', () => {
        const folio = selectCita.value;
        if (folio) window.location.href = `/consultas/${folio}/iniciar/`;
    });

    // ── Escape ───────────────────────────────────────────────────────────────
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && overlay?.classList.contains('visible')) cerrarModal();
    });

    // ── Búsqueda en tabla ────────────────────────────────────────────────────
    document.getElementById('consultasSearch')?.addEventListener('input', function() {
        const q = this.value.toLowerCase();
        document.querySelectorAll('#consultasBody tr').forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    });

    // ── Menú de acciones ─────────────────────────────────────────────────────
    function cerrarDropdowns() {
        document.querySelectorAll('.dropdown-menu.open').forEach(d => {
            d.classList.remove('open');
            d.removeAttribute('style');
        });
    }

    function abrirDropdown(btn, menu) {
        const rect       = btn.getBoundingClientRect();
        const spaceBelow = window.innerHeight - rect.bottom;
        const abreArriba = spaceBelow < 120;
        menu.classList.add('open');
        menu.style.position = 'fixed';
        menu.style.left = `${rect.right - (menu.offsetWidth || 170)}px`;
        menu.style.top  = abreArriba
            ? `${rect.top - menu.offsetHeight - 4}px`
            : `${rect.bottom + 4}px`;
        menu.style.zIndex = '9999';
    }

    document.addEventListener('click', (e) => {
        const menuBtn = e.target.closest('.menu-btn');
        if (menuBtn) {
            const menu   = menuBtn.nextElementSibling;
            const isOpen = menu.classList.contains('open');
            cerrarDropdowns();
            if (!isOpen) abrirDropdown(menuBtn, menu);
            return;
        }
        cerrarDropdowns();
    });

    document.addEventListener('scroll', cerrarDropdowns, true);
});