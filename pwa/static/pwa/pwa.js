// Loaded with `defer`, so the DOM is already parsed when this runs.
(() => {
  const script = document.currentScript;

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register(script.dataset.swUrl).catch((error) => {
        console.warn('[pwa] Service worker registration failed:', error);
      });
    });
  }

  // "Install app" button, shown only when the browser offers installation.
  const installButton = document.querySelector('[data-install-button]');
  let deferredPrompt = null;

  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    deferredPrompt = event;
    if (installButton) installButton.hidden = false;
  });

  installButton?.addEventListener('click', async () => {
    installButton.hidden = true;
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
  });

  window.addEventListener('appinstalled', () => {
    if (installButton) installButton.hidden = true;
  });

  // Offline banner.
  const banner = document.querySelector('[data-offline-banner]');
  const updateBanner = () => {
    if (banner) banner.hidden = navigator.onLine;
  };
  window.addEventListener('online', updateBanner);
  window.addEventListener('offline', updateBanner);
  updateBanner();
})();
