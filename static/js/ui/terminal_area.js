// ui/terminal_area.js
// UI logic for the terminal area component.

document.addEventListener('DOMContentLoaded', () => {
    const maximizeBtn = document.getElementById('maximizeTerminalBtn');
    const container = document.querySelector('.container');

    if (!maximizeBtn || !container) return;

    maximizeBtn.addEventListener('click', () => {
        const isMaximized = container.classList.toggle('terminal-maximized');
        const icon = maximizeBtn.querySelector('i');
        if (isMaximized) {
            icon.classList.remove('fa-expand');
            icon.classList.add('fa-compress');
            maximizeBtn.title = 'Restore Terminal';
        } else {
            icon.classList.remove('fa-compress');
            icon.classList.add('fa-expand');
            maximizeBtn.title = 'Maximize Terminal';
        }
    });
});
