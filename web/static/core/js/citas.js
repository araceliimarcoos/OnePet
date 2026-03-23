// ===== MODAL =====
    const modal        = document.getElementById('modalNuevaCita');
    const btnAbrir     = document.getElementById('btnNuevaCita');
    const btnCerrar    = document.getElementById('cerrarModal');
    const btnCancelar  = document.getElementById('cancelarModal');

    btnAbrir.addEventListener('click',   () => modal.classList.add('open'));
    btnCerrar.addEventListener('click',  () => modal.classList.remove('open'));
    btnCancelar.addEventListener('click',() => modal.classList.remove('open'));
    modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('open'); });

    // ===== BÚSQUEDA =====
    document.getElementById('citasSearch').addEventListener('input', filtrar);
    document.getElementById('filterEstado').addEventListener('change', filtrar);
    document.getElementById('filterVet').addEventListener('change', filtrar);

    function filtrar() {
        const q      = document.getElementById('citasSearch').value.toLowerCase();
        const estado = document.getElementById('filterEstado').value;
        const vet    = document.getElementById('filterVet').value;

        document.querySelectorAll('#citasBody tr').forEach(row => {
            const texto      = row.textContent.toLowerCase();
            const rowEstado  = row.dataset.estado || '';
            const rowVet     = row.dataset.vet    || '';

            const okTexto  = texto.includes(q);
            const okEstado = !estado || rowEstado === estado;
            const okVet    = !vet    || rowVet === vet;

            row.style.display = (okTexto && okEstado && okVet) ? '' : 'none';
        });
    }