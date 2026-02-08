document.addEventListener('DOMContentLoaded', function() {
    const themeSelect = document.getElementById('theme-select');
    themeSelect.addEventListener('change', function() {
        // Reload page with new theme parameter
        const url = new URL(window.location);
        url.searchParams.set('theme', this.value);
        window.location.href = url.toString();
    });
});