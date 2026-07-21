(() => {
  "use strict";

  const status = {
    configured: false,
    libraryLoaded: false,
    enabled: false,
    reason: "not_configured",
    adUnitPath: "",
  };
  window.LEEHYEON_GAM_INTERSTITIAL_STATUS = status;

  const meta = document.querySelector('meta[name="google-ad-manager-interstitial-unit"]');
  const adUnitPath = String(meta?.content || "").trim();
  status.adUnitPath = adUnitPath;

  if (!adUnitPath) return;
  if (!/^\/\d+\/[A-Za-z0-9_./-]+$/.test(adUnitPath)) {
    status.reason = "invalid_ad_unit_path";
    return;
  }
  if (window.top !== window.self) {
    status.reason = "not_top_window";
    return;
  }

  status.configured = true;
  status.reason = "loading";
  window.googletag = window.googletag || { cmd: [] };

  const configureSlot = () => {
    window.googletag.cmd.push(() => {
      try {
        const slot = window.googletag.defineOutOfPageSlot(
          adUnitPath,
          window.googletag.enums.OutOfPageFormat.INTERSTITIAL,
        );
        if (!slot) {
          status.reason = "unsupported_page";
          return;
        }

        slot.setConfig({
          interstitial: {
            triggers: {
              endOfArticle: false,
              inactivity: false,
              navBar: false,
              unhideWindow: false,
            },
          },
        });
        slot.addService(window.googletag.pubads());
        window.googletag.enableServices();
        window.googletag.display(slot);
        status.enabled = true;
        status.reason = "ready";
      } catch (_error) {
        status.reason = "slot_configuration_failed";
      }
    });
  };

  const script = document.createElement("script");
  script.async = true;
  script.crossOrigin = "anonymous";
  script.src = "https://securepubads.g.doubleclick.net/tag/js/gpt.js";
  script.dataset.leehyeonGpt = "true";
  script.addEventListener("load", () => {
    status.libraryLoaded = true;
    configureSlot();
  }, { once: true });
  script.addEventListener("error", () => {
    status.reason = "gpt_load_failed";
  }, { once: true });
  document.head.appendChild(script);
})();
