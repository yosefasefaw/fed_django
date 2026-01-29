/**
 * Report Box Page - Clickable Table Rows
 * Handles navigation when clicking on report rows
 */

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.clickable-row').forEach(row => {
        row.addEventListener('click', function () {
            const href = this.dataset.href;
            if (href && href !== '#') {
                window.location.href = href;
            }
        });
    });
});
