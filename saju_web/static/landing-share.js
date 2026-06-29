const LANDING_SHARE_FALLBACK_URL = "https://aisajuleehyeon.com/";

let landingShareToastTimer = null;

function landingCanonicalUrl() {
  const canonical = document.querySelector('link[rel="canonical"]')?.href;
  if (canonical) {
    return canonical;
  }
  return window.location.href || LANDING_SHARE_FALLBACK_URL;
}

function landingShareIconHtml() {
  return `
    <span class="share-icon-stack" aria-hidden="true">
      <span class="share-icon is-kakao"></span>
      <span class="share-icon is-instagram"></span>
    </span>
    <span>공유하기</span>
  `;
}

function landingShareText() {
  const title = document.querySelector("h1")?.textContent?.trim() || "무료 사주 분석";
  const description =
    document.querySelector('meta[name="description"]')?.content?.trim() ||
    "생년월일을 입력하면 정통 명리 이론을 기반으로 무료 사주 분석을 확인할 수 있습니다.";
  return ["AI 사주 : 이현", title, description].filter(Boolean).join("\n");
}

function showLandingShareToast(message) {
  let toast = document.querySelector(".landing-share-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "landing-share-toast";
    toast.setAttribute("role", "status");
    toast.setAttribute("aria-live", "polite");
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add("is-visible");
  if (landingShareToastTimer) {
    window.clearTimeout(landingShareToastTimer);
  }
  landingShareToastTimer = window.setTimeout(() => {
    toast.classList.remove("is-visible");
  }, 2300);
}

async function copyLandingShareText(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch (_error) {}
  try {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    textarea.style.top = "0";
    document.body.appendChild(textarea);
    textarea.select();
    textarea.setSelectionRange(0, textarea.value.length);
    const copied = document.execCommand("copy");
    textarea.remove();
    return copied;
  } catch (_error) {
    return false;
  }
}

async function shareLandingPage() {
  const url = landingCanonicalUrl();
  const text = landingShareText();
  const shareData = {
    title: document.title || "AI 사주 : 이현 무료 사주 분석",
    text,
    url,
  };
  try {
    if (navigator.share) {
      await navigator.share(shareData);
      showLandingShareToast("공유창을 열었습니다.");
      return;
    }
  } catch (error) {
    if (error?.name === "AbortError") {
      return;
    }
  }
  const copied = await copyLandingShareText(`${text}\n\n${url}`);
  showLandingShareToast(copied ? "공유 문구와 링크를 복사했습니다." : "복사에 실패했습니다. 다시 시도해주세요.");
}

function createLandingShareButton() {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "secondary-cta landing-share-button";
  button.setAttribute("data-landing-share", "true");
  button.innerHTML = landingShareIconHtml();
  button.addEventListener("click", shareLandingPage);
  return button;
}

function mountLandingShareButtons() {
  document.querySelectorAll(".cta-row").forEach((row) => {
    if (row.querySelector("[data-landing-share]")) {
      return;
    }
    row.appendChild(createLandingShareButton());
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", mountLandingShareButtons);
} else {
  mountLandingShareButtons();
}
