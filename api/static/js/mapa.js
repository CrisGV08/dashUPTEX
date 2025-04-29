// Espera a que el DOM cargue completamente
document.addEventListener('DOMContentLoaded', function () {
    // Crear el mapa centrado en el Estado de México
    var map = L.map('map').setView([19.35, -99.75], 8); // Coordenadas aproximadas del Estado de México

    // Añadir el mapa base desde OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Prueba de marcador (para verificar que el mapa está funcionando)
    L.marker([19.35, -99.75]).addTo(map)
        .bindPopup('Estado de México')
        .openPopup();
});
