(() => {
  "use strict";

  const status = {
    configured: false,
    libraryLoaded: false,
    enabled: false,
    armRequested: false,
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
  status.reason = "waiting_for_coupang_departure";
  window.googletag = window.googletag || { cmd: [] };

  let slotQueued = false;
  let libraryFailed = false;

  const configureSlot = () => {
    if (slotQueued || !status.armRequested || libraryFailed) return;
    slotQueued = true;
    status.reason = status.libraryLoaded ? "arming" : "waiting_for_library";
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
              backward: false,
              continueReading: false,
              endOfArticle: false,
              inactivity: false,
              navBar: false,
              unhideWindow: true,
            },
          },
        });
        slot.addService(window.googletag.pubads());
        window.googletag.enableServices();
        window.googletag.display(slot);
        status.enabled = true;
        status.reason = "armed_for_coupang_return";
      } catch (_error) {
        status.reason = "slot_configuration_failed";
      }
    });
  };

  const armForCoupangReturn = () => {
    status.armRequested = true;
    configureSlot();
    return status;
  };
  window.LEEHYEON_ARM_GAM_AFTER_COUPANG = armForCoupangReturn;

  const script = document.createElement("script");
  script.async = true;
  script.crossOrigin = "anonymous";
  script.src = "https://securepubads.g.doubleclick.net/tag/js/gpt.js";
  script.dataset.leehyeonGpt = "true";
  script.addEventListener("load", () => {
    status.libraryLoaded = true;
    if (status.armRequested) configureSlot();
  }, { once: true });
  script.addEventListener("error", () => {
    libraryFailed = true;
    status.reason = "gpt_load_failed";
  }, { once: true });
  document.head.appendChild(script);
})();
