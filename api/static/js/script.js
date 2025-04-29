document.addEventListener("DOMContentLoaded", function () {
    // ✅ Mostrar solo los submenús al hacer clic en el menú principal
    let menuItems = document.querySelectorAll(".menu-item > a");
    let submenuItems = document.querySelectorAll(".submenu-item > a");

    // ✅ Leer el estado guardado en localStorage
    const activeMenu = localStorage.getItem("activeMenu");
    const activeSubmenu = localStorage.getItem("activeSubmenu");

    // ✅ Mantener abiertos el menú y submenú activos
    if (activeMenu) {
        const menu = document.querySelector(`[data-menu="${activeMenu}"]`);
        if (menu && menu.nextElementSibling) {
            menu.classList.add("active");
            menu.nextElementSibling.style.display = "block";
        }
    }

    if (activeSubmenu) {
        const submenu = document.querySelector(`[data-submenu="${activeSubmenu}"]`);
        if (submenu && submenu.nextElementSibling) {
            submenu.classList.add("active");
            submenu.nextElementSibling.style.display = "block";
        }
    }

    // ✅ Mostrar solo el submenú seleccionado
    menuItems.forEach((item) => {
        item.addEventListener("click", function (e) {
            let submenu = this.nextElementSibling;

            // Si no hay submenu, no se hace toggle, y se permite la redirección
            if (!submenu || !submenu.classList.contains("submenu")) {
                return;
            }

            e.preventDefault(); // solo si hay submenú se previene la redirección

            // 🔒 Ocultar otros submenús
            document.querySelectorAll(".submenu").forEach((menu) => {
                if (menu !== submenu) {
                    menu.style.display = "none";
                }
            });

            // ✅ Mostrar solo el submenú seleccionado
            submenu.style.display = submenu.style.display === "block" ? "none" : "block";

            // ✅ Guardar el estado en localStorage
            if (submenu.style.display === "block") {
                localStorage.setItem("activeMenu", this.getAttribute("data-menu"));
            } else {
                localStorage.removeItem("activeMenu");
            }
        });
    });

    // ✅ Mostrar solo el sub-submenú seleccionado
    submenuItems.forEach((item) => {
        item.addEventListener("click", function (e) {
            let subsubmenu = this.nextElementSibling;

            if (!subsubmenu || !subsubmenu.classList.contains("sub-submenu")) {
                return;
            }

            e.preventDefault();

            let parentSubmenu = this.closest(".submenu");
            if (parentSubmenu) {
                parentSubmenu.querySelectorAll(".sub-submenu").forEach((submenu) => {
                    if (submenu !== subsubmenu) {
                        submenu.style.display = "none";
                    }
                });
            }

            subsubmenu.style.display = subsubmenu.style.display === "block" ? "none" : "block";

            if (subsubmenu.style.display === "block") {
                localStorage.setItem("activeSubmenu", this.getAttribute("data-submenu"));
            } else {
                localStorage.removeItem("activeSubmenu");
            }
        });
    });
});
