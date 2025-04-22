// layout_manager.js - handles the draggable vertical resizer between panels
export function initResizer() {
  const resizer   = document.getElementById('vertical-resizer');
  const leftPane  = document.querySelector('.content-area');
  const rightPane = document.querySelector('.terminal-area');
  let startX, startWidth;

  resizer.addEventListener('mousedown', e => {
    e.preventDefault();
    startX     = e.clientX;
    startWidth = leftPane.getBoundingClientRect().width;
    document.body.classList.add('resizing');
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup',   onMouseUp);
  });

  function onMouseMove(e) {
    const dx      = e.clientX - startX;
    let newWidth  = startWidth + dx;
    const minLeft = 200; // matches CSS min-width
    const maxLeft = leftPane.parentElement.getBoundingClientRect().width
                    - rightPane.getBoundingClientRect().width
                    - resizer.getBoundingClientRect().width;
    newWidth = Math.max(minLeft, Math.min(newWidth, maxLeft));
    leftPane.style.flex = `0 0 ${newWidth}px`;
  }

  function onMouseUp() {
    document.body.classList.remove('resizing');
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup',   onMouseUp);
  }
}
