document.addEventListener('DOMContentLoaded', () => {
 
    // ── Modal iniciar hospitalización ────────────────────────────────────────
    const overlay   = document.getElementById('modalIniciarHosp');
    const selectC   = document.getElementById('selectConsulta');
    const resumen   = document.getElementById('resumenHosp');
    const btnConf   = document.getElementById('btnConfirmarHosp');
 
    document.getElementById('btnIniciarHosp')?.addEventListener('click', () => {
        overlay.classList.add('visible'); document.body.style.overflow = 'hidden';
    });
 
    function cerrar() {
        overlay.classList.remove('visible'); document.body.style.overflow = '';
        selectC.value = ''; resumen.style.display = 'none'; btnConf.disabled = true;
    }
 
    document.getElementById('btnCerrarHosp')?.addEventListener('click', cerrar);
    document.getElementById('btnCancelarHosp')?.addEventListener('click', cerrar);
    overlay?.addEventListener('click', (e) => { if (e.target === overlay) cerrar(); });
 
    selectC?.addEventListener('change', () => {
        const opt = selectC.selectedOptions[0];
        if (!opt?.value) { resumen.style.display = 'none'; btnConf.disabled = true; return; }
        document.getElementById('h-mascota').textContent    = opt.dataset.mascota;
        document.getElementById('h-fecha').textContent      = opt.dataset.fecha;
        document.getElementById('h-propietario').textContent = opt.dataset.propietario;
        document.getElementById('h-motivo').textContent     = opt.dataset.motivo;
        resumen.style.display = 'block';
        btnConf.disabled = false;
    });
 
    btnConf?.addEventListener('click', () => {
        const num = selectC.value;
        if (num) window.location.href = `/hospitalizacion/${num}/iniciar/`;
    });
 
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && overlay?.classList.contains('visible')) cerrar();
    });
 
    // ── Filtros de tabla ─────────────────────────────────────────────────────
    document.getElementById('hospSearch')?.addEventListener('input', function() {
        const q = this.value.toLowerCase();
        filtrar(q, document.getElementById('filterEstadoHosp').value);
    });
 
    document.getElementById('filterEstadoHosp')?.addEventListener('change', function() {
        filtrar(document.getElementById('hospSearch').value.toLowerCase(), this.value);
    });
 
    function filtrar(q, estado) {
        document.querySelectorAll('#hospBody tr').forEach(row => {
            const texto  = row.textContent.toLowerCase();
            const rowEdo = row.dataset.estado || '';
            const okQ    = !q      || texto.includes(q);
            const okEdo  = !estado || rowEdo === estado;
            row.style.display = (okQ && okEdo) ? '' : 'none';
        });
    }
 
    // ── Menú de acciones ─────────────────────────────────────────────────────
    function cerrarDropdowns() {
        document.querySelectorAll('.dropdown-menu.open').forEach(d => {
            d.classList.remove('open'); d.removeAttribute('style');
        });
    }
 
    function abrirDropdown(btn, menu) {
        const rect = btn.getBoundingClientRect();
        const spaceBelow = window.innerHeight - rect.bottom;
        menu.classList.add('open');
        menu.style.position = 'fixed';
        menu.style.zIndex   = '9999';
        menu.style.left     = `${rect.right - (menu.offsetWidth || 160)}px`;
        menu.style.top      = spaceBelow < 120
            ? `${rect.top - menu.offsetHeight - 4}px`
            : `${rect.bottom + 4}px`;
    }
 
    document.addEventListener('click', (e) => {
        const menuBtn = e.target.closest('.menu-btn');
        if (menuBtn) {
            const menu = menuBtn.nextElementSibling;
            const isOpen = menu.classList.contains('open');
            cerrarDropdowns();
            if (!isOpen) abrirDropdown(menuBtn, menu);
            return;
        }
        cerrarDropdowns();
    });
 
    document.addEventListener('scroll', cerrarDropdowns, true);
});