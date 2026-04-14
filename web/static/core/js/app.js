/* =====================================================
   OnePet – app.js
   Maneja: sidebar collapse, mobile, roles del sidebar
   ===================================================== */

(function () {
  'use strict';

  const sidebar     = document.getElementById('sidebar');
  const mainWrapper = document.getElementById('mainWrapper');
  const collapseBtn = document.getElementById('collapseBtn');
  const hamburger   = document.getElementById('hamburger');
  const overlay     = document.getElementById('overlay');

  /* ─────────────────────────────────────────────────────
     ROLES: ocultar items del sidebar según el rol
     El rol viene del atributo data-rol en el <body>.
     En Django: <body data-rol="{{ request.user.rol }}">

     Permisos por módulo:
       dashboard       → admin, veterinario, recepcionista
       propietarios    → admin, recepcionista
       mascotas        → admin, veterinario, recepcionista
       citas           → admin, veterinario, recepcionista
       consultas       → admin, veterinario
       hospitalizacion → admin, veterinario
       pagos           → admin, recepcionista
       catalogo        → admin, recepcionista
       medicamentos    → admin, veterinario
       usuarios        → admin
       especies        → admin
       reportes        → admin
  ───────────────────────────────────────────────────── */
  function aplicarPermisosSidebar() {
    const rol = document.body.dataset.rol || 'rec';
    const items = document.querySelectorAll('.nav-item[data-roles]');

    items.forEach(item => {
      const rolesPermitidos = item.dataset.roles
        .split(',')
        .map(r => r.trim());

      if (!rolesPermitidos.includes(rol)) {
        item.remove(); 
      }
    });
  }

  aplicarPermisosSidebar();


  /* ─────────────────────────────────────────────────────
     SIDEBAR COLLAPSE (desktop)
  ───────────────────────────────────────────────────── */
  let isCollapsed = false;

  function toggleCollapse() {
    isCollapsed = !isCollapsed;
    sidebar.classList.toggle('collapsed', isCollapsed);
    mainWrapper.classList.toggle('collapsed', isCollapsed);
    localStorage.setItem('sidebarCollapsed', isCollapsed);
  }

  if (collapseBtn) collapseBtn.addEventListener('click', toggleCollapse);

  // Restaurar estado guardado
  const savedState = localStorage.getItem('sidebarCollapsed');
  if (savedState === 'true') {
    isCollapsed = true;
    sidebar.classList.add('collapsed');
    mainWrapper.classList.add('collapsed');
  }


  /* ─────────────────────────────────────────────────────
     SIDEBAR MOBILE (hamburger + overlay)
  ───────────────────────────────────────────────────── */
  function openMobile() {
    sidebar.classList.add('mobile-open');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeMobile() {
    sidebar.classList.remove('mobile-open');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (hamburger) hamburger.addEventListener('click', openMobile);
  if (overlay)   overlay.addEventListener('click', closeMobile);

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeMobile();
  });

  // Cerrar al navegar en móvil
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      if (window.innerWidth <= 900) closeMobile();
    });
  });


  /* ─────────────────────────────────────────────────────
     RESIZE
  ───────────────────────────────────────────────────── */
  let lastWidth = window.innerWidth;

  window.addEventListener('resize', () => {
    const w = window.innerWidth;
    if (w > 900 && lastWidth <= 900) closeMobile();
    lastWidth = w;
  });

})();
