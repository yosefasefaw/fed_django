/**
 * Topic Detail Page Interactivity
 * Handles collapsible stance sections
 */

function toggleSection(button) {
    const section = button.closest('.collapsible-section');
    section.classList.toggle('collapsed');
}

// Initialize all sections as expanded
document.addEventListener('DOMContentLoaded', function () {
    // Sections start expanded by default (no 'collapsed' class)
    // User can click to collapse them
});
