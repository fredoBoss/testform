// Adds a show/hide "eye" button to every password field on the page.
// Loaded with `defer`; without JS the fields stay plain password inputs.
(() => {
  const icon = (paths) =>
    `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
  const EYE = icon('<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>');
  const EYE_OFF = icon(
    '<path d="M10.6 5.1A10.4 10.4 0 0 1 12 5c6.4 0 10 7 10 7a17.6 17.6 0 0 1-2.6 3.5M6.6 6.6A17.4 17.4 0 0 0 2 12s3.6 7 10 7a9.7 9.7 0 0 0 5.4-1.6"/>' +
    '<path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/><path d="m3 3 18 18"/>'
  );

  document.querySelectorAll('input[type="password"]').forEach((input) => {
    const wrapper = document.createElement('div');
    wrapper.className = 'password-field';
    input.before(wrapper);
    wrapper.append(input);

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'password-toggle';
    button.setAttribute('aria-label', 'Show password');
    if (input.id) button.setAttribute('aria-controls', input.id);
    wrapper.append(button);

    const setVisible = (visible) => {
      input.type = visible ? 'text' : 'password';
      button.innerHTML = visible ? EYE_OFF : EYE;
      button.title = visible ? 'Hide password' : 'Show password';
      button.setAttribute('aria-pressed', String(visible));
    };

    button.addEventListener('click', () => setVisible(input.type === 'password'));
    // Mask again before submitting so password managers still recognise the field.
    input.form?.addEventListener('submit', () => setVisible(false));
    setVisible(false);
  });
})();
