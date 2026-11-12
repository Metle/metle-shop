(function () {
  function init() {
    if (!window.tinymce) {
      return;
    }
    window.tinymce.init({
      selector: 'textarea.wysiwyg-editor',
      menubar: false,
      plugins: 'link lists code',
      toolbar: 'undo redo | bold italic underline | bullist numlist | link | code',
      height: 420,
      // Self-hosted GPL build (loaded from CDN) — no API key required.
      license_key: 'gpl',
      promotion: false,
      branding: false,
      // Keep Django template tags ({{ }} / {% %}) intact.
      entity_encoding: 'raw',
      verify_html: false,
    });
  }

  if (document.readyState !== 'loading') {
    init();
  } else {
    document.addEventListener('DOMContentLoaded', init);
  }
})();
