const form = document.querySelector("#birth-form");
const inputDisclosure = document.querySelector(".input-disclosure");
const inputPanel = document.querySelector(".input-panel");
const inputSummaryText = document.querySelector("#input-summary-text");
const statusBox = document.querySelector("#status");
const fortuneSpotlight = document.querySelector("#fortune-spotlight");
const homeFunnel = document.querySelector("#home-funnel");
const sideSummary = document.querySelector("#side-summary");
const manseBoard = document.querySelector("#manse-board");
const tierInput = form.elements.tier;
const tierButtons = [...document.querySelectorAll(".tier-button")];
const viewButtons = [...document.querySelectorAll("[data-view-target]")];
const staticActionButtons = [...document.querySelectorAll("[data-view-target], [data-upgrade], [data-input-target]")];
const panels = {
  summary: document.querySelector("#summary"),
  premium: document.querySelector("#premium"),
  factors: document.querySelector("#factors"),
};
const views = {
  home: document.querySelector("#home-view"),
  judgment: document.querySelector("#judgment-view"),
  premium: document.querySelector("#premium-view"),
  basis: document.querySelector("#basis-view"),
};
const viewNames = new Set(Object.keys(views));
const COUPANG_PARTNERS_URL =
  window.LEEHYEON_COUPANG_PARTNERS_URL ||
  "https://link.coupang.com/re/AFFSDP?lptag=AF3151585&pageKey=8174473713&itemId=23653028364&traceid=V0-201-4d8275f22060fd79";
const COUPANG_POPUP_IFRAME_HTML =
  window.LEEHYEON_COUPANG_POPUP_IFRAME_HTML ||
  '<iframe src="https://coupa.ng/cnBqRZ" width="120" height="240" frameborder="0" scrolling="no" referrerpolicy="unsafe-url" browsingtopics></iframe>';
const COUPANG_POPUP_IMAGE_URL = window.LEEHYEON_COUPANG_POPUP_IMAGE_URL || "";
const REPORT_SESSION_KEY = "leehyeon:lastPremiumReport";
const AFFILIATE_RETURN_VIEW_KEY = "leehyeon:coupangReturnView";
const AFFILIATE_LEFT_PAGE_KEY = "leehyeon:coupangPageVisited";
const AFFILIATE_LEFT_AT_KEY = "leehyeon:coupangLeftAt";
const INPUT_EDITOR_REQUEST_KEY = "leehyeon:inputEditorRequested";
const AFFILIATE_RETURN_MAX_AGE_MS = 10 * 60 * 1000;
const REPORT_CLIENT_CACHE_PREFIX = "leehyeon:reportCache:";
const REPORT_CLIENT_CACHE_VERSION = "report-client-v172";
const REPORT_CLIENT_CACHE_MAX_AGE_MS = 24 * 60 * 60 * 1000;
const LOADING_MESSAGES = [
  "분석을 시작했습니다. 생년월일과 태어난 시간을 기준으로 명식을 계산하고 있습니다.",
  "월령과 오행의 강약을 정리하고 있습니다. 잠시만 기다려주세요.",
  "재물·직업·애정·성향 지표를 구성하고 있습니다.",
  "대운과 세운의 작용을 대조하고 있습니다.",
  "프리미엄 화면에 표시할 결과를 정리하고 있습니다.",
  "분석이 마무리 단계입니다. 곧 결과 화면으로 이동합니다.",
];

let currentPayload = null;
let activeView = "home";
let isReportLoading = false;
let affiliatePopupVisible = false;
let loadingTicker = null;
let loadingStartedAt = 0;
let loadingMessageIndex = 0;
let loadingDisplayedPercent = 0;

function storedValue(key) {
  try {
    const value = sessionStorage.getItem(key);
    if (value !== null) {
      return value;
    }
  } catch (_error) {}
  try {
    return localStorage.getItem(key);
  } catch (_error) {
    return null;
  }
}

function setStoredValue(key, value) {
  try {
    sessionStorage.setItem(key, value);
  } catch (_error) {}
  try {
    localStorage.setItem(key, value);
  } catch (_error) {}
}

function removeStoredValue(key) {
  try {
    sessionStorage.removeItem(key);
  } catch (_error) {}
  try {
    localStorage.removeItem(key);
  } catch (_error) {}
}

function markAffiliateDeparture() {
  setStoredValue(AFFILIATE_LEFT_PAGE_KEY, "1");
  setStoredValue(AFFILIATE_RETURN_VIEW_KEY, "premium");
  setStoredValue(AFFILIATE_LEFT_AT_KEY, String(Date.now()));
}

function leaveForAffiliatePage() {
  markAffiliateDeparture();
  removeStoredValue(INPUT_EDITOR_REQUEST_KEY);
  closeCoupangAffiliatePopup();
  setActiveView("premium", { updateHistory: false, instant: true });
  window.location.assign(COUPANG_PARTNERS_URL);
}

function clearAffiliateReturnState() {
  removeStoredValue(AFFILIATE_LEFT_PAGE_KEY);
  removeStoredValue(AFFILIATE_RETURN_VIEW_KEY);
  removeStoredValue(AFFILIATE_LEFT_AT_KEY);
}

function hasFreshAffiliateReturn() {
  const shouldReturnToPremium = storedValue(AFFILIATE_RETURN_VIEW_KEY) === "premium";
  const pageWasVisited = storedValue(AFFILIATE_LEFT_PAGE_KEY) === "1";
  const leftAt = Number(storedValue(AFFILIATE_LEFT_AT_KEY) || 0);
  if (!shouldReturnToPremium || !pageWasVisited || !Number.isFinite(leftAt) || leftAt <= 0) {
    return false;
  }
  return Date.now() - leftAt <= AFFILIATE_RETURN_MAX_AGE_MS;
}

const groupLabels = {
  default: "핵심",
  native: "타고난 운",
  annual: "시기",
  timing: "시기",
  premium: "프리미엄",
};

const kindLabels = {
  core: "핵심 운세",
  domain: "영역별 운세",
  advice: "조언",
  annual: "시기",
  timing: "시기",
  premium: "프리미엄",
};

const premiumRiskMarkerPatternText = "주의|리스크|위험|손실|부담|갈등|맞지";
const premiumRiskMarkerPattern = new RegExp(premiumRiskMarkerPatternText);

function setStatus(message, mode = "normal") {
  if (mode === "loading" && message) {
    renderLoadingStatus(message);
  } else {
    statusBox.textContent = message;
    statusBox.style.removeProperty("--loading-progress");
  }
  statusBox.classList.toggle("is-error", mode === "error");
  statusBox.classList.toggle("is-loading", mode === "loading");
  statusBox.classList.toggle("is-visible", Boolean(message));
}

function clearStatus() {
  statusBox.textContent = "";
  statusBox.style.removeProperty("--loading-progress");
  statusBox.classList.remove("is-visible", "is-error", "is-loading");
}

function loadingMessage(index) {
  const safeIndex = Math.max(0, Math.min(index, LOADING_MESSAGES.length - 1));
  return LOADING_MESSAGES[safeIndex];
}

function showLoadingMessage(index) {
  loadingMessageIndex = Math.max(0, Math.min(index, LOADING_MESSAGES.length - 1));
  setStatus(loadingMessage(loadingMessageIndex), "loading");
}

function refreshLoadingStatus() {
  setStatus(loadingMessage(loadingMessageIndex), "loading");
}

function loadingProgressPercent() {
  if (!loadingStartedAt) {
    return Math.max(12, loadingDisplayedPercent || 12);
  }
  const elapsedSeconds = Math.max(0, (Date.now() - loadingStartedAt) / 1000);
  const target = 8 + 87 * (1 - Math.exp(-elapsedSeconds / 14));
  const nextPercent = Math.min(94, Math.max(8, Math.round(target)));
  loadingDisplayedPercent = Math.max(loadingDisplayedPercent, nextPercent);
  return loadingDisplayedPercent;
}

function renderLoadingStatus(message) {
  const percent = loadingProgressPercent();
  statusBox.style.setProperty("--loading-progress", `${percent}%`);
  statusBox.innerHTML = `
    <div class="status-loading-head">
      <span>분석 준비 중</span>
      <b>${percent}%</b>
    </div>
    <div class="status-loading-bar" aria-hidden="true"><i></i></div>
    <p class="status-loading-copy">${escapeHtml(message)}</p>
  `;
}

function startLoadingStatus() {
  stopLoadingStatus();
  loadingStartedAt = Date.now();
  loadingMessageIndex = 0;
  loadingDisplayedPercent = 8;
  showLoadingMessage(0);
  window.requestAnimationFrame(() => {
    statusBox.scrollIntoView({ behavior: "smooth", block: "center" });
  });
  loadingTicker = window.setInterval(() => {
    const elapsed = Date.now() - loadingStartedAt;
    const nextIndex = Math.min(Math.floor(elapsed / 2600), LOADING_MESSAGES.length - 1);
    showLoadingMessage(nextIndex);
  }, 900);
}

function stopLoadingStatus() {
  if (loadingTicker) {
    window.clearInterval(loadingTicker);
    loadingTicker = null;
  }
  loadingStartedAt = 0;
  loadingMessageIndex = 0;
  loadingDisplayedPercent = 0;
}

function closeCoupangAffiliatePopup() {
  document.querySelector(".affiliate-popup-backdrop")?.remove();
  affiliatePopupVisible = false;
}

function showCoupangAffiliatePopup() {
  closeCoupangAffiliatePopup();
  affiliatePopupVisible = true;
  removeStoredValue(INPUT_EDITOR_REQUEST_KEY);
  const popupProduct = COUPANG_POPUP_IFRAME_HTML
    ? COUPANG_POPUP_IFRAME_HTML
    : COUPANG_POPUP_IMAGE_URL
    ? `<img src="${escapeHtml(COUPANG_POPUP_IMAGE_URL)}" alt="쿠팡 추천 상품" />`
    : `<div class="affiliate-popup-product-placeholder">COUPANG</div>`;
  const backdrop = document.createElement("section");
  backdrop.className = "affiliate-popup-backdrop";
  backdrop.setAttribute("aria-label", "쿠팡 제휴 안내");
  backdrop.innerHTML = `
    <div class="affiliate-popup" role="dialog" aria-modal="true" aria-labelledby="affiliate-popup-title">
      <span class="affiliate-popup-help" aria-hidden="true">?</span>
      <h2 id="affiliate-popup-title">쿠팡 방문하기</h2>
      <p class="affiliate-popup-copy">
        쿠팡 페이지를 방문한 뒤 이 화면으로 돌아오면 분석 결과를 확인할 수 있습니다.
      </p>
      <div class="affiliate-popup-product" aria-hidden="true">
        ${popupProduct}
      </div>
      <strong class="affiliate-popup-visit">쿠팡 방문하기</strong>
      <p class="affiliate-popup-disclosure">
        쿠팡 파트너스 활동의 일환으로 일정액의 수수료를 제공받습니다.
      </p>
      <div class="affiliate-popup-actions">
        <a class="affiliate-popup-primary" href="${escapeHtml(COUPANG_PARTNERS_URL)}" rel="nofollow sponsored noopener">
          쿠팡 방문하고 결과 보기
        </a>
      </div>
    </div>
  `;
  backdrop.querySelector(".affiliate-popup-primary")?.addEventListener("click", (event) => {
    event.preventDefault();
    leaveForAffiliatePage();
  });
  document.body.appendChild(backdrop);
  backdrop.querySelector(".affiliate-popup-primary")?.focus();
}

function revealReportAfterCoupangReturn() {
  if (!hasFreshAffiliateReturn()) {
    document.documentElement.classList.remove("is-restoring-premium");
    clearAffiliateReturnState();
    return;
  }
  if (!currentPayload) {
    restoreReportSession();
  }
  if (!currentPayload) {
    document.documentElement.classList.remove("is-restoring-premium");
    clearAffiliateReturnState();
    return;
  }
  closeCoupangAffiliatePopup();
  setActiveView("premium");
  clearAffiliateReturnState();
  removeStoredValue(INPUT_EDITOR_REQUEST_KEY);
  document.documentElement.classList.remove("is-restoring-premium");
}

function setReportLoading(isLoading) {
  isReportLoading = Boolean(isLoading);
  document.body.classList.toggle("is-report-loading", isReportLoading);
  document.querySelectorAll("button").forEach((button) => {
    if (isReportLoading) {
      if (!button.dataset.loadingLock) {
        button.dataset.loadingLock = "true";
        button.dataset.previousDisabled = button.disabled ? "true" : "false";
      }
      button.disabled = true;
      return;
    }
    if (button.dataset.loadingLock) {
      button.disabled = button.dataset.previousDisabled === "true";
      delete button.dataset.loadingLock;
      delete button.dataset.previousDisabled;
    }
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function sentenceList(value) {
  return String(value || "")
    .split(".")
    .map((sentence) => sentence.trim())
    .filter(Boolean)
    .map((sentence) => `${sentence}.`);
}

function firstSentences(value, limit = 1) {
  return sentenceList(value).slice(0, limit).join(" ");
}

function normalizedSentenceKey(value) {
  return String(value || "")
    .replace(/\s+/g, "")
    .replace(/[.,!?。．·:;'"“”‘’()\[\]{}]/g, "")
    .trim();
}

function sentenceAlreadyShown(sentence, context) {
  const key = normalizedSentenceKey(sentence);
  if (!key) {
    return false;
  }
  return sentenceList(context).some((item) => normalizedSentenceKey(item) === key);
}

function removeShownSentences(value, context, limit = 1) {
  const contextText = String(context || "");
  return sentenceList(value)
    .filter((sentence) => !sentenceAlreadyShown(sentence, contextText))
    .slice(0, limit)
    .join(" ");
}

function sentenceContaining(value, pattern) {
  return sentenceList(value).find((sentence) => sentence.includes(pattern)) || "";
}

function domainDisplayLabel(card) {
  return card?.domain_label || card?.title || "운세";
}

function entryDisplayLabel(entry) {
  return groupLabels[entry?.display_group] || kindLabels[entry?.kind] || "운세 기준";
}

function domainKeyFromText(value) {
  const text = String(value || "");
  if (text.includes("재물") || text.includes("돈") || text.includes("수입")) {
    return "money";
  }
  if (text.includes("직업") || text.includes("일") || text.includes("평가") || text.includes("성과")) {
    return "career";
  }
  if (text.includes("연애") || text.includes("애정") || text.includes("인연") || text.includes("호감")) {
    return "love";
  }
  if (text.includes("결혼") || text.includes("배우자") || text.includes("가정")) {
    return "marriage";
  }
  return "default";
}

function cardDomainClass(item) {
  const source = [item?.domain_label, item?.domain, item?.title, item?.headline, item?.entry_id, item?.display_group]
    .filter(Boolean)
    .join(" ");
  const domain = domainKeyFromText(source);
  return domain === "default" ? "" : `domain-${domain}`;
}

function cleanCustomerSentence(sentence) {
  return String(sentence || "")
    .replaceAll("성과의 금전 전환", "해낸 일의 금전 보상")
    .replaceAll("성과의 금전 보상", "해낸 일의 금전 보상")
    .replaceAll("지급 조건", "지급 기준")
    .replaceAll("거래 성사", "거래가 성사되는 일")
    .replaceAll("거래가 성사되는 일가", "거래가 성사되는 일이")
    .replaceAll("맡는 일이 커지는 일가", "맡는 일이 늘어나는 일이")
    .replaceAll("맡는 일이 커지는 일나", "맡는 일이 늘어나는 일이나")
    .replaceAll("맡는 일이 바뀌는 일가", "맡는 일이 바뀌는 일이")
    .replaceAll("맡는 일이 바뀌는 일나", "맡는 일이 바뀌는 일이나")
    .replaceAll("보상 실현", "보상이 수입으로 들어오는 일")
    .replaceAll("보상 조건", "보상 기준")
    .replaceAll("보상이 정해지는 기준에서 실제 크기가 정해집니다.", "수령액의 크기가 여기서 정해집니다.")
    .replaceAll("수입 조건", "수입 기준")
    .replaceAll("계약 부담", "계약에서 생기는 부담")
    .replaceAll("지급 시점", "지급일")
    .replaceAll("역할 범위", "맡는 범위")
    .replaceAll("역할 확대", "업무 범위 확대")
    .replaceAll("직무 전환", "직무 변경")
    .replaceAll("권한 범위", "결정권")
    .replaceAll("관계가 안정되는 일성", "관계 안정성")
    .replaceAll("호감 형성", "호감")
    .replaceAll("생활 합의", "함께 사는 방식에 대한 합의")
    .replace(new RegExp(["받을", "돈이 커지고 성과 보상이 강해지는 해입니다."].join(" "), "g"), "수령액이 늘고 보상 기준이 분명해지는 해입니다.")
    .replaceAll("성과 보상이 정해지는", "해낸 일에 따른 보상이 정해지는")
    .replaceAll("당신의 세부 특성에서는 재물 잠재력이", "재물 잠재력은")
    .replaceAll("당신의 세부 특성에서는 사회적 성공 잠재력이", "사회적으로 올라설 가능성은")
    .replaceAll("당신의 세부 특성에서는 명예운이", "사회적 인정도는")
    .replaceAll("당신의 세부 특성에서는 직업적 성취력이", "직업 성취 기반은")
    .replaceAll("당신의 세부 특성에서는 관계 안정성이", "관계 안정성은")
    .replaceAll("권한를", "권한을")
    .replaceAll("일가", "일이")
    .replaceAll("일나", "일이나")
    .replaceAll("명예운은 상위", "사회적 인정도는 상위")
    .replaceAll("사회적 성공 잠재력은 상위", "사회적으로 올라설 가능성은 상위")
    .replaceAll("명예운은 강한 편입니다.", "인정과 평가가 분명하게 들어오는 편입니다.")
    .replaceAll("공식 평가를 안정적으로 얻는 방식", "공식적인 자리에서 좋은 평가를 받는 방식")
    .replaceAll("좋은 선택을 잡을 때와 결정을 늦춰야 할 때가 여러 구간으로 나뉩니다.", "좋은 연도와 주의 연도가 따로 드러납니다.")
    .replaceAll("좋은 연도와 주의 연도가 뚜렷합니다.", "좋은 연도와 주의 연도가 따로 드러납니다.")
    .replaceAll("맡은 일의 결과가 보수와 계약 조건으로 확정됩니다.", "일의 대가가 보수로 분명히 잡힙니다.")
    .replaceAll("직업운은 성과가 평가와 보상으로 확정되는 힘이 강합니다.", "직업운은 결과가 직함과 평판으로 굳어집니다.")
    .replaceAll("공식 평가를 확보합니다.", "공식 평가가 직책 상승으로 이어집니다.")
    .replaceAll("조력은 말보다 실질적인 지원을 하는 사람에게서 들어옵니다.", "결정적인 도움은 실제 소개로 들어옵니다.")
    .replaceAll("중요한 순간에는 말보다 실질적인 지원을 하는 사람이 곁에 남습니다.", "중요한 순간에는 실제 소개를 해줄 사람이 곁에 남습니다.")
    .replaceAll("공동 자금 기준 필요", "지분·명의 안정성")
    .replaceAll("정산 기준 필요", "수익 배분 안정성")
    .replaceAll("판정 기준", "근거 항목")
    .replaceAll("판정 근거", "근거 항목")
    .replaceAll("대표 판정", "대표 결과")
    .replaceAll("핵심 판정", "핵심 결과")
    .replaceAll("세부 판정", "세부 내용")
    .replaceAll("추가 판정", "추가 내용")
    .replaceAll("판정 범위", "분석 범위")
    .replaceAll("판정 배경", "분석 배경")
    .replaceAll("월령 판정", "월령 기준")
    .replaceAll("연도 판정", "연도 결과")
    .replaceAll("주의 판정", "주의 기준")
    .replaceAll("판정합니다", "정리합니다")
    .replaceAll("판정했습니다", "정리했습니다")
    .replaceAll("판정한", "정리한")
    .replaceAll("판정에", "분석에")
    .replaceAll("판정이", "결과가")
    .replaceAll("판정은", "결과는")
    .replaceAll("판정을", "결과를")
    .replaceAll("판정의", "결과의")
    .replaceAll("판정", "결과");
}

function cleanCustomerText(value) {
  return sentenceList(value)
    .map(cleanCustomerSentence)
    .join(" ");
}

function cleanCustomerLabel(value) {
  return cleanCustomerSentence(value).replace(/\.$/, "").replace(/\s+일$/, "").trim();
}

const scoreAxisLabels = {
  money: {
    focus: "재물 핵심",
    result: "재물 형성력",
    opportunity: "수익 전환력",
    risk: "손실 방어력",
    change: "재정 변동성",
    confidence: "분석 신뢰도",
  },
  career: {
    focus: "직업 핵심",
    result: "성취 축적력",
    opportunity: "사회적 기회",
    risk: "권한 확보력",
    change: "자리 변화",
    confidence: "분석 신뢰도",
  },
  love: {
    focus: "관계 핵심",
    result: "관계 형성력",
    opportunity: "인연 가능성",
    risk: "감정 조율력",
    change: "관계 변동성",
    confidence: "분석 신뢰도",
  },
  marriage: {
    focus: "결혼 핵심",
    result: "결혼 현실화",
    opportunity: "약속 추진력",
    risk: "생활 안정성",
    change: "결정 변동성",
    confidence: "분석 신뢰도",
  },
  default: {
    focus: "핵심 결론",
    result: "현실화 강도",
    opportunity: "기회 강도",
    risk: "관리 필요도",
    change: "변동성",
    confidence: "분석 신뢰도",
  },
};

function scoreDomain(card) {
  return card?.domain || domainKeyFromText([card?.domain_label, card?.title, card?.headline].filter(Boolean).join(" "));
}

function scoreAxisKey(text) {
  if (text.includes("핵심")) return "focus";
  if (text.includes("발생력") || text.includes("형성력") || text.includes("성취력") || text.includes("현실화") || text.includes("결과")) return "result";
  if (text.includes("창출력") || text.includes("사회적 기회") || text.includes("인연 가능성") || text.includes("약속 추진력") || text.includes("기회")) return "opportunity";
  if (text.includes("손실") || text.includes("분산") || text.includes("부담") || text.includes("마찰") || text.includes("충돌") || text.includes("위험") || text.includes("주의")) return "risk";
  if (text.includes("변동") || text.includes("자리 변화") || text.includes("관계 변화") || text.includes("결정 변화") || text.includes("변화")) return "change";
  if (text.includes("신뢰")) return "confidence";
  return "result";
}

function compactScoreValue(text) {
  return String(text || "")
    .replaceAll("재물 핵심", "")
    .replaceAll("직업 핵심", "")
    .replaceAll("관계 핵심", "")
    .replaceAll("결혼 핵심", "")
    .replaceAll("핵심 판정", "")
    .replaceAll("핵심", "")
    .replaceAll("재물 발생력", "")
    .replaceAll("수입 창출력", "")
    .replaceAll("손실·분산 주의", "")
    .replaceAll("손실 방어력", "")
    .replaceAll("손실 관리", "")
    .replaceAll("재정 변동성", "")
    .replaceAll("직업 성취력", "")
    .replaceAll("사회적 기회", "")
    .replaceAll("권한·책임 균형도", "")
    .replaceAll("결정권 없는 책임", "권한·책임 균형도")
    .replaceAll("자리 변화", "")
    .replaceAll("관계 형성력", "")
    .replaceAll("인연 가능성", "")
    .replaceAll("감정 마찰", "")
    .replaceAll("감정 조율력", "")
    .replaceAll("감정 충돌", "")
    .replaceAll("관계 변동성", "")
    .replaceAll("결혼 현실화", "")
    .replaceAll("약속 추진력", "")
    .replaceAll("생활 충돌", "")
    .replace(/생활\s*변수/g, "")
    .replaceAll("결정 변동성", "")
    .replaceAll("현실화 강도", "")
    .replaceAll("기회 강도", "")
    .replaceAll("주의 강도", "")
    .replaceAll("결과성", "")
    .replaceAll("결과", "")
    .replaceAll("기회", "")
    .replaceAll("위험", "")
    .replaceAll("변동성", "")
    .replaceAll("변화", "")
    .replaceAll("신뢰도", "")
    .replaceAll("강한 주의", "주의 강함")
    .replaceAll("중간 주의", "주의 보통")
    .replaceAll("낮은 주의", "주의 낮음")
    .replace(/\s+/g, " ")
    .trim();
}

function scoreItems(card, limit = 4) {
  const explicitAxes = Array.isArray(card?.judgment_axes) ? card.judgment_axes : [];
  if (explicitAxes.length) {
    const mapped = explicitAxes
      .filter((item) => item && item.label)
      .map((item) => ({
        axis: item.key || item.label,
        label: cleanCustomerLabel(item.label),
        value: cleanCustomerLabel(item.value || "확인"),
        description: axisDescription(item.key || item.label, item.label),
      }));
    if (mapped.length <= limit) {
      return mapped;
    }
    const riskItem = mapped.find((item) => isCardRiskAxis(item.axis, item.label));
    if (!riskItem || limit < 2) {
      return mapped.slice(0, limit);
    }
    const front = mapped.filter((item) => item !== riskItem).slice(0, limit - 1);
    return [...front, riskItem];
  }
  const labelMap = scoreAxisLabels[scoreDomain(card)] || scoreAxisLabels.default;
  const raw = String(card?.score_label || "");
  const segments = raw
    .split(",")
    .map((segment) => segment.trim())
    .filter(Boolean);
  if (!segments.length) {
    return [];
  }
  const preferred = ["focus", "result", "opportunity", "risk", "change", "confidence"];
  const byAxis = new Map();
  segments.forEach((segment) => {
    const axis = scoreAxisKey(segment);
    if (!byAxis.has(axis)) {
      byAxis.set(axis, {
        axis,
        label: labelMap[axis] || scoreAxisLabels.default[axis] || "분석",
        value: normalizeScoreValue(compactScoreValue(segment), axis),
        description: axisDescription(axis, labelMap[axis] || scoreAxisLabels.default[axis] || "분석"),
      });
    }
  });
  return preferred
    .map((axis) => byAxis.get(axis))
    .filter(Boolean)
    .slice(0, limit);
}

function isCardRiskAxis(axis, label) {
  const key = String(axis || "");
  const text = String(label || "");
  return (
    key.includes("risk") ||
    key.includes("friction") ||
    key.includes("family_risk") ||
    key.includes("authority") ||
    text.includes("손해") ||
    text.includes("위험") ||
    text.includes("정산") ||
    text.includes("충돌") ||
    text.includes("문제") ||
    text.includes("결정권 없는 책임") ||
    text.includes("책임·권한 불균형")
  );
}

const axisDescriptionMap = {
  wealth_formation: "금전 기회가 실제 생활권 안으로 들어오는 규모와 속도입니다.",
  income_creation: "성과, 거래, 보상이 실제 수입으로 전환되는 강도입니다.",
  asset_retention: "수입이 소비로 흩어지지 않고 자산으로 남습니다.",
  spending_control: "생활비, 고정비, 관계 비용을 감당한 뒤 남는 금액을 지킵니다.",
  shared_asset_risk: "동업, 가족, 가까운 사람과 함께 다루는 자금에서 몫과 책임을 분명히 남기는 안정성입니다.",
  contract_loss_risk: "계약 조건, 지급일, 보증 관계에서 금전 권리를 지켜내는 안정성입니다.",
  skill_income: "기술, 콘텐츠, 서비스가 유료 상품으로 바뀌는 수익성입니다.",
  performance_reward: "해낸 일의 대가를 보상과 배분으로 확정합니다.",
  career_achievement: "일의 성과가 이력, 직책, 다음 자리의 근거가 됩니다.",
  recognition: "업무 결과가 평가, 평판, 책임 있는 자리의 근거가 됩니다.",
  organization_fit: "조직의 규칙과 질서 안에서 자리를 잡는 적합성입니다.",
  responsibility_capacity: "책임이 커질 때 업무 무게를 감당하는 여력입니다.",
  expertise: "지식, 기술, 숙련도가 경쟁력으로 인정되는 기반입니다.",
  authority_risk: "책임과 결정권이 함께 주어져 직업적 위치가 흔들리지 않습니다.",
  relationship_opening: "새로운 인연과 호감이 실제 만남으로 이어지는 접점입니다.",
  expression: "마음이 상대에게 전달되는 속도와 방식입니다.",
  stability: "관계가 쉽게 흔들리지 않고 오래 유지되는 안정성입니다.",
  boundary: "거리, 기대, 역할이 과하게 섞이지 않게 잡는 조절력입니다.",
  recovery: "다툼이나 오해가 생겨도 관계를 다시 세우는 회복력입니다.",
  friction: "감정 표현의 차이와 대화 방식을 조율하는 안정성입니다.",
  marriage_realization: "관계가 결혼과 장기 약속으로 안정되는 현실성입니다.",
  life_stability: "주거 기준이 맞물리는 현실 안정성입니다.",
  responsibility_share: "가족과 생활 책임을 감당하고 나누는 현실 감각입니다.",
  decision_consistency: "결혼과 가정 문제에서 결정을 오래 유지하는 지속성입니다.",
  family_risk: "가족, 주거, 생활비 문제가 결혼 생활 안에서 흔들리지 않는 안정성입니다.",
};

function axisDescription(axis, label) {
  const key = String(axis || "").trim();
  if (axisDescriptionMap[key]) {
    return axisDescriptionMap[key];
  }
  const text = String(label || key || "").trim();
  if (text.includes("재물")) {
    return "재물이 만들어지고 자산으로 남는 방식입니다.";
  }
  if (text.includes("직업") || text.includes("평가") || text.includes("전문")) {
    return "성과와 평가가 직업적 위치를 만드는 방식입니다.";
  }
  if (text.includes("관계") || text.includes("연애") || text.includes("애정")) {
    return "호감과 안정감이 실제 관계로 이어지는 방식입니다.";
  }
  if (text.includes("결혼") || text.includes("가족") || text.includes("생활")) {
    return "약속, 생활, 책임이 현실에서 맞춰지는 방식입니다.";
  }
  return "";
}

function scoreLimitForCard(card) {
  return 4;
}

function normalizeScoreValue(value, axis) {
  let text = String(value || "").trim();
  if (axis === "risk") {
    text = text
      .replaceAll("강한 주의", "높음")
      .replaceAll("주의 강함", "높음")
      .replaceAll("중간 주의", "보통")
      .replaceAll("주의 보통", "보통")
      .replaceAll("낮은 주의", "낮음")
      .replaceAll("주의 낮음", "낮음");
  }
  return text;
}

function judgmentOverviewContent(report) {
  const overview = cleanOverviewText(report.overview || "");
  return firstSentences(overview, 3) || "사주 전체의 첫 결론이 분명합니다.";
}

function viewFromHash() {
  const hashView = window.location.hash.replace("#", "");
  if (hashView === "report" || hashView === "summary" || hashView === "detail" || hashView === "catalog" || hashView === "judgment") {
    window.history.replaceState({}, "", viewUrl("premium"));
    return "premium";
  }
  if (hashView === "factors") {
    return "basis";
  }
  return viewNames.has(hashView) ? hashView : "home";
}

function viewUrl(viewName) {
  const base = `${window.location.pathname}${window.location.search}`;
  return viewName === "home" ? base : `${base}#${viewName}`;
}

function applyTierSelection(tier) {
  const normalized = tier === "premium" ? "premium" : "free";
  tierInput.value = normalized;
  tierButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tier === normalized);
  });
}

function setActiveView(viewName, options = {}) {
  const nextView = views[viewName] ? viewName : "home";
  activeView = nextView;
  document.body.dataset.view = nextView;
  Object.entries(views).forEach(([key, view]) => {
    view.classList.toggle("is-active", key === nextView);
  });
  if (nextView === "home") {
    inputDisclosure?.setAttribute("open", "");
  }
  viewButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.viewTarget === nextView);
  });
  document.querySelectorAll(".mobile-action-bar button[data-upgrade]").forEach((button) => {
    button.classList.toggle("is-active", nextView === "premium");
  });
  if (options.updateHistory !== false) {
    const nextUrl = viewUrl(nextView);
    const currentUrl = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    if (currentUrl !== nextUrl) {
      window.history.pushState({ view: nextView }, "", nextUrl);
    }
  }
  if (!options.keepScroll) {
    window.scrollTo({ top: 0, behavior: options.instant ? "auto" : "smooth" });
  }
}

function openInputEditor(options = {}) {
  if (options.tier) {
    applyTierSelection(options.tier);
  }
  setStoredValue(INPUT_EDITOR_REQUEST_KEY, "1");
  if (activeView !== "home") {
    setActiveView("home", { instant: true });
  }
  closeCoupangAffiliatePopup();
  document.body.classList.add("input-editor-open");
  inputDisclosure?.setAttribute("open", "");
  window.requestAnimationFrame(() => {
    inputPanel?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

function formPayload() {
  const data = new FormData(form);
  return {
    birthDate: data.get("birthDate"),
    birthTime: data.get("birthTime"),
    gender: data.get("gender"),
    calendarType: data.get("calendarType"),
    relationshipStatus: data.get("relationshipStatus"),
    targetYear: Number(data.get("targetYear")),
    tier: data.get("tier"),
  };
}

function reportClientCacheKey(payload) {
  const normalized = {
    version: REPORT_CLIENT_CACHE_VERSION,
    birthDate: String(payload.birthDate || ""),
    birthTime: String(payload.birthTime || ""),
    gender: String(payload.gender || ""),
    calendarType: String(payload.calendarType || ""),
    relationshipStatus: String(payload.relationshipStatus || ""),
    targetYear: String(payload.targetYear || ""),
    tier: String(payload.tier || ""),
  };
  return `${REPORT_CLIENT_CACHE_PREFIX}${JSON.stringify(normalized)}`;
}

function readReportClientCache(cacheKey) {
  try {
    const raw = localStorage.getItem(cacheKey);
    if (!raw) {
      return null;
    }
    const cached = JSON.parse(raw);
    if (!cached?.payload || !cached.savedAt || Date.now() - Number(cached.savedAt) > REPORT_CLIENT_CACHE_MAX_AGE_MS) {
      localStorage.removeItem(cacheKey);
      return null;
    }
    return cached.payload;
  } catch (_error) {
    return null;
  }
}

function writeReportClientCache(cacheKey, payload) {
  try {
    localStorage.setItem(
      cacheKey,
      JSON.stringify({
        payload,
        savedAt: Date.now(),
      })
    );
  } catch (_error) {}
}

function formSessionState() {
  return {
    birthDate: form.elements.birthDate?.value || "",
    birthTime: form.elements.birthTime?.value || "",
    gender: form.elements.gender?.value || "male",
    calendarType: form.elements.calendarType?.value || "solar",
    relationshipStatus: form.elements.relationshipStatus?.value || "unknown",
    targetYear: form.elements.targetYear?.value || "2026",
    tier: form.elements.tier?.value || "premium",
  };
}

function applyFormSessionState(state = {}) {
  Object.entries(state).forEach(([key, value]) => {
    if (form.elements[key] && value !== undefined && value !== null) {
      form.elements[key].value = value;
    }
  });
  applyTierSelection(state.tier || "premium");
  updateInputSummary();
}

function persistReportSession(payload) {
  try {
    setStoredValue(
      REPORT_SESSION_KEY,
      JSON.stringify({
        payload,
        formState: formSessionState(),
        savedAt: Date.now(),
      })
    );
    removeStoredValue(INPUT_EDITOR_REQUEST_KEY);
  } catch (_error) {
    // Session restore is a convenience layer. If storage is unavailable, the report still renders normally.
  }
}

function restoreReportSession() {
  try {
    const raw = storedValue(REPORT_SESSION_KEY);
    if (!raw) {
      return false;
    }
    const saved = JSON.parse(raw);
    if (!saved?.payload?.ok) {
      return false;
    }
    applyFormSessionState(saved.formState || {});
    renderJudgmentPayload(saved.payload);
    document.body.classList.remove("input-editor-open");
    inputDisclosure?.removeAttribute("open");
    return true;
  } catch (_error) {
    removeStoredValue(REPORT_SESSION_KEY);
    return false;
  }
}

function updateInputSummary() {
  const data = new FormData(form);
  const genderSelect = form.elements.gender;
  const timeSelect = form.elements.birthTime;
  const genderLabel = genderSelect.options[genderSelect.selectedIndex]?.text || "성별";
  const timeLabel = timeSelect.options?.[timeSelect.selectedIndex]?.text || data.get("birthTime");
  const birthDate = data.get("birthDate");
  const birthTime = data.get("birthTime");
  inputSummaryText.textContent =
    birthDate && birthTime ? `${birthDate} · ${timeLabel} · ${genderLabel}` : "출생 정보";
}

function wait(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

async function readJudgmentResponse(response) {
  let payload = null;
  try {
    payload = await response.json();
  } catch (_error) {
    throw new Error("분석 결과를 불러오지 못했습니다.");
  }
  return payload;
}

async function pollJudgmentJob(jobId) {
  const startedAt = Date.now();
  let attempt = 0;
  while (Date.now() - startedAt < 180000) {
    await wait(attempt === 0 ? 650 : attempt < 5 ? 1200 : 1800);
    attempt += 1;
    refreshLoadingStatus();
    const response = await fetch(`/api/judgment-status?jobId=${encodeURIComponent(jobId)}`, {
      headers: {
        Accept: "application/json",
      },
    });
    const payload = await readJudgmentResponse(response);
    if (response.status === 202 && payload?.pending) {
      continue;
    }
    if (!response.ok || !payload?.ok) {
      throw new Error(payload?.error?.message || "분석 결과 생성에 실패했습니다.");
    }
    return payload;
  }
  throw new Error("분석 시간이 길어지고 있습니다. 잠시 뒤 다시 시도해주세요.");
}

async function requestJudgment() {
  const basePayload = formPayload();
  const cacheKey = reportClientCacheKey(basePayload);
  const cachedPayload = readReportClientCache(cacheKey);
  if (cachedPayload) {
    setStatus("저장된 분석 결과를 불러오고 있습니다.", "loading");
    await wait(180);
    return cachedPayload;
  }
  startLoadingStatus();
  const response = await fetch("/api/judgment", {
    method: "POST",
    headers: {
      "Content-Type": "application/json; charset=utf-8",
    },
    body: JSON.stringify({ ...basePayload, async: true }),
  });
  const payload = await readJudgmentResponse(response);
  if (response.status === 202 && payload?.pending && payload.jobId) {
    const result = await pollJudgmentJob(payload.jobId);
    writeReportClientCache(cacheKey, result);
    return result;
  }
  if (!response.ok || !payload?.ok) {
    throw new Error(payload?.error?.message || "분석 결과 생성에 실패했습니다.");
  }
  writeReportClientCache(cacheKey, payload);
  return payload;
}

function renderManseBoard(chart) {
  const pillars = chart.pillarRows || [];
  const daeunRows = chart.daeunRows || [];
  const annualRows = chart.annualRows || [];
  manseBoard.innerHTML = `
    <div class="manse-head">
      <div>
        <p class="eyebrow">명식 근거</p>
        <h2>팔자와 대운·세운을 함께 표시합니다.</h2>
      </div>
    </div>
    <div class="palja-grid" aria-label="사주 팔자 기둥">
      <div class="palja-row palja-label-row">
        ${pillars.map((item) => `<div>${escapeHtml(item.label)}</div>`).join("")}
      </div>
      <div class="palja-row palja-stem-row">
        ${pillars.map((item) => `<div>${escapeHtml(item.stem)}</div>`).join("")}
      </div>
      <div class="palja-row palja-branch-row">
        ${pillars.map((item) => `<div>${escapeHtml(item.branch)}</div>`).join("")}
      </div>
      <div class="palja-row palja-god-row">
        ${pillars.map((item) => `<div>${escapeHtml(item.tenGod || "-")}</div>`).join("")}
      </div>
    </div>
    <div class="cycle-board">
      ${renderCycleLane("대운", daeunRows, "ageLabel")}
      ${renderCycleLane("세운", annualRows, "year")}
    </div>
  `;
}

function renderCycleLane(title, rows, labelKey) {
  if (!rows.length) {
    return `
      <section class="cycle-lane">
        <div class="cycle-title"><h3>${escapeHtml(title)}</h3><p>산출 대기</p></div>
      </section>
    `;
  }
  return `
    <section class="cycle-lane">
      <div class="cycle-title">
        <h3>${escapeHtml(title)}</h3>
        <p>${title === "대운" ? "10년 단위 기둥" : "선택 연도부터 순서대로"}</p>
      </div>
      <div class="cycle-scroll">
        ${rows
          .map((row) => {
            const label = labelKey === "year" ? `${row.year}년 · ${row.ageLabel}` : row.ageLabel;
            return `
              <article class="cycle-pillar ${row.isCurrent ? "is-current" : ""}">
                <span>${escapeHtml(label)}</span>
                <strong>${escapeHtml(row.stem)}</strong>
                <strong>${escapeHtml(row.branch)}</strong>
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function renderFortuneSpotlight(payload) {
  fortuneSpotlight.innerHTML = `
    <article class="spotlight-main service-hero">
      <div>
        <p class="eyebrow">AI 사주 : 이현</p>
        <h2>정통 명리 사주 분석</h2>
        <p class="spotlight-lead">생년월일과 태어난 시간을 바탕으로, 당신의 성격과 재물·직업·인연의 길흉을 정밀하게 안내해드립니다.</p>
        <div class="spotlight-symbol-row" aria-label="대표 운세 영역">
          <span>總</span>
          <span>財</span>
          <span>職</span>
          <span>緣</span>
        </div>
      </div>
    </article>
  `;
}

function renderHead(payload) {
  const { chart } = payload;
  renderFortuneSpotlight(payload);
  renderHomeFunnel(payload);
  renderSideSummary(payload);
  renderManseBoard(chart);
}

function renderSideSummary(payload) {
  const chart = payload.chart;
  const pillars = chart.pillarRows || [];
  const currentDaeun = chart.currentDaeun;
  const genderLabel = payload.request?.gender === "female" ? "여자" : payload.request?.gender === "male" ? "남자" : "";
  sideSummary.innerHTML = `
    <div class="side-summary-head">
      <p class="eyebrow">사주 기준</p>
      <h2>${escapeHtml(genderLabel || "입력 정보")} 기준</h2>
    </div>
    <div class="side-pillar-list">
      ${pillars
        .map(
          (pillar) => `
            <div>
              <span>${escapeHtml(pillar.label)}</span>
              <strong>${escapeHtml(pillar.pillar)}</strong>
            </div>
          `,
        )
        .join("")}
    </div>
    <div class="side-current">
      <span>현재 대운</span>
      <strong>${escapeHtml(currentDaeun ? `${currentDaeun.ageLabel} · ${currentDaeun.pillar}` : "산출 대기")}</strong>
    </div>
    <div class="side-actions">
      <button type="button" data-view-target="basis">명식표 보기</button>
      <button type="button" data-upgrade="true">프리미엄 운세 보기</button>
    </div>
  `;
}

function renderHomeFunnel(payload) {
  homeFunnel.innerHTML = "";
}

function renderServiceCard(title, description, badge, tier) {
  const tierLabel = tier === "premium" ? "premium" : "free";
  return `
    <article class="service-card ${tier === "premium" ? "is-premium" : ""}">
      <span>${escapeHtml(badge)}</span>
      <h3>${escapeHtml(title)}</h3>
      <p>${escapeHtml(description)}</p>
      <button type="button" data-input-target="birth" data-start-tier="${tierLabel}">
        ${tier === "premium" ? "프리미엄 운세 보기" : "운세 보기"}
      </button>
    </article>
  `;
}

function renderPremiumMiniItem(title, description) {
  return `
    <article class="premium-mini-item">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(description)}</span>
    </article>
  `;
}

function renderQuickService(title, description, viewTarget = "") {
  const action = viewTarget
    ? `data-view-target="${escapeHtml(viewTarget)}"`
    : `data-input-target="birth" data-start-tier="free"`;
  return `
    <button class="quick-service" type="button" ${action}>
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(description)}</span>
    </button>
  `;
}

function renderHomeFreeCard(card, index) {
  return `
    <article class="home-free-card ${cardDomainClass(card)}" id="home-card-${index + 1}">
      <span>${escapeHtml(domainDisplayLabel(card))}</span>
      <h3>${escapeHtml(cleanCustomerSentence(card.headline || card.title))}</h3>
      <p>${escapeHtml(cleanCustomerSentence(firstSentences(card.summary, 1) || card.title))}</p>
      <button type="button" data-linked-index="${index + 1}">운세 읽기</button>
    </article>
  `;
}

function chipRow(values) {
  if (!values?.length) {
    return "";
  }
  return `<div class="chip-row">${values.map((value) => `<span class="chip">${escapeHtml(value)}</span>`).join("")}</div>`;
}

function renderFreeProfilePreview(report) {
  const preview = report.free_profile_preview || {};
  const sections = freeProfileSections(report);
  if (!sections.length) {
    panels.summary.innerHTML = `<div class="empty-state">핵심 요약이 준비되지 않았습니다.</div>`;
    return;
  }
  panels.summary.innerHTML = `
    <section class="free-profile-shell">
      ${renderJudgmentOverview(report)}
      <section class="free-profile-intro" aria-label="무료 결과 안내">
        <div>
          <p class="eyebrow">무료 종합운</p>
          <h2>${escapeHtml(preview.headline || "재물, 직업, 연애, 결혼의 핵심 결과입니다.")}</h2>
          <p>${escapeHtml(preview.lead || "무료 운세에서는 전체 결론과 영역별 대표 강점, 주의 기준만 공개합니다.")}</p>
        </div>
        <button type="button" data-upgrade="true">프리미엄 운세 보기</button>
      </section>
      <div class="free-profile-sections">
        ${sections.map((section, index) => renderFreeProfileSection(section, index)).join("")}
      </div>
      ${renderFreePremiumBridge(sections)}
    </section>
  `;
}

function freeProfileSections(report) {
  const previewSections = Array.isArray(report?.free_profile_preview?.sections)
    ? report.free_profile_preview.sections
    : [];
  if (previewSections.length) {
    return previewSections;
  }
  return (report.mobile_cards || []).map((card) => freeProfileSectionFromCard(card));
}

function freeProfileSectionFromCard(card) {
  const axes = Array.isArray(card?.judgment_axes) ? card.judgment_axes : [];
  const strongAxis = [...axes].sort((a, b) => axisSortValue(b) - axisSortValue(a))[0] || {};
  const watchAxis = [...axes].sort((a, b) => axisSortValue(a) - axisSortValue(b))[0] || {};
  return {
    domain: scoreDomain(card),
    title: domainDisplayLabel(card),
    headline: productCardHeadline(card),
    summary: productCardSummary(card),
    grade: reportCardGrade(card),
    strong_axis: profileAxisPayload(strongAxis),
    watch_axis: profileAxisPayload(watchAxis),
    premium_hint: premiumPromptText(card),
  };
}

function axisSortValue(axis) {
  const value = String(axis?.value || "");
  if (value.includes("최상위")) return 96;
  if (value.includes("상위")) return 86;
  if (value.includes("중상위")) return 76;
  if (value.includes("안정")) return 72;
  if (value.includes("평균")) return 62;
  if (value.includes("보통")) return 56;
  if (value.includes("주의")) return 42;
  if (value.includes("약세") || value.includes("낮음")) return 34;
  return 50;
}

function profileAxisPayload(axis) {
  const label = cleanCustomerLabel(axis?.label || "핵심 항목");
  return {
    label,
    value: cleanCustomerLabel(axis?.value || "확인"),
    definition: freeAxisDefinition(label),
    score: axisSortValue(axis),
  };
}

function freeAxisDefinition(label) {
  const definitions = {
    "타고난 재물의 그릇": "재물을 감당하고 키울 수 있는 선천적 기반입니다.",
    "재물이 들어오는 길": "일, 거래, 성과가 실제 수입으로 바뀌는 자리입니다.",
    "재산으로 굳어지는 힘": "들어온 돈이 소비로 흩어지지 않고 자산으로 남는 구조입니다.",
    "재물에 얽히는 사람 문제": "가족, 지인, 동업자와 얽힌 돈에서 자기 몫과 명의를 지키는 기준입니다.",
    "돈을 지켜내는 기준": "계약, 명의, 정산, 보증에서 권리와 수령액을 지키는 기준입니다.",
    "재물 발생력": "금전 기회가 실제 수익으로 확정되는 재물 기반입니다.",
    "재물 형성력": "일, 거래, 보유 자산이 자기 재산의 기반으로 굳어지는 자리입니다.",
    "수익 전환력": "성과와 거래가 실제 입금으로 회수되는 자리입니다.",
    "자산 축적력": "수입이 부동산, 예금, 지분처럼 소유권 있는 자산으로 남는 자리입니다.",
    "공동 자금 관리력": "가족, 지인, 동업자와 얽힌 자금에서 명의와 몫을 지키는 기준입니다.",
    "공동재 관리력": "가족, 지인, 동업자와 얽힌 재산에서 명의와 권리를 지키는 기준입니다.",
    "수입 창출력": "직업 활동과 거래가 반복 수입으로 이어지는 자리입니다.",
    "축재력": "들어온 수입이 생활비 이후에도 자산으로 남는 자리입니다.",
    "지출 통제력": "생활비, 체면 비용, 관계 비용이 재산 형성을 흔들지 않게 하는 기준입니다.",
    "공동 자금 운영력": "가족, 지인, 동업자와 함께 다루는 돈에서 몫과 책임 범위를 지키는 기준입니다.",
    "공동자금 운영력": "가족, 지인, 동업자와 함께 다루는 돈에서 명의와 지분을 지키는 기준입니다.",
    "계약·문서 안정성": "계약서, 명의, 정산, 보증에서 권리와 수령액을 지켜내는 안정성입니다.",
    "계약·명의 안정성": "계약서, 명의, 정산, 보증에서 금전 권리를 지켜내는 안정성입니다.",
    "재주 수익화": "기술, 말, 기획, 콘텐츠가 단가와 보수로 바뀌는 자리입니다.",
    "성과 보상력": "본인이 만든 성과가 보수, 직책, 공식 인정으로 돌아오는 자리입니다.",
    "직업 성취력": "맡은 일이 결과와 이력으로 남아 직업적 위치를 올리는 자리입니다.",
    "성취 축적력": "맡은 일이 이력과 성과로 쌓여 직업적 위치를 올리는 자리입니다.",
    "직업적 성취의 그릇": "맡은 일을 성취와 이력으로 남기는 직업적 기반입니다.",
    "평가가 따라오는 자리": "성과가 조직과 시장에서 인정으로 돌아오는 자리입니다.",
    "조직 안에서 자리 잡는 힘": "조직의 기준 안에서 역할과 영향력을 확보하는 방식입니다.",
    "권한과 책임의 균형": "맡은 책임에 걸맞은 결정권과 보상을 확보하는 기준입니다.",
    "전문성으로 남는 힘": "시간이 지날수록 쉽게 대체되지 않는 직업 기반입니다.",
    "업무 평가력": "상사, 조직, 시장에서 실력과 성과가 공적으로 인정되는 기준입니다.",
    "평가·명예 전환력": "성과가 공식 평가와 사회적 인정으로 이어지는 자리입니다.",
    "권한·책임 균형도": "맡은 책임에 걸맞은 결정권과 보상 기준이 함께 붙는 자리입니다.",
    "권한 확보력": "맡은 책임에 걸맞은 결정권과 보상 기준을 확보해야 하는 자리입니다.",
    "전문 자산화": "전문성이 경력, 단가, 협상력으로 남는 자리입니다.",
    "인연 형성력": "새로운 만남과 호감이 실제 관계의 계기로 이어지는 자리입니다.",
    "호감 형성력": "상대의 관심이 실제 관계의 계기로 바뀌는 자리입니다.",
    "인연이 들어오는 길": "새로운 만남과 호감이 실제 관계로 번지는 접점입니다.",
    "애정이 표현되는 방식": "좋아하는 마음이 말과 행동으로 드러나는 방식입니다.",
    "관계가 오래 가는 힘": "감정이 깊어진 뒤 관계가 오래 유지되는 안정성입니다.",
    "결혼으로 이어지는 현실성": "연애가 실제 결혼 논의로 옮겨갈 수 있는 현실성입니다.",
    "함께 살아가는 기준": "생활비, 주거, 역할 분담을 함께 맞춰가는 기준입니다.",
    "애정 표현력": "좋아하는 마음을 상대가 알아들을 수 있게 드러내는 방식입니다.",
    "애정 표현성": "좋아하는 마음이 말과 행동으로 드러나는 방식입니다.",
    "관계 안정성": "감정이 깊어진 뒤에도 관계를 오래 유지합니다.",
    "관계 지속력": "감정이 깊어진 뒤에도 관계를 오래 유지합니다.",
    "끌림의 기준": "어떤 성향과 조건의 상대에게 마음이 움직이는지를 정리한 기준입니다.",
    "관계 진전력": "호감이 실제 만남과 약속으로 이어지는 자리입니다.",
    "오해 발생점": "말하지 않고 넘긴 감정이 관계의 불편함으로 돌아오는 지점입니다.",
    "결혼 연결력": "연애가 공식적인 약속과 결혼 논의로 이어지는 현실성입니다.",
    "결혼 안정성": "연애 감정이 실제 생활에서도 유지되는 안정성입니다.",
    "혼인 성향": "결혼을 감정의 결론으로 보는지, 생활과 책임의 결합으로 보는지에 대한 기준입니다.",
    "배우자상": "오래 맞는 상대의 성격, 생활 태도, 책임 감각을 정리한 기준입니다.",
    "생활 안정": "주거, 생활비, 역할 기준이 결혼 생활을 버티게 하는 현실 기반입니다.",
    "부부 재정": "명의, 생활비, 공동 자산을 부부 사이에서 정리하는 기준입니다.",
    "부부 갈등": "역할 불균형, 가족 개입, 돈 문제로 결혼 생활이 흔들리는 지점입니다.",
    "재물 규모 확장력": "고정 수입을 넘어 거래 단위와 자산 단위가 커집니다.",
    "승진·직함 가능성": "성과가 승진, 직함, 공식 책임자로 이어집니다.",
    "상대 신뢰 감별력": "호감 이후에도 상대의 말, 책임감, 생활 태도를 가려내는 기준입니다.",
    "가족 책임 경계력": "양가와 원가족 문제에서 맡을 책임과 끊어낼 책임을 구분하는 기준입니다.",
    "가족 변수": "양가와 원가족 문제가 결혼 생활에 들어오는 지점입니다.",
    "배우자 복": "배우자로 인해 얻는 안정과 함께 따라오는 부담의 크기입니다.",
    "혼인 위기 대응력": "돈, 가족, 주거, 역할 문제가 겹칠 때 결혼 생활을 지키는 기준입니다.",
    "유지와 위기": "결혼을 오래 유지하는 지점과 중간에 흔들리기 쉬운 계기입니다.",
    "결혼이 안정되는 힘": "결혼을 감정의 결론이 아니라 생활의 약속으로 지킵니다.",
    "생활 기반이 잡히는 방식": "주거, 생활비, 역할 기준이 결혼 생활의 기반으로 자리 잡는 방식입니다.",
    "가족 책임을 감당하는 힘": "양가와 원가족 문제에서 맡을 책임과 끊어낼 책임을 구분합니다.",
    "약속을 오래 지키는 힘": "결혼을 오래 유지하고 중간의 위기를 넘깁니다.",
    "생활 안정성": "주거, 생활비, 역할 분담이 결혼을 지탱하는 생활 기반입니다.",
  };
  return definitions[label] || "실제 생활에서 결과의 크기와 안정성을 가르는 세부 기준입니다.";
}

function renderJudgmentOverview(report) {
  const overview = judgmentOverviewContent(report);
  const payload = currentPayload || {};
  const chart = payload.chart || {};
  const request = payload.request || {};
  const inputLine = resultInputLine(request, chart);
  const summaryItems = overviewSummaryItems(report, inputLine);
  return `
    <section class="judgment-overview-panel">
      <div class="result-meta-row">
        <span>${escapeHtml(report.product_tier === "free" ? "무료 운세" : "프리미엄 운세")}</span>
        <button type="button" data-input-target="birth">정보 수정</button>
      </div>
      <p class="eyebrow">AI 사주 : 이현</p>
      <h2>${escapeHtml(primaryOverviewTitle(report))}</h2>
      <p>${escapeHtml(cleanOverviewText(overview || "사주 전체의 첫 결론이 분명합니다."))}</p>
      <div class="result-summary-strip">
        ${summaryItems.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
      </div>
    </section>
  `;
}

function overviewSummaryItems(report, inputLine) {
  const cards = Array.isArray(report.mobile_cards) ? report.mobile_cards : [];
  const strongest = strongestOverviewCard(cards);
  const caution = strongestCautionCard(cards);
  return [
    inputLine,
    strongest ? `최강 운세: ${domainDisplayLabel(strongest)}` : "최강 운세: 종합운",
    caution ? `주의 기준: ${cardCautionLine(caution)}` : "주의 기준: 뚜렷한 약점 적음",
  ];
}

function strongestOverviewCard(cards) {
  return cards
    .filter(Boolean)
    .sort((a, b) => Number(b.strength_score || 0) - Number(a.strength_score || 0))[0];
}

function strongestCautionCard(cards) {
  const ranked = cards
    .filter(Boolean)
    .map((card) => ({ card, severity: cautionSeverity(card) }))
    .sort((a, b) => {
      if (b.severity !== a.severity) {
        return b.severity - a.severity;
      }
      return Number(b.card?.strength_score || 0) - Number(a.card?.strength_score || 0);
    });
  return ranked[0]?.severity > 0 ? ranked[0].card : null;
}

function cautionSeverity(card) {
  const text = `${card?.caution_label || ""} ${(card?.judgment_axes || [])
    .map((axis) => `${axis.label || ""} ${axis.value || ""}`)
    .join(" ")}`;
  if (/주의|높음|강함/.test(text)) return 3;
  if (/보통|압박|부담|충돌|정산|손해|문제/.test(text)) return 2;
  if (/낮음|약세|평균 이하|보완 필요|주의 필요/.test(text)) return 1;
  return 0;
}

function renderFreeProfileSection(section, index) {
  const label = section.title || domainDisplayLabel(section);
  const headline = cleanCustomerSentence(section.headline || label);
  const strong = section.strong_axis || {};
  const watch = section.watch_axis || {};
  return `
    <section class="free-profile-section ${freeProfileDomainClass(section)}" id="profile-${index + 1}">
      <div class="free-profile-section-head">
        <div>
          <span>${escapeHtml(label)}</span>
          <h3>${escapeHtml(headline)}</h3>
        </div>
        <strong>${escapeHtml(section.grade || "확인")}</strong>
      </div>
      <p>${escapeHtml(premiumDisplayPoint(cleanCustomerSentence(section.summary || headline)))}</p>
      <dl class="free-profile-points">
        ${renderFreeProfilePoint("대표 강점", strong)}
        ${renderFreeProfilePoint("주의 기준", watch)}
      </dl>
      <p class="free-profile-premium-hint">${escapeHtml(cleanCustomerSentence(section.premium_hint || "프리미엄에서는 세부 기준이 더 선명하게 드러납니다."))}</p>
    </section>
  `;
}

function renderFreeProfilePoint(title, axis) {
  const label = premiumDisplayAxisLabel(axis?.label || "핵심 항목");
  return `
    <div>
      <dt>${escapeHtml(title)}</dt>
      <dd>
        <strong>${escapeHtml(label)} · ${escapeHtml(axis?.value || "확인")}</strong>
        <span>${escapeHtml(cleanCustomerSentence(axis?.definition || "이 항목은 실제 결과가 강하게 남는 생활 영역입니다."))}</span>
      </dd>
    </div>
  `;
}

function freeProfileDomainClass(section) {
  const domain = scoreDomain(section);
  return domain ? `domain-${domain}` : "";
}

function renderFreePremiumBridge(sections) {
  const strongest = strongestOverviewSection(sections);
  const caution = strongestWatchSection(sections);
  return `
    <section class="free-premium-bridge">
      <div>
        <p class="eyebrow">프리미엄에서 이어지는 내용</p>
        <h2>프리미엄에서는 주요 운세를 더 세밀하게 나눕니다.</h2>
      </div>
      <ul>
        <li>${escapeHtml(strongest ? `${strongest.title || "강한 운"}의 세부 내용` : "강한 운의 세부 내용")}</li>
        <li>${escapeHtml(caution ? `${caution.title || "주의 기준"}의 손실 지점` : "주의 기준")}</li>
        <li>성격, 인생 연도, 명예운, 대인관계운</li>
      </ul>
    </section>
  `;
}

function strongestOverviewSection(sections) {
  return [...(sections || [])].sort(
    (a, b) => Number(b?.strong_axis?.score || 0) - Number(a?.strong_axis?.score || 0),
  )[0];
}

function strongestWatchSection(sections) {
  return [...(sections || [])].sort(
    (a, b) => Number(a?.watch_axis?.score || 99) - Number(b?.watch_axis?.score || 99),
  )[0];
}

function resultInputLine(request, chart) {
  const formData = new FormData(form);
  const birthDate = request?.birthDate || formData.get("birthDate");
  const timeSelect = form.elements.birthTime;
  const timeLabel = timeSelect?.options?.[timeSelect.selectedIndex]?.text || "";
  const gender = request?.gender === "female" ? "여자" : request?.gender === "male" ? "남자" : "";
  return [birthDate, timeLabel, gender].filter(Boolean).join(" · ") || "입력 정보 확인";
}

function primaryOverviewTitle(report) {
  if (report.product_tier === "premium") {
    return "프리미엄 종합운";
  }
  return "무료 종합운";
}

function productCardSummary(card) {
  const headline = productCardHeadline(card).replace(/\.$/, "");
  const sentences = sentenceList(cleanReportCardSummary(card.summary))
    .filter((sentence) => !/[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]/.test(sentence))
    .filter((sentence) => !sentence.includes("기운"))
    .filter((sentence) => !sentence.includes("해입니다"))
    .filter((sentence) => !sentence.includes("시기입니다"))
    .filter((sentence) => sentence.replace(/\.$/, "") !== headline)
    .slice(0, 2);
  const text = sentences.join(" ");
  if (text) {
    return text;
  }
  return fallbackCardSummary(card);
}

function productCardHeadline(card) {
  const supplied = cleanReportCardHeadline(card.headline || "");
  if (supplied && !/한국 나이|올해|시기입니다|해입니다/.test(supplied)) {
    return supplied;
  }
  const domain = scoreDomain(card);
  const scoreText = String(card?.score_label || "");
  const veryStrong = scoreText.includes("매우 강함");
  const riskStrong = scoreText.includes("강한 주의") || scoreText.includes("주의 강함");
  if (domain === "money") {
    return veryStrong ? "재물 형성력이 매우 강합니다." : "재물 형성력은 낮은 편입니다.";
  }
  if (domain === "career") {
    return veryStrong ? "성취 축적력이 매우 강합니다." : "성취 축적력에 보완이 필요합니다.";
  }
  if (domain === "love") {
    return veryStrong ? "관계 형성력이 매우 강합니다." : "관계 형성력은 낮은 편입니다.";
  }
  if (domain === "marriage") {
    return veryStrong ? "결혼 연결력이 강하게 나타납니다." : "결혼 연결력에 보완이 필요합니다.";
  }
  if (riskStrong) {
    return "주의가 필요한 항목이 분명합니다.";
  }
  return cleanReportCardHeadline(card.headline);
}

function fallbackCardSummary(card) {
  const domain = scoreDomain(card);
  if (domain === "money") {
    return "재물 형성력이 강합니다. 공동 자금에서는 계약 안정성이 승부처입니다.";
  }
  if (domain === "career") {
    return "성취 축적력과 평가·명예 전환력이 강합니다. 권한 확보력이 직업 만족도를 가릅니다.";
  }
  if (domain === "love") {
    return "인연 형성력과 호감 반응이 강합니다. 감정 조율력이 관계 지속성을 가릅니다.";
  }
  if (domain === "marriage") {
    return "결혼 연결력과 생활 안정이 강합니다. 생활 기반이 결혼의 장기 유지력을 가릅니다.";
  }
  return cleanCustomerSentence(card.summary || card.headline);
}

function cardCoreLine(card) {
  const supplied = cleanCustomerSentence(card.action_label || "");
  if (supplied && !supplied.includes("확인해야")) {
    return supplied.replace(/\.$/, "");
  }
  const domain = scoreDomain(card);
  const scoreText = String(card?.score_label || "");
  if (domain === "money") {
    return scoreText.includes("매우 강함") ? "성과 보상형 재물운" : "공동 자금·계약 관리";
  }
  if (domain === "career") {
    return scoreText.includes("매우 강함") ? "성취·평가형 직업운" : "권한·책임 균형";
  }
  if (domain === "love") {
    return scoreText.includes("매우 강함") ? "안정성 강한 관계운" : "감정 조율";
  }
  if (domain === "marriage") {
    return scoreText.includes("매우 강함") ? "생활 안정형 결혼운" : "생활 기반 안정";
  }
  return cleanCustomerSentence(card.action_label || card.headline);
}

function cardCautionLine(card) {
  return cleanCustomerSentence(card.caution_label || "주의점").replace(/\.$/, "");
}

function premiumPromptText(card) {
  const domain = scoreDomain(card);
  if (domain === "money") {
    return "수입, 축재, 공동 자금, 계약 안정성까지 나누어 보여드립니다.";
  }
  if (domain === "career") {
    return "성취가 평가와 권한으로 이어지는지를 세부 항목으로 보여드립니다.";
  }
  if (domain === "love") {
    return "인연의 시작, 표현 방식, 관계 지속성을 나누어 보여드립니다.";
  }
  if (domain === "marriage") {
    return "배우자상, 생활 안정, 가정 기반, 결혼 시기를 나누어 보여드립니다.";
  }
  return "세부 항목을 더 좁혀 보여드립니다.";
}

function cleanOverviewText(value) {
  return cleanCustomerText(value)
    .replaceAll("올해는 중요한 결론이 비교적 분명하게 드러납니다.", "사주 전체의 첫 결론이 분명합니다.")
    .replaceAll("사주 전체에서 중요한 결론이 비교적 분명하게 드러납니다.", "사주 전체의 첫 결론이 분명합니다.")
    .replaceAll("올해 먼저 드러나는 운세", "사주 전체의 첫 결론")
    .replace(/^올해는\s*/, "사주 전체를 보면 ");
}

function cleanReportCardSummary(value) {
  return cleanCustomerText(value)
    .replace(/당신의 한국 나이\s*\d+세 전후\s*([가-힣· ]+?)은/g, "당신의 $1은")
    .replace(/한국 나이\s*\d+세 전후\s*/g, "")
    .replace(/수입 규모가 커지는 해입니다\./g, "수입 규모가 분명하게 늘어납니다.")
    .replace(/직업운이 강한 해입니다\./g, "직업운이 강하게 나타납니다.")
    .replace(/인연이 움직이는 해입니다\./g, "인연의 움직임이 분명합니다.")
    .replace(/결혼 이야기가 움직이는 해입니다\./g, "결혼 이야기가 구체적으로 움직입니다.")
    .replace(/올해 먼저/g, "먼저")
    .replace(/올해는\s*/g, "사주 전체를 보면 ");
}

function cleanReportCardHeadline(value) {
  const text = cleanCustomerSentence(value);
  const fixed = {
    "돈의 규모가 커지지만 관리 부담이 따르는 시기입니다.": "돈의 규모가 늘고 관리 부담도 따라옵니다.",
    "맡는 책임이 커지며 직업운이 강한 시기입니다.": "맡는 책임이 늘고 직업운도 강합니다.",
    "끌림은 생기지만 속도 차이가 드러나는 시기입니다.": "끌림은 생기지만 관계의 속도 차이가 분명합니다.",
    "결혼 이야기가 생활비 문제로 이어지는 시기입니다.": "결혼 이야기는 생활비 문제와 함께 결혼 의제가 됩니다.",
  };
  if (fixed[text]) {
    return fixed[text];
  }
  return text
    .replace(/(.+)하는 시기입니다\.$/, "$1합니다.")
    .replace(/(.+)되는 시기입니다\.$/, "$1됩니다.")
    .replace(/(.+) 시기입니다\.$/, "$1 운이 강하게 나타납니다.");
}

function cleanTimingLabel(value) {
  const text = cleanCustomerLabel(value);
  if (!text || text === "올해" || /^\d{4}-\d{2}-\d{2}/.test(text)) {
    return "전체 운세";
  }
  return text.replace(/한국 나이\s*\d+세 전후/g, "종합 기준");
}

function reportCardGrade(card) {
  const strength = Number(card?.strength_score || 0);
  if (strength >= 90) {
    return "최상위";
  }
  if (strength >= 75) {
    return "상위";
  }
  if (strength >= 60) {
    return "양호";
  }
  const text = String(card?.score_label || "");
  if (text.includes("매우 강함")) {
    return "강한 운";
  }
  if (text.includes("주의 강함") || text.includes("강한 주의")) {
    return "주의 필요";
  }
  if (text.includes("강함")) {
    return "상위";
  }
  return "확인";
}

function renderPremiumSections(report) {
  const sections = report.premium_sections || [];
  if (!sections.length) {
    panels.premium.innerHTML = `
      <section class="premium-teaser">
        <div class="premium-teaser-head">
          <p class="eyebrow">프리미엄 운세</p>
        <h2>프리미엄은 성격과 인생 구간까지 세밀하게 나눕니다.</h2>
        <p>성격, 인생 구간별 운세와 영역별 세부 지표가 추가됩니다.</p>
        </div>
        <button class="entry-button is-premium" type="button" data-upgrade="true">프리미엄 운세 보기</button>
      </section>
    `;
    return;
  }
  panels.premium.innerHTML = renderPremiumResultPage(report, sections);
}

function renderPremiumResultPage(report, sections) {
  return `
    <section class="premium-result-shell premium-mobile-result">
      ${renderPremiumInputReturnBar()}
      ${renderPremiumMobileHero(report, sections)}
      ${renderPremiumSectionIndex(report, sections)}
      ${renderPremiumDomainShowcase(report, sections)}
      ${renderPremiumResultFooter()}
    </section>
  `;
}

function renderPremiumInputReturnBar() {
  return `
    <div class="premium-input-return-bar">
      <button class="input-return-button" type="button" data-input-target="birth">출생 정보 수정</button>
    </div>
  `;
}

function renderPremiumMobileHero(report, sections) {
  const title = "사주 분석 결과";
  const body = "성격, 재물, 직업, 연애와 결혼, 인생 구간을 차례로 정리했습니다.";
  return `
    <section class="premium-mobile-hero" aria-label="프리미엄 종합 결론">
      <div>
        <p class="eyebrow">프리미엄 종합운</p>
        <h1>${escapeHtml(title)}</h1>
        <p>${escapeHtml(body)}</p>
      </div>
      <div class="premium-mobile-hero-meta" aria-label="분석 기준">
        <span>${escapeHtml(premiumRequestLine())}</span>
      </div>
      <a class="service-blog-button premium-blog-button is-top" href="https://place-leehyeon.tistory.com/" target="_blank" rel="noopener noreferrer">
        사주명리 공간 : 이현 블로그
      </a>
    </section>
  `;
}

function renderPremiumMobileCoreBoard(report, sections) {
  const summary = premiumProfileSummary(report);
  const profileType = premiumDisplayProfileType(summary.profile_type || "");
  const headline =
    firstSentences(cleanPremiumDisplayText(summary.headline || ""), 1) ||
    firstSentences(cleanPremiumDisplayText(summary.summary || ""), 2) ||
    premiumConclusionSummary(report, sections);
  const primary = premiumSummaryPrimarySignal(summary, sections);
  const management = premiumSummaryManagementSignal(summary, sections);
  const signals = [primary, management].filter(Boolean);
  if (profileType || headline || signals.length) {
    return `
      <section class="premium-mobile-core-board premium-mobile-verdict-board" aria-label="프리미엄 핵심 결과">
        <article class="premium-verdict-main-card">
          <span>대표 결과</span>
          <strong>${escapeHtml(profileType || premiumMainConclusion(report, sections))}</strong>
          ${headline ? `<p>${escapeHtml(headline)}</p>` : ""}
        </article>
        ${
          signals.length
            ? `<div class="premium-verdict-signal-grid">
                ${signals.map(renderPremiumVerdictSignalCard).join("")}
              </div>`
            : ""
        }
      </section>
    `;
  }

  const personality = premiumFindSection(sections, "personality");
  const strongest = premiumStrongestSectionFromReport(report, sections);
  const risk = premiumPrimaryRiskSection(sections, report);
  const personalityType =
    cleanCustomerLabel(personality?.section_profile?.type || "") ||
    premiumDisplayPoint(premiumSectionFocus(personality)) ||
    "성격 기준";
  const strongestTitle = strongest ? premiumNavTitle(strongest) : "강한 운";
  const strongestDetail = strongest ? premiumDisplayPoint(premiumSectionFocus(strongest)) : "";
  const riskTitle = risk ? premiumNavTitle(risk) : "주의 지점";
  const riskDetail = risk ? premiumDisplayPoint(premiumSectionRisk(risk)) : "";
  const items = [
    {
      label: "성격 기준",
      value: personalityType,
      detail: "판단 방식과 관계 태도를 먼저 봅니다.",
      tone: "profile",
    },
    {
      label: "가장 강한 운",
      value: strongestTitle,
      detail: strongestDetail || "가장 두드러지는 운세 영역입니다.",
      tone: "strong",
    },
    {
      label: "주의 지점",
      value: riskTitle,
      detail: riskDetail || "결과를 흔들 수 있는 지점입니다.",
      tone: "watch",
    },
  ];
  return `
    <section class="premium-mobile-core-board" aria-label="프리미엄 핵심 결과">
      ${items
        .map(
          (item) => `
            <article class="premium-mobile-core-card is-${escapeHtml(item.tone)}">
              <span>${escapeHtml(item.label)}</span>
              <strong>${escapeHtml(item.value)}</strong>
              <p>${escapeHtml(item.detail)}</p>
            </article>
          `,
        )
        .join("")}
    </section>
  `;
}

function premiumSummaryPrimarySignal(summary, sections) {
  const source = summary?.primary || {};
  const panel = premiumSummaryPanel(summary, "primary");
  const fallback = premiumStrongestSectionFromReport({ premium_profile_summary: summary }, sections) || null;
  if (!source.domain_label && !source.family && !source.label && !source.value && !fallback) {
    return null;
  }
  const fallbackTitle = fallback ? premiumNavTitle(fallback) : "";
  const fallbackFocus = fallback ? premiumSectionFocus(fallback) : "";
  const panelTitle = cleanCustomerLabel(panel?.title || "");
  const label = premiumDisplaySignalLabel(source.domain_label || panelTitle || fallbackTitle || "강한 운");
  const title = cleanCustomerLabel(source.family || source.label || fallbackFocus || "");
  const value = premiumSummarySignalValue(source);
  const detail =
    cleanPremiumDisplayText(panel?.detail || "") ||
    cleanPremiumDisplayText(source.caption || "") ||
    (fallback ? firstSentences(cleanPremiumDisplayText(premiumFinalStrengthSentence(fallback)), 1) : "");
  return premiumVerdictSignal("강점", label, cleanPremiumDisplayText(panel?.verdict || "") || premiumCompactSignalValue(title, value), detail, "strong");
}

function premiumSummaryManagementSignal(summary, sections) {
  const source = summary?.management || {};
  const panel = premiumSummaryPanel(summary, "management");
  const fallback = premiumPrimaryRiskSection(sections, { premium_profile_summary: summary }) || null;
  if (!source.domain_label && !source.family && !source.label && !source.value && !fallback) {
    return null;
  }
  const fallbackTitle = fallback ? premiumNavTitle(fallback) : "";
  const fallbackRisk = fallback ? premiumSectionRisk(fallback) : "";
  const panelTitle = cleanCustomerLabel(panel?.title || "");
  const label = premiumDisplaySignalLabel(source.domain_label || panelTitle || fallbackTitle || "주의 지점");
  const title = cleanCustomerLabel(source.label || source.family || fallbackRisk || "");
  const value = premiumSummarySignalValue(source);
  const detail =
    cleanPremiumDisplayText(panel?.detail || "") ||
    cleanPremiumDisplayText(source.caption || "") ||
    (fallback ? firstSentences(cleanPremiumDisplayText(premiumFinalRiskSentence(fallback)), 1) : "");
  return premiumVerdictSignal("주의 지점", label, cleanPremiumDisplayText(panel?.verdict || "") || premiumCompactSignalValue(title, value), detail, "watch");
}

function premiumSummaryTimingSignal(summary, sections) {
  const timing = summary?.timing || {};
  const section = premiumFindSection(sections, "timing");
  const good = cleanCustomerLabel(timing.good || premiumTimingSummaryValue(section) || "");
  const caution = cleanCustomerLabel(timing.caution || "");
  const value = timingYearHeadlineItems(good).slice(0, 2).join(" · ") || good;
  const detail = caution ? `주의 연도 ${timingYearHeadlineItems(caution).slice(0, 2).join(" · ")}` : "20세부터 79세까지의 주요 연도";
  return premiumVerdictSignal("상승 연도", "20세~79세", value, detail, "timing");
}

function premiumSummaryPanel(summary, role) {
  const panels = Array.isArray(summary?.profile_panels) ? summary.profile_panels : [];
  return panels.find((panel) => panel?.role === role) || null;
}

function premiumDisplayProfileType(value) {
  return cleanCustomerLabel(value || "")
    .replaceAll("사회 평가·관계 안정형", "평판·인연 장기형")
    .replaceAll("관계 안정·사회 평가형", "인연·평판 장기형")
    .replaceAll("관계 안정·평판 축적형", "인연·평판 장기형")
    .replaceAll("사회 평가형", "평판 장기형")
    .replaceAll("평판 축적형", "평판 장기형")
    .replaceAll("초년 기준형입니다.", "초년부터 자기 기준이 분명한 편입니다.")
    .replaceAll("공식 책임형입니다.", "공식적인 책임을 맡을수록 이름이 드러납니다.")
    .replaceAll("신뢰 누적형입니다.", "오래 쌓은 신뢰가 결정적인 도움으로 돌아옵니다.")
    .replaceAll("연도 사건 집중형", "좋은 해와 주의할 해가 뚜렷한 사주")
    .replaceAll("공식 평판형입니다.", "공식적인 책임을 맡을수록 이름이 드러납니다.")
    .replaceAll("신뢰 축적형입니다.", "오래 쌓은 신뢰가 결정적인 도움으로 돌아옵니다.")
    .replaceAll("공식 평가, 추천, 직책 상승이 분명하게 따라옵니다.", "추천과 직책 상승이 공식 평가로 이어집니다.")
    .replaceAll("공식 평가가 분명해집니다.", "공식 평가가 뚜렷해집니다.")
    .replaceAll("직함과 공식 평가가 분명합니다.", "직함과 공식 평가가 또렷하게 남습니다.")
    .replaceAll("20세~79세 전체에서 좋은 연도와 주의 연도가 뚜렷합니다.", "20세부터 79세까지 상승 연도와 주의 연도가 분명하게 드러납니다.")
    .replaceAll("좋은 분야는", "좋은 해가 강한 분야는")
    .replaceAll("주의 분야는", "주의가 필요한 분야는")
    .replaceAll("공식 책임형", "공식 평판형")
    .replaceAll("신뢰 누적형", "신뢰 축적형")
    .replaceAll("성과 수익형", "성과가 수입으로 돌아오는 사주")
    .replaceAll("전문성 확립형", "전문성으로 경력이 남는 사주")
    .replaceAll("결혼 현실화형", "연애가 결혼 준비로 이어지는 사주")
    .replaceAll("초년 기준형", "초년부터 자기 기준이 선명한 사주")
    .replaceAll("기준 관리형", "기준 확립형")
    .replaceAll("성취 보상형", "성취 보상 확정형")
    .trim();
}

function premiumDisplaySignalLabel(value) {
  return cleanCustomerLabel(value || "")
    .replaceAll("연애·결혼운", "관계")
    .replaceAll("재물운", "재물")
    .replaceAll("직업운", "직업")
    .replaceAll("명예운", "명예")
    .trim();
}

function premiumCompactSignalValue(title, value) {
  const cleanTitle = cleanCustomerLabel(title || "");
  const cleanValue = premiumSignalGradeLabel(value);
  if (/공동 자금|재물에 얽히는 사람 문제|명의|지분/.test(cleanTitle) && /낮음|주의|약함/.test(cleanValue)) {
    return "지분·명의 안정성 주의";
  }
  if (/관계 안정|관계 지속|관계가 오래/.test(cleanTitle) && /최상|강세|강함/.test(cleanValue)) {
    return "인연 지속 최상";
  }
  if (/공식 평가|평판|명예/.test(cleanTitle) && /최상|강세|강함/.test(cleanValue)) {
    return "평판 상승 강세";
  }
  if (cleanTitle && cleanValue) {
    return `${cleanTitle} ${cleanValue}`;
  }
  return cleanTitle || cleanValue;
}

function premiumSignalGradeLabel(value) {
  const text = cleanCustomerLabel(value || "");
  if (!text) return "";
  return text
    .replaceAll("주의 필요", "낮음")
    .replaceAll("보완 필요", "낮음")
    .replaceAll("취약", "낮음")
    .replaceAll("평균권", "보통")
    .replaceAll("중상위권", "우세")
    .replaceAll("상위권", "강세")
    .replaceAll("최상위권", "최상")
    .replaceAll("좋음", "우세")
    .replaceAll("양호", "우세");
}

function premiumSummarySignalValue(source) {
  const value = premiumDisplayPoint(source?.value || "");
  const score = Number(source?.score);
  if (value) {
    return value;
  }
  if (Number.isFinite(score)) {
    return premiumMetricValueFromScore(score);
  }
  return "";
}

function premiumVerdictSignal(kicker, label, value, detail, tone) {
  const cleanValue = cleanPremiumDisplayText(value || "");
  if (!cleanValue && !detail) {
    return null;
  }
  return {
    kicker,
    label,
    value: cleanValue || cleanPremiumDisplayText(detail || ""),
    detail: cleanPremiumDisplayText(detail || ""),
    tone,
  };
}

function renderPremiumVerdictSignalCard(item) {
  return `
    <article class="premium-verdict-signal-card is-${escapeHtml(item.tone || "neutral")}">
      <span>${escapeHtml(item.kicker)}</span>
      <strong>${escapeHtml(item.label)}</strong>
      <b>${escapeHtml(item.value)}</b>
      ${item.detail ? `<p>${escapeHtml(item.detail)}</p>` : ""}
    </article>
  `;
}

function premiumProductContract(report) {
  const contract = report?.premium_profile_contract;
  return contract && typeof contract === "object" ? contract : {};
}

function premiumSurfaceSection(report, key) {
  const sections = premiumProductContract(report)?.surface_sections;
  const section = sections && typeof sections === "object" ? sections[key] : null;
  return section && typeof section === "object" ? section : {};
}

function premiumProfileSummary(report) {
  const summary = report?.premium_profile_summary;
  return summary && typeof summary === "object" ? summary : {};
}

function renderPremiumSectionIndex(report, sections) {
  const ordered = premiumDomainOrder(premiumVisibleDomainSections(sections));
  if (!ordered.length) {
    return "";
  }
  const surface = premiumSurfaceSection(report, "section_index");
  const sectionIndexTitle = cleanPremiumDisplayText(surface.title || "");
  const sectionIndexDisplayTitle = sectionIndexTitle && !sectionIndexTitle.includes("보고 싶은")
    ? sectionIndexTitle
    : "프리미엄 구성";
  return `
    <section class="premium-section-index is-compact" aria-label="프리미엄 빠른 이동">
      <div class="premium-section-index-head">
        <div>
          <p class="eyebrow">${escapeHtml(surface.eyebrow || "프리미엄 구성")}</p>
          <h2>${escapeHtml(sectionIndexDisplayTitle)}</h2>
        </div>
      </div>
      <div class="premium-section-index-grid">
        ${ordered.map((section, index) => renderPremiumSectionIndexCard(section, index)).join("")}
      </div>
    </section>
  `;
}

function premiumVisibleDomainSections(sections) {
  return (Array.isArray(sections) ? sections : []).filter((section) => {
    const domain = premiumSectionDomain(section);
    return domain !== "default" && domain !== "timing";
  });
}

function renderPremiumSectionIndexCard(section, index) {
  const domain = premiumSectionDomain(section);
  const title = premiumSectionIndexTitle(section);
  const role = premiumSectionIndexRole(domain, title);
  const point = premiumSectionIndexPoint(section);
  const teaser = point || role;
  const targetId = `premium-section-${index + 1}`;
  return `
    <button class="premium-section-index-card domain-${escapeHtml(domain)}" type="button" data-scroll-target="${escapeHtml(targetId)}" aria-label="${escapeHtml(`${title} ${role}`)}">
      <span>${String(index + 1).padStart(2, "0")}</span>
      <div>
        <strong>${escapeHtml(title)}</strong>
        ${teaser ? `<p>${escapeHtml(teaser)}</p>` : ""}
      </div>
    </button>
  `;
}

function premiumSectionIndexTitle(section) {
  const domain = premiumSectionDomain(section);
  const labels = {
    personality: "성격",
    money: "재물",
    career: "직업",
    love: "연애",
    marriage: "결혼",
    timing: "주요 연도",
    life: "인생 구간",
    honor: "명예운",
    social: "대인관계",
  };
  return labels[domain] || premiumNavTitle(section);
}

function premiumSectionIndexRole(domain, title) {
  const roles = {
    personality: "기질과 판단 기준",
    money: "재물 그릇과 자산화",
    career: "직함과 평가",
    love: "연애 감각과 표현",
    marriage: "배우자와 생활 기반",
    timing: "좋은 연도·주의 연도",
    life: "초년·중년·말년",
    honor: "명예와 공식 평판",
    social: "사람 운과 조력",
  };
  return roles[domain] || `${title}의 핵심 운세`;
}

function premiumSectionIndexPoint(section) {
  const domain = premiumSectionDomain(section);
  if (domain === "timing") {
    return premiumTimingSummaryValue(section) || "주요 연도";
  }
  const profileType = cleanCustomerLabel(section?.section_profile?.type || "");
  if (profileType) {
    return premiumSectionIndexPointLabel(domain, profileType);
  }
  const focus = premiumDisplayPoint(premiumSectionFocus(section));
  return focus || premiumDomainBadge(section);
}

function premiumSectionIndexPointLabel(domain, value) {
  const text = cleanCustomerLabel(value || "");
  if (!text) {
    return "";
  }
  if (domain === "personality") {
    return text === "성격형" ? "성격 핵심" : text;
  }
  return text;
}

function premiumProfileIntroTitle(summary, surface) {
  const headline = cleanPremiumDisplayText(summary?.headline || "");
  if (headline) {
    return headline;
  }
  return cleanPremiumDisplayText(surface?.title || "") || "첫 결론부터 확인하는 프리미엄 운세입니다.";
}

function premiumProfileIntroBody(summary, surface) {
  const body = cleanPremiumDisplayText(summary?.summary || "");
  if (body) {
    return body;
  }
  return (
    cleanPremiumDisplayText(surface?.body || "") ||
    "성격, 강한 운세, 주의점, 주요 연도를 한 화면에서 먼저 정리합니다."
  );
}

function renderPremiumProfileIntro(report, sections) {
  const summary = premiumProfileSummary(report);
  const profilePanels = Array.isArray(report?.premium_profile_panels)
    ? report.premium_profile_panels.filter((item) => item?.title && (item?.verdict || item?.body))
    : [];
  const summaryPanels = Array.isArray(summary.profile_panels)
    ? summary.profile_panels.filter((item) => item?.title && (item?.verdict || item?.body))
    : [];
  const personality = premiumFindSection(sections, "personality");
  const strongest = premiumStrongestSectionFromReport(report, sections);
  const risk = premiumPrimaryRiskSection(sections, report);
  const timing = premiumFindSection(sections, "timing");
  const basis = premiumCheckpointValue(personality?.checkpoints || [], "삶의 기준");
  const profileType = personality?.section_profile?.type || (basis ? premiumPersonalityBasisText(basis) : "성격 분석");
  const strongestText = strongest ? `${premiumNavTitle(strongest)} · ${premiumDisplayPoint(premiumSectionFocus(strongest))}` : "강한 운세";
  const riskText = risk ? `${premiumNavTitle(risk)} · ${premiumDisplayPoint(premiumSectionRisk(risk))}` : "주의점";
  const timingText = premiumTimingSummaryValue(timing) || "인생 연도";
  const strongestCopy = premiumProfileSnapshotCopy(premiumSectionDomain(strongest), "primary");
  const riskCopy = premiumProfileSnapshotCopy(premiumSectionDomain(risk), "management");
  const items = [
    {
      title: "성격 유형·판단 기준",
      body: profileType,
      meta: "판단 기준과 감정 반응",
    },
    {
      title: strongestCopy.title,
      body: strongestText,
      meta: strongestCopy.caption,
    },
    {
      title: riskCopy.title,
      body: riskText,
      meta: riskCopy.caption,
    },
    {
      title: "인생 연도",
      body: timingText,
      meta: "20세~79세 기준",
    },
  ];
  const displayItems = profilePanels.length ? profilePanels : summaryPanels.length ? summaryPanels : items;
  const surface = premiumSurfaceSection(report, "executive_summary");
  const introTitle = premiumProfileIntroTitle(summary, surface);
  return `
    <section class="premium-executive-summary" aria-label="프리미엄 결과 요약">
      <div class="premium-executive-title">
        <p class="eyebrow">${escapeHtml(surface.eyebrow || "종합 요약")}</p>
        <h2>${escapeHtml(introTitle)}</h2>
        ${renderPremiumProfileSignature(summary)}
      </div>
      ${renderPremiumProfileSnapshot(displayItems)}
    </section>
  `;
}

function premiumProfileSnapshotCopy(domain, role) {
  if (role === "management") {
    const labels = {
      money: { title: "재물 주의점", caption: "재물 관리 지점" },
      career: { title: "직업 주의점", caption: "경력 손실 지점" },
      honor: { title: "명예 주의점", caption: "평판 검증 지점" },
      love: { title: "관계 주의점", caption: "관계가 흔들리는 지점" },
      marriage: { title: "결혼 주의점", caption: "부담이 올라오는 지점" },
      social: { title: "대인 주의점", caption: "부담이 붙는 관계" },
      life: { title: "생애 주의점", caption: "흔들리기 쉬운 구간" },
    };
    return labels[domain] || { title: "주의점", caption: "반드시 볼 지점" };
  }
  const labels = {
    money: { title: "재물 강점", caption: "자산화 강점" },
    career: { title: "직업 강점", caption: "평가 확보 지점" },
    honor: { title: "명예 강점", caption: "공식 인정 지점" },
    love: { title: "관계 강점", caption: "관계 지속 지점" },
    marriage: { title: "결혼 강점", caption: "생활이 안정되는 자리" },
    social: { title: "대인 강점", caption: "오래 남는 관계" },
    life: { title: "생애 강점", caption: "강하게 드러나는 구간" },
  };
  return labels[domain] || { title: "강한 운세", caption: "주요 강점" };
}

function renderPremiumProfileSignature(summary) {
  if (!summary || typeof summary !== "object") {
    return "";
  }
  const primary = summary.primary || {};
  const management = summary.management || {};
  const timing = summary.timing || {};
  const items = [
    {
      label: "유형",
      value: cleanCustomerLabel(summary.profile_type || ""),
      detail: cleanPremiumDisplayText(summary.headline || ""),
    },
    {
      label: "강점",
      value: cleanCustomerLabel(primary.family || primary.domain_label || ""),
      detail: [primary.label, premiumDisplayPoint(primary.value)].filter(Boolean).join(" · "),
    },
    {
      label: "주의",
      value: cleanCustomerLabel(management.family || management.domain_label || ""),
      detail: [management.label, premiumSnapshotDisplayValue(management, "watch")].filter(Boolean).join(" · "),
      tone: "watch",
    },
    {
      label: "연도",
      value: cleanCustomerLabel(String(timing.good || "").split("·")[0] || ""),
      detail: cleanCustomerLabel(String(timing.caution || "").split("·")[0] || ""),
    },
  ].filter((item) => item.value || item.detail);
  if (!items.length) {
    return "";
  }
  return `
    <div class="premium-profile-signature" aria-label="프리미엄 핵심 식별표">
      ${items
        .map(
          (item) => `
            <section class="${item.tone === "watch" ? "is-watch" : ""}">
              <span>${escapeHtml(item.label)}</span>
              ${item.value ? `<strong>${escapeHtml(item.value)}</strong>` : ""}
              ${item.detail ? `<p>${escapeHtml(item.detail)}</p>` : ""}
            </section>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderPremiumProfileSnapshot(items) {
  const source = Array.isArray(items) ? items.filter((item) => item?.title && (item?.verdict || item?.body)) : [];
  if (!source.length) {
    return "";
  }
  return `
    <div class="premium-profile-snapshot" aria-label="프리미엄 핵심 운세">
      ${source
        .slice(0, 4)
        .map((item, index) => renderPremiumProfileSnapshotCard(item, index))
        .join("")}
    </div>
  `;
}

function renderPremiumProfileSnapshotCard(item, index) {
  const score =
    item?.score !== null && item?.score !== undefined && item?.score !== "" && Number.isFinite(Number(item.score))
      ? Math.max(0, Math.min(100, Number(item.score)))
      : null;
  const tone = item.tone || item.role || "neutral";
  const metric = item.metric_label || item.value || score !== null;
  const caption = premiumDisplayPoint(item.caption || item.meta || "");
  const metricLabel = premiumDisplayPoint(item.metric_label || "");
  const verdict = premiumDisplayPoint(item.verdict || item.body || "");
  const detail = premiumDisplayPoint(item.detail || "");
  const metricValue = premiumSnapshotDisplayValue(item, tone);
  const isTiming = item.role === "timing" || item.domain === "timing" || item.title === "인생 연도";
  return `
    <article class="premium-profile-snapshot-card is-${escapeHtml(tone)}${isTiming ? " is-timing" : ""}">
      <header>
        <span>${String(index + 1).padStart(2, "0")}</span>
        <strong>${escapeHtml(item.title)}</strong>
      </header>
      ${caption ? `<p class="premium-profile-snapshot-caption">${escapeHtml(caption)}</p>` : ""}
      ${
        metric
          ? `<div class="premium-profile-snapshot-metric">
              ${metricLabel ? `<b>${escapeHtml(metricLabel)}</b>` : ""}
              ${metricValue ? `<i>${escapeHtml(metricValue)}</i>` : ""}
              ${score !== null ? `<mark>${score}점</mark>` : ""}
            </div>`
          : ""
      }
      ${isTiming ? renderPremiumProfileTimingSnapshot(verdict, detail) : `<h3>${escapeHtml(verdict)}</h3>`}
      ${score !== null ? `<div class="premium-profile-snapshot-bar"><em style="width:${score}%"></em></div>` : ""}
      ${!isTiming ? renderPremiumProfileSnapshotDetail(detail) : ""}
    </article>
  `;
}

function renderPremiumProfileSnapshotDetail(detail) {
  const sentences = sentenceList(detail).slice(0, 3);
  if (sentences.length >= 2) {
    return `
      <ul class="premium-profile-snapshot-detail-list">
        ${sentences.map((sentence) => `<li>${escapeHtml(sentence)}</li>`).join("")}
      </ul>
    `;
  }
  return detail ? `<p class="premium-profile-snapshot-detail">${escapeHtml(detail)}</p>` : "";
}

function renderPremiumProfileTimingSnapshot(goodLine, cautionLine) {
  const good = premiumTimingSnapshotEntries(goodLine, "좋은 연도");
  const caution = premiumTimingSnapshotEntries(cautionLine, "주의 연도");
  return `
    <div class="premium-profile-year-lines">
      ${renderPremiumProfileYearLine("좋은 연도", good, "good")}
      ${renderPremiumProfileYearLine("주의 연도", caution, "watch")}
    </div>
  `;
}

function premiumTimingSnapshotEntries(value, label) {
  const cleaned = cleanPremiumDisplayText(value || "")
    .replace(new RegExp(`^${label}:\\s*`), "")
    .trim();
  if (!cleaned) {
    return [];
  }
  return cleaned
    .split("·")
    .map((part) => part.trim())
    .filter(Boolean)
    .slice(0, 3)
    .map((part) => {
      const match = part.match(/^(\d{4}년)\s*(.*)$/);
      return {
        year: match ? match[1] : "",
        title: match ? match[2].trim() : part,
      };
    });
}

function renderPremiumProfileYearLine(label, entries, tone) {
  if (!entries.length) {
    return "";
  }
  return `
    <section class="premium-profile-year-line is-${escapeHtml(tone)}">
      <strong>${escapeHtml(label)}</strong>
      <div class="premium-profile-year-tags">
        ${entries
          .map(
            (entry) => `
              <span>
                ${entry.year ? `<b>${escapeHtml(entry.year)}</b>` : ""}
                <em>${escapeHtml(entry.title)}</em>
              </span>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function premiumSnapshotDisplayValue(item, tone = "neutral") {
  const isWatch =
    tone === "watch" ||
    tone === "risk" ||
    tone === "management" ||
    item?.role === "management" ||
    item?.tone === "watch" ||
    item?.tone === "risk";
  return premiumSignatureDisplayValue(
    {
      value: item?.value,
      score: item?.score,
    },
    isWatch ? "watch" : "neutral",
  );
}

function renderPremiumResultHeader(report, sections) {
  const sectionCount = Array.isArray(sections) ? sections.length : 0;
  return `
    <header class="premium-result-header">
      <div>
        <p class="eyebrow">AI 사주 : 이현 프리미엄</p>
        <h2>프리미엄 종합운</h2>
        <p>성향부터 주요 운세까지 한 번에 확인합니다.</p>
      </div>
      <div class="premium-result-header-meta" aria-label="프리미엄 결과 정보">
        <span>${sectionCount}개 항목</span>
        <span>${escapeHtml(premiumRequestLine())}</span>
      </div>
      <div class="premium-result-actions">
        <button type="button" data-input-target="birth">정보 수정</button>
        <button type="button" data-view-target="basis">명식표 보기</button>
      </div>
    </header>
  `;
}

function premiumRequestLine() {
  const request = currentPayload?.request || {};
  const form = document.querySelector("#birth-form");
  const dateText = formatPremiumBirthDate(
    request.birthDate || request.birth_date || request.birth_date_text || form?.elements?.birthDate?.value || "",
  );
  const timeText = premiumTimeLabel(
    request.birthTime || request.birth_time || request.time_branch || form?.elements?.birthTime?.value || "",
  );
  const genderValue = request.gender || form?.elements?.gender?.value || "";
  const genderText = genderValue === "female" ? "여자" : genderValue === "male" ? "남자" : "";
  const parts = [dateText, timeText, genderText].filter(Boolean);
  return parts.length ? `${parts.join(" · ")} 기준` : "입력한 출생 정보 기준";
}

function formatPremiumBirthDate(value) {
  const text = String(value || "").replace(/\D/g, "");
  if (text.length === 8) {
    return `${text.slice(0, 4)}.${text.slice(4, 6)}.${text.slice(6, 8)}`;
  }
  return cleanCustomerLabel(value);
}

function premiumTimeLabel(value) {
  const labels = {
    ja: "자시",
    chuk: "축시",
    in: "인시",
    myo: "묘시",
    jin: "진시",
    sa: "사시",
    o: "오시",
    mi: "미시",
    sin: "신시",
    yu: "유시",
    sul: "술시",
    hae: "해시",
  };
  return labels[value] || cleanCustomerLabel(value);
}

function renderPremiumConclusionPanel(report, sections) {
  return `
    <section class="premium-conclusion-panel">
      <div>
        <p class="eyebrow">종합 결론</p>
        <h1>${escapeHtml(premiumMainConclusion(report, sections))}</h1>
      </div>
    </section>
  `;
}

function premiumMainConclusion(report, sections) {
  const summary = premiumProfileSummary(report);
  if (summary.profile_type) {
    return `${cleanCustomerLabel(summary.profile_type)} 사주입니다.`;
  }
  const strongest = premiumStrongestSectionFromReport(report, sections);
  if (strongest) {
    return premiumConclusionSentence(strongest);
  }
  return "강하게 드러나는 운세와 주의점이 분명합니다.";
}

function premiumConclusionSentence(section) {
  const title = premiumNavTitle(section);
  const domain = premiumSectionDomain(section);
  if (domain === "love") {
    return "연애운은 깊어질수록 오래 남는 관계에 강합니다.";
  }
  if (domain === "marriage") {
    return "결혼운은 생활 기준과 책임감이 분명합니다.";
  }
  if (domain === "money") {
    return "재산 형성 능력이 강합니다.";
  }
  if (domain === "career") {
    return "직업 성취와 사회적 평가가 뚜렷합니다.";
  }
  if (domain === "personality") {
    return "성격의 기준과 감정 반응이 분명한 사주입니다.";
  }
  if (domain === "honor") {
    return "명예와 사회적 인정이 강합니다.";
  }
  return `${title}이 가장 선명합니다.`;
}

function premiumConclusionSummary(report, sections) {
  const profileSummary = premiumProfileSummary(report);
  if (profileSummary.summary) {
    return cleanPremiumDisplayText(profileSummary.summary);
  }
  const strongest = premiumStrongestSectionFromReport(report, sections);
  const risk = premiumPrimaryRiskSection(sections, report);
  const parts = [];
  if (strongest) {
    parts.push(premiumFinalStrengthSentence(strongest));
  }
  if (risk && (!strongest || premiumNavTitle(risk) !== premiumNavTitle(strongest))) {
    parts.push(premiumFinalRiskSentence(risk));
  }
  return parts.join(" ") || cleanPremiumDisplayText(judgmentOverviewContent(report));
}

function premiumStrongestSectionFromReport(report, sections) {
  const summary = premiumProfileSummary(report);
  const primaryDomain = summary?.primary?.domain;
  if (primaryDomain) {
    const found = premiumFindSection(sections, primaryDomain);
    if (found) {
      return found;
    }
  }
  const overview = cleanPremiumDisplayText(judgmentOverviewContent(report));
  const match = overview.match(/가장 강한 운세는\s*([^.\s]+)입니다/);
  if (match) {
    const target = cleanCustomerLabel(match[1]);
    const found = sections.find((section) => premiumNavTitle(section).includes(target) || target.includes(premiumNavTitle(section)));
    if (found) {
      return found;
    }
  }
  return premiumStrongestSection(sections);
}

function premiumStrongestSection(sections) {
  return [...sections]
    .filter((section) => premiumSectionDomain(section) !== "timing")
    .sort((a, b) => Number(b?.strength_score || 0) - Number(a?.strength_score || 0))[0];
}

function premiumPrimaryRiskSection(sections, report = null) {
  const summary = premiumProfileSummary(report);
  const managementDomain = summary?.management?.domain;
  if (managementDomain) {
    const found = premiumFindSection(sections, managementDomain);
    if (found) {
      return found;
    }
  }
  const risky = sections
    .filter((section) => premiumSectionDomain(section) !== "timing")
    .map((section) => ({ section, risk: premiumSectionRisk(section) }))
    .filter((item) => /주의|위험|손실|불균형|충돌|변수|정산|책임|저하|관리/.test(item.risk));
  return (risky[0] && risky[0].section) || premiumFindSection(sections, "money") || sections[0];
}

function premiumTimingSummaryValue(section) {
  if (!section) {
    return "";
  }
  if (Array.isArray(section.timing_events) && section.timing_events.length) {
    return section.timing_events
      .filter((event) => event.kind === "good")
      .slice(0, 2)
      .map((event) => `${event.year}년 ${event.title || event.domainLabel || "운세"}`)
      .join(" · ");
  }
  const checkpoints = Array.isArray(section.checkpoints) ? section.checkpoints : [];
  const value = premiumCheckpointValue(checkpoints, "상승 연도") || premiumCheckpointValue(checkpoints, "좋은 연도") || premiumCheckpointValue(checkpoints, "앞으로 좋은 연도");
  return timingYearHeadlineItems(value).slice(0, 2).join(" · ");
}

function timingYearHeadlineItems(value) {
  const items = timingSplitItems(value)
    .map((line) => line.split("·")[0].trim())
    .filter(Boolean);
  return items.length ? items : timingSplitItems(value);
}

function premiumDisplayPoint(value) {
  const text = cleanPremiumDisplayText(value || "")
    .replace(/:/g, " ")
    .replaceAll("최상위권", "최상")
    .replaceAll("중상위권", "좋음")
    .replaceAll("상위권", "강함")
    .replaceAll("평균권", "보통")
    .replaceAll("보완 필요", "주의 필요")
    .replaceAll("공동비용 정산 주의", "공동자금 운영력")
    .replaceAll("타고난 재물의 그릇", "재물 형성력")
    .replaceAll("재물 발생력", "재물 형성력")
    .replaceAll("재물이 들어오는 길", "수입 창출력")
    .replaceAll("수입 발생력", "수입 창출력")
    .replaceAll("축재력", "자산화 능력")
    .replaceAll("자산 확정력", "자산화 능력")
    .replaceAll("재물에 얽히는 사람 문제", "공동자금 운영력")
    .replaceAll("공동 자금 운영력", "공동자금 운영력")
    .replaceAll("공동 자금 관리력", "공동자금 운영력")
    .replaceAll("공동 자금 안정성", "공동자금 운영력")
    .replaceAll("돈을 지켜내는 기준", "계약·명의 안정성")
    .replaceAll("계약·문서 안정성", "계약·명의 안정성")
    .replaceAll("직업적 성취의 그릇", "성취 축적력")
    .replaceAll("직업 성취력", "성취 축적력")
    .replaceAll("평가가 따라오는 자리", "평가·명예 전환력")
    .replaceAll("업무 평가력", "평가·명예 전환력")
    .replaceAll("조직 안에서 자리 잡는 힘", "조직 적응력")
    .replaceAll("조직 적합도", "조직 적응력")
    .replaceAll("권한과 책임의 균형", "권한 확보력")
    .replaceAll("권한·책임 균형도", "권한 확보력")
    .replaceAll("책임·권한 불균형", "권한 확보력")
    .replaceAll("전문성으로 남는 힘", "전문 자산화")
    .replaceAll("애정 표현력", "애정 표현성")
    .replaceAll("애정이 표현되는 방식", "애정 표현성")
    .replaceAll("관계가 오래 가는 힘", "관계 지속력")
    .replaceAll("관계 안정성", "관계 지속력")
    .replaceAll("결혼으로 이어지는 현실성", "결혼 연결력")
    .replaceAll("결혼 현실화", "결혼 연결력")
    .replaceAll("결혼 현실성", "결혼 연결력")
    .replaceAll("생활 안정성", "생활 안정")
    .replaceAll("사회적 인정이 붙는 자리", "공적 인정 기반")
    .replaceAll("사회적 인정도", "공적 인정 기반")
    .replaceAll("평가가 직함으로 이어지는 자리", "직책 상승력")
    .replaceAll("권한이 붙을수록 커지는 평판", "권한 기반 평판")
    .replaceAll("감정 표현 차이", "감정 표현이 늦어지면 상대가 거리감을 느낍니다")
    .replaceAll("감정 거리 차이", "감정 표현이 늦어지면 상대가 거리감을 느낍니다")
    .replace(/\s+/g, " ")
    .trim();
  if (text.includes(">")) {
    return premiumPersonalityBasisText(text);
  }
  return text;
}

function renderPremiumDomainShowcase(report, sections) {
  const ordered = premiumDomainOrder(premiumVisibleDomainSections(sections));
  return `
    <section class="premium-domain-showcase" aria-label="프리미엄 영역별 결과">
      <div class="premium-section-title">
        <p class="eyebrow">프리미엄 결과</p>
        <h2>영역별 시각 요약</h2>
        <p>모든 지표는 높을수록 강점, 낮을수록 보완 지점으로 읽습니다.</p>
      </div>
      <div class="premium-domain-grid">
        ${ordered.map((section, index) => renderPremiumDomainPanel(section, index, report)).join("")}
      </div>
    </section>
  `;
}

function premiumDomainOrder(sections) {
  const order = ["personality", "money", "career", "love", "marriage", "timing", "life", "honor", "social"];
  return [...sections].sort((a, b) => {
    const aIndex = order.indexOf(premiumSectionDomain(a));
    const bIndex = order.indexOf(premiumSectionDomain(b));
    return (aIndex < 0 ? 99 : aIndex) - (bIndex < 0 ? 99 : bIndex);
  });
}

function renderPremiumDomainPanel(section, index, report = null) {
  const title = premiumSectionIndexTitle(section);
  const domain = premiumSectionDomain(section);
  const coreBody = renderPremiumDomainCoreBody(section, report);
  const cardBody = `
        <div class="premium-domain-card-body">
          <div class="premium-domain-summary">
            <div class="premium-domain-head">
              <h3>${escapeHtml(title)}</h3>
            </div>
            ${coreBody}
          </div>
        </div>
  `;
  return `
    <article class="premium-domain-panel domain-${escapeHtml(domain)} is-core-profile" id="premium-section-${index + 1}">
      <section class="premium-domain-card is-static">
        ${cardBody}
      </section>
    </article>
  `;
}

function renderPremiumDomainCoreBody(section, report = null) {
  const domain = premiumSectionDomain(section);
  if (domain === "timing") {
    return renderPremiumTimingProductBoard(report || {}, section) || renderPremiumProductStory(section) || renderPremiumVisualMetricBoard(section);
  }
  if (domain === "life") {
    return renderPremiumLifeSectionProduct(section);
  }
  const productStory = renderPremiumProductStory(section);
  const productBrief = productStory || renderPremiumProductInterpretation(section);
  const metricBoard = renderPremiumVisualMetricBoard(section);
  const reading = renderPremiumSectionReading(section);
  return `
      ${metricBoard}
      ${productBrief}
      ${reading}
    `;
}

function renderPremiumLifeSectionProduct(section) {
  const stageBoard = renderPremiumLifeStageBarBoard(section);
  if (stageBoard) {
    return stageBoard;
  }
  return renderPremiumVisualMetricBoard(section);
}

function renderPremiumLifeStageBarBoard(section) {
  const model = premiumLifeStageBarModel(section);
  if (!model.items.length) {
    return "";
  }
  return `
    <section class="premium-life-stage-board" aria-label="나이별 인생 구간">
      <header>
        <span>나이별 구간</span>
        <strong>생애 구간별 힘의 분포</strong>
        ${model.lead ? `<p>${escapeHtml(model.lead)}</p>` : ""}
      </header>
      <div class="premium-life-stage-bars">
        ${model.items.map(renderPremiumLifeStageBarItem).join("")}
      </div>
      ${model.summary.length ? `<div class="premium-life-stage-summary">${model.summary.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div>` : ""}
    </section>
  `;
}

function renderPremiumLifeStageBarItem(item) {
  const level = premiumMetricLevel(item.score);
  const percent = Math.max(12, Math.min(100, level.percent));
  const tone = item.score >= 70 ? "strong" : item.score < 55 ? "watch" : "neutral";
  return `
    <article class="premium-life-stage-bar-item is-${escapeHtml(tone)}">
      <div class="premium-life-stage-bar-head">
        <div>
          <strong>${escapeHtml(item.label)}</strong>
          <span>${escapeHtml(item.ageRange)}</span>
        </div>
        <b>${escapeHtml(level.label)}</b>
      </div>
      <div class="premium-life-stage-meter" aria-label="${escapeHtml(`${item.label} ${level.label}`)}">
        <i style="width:${percent}%"></i>
      </div>
      <p><b>${escapeHtml(item.title)}</b>${escapeHtml(item.body)}</p>
    </article>
  `;
}

function premiumLifeStageBarModel(section) {
  const early = premiumLifeStageSource(section, ["초년", "초년·청년", "형성"], 62);
  const middle = premiumLifeStageSource(section, ["중년", "성취"], 58);
  const late = premiumLifeStageSource(section, ["말년", "안정"], 60);
  const earlyScore = premiumLifeStageScore(early, 62);
  const middleScore = premiumLifeStageScore(middle, 58);
  const lateScore = premiumLifeStageScore(late, 60);
  const youthScore = Math.round((earlyScore * 0.58) + (middleScore * 0.42));
  const primeScore = Math.round((middleScore * 0.72) + (earlyScore * 0.12) + (lateScore * 0.16));
  const laterMiddleScore = Math.round((middleScore * 0.46) + (lateScore * 0.54));
  const items = [
    {
      label: "초년",
      ageRange: "출생~18세",
      score: earlyScore,
      title: "기준 형성",
      body: premiumLifeStageBody(early, "성격과 진로의 첫 기준이 만들어지는 시기입니다."),
    },
    {
      label: "청년",
      ageRange: "19~34세",
      score: youthScore,
      title: "진로와 관계 선택",
      body: "초년에 잡힌 기준이 전공, 첫 직업, 인간관계 선택으로 이어지는 시기입니다.",
    },
    {
      label: "장년",
      ageRange: "35~49세",
      score: primeScore,
      title: "책임 확대",
      body: "사회적 역할이 커지고, 맡은 책임이 경력과 생활 기반으로 연결되는 시기입니다.",
    },
    {
      label: "중년",
      ageRange: "50~64세",
      score: laterMiddleScore,
      title: "성취 보존",
      body: "그동안 쌓은 성취를 자산, 평판, 생활 구조로 굳히는 시기입니다.",
    },
    {
      label: "말년",
      ageRange: "65세 이후",
      score: lateScore,
      title: "생활 기반",
      body: premiumLifeStageBody(late, "보유 자산과 가족 관계가 후반의 안정감으로 드러나는 시기입니다."),
    },
  ];
  const strongest = [...items].sort((a, b) => b.score - a.score)[0];
  const weakest = [...items].sort((a, b) => a.score - b.score)[0];
  const weakestLabel = weakest
    ? weakest.score < 55
      ? "주의 구간"
      : weakest.score < 65
        ? "보완 구간"
        : "기반을 다지는 구간"
    : "";
  const profileSummary = cleanPremiumDisplayText(section?.section_profile?.summary || "");
  return {
    lead: profileSummary || "초년부터 말년까지, 어느 구간에서 힘이 강해지고 어느 구간에서 기반을 다지는지 정리했습니다.",
    items,
    summary: [
      strongest ? `가장 강한 구간: ${strongest.label}` : "",
      weakest && weakest.label !== strongest?.label ? `${weakestLabel}: ${weakest.label}` : "",
    ].filter(Boolean),
  };
}

function premiumLifeStageSource(section, keywords, fallbackScore) {
  const lists = [
    section?.visual_profile?.items,
    section?.topic_items,
    section?.product_story?.items,
    section?.section_profile?.items,
  ].filter(Array.isArray);
  const normalizedKeywords = keywords.map((item) => cleanCustomerLabel(item));
  for (const list of lists) {
    const found = list.find((item) => {
      const text = [item?.label, item?.title, item?.source_title, item?.value].map(cleanCustomerLabel).join(" ");
      return normalizedKeywords.some((keyword) => text.includes(keyword));
    });
    if (found) {
      return found;
    }
  }
  return { score: fallbackScore, body: "", caption: "" };
}

function premiumLifeStageScore(source, fallback) {
  const score = Number(source?.score);
  if (Number.isFinite(score)) {
    return Math.max(0, Math.min(100, Math.round(score)));
  }
  return premiumMetricScoreFromValue(source?.value || source?.grade || source?.tone || "", source?.tone || "") || fallback;
}

function premiumLifeStageBody(source, fallback) {
  return firstSentences(cleanPremiumDisplayText(source?.caption || source?.body || source?.text || source?.definition || fallback), 1);
}

function renderPremiumEvidenceDrawer(section, content) {
  const body = String(content || "").trim();
  if (!body) {
    return "";
  }
  const domain = premiumSectionDomain(section);
  const title = premiumNavTitle(section);
  const labels = {
    personality: ["성격 상세 보기", "성격과 실제 장면"],
    money: ["재물 상세 보기", "세부 지표와 구체적 양상"],
    career: ["직업 상세 보기", "평가 지표와 경력 손실 지점"],
    love: ["연애 상세 보기", "상대 선택과 관계 진전"],
    marriage: ["결혼 상세 보기", "생활 기준과 결혼 변수"],
  };
  const [summary, caption] = labels[domain] || [`${title} 상세 보기`, "세부 지표와 구체적 양상"];
  return `
    <details class="premium-evidence-drawer">
      <summary>
        <span>${escapeHtml(summary)}</span>
        <b>${escapeHtml(caption)}</b>
      </summary>
      <div class="premium-evidence-drawer-body">
        ${body}
      </div>
    </details>
  `;
}

function isPremiumCoreDomain(domain) {
  return ["personality", "money", "career", "love", "marriage"].includes(domain);
}

function renderPremiumCoreDomainSummary(section) {
  return `
    ${renderPremiumCoreDossier(section)}
  `;
}

function renderPremiumCoreDomainExpansion(section, details) {
  const domain = premiumSectionDomain(section);
  const source = premiumExpandedDomainDetails(section, details);
  if (!source.length) {
    return "";
  }
  const labels = {
    personality: {
      kicker: "성격의 실제 모습",
      title: "성격은 선택, 관계, 압박 앞에서 분명히 드러납니다.",
    },
    money: {
      kicker: "재물의 실제 결론",
      title: "재물운은 수입보다 소유권과 권리 관계에서 결론이 납니다.",
    },
    career: {
      kicker: "직업의 실제 결론",
      title: "직업운은 성취가 누구의 이름으로 남는지에서 갈립니다.",
    },
    love: {
      kicker: "연애의 실제 모습",
      title: "애정운은 마음의 깊이보다 약속과 표현에서 결과가 나옵니다.",
    },
    marriage: {
      kicker: "결혼의 실제 변수",
      title: "결혼운은 생활 기준, 주거, 가족 책임에서 결정됩니다.",
    },
  };
  const label = labels[domain] || {
    kicker: "실제 양상",
    title: `${premiumNavTitle(section)}에서 실제로 드러나는 장면입니다.`,
  };
  return `
    <section class="premium-core-expansion domain-${escapeHtml(domain)}" aria-label="${escapeHtml(label.kicker)}">
      <header>
        <span>${escapeHtml(label.kicker)}</span>
        <strong>${escapeHtml(label.title)}</strong>
      </header>
      <div class="premium-core-expansion-grid">
        ${source.map(renderPremiumCoreExpansionCard).join("")}
      </div>
    </section>
  `;
}

function premiumExpandedDomainDetails(section, details) {
  const domain = premiumSectionDomain(section);
  const rawDetails = Array.isArray(section?.detail_blocks) ? section.detail_blocks : [];
  const normalized = rawDetails
    .map((item) => ({
      title: cleanCustomerLabel(item?.title || ""),
      body: cleanPremiumDisplayText(item?.body || ""),
      bullets: Array.isArray(item?.bullets)
        ? item.bullets.map((bullet) => cleanPremiumDisplayText(bullet || "")).filter(Boolean)
        : [],
      tone: item?.tone || "",
    }))
    .filter((item) => item.title && (item.body || item.bullets.length));
  const fallback = Array.isArray(details) ? details : [];
  const pool = normalized.length ? normalized : fallback;
  const priority = {
    personality: ["판단", "대인", "감정", "압박", "행동", "관심"],
    money: ["자산", "수익", "재주", "명의", "약속", "정산", "가족"],
    career: ["성과", "평가", "전문", "권한", "독립", "운영"],
    love: ["사랑", "애정", "관계", "결혼", "배우자", "표현"],
    marriage: ["결혼", "생활", "배우자", "가족", "주거"],
  }[domain] || [];
  const scored = pool.map((item, index) => ({
    ...item,
    sortScore:
      (item.tone === "strong" ? 30 : item.tone === "watch" || item.tone === "risk" ? 24 : 12) +
      Math.max(
        0,
        12 -
          Math.min(
            ...priority
              .map((word, wordIndex) => (String(item.title || "").includes(word) ? wordIndex : 99))
              .filter((value) => Number.isFinite(value)),
          ),
      ) -
      index * 0.01,
  }));
  const seen = new Set();
  const limit = domain === "personality" ? 6 : domain === "love" ? 6 : 5;
  return scored
    .sort((a, b) => b.sortScore - a.sortScore)
    .filter((item) => {
      const key = premiumTopicMatchKey(item.title);
      if (!key || seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    })
    .slice(0, limit);
}

function renderPremiumCoreExpansionCard(item) {
  const tone = item.tone === "risk" || item.tone === "watch" ? "watch" : item.tone === "strong" ? "strong" : "neutral";
  const body = cleanPremiumDisplayText(item.body || "");
  const bullets = Array.isArray(item.bullets) ? item.bullets.filter(Boolean).slice(0, 3) : [];
  return `
    <article class="is-${escapeHtml(tone)}">
      <span>${escapeHtml(tone === "watch" ? "주의" : tone === "strong" ? "강점" : "양상")}</span>
      <strong>${escapeHtml(premiumDisplayAxisLabel(item.title || ""))}</strong>
      ${body ? `<p>${escapeHtml(body)}</p>` : ""}
      ${
        bullets.length
          ? `<ul>${bullets
              .map(premiumDetailSceneText)
              .filter(Boolean)
              .map((bullet) => `<li>${escapeHtml(bullet)}</li>`)
              .join("")}</ul>`
          : ""
      }
    </article>
  `;
}

function premiumProductStory(section) {
  const story = section?.product_story;
  return story && typeof story === "object" ? story : {};
}

function renderPremiumProductStory(section) {
  const story = premiumProductStory(section);
  const headline = cleanPremiumDisplayText(story.headline || premiumSectionHeadline(section));
  const lead = cleanPremiumDisplayText(story.lead || "");
  const items = Array.isArray(story.items)
    ? story.items
        .map((item) => ({
          role: item?.role || "scene",
          label: cleanCustomerLabel(item?.label || ""),
          title: cleanCustomerLabel(item?.title || ""),
          value: cleanCustomerLabel(item?.value || ""),
          body: cleanPremiumDisplayText(item?.body || ""),
        }))
        .filter((item) => item.title || item.body)
    : [];
  if (!headline && !lead && !items.length) {
    return "";
  }
  return `
    <section class="premium-product-story domain-${escapeHtml(premiumSectionDomain(section))}" aria-label="${escapeHtml(`${premiumNavTitle(section)} 프리미엄 요약`)}">
      <header>
        <span>${escapeHtml(cleanCustomerLabel(story.kicker || `${premiumNavTitle(section)} 요약`))}</span>
        ${headline ? `<strong>${escapeHtml(headline)}</strong>` : ""}
      </header>
      ${lead ? `<p class="premium-product-story-lead">${escapeHtml(lead)}</p>` : ""}
      ${
        items.length
          ? `<div class="premium-product-story-grid">
              ${items.map(renderPremiumProductStoryItem).join("")}
            </div>`
          : ""
      }
    </section>
  `;
}

function renderPremiumSectionReading(section) {
  const model = premiumSectionReadingModel(section);
  if (!model) {
    return "";
  }
  return `
    <section class="premium-section-reading domain-${escapeHtml(model.domain)}" aria-label="${escapeHtml(`${model.title} 세부 해석`)}">
      <header>
        <span>${escapeHtml(model.kicker)}</span>
        <strong>${escapeHtml(model.title)}</strong>
      </header>
      ${model.lead ? `<p class="premium-section-reading-lead">${escapeHtml(model.lead)}</p>` : ""}
      ${model.basis.length ? `
        <div class="premium-section-reading-basis" aria-label="근거 항목">
          ${model.basis.map((item) => `<p>${escapeHtml(item)}</p>`).join("")}
        </div>
      ` : ""}
      <div class="premium-section-reading-grid">
        ${model.chapters.map(renderPremiumSectionReadingChapter).join("")}
      </div>
    </section>
  `;
}

function premiumSectionReadingModel(section) {
  if (!section) {
    return null;
  }
  const domain = premiumSectionDomain(section);
  if (!["personality", "money", "career", "love", "marriage"].includes(domain)) {
    return null;
  }
  const headline =
    cleanPremiumDisplayText(section?.product_story?.headline || "") ||
    cleanPremiumDisplayText(section?.section_profile?.summary || "") ||
    cleanPremiumDisplayText(premiumSectionHeadline(section));
  const lead =
    cleanPremiumDisplayText(section?.product_story?.lead || "") ||
    cleanPremiumDisplayText(section?.lead || "") ||
    firstSentences(headline, 2);
  const titles = {
    personality: "성격은 판단 기준, 감정 처리, 대인 거리에서 분명하게 드러납니다.",
    money: "재물운은 수입보다 귀속, 권리, 손실 지점에서 차이가 큽니다.",
    career: "직업운은 성취가 직함, 평가, 보상으로 남는 자리에서 강합니다.",
    love: "연애운은 끌림보다 선택 기준과 표현 방식에서 결론이 납니다.",
    marriage: "결혼운은 배우자상, 생활 기준, 가족 책임에서 실제 모습이 갈립니다.",
  };
  const kickers = {
    personality: "성격 요약",
    money: "재물 요약",
    career: "직업 요약",
    love: "연애 요약",
    marriage: "결혼 요약",
  };
  const chapters = premiumSectionReadingChapters(section, domain).filter(Boolean);
  if (!chapters.length && !lead) {
    return null;
  }
  return {
    domain,
    kicker: kickers[domain] || "핵심 요약",
    title: titles[domain] || premiumNavTitle(section),
    lead: firstSentences(lead || headline, 3),
    basis: premiumSectionReadingBasis(section, domain),
    chapters,
  };
}

function premiumSectionReadingBasis(section, domain) {
  const cards = Array.isArray(section?.premium_basis_cards) ? section.premium_basis_cards : [];
  if (!cards.length) {
    return [];
  }
  const usable = cards
    .map((card) => ({
      label: cleanCustomerLabel(card?.label || ""),
      title: cleanCustomerLabel(card?.title || ""),
      body: cleanPremiumDisplayText(card?.body || ""),
    }))
    .filter((card) => card.title || card.body);
  const priority = domain === "personality"
    ? ["생극·십신", "오행 배합", "월령 기준", "일간 반응", "상생상극"]
    : ["월령 기준", "월령 심화", "지지·지장간", "생극·십신", "상생상극"];
  const selected = [];
  const used = new Set();
  priority.forEach((label) => {
    if (selected.length >= 3) {
      return;
    }
    const index = usable.findIndex((card, itemIndex) => !used.has(itemIndex) && card.label === label);
    if (index >= 0) {
      selected.push(usable[index]);
      used.add(index);
    }
  });
  usable.forEach((card, index) => {
    if (selected.length >= 3 || used.has(index)) {
      return;
    }
    selected.push(card);
  });
  return selected
    .map((card) => {
      const body = firstSentences(card.body, 1);
      if (card.title && body) {
        return `${card.title}. ${body}`;
      }
      return body || card.title;
    })
    .filter(Boolean)
    .slice(0, domain === "personality" ? 2 : 3);
}

function premiumSectionReadingChapters(section, domain) {
  const chapterConfig = {
    personality: [
      { label: "기준", title: "판단의 구조", detailTitles: ["판단 기준"], fallback: "중요한 선택 앞에서 남의 말보다 직접 확인한 근거를 우선합니다." },
      { label: "관계", title: "사람을 대하는 거리", detailTitles: ["대인 거리감"], fallback: "처음부터 쉽게 가까워지기보다 시간을 두고 사람을 확인합니다." },
      { label: "감정", title: "감정 처리 방식", detailTitles: ["감정 반응"], fallback: "감정이 올라와도 바로 드러내기보다 속으로 정리한 뒤 표현합니다." },
      { label: "압박", title: "부담 앞의 반응", detailTitles: ["압박 대응"], tone: "watch", fallback: "부담이 커지면 책임 범위를 먼저 확인하고 말투가 단호해집니다." },
    ],
    money: [
      { label: "결론", title: "재물의 귀속", cardTitles: ["재물 형성력", "재물 규모 확장력"], detailTitles: ["자산 축적"], fallback: "번 돈이 소비로 사라지기보다 자기 이름의 권리와 자산으로 남을 때 재물운이 커집니다." },
      { label: "수입", title: "수입의 성립", cardTitles: ["수입 창출력", "성과 보상력", "재주 수익화"], detailTitles: ["성과보다 덜 남는 보상"], fallback: "일의 결과가 실제 입금으로 이어지려면 받을 몫과 보상 기준이 먼저 분명해야 합니다." },
      { label: "자산", title: "자산의 고정", cardTitles: ["자산화 능력", "자금 운용 안정성", "투자·거래 판단력"], detailTitles: ["자산 축적"], fallback: "현금보다 명의, 지분, 장기 보유 자산처럼 권리로 확인되는 돈에서 강점이 나타납니다." },
      { label: "주의", title: "손실의 발단", cardTitles: ["공동자금 운영력", "계약·명의 안정성", "부채·보증 관리력", "가족재산 경계력"], detailTitles: ["배우자·가족과 섞이는 재산", "말로 정한 약속의 손실"], tone: "watch", fallback: "가까운 사람과 돈을 묶으면 처음의 호의가 나중에는 명의와 몫의 문제로 바뀌기 쉽습니다." },
    ],
    career: [
      { label: "적성", title: "직업적 기질", cardTitles: ["직업 적성", "직업 분야"], detailTitles: ["운영을 장악하는 직업 성취"], fallback: "단순 실행보다 책임 있는 운영, 기획, 관리에서 직업적 강점이 살아납니다." },
      { label: "평가", title: "평가와 직함", cardTitles: ["평가·명예 전환력", "승진·직함 가능성", "성취 축적력"], detailTitles: ["성과가 자기 이름으로 남는 자리"], fallback: "성과가 기록, 직함, 공식 평가로 남을 때 경력의 값이 올라갑니다." },
      { label: "보상", title: "보상과 협상", cardTitles: ["보상 협상력", "성과 보상력", "전문 자산화"], detailTitles: ["성과가 자기 이름으로 남는 자리"], fallback: "해낸 일이 연봉, 성과급, 지분처럼 자기 몫으로 계산될수록 유리합니다." },
      { label: "주의", title: "경력 손상 지점", cardTitles: ["권한 확보력", "책임·권한 균형", "평가 손실 위험"], detailTitles: ["공을 빼앗기는 조직 자리", "책임과 결정권의 불균형"], tone: "watch", fallback: "책임은 크고 결정권은 약한 자리는 경력보다 소모가 먼저 남습니다." },
    ],
    love: [
      { label: "선택", title: "애정의 선택 기준", cardTitles: ["끌림의 기준", "상대 선택력", "상대 신뢰 감별력"], detailTitles: ["사랑을 시작하는 방식"], fallback: "가벼운 설렘보다 태도와 책임감이 확인되는 사람에게 마음이 오래 갑니다." },
      { label: "지속", title: "관계의 지속성", cardTitles: ["관계 지속력", "관계 진전력"], detailTitles: ["관계가 공식화되는 연애"], fallback: "한 번 깊어진 관계는 오래 유지하려는 힘이 강합니다." },
      { label: "표현", title: "표현과 확신", cardTitles: ["애정 표현성", "관계 주도권"], detailTitles: ["마음보다 늦은 표현"], fallback: "마음이 있어도 표현이 늦으면 상대는 확신보다 거리감을 먼저 느낍니다." },
      { label: "주의", title: "감정 손상 지점", cardTitles: ["갈등 관리력", "관계 주의 지점", "감정 기복 대응력"], detailTitles: ["감정 기복이 큰 상대와의 손상"], tone: "watch", fallback: "감정 기복이 큰 상대와 만나면 일상과 돈까지 흔들릴 수 있습니다." },
    ],
    marriage: [
      { label: "성향", title: "혼인의 성격", cardTitles: ["혼인 성향", "결혼 현실화력"], detailTitles: ["결혼이 안정되는 방식"], fallback: "결혼은 감정의 결론보다 생활을 함께 책임지는 약속으로 받아들입니다." },
      { label: "상대", title: "배우자상", cardTitles: ["배우자상", "배우자 선택력"], detailTitles: ["안정적인 상대와 오래 가는 결혼"], fallback: "성실하고 생활 기준이 분명한 배우자와 오래 갑니다." },
      { label: "생활", title: "생활의 안정", cardTitles: ["생활 안정", "주거·생활 설계력", "부부 재정 안정성"], detailTitles: ["생활 기준"], fallback: "주거, 생활비, 시간 사용의 기준이 잡힐수록 결혼 생활이 안정됩니다." },
      { label: "주의", title: "결혼 뒤 부담", cardTitles: ["가족 책임 경계력", "가족 변수", "부부 재정 갈등"], detailTitles: ["결혼 후 돈과 가족 책임의 충돌"], tone: "watch", fallback: "원가족과 돈 문제가 부부 사이로 들어오면 결혼 생활의 부담이 커집니다." },
    ],
  }[domain] || [];
  return chapterConfig.map((config) => premiumSectionReadingChapterFromConfig(section, config));
}

function premiumSectionReadingChapterFromConfig(section, config) {
  const card = premiumRequiredCardByTitle(section, config.cardTitles || []);
  const detail = premiumDetailBlockByTitle(section, config.detailTitles || []);
  const sourceText = premiumReadingBodyFromSources(card, detail, config.fallback || "", premiumSectionDomain(section));
  if (!sourceText) {
    return null;
  }
  const tone = config.tone || (card?.tone === "watch" || card?.grade === "주의" || detail?.tone === "risk" || detail?.tone === "watch" ? "watch" : "strong");
  return {
    label: config.label || "결과",
    title: config.title || cleanCustomerLabel(card?.title || detail?.title || ""),
    body: sourceText,
    tone,
    meta: premiumReadingCardMeta(card),
  };
}

function premiumRequiredCardByTitle(section, titles) {
  const cards = Array.isArray(section?.required_judgment_cards) ? section.required_judgment_cards : [];
  const wanted = (titles || []).map((title) => premiumTopicMatchKey(title));
  return (
    cards.find((card) => wanted.includes(premiumTopicMatchKey(card?.title || ""))) ||
    cards.find((card) => wanted.some((key) => key && premiumTopicMatchKey(card?.title || "").includes(key))) ||
    null
  );
}

function premiumDetailBlockByTitle(section, titles) {
  const details = Array.isArray(section?.detail_blocks) ? section.detail_blocks : [];
  const wanted = (titles || []).map((title) => premiumTopicMatchKey(title));
  return (
    details.find((detail) => wanted.includes(premiumTopicMatchKey(detail?.title || ""))) ||
    details.find((detail) => wanted.some((key) => key && premiumTopicMatchKey(detail?.title || "").includes(key))) ||
    null
  );
}

function premiumReadingBodyFromSources(card, detail, fallback, domain = "") {
  const pieces = [];
  const add = (text, sentenceLimit = 2) => {
    const cleaned = firstSentences(cleanPremiumDisplayText(text || ""), sentenceLimit);
    if (cleaned && !pieces.some((item) => normalizedSentenceKey(item) === normalizedSentenceKey(cleaned))) {
      pieces.push(cleaned);
    }
  };
  if (card && domain) {
    add(premiumRequiredJudgmentResultLine(domain, card), 1);
    add(premiumRequiredJudgmentMeaningLine(domain, card), 1);
    add(premiumRequiredJudgmentSceneLine(domain, card), 1);
    add(premiumRequiredJudgmentDetailLine(domain, card), 1);
  }
  add(card?.body, 2);
  add(card?.scene, 1);
  add(detail?.body, 2);
  const bullets = Array.isArray(detail?.bullets) ? detail.bullets : [];
  for (const bullet of bullets.slice(0, 2)) {
    add(premiumDetailSceneText(bullet), 1);
  }
  if (!pieces.length) {
    add(fallback, 3);
  }
  return pieces.slice(0, domain === "personality" ? 4 : 5).join(" ");
}

function premiumReadingCardMeta(card) {
  if (!card) {
    return "";
  }
  const grade = cleanCustomerLabel(card.grade || "");
  const score = Number(card.score);
  if (grade && Number.isFinite(score)) {
    return `${grade} · ${Math.round(score)}점`;
  }
  if (grade) {
    return grade;
  }
  return "";
}

function renderPremiumSectionReadingChapter(item) {
  return `
    <article class="is-${escapeHtml(item.tone || "neutral")}">
      <span>${escapeHtml(item.label)}</span>
      <strong>${escapeHtml(item.title)}</strong>
      <p>${escapeHtml(item.body)}</p>
      ${item.meta ? `<em>${escapeHtml(item.meta)}</em>` : ""}
    </article>
  `;
}

function premiumMetricScoreFromValue(value, tone = "") {
  const text = cleanCustomerLabel(value || "");
  if (/최상위|매우 강|상위권|높음/.test(text)) {
    return 88;
  }
  if (/중상위|강함|양호|강점|핵심|성취기|안정기/.test(text)) {
    return 74;
  }
  if (/평균|보통|보완|형성기/.test(text)) {
    return 56;
  }
  if (/다소 낮|주의|약함|낮음/.test(text)) {
    return tone === "watch" ? 34 : 38;
  }
  if (tone === "watch" || tone === "risk") {
    return 38;
  }
  if (tone === "strong" || tone === "good") {
    return 76;
  }
  return 56;
}

function premiumMetricLevel(score) {
  const value = Number.isFinite(Number(score)) ? Number(score) : 56;
  const percent = Math.max(14, Math.min(96, Math.round(value)));
  if (value >= 80) {
    return { label: "매우 좋음", percent };
  }
  if (value >= 65) {
    return { label: "좋음", percent };
  }
  if (value >= 45) {
    return { label: "보통", percent };
  }
  if (value >= 30) {
    return { label: "주의", percent };
  }
  return { label: "위험", percent };
}

function premiumMetricIsNegativeAxis(value) {
  const text = cleanCustomerLabel(value || "");
  if (!text) {
    return false;
  }
  if (/(관리력|안정성|경계력|방어력|조정력|대응력|회복성|유지력|감별력|확보력|운영력|자산화|수익화|창출력|형성력|축적력|전환력|적응력|가능성|기준성)$/u.test(text)) {
    return false;
  }
  return /(주의|손실|위기|이별|부담|갈등|손상|리스크|위험|새기 쉬|돈이 새|결정권 없는 책임|기록이 없|정산 문제|몫 문제|책임은 많은데)/u.test(text);
}

function premiumMetricDefinition(domain, title) {
  const label = premiumDisplayAxisLabel(title || "");
  const profile = premiumMetricDefinitionProfile(domain, label);
  if (profile?.definition) {
    return profile.definition;
  }
  const common = {
    "판단 기준": "중요한 선택 앞에서 무엇을 근거로 결론을 내리는지 보여주는 지표입니다.",
    "대인 조율감": "사람을 받아들이는 속도와 가까워진 뒤에도 지키는 선을 나타냅니다.",
    "감정 반응성": "감정이 올라왔을 때 바로 드러나는지, 정리한 뒤 표현되는지를 보여줍니다.",
    "압박 대응력": "책임과 문제가 커졌을 때 버티는 방식과 예민해지는 지점을 나타냅니다.",
    "실행 속도": "판단한 내용을 실제 행동으로 옮기는 속도를 나타냅니다.",
    "관심 몰입도": "한 번 꽂힌 주제에 집중하고 오래 파고드는 정도를 보여줍니다.",
    "재물 형성력": "돈이 들어오는 기회가 실제 재산의 바탕으로 이어지는 정도입니다.",
    "재물 규모 확장력": "일상의 수입을 넘어 거래 단위와 자산 단위가 커지는 정도입니다.",
    "수입 창출력": "직업, 거래, 성과가 실제 입금으로 확인되는 힘입니다.",
    "재주 수익화": "기술, 말, 콘텐츠, 서비스가 가격을 갖고 수입으로 바뀌는 정도입니다.",
    "자산화 능력": "현금이 소비로 사라지지 않고 명의, 지분, 장기 보유 자산으로 굳어지는 힘입니다.",
    "공동자금 운영력": "가족, 지인, 동업자와 얽힌 돈에서 자기 몫과 책임을 지키는 정도입니다.",
    "계약·명의 안정성": "지급일, 명의, 지분, 수령액이 문서로 보호되는 정도입니다.",
    "부채·보증 관리력": "대여, 보증, 채무 인수에서 책임 범위를 제한하는 힘입니다.",
    "직업 적성": "실력이 가장 빨리 인정받는 업무 성격과 역할의 방향입니다.",
    "직업 분야": "직업명보다 실제 업무 방식, 책임 구조, 결과물의 성격을 가르는 기준입니다.",
    "성취 축적력": "한 번의 성과가 이력, 실적, 다음 자리의 근거로 남는 힘입니다.",
    "평가·명예 전환력": "실적이 평판, 추천, 직함, 공식 평가로 바뀌는 정도입니다.",
    "승진·직함 가능성": "책임이 커질 때 직함과 사회적 이름이 함께 붙는 정도입니다.",
    "보상 협상력": "성과를 연봉, 수수료, 성과급, 지분처럼 자기 몫으로 확정하는 힘입니다.",
    "권한 확보력": "맡은 책임에 맞는 결정권과 평가 권한을 함께 확보하는 정도입니다.",
    "책임·권한 균형": "맡은 범위, 보고 체계, 평가 기준이 균형 있게 주어지는 정도입니다.",
    "끌림의 기준": "처음 마음이 움직이는 지점과 오래 끌리는 상대의 조건을 구분하는 기준입니다.",
    "상대 선택력": "오래 갈 사람과 손상될 관계를 초기에 가려내는 눈입니다.",
    "상대 신뢰 감별력": "상대의 말보다 반복된 태도, 약속, 책임감을 읽는 감각입니다.",
    "인연 형성력": "스쳐 가는 호감이 실제 만남과 관계로 이어지는 힘입니다.",
    "관계 지속력": "감정이 깊어진 뒤에도 관계를 안정적으로 오래 유지하는 정도입니다.",
    "애정 표현성": "마음이 상대에게 말과 행동으로 전달되는 정도입니다.",
    "관계 주도권": "관계를 시작하고 멈추는 속도와 거리를 스스로 정하는 힘입니다.",
    "혼인 성향": "결혼을 감정의 결론이 아니라 생활의 약속과 책임으로 받아들이는 방식입니다.",
    "배우자상": "오래 맞는 배우자의 성격, 생활 태도, 책임 감각을 보여주는 기준입니다.",
    "결혼 적기": "혼인 논의가 약속과 절차로 굳어지기 쉬운 시기입니다.",
    "결혼 현실화력": "결혼 의사가 집, 일정, 가족 협의, 공식 절차로 넘어가는 힘입니다.",
    "생활 안정": "주거, 생활비, 역할 기준이 결혼 생활 안에서 안정되는 정도입니다.",
    "주거·생활 설계력": "집, 생활비, 역할 분담을 실제 계획으로 정리하는 힘입니다.",
    "부부 재정": "공동 생활비와 개인 자산의 기준을 세우는 방식입니다.",
    "가족 책임 경계력": "양가와 원가족 문제에서 부부의 기준을 먼저 세우는 힘입니다.",
    "상승 연도": "성과, 인연, 재물 중 한 가지가 선명한 결과로 남는 해입니다.",
    "주의 연도": "손실, 책임, 관계 부담이 실제 문제로 드러나기 쉬운 해입니다.",
    "시기 대응력": "불리한 해에 손실, 책임, 관계 문제를 키우지 않고 정리하는 힘입니다.",
    "초년·청년의 형성": "성격과 진로의 기준이 처음 만들어지는 구간입니다.",
    "중년의 성취": "사회적 책임과 직업적 성취가 실제 이력으로 남는 구간입니다.",
    "말년의 안정": "말년에 자산과 생활 기반이 남는 방식을 보여줍니다.",
    "공적 인정 기반": "직함, 평가, 공식 역할이 사회적 신뢰로 전환되는 기반입니다.",
    "사회적 인정이 붙는 자리": "직함, 평가, 공식 역할이 사회적 신뢰로 전환되는 기반입니다.",
    "평판이 오래 남는 힘": "한 번 얻은 신뢰와 이름이 오래 유지되는 구조입니다.",
    "공식 책임을 맡는 힘": "이름이 남는 역할을 감당하는 자리입니다.",
    "명예를 지켜내는 기준": "평판이 손상되는 자리를 피하고 이름을 지켜내는 기준입니다.",
    "사람을 얻는 힘": "인맥의 규모보다 신뢰가 오래 남는 관계를 형성하는 방식입니다.",
    "도움으로 이어지는 인연": "말뿐인 친분이 아니라 실제 조력이 되는 관계입니다.",
    "관계가 오래 남는 힘": "감정이 깊어진 뒤에도 관계를 오래 유지하는 힘입니다.",
    "부탁과 책임의 경계": "가까운 사람의 부탁이 부담으로 바뀌는 지점입니다.",
  };
  if (common[label]) {
    return common[label];
  }
  const domainFallback = {
    personality: "성격과 행동 방식에서 해당 요소가 차지하는 비중을 나타냅니다.",
    money: "재물이 생기고 남고 보호되는 과정에서 해당 요소가 차지하는 비중입니다.",
    career: "직업 선택, 평가, 보상, 경력 유지에서 해당 요소가 작용하는 정도입니다.",
    love: "호감, 선택, 표현, 관계 유지에서 해당 요소가 작용하는 정도입니다.",
    marriage: "결혼 결정, 생활 안정, 가족 책임에서 해당 요소가 작용하는 정도입니다.",
    timing: "특정 연도에 사건으로 드러나는 힘의 방향을 나타냅니다.",
    life: "인생 구간별로 중심 과제가 형성되는 방식을 나타냅니다.",
    honor: "사회적 이름, 공식 평가, 평판 유지에 관여하는 요소입니다.",
    social: "관계의 규모, 신뢰, 도움, 책임 경계에 관여하는 요소입니다.",
  };
  return domainFallback[domain] || "해당 영역의 결과에 반영되는 세부 요소입니다.";
}

function premiumMetricDefinitionProfile(domain, title) {
  const label = premiumDisplayAxisLabel(title || "");
  const profiles = {
    "판단 기준": ["중요한 선택 앞에서 결론을 내리는 방식입니다.", "근거가 분명한 선택에서 강점이 드러납니다.", "판단 기준이 흔들리면 주변 말에 끌려 결정이 늦어집니다."],
    "대인 조율감": ["사람을 받아들이고 거리를 맞추는 감각입니다.", "관계의 온도를 지나치게 높이지 않고 안정적으로 맞춥니다.", "낮으면 가까운 관계에서도 말의 온도와 거리감이 어긋나기 쉽습니다."],
    "감정 반응성": ["감정이 올라왔을 때 밖으로 드러나는 속도입니다.", "높으면 마음의 변화가 빠르게 전달되고 관계의 반응도 빨라집니다.", "낮으면 속마음은 있어도 상대가 알아차리기까지 시간이 걸립니다."],
    "압박 대응력": ["책임과 문제가 커졌을 때 흔들림을 견디는 힘입니다.", "높으면 부담스러운 자리에서도 중심을 쉽게 잃지 않습니다.", "낮으면 책임이 겹치는 순간 말투와 판단이 급격히 예민해집니다."],
    "실행 속도": ["생각한 일을 실제 행동으로 옮기는 속도입니다.", "높으면 기회가 왔을 때 붙잡는 시간이 짧습니다.", "낮으면 준비는 충분해도 결과를 내놓는 시점이 늦어집니다."],
    "관심 몰입도": ["한 주제에 깊이 들어가 오래 붙드는 힘입니다.", "높으면 전문성이나 취향이 분명한 영역에서 실력이 빠르게 쌓입니다.", "낮으면 관심이 분산되어 성과가 얇게 남기 쉽습니다."],
    "시기 대응력": ["불리한 해에 손실, 책임, 관계 문제가 커지기 전에 정리하는 힘입니다.", "높으면 흔들리는 해에도 중요한 결정과 책임 범위를 비교적 분명하게 잡습니다.", "낮으면 손실, 책임, 관계 문제가 한꺼번에 올라올 때 판단이 늦어질 수 있습니다."],
    "감정 처리": ["감정이 생긴 뒤 그것을 정리하고 표현하는 방식입니다.", "감정이 커져도 바로 터뜨리기보다 상황을 정리한 뒤 움직입니다.", "정리가 늦어지면 속으로 쌓인 감정이 어느 순간 단호한 말로 나옵니다."],
    "기준 조율력": ["부담이 커졌을 때 자기 입장을 세우면서도 상황에 맞게 조정하는 힘입니다.", "필요한 순간에는 입장을 분명히 하되 관계의 선을 해치지 않습니다.", "타협이 필요한 자리에서 말이 굳어지고 관계가 뻣뻣해질 수 있습니다."],
    "재물 형성력": ["돈이 생기는 기회가 실제 재산의 바탕으로 바뀌는 힘입니다.", "높으면 수입이 단순 소비로 흩어지지 않고 다음 자산의 기초가 됩니다.", "낮으면 벌이는 있어도 시간이 지난 뒤 남는 것이 약해집니다."],
    "재물 규모 확장력": ["수입 단위와 거래 단위가 커지는 힘입니다.", "높으면 작은 벌이에서 멈추지 않고 자산 규모를 키울 기회가 붙습니다.", "낮으면 수입은 생겨도 큰 판으로 확장되는 속도가 더딥니다."],
    "수입 창출력": ["일, 거래, 성과가 실제 입금으로 연결되는 힘입니다.", "높으면 움직인 만큼 돈으로 확인되는 일이 많습니다.", "낮으면 활동량에 비해 현금화가 늦거나 보상이 작게 남습니다."],
    "재주 수익화": ["기술, 말, 콘텐츠, 서비스가 가격을 얻는 힘입니다.", "높으면 가진 재주가 취미에 머물지 않고 수입원이 됩니다.", "낮으면 재능은 보여도 돈을 받는 구조까지 만들기 어렵습니다."],
    "성과 보상력": ["해낸 일이 연봉, 성과급, 수수료, 지분으로 돌아오는 힘입니다.", "높으면 결과물에 맞는 보상을 요구하고 확보하기 쉽습니다.", "낮으면 일은 많이 했는데 몫은 작게 남는 상황이 생깁니다."],
    "자금 운용 안정성": ["들어온 돈을 일정하게 관리하고 유지하는 힘입니다.", "높으면 수입의 변동이 있어도 생활과 자산 계획이 크게 흔들리지 않습니다.", "낮으면 수입이 늘어도 지출 구조가 먼저 흔들립니다."],
    "자산화 능력": ["현금이 명의, 지분, 권리, 장기 보유 자산으로 굳어지는 힘입니다.", "높으면 벌어들인 돈이 눈에 보이는 소유로 남습니다.", "낮으면 현금 흐름은 있어도 내 이름의 자산으로 고정되기 어렵습니다."],
    "투자·거래 판단력": ["투자와 거래에서 회수 가능성과 손실 범위를 가르는 감각입니다.", "높으면 수익률보다 구조와 권리를 먼저 확인합니다.", "낮으면 말이 좋은 거래에 들어갔다가 회수에서 막히기 쉽습니다."],
    "계약·명의 안정성": ["지급일, 명의, 지분, 수령액이 문서로 보호되는 정도입니다.", "높으면 돈이 오갈 때 권리관계가 분명하게 남습니다.", "낮으면 말로 정한 약속이 나중에 서로 다르게 해석됩니다."],
    "채권·미수금 회수력": ["받아야 할 돈을 끝까지 회수하는 힘입니다.", "높으면 밀린 돈이나 약속된 대가를 흐지부지 넘기지 않습니다.", "낮으면 받을 돈이 남아도 관계 때문에 강하게 정리하지 못합니다."],
    "공동자금 운영력": ["가족, 지인, 동업자와 섞인 돈에서 자기 몫을 지키는 힘입니다.", "높으면 함께 쓰는 돈도 기준과 책임이 분명합니다.", "낮으면 가까운 관계에서 손해를 떠안거나 몫이 흐려집니다."],
    "부채·보증 관리력": ["대여, 보증, 채무 인수에서 책임 범위를 제한하는 힘입니다.", "높으면 내 돈과 남의 책임을 분리할 수 있습니다.", "낮으면 호의가 부채나 보증 문제로 바뀌기 쉽습니다."],
    "가족재산 경계력": ["가족 문제와 개인 자산을 구분하는 힘입니다.", "높으면 도와주더라도 내 재산의 경계는 지킵니다.", "낮으면 가족 문제로 돈의 방향이 자주 바뀝니다."],
    "사업 확장성": ["개인 수입을 넘어 사업 단위로 넓히는 힘입니다.", "높으면 사람, 거래처, 상품을 묶어 규모를 키울 수 있습니다.", "낮으면 혼자 움직일 때는 괜찮아도 조직화에서 부담이 커집니다."],
    "재정 방어력": ["예상 밖의 지출과 손실을 막아내는 힘입니다.", "높으면 위기 때도 현금과 자산의 손상을 줄입니다.", "낮으면 한 번의 지출이 오래 남는 부담으로 바뀝니다."],
    "후반 축재력": ["나이가 들수록 재산이 안정적으로 남는 힘입니다.", "높으면 후반으로 갈수록 자산의 형태가 단단해집니다.", "낮으면 벌어온 기간에 비해 말년에 남는 기반이 약할 수 있습니다."],
    "금전 기준성": ["돈을 쓰고 나누고 보관하는 기준의 선명도입니다.", "높으면 관계보다 기준이 앞서 재정이 흔들리지 않습니다.", "낮으면 상황과 사람에 따라 돈의 기준이 자주 바뀝니다."],
    "직업 적성": ["실력이 가장 빨리 인정받는 일의 성격입니다.", "높으면 맡는 일과 기질이 맞아 경력의 속도가 붙습니다.", "낮으면 능력은 있어도 일의 방식과 맞지 않아 소모가 큽니다."],
    "직업 분야": ["직업명보다 실제 업무 방식과 책임 구조의 적합도를 가르는 기준입니다.", "높으면 분야를 바꾸어도 유사한 역할에서 성취가 이어집니다.", "낮으면 이름 좋은 직업이라도 실제 업무 방식에서 답답함이 큽니다."],
    "성취 축적력": ["한 번의 성과가 이력과 다음 기회로 남는 힘입니다.", "높으면 지나간 성과가 다음 자리의 근거가 됩니다.", "낮으면 일회성 성과는 있어도 경력 자산으로 쌓이는 힘이 약합니다."],
    "평가·명예 전환력": ["실적이 평판, 추천, 직함, 공식 평가로 바뀌는 힘입니다.", "높으면 해낸 일이 사람들에게 분명히 알려집니다.", "낮으면 실력에 비해 이름과 평판이 늦게 따라옵니다."],
    "승진·직함 가능성": ["책임이 커질 때 직함과 사회적 이름이 함께 붙는 힘입니다.", "높으면 역할 확대가 실제 자리 상승으로 이어집니다.", "낮으면 책임은 늘지만 직함은 늦게 붙을 수 있습니다."],
    "사회적 도약성": ["직업적 성과가 사회적 위치 상승으로 이어지는 힘입니다.", "높으면 일정 시점에 자리의 격이 올라가는 계기가 생깁니다.", "낮으면 성과가 있어도 도약보다 유지에 머무르기 쉽습니다."],
    "권한 확보력": ["맡은 책임에 맞는 결정권을 확보하는 힘입니다.", "높으면 책임과 권한이 함께 움직여 실력이 잘 드러납니다.", "낮으면 일은 맡지만 결정은 남이 하는 자리에 묶이기 쉽습니다."],
    "책임·권한 균형": ["맡은 범위와 결정권, 평가 기준이 균형 있게 주어지는 정도입니다.", "높으면 일의 부담이 성과와 평가로 이어집니다.", "낮으면 책임은 크고 권한은 약해 경력 피로가 커집니다."],
    "보상 협상력": ["성과를 자기 몫으로 확정하는 힘입니다.", "높으면 보상 기준을 말하고 받아낼 수 있습니다.", "낮으면 좋은 평가를 받고도 실제 보상은 작게 남습니다."],
    "전문 자산화": ["경험과 기술이 대체하기 어려운 전문성으로 굳어지는 힘입니다.", "높으면 시간이 지날수록 일의 단가와 신뢰가 올라갑니다.", "낮으면 일을 많이 해도 자기 이름의 전문 분야가 흐려집니다."],
    "조직 적응력": ["조직의 규칙과 사람 사이에서 자리를 잡는 힘입니다.", "높으면 조직 안에서도 자기 역할을 안정적으로 확보합니다.", "낮으면 규칙과 윗선의 방식 때문에 능력 발휘가 막힙니다."],
    "소속 전환력": ["소속이나 업무 환경이 바뀔 때 다시 자리 잡는 힘입니다.", "높으면 이직이나 부서 이동 뒤에도 적응이 빠릅니다.", "낮으면 환경 변화가 경력의 공백처럼 느껴질 수 있습니다."],
    "독립 가능성": ["직장 밖에서 자기 이름으로 일할 수 있는 힘입니다.", "높으면 독립, 프리랜스, 사업 운영에서 기회가 생깁니다.", "낮으면 독립보다 조직 안에서 기반을 갖출 때 안정됩니다."],
    "업무 조건 감별력": ["좋은 자리와 소모적인 자리를 구분하는 감각입니다.", "높으면 들어가기 전에 책임과 보상의 균형을 확인합니다.", "낮으면 이름 좋은 자리라도 실제 조건에서 손해를 볼 수 있습니다."],
    "끌림의 기준": ["마음이 움직이는 이유와 오래 끌리는 상대의 조건입니다.", "높으면 순간의 설렘과 오래 갈 상대를 구분합니다.", "낮으면 감정은 생겨도 관계의 방향을 늦게 판단합니다."],
    "상대 선택력": ["오래 갈 사람과 손상될 관계를 초기에 가려내는 힘입니다.", "높으면 상대의 말보다 생활 태도와 책임감을 봅니다.", "낮으면 초반의 분위기에 끌려 관계의 본질을 늦게 봅니다."],
    "상대 신뢰 감별력": ["상대의 반복된 행동에서 신뢰를 판단하는 감각입니다.", "높으면 말보다 약속을 지키는 방식을 중요하게 여깁니다.", "낮으면 표현은 많은데 책임이 약한 사람에게 흔들릴 수 있습니다."],
    "인연 형성력": ["호감이 실제 만남과 관계로 이어지는 힘입니다.", "높으면 인연이 생겼을 때 자연스럽게 접점이 늘어납니다.", "낮으면 마음은 있어도 만남이 이어지는 계기가 부족합니다."],
    "관계 진전력": ["호감이 교제와 약속으로 넘어가는 힘입니다.", "높으면 애매한 관계가 오래 머물지 않고 방향이 정리됩니다.", "낮으면 서로 마음이 있어도 관계가 늦게 확정됩니다."],
    "관계 주도권": ["관계의 속도와 거리를 스스로 정하는 힘입니다.", "높으면 끌려가기보다 자신의 기준으로 관계를 이끕니다.", "낮으면 상대의 속도에 맞추다 피로가 쌓입니다."],
    "관계 속도 조절력": ["가까워지는 속도와 멀어지는 속도를 조절하는 감각입니다.", "높으면 급한 감정에도 관계를 무리하게 밀어붙이지 않습니다.", "낮으면 가까워지는 속도와 기대치가 어긋나기 쉽습니다."],
    "애정 표현성": ["마음이 말과 행동으로 전달되는 정도입니다.", "높으면 상대가 애정의 방향을 분명히 느낍니다.", "낮으면 좋아해도 차갑거나 무심하게 보일 수 있습니다."],
    "정서 수용력": ["상대의 감정 변화와 불안을 받아주는 힘입니다.", "높으면 상대가 마음을 열고 기대기 쉽습니다.", "낮으면 감정보다 해결책을 먼저 내밀어 서운함이 생깁니다."],
    "관계 지속력": ["감정이 깊어진 뒤에도 관계를 오래 유지하는 힘입니다.", "높으면 시간이 지나도 책임감 있게 관계를 붙듭니다.", "낮으면 초반의 감정이 지나면 유지의 노력이 약해집니다."],
    "연락·거리 안정성": ["연락 빈도와 생활 거리에서 상대에게 안정감을 주는 정도입니다.", "높으면 바쁘더라도 관계의 기본 신호를 놓치지 않습니다.", "낮으면 마음과 달리 상대가 방치된 느낌을 받을 수 있습니다."],
    "오해 조정력": ["말이 엇갈렸을 때 관계를 다시 맞추는 힘입니다.", "높으면 오해가 생겨도 오래 끌지 않고 정리합니다.", "낮으면 작은 말이 오래 남아 관계의 온도를 떨어뜨립니다."],
    "갈등 관리력": ["싸움이 났을 때 선을 넘지 않고 수습하는 힘입니다.", "높으면 갈등이 생겨도 관계 자체를 무너뜨리지 않습니다.", "낮으면 한 번의 충돌이 이별의 명분으로 커질 수 있습니다."],
    "주변 개입 관리력": ["친구, 가족, 주변 시선이 관계에 들어오는 정도를 조절하는 힘입니다.", "높으면 두 사람의 문제를 밖으로 과하게 열지 않습니다.", "낮으면 주변 말이 관계 판단을 흔들기 쉽습니다."],
    "재회 가능성": ["끝난 관계가 다시 이어질 여지를 나타냅니다.", "높으면 감정이 완전히 끊기기보다 다시 확인되는 시기가 생깁니다.", "낮으면 한 번 정리된 관계는 되돌리기보다 새 방향으로 갑니다."],
    "결혼 연결력": ["연애가 결혼 논의로 이어지는 힘입니다.", "높으면 만남이 생활 약속과 미래 계획으로 넘어갑니다.", "낮으면 사랑은 있어도 결혼 이야기에서 속도가 늦어집니다."],
    "혼인 성향": ["결혼을 어떤 방식으로 받아들이는지 보여주는 기준입니다.", "높으면 감정보다 생활의 약속과 책임을 중요하게 둡니다.", "낮으면 결혼을 현실 문제로 정리하는 데 시간이 더 걸립니다."],
    "배우자상": ["오래 맞는 배우자의 성격과 생활 태도입니다.", "높으면 자신에게 맞는 배우자 조건을 비교적 분명히 압니다.", "낮으면 끌리는 사람과 오래 맞는 사람의 차이를 늦게 봅니다."],
    "결혼 적기": ["혼인 논의가 실제 약속으로 굳어지기 쉬운 시기입니다.", "높으면 결혼 이야기가 일정과 절차로 넘어갈 가능성이 큽니다.", "낮으면 결혼 의사는 있어도 시점이 늦어지거나 미뤄집니다."],
    "결혼 현실화력": ["결혼 의사가 집, 일정, 가족 협의로 넘어가는 힘입니다.", "높으면 말뿐인 약속이 실제 준비로 이어집니다.", "낮으면 마음은 있어도 현실 준비가 느리게 진행됩니다."],
    "생활 안정": ["결혼 생활 안에서 주거, 생활비, 역할 기준이 안정되는 정도입니다.", "높으면 생활의 기본 틀이 흔들리지 않습니다.", "낮으면 작은 생활 문제도 반복되면 큰 불만으로 쌓입니다."],
    "주거·생활 설계력": ["집, 생활비, 역할 분담을 계획으로 정리하는 힘입니다.", "높으면 결혼 후 생활의 부담을 미리 나누고 준비합니다.", "낮으면 준비 없이 시작해 생활비와 역할에서 마찰이 생깁니다."],
    "가정 운영력": ["부부 생활을 실제로 굴러가게 만드는 관리 능력입니다.", "높으면 집안일, 돈, 일정의 기본 질서가 잡힙니다.", "낮으면 마음은 있어도 생활 운영이 자주 흐트러집니다."],
    "부부 재정": ["공동 생활비와 개인 자산의 기준을 세우는 방식입니다.", "높으면 부부 사이에서도 돈의 기준이 분명합니다.", "낮으면 사랑과 돈이 섞여 서운함과 손해가 같이 생깁니다."],
    "생활비 기준성": ["고정 지출과 생활비 범위를 정하는 힘입니다.", "높으면 생활 수준이 올라가도 지출 기준이 유지됩니다.", "낮으면 생활비가 늘어나는 이유를 서로 다르게 받아들입니다."],
    "부부 갈등 조정력": ["의견이 부딪힐 때 생활을 무너뜨리지 않고 맞추는 힘입니다.", "높으면 갈등 뒤에도 역할과 책임을 다시 정리합니다.", "낮으면 같은 주제로 반복해서 다투기 쉽습니다."],
    "부부 갈등 회복성": ["상처가 생긴 뒤 다시 관계를 회복하는 힘입니다.", "높으면 싸움 뒤에도 관계가 완전히 꺾이지 않습니다.", "낮으면 한 번의 말이 오래 남아 관계의 여지를 줄입니다."],
    "가족 책임 경계력": ["양가와 원가족 문제에서 부부의 기준을 먼저 세우는 힘입니다.", "높으면 가족 문제도 부부의 합의 안에서 정리됩니다.", "낮으면 양가 문제로 부부 사이의 균형이 흔들립니다."],
    "배우자 가족 경계": ["배우자 가족과의 거리와 책임 범위를 정하는 힘입니다.", "높으면 예의와 경계를 함께 지킵니다.", "낮으면 상대 가족 문제를 개인의 부담으로 떠안기 쉽습니다."],
    "자녀·양육 책임": ["자녀 문제에서 책임과 생활 구조를 감당하는 힘입니다.", "높으면 양육과 생활 기준을 비교적 안정적으로 세웁니다.", "낮으면 자녀 문제로 시간과 재정 부담이 커집니다."],
    "배우자 복": ["배우자가 삶의 안정과 사회적 기반에 주는 힘입니다.", "높으면 결혼이 생활의 안정과 성장에 도움이 됩니다.", "낮으면 배우자 문제에서 기대보다 책임이 더 크게 느껴집니다."],
    "혼인 위기 대응력": ["결혼 생활의 위기에서 관계를 지키는 힘입니다.", "높으면 큰 갈등이 있어도 쉽게 끊지 않고 수습합니다.", "낮으면 생활 문제 하나가 관계 전체의 위기로 번집니다."],
    "결혼 지속력": ["결혼 생활을 오래 유지하는 힘입니다.", "높으면 시간이 지나도 약속과 책임이 쉽게 흐트러지지 않습니다.", "낮으면 감정보다 생활 피로가 관계를 약하게 만듭니다."],
    "혼인 갈등 조정력": ["양가, 생활비, 역할 문제처럼 결혼 안에서 부딪히는 문제를 조정하는 힘입니다.", "갈등이 생겨도 부부의 기준으로 다시 정리할 수 있습니다.", "가족 문제나 생활 책임이 부부 사이로 들어와 피로가 커집니다."],
    "초년에 형성되는 바탕": ["초년과 청년기에 성격, 진로, 관계 기준이 만들어지는 힘입니다.", "초기의 경험이 이후 선택의 기준으로 오래 남습니다.", "이 시기의 혼란을 정리하지 못하면 뒤늦게 방향을 다시 잡아야 합니다."],
    "중년에 굳어지는 성취": ["중년기에 직업, 평판, 자산의 형태가 실제로 굳어지는 힘입니다.", "그동안 쌓은 일이 사회적 자리와 생활 기반으로 남습니다.", "기반이 약하면 책임만 늘고 성취의 소유권은 약하게 남습니다."],
    "말년에 남는 안정": ["말년에 생활 기반과 자산, 관계가 얼마나 안정적으로 남는지 보여주는 힘입니다.", "후반으로 갈수록 삶의 중심이 단단해집니다.", "남는 기반이 약하면 지나온 성취에 비해 생활 안정감이 부족합니다."],
    "초년·청년의 형성": ["성격과 진로의 초기 기준이 만들어지는 구간입니다.", "초기의 시행착오가 이후 방향을 잡는 재료가 됩니다.", "기준이 늦게 잡히면 진로와 관계에서 돌아가는 시간이 생깁니다."],
    "중년의 성취": ["사회적 책임과 직업적 결과가 실제 이력으로 남는 구간입니다.", "중년 이후 성과가 이름, 자리, 자산으로 굳어집니다.", "성과가 흩어지면 책임에 비해 남는 결과가 작습니다."],
    "말년의 안정": ["후반 삶에서 생활 기반과 관계가 안정되는 정도입니다.", "말년으로 갈수록 삶의 중심이 정돈됩니다.", "기반이 약하면 가족, 돈, 건강 문제에 더 신경을 써야 합니다."],
    "운이 바뀌는 전환기": ["삶의 방향이 달라지는 시점을 받아들이고 다시 자리 잡는 힘입니다.", "변화가 왔을 때 새 기준을 세우는 속도가 빠릅니다.", "전환기를 놓치면 이전 방식으로 버티다 기회를 늦게 잡습니다."],
    "공적 인정 기반": ["공식 평가와 역할이 사회적 신뢰로 전환되는 힘입니다.", "높으면 맡은 일이 개인적 칭찬에 그치지 않고 공적인 이력으로 남습니다.", "낮으면 일을 해도 인정이 사적인 호평에 머물기 쉽습니다."],
    "사회적 인정이 붙는 자리": ["공식 평가와 역할이 사회적 신뢰로 전환되는 힘입니다.", "높으면 맡은 일이 개인적 칭찬에 그치지 않고 공적인 이력으로 남습니다.", "낮으면 일을 해도 인정이 사적인 호평에 머물기 쉽습니다."],
    "직책 상승력": ["성과와 평가가 실제 직책과 역할 확대로 이어지는 힘입니다.", "높으면 좋은 평가가 책임 있는 자리와 사회적 이름으로 굳어집니다.", "낮으면 평가가 있어도 기록과 절차가 약해 자리 상승이 늦어집니다."],
    "평가가 직함으로 이어지는 자리": ["성과와 평가가 실제 직책과 역할 확대로 이어지는 힘입니다.", "높으면 좋은 평가가 책임 있는 자리와 사회적 이름으로 굳어집니다.", "낮으면 평가가 있어도 기록과 절차가 약해 자리 상승이 늦어집니다."],
    "권한 기반 평판": ["결정권과 책임 범위가 분명해질수록 평판의 무게가 커지는 힘입니다.", "높으면 책임 있는 자리에 설수록 이름값이 함께 올라갑니다.", "낮으면 권한을 얻어도 기준이 흐려 평판이 부담으로 바뀝니다."],
    "권한이 붙을수록 커지는 평판": ["결정권과 책임 범위가 분명해질수록 평판의 무게가 커지는 힘입니다.", "높으면 책임 있는 자리에 설수록 이름값이 함께 올라갑니다.", "낮으면 권한을 얻어도 기준이 흐려 평판이 부담으로 바뀝니다."],
    "평판이 오래 남는 힘": ["한 번 얻은 신뢰와 이름이 오래 유지되는 힘입니다.", "높으면 시간이 지나도 좋은 인상이 자산으로 남습니다.", "낮으면 평가가 순간적으로 끝나 다음 기회로 이어지기 어렵습니다."],
    "공식 책임을 맡는 힘": ["공식 직함과 책임 있는 역할을 감당하는 힘입니다.", "높으면 이름이 남는 자리에서 역할을 맡기 쉽습니다.", "낮으면 책임 있는 자리가 부담으로 먼저 다가옵니다."],
    "명예를 지켜내는 기준": ["평판이 손상되는 자리를 피하고 이름을 지키는 기준입니다.", "높으면 불필요한 구설과 책임을 미리 피합니다.", "낮으면 애매한 부탁이나 책임이 명예 손상으로 이어집니다."],
    "기록·증빙 안정성": ["말로 끝난 약속을 기록과 증빙으로 남기는 힘입니다.", "평가와 책임 소재가 분명해져 이름을 지키는 데 유리합니다.", "구두 약속이나 공동 비용 문제가 평판 손상으로 번질 수 있습니다."],
    "사람을 얻는 힘": ["인맥의 숫자보다 오래 남는 신뢰를 만드는 힘입니다.", "높으면 적은 관계에서도 실질적인 사람이 남습니다.", "낮으면 만나는 사람은 많아도 오래 가는 인연이 줄어듭니다."],
    "도움으로 이어지는 인연": ["친분이 실제 도움과 조력으로 바뀌는 힘입니다.", "높으면 필요한 순간에 움직여주는 사람이 생깁니다.", "낮으면 말은 가까워도 실제 도움은 약합니다."],
    "관계가 오래 남는 힘": ["감정이 깊어진 뒤에도 관계를 유지하는 힘입니다.", "높으면 한 번 맺은 인연이 쉽게 끊기지 않습니다.", "낮으면 관계가 상황에 따라 쉽게 멀어집니다."],
    "오래 남는 사람을 고르는 기준": ["스쳐 가는 인연과 오래 갈 사람을 구분하는 기준입니다.", "관계의 양보다 사람의 질을 분명히 가립니다.", "기준이 흐리면 가까워진 뒤에야 부담이 드러납니다."],
    "말보다 행동으로 돕는 인연": ["말보다 실제 행동으로 힘이 되는 관계입니다.", "필요한 순간에 움직이는 사람이 곁에 남습니다.", "말뿐인 친분을 믿으면 기대에 비해 돌아오는 것이 약합니다."],
    "부탁과 책임의 경계": ["가까운 사람의 부탁이 부담으로 바뀌는 지점입니다.", "높으면 도울 일과 거절할 일을 구분합니다.", "낮으면 부탁을 받아들이다 책임까지 떠안기 쉽습니다."],
    "관계 책임 경계력": ["가까운 사람의 부탁과 내가 질 책임을 구분하는 힘입니다.", "호의를 베풀어도 내 책임 범위를 넘기지 않습니다.", "부탁을 받아들이다 관계와 책임이 함께 무거워집니다."],
  };
  if (profiles[label]) {
    const [definition, high, low] = profiles[label];
    return { definition, high, low };
  }
  const timingProfile = label.includes("연도")
    ? ["특정 해에 두드러지는 사건의 성격입니다.", "높게 잡힌 해에는 해당 영역의 결과가 비교적 선명하게 드러납니다.", "낮게 잡힌 해에는 무리한 확장보다 정리와 보존이 우선입니다."]
    : null;
  if (timingProfile) {
    const [definition, high, low] = timingProfile;
    return { definition, high, low };
  }
  const domainProfiles = {
    personality: ["성격과 행동 방식에서 해당 요소가 차지하는 비중입니다.", "높으면 그 성향이 선택과 관계에서 뚜렷하게 드러납니다.", "낮으면 같은 상황에서도 반응이 늦거나 주변 조건의 영향을 더 받습니다."],
    money: ["재물이 생기고 남고 보호되는 과정에서 해당 요소가 차지하는 비중입니다.", "높으면 돈의 흐름이 실제 이익과 자산으로 남기 쉽습니다.", "낮으면 수입이 있어도 보존과 권리 확정에서 빈틈이 생깁니다."],
    career: ["직업 선택, 평가, 보상, 경력 유지에서 해당 요소가 작용하는 정도입니다.", "높으면 경력의 방향과 결과가 분명해집니다.", "낮으면 노력에 비해 자리와 보상이 늦게 따라옵니다."],
    love: ["호감, 선택, 표현, 관계 유지에서 해당 요소가 작용하는 정도입니다.", "높으면 감정이 관계의 형태로 안정되기 쉽습니다.", "낮으면 마음은 있어도 관계가 불분명하게 머물 수 있습니다."],
    marriage: ["결혼 결정, 생활 안정, 가족 책임에서 해당 요소가 작용하는 정도입니다.", "높으면 결혼이 현실의 약속과 생활 질서로 굳어집니다.", "낮으면 감정과 생활 조건 사이의 차이가 크게 느껴집니다."],
    timing: ["해당 시기에 사건으로 드러나는 힘의 방향입니다.", "높게 잡힌 시기에는 성취와 변화가 비교적 분명하게 나타납니다.", "낮게 잡힌 시기에는 손실을 줄이고 기준을 세우는 일이 중요합니다."],
    life: ["인생 구간별 중심 과제가 형성되는 방식입니다.", "높으면 그 시기의 경험이 이후 삶의 기반으로 남습니다.", "낮으면 지나간 경험을 다시 정리해야 다음 구간이 안정됩니다."],
    honor: ["사회적 이름, 공식 평가, 평판 유지에 관여하는 요소입니다.", "높으면 이름과 신뢰가 오래 남는 방식으로 평가받습니다.", "낮으면 실력에 비해 평판 관리의 부담이 커집니다."],
    social: ["관계의 규모, 신뢰, 도움, 책임 경계에 관여하는 요소입니다.", "높으면 필요한 사람과 오래 갈 인연을 구분합니다.", "낮으면 관계는 생겨도 실질적인 도움과 신뢰가 약해집니다."],
  };
  const fallback = domainProfiles[domain] || ["해당 영역의 결과에 반영되는 세부 요소입니다.", "높으면 해당 영역의 장점이 분명하게 드러납니다.", "낮으면 같은 요소가 부담이나 지연으로 나타납니다."];
  return { definition: fallback[0], high: fallback[1], low: fallback[2] };
}

function premiumVisualMetricPool(section) {
  const domain = premiumSectionDomain(section);
  const definitions = new Map();
  const addDefinition = (title, definition) => {
    const key = premiumTopicMatchKey(title || "");
    const body = cleanPremiumDisplayText(definition || "");
    if (key && body && !definitions.has(key)) {
      definitions.set(key, body);
    }
  };
  ["topic_items", "required_judgment_cards"].forEach((key) => {
    const list = Array.isArray(section?.[key]) ? section[key] : [];
    list.forEach((item) => addDefinition(item?.title || item?.label, item?.meaning || item?.definition));
  });

  const rawItems = [
    ...premiumMetricSourceItems(section?.required_judgment_cards, "required"),
    ...premiumMetricSourceItems(section?.judgment_axes, "axis"),
    ...premiumMetricSourceItems(section?.topic_items, "topic"),
    ...premiumMetricSourceItems(section?.product_story?.items, "story"),
  ];
  const seen = new Map();
  rawItems.forEach((item, index) => {
    if (!item || typeof item !== "object") {
      return;
    }
    const rawTitle = cleanCustomerLabel(item.title || item.label || item.source_title || "");
    const title = premiumDisplayAxisLabel(rawTitle);
    const key = premiumTopicMatchKey(title);
    if (!key || !title) {
      return;
    }
    const rawScore = Number(item.score);
    const hasNumericScore = Number.isFinite(rawScore);
    const rawMetricValue = item.value || item.grade || item.tone || item.role || "";
    if (!hasNumericScore && !String(rawMetricValue || "").trim()) {
      return;
    }
    const negativeAxis = premiumMetricIsNegativeAxis(rawTitle);
    const numericScore = hasNumericScore ? Math.max(0, Math.min(100, rawScore)) : 56;
    const score = Number.isFinite(rawScore)
      ? (negativeAxis ? 100 - numericScore : numericScore)
      : premiumMetricScoreFromValue(rawMetricValue, item.tone || item.role || "");
    const level = premiumMetricLevel(score);
    const toneText = String(item.tone || item.role || "").toLowerCase();
    const tone = score < 55 || (!hasNumericScore && (toneText.includes("watch") || toneText.includes("risk")))
      ? "watch"
      : score >= 70
        ? "strong"
        : "neutral";
    const definition =
      premiumMetricDefinition(domain, title) ||
      definitions.get(key) ||
      cleanPremiumDisplayText(item.meaning || item.definition || "");
    const profile = premiumMetricDefinitionProfile(domain, title);
    const metric = {
      key,
      title,
      score,
      level: level.label,
      percent: level.percent,
      tone,
      definition,
      highText: profile?.high || "",
      lowText: profile?.low || "",
      sourceIndex: index,
      sourceKind: item.__metricSource || "",
      sourcePriority: premiumMetricSourcePriority(item.__metricSource || ""),
    };
    const existing = seen.get(key);
    if (!existing) {
      seen.set(key, metric);
      return;
    }
    if (metric.sourcePriority !== existing.sourcePriority) {
      if (metric.sourcePriority > existing.sourcePriority) {
        seen.set(key, { ...metric, sourceIndex: existing.sourceIndex });
      }
      return;
    }
    const existingPriority = existing.definition && existing.definition !== premiumMetricDefinition(domain, existing.title) ? 2 : 0;
    const metricPriority = metric.definition && metric.definition !== premiumMetricDefinition(domain, metric.title) ? 2 : 0;
    if (metricPriority > existingPriority || Math.abs(metric.score - 56) > Math.abs(existing.score - 56)) {
      seen.set(key, { ...metric, sourceIndex: existing.sourceIndex });
    }
  });
  return [...seen.values()].sort((a, b) => a.sourceIndex - b.sourceIndex);
}

function premiumMetricSourceItems(items, sourceKind) {
  return (Array.isArray(items) ? items : [])
    .filter((item) => item && typeof item === "object")
    .map((item) => ({ ...item, __metricSource: sourceKind }));
}

function premiumMetricSourcePriority(sourceKind) {
  if (sourceKind === "required") {
    return 4;
  }
  if (sourceKind === "axis") {
    return 3;
  }
  if (sourceKind === "topic") {
    return 2;
  }
  if (sourceKind === "story") {
    return 1;
  }
  return 0;
}

function premiumRepresentativeMetrics(section) {
  const pool = premiumVisualMetricPool(section);
  const representativePool = pool.filter((item) => !premiumMetricIsTimingLike(item));
  const strongTarget = Math.min(3, representativePool.filter((item) => item.score >= 65).length);
  const watchTarget = Math.min(3, representativePool.filter((item) => item.score < 55).length);
  let selectedKeys = new Set();
  let strong = representativePool
    .filter((item) => item.score >= 65)
    .sort((a, b) => b.score - a.score)
    .slice(0, strongTarget);
  strong.forEach((item) => selectedKeys.add(item.key));
  let watch = representativePool
    .filter((item) => item.score < 55 && !selectedKeys.has(item.key))
    .sort((a, b) => a.score - b.score)
    .slice(0, watchTarget);
  return {
    strong,
    watch,
    all: pool,
  };
}

function premiumMetricIsTimingLike(item) {
  const text = cleanCustomerLabel(`${item?.title || ""} ${item?.key || ""}`);
  if (!text) {
    return false;
  }
  return /(연도|강세연도|주의연도|전환연도|결혼적기|시기|타이밍)$/u.test(text.replace(/\s+/g, ""));
}

function renderPremiumVisualMetricBoard(section) {
  const model = premiumRepresentativeMetrics(section);
  if (!model.strong.length && !model.watch.length) {
    return "";
  }
  return `
    <section class="premium-visual-metric-board domain-${escapeHtml(premiumSectionDomain(section))}" aria-label="${escapeHtml(`${premiumNavTitle(section)} 시각 요약`)}">
      <header>
        <span>5단계 요약</span>
        <strong>핵심 지표</strong>
      </header>
      <ol class="premium-metric-scale" aria-label="5단계 지표 기준">
        <li>위험</li><li>주의</li><li>보통</li><li>좋음</li><li>매우 좋음</li>
      </ol>
      <div class="premium-visual-metric-columns">
        ${renderPremiumVisualMetricColumn("강점 항목", model.strong, "strong")}
        ${renderPremiumVisualMetricColumn("주의 항목", model.watch, "watch")}
      </div>
      ${renderPremiumVisualDetailDrawer(section, model)}
    </section>
  `;
}

function premiumVisualDetailItems(model) {
  return (Array.isArray(model?.all) ? model.all : [])
    .filter((item) => item?.key && item?.title)
    .slice(0, 24);
}

function renderPremiumVisualDetailDrawer(section, model) {
  const items = premiumVisualDetailItems(model);
  if (!items.length) {
    return "";
  }
  return `
    <details class="premium-visual-detail-drawer">
      <summary>
        <span>전체 항목 보기</span>
        <b>${escapeHtml(`${items.length}개 항목`)}</b>
      </summary>
      <div class="premium-visual-detail-grid" aria-label="${escapeHtml(`${premiumNavTitle(section)} 세부 항목`)}">
        ${items.map(renderPremiumVisualDetailMetricCard).join("")}
      </div>
    </details>
  `;
}

function renderPremiumVisualDetailMetricCard(item) {
  const score = Number.isFinite(Number(item.score)) ? Math.max(0, Math.min(100, Number(item.score))) : 56;
  const level = premiumMetricLevel(score);
  const width = Math.max(8, Math.min(100, level.percent));
  const tone =
    item.tone === "watch" || score < 55
      ? "watch"
      : item.tone === "strong" || score >= 70
        ? "strong"
        : "neutral";
  return `
    <article class="premium-visual-detail-card is-${escapeHtml(tone)}">
      <div class="premium-visual-detail-card-head">
        <strong>${escapeHtml(item.title)}</strong>
      </div>
      <div class="premium-visual-detail-card-meta">
        <span>지표 수준</span>
        <b>${escapeHtml(level.label)}</b>
      </div>
      <div class="premium-visual-meter" aria-label="${escapeHtml(`${item.title} ${level.label}`)}">
        <i style="width:${width}%"></i>
      </div>
      <p>${escapeHtml(item.definition || "해당 영역의 결과에 반영되는 세부 요소입니다.")}</p>
    </article>
  `;
}

function renderPremiumVisualMetricColumn(title, items, tone) {
  if (!items.length) {
    return "";
  }
  return `
    <div class="premium-visual-metric-column is-${escapeHtml(tone)}">
      <h4>${escapeHtml(title)}</h4>
      ${items.map((item) => renderPremiumVisualMetricCard(item, tone)).join("")}
    </div>
  `;
}

function renderPremiumVisualMetricCard(item, fallbackTone = "neutral") {
  const tone = fallbackTone === "watch"
    ? "watch"
    : fallbackTone === "strong"
      ? "strong"
      : item.tone === "watch"
        ? "watch"
        : item.tone === "strong"
          ? "strong"
          : "neutral";
  const rawScore = Number.isFinite(Number(item.score)) ? Math.max(0, Math.min(100, Number(item.score))) : 56;
  const displayScore = rawScore;
  const displayLevel = premiumMetricLevel(displayScore);
  const width = Math.max(8, Math.min(100, displayLevel.percent));
  const levelCaption = "지표 수준";
  const noteLabel = tone === "watch" ? "낮게 나오면" : "높게 나오면";
  const noteText = premiumMetricOutcomeText(tone === "watch" ? item.lowText : item.highText);
  return `
    <article class="premium-visual-metric-card is-${escapeHtml(tone)}">
      <header>
        <strong>${escapeHtml(item.title)}</strong>
        <div class="premium-visual-metric-level">
          <span>${escapeHtml(levelCaption)}</span>
          <b>${escapeHtml(displayLevel.label)}</b>
        </div>
      </header>
      <div class="premium-visual-meter" aria-label="${escapeHtml(`${item.title} ${levelCaption} ${displayLevel.label}`)}">
        <i style="width:${width}%"></i>
      </div>
      <p>${escapeHtml(item.definition)}</p>
      ${noteText ? `
        <div class="premium-visual-metric-note">
          <span>${escapeHtml(noteLabel)}</span>
          <em>${escapeHtml(noteText)}</em>
        </div>
      ` : ""}
    </article>
  `;
}

function premiumMetricOutcomeText(text) {
  return cleanPremiumDisplayText(text || "")
    .replace(/^(높으면|낮으면|높게 잡힌 해에는|낮게 잡힌 해에는|높게 잡힌 시기에는|낮게 잡힌 시기에는)\s*/u, "")
    .trim();
}

function renderPremiumVisualMetricDrawer(section) {
  const model = premiumRepresentativeMetrics(section);
  if (!model.all.length) {
    return "";
  }
  return `
    <details class="premium-visual-detail-drawer">
      <summary>
        <span>전체 세부 지표 보기</span>
        <b>전체 ${model.all.length}개 항목</b>
      </summary>
      <div class="premium-visual-detail-grid">
        ${model.all.map((item) => renderPremiumVisualMetricCard(item, item.tone)).join("")}
      </div>
    </details>
  `;
}

function renderPremiumProductStoryItem(item) {
  const role = item.role === "strong" || item.role === "watch" ? item.role : "scene";
  return `
    <article class="is-${escapeHtml(role)}">
      ${item.label ? `<span>${escapeHtml(item.label)}</span>` : ""}
      ${item.title ? `<b>${escapeHtml(item.title)}</b>` : ""}
      ${item.value ? `<em>${escapeHtml(item.value)}</em>` : ""}
      ${item.body ? `<p>${escapeHtml(firstSentences(item.body, 2))}</p>` : ""}
    </article>
  `;
}

function renderPremiumProductInterpretation(section) {
  const model = premiumProductInterpretation(section);
  if (!model) {
    return "";
  }
  return `
    <section class="premium-product-interpretation domain-${escapeHtml(model.domain)}" aria-label="${escapeHtml(`${model.title} 핵심 해석`)}">
      <header>
        <span>${escapeHtml(model.title)} 요약</span>
        <strong>${escapeHtml(model.verdictTitle)}</strong>
      </header>
      ${model.summary ? `<p class="premium-product-interpretation-lead">${escapeHtml(model.summary)}</p>` : ""}
      ${renderPremiumProductThesis(model)}
      <div class="premium-product-interpretation-grid">
        ${renderPremiumProductInterpretationItem(model.strong, "strong", model.domain)}
        ${renderPremiumProductInterpretationItem(model.scene, "scene", model.domain)}
        ${renderPremiumProductInterpretationItem(model.watch, "watch", model.domain)}
      </div>
    </section>
  `;
}

function renderPremiumProductThesis(model) {
  const paragraphs = premiumProductThesisParagraphs(model)
    .map((paragraph) => cleanPremiumDisplayText(paragraph || ""))
    .filter(Boolean);
  if (!paragraphs.length) {
    return "";
  }
  return `
    <div class="premium-product-thesis" aria-label="${escapeHtml(model.title)} 상세 결론">
      ${paragraphs.map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`).join("")}
    </div>
  `;
}

function premiumProductThesisParagraphs(model) {
  const domain = model?.domain || "";
  const strongTitle = cleanCustomerLabel(model?.strong?.title || "");
  const strongBody = firstSentences(model?.strong?.body || "", 2);
  const sceneTitle = cleanCustomerLabel(model?.scene?.title || "");
  const sceneBody = firstSentences(model?.scene?.body || "", 2);
  const watchTitle = cleanCustomerLabel(model?.watch?.title || "");
  const watchBody = firstSentences(model?.watch?.body || "", 2);
  const paragraphs = [];
  const add = (text) => {
    const cleaned = cleanPremiumDisplayText(text || "");
    if (cleaned && !paragraphs.some((item) => normalizedSentenceKey(item) === normalizedSentenceKey(cleaned))) {
      paragraphs.push(cleaned);
    }
  };
  if (domain === "personality") {
    add(strongTitle ? `성격의 바탕은 ${strongTitle}에서 먼저 드러납니다. ${strongBody}` : strongBody);
    add(sceneTitle ? `사람을 대할 때는 ${sceneTitle}이 강하게 나타납니다. ${sceneBody}` : sceneBody);
    add(watchTitle ? `압박을 받을 때는 ${watchTitle}이 문제가 됩니다. ${watchBody}` : watchBody);
    return paragraphs.slice(0, 3);
  }
  if (domain === "money") {
    add(strongTitle ? `재물운의 핵심은 ${strongTitle}입니다. ${strongBody}` : strongBody);
    add(sceneTitle ? `현실에서는 ${sceneTitle}에서 재물의 격차가 벌어집니다. ${sceneBody}` : sceneBody);
    add(watchTitle ? `주의할 대목은 ${watchTitle}입니다. ${watchBody}` : watchBody);
    return paragraphs.slice(0, 3);
  }
  if (domain === "career") {
    add(strongTitle ? `직업운은 ${strongTitle}에서 가장 뚜렷합니다. ${strongBody}` : strongBody);
    add(sceneTitle ? `현실에서는 ${sceneTitle}을 맡을 때 경력이 분명하게 남습니다. ${sceneBody}` : sceneBody);
    add(watchTitle ? `경계할 자리는 ${watchTitle}입니다. ${watchBody}` : watchBody);
    return paragraphs.slice(0, 3);
  }
  if (domain === "love") {
    add(strongTitle ? `연애운의 결론은 ${strongTitle}입니다. ${strongBody}` : strongBody);
    add(sceneTitle ? `관계가 깊어지는 장면은 ${sceneTitle}에서 확인됩니다. ${sceneBody}` : sceneBody);
    add(watchTitle ? `주의할 대목은 ${watchTitle}입니다. ${watchBody}` : watchBody);
    return paragraphs.slice(0, 3);
  }
  if (domain === "marriage") {
    add(strongTitle ? `결혼운은 ${strongTitle}에서 안정됩니다. ${strongBody}` : strongBody);
    add(sceneTitle ? `생활로 들어가면 ${sceneTitle}이 결혼의 실제 기준이 됩니다. ${sceneBody}` : sceneBody);
    add(watchTitle ? `결혼에서 조심할 지점은 ${watchTitle}입니다. ${watchBody}` : watchBody);
    return paragraphs.slice(0, 3);
  }
  if (domain === "timing") {
    add(strongTitle ? `좋은 연도는 ${strongTitle} 쪽으로 작용합니다. ${strongBody}` : strongBody);
    add(watchTitle ? `주의 연도는 ${watchTitle}이 먼저 올라옵니다. ${watchBody}` : watchBody);
    return paragraphs.slice(0, 2);
  }
  add(strongBody);
  add(sceneBody);
  add(watchBody);
  return paragraphs.slice(0, 3);
}

function renderPremiumProductInterpretationItem(item, tone, domain = "") {
  if (!item || (!item.title && !item.body && !item.note)) {
    return "";
  }
  const labelsByDomain = {
    personality: { strong: "성격의 강점", scene: "사람을 대하는 방식", watch: "압박을 받을 때" },
    money: { strong: "재물의 강점", scene: "자산이 남는 방식", watch: "손실이 생기는 자리" },
    career: { strong: "직업의 강점", scene: "경력이 남는 방식", watch: "경력이 손상되는 자리" },
    love: { strong: "강한 연애", scene: "관계가 깊어지는 방식", watch: "관계가 흔들리는 자리" },
    marriage: { strong: "강한 결혼", scene: "생활이 안정되는 방식", watch: "반복 부담이 생기는 자리" },
    timing: { strong: "상승 연도", scene: "연도별 사건", watch: "주의 연도" },
  };
  const labels = labelsByDomain[domain] || {
    strong: "강한 결과",
    scene: "현실 양상",
    watch: "주의 기준",
  };
  return `
    <article class="is-${escapeHtml(tone)}">
      <span>${escapeHtml(labels[tone] || "해석")}</span>
      ${item.title ? `<b>${escapeHtml(item.title)}</b>` : ""}
      ${item.body ? `<p>${escapeHtml(item.body)}</p>` : ""}
      ${item.note ? `<em>${escapeHtml(item.note)}</em>` : ""}
    </article>
  `;
}

function premiumProductInterpretation(section) {
  if (!section) {
    return null;
  }
  const domain = premiumSectionDomain(section);
  const title = premiumNavTitle(section);
  const summary = premiumProductSummaryText(section);
  const strong = premiumProductPoint(section, "strong");
  const scene = premiumProductPoint(section, "scene");
  const watch = premiumProductPoint(section, "watch");
  const verdictTitle = premiumProductVerdictTitle(section, strong, watch);
  if (!summary && !strong && !scene && !watch) {
    return null;
  }
  return {
    domain,
    title,
    verdictTitle,
    summary,
    strong,
    scene,
    watch,
  };
}

function premiumProductSummaryText(section) {
  const candidates = [
    section?.section_profile?.summary,
    section?.summary,
    section?.lead,
    premiumSectionHeadline(section),
  ];
  for (const candidate of candidates) {
    const text = cleanPremiumDisplayText(candidate || "");
    if (text) {
      return firstSentences(text, premiumSectionDomain(section) === "timing" ? 1 : 3);
    }
  }
  return "";
}

function premiumProductPoint(section, role) {
  const domain = premiumSectionDomain(section);
  const storyCards = Array.isArray(section?.section_story_cards) ? section.section_story_cards : [];
  const detailBlocks = Array.isArray(section?.detail_blocks) ? section.detail_blocks : [];
  const topicItems = Array.isArray(section?.topic_items) ? section.topic_items : [];
  const sources = [];
  if (role === "strong") {
    sources.push(
      storyCards.find((card) => String(card?.label || "").includes("강점")),
      storyCards.find((card) => card?.tone === "strong"),
      detailBlocks.find((item) => item?.tone === "strong"),
      topicItems.find((item) => item?.tone === "strong"),
    );
  } else if (role === "scene") {
    sources.push(
      storyCards.find((card) => String(card?.label || "").includes("생활")),
      detailBlocks.find((item) => item?.body && !["strong", "watch", "risk"].includes(item?.tone || "")),
      topicItems.find((item) => item?.body && !["strong", "watch", "risk"].includes(item?.tone || "")),
    );
  } else {
    sources.push(
      storyCards.find((card) => String(card?.label || "").includes("주의") || card?.tone === "watch" || card?.tone === "risk"),
      detailBlocks.find((item) => item?.tone === "watch" || item?.tone === "risk"),
      topicItems.find((item) => item?.tone === "watch" || item?.tone === "risk"),
    );
  }
  const source = sources.find(Boolean);
  if (!source) {
    return null;
  }
  const title = cleanCustomerLabel(source.title || source.display_label || source.label || "");
  const rawBody = cleanPremiumDisplayText(source.body || source.result || source.focus || source.definition || "");
  const note = premiumProductPointNote(source);
  return {
    title,
    body: firstSentences(premiumProductPointBody(domain, role, title, rawBody), 2),
    note,
  };
}

function premiumProductPointBody(domain, role, title, body) {
  const cleanTitle = cleanCustomerLabel(title || "");
  const text = cleanPremiumDisplayText(body || "");
  const expansion = premiumProductPointExpansion(domain, role, cleanTitle);
  if (text.length >= 44) {
    if (sentenceList(text).length < 2 && expansion && !sentenceAlreadyShown(expansion, text)) {
      return `${text} ${expansion}`;
    }
    return text;
  }
  const fallback = {
    personality: {
      strong: "중요한 선택 앞에서 남의 판단에 쉽게 끌려가지 않습니다. 맡은 일과 관계에서도 본인이 확인한 기준을 끝까지 지키는 편입니다.",
      scene: "사람을 가까이 두는 속도가 빠르지 않습니다. 믿을 만하다고 판단한 관계는 오래 두지만, 무례와 책임 전가는 분명하게 가릅니다.",
      watch: "압박을 받으면 말이 단호해지고 타협의 폭이 좁아집니다. 이때는 상대의 말보다 책임 범위와 결과를 먼저 확인하려 합니다.",
    },
    money: {
      strong: "돈이 단순 소비로 끝나지 않고 권리와 소유로 남기 쉬운 재물운입니다. 수입보다 귀속이 분명한 자산에서 결과가 큽니다.",
      scene: "현금 유입만으로 승부하는 사주가 아닙니다. 명의, 지분, 장기 계약처럼 자기 이름으로 남는 방식에서 재물의 격이 올라갑니다.",
      watch: "가까운 사람과 돈을 묶으면 처음의 호의가 나중에는 몫과 명의 문제로 바뀝니다. 이 사주는 금전 관계에서 선을 늦게 긋는 일이 손실로 이어집니다.",
    },
    career: {
      strong: "직업운은 책임을 맡을수록 강해집니다. 다만 그 책임이 직함, 실적, 평판으로 남아야 경력의 값이 올라갑니다.",
      scene: "여러 이해관계가 얽힌 일을 정리하고 기준을 세울 때 강점이 드러납니다. 단순 보조보다 결과의 소유자가 되는 자리에서 운이 살아납니다.",
      watch: "책임만 크고 결정권이 약한 자리는 피해야 합니다. 해낸 일의 이름이 남지 않으면 직업운이 소모됩니다.",
    },
    love: {
      strong: "연애는 가벼운 설렘보다 신뢰가 확인된 관계에서 깊어집니다. 마음을 준 뒤에는 쉽게 물러서지 않는 편입니다.",
      scene: "반복해서 마주치는 생활권 안에서 호감이 커집니다. 상대가 책임 있는 태도를 보이면 관계가 빠르게 진지해집니다.",
      watch: "마음이 있어도 표현이 늦으면 상대는 확신을 받지 못합니다. 애정을 행동으로만 보이면 관계의 온도가 다르게 읽힙니다.",
    },
    marriage: {
      strong: "결혼운은 감정이 생활 질서로 넘어갈 때 강해집니다. 주거와 재정 기준이 잡히면 관계의 지속성이 높습니다.",
      scene: "결혼 이야기는 말보다 실제 준비에서 구체화됩니다. 집, 생활비, 가족 책임이 정리될수록 결정이 빨라집니다.",
      watch: "원가족 문제가 부부 사이로 들어오면 부담이 커집니다. 결혼 전부터 책임의 범위를 분명히 해야 안정됩니다.",
    },
  };
  const domainFallback = fallback[domain] || {};
  if (text && expansion) {
    return `${text} ${expansion}`;
  }
  if (domainFallback[role]) {
    return domainFallback[role];
  }
  return text || cleanTitle;
}

function premiumProductPointExpansion(domain, role, title) {
  const titleText = cleanCustomerLabel(title || "");
  const byDomain = {
    personality: {
      strong: "선택이 커질수록 자기 기준이 먼저 서고, 쉽게 휘둘리지 않는 성격이 분명해집니다.",
      scene: "가까운 관계에서도 상대의 태도와 책임감을 오래 확인한 뒤 관계를 진전시킵니다.",
      watch: "압박이 커지면 말투가 단호해지고 타협의 폭이 좁아질 수 있습니다.",
    },
    money: {
      strong: "수입이 생겼을 때 소비보다 권리, 소유, 회수 가능성이 남는 쪽으로 재물이 굳어집니다.",
      scene: "현실에서는 급여보다 계약 단위, 보유 자산, 회수 가능한 권리에서 차이가 커집니다.",
      watch: "가까운 사람의 부탁, 공동 명의, 가족 지원금이 나중에 손익 분쟁으로 바뀌기 쉽습니다.",
    },
    career: {
      strong: "성과가 문서, 직함, 공식 평가로 남을 때 경력의 가치가 확실히 올라갑니다.",
      scene: "운영, 조율, 책임 범위가 분명한 자리에서 실력이 제대로 드러납니다.",
      watch: "권한 없이 책임만 지는 자리는 경력보다 소모가 먼저 남습니다.",
    },
    love: {
      strong: "쉽게 지나가는 호감보다 신뢰가 확인된 관계에서 관계가 깊어집니다.",
      scene: "반복해서 마주치는 생활권 안에서 호감이 굳어지고, 상대의 태도가 관계를 진지하게 만듭니다.",
      watch: "좋아하는 마음이 있어도 표현이 늦으면 상대는 확신을 갖기 어렵습니다.",
    },
    marriage: {
      strong: "감정이 깊어진 뒤 생활 기준까지 맞아야 결혼이 안정적으로 굳어집니다.",
      scene: "집, 생활비, 가족 책임이 정리될수록 결혼 이야기가 현실로 넘어갑니다.",
      watch: "원가족 문제와 주거 조건이 흐리면 부부 사이의 부담으로 남습니다.",
    },
  };
  if (byDomain[domain]?.[role]) {
    if (role === "watch" && titleText) {
      return `${titleText}은 실제 손실이나 갈등으로 이어질 수 있습니다. ${byDomain[domain][role]}`;
    }
    return byDomain[domain][role];
  }
  return "";
}

function premiumProductPointNote(source) {
  const bullets = Array.isArray(source?.bullets) ? source.bullets : Array.isArray(source?.scenes) ? source.scenes : [];
  const first = bullets.map((item) => cleanPremiumDisplayText(item || "")).find(Boolean);
  if (first) {
    return firstSentences(first, 1);
  }
  const value = cleanCustomerLabel(source?.value || source?.grade || "");
  if (value && !["주의", "보통", "평균권"].includes(value)) {
    return value;
  }
  return "";
}

function premiumProductVerdictTitle(section, strong, watch) {
  const domain = premiumSectionDomain(section);
  const headline = cleanPremiumDisplayText(premiumSectionHeadline(section));
  if (domain === "money") {
    return headline || "재물은 자산화 능력이 강하고, 사람과 얽힌 돈에서 손실이 드러납니다.";
  }
  if (domain === "career") {
    return headline || "직업은 평가가 붙는 자리에서 강하고, 권한 없는 책임에서 손실이 납니다.";
  }
  if (domain === "love") {
    return headline || "연애는 오래 갈 관계에 강하고, 표현이 늦어질 때 흔들립니다.";
  }
  if (domain === "marriage") {
    return headline || "결혼은 생활 기반에 강하고, 가족 책임이 과해질 때 부담이 커집니다.";
  }
  if (domain === "timing") {
    return headline || "상승 연도와 주의 연도가 분명하게 갈립니다.";
  }
  if (strong?.title && watch?.title) {
    return `${strong.title}은 강점이고, ${watch.title}은 주의 지점입니다.`;
  }
  return headline || `${premiumNavTitle(section)}의 핵심 결과입니다.`;
}

function renderPremiumCoreDossier(section) {
  const dossier = premiumCoreDossier(section);
  if (!dossier) {
    return "";
  }
  const labels = premiumCoreDossierLabels(dossier.domain);
  const judgmentHeadline = premiumCoreDossierJudgmentHeadline(dossier);
  const pointContext = [dossier.verdict, judgmentHeadline].filter(Boolean).join(" ");
  const verdict = removeShownSentences(dossier.verdict || "", judgmentHeadline, 1);
  const details = renderPremiumCoreDetailCards(section);
  const requiredJudgments = renderPremiumRequiredJudgmentCards(section);
  const basis = renderPremiumCoreDossierBasis(section);
  const basisChips = renderPremiumCoreBasisChips(section);
  const experienceBoard = renderPremiumCoreExperienceBoard(section);
  return `
    <section class="premium-core-dossier domain-${escapeHtml(dossier.domain)}" aria-label="핵심 운세 진단">
      <header>
        <div>
          <span>${escapeHtml(dossier.label)}</span>
          <strong>${escapeHtml(dossier.type)}</strong>
        </div>
        ${dossier.grade ? `<b>${escapeHtml(dossier.grade)}</b>` : ""}
      </header>
      ${renderPremiumCoreDossierJudgment(dossier, judgmentHeadline)}
      ${basisChips}
      ${verdict ? `<p class="premium-core-dossier-verdict">${escapeHtml(firstSentences(verdict, 1))}</p>` : ""}
      ${experienceBoard}
      <div class="premium-core-dossier-grid">
        ${renderPremiumCoreDossierPoint(labels.strong, dossier.strong, "strong", pointContext)}
        ${renderPremiumCoreDossierPoint(labels.watch, dossier.watch, "watch", pointContext)}
        ${renderPremiumCoreDossierPoint(labels.scene, dossier.scene, "scene", pointContext)}
      </div>
      ${details}
      ${requiredJudgments}
      ${renderPremiumCoreDossierMetrics(dossier.metrics)}
      ${basis ? renderPremiumCoreBasisDrawer(basis) : ""}
    </section>
  `;
}

function renderPremiumCoreExperienceBoard(section) {
  const story = premiumProductStory(section);
  const domain = premiumSectionDomain(section);
  const storyItems = Array.isArray(story.items)
    ? story.items
        .map((item) => ({
          role: item?.role === "watch" ? "watch" : item?.role === "strong" ? "strong" : "scene",
          label: cleanCustomerLabel(item?.label || ""),
          title: cleanCustomerLabel(item?.title || ""),
          body: cleanPremiumDisplayText(item?.body || ""),
        }))
        .filter((item) => item.title || item.body)
    : [];
  const detailScenes = premiumDictionaryItems(section)
    .map((detail) => ({
      role: detail.level === "watch" || detail.level === "risk" ? "watch" : detail.level === "strong" ? "strong" : "scene",
      label: detail.level === "watch" ? "주의 장면" : detail.level === "strong" ? "강한 장면" : "현실 장면",
      title: cleanCustomerLabel(detail.title || ""),
      body: cleanPremiumDisplayText(detail.judgment || ""),
      scenes: Array.isArray(detail.scenes) ? detail.scenes.slice(0, 2) : [],
    }))
    .filter((item) => item.title || item.body || item.scenes?.length);
  const selected = premiumCoreExperienceItems(domain, storyItems, detailScenes);
  if (!selected.length) {
    return "";
  }
  const labels = {
    personality: ["성격의 실제 모습", "선택과 관계에서 드러나는 장면입니다."],
    money: ["재물의 실제 모습", "돈이 생기고 남고 손상되는 장면입니다."],
    career: ["직업의 실제 모습", "평가와 경력에서 드러나는 장면입니다."],
    love: ["연애의 실제 모습", "마음이 움직이고 관계가 흔들리는 장면입니다."],
    marriage: ["결혼의 실제 모습", "생활과 가족 문제에서 드러나는 장면입니다."],
  };
  const [title, caption] = labels[domain] || ["실제 모습", "해당 영역에서 드러나는 장면입니다."];
  return `
    <section class="premium-core-experience-board domain-${escapeHtml(domain)}" aria-label="${escapeHtml(title)}">
      <header>
        <span>${escapeHtml(title)}</span>
        <strong>${escapeHtml(caption)}</strong>
      </header>
      <div>
        ${selected.map(renderPremiumCoreExperienceCard).join("")}
      </div>
    </section>
  `;
}

function premiumCoreExperienceItems(domain, storyItems, detailScenes) {
  const pool = [...storyItems, ...detailScenes];
  if (!pool.length) {
    return [];
  }
  const roleOrder = domain === "personality"
    ? ["strong", "scene", "watch"]
    : ["strong", "scene", "watch"];
  const selected = [];
  const used = new Set();
  roleOrder.forEach((role) => {
    const index = pool.findIndex((item, itemIndex) => !used.has(itemIndex) && item.role === role);
    if (index >= 0) {
      selected.push(pool[index]);
      used.add(index);
    }
  });
  pool.forEach((item, index) => {
    if (selected.length >= 4 || used.has(index)) {
      return;
    }
    selected.push(item);
    used.add(index);
  });
  const seen = new Set();
  return selected
    .filter((item) => {
      const key = premiumTopicMatchKey(`${item.title || ""}:${item.body || ""}`);
      if (!key || seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    })
    .slice(0, 4);
}

function renderPremiumCoreExperienceCard(item) {
  const tone = item.role === "watch" ? "watch" : item.role === "strong" ? "strong" : "scene";
  const scenes = Array.isArray(item.scenes)
    ? item.scenes.map((scene) => cleanPremiumDisplayText(scene || "")).filter(Boolean).slice(0, 2)
    : [];
  return `
    <article class="is-${escapeHtml(tone)}">
      ${item.label ? `<span>${escapeHtml(item.label)}</span>` : ""}
      ${item.title ? `<strong>${escapeHtml(item.title)}</strong>` : ""}
      ${item.body ? `<p>${escapeHtml(firstSentences(item.body, 2))}</p>` : ""}
      ${
        scenes.length
          ? `<ul>${scenes.map((scene) => `<li>${escapeHtml(scene)}</li>`).join("")}</ul>`
          : ""
      }
    </article>
  `;
}

function renderPremiumCoreBasisChips(section) {
  const cards = Array.isArray(section?.premium_basis_cards) ? section.premium_basis_cards : [];
  const normalized = cards
    .map((card) => ({
      label: cleanCustomerLabel(card?.label || ""),
      title: cleanCustomerLabel(card?.title || ""),
      body: cleanPremiumDisplayText(card?.body || ""),
    }))
    .filter((card) => card.label || card.title || card.body);
  const chips = selectPremiumBasisCards(normalized, 2);
  if (!chips.length) {
    return "";
  }
  return `
    <section class="premium-core-basis-chips" aria-label="주요 근거 항목">
      <header>
        <span>근거 항목</span>
        <strong>명식에서 직접 확인한 기준</strong>
      </header>
      ${chips
        .map(
          (chip) => `
            <article>
              <span>${escapeHtml(chip.label || "근거")}</span>
              ${chip.title ? `<strong>${escapeHtml(chip.title)}</strong>` : ""}
              ${chip.body ? `<p>${escapeHtml(firstSentences(chip.body, 1))}</p>` : ""}
            </article>
          `,
        )
        .join("")}
    </section>
  `;
}

function selectPremiumBasisCards(cards, limit = 3) {
  const usable = Array.isArray(cards) ? cards.filter((card) => card && (card.title || card.body)) : [];
  const priority = ["월령 기준", "생극·십신", "지지·지장간", "월령 심화", "상생상극", "오행 배합", "일간 반응"];
  const selected = [];
  const used = new Set();
  priority.forEach((label) => {
    if (selected.length >= limit) {
      return;
    }
    const index = usable.findIndex((card, itemIndex) => !used.has(itemIndex) && card.label === label);
    if (index >= 0) {
      selected.push(usable[index]);
      used.add(index);
    }
  });
  usable.forEach((card, index) => {
    if (selected.length >= limit || used.has(index)) {
      return;
    }
    selected.push(card);
    used.add(index);
  });
  return selected.slice(0, limit);
}

function premiumCoreDossierLabels(domain) {
  const labels = {
    money: {
      strong: "강한 재물 결과",
      scene: "수익화 지점",
      watch: "손실 기준",
    },
    career: {
      strong: "강한 직업 결과",
      scene: "평가 지점",
      watch: "주의 기준",
    },
    love: {
      strong: "강한 애정 결과",
      scene: "진전 지점",
      watch: "주의 기준",
    },
    marriage: {
      strong: "강한 결혼 결과",
      scene: "안정 지점",
      watch: "주의 기준",
    },
  };
  return labels[domain] || {
    strong: "강한 결과",
    scene: "현실 적용",
    watch: "주의 기준",
  };
}

function renderPremiumCoreDossierJudgment(dossier, providedHeadline = "") {
  const headline = providedHeadline || premiumCoreDossierJudgmentHeadline(dossier);
  const chips = [
    { label: "강점", value: premiumCorePointName(dossier?.strong) },
    { label: "주의", value: premiumCorePointName(dossier?.watch), tone: "watch" },
  ].filter((item) => item.value);
  if (!headline && !chips.length) {
    return "";
  }
  return `
    <section class="premium-core-judgment-strip" aria-label="핵심 결과">
      ${headline ? `<span class="premium-core-judgment-label">핵심 결론</span>` : ""}
      ${headline ? `<strong>${escapeHtml(headline)}</strong>` : ""}
      ${
        chips.length
          ? `<div>${chips
              .map(
                (item) => `
                  <span class="${item.tone === "watch" ? "is-watch" : ""}">
                    <b>${escapeHtml(item.label)}</b>
                    <em>${escapeHtml(item.value)}</em>
                  </span>
                `,
              )
              .join("")}</div>`
          : ""
      }
    </section>
  `;
}

function premiumCorePointName(point) {
  return cleanCustomerLabel(point?.label || point?.value || "");
}

function premiumCoreDossierJudgmentHeadline(dossier) {
  const domain = dossier?.domain || "default";
  const strong = premiumCorePointName(dossier?.strong);
  const watch = premiumCorePointName(dossier?.watch);
  if (domain === "money") {
    if (strong.includes("수익") && watch.includes("공동")) {
      return "수입은 강하게 열리지만, 가까운 사람과 섞인 돈에서 손실이 커집니다.";
    }
    if (strong.includes("축적") || strong.includes("축재")) {
      return "수입을 자기 명의의 자산으로 굳히는 과정이 재물운의 핵심입니다.";
    }
    return "돈은 들어오는 사주입니다. 다만 권리와 명의가 분명해야 재산으로 남습니다.";
  }
  if (domain === "career") {
    if (strong.includes("권한") || watch.includes("권한")) {
      return "책임과 결정권이 함께 주어질 때 직업운이 가장 강합니다.";
    }
    if (strong.includes("전문")) {
      return "전문 영역이 분명해질수록 경력과 평가가 강해집니다.";
    }
    return "성과가 직함과 이력으로 남는 자리에서 직업운이 강합니다.";
  }
  if (domain === "love") {
    if (strong.includes("표현")) {
      return "마음을 분명히 드러낼수록 인연의 진전이 빨라집니다.";
    }
    if (strong.includes("선택") || strong.includes("신뢰")) {
      return "상대를 가려내는 기준이 분명해질수록 연애운이 안정됩니다.";
    }
    return "연애운은 오래 이어질 관계를 고르는 힘에서 결론이 납니다.";
  }
  if (domain === "marriage") {
    if (strong.includes("생활") || strong.includes("가정")) {
      return "결혼운은 생활 기준과 가정 운영력이 분명하게 살아납니다.";
    }
    if (strong.includes("배우자")) {
      return "배우자 선택이 결혼 생활의 안정성을 크게 끌어올립니다.";
    }
    return "결혼운은 감정보다 생활의 지속성과 책임감에서 결론이 납니다.";
  }
  if (domain === "personality") {
    if (strong.includes("판단")) {
      return "판단 기준이 분명하고, 중요한 선택을 쉽게 남에게 넘기지 않습니다.";
    }
    if (strong.includes("감정")) {
      return "상대의 반응을 빠르게 읽고 관계의 거리를 조절합니다.";
    }
    return "성격의 중심 기준이 분명해 선택과 태도가 쉽게 흐려지지 않습니다.";
  }
  return strong ? `${strong}이 결과의 중심입니다.` : "";
}

function premiumCoreDossier(section) {
  if (!section) {
    return null;
  }
  const domain = premiumSectionDomain(section);
  const profile = section?.section_profile || {};
  const storyCards = Array.isArray(section?.section_story_cards) ? section.section_story_cards : [];
  const profileItems = Array.isArray(profile.items) ? profile.items : [];
  const visualItems = Array.isArray(section?.visual_profile?.items) ? section.visual_profile.items : [];
  const strong = premiumCoreStrongPoint(profileItems, visualItems, storyCards);
  const scene = premiumCoreScenePoint(section, storyCards);
  const watch = premiumCoreWatchPoint(section, storyCards, profileItems, visualItems);
  const metrics = premiumCoreMetricItems(visualItems, profileItems);
  const type = cleanCustomerLabel(profile.type || premiumSectionFocus(section) || premiumNavTitle(section));
  const verdict = cleanPremiumDisplayText(profile.summary || premiumSectionHeadline(section));
  if (!type && !verdict && !strong && !scene && !watch && !metrics.length) {
    return null;
  }
  return {
    domain,
    label: premiumSectionIndexTitle(section),
    type: type || "핵심 진단",
    verdict,
    grade: premiumDomainBadge(section),
    strong,
    scene,
    watch,
    metrics,
  };
}

function premiumCoreStrongPoint(profileItems, visualItems, storyCards) {
  const storyStrong = (storyCards || []).find((card) => card?.tone === "strong" || String(card?.label || "").includes("강하게"));
  const profileStrong = (profileItems || []).find((item) => String(item?.label || "").includes("대표"));
  const visualStrong = [...(visualItems || [])].sort((a, b) => Number(b?.score || 0) - Number(a?.score || 0))[0];
  return premiumCorePointFromSource(profileStrong || storyStrong || visualStrong);
}

function premiumCoreScenePoint(section, storyCards) {
  const storyScene = (storyCards || []).find((card) => String(card?.label || "").includes("생활"));
  if (storyScene) {
    return premiumCorePointFromSource(storyScene);
  }
  const details = Array.isArray(section?.detail_blocks) ? section.detail_blocks : [];
  const strongDetail = details.find((detail) => detail?.tone === "strong") || details.find((detail) => detail?.body);
  return premiumCorePointFromSource(strongDetail);
}

function premiumCoreWatchPoint(section, storyCards, profileItems, visualItems) {
  const storyWatch = (storyCards || []).find(
    (card) =>
      card?.tone === "watch" ||
      card?.tone === "risk" ||
      String(card?.label || "").includes("주의") ||
      String(card?.title || "").includes("주의"),
  );
  if (storyWatch) {
    return premiumCorePointFromSource(storyWatch);
  }
  const profileWatch = (profileItems || []).find(
    (item) => item?.tone === "watch" || item?.tone === "risk" || String(item?.label || "").includes("주의"),
  );
  if (profileWatch) {
    return premiumCorePointFromSource(profileWatch);
  }
  const visualWatch = (visualItems || [])
    .filter((item) => Number.isFinite(Number(item?.score)))
    .sort((a, b) => Number(a.score) - Number(b.score))[0];
  return premiumCorePointFromSource(visualWatch);
}

function premiumCorePointFromSource(source) {
  if (!source) {
    return null;
  }
  const label = cleanCustomerLabel(
    source.title ||
      source.value ||
      source.display_label ||
      source.label ||
      source.source_title ||
      "",
  );
  const body = cleanPremiumDisplayText(source.body || source.text || source.caption || source.judgment || source.result || "");
  const value = cleanCustomerLabel(source.grade || source.value || "");
  if (!label && !body && !value) {
    return null;
  }
  return { label, body, value };
}

function renderPremiumCoreDossierPoint(label, point, tone, contextText = "") {
  if (!point) {
    return "";
  }
  const body = removeShownSentences(point.body || "", contextText, 2);
  return `
    <article class="is-${escapeHtml(tone)}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(point.label || point.value || "진단")}</strong>
      ${body ? `<p>${escapeHtml(body)}</p>` : ""}
    </article>
  `;
}

function premiumCoreMetricItems(visualItems, profileItems) {
  const pool = [...(visualItems || []), ...(profileItems || [])]
    .map((item) => ({
      label: cleanCustomerLabel(item?.label || item?.value || item?.source_title || ""),
      value: premiumCardMetricValue(item),
      score: Number(item?.score),
    }))
    .filter((item) => item.label && (item.value || Number.isFinite(item.score)));
  const seen = new Set();
  return pool
    .filter((item) => {
      const key = premiumTopicMatchKey(item.label);
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    })
    .slice(0, 3);
}

function renderPremiumCoreDossierMetrics(metrics) {
  if (!Array.isArray(metrics) || !metrics.length) {
    return "";
  }
  return `
    <div class="premium-core-dossier-metrics" aria-label="핵심 지표">
      ${metrics
        .map((item) => {
          const width = Number.isFinite(item.score) ? Math.max(8, Math.min(100, Math.round(item.score))) : null;
          return `
            <span>
              <b>${escapeHtml(item.label)}</b>
              <strong>${escapeHtml(item.value || (width ? `${width}점` : ""))}</strong>
              ${width ? `<i aria-hidden="true"><em style="width:${width}%"></em></i>` : ""}
            </span>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderPremiumCoreDetailCards(section) {
  const details = premiumCoreDetailCardItems(section).slice(0, 4);
  if (!details.length) {
    return "";
  }
  return `
    <section class="premium-core-detail-cards" aria-label="상세 내용">
      <header>
        <span>상세 내용</span>
        <strong>${escapeHtml(`${premiumNavTitle(section)}에서 실제로 드러나는 대목`)}</strong>
      </header>
      <div>
        ${details
          .map((detail) => {
            const scenes = Array.isArray(detail.scenes) ? detail.scenes.slice(0, 2) : [];
            const targets = Array.isArray(detail.cautionTargets) ? detail.cautionTargets.slice(0, 2) : [];
            const tone = detail.level === "watch" || detail.level === "risk" ? "is-watch" : detail.level === "strong" ? "is-strong" : "";
            return `
              <article class="${tone}">
                <b>${escapeHtml(detail.title)}</b>
                <strong>${escapeHtml(detail.judgment)}</strong>
                ${
                  scenes.length
                    ? `<ul>${scenes.map((scene) => `<li>${escapeHtml(scene)}</li>`).join("")}</ul>`
                    : ""
                }
                ${
                  targets.length
                    ? `<p class="premium-core-detail-targets">${targets.map((target) => escapeHtml(target)).join(" · ")}</p>`
                    : ""
                }
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function premiumCoreDetailCardItems(section) {
  const dictionary = premiumDictionaryItems(section);
  const seen = new Set(dictionary.map((item) => premiumTopicMatchKey(item.title)));
  const fallback = Array.isArray(section?.detail_blocks)
    ? section.detail_blocks
        .map((detail) => {
          const title = cleanCustomerLabel(detail?.title || "");
          const key = premiumTopicMatchKey(title);
          if (!title || seen.has(key)) {
            return null;
          }
          seen.add(key);
          return {
            title,
            judgment: cleanPremiumDisplayText(detail?.body || ""),
            scenes: Array.isArray(detail?.bullets)
              ? detail.bullets.map((bullet) => cleanPremiumDisplayText(bullet || "")).filter(Boolean).slice(0, 2)
              : [],
            cautionTargets: [],
            level: detail?.tone === "risk" || detail?.tone === "watch" ? "watch" : detail?.tone === "strong" ? "strong" : "",
          };
        })
        .filter(Boolean)
    : [];
  const priority = (item) => {
    if (item.level === "strong") return 3;
    if (item.level === "watch" || item.level === "risk") return 2;
    return 1;
  };
  return [...dictionary, ...fallback]
    .filter((item) => item.title && item.judgment)
    .sort((a, b) => priority(b) - priority(a));
}

function renderPremiumRequiredJudgmentCards(section) {
  const cards = Array.isArray(section?.required_judgment_cards) ? section.required_judgment_cards : [];
  const domain = premiumSectionDomain(section);
  const isLoveMarriageCombined = domain === "love" && String(section?.heading || "").includes("결혼");
  const limit = domain === "money" ? 13 : domain === "career" ? 12 : isLoveMarriageCombined ? 23 : domain === "love" ? 11 : domain === "marriage" ? 12 : domain === "timing" ? 15 : 6;
  const usable = cards
    .map((card) => {
      const rawScore = card?.score;
      const parsedScore = rawScore === null || rawScore === undefined || rawScore === "" ? null : Number(rawScore);
      return {
        title: cleanCustomerLabel(card?.title || ""),
        grade: cleanCustomerLabel(card?.grade || ""),
        value: cleanCustomerLabel(card?.value || ""),
        score: Number.isFinite(parsedScore) ? parsedScore : null,
        tone: card?.tone || "",
        body: cleanPremiumDisplayText(card?.body || ""),
        meaning: cleanPremiumDisplayText(card?.meaning || ""),
        scene: cleanPremiumDisplayText(card?.scene || ""),
      };
    })
    .filter((card) => card.title && card.body)
    .slice(0, limit);
  if (!usable.length) {
    return "";
  }
  const preferredFeaturedTitles = {
    money: ["재물 형성력", "수입 창출력", "투자·거래 판단력"],
    career: ["직업 적성", "사회적 도약성", "책임·권한 균형"],
    love: ["끌림의 기준", "관계 진전력", "관계 지속력"],
    marriage: ["혼인 성향", "배우자상", "생활 안정"],
    timing: ["상승 연도", "재물 주의 연도", "인생 전환 연도"],
  };
  const featuredTarget = domain === "timing" ? 2 : 3;
  const selectedTitles = new Set();
  const featured = [];
  for (const title of preferredFeaturedTitles[domain] || []) {
    const match = usable.find((card) => card.title === title && !selectedTitles.has(card.title));
    if (match) {
      selectedTitles.add(match.title);
      featured.push(match);
    }
    if (featured.length >= featuredTarget) {
      break;
    }
  }
  for (const card of usable) {
    if (featured.length >= featuredTarget) {
      break;
    }
    if (!selectedTitles.has(card.title)) {
      selectedTitles.add(card.title);
      featured.push(card);
    }
  }
  const compact = usable.filter((card) => !selectedTitles.has(card.title));
  const intro = premiumRequiredJudgmentIntro(domain);
  const outcomeStrip = renderPremiumRequiredOutcomeStrip(domain, usable);
  const displayValue = (card) => {
    const value = cleanCustomerLabel(card.value || "");
    if (!value || value === card.title) {
      return "";
    }
    if (domain !== "timing" && value.replace(/\s+/g, "") === card.title.replace(/\s+/g, "")) {
      return "";
    }
    return value;
  };
  const cardParts = (card, variant) => {
    const result = premiumRequiredJudgmentResultLine(domain, card);
    const remainder = removeShownSentences(card.body || "", result, 1);
    const meaning = firstSentences(
      card.meaning || premiumRequiredJudgmentMeaningLine(domain, card),
      variant === "compact" ? 1 : 2
    );
    const scene = firstSentences(
      removeShownSentences(card.scene || premiumRequiredJudgmentSceneLine(domain, card), [result, meaning].join(" "), 1),
      1
    );
    const detail = firstSentences(
      removeShownSentences(remainder || premiumRequiredJudgmentDetailLine(domain, card), [meaning, scene].join(" "), 1),
      variant === "compact" ? 1 : 2
    );
    return { result, meaning, scene, detail };
  };
  const renderCard = (card, variant = "featured") => {
    const width = Number.isFinite(card.score) ? Math.max(8, Math.min(100, Math.round(card.score))) : null;
    const tone = card.tone === "watch" || card.grade === "주의" ? "watch" : card.tone === "strong" ? "strong" : "neutral";
    const isCompact = variant === "compact";
    const value = displayValue(card);
    const parts = cardParts(card, variant);
    const copyLabels = premiumRequiredCopyLabels(domain, card);
    return `
      <article class="is-${escapeHtml(tone)} ${isCompact ? "is-compact-card" : "is-featured-card"}">
        <div>
          <b>${escapeHtml(card.title)}</b>
          ${card.grade ? `<strong>${escapeHtml(card.grade)}</strong>` : ""}
        </div>
        ${value ? `<em>${escapeHtml(value)}</em>` : ""}
        ${width && !isCompact ? `<i aria-label="지표 강약"><span style="width:${width}%"></span></i>` : ""}
        <section class="premium-required-card-copy">
          <span>${escapeHtml(isCompact ? copyLabels.compact : copyLabels.result)}</span>
          <p>${escapeHtml(parts.result)}</p>
        </section>
        ${parts.meaning ? `
          <section class="premium-required-card-copy is-meaning">
            <span>${escapeHtml(copyLabels.meaning)}</span>
            <p>${escapeHtml(parts.meaning)}</p>
          </section>
        ` : ""}
        ${!isCompact && parts.scene ? `
          <section class="premium-required-card-copy is-scene">
            <span>${escapeHtml(copyLabels.scene)}</span>
            <p>${escapeHtml(parts.scene)}</p>
          </section>
        ` : ""}
        ${parts.detail ? `
          <section class="premium-required-card-copy is-detail">
            <span>${escapeHtml(isCompact ? copyLabels.compactDetail || copyLabels.detail : copyLabels.detail)}</span>
            <p>${escapeHtml(parts.detail)}</p>
          </section>
        ` : ""}
      </article>
    `;
  };
  return `
    <section class="premium-required-judgments" aria-label="분야별 결과">
      <header>
        <span>분야별 결과</span>
        <strong>${escapeHtml(premiumNavTitle(section))}</strong>
      </header>
      ${intro ? `<p class="premium-required-intro">${escapeHtml(intro)}</p>` : ""}
      ${outcomeStrip}
      <div class="premium-required-judgment-board">
        <div class="premium-required-featured">
          ${featured.map((card) => renderCard(card, "featured")).join("")}
        </div>
        ${
          compact.length
            ? `<div class="premium-required-compact">
                ${compact.map((card) => renderCard(card, "compact")).join("")}
              </div>`
            : ""
        }
      </div>
    </section>
  `;
}

function premiumRequiredCopyLabels(domain, card) {
  const isWatch = card?.tone === "watch" || card?.grade === "주의";
  const map = {
    money: {
      compact: "재물 요지",
      compactDetail: "실제 대목",
      result: "재물 결론",
      meaning: "손익 기준",
      scene: "현실 장면",
      detail: isWatch ? "주의 대목" : "적용 지점",
    },
    career: {
      compact: "직업 요지",
      compactDetail: "경력 대목",
      result: "직업 결론",
      meaning: "평가 기준",
      scene: "현실 장면",
      detail: isWatch ? "손상 지점" : "성취 지점",
    },
    love: {
      compact: "연애 요지",
      compactDetail: "관계 대목",
      result: "애정 결론",
      meaning: "관계 기준",
      scene: "실제 모습",
      detail: isWatch ? "상처 지점" : "진전 지점",
    },
    marriage: {
      compact: "결혼 요지",
      compactDetail: "생활 대목",
      result: "결혼 결론",
      meaning: "생활 기준",
      scene: "실제 모습",
      detail: isWatch ? "부담 지점" : "안정 지점",
    },
    timing: {
      compact: "연도 요지",
      compactDetail: "발현 근거",
      result: "연도 결과",
      meaning: "사건 성격",
      scene: "발현 장면",
      detail: isWatch ? "주의 대목" : "활용 지점",
    },
  };
  return map[domain] || {
    compact: "요지",
    compactDetail: "적용 대목",
    result: "핵심 결과",
    meaning: "근거 항목",
    scene: "현실 장면",
    detail: isWatch ? "주의 대목" : "세부 해석",
  };
}

function premiumRequiredJudgmentIntro(domain) {
  if (domain === "money") {
    return "재물운은 돈이 들어오는 자리, 자기 몫으로 굳어지는 자리, 손실이 생기는 자리가 분명하게 갈립니다.";
  }
  if (domain === "career") {
    return "직업운은 이름값보다 실제 권한과 평가가 남는 자리에서 강하게 드러납니다.";
  }
  if (domain === "love") {
    return "연애운은 첫 호감보다 누구에게 마음을 오래 주고, 어디서 관계가 흔들리는지가 더 중요하게 드러납니다.";
  }
  if (domain === "marriage") {
    return "결혼운은 사랑의 깊이보다 배우자상, 생활 기준, 가족 책임에서 실제 결론이 납니다.";
  }
  if (domain === "timing") {
    return "20세부터 79세까지 좋은 해와 주의할 해를 사건별로 압축했습니다.";
  }
  return "";
}

function renderPremiumRequiredOutcomeStrip(domain, cards) {
  const usable = Array.isArray(cards)
    ? cards.filter((card) => card?.title && card?.body)
    : [];
  if (!usable.length) {
    return "";
  }
  const isWatch = (card) => card?.tone === "watch" || card?.grade === "주의";
  const scoreOf = (card) => Number.isFinite(Number(card?.score)) ? Number(card.score) : 0;
  const strongCard =
    usable.find((card) => card?.tone === "strong") ||
    [...usable].filter((card) => !isWatch(card)).sort((a, b) => scoreOf(b) - scoreOf(a))[0];
  const watchCard =
    usable.find((card) => isWatch(card)) ||
    [...usable].sort((a, b) => scoreOf(a) - scoreOf(b))[0];
  const sceneCard = usable.find((card) => card !== strongCard && card !== watchCard) || strongCard || watchCard;
  const rows = [
    premiumRequiredOutcomeRow(domain, strongCard, "결론", "strong"),
    premiumRequiredOutcomeRow(domain, sceneCard, "현실 양상", "scene"),
    premiumRequiredOutcomeRow(domain, watchCard, "주의 지점", "watch"),
  ].filter(Boolean);
  if (!rows.length) {
    return "";
  }
  return `
    <div class="premium-required-outcome-strip">
      ${rows.join("")}
    </div>
  `;
}

function premiumRequiredOutcomeRow(domain, card, label, tone) {
  if (!card) {
    return "";
  }
  const title = cleanCustomerLabel(card.title || "");
  const result = cleanPremiumDisplayText(premiumRequiredJudgmentResultLine(domain, card));
  const scene = cleanPremiumDisplayText(premiumRequiredJudgmentSceneLine(domain, card));
  const meaning = cleanPremiumDisplayText(premiumRequiredJudgmentMeaningLine(domain, card));
  const second = removeShownSentences(scene || meaning, result, 1);
  const body = firstSentences([result, second].filter(Boolean).join(" "), 2);
  if (!title && !body) {
    return "";
  }
  return `
    <article class="is-${escapeHtml(tone)}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(title)}</strong>
      ${body ? `<p>${escapeHtml(body)}</p>` : ""}
    </article>
  `;
}

function premiumRequiredJudgmentResultLine(domain, card) {
  const title = card.title || "";
  const tone = card.tone === "watch" || card.grade === "주의" ? "watch" : card.tone === "strong" ? "strong" : "neutral";
  const grade = card.grade || "";
  const strong = grade === "매우 강함" || grade === "강함" || tone === "strong";
  const watch = tone === "watch";
  const map = {
    money: {
      "재물 형성력": strong ? "수입이 재산의 기초로 굳어지는 명식입니다." : watch ? "수입이 생겨도 명의와 소유권으로 고정되는 속도가 늦습니다." : "재물은 반복 수입과 장기 거래에서 축적됩니다.",
      "재물 규모 확장력": strong ? "큰 금액을 다룰 운이 열려 있습니다." : watch ? "금액을 키울수록 회수 조건과 손실 범위를 냉정하게 따져야 합니다." : "재물 규모는 안정된 수입 이후에 단계적으로 넓어집니다.",
      "수입 창출력": strong ? "일의 결과가 곧장 보수로 돌아옵니다." : watch ? "일은 많아도 보수 기준이 늦으면 실질 몫이 줄어듭니다." : "수입은 대가가 분명한 일에서 안정됩니다.",
      "재주 수익화": strong ? "기술과 결과물이 가격을 갖는 사주입니다." : watch ? "재능은 있어도 상품명과 단가가 늦게 붙습니다." : "재주는 상품의 형태가 잡힐 때 수입으로 전환됩니다.",
      "성과 보상력": strong ? "성과에 대한 몫을 요구할 명분이 분명합니다." : watch ? "성과가 있어도 몫을 확정하지 않으면 보상이 작아집니다." : "성과 보상은 기준이 분명할 때 확보됩니다.",
      "자산화 능력": strong ? "수입이 자기 명의의 자산으로 굳어집니다." : watch ? "수입이 생겨도 자산으로 굳기 전에 흩어지기 쉽습니다." : "재산은 소유권이 남는 방식에서 만들어집니다.",
      "공동자금 운영력": watch ? "가까운 금전관계에서 손실을 떠안을 가능성이 큽니다." : strong ? "공동자금에서도 자기 몫을 지키는 계산이 됩니다." : "공동자금은 명의와 지분을 분리할 때 안정됩니다.",
      "계약·명의 안정성": watch ? "명의와 계약이 흐리면 받을 돈이 줄어듭니다." : strong ? "계약과 명의가 금전 권리를 지켜줍니다." : "계약과 명의가 재물의 안정성을 결정합니다.",
      "투자·거래 판단력": watch ? "투자와 거래는 회수 조건이 흔들릴 때 손실로 굳어집니다." : strong ? "거래의 손익 구조를 읽는 감각이 있습니다." : "투자와 거래는 권리 구조가 분명할 때 맞습니다.",
    },
    career: {
      "직업 적성": strong ? "결과와 책임이 남는 운영형 업무에서 강합니다." : watch ? "맞지 않는 자리는 실력보다 피로와 손실을 먼저 남깁니다." : "역할이 분명한 자리에서 직업 적성이 드러납니다.",
      "직업 분야": strong ? "직업명보다 맡는 역할에서 강점이 분명합니다." : watch ? "겉으로 좋아 보이는 직업도 실제 역할이 맞지 않으면 오래 버티기 어렵습니다." : "직업 분야는 책임과 결과물이 남는 쪽이 맞습니다.",
      "성취 축적력": strong ? "성과가 경력 자산으로 축적됩니다." : watch ? "성과가 자기 이름으로 남지 않으면 경력의 값이 늦게 오릅니다." : "성과는 기록과 실적으로 남을 때 강해집니다.",
      "평가·명예 전환력": strong ? "성과가 평판, 추천, 직책으로 이어집니다." : watch ? "평가 기준이 흐리면 공로가 다른 사람에게 넘어갑니다." : "평가는 공식 기록에서 올라갑니다.",
      "책임·권한 균형": watch ? "결정권 없는 책임은 경력 손상으로 남습니다." : strong ? "책임과 권한이 함께 붙을 때 경력이 강해집니다." : "책임의 범위와 결정권이 함께 맞아야 합니다.",
      "권한 확보력": strong ? "권한이 붙을수록 직업적 위상이 올라갑니다." : watch ? "권한 없이 책임만 커지는 자리는 피해야 합니다." : "권한이 붙을 때 경력이 안정됩니다.",
    },
    love: {
      "끌림의 기준": strong ? "상대의 태도와 책임감에서 마음이 움직입니다." : watch ? "첫 호감만으로 시작한 관계는 오래 버티기 어렵습니다." : "호감은 생활 태도와 책임감에서 깊어집니다.",
      "상대 선택력": strong ? "오래 갈 사람과 피해야 할 사람을 비교적 잘 가립니다." : watch ? "순간적인 끌림에 밀리면 맞지 않는 사람을 오래 붙잡을 수 있습니다." : "상대 선택은 태도와 생활 기준에서 갈립니다.",
      "상대 신뢰 감별력": strong ? "말보다 반복된 행동을 보고 마음을 줍니다." : watch ? "말을 믿고 빨리 가까워지면 뒤늦게 실망이 큽니다." : "신뢰는 반복된 행동으로 확인됩니다.",
      "인연 형성력": strong ? "생활권과 반복 접점에서 인연이 들어옵니다." : watch ? "새 인연이 적게 열리면 관계 시작이 늦습니다." : "인연은 반복해서 마주치는 자리에서 깊어집니다.",
      "관계 진전력": strong ? "호감이 실제 만남과 약속으로 넘어갑니다." : watch ? "마음이 있어도 관계 확정이 늦어질 수 있습니다." : "관계 진전은 확인을 거쳐 움직입니다.",
      "애정 표현성": strong ? "좋아하는 마음이 상대에게 분명히 전달됩니다." : watch ? "마음보다 표현이 늦어 상대가 확신을 받지 못합니다." : "표현의 선명도가 관계의 안정감을 가릅니다.",
      "관계 지속력": strong ? "깊어진 관계를 오래 붙잡는 편입니다." : watch ? "서운함이 쌓이면 관계가 한 번에 식을 수 있습니다." : "관계는 오래 보지만 기준이 맞아야 합니다.",
    },
    marriage: {
      "혼인 성향": strong ? "결혼을 안정과 책임의 약속으로 받아들입니다." : watch ? "감정만으로 결혼을 밀어붙이면 뒤늦은 부담이 큽니다." : "결혼은 현실 조건이 맞을 때 안정됩니다.",
      "배우자상": strong ? "성실하고 생활 기준이 분명한 배우자와 오래 갑니다." : watch ? "감정 기복이 큰 상대와는 생활 손상이 먼저 옵니다." : "생활 기준이 맞는 배우자와 오래 갑니다.",
      "결혼 적기": strong ? "결혼 논의가 현실 절차로 넘어가는 해가 뚜렷합니다." : watch ? "현실 준비가 늦으면 결혼 결정도 함께 늦어집니다." : "결혼 시기는 주거와 가족 협의가 잡힐 때 선명해집니다.",
      "결혼 현실화력": strong ? "마음이 집, 일정, 가족 협의로 옮겨갈 때 결혼이 성사됩니다." : watch ? "현실 준비가 늦으면 결혼 의사도 함께 약해집니다." : "결혼 의사는 생활 준비와 함께 굳어집니다.",
      "생활 안정": strong ? "주거와 생활비 기준이 잡히면 결혼 생활이 오래 갑니다." : watch ? "생활 기준이 어긋나면 애정이 있어도 피로가 커집니다." : "주거와 생활비 기준이 결혼 안정의 핵심입니다.",
      "부부 재정": watch ? "부부 재정의 선이 흐리면 결혼 뒤 돈 문제가 반복됩니다." : strong ? "부부 재정은 기준이 맞을수록 안정됩니다." : "공동 생활비와 개인 자산을 분리해야 합니다.",
    },
  };
  const domainMap = map[domain] || {};
  return domainMap[title] || firstSentences(card.body || `${title}은 세부 확인이 필요한 기준입니다.`, 1);
}

function premiumRequiredJudgmentDetailLine(domain, card) {
  const title = card.title || "";
  const tone = card.tone === "watch" || card.grade === "주의" ? "watch" : card.tone === "strong" ? "strong" : "neutral";
  const map = {
    money: {
      "재물 형성력": "수입의 출처와 권리 형태가 분명할 때 재물 규모가 커집니다.",
      "수입 창출력": "월급, 성과급, 매출, 계약금처럼 계산 가능한 대가에서 수입이 살아납니다.",
      "자산화 능력": "현금으로 들고 있기보다 소유권, 지분, 장기 보유 자산으로 바꿀 때 재산이 남습니다.",
      "공동자금 운영력": tone === "watch" ? "가족, 지인, 동업자와 돈을 묶으면 명의와 몫이 불리하게 기울 수 있습니다." : "가까운 사람과 돈을 다룰 때도 명의와 몫을 먼저 정하면 손실을 줄입니다.",
      "계약·명의 안정성": tone === "watch" ? "구두 약속, 늦은 지급일, 흐린 명의는 금전 손실로 이어집니다." : "계약서와 명의가 분명할수록 받을 돈과 지분이 안정됩니다.",
    },
    career: {
      "직업 적성": "직무 이름보다 맡는 역할이 중요합니다. 업무의 기준과 결과물을 함께 맡는 일이 맞습니다.",
      "책임·권한 균형": "책임만 커지고 결정권이 없으면 성취가 경력으로 남지 않습니다.",
      "평가·명예 전환력": "성과가 문서, 직함, 추천, 공식 평가로 남을 때 직업적 값이 올라갑니다.",
    },
    love: {
      "애정 표현성": "상대가 기다리는 시간이 길어지면 마음이 있어도 거리감이 먼저 생깁니다.",
      "관계 지속력": "한 번 깊어진 관계는 오래 보지만 서운함을 넘기는 방식에는 주의가 필요합니다.",
    },
    marriage: {
      "생활 안정": "집, 생활비, 역할 기준이 맞아야 애정이 생활 속에서 오래 갑니다.",
      "부부 재정": "공동 생활비와 개인 자산의 선이 불분명하면 결혼 뒤 돈 문제가 반복됩니다.",
    },
  };
  return map[domain]?.[title] || "";
}

function premiumRequiredJudgmentMeaningLine(domain, card) {
  const title = card.title || "";
  const common = {
    money: "들어온 돈이 소비로 끝나는지, 권리와 자산으로 남는지에서 차이가 납니다.",
    career: "해낸 일이 지나가는 업무로 끝나는지, 경력과 평가로 남는지에서 차이가 납니다.",
    love: "첫 호감이 스쳐 지나가는지, 실제 만남과 오래 갈 관계로 이어지는지에서 차이가 납니다.",
    marriage: "감정이 생활 책임과 가족 문제까지 감당할 수 있는지가 드러납니다.",
    timing: "특정 연도에 가장 강하게 올라오는 사건 성격을 압축했습니다.",
  };
  const titleMap = {
    money: {
      "재물 형성력": "수입이 현금으로 지나가지 않고 명의, 지분, 장기 보유 자산으로 남는 힘입니다.",
      "재물 규모 확장력": "돈의 단위가 커질 때 감당 가능한 거래 규모와 손실 한도가 함께 드러납니다.",
      "수입 창출력": "노동, 거래, 성과가 실제 입금으로 확인되는 수입 경로입니다.",
      "재주 수익화": "기술, 말, 콘텐츠, 서비스가 단순 재능에 머물지 않고 가격을 갖는 지점입니다.",
      "성과 보상력": "해낸 일이 타인의 이름으로 흩어지지 않고 자기 몫의 보수로 회수되는 힘입니다.",
      "자산화 능력": "벌어들인 돈을 소비가 아니라 소유권과 보유 자산으로 바꾸는 능력입니다.",
      "공동자금 운영력": "가까운 사람과 돈이 얽힐 때 자기 몫, 명의, 책임 범위를 지키는 힘입니다.",
      "계약·명의 안정성": "받을 돈과 권리를 계약서, 명의, 지분으로 고정시키는 능력입니다.",
      "투자·거래 판단력": "겉수익보다 회수 가능성, 상대의 책임, 권리 구조를 먼저 읽는 감각입니다.",
    },
    career: {
      "직업 적성": "실력이 가장 빨리 인정받고 경력의 값이 올라가는 업무 성격입니다.",
      "직업 분야": "직업명보다 실제 업무 방식, 책임 구조, 결과물의 성격을 가르는 기준입니다.",
      "성취 축적력": "한 번의 성과가 칭찬으로 끝나지 않고 이력, 실적, 다음 자리의 근거로 남는 힘입니다.",
      "평가·명예 전환력": "실적이 평판, 추천, 직함, 공식 평가로 바뀌어 사회적 이름을 만드는 힘입니다.",
      "책임·권한 균형": "맡은 책임에 걸맞은 결정권이 붙을 때 경력 손상을 막고 성취를 남기는 기준입니다.",
      "권한 확보력": "일을 맡는 수준에 맞춰 결정권, 보고 체계, 보상 기준을 확보하는 힘입니다.",
    },
    love: {
      "끌림의 기준": "처음 마음이 움직이는 지점과 오래 끌리는 상대의 조건을 구분하는 기준입니다.",
      "상대 선택력": "오래 갈 사람과 손상될 관계를 초기에 가려내는 눈입니다.",
      "상대 신뢰 감별력": "상대의 말보다 반복된 태도, 약속, 책임감을 읽는 감각입니다.",
      "인연 형성력": "스쳐 가는 호감이 실제 만남과 관계로 이어지는 힘입니다.",
      "관계 진전력": "호감이 만남, 약속, 공개된 관계로 넘어가는 속도와 확정성입니다.",
      "애정 표현성": "마음이 상대에게 오해 없이 전달되는 정도입니다.",
      "관계 지속력": "깊어진 관계를 쉽게 끊지 않고 오래 유지하려는 힘입니다.",
    },
    marriage: {
      "혼인 성향": "결혼을 감정의 결론이 아니라 생활의 약속과 책임으로 받아들이는 방식입니다.",
      "배우자상": "오래 맞는 배우자의 성격, 생활 태도, 책임 감각을 보여주는 기준입니다.",
      "결혼 적기": "혼인 논의가 실제 절차로 굳어지기 쉬운 해입니다.",
      "결혼 현실화력": "결혼 의사가 집, 일정, 가족 협의, 공식 절차로 넘어가는 힘입니다.",
      "생활 안정": "주거, 생활비, 역할 기준이 결혼 생활을 오래 버티게 하는 기반입니다.",
      "부부 재정": "공동 생활비와 개인 자산의 선이 부부 사이의 안정에 미치는 힘입니다.",
      "가족 책임 경계력": "양가와 원가족 문제에서 부부의 책임선을 지켜내는 힘입니다.",
    },
  };
  return titleMap[domain]?.[title] || common[domain] || "";
}

function premiumRequiredJudgmentSceneLine(domain, card) {
  const title = card.title || "";
  const isWatch = card.tone === "watch" || card.grade === "주의";
  const sceneMap = {
    money: {
      "재물 형성력": ["고정 수입과 반복 거래가 쌓일수록 재산의 바닥이 단단해집니다.", "수입이 생겨도 권리와 명의가 남지 않으면 재산으로 굳지 않습니다."],
      "수입 창출력": ["성과가 보수로 환산되고 일의 대가가 비교적 분명하게 들어옵니다.", "일은 많아도 보상 기준이 흐리면 받을 몫이 줄어듭니다."],
      "자산화 능력": ["돈은 현금보다 소유권이 남는 형태에서 힘을 얻습니다.", "수입이 소비와 임시 비용으로 빠지면 자산의 흔적이 약해집니다."],
      "공동자금 운영력": ["지분과 명의를 나누면 관계와 돈을 함께 지킬 수 있습니다.", "호의로 시작한 돈이 나중에는 몫과 책임 문제로 바뀝니다."],
      "계약·명의 안정성": ["지급일, 지분, 수령액이 문서에 남을수록 금전 권리가 안정됩니다.", "구두 약속과 흐린 명의는 받을 몫을 줄입니다."],
    },
    career: {
      "직업 적성": ["업무의 기준과 결과물을 맡는 직무에서 강점이 분명합니다.", "단순 보조와 반복 처리만 많은 자리는 오래 맞지 않습니다."],
      "성취 축적력": ["기록과 실적이 쌓일수록 경력의 단가가 올라갑니다.", "성과가 자기 이름으로 남지 않으면 경력의 값이 늦게 오릅니다."],
      "평가·명예 전환력": ["공식 평가와 추천이 따라올 때 직업운이 강해집니다.", "평가 기준이 흐린 자리는 공로가 다른 사람에게 넘어갑니다."],
      "책임·권한 균형": ["책임과 권한이 함께 붙는 자리에서 오래 갑니다.", "문제가 생겼을 때 이름만 남는 자리는 피해야 합니다."],
    },
    love: {
      "끌림의 기준": ["말보다 생활 태도와 책임감에서 관계가 깊어집니다.", "첫 호감만으로는 오래 갈 관계가 되기 어렵습니다."],
      "관계 진전력": ["호감이 생기면 실제 만남과 약속으로 넘어갑니다.", "확정을 미루면 상대가 먼저 지칠 수 있습니다."],
      "애정 표현성": ["마음을 상대가 알아들을 수 있게 보여주는 일이 중요합니다.", "마음이 있어도 표현이 늦으면 상대는 확신을 받지 못합니다."],
      "관계 지속력": ["한 번 깊어진 관계는 쉽게 끊지 않습니다.", "서운함을 오래 넘기면 한 번에 거리가 생깁니다."],
    },
    marriage: {
      "혼인 성향": ["결혼을 안정과 책임의 약속으로 받아들이는 편입니다.", "감정만 앞세운 결혼은 뒤늦은 부담을 남깁니다."],
      "배우자상": ["성실하고 생활 기준이 분명한 상대와 오래 맞습니다.", "감정 기복이 큰 상대와는 결혼 뒤 생활 손상이 먼저 옵니다."],
      "생활 안정": ["주거와 생활비 기준이 잡히면 결혼 생활이 오래 갑니다.", "생활 기준이 어긋나면 애정이 있어도 피로가 커집니다."],
      "가족 책임 경계력": ["양가와 원가족 문제에서 부부의 기준을 먼저 세워야 합니다.", "가족 문제를 정으로 떠안으면 결혼 생활이 흔들립니다."],
    },
  };
  const pair = sceneMap[domain]?.[title];
  if (pair) {
    return pair[isWatch ? 1 : 0];
  }
  if (domain === "timing") {
    return isWatch
      ? "새 결정보다 기존 약속과 책임 범위를 먼저 정리해야 합니다."
      : "좋은 해라도 맡을 일과 남길 결과를 분명히 해야 합니다.";
  }
  return "";
}

function renderPremiumCoreDossierBasis(section) {
  const cards = Array.isArray(section?.premium_basis_cards) ? section.premium_basis_cards : [];
  const usable = cards
    .map((card) => ({
      label: cleanCustomerLabel(card?.label || ""),
      title: cleanCustomerLabel(card?.title || ""),
      body: cleanPremiumDisplayText(card?.body || ""),
    }))
    .filter((card) => card.title || card.body);
  const selected = selectPremiumBasisCards(usable, 3);
  if (!selected.length) {
    return "";
  }
  return `
    <section class="premium-core-basis" aria-label="분석 배경">
      <header>
        <span>분석 배경</span>
        <strong>실제 분석에 쓰인 기준</strong>
      </header>
      <div>
        ${selected.map(renderPremiumCoreBasisCard).join("")}
      </div>
    </section>
  `;
}

function renderPremiumCoreBasisDrawer(content) {
  const safeContent = String(content || "").trim();
  if (!safeContent) {
    return "";
  }
  return `
    <details class="premium-core-basis-drawer">
      <summary>
        <span>분석 배경</span>
        <em>적용 기준</em>
      </summary>
      <div class="premium-core-basis-drawer-body">
        ${safeContent}
      </div>
    </details>
  `;
}

function renderPremiumCoreBasisCard(card) {
  const body = firstSentences(card.body, 2);
  return `
    <article>
      ${card.label ? `<span>${escapeHtml(card.label)}</span>` : ""}
      ${card.title ? `<strong>${escapeHtml(card.title)}</strong>` : ""}
      ${body ? `<p>${escapeHtml(body)}</p>` : ""}
    </article>
  `;
}

function renderPremiumCoreDomainEvidence(section, details) {
  const limitedDetails = Array.isArray(details) ? details.slice(0, 3) : [];
  const domain = premiumSectionDomain(section);
  const profileBoard =
    domain === "personality"
      ? renderPremiumPersonalityCoreProfile(section)
      : renderPremiumDomainDossier(section) || renderPremiumDomainSignatureBoard(section);
  return `
    ${profileBoard}
    ${renderPremiumDomainDetails(limitedDetails)}
  `;
}

function renderPremiumPersonalityCoreProfile(section) {
  const profile = section?.personality_profile || {};
  const lead = cleanPremiumDisplayText(section?.lead || profile.summary || profile.subtitle || "");
  const leadSentences = sentenceList(lead);
  const headline = leadSentences[0] || cleanCustomerLabel(profile.title || "");
  const sublead =
    leadSentences.slice(1, 3).join(" ") ||
    firstSentences(cleanPremiumDisplayText(profile.subtitle || profile.summary || ""), 2);
  const coordinateAxes = Array.isArray(profile.coordinate_axes) ? profile.coordinate_axes.slice(0, 4) : [];
  const cards = Array.isArray(profile.cards) ? profile.cards.slice(0, 4) : [];
  const verdictItems = premiumPersonalityVerdictItems(profile, coordinateAxes, cards);
  if (!profile.title && !lead && !coordinateAxes.length && !cards.length) {
    return "";
  }
  return `
    <section class="premium-personality-dossier" aria-label="성격 종합 진단">
      <header class="premium-personality-hero">
        <span>성격 종합 진단</span>
        ${headline ? `<strong>${escapeHtml(headline)}</strong>` : ""}
        ${profile.title ? `<em>${escapeHtml(cleanCustomerLabel(profile.title))}</em>` : ""}
        ${sublead ? `<p>${escapeHtml(sublead)}</p>` : ""}
      </header>
      ${verdictItems.length ? renderPremiumPersonalityVerdictStrip(verdictItems) : ""}
      ${coordinateAxes.length ? renderPremiumPersonalityCoordinateMap(coordinateAxes) : ""}
      ${cards.length ? `<div class="premium-personality-trait-grid">${cards.map(renderPremiumPersonalityTraitCard).join("")}</div>` : ""}
      ${profile.contrast ? `<p class="premium-personality-dossier-note">${escapeHtml(cleanPremiumDisplayText(profile.contrast))}</p>` : ""}
    </section>
  `;
}

function premiumPersonalityVerdictItems(profile, coordinateAxes, cards) {
  const findByLabel = (items, label) =>
    (Array.isArray(items) ? items : []).find((item) => cleanCustomerLabel(item?.label || "") === label) || null;
  const relation = findByLabel(coordinateAxes, "관계의 거리");
  const pressure = findByLabel(coordinateAxes, "압박 반응");
  const focus = findByLabel(cards, "몰입 방향") || findByLabel(cards, "판단 방식");
  return [
    {
      label: "성격 결론",
      value: profile?.title || "",
      body: profile?.summary || profile?.subtitle || "",
    },
    {
      label: "관계 태도",
      value: relation?.value || "",
      body: relation?.body || "",
    },
    {
      label: "압박 반응",
      value: pressure?.value || "",
      body: pressure?.body || "",
    },
    {
      label: "관심 방향",
      value: focus?.value || "",
      body: focus?.body || "",
    },
  ].filter((item) => item.value || item.body);
}

function renderPremiumPersonalityVerdictStrip(items) {
  return `
    <div class="premium-personality-verdict-strip" aria-label="성격 핵심 결과">
      ${items.slice(0, 4).map(renderPremiumPersonalityVerdictCard).join("")}
    </div>
  `;
}

function renderPremiumPersonalityVerdictCard(item) {
  return `
    <article>
      <span>${escapeHtml(cleanCustomerLabel(item.label || ""))}</span>
      ${item.value ? `<strong>${escapeHtml(cleanCustomerLabel(item.value))}</strong>` : ""}
      ${item.body ? `<p>${escapeHtml(firstSentences(cleanPremiumDisplayText(item.body), 1))}</p>` : ""}
    </article>
  `;
}

function renderPremiumPersonalityCoordinateMap(items) {
  return `
    <div class="premium-personality-coordinate-map" aria-label="성격 지표">
      ${items.map(renderPremiumPersonalityCoordinateItem).join("")}
    </div>
  `;
}

function renderPremiumPersonalityCoordinateItem(item) {
  const score = Number(item?.score);
  const marker = Number.isFinite(score) ? Math.max(8, Math.min(92, Math.round(score))) : 50;
  return `
    <article>
      <header>
        <span>${escapeHtml(cleanCustomerLabel(item?.label || ""))}</span>
        ${item?.value ? `<strong>${escapeHtml(cleanCustomerLabel(item.value))}</strong>` : ""}
      </header>
      <div class="premium-personality-coordinate-track">
        <small>${escapeHtml(cleanCustomerLabel(item?.left || ""))}</small>
        <i aria-hidden="true"><em style="left:${marker}%"></em></i>
        <small>${escapeHtml(cleanCustomerLabel(item?.right || ""))}</small>
      </div>
      ${item?.body ? `<p>${escapeHtml(firstSentences(cleanPremiumDisplayText(item.body), 1))}</p>` : ""}
    </article>
  `;
}

function renderPremiumPersonalityOverviewItem(item) {
  return `
    <article>
      <span>${escapeHtml(cleanCustomerLabel(item?.label || ""))}</span>
      ${item?.value ? `<strong>${escapeHtml(cleanCustomerLabel(item.value))}</strong>` : ""}
      ${item?.body ? `<p>${escapeHtml(firstSentences(cleanPremiumDisplayText(item.body), 1))}</p>` : ""}
    </article>
  `;
}

function renderPremiumPersonalityAxisItem(item) {
  const score = Number(item?.score);
  const width = Number.isFinite(score) ? Math.max(8, Math.min(100, Math.round(score))) : null;
  return `
    <article>
      <div>
        <b>${escapeHtml(cleanCustomerLabel(item.label || ""))}</b>
        ${item.value ? `<strong>${escapeHtml(cleanCustomerLabel(item.value))}</strong>` : ""}
      </div>
      ${width ? `<i aria-label="성격 축 강도"><em style="width:${width}%"></em></i>` : ""}
      ${item.body ? `<p>${escapeHtml(firstSentences(cleanPremiumDisplayText(item.body), 1))}</p>` : ""}
    </article>
  `;
}

function renderPremiumPersonalityTraitCard(item) {
  const tone = item?.tone === "watch" || item?.tone === "risk" ? "watch" : item?.tone || "neutral";
  return `
    <article class="is-${escapeHtml(tone)}">
      <span>${escapeHtml(cleanCustomerLabel(item.label || ""))}</span>
      ${item.value ? `<strong>${escapeHtml(cleanCustomerLabel(item.value))}</strong>` : ""}
      ${item.body ? `<p>${escapeHtml(firstSentences(cleanPremiumDisplayText(item.body), 2))}</p>` : ""}
    </article>
  `;
}

function renderPremiumDomainDossier(section) {
  const profile = section?.section_profile || {};
  const domain = premiumSectionDomain(section);
  const config = premiumDomainDossierConfig(domain);
  const title = cleanCustomerLabel(profile.type || premiumSectionFocus(section) || premiumNavTitle(section));
  const summary = cleanPremiumDisplayText(profile.summary || premiumSectionHeadline(section));
  const insights = Array.isArray(profile.insights) ? profile.insights.slice(0, 4) : [];
  const units = premiumDomainResultUnits(section).slice(0, 5);
  const signatureItems = premiumDomainDossierSignatureItems(section, units);
  const seenContext = [
    summary,
    ...signatureItems.map((item) => item.body || ""),
  ].join(" ");
  if (!title && !summary && !insights.length && !units.length) {
    return "";
  }
  return `
    <section class="premium-domain-dossier domain-${escapeHtml(domain)}" aria-label="${escapeHtml(config.aria)}">
      <header>
        <div>
          <span>${escapeHtml(config.kicker)}</span>
          ${title ? `<strong>${escapeHtml(title)}</strong>` : ""}
        </div>
        <b>${escapeHtml(premiumDomainBadge(section))}</b>
      </header>
      ${summary ? `<p class="premium-domain-dossier-summary">${escapeHtml(firstSentences(summary, 2))}</p>` : ""}
      ${
        signatureItems.length
          ? `<div class="premium-domain-dossier-signature">
              ${signatureItems.map(renderPremiumDomainDossierSignatureItem).join("")}
            </div>`
          : ""
      }
      ${
        insights.length
          ? `<div class="premium-domain-dossier-insights">
              ${insights.map((item) => renderPremiumDomainDossierInsight(item, seenContext)).join("")}
            </div>`
          : ""
      }
      ${
        units.length
          ? `<div class="premium-domain-dossier-metrics">
              ${units.map(renderPremiumDomainDossierMetric).join("")}
            </div>`
          : ""
      }
    </section>
  `;
}

function premiumDomainDossierSignatureItems(section, units) {
  const usable = (Array.isArray(units) ? units : []).filter((unit) => unit?.label && (unit?.value || unit?.score !== null || unit?.body));
  if (!usable.length) {
    return [];
  }
  const roles = premiumDomainDossierSignatureRoles(premiumSectionDomain(section));
  const isWatch = (unit) => unit?.tone === "watch" || unit?.tone === "risk" || Number(unit?.score) < 56;
  const strong = usable.find((unit) => !isWatch(unit)) || usable[0];
  const watch = usable.find((unit) => isWatch(unit) && unit !== strong);
  const support = usable.find((unit) => unit !== strong && unit !== watch);
  const rows = [
    { role: roles.strong, source: strong, tone: "strong" },
    { role: roles.watch, source: watch, tone: "watch" },
    { role: roles.support, source: support, tone: "neutral" },
  ].filter((row) => row.source);
  return rows.map((row) => ({
    role: row.role,
    label: cleanCustomerLabel(row.source.label || ""),
    value: premiumSignatureDisplayValue(row.source, row.tone),
    body: cleanPremiumDisplayText(row.source.body || ""),
    score: Number(row.source.score),
    tone: row.tone,
  }));
}

function premiumDomainDossierSignatureRoles(domain) {
  const roles = {
    money: {
      strong: "재물 강점",
      watch: "주의 재물 기준",
      support: "추가 재물 내용",
    },
    career: {
      strong: "직업 강점",
      watch: "주의 직업 기준",
      support: "추가 직업 내용",
    },
    love: {
      strong: "관계 강점",
      watch: "주의 관계 기준",
      support: "추가 관계 내용",
    },
    marriage: {
      strong: "결혼 강점",
      watch: "주의 결혼 기준",
      support: "추가 결혼 내용",
    },
  };
  return roles[domain] || {
    strong: "강한 기준",
    watch: "주의 기준",
    support: "추가 내용",
  };
}

function renderPremiumDomainDossierSignatureItem(item) {
  const score = Number(item?.score);
  const width = Number.isFinite(score) ? Math.max(8, Math.min(100, Math.round(score))) : null;
  return `
    <section class="is-${escapeHtml(item?.tone || "neutral")}">
      <span>${escapeHtml(item?.role || "")}</span>
      <div>
        <b>${escapeHtml(item?.label || "")}</b>
        ${item?.value ? `<strong>${escapeHtml(item.value)}</strong>` : ""}
      </div>
      ${width ? `<i aria-label="지표 강도"><em style="width:${width}%"></em></i>` : ""}
    </section>
  `;
}

function premiumDomainDossierConfig(domain) {
  const configs = {
    money: {
      aria: "재물 종합 진단",
      kicker: "재물 종합",
    },
    career: {
      aria: "직업 종합 진단",
      kicker: "직업 종합",
    },
    love: {
      aria: "연애 종합 진단",
      kicker: "연애 종합",
    },
    marriage: {
      aria: "결혼 종합 진단",
      kicker: "결혼 종합",
    },
  };
  return configs[domain] || {
    aria: "영역별 종합 진단",
    kicker: "종합 진단",
  };
}

function renderPremiumDomainDossierInsight(item, summaryText = "") {
  const tone = item?.tone === "watch" || item?.tone === "risk" ? "watch" : item?.tone || "neutral";
  const body = removeShownSentences(cleanPremiumDisplayText(item?.body || ""), summaryText, 1);
  return `
    <article class="is-${escapeHtml(tone)}">
      <span>${escapeHtml(cleanCustomerLabel(item?.label || ""))}</span>
      ${item?.value ? `<strong>${escapeHtml(cleanCustomerLabel(item.value))}</strong>` : ""}
      ${body ? `<p>${escapeHtml(firstSentences(body, 1))}</p>` : ""}
    </article>
  `;
}

function renderPremiumDomainDossierMetric(unit) {
  const score = Number(unit?.score);
  const width = Number.isFinite(score) ? Math.max(8, Math.min(100, Math.round(score))) : null;
  const tone = unit?.tone === "watch" || unit?.tone === "risk" ? "watch" : unit?.tone || "neutral";
  const value = premiumSignatureDisplayValue(unit, tone === "watch" ? "watch" : "neutral");
  return `
    <article class="is-${escapeHtml(tone)}">
      <div>
        <b>${escapeHtml(cleanCustomerLabel(unit?.label || ""))}</b>
        ${value ? `<strong>${escapeHtml(value)}</strong>` : ""}
      </div>
      ${width ? `<i aria-label="항목 강도"><em style="width:${width}%"></em></i>` : ""}
    </article>
  `;
}

function renderPremiumDomainSignatureBoard(section) {
  const units = premiumDomainResultUnits(section);
  if (!units.length) {
    return renderPremiumCoreProfileBoard(section);
  }
  const domain = premiumSectionDomain(section);
  const config = premiumDomainSignatureConfig(domain);
  const strong = premiumSignatureStrongUnit(units);
  const watch = premiumSignatureWatchUnit(units, strong);
  const support = units
    .filter((unit) => unit !== strong && unit !== watch)
    .slice(0, 3);
  return `
    <section class="premium-domain-signature domain-${escapeHtml(domain)}" aria-label="${escapeHtml(config.aria)}">
      <header>
        <div>
          <span>${escapeHtml(config.kicker)}</span>
          <strong>${escapeHtml(cleanCustomerLabel(section?.section_profile?.type || premiumSectionFocus(section) || premiumNavTitle(section)))}</strong>
        </div>
        <b>${escapeHtml(premiumDomainBadge(section))}</b>
      </header>
      ${config.lead ? `<p class="premium-domain-signature-lead">${escapeHtml(config.lead)}</p>` : ""}
      <div class="premium-domain-signature-main">
        ${renderPremiumSignatureMajorCard(config.strongLabel, strong, "strong")}
        ${renderPremiumSignatureMajorCard(config.watchLabel, watch, "watch")}
      </div>
      ${
        support.length
          ? `<div class="premium-domain-signature-strip">
              ${support.map(renderPremiumSignatureAxis).join("")}
            </div>`
          : ""
      }
    </section>
  `;
}

function premiumDomainSignatureConfig(domain) {
  const configs = {
    money: {
      aria: "재물 핵심 결과",
      kicker: "재물 핵심",
      strongLabel: "가장 강한 재물 기준",
      watchLabel: "재물 관리 지점",
      lead: "수입, 자산화, 공동자금, 계약 안정성을 분리해 재물 결론을 잡았습니다.",
    },
    career: {
      aria: "직업 핵심 결과",
      kicker: "직업 핵심",
      strongLabel: "가장 강한 직업 기준",
      watchLabel: "직업 관리 지점",
      lead: "일에서 인정받는 방식, 책임의 크기, 권한이 붙는 자리를 구분했습니다.",
    },
    love: {
      aria: "연애 핵심 결과",
      kicker: "연애 핵심",
      strongLabel: "가장 강한 관계 기준",
      watchLabel: "주의할 관계 기준",
      lead: "상대 선택, 애정 표현, 관계 지속력을 분리해 정리합니다.",
    },
    marriage: {
      aria: "결혼 핵심 결과",
      kicker: "결혼 핵심",
      strongLabel: "가장 강한 결혼 기준",
      watchLabel: "주의할 결혼 기준",
      lead: "생활 방식, 책임 분담, 가정 안정성을 나누어 결혼 결론을 잡았습니다.",
    },
  };
  return configs[domain] || {
    aria: "영역별 핵심 결과",
    kicker: "핵심 결과",
    strongLabel: "강한 기준",
    watchLabel: "보강할 기준",
    lead: "",
  };
}

function premiumSignatureStrongUnit(units) {
  const candidates = (units || []).filter((unit) => unit && unit.tone !== "watch" && unit.tone !== "risk");
  const pool = candidates.length ? candidates : units || [];
  return [...pool].sort((a, b) => Number(b?.score ?? -1) - Number(a?.score ?? -1))[0] || null;
}

function premiumSignatureWatchUnit(units, strong) {
  const watchCandidates = (units || []).filter((unit) => unit && unit !== strong && (unit.tone === "watch" || unit.tone === "risk"));
  const pool = watchCandidates.length ? watchCandidates : (units || []).filter((unit) => unit && unit !== strong);
  return [...pool].sort((a, b) => Number(a?.score ?? 101) - Number(b?.score ?? 101))[0] || null;
}

function premiumSignatureDisplayValue(unit, tone) {
  const raw = cleanCustomerLabel(unit?.value || premiumMetricValueFromScore(Number(unit?.score)));
  if (tone === "watch") {
    return raw
      .replaceAll("주의 필요", "주의")
      .replaceAll("하위권", "주의")
      .replaceAll("약세", "주의")
      .replaceAll("낮음", "주의");
  }
  return raw.replaceAll("좋음", "강세").replaceAll("양호", "양호권");
}

function premiumCardMetricValue(item) {
  const score = Number(item?.score);
  const tone =
    item?.tone === "watch" || item?.tone === "risk" || (Number.isFinite(score) && score < 56)
      ? "watch"
      : item?.tone || "neutral";
  return premiumSignatureDisplayValue(item, tone);
}

function renderPremiumSignatureMajorCard(title, unit, tone) {
  if (!unit) {
    return "";
  }
  const score = Number(unit.score);
  const width = Number.isFinite(score) ? Math.max(8, Math.min(100, Math.round(score))) : null;
  const body = cleanPremiumDisplayText(unit.body || "");
  return `
    <article class="is-${escapeHtml(tone)}">
      <span>${escapeHtml(title)}</span>
      <div>
        <b>${escapeHtml(cleanCustomerLabel(unit.label || ""))}</b>
        <strong>${escapeHtml(premiumSignatureDisplayValue(unit, tone))}</strong>
      </div>
      ${width ? `<i aria-label="지표 강도"><em style="width:${width}%"></em></i>` : ""}
      ${body ? `<p>${escapeHtml(firstSentences(body, 1))}</p>` : ""}
    </article>
  `;
}

function renderPremiumSignatureAxis(unit) {
  const score = Number(unit?.score);
  const width = Number.isFinite(score) ? Math.max(8, Math.min(100, Math.round(score))) : null;
  return `
    <span>
      <b>${escapeHtml(cleanCustomerLabel(unit?.label || ""))}</b>
      <strong>${escapeHtml(premiumSignatureDisplayValue(unit, unit?.tone === "watch" || unit?.tone === "risk" ? "watch" : "neutral"))}</strong>
      ${width ? `<i aria-hidden="true"><em style="width:${width}%"></em></i>` : ""}
    </span>
  `;
}

function renderPremiumCoreProfileBoard(section) {
  const units = premiumDomainResultUnits(section).slice(0, premiumReadingUnitLimit(section));
  if (!units.length) {
    return "";
  }
  const domain = premiumSectionDomain(section);
  return `
    <section class="premium-core-profile-board domain-${escapeHtml(domain)}" aria-label="세부 지표">
      <header>
        <span>세부 지표</span>
        <strong>${escapeHtml(premiumNavTitle(section))}</strong>
      </header>
      <div>
        ${units.map(renderPremiumCoreProfileRow).join("")}
      </div>
    </section>
  `;
}

function renderPremiumCoreProfileRow(unit) {
  const score = Number(unit?.score);
  const hasScore = Number.isFinite(score);
  const width = hasScore ? Math.max(8, Math.min(100, Math.round(score))) : null;
  const tone = unit?.tone === "watch" || unit?.tone === "risk" ? "watch" : unit?.tone || "neutral";
  const body = cleanPremiumDisplayText(unit?.body || "");
  const value = premiumSignatureDisplayValue(unit, tone === "watch" ? "watch" : "neutral");
  return `
    <article class="is-${escapeHtml(tone)}">
      <div>
        <b>${escapeHtml(unit.label)}</b>
        ${value ? `<strong>${escapeHtml(value)}</strong>` : ""}
      </div>
      ${width ? `<i aria-label="지표 강도"><em style="width:${width}%"></em></i>` : ""}
      ${body ? `<p>${escapeHtml(firstSentences(body, 1))}</p>` : ""}
    </article>
  `;
}

function renderPremiumDomainResultSheet(section) {
  const profile = section?.section_profile || {};
  const title = cleanCustomerLabel(profile.type || premiumSectionFocus(section));
  const summary = cleanPremiumDisplayText(profile.summary || premiumSectionHeadline(section));
  const units = premiumDomainResultUnits(section).slice(0, 4);
  if (!title && !summary && !units.length) {
    return "";
  }
  return `
    <section class="premium-domain-result-sheet" aria-label="영역별 핵심 운세">
      <header>
        <span>${escapeHtml(premiumNavTitle(section))} 핵심 운세</span>
        ${title ? `<strong>${escapeHtml(title)}</strong>` : ""}
      </header>
      ${summary ? `<p>${escapeHtml(summary)}</p>` : ""}
      ${
        units.length
          ? `<div class="premium-domain-result-grid">
              ${units.map(renderPremiumDomainResultUnit).join("")}
            </div>`
          : ""
      }
    </section>
  `;
}

function premiumDomainResultUnits(section) {
  const rows = [];
  const seen = new Set();
  const summaryText = cleanPremiumDisplayText(section?.section_profile?.summary || premiumSectionHeadline(section));
  const pushRow = (source, role = "") => {
    const label = cleanCustomerLabel(source?.display_label || source?.label || source?.title || source?.source_title || "");
    if (!label) {
      return;
    }
    const key = premiumTopicMatchKey(label);
    if (key && seen.has(key)) {
      return;
    }
    if (key) {
      seen.add(key);
    }
    const score = Number(source?.score);
    const value = premiumDisplayPoint(source?.value || premiumMetricValueFromScore(score));
    let body = cleanPremiumDisplayText(source?.result || source?.focus || source?.caption || source?.body || "");
    body = removeShownSentences(body, summaryText, 1);
    rows.push({
      label,
      value,
      body,
      score: Number.isFinite(score) ? score : null,
      tone: source?.tone || role,
      role,
    });
  };
  const profileItems = Array.isArray(section?.section_profile?.items) ? section.section_profile.items : [];
  const visualItems = Array.isArray(section?.visual_profile?.items) ? section.visual_profile.items : [];
  const readingUnits = Array.isArray(section?.category_contract?.reading_units) ? section.category_contract.reading_units : [];
  profileItems.forEach((item) => pushRow(item, "profile"));
  visualItems.forEach((item) => pushRow(item, "visual"));
  readingUnits.forEach((item) => pushRow(item, "reading"));
  return premiumPrioritizedDomainResultUnits(rows, section);
}

function premiumPrioritizedDomainResultUnits(rows, section) {
  const priority = premiumMetricDomainPriority(premiumSectionDomain(section));
  return rows
    .filter((row) => row.label && (row.value || row.body || row.score !== null))
    .map((row) => ({
      ...row,
      priority: priority.indexOf(cleanCustomerLabel(row.label)),
    }))
    .sort((a, b) => {
      const aPriority = a.priority >= 0 ? a.priority : 99;
      const bPriority = b.priority >= 0 ? b.priority : 99;
      if (aPriority !== bPriority) {
        return aPriority - bPriority;
      }
      const aTone = a.tone === "watch" || a.tone === "risk" ? 1 : 0;
      const bTone = b.tone === "watch" || b.tone === "risk" ? 1 : 0;
      if (aTone !== bTone) {
        return aTone - bTone;
      }
      return Number(b.score || 0) - Number(a.score || 0);
    });
}

function renderPremiumDomainResultUnit(unit) {
  const score = Number(unit?.score);
  const hasScore = Number.isFinite(score);
  const width = hasScore ? Math.max(8, Math.min(100, Math.round(score))) : null;
  const tone = unit?.tone === "watch" || unit?.tone === "risk" ? "watch" : unit?.tone || "neutral";
  const body = cleanPremiumDisplayText(unit?.body || "");
  const value = unit.value ? premiumSignatureDisplayValue(unit, tone === "watch" ? "watch" : "neutral") : "";
  return `
    <article class="premium-domain-result-unit is-${escapeHtml(tone)}">
      <div>
        <b>${escapeHtml(unit.label)}</b>
        ${value ? `<strong>${escapeHtml(value)}</strong>` : ""}
      </div>
      ${hasScore ? `<i aria-label="지표 강도"><em style="width:${width}%"></em></i>` : ""}
      ${body ? `<p>${escapeHtml(firstSentences(body, 2))}</p>` : ""}
    </article>
  `;
}

function renderPremiumContentPlan(section) {
  const plan = premiumContentPlanItems(section);
  if (!plan.length) {
    return "";
  }
  return `
    <section class="premium-content-plan" aria-label="읽는 순서">
      <header>
        <span>읽는 순서</span>
        <strong>${escapeHtml(premiumContentPlanTitle(section))}</strong>
      </header>
      <div class="premium-content-plan-grid">
        ${plan
          .map(
            (item) => `
              <article class="is-${escapeHtml(item.slot || "default")}">
                <header>
                  <b>${escapeHtml(item.label)}</b>
                  ${item.value ? `<strong>${escapeHtml(item.value)}</strong>` : ""}
                </header>
                <p>${escapeHtml(item.result || item.purpose)}</p>
                ${
                  Number.isFinite(Number(item.score))
                    ? `<i aria-label="세부 지표 강약"><em style="width:${Math.max(0, Math.min(100, Number(item.score)))}%"></em></i>`
                    : ""
                }
                ${item.purpose && item.purpose !== item.result ? `<small>${escapeHtml(item.purpose)}</small>` : ""}
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function premiumContentPlanItems(section) {
  const rawPlan = Array.isArray(section?.category_contract?.content_plan) ? section.category_contract.content_plan : [];
  const preferredSlots = ["opening", "primary_profile", "behavior_scene", "strength_metric", "management_metric"];
  const seen = new Set();
  const picked = [];
  preferredSlots.forEach((slot) => {
    const item = rawPlan.find((entry) => entry?.slot === slot && entry?.label && entry?.purpose);
    if (item) {
      seen.add(slot);
      picked.push(item);
    }
  });
  rawPlan.forEach((item) => {
    if (picked.length >= 5) {
      return;
    }
    const slot = item?.slot || "";
    if (!seen.has(slot) && item?.label && item?.purpose) {
      seen.add(slot);
      picked.push(item);
    }
  });
  return picked.map((item) => ({
    slot: cleanCustomerLabel(item.slot || "default").replace(/\s+/g, "-").toLowerCase(),
    label: cleanCustomerLabel(item.label || ""),
    purpose: cleanPremiumDisplayText(item.purpose || ""),
    result: cleanPremiumDisplayText(item.result || ""),
    source: cleanCustomerLabel(item.source || ""),
    value: premiumDisplayPoint(item.value || ""),
    tone: cleanCustomerLabel(item.tone || "neutral"),
    score: item.score,
    linkedTopic: cleanCustomerLabel(item.linked_topic || ""),
  }));
}

function premiumContentPlanTitle(section) {
  const domain = premiumSectionDomain(section);
  const titles = {
    personality: "성격에서 확인하는 내용",
    money: "재물운에서 확인하는 내용",
    career: "직업운에서 확인하는 내용",
    love: "연애운에서 확인하는 내용",
    marriage: "결혼운에서 확인하는 내용",
    life: "인생 구간에서 확인하는 내용",
    honor: "명예운에서 확인하는 내용",
    social: "대인관계운에서 확인하는 내용",
  };
  return titles[domain] || "이 영역에서 확인하는 내용";
}

function renderPremiumSectionProfile(section) {
  const profile = section?.section_profile || {};
  const items = Array.isArray(profile.items) ? profile.items.filter((item) => item?.label && (item?.value || item?.text)).slice(0, 3) : [];
  if (!profile.type && !profile.summary && !items.length) {
    return "";
  }
  return `
    <section class="premium-section-profile" aria-label="핵심 유형">
      <header>
        <span>${escapeHtml(cleanCustomerLabel(profile.label || "핵심 유형"))}</span>
        ${profile.type ? `<strong>${escapeHtml(cleanCustomerLabel(profile.type))}</strong>` : ""}
      </header>
      ${profile.summary ? `<p>${escapeHtml(cleanPremiumDisplayText(profile.summary))}</p>` : ""}
      ${
        items.length
          ? `<div>${items
              .map(
                (item) => `
                  <article class="is-${escapeHtml(item.tone || "neutral")}">
                    <b>${escapeHtml(cleanCustomerLabel(item.label || ""))}</b>
                    <strong>${escapeHtml(cleanCustomerLabel(item.value || ""))}</strong>
                    ${item.grade ? `<em>${escapeHtml(cleanCustomerLabel(item.grade))}</em>` : ""}
                    ${item.text ? `<p>${escapeHtml(cleanPremiumDisplayText(item.text))}</p>` : ""}
                  </article>
                `,
              )
              .join("")}</div>`
          : ""
      }
    </section>
  `;
}

function renderPremiumProfileInsights(section) {
  const insights = Array.isArray(section?.section_profile?.insights)
    ? section.section_profile.insights.filter((item) => item?.label && (item?.body || item?.value)).slice(0, 4)
    : [];
  if (!insights.length) {
    return "";
  }
  return `
    <section class="premium-profile-insights" aria-label="핵심 해석">
      <header>
        <span>핵심 해석</span>
        <strong>${escapeHtml(premiumNavTitle(section))}</strong>
      </header>
      <div>
        ${insights
          .map(
            (item) => `
              <article class="is-${escapeHtml(item.tone || "neutral")}">
                <span>${escapeHtml(cleanCustomerLabel(item.label || ""))}</span>
                ${item.value ? `<b>${escapeHtml(cleanCustomerLabel(item.value || ""))}</b>` : ""}
                ${item.body ? `<p>${escapeHtml(cleanPremiumDisplayText(item.body || ""))}</p>` : ""}
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderPremiumSectionStoryCards(section) {
  const cards = Array.isArray(section?.section_story_cards)
    ? section.section_story_cards.filter((item) => item?.label && (item?.title || item?.body)).slice(0, 3)
    : [];
  if (!cards.length) {
    return "";
  }
  return `
    <section class="premium-section-story-cards" aria-label="구체적 양상">
      <header>
        <span>구체적 양상</span>
        <strong>${escapeHtml(premiumNavTitle(section))}</strong>
      </header>
      <div>
        ${cards
          .map(
            (item) => `
              <article class="is-${escapeHtml(item.tone || "neutral")}">
                <span>${escapeHtml(cleanCustomerLabel(item.label || ""))}</span>
                ${item.title ? `<b>${escapeHtml(cleanCustomerLabel(item.title || ""))}</b>` : ""}
                ${item.body ? `<p>${escapeHtml(cleanPremiumDisplayText(item.body || ""))}</p>` : ""}
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderPremiumProfileMatrix(section) {
  const topics = Array.isArray(section?.topic_items)
    ? section.topic_items
        .filter((item) => item?.title && (item?.body || item?.definition))
        .slice(0, premiumReadingUnitLimit(section))
    : [];
  if (!topics.length || premiumSectionDomain(section) === "timing") {
    return "";
  }
  return `
    <section class="premium-profile-matrix" aria-label="프리미엄 세부 지표">
      <div class="premium-profile-matrix-head">
        <span>세부 지표</span>
        <strong>${topics.length}개 지표</strong>
      </div>
      <div class="premium-profile-matrix-grid">
        ${topics
          .map((item) => {
            const score = Number(item.score);
            const width = Number.isFinite(score) ? Math.max(0, Math.min(100, score)) : premiumProfileMetricWidth(item);
            const definition = cleanPremiumDisplayText(item.definition || "");
            const body = cleanPremiumDisplayText(item.body || "");
            return `
              <article class="is-${escapeHtml(item.tone || "neutral")}">
                <header>
                  <b>${escapeHtml(cleanCustomerLabel(item.title || ""))}</b>
                  ${item.value ? `<strong>${escapeHtml(cleanCustomerLabel(item.value))}</strong>` : ""}
                </header>
                <i aria-label="지표 강도"><em style="width:${width}%"></em></i>
                ${definition ? `<small>${escapeHtml(definition)}</small>` : ""}
                ${body ? `<p>${escapeHtml(body)}</p>` : ""}
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function renderPremiumReadingUnits(section) {
  const unitLimit = premiumReadingUnitLimit(section);
  const units = Array.isArray(section?.category_contract?.reading_units)
    ? section.category_contract.reading_units.filter((item) => item?.label && (item?.result || item?.focus)).slice(0, unitLimit)
    : [];
  if (!units.length) {
    return "";
  }
  return `
    <section class="premium-reading-units" aria-label="프리미엄 핵심 내용">
      <div class="premium-reading-units-head">
        <span>핵심 내용</span>
        <strong>${units.length}개 기준</strong>
      </div>
      <div class="premium-reading-unit-grid">
        ${units
          .map((unit) => {
            const resultText = cleanPremiumDisplayText(unit.result || unit.focus || "");
            const focusText = cleanPremiumDisplayText(unit.focus || "");
            const showFocus = focusText && focusText !== resultText;
            return `
              <article class="is-${escapeHtml(unit.tone || "neutral")}">
                <header>
                  <b>${escapeHtml(cleanCustomerLabel(unit.display_label || unit.label || ""))}</b>
                  ${unit.value ? `<strong>${escapeHtml(cleanCustomerLabel(unit.value))}</strong>` : ""}
                </header>
                <p>${escapeHtml(resultText)}</p>
                ${showFocus ? `<small>${escapeHtml(focusText)}</small>` : ""}
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function premiumReadingUnitLimit(section) {
  return premiumSectionDomain(section) === "personality" ? 6 : 5;
}

function renderPremiumDomainVisualProfile(section) {
  const profile = section?.visual_profile || {};
  const items = Array.isArray(profile.items) ? profile.items.slice(0, 3) : [];
  if (!items.length) {
    return "";
  }
  const domain = premiumSectionDomain(section);
  return `
    <section class="premium-domain-visual-profile domain-${escapeHtml(domain)}" aria-label="영역별 시각 요약">
      <header>
        <span>${escapeHtml(cleanCustomerLabel(profile.label || "핵심 결과"))}</span>
        <p>${escapeHtml(cleanPremiumDisplayText(profile.headline || ""))}</p>
      </header>
      <div>
        ${items
          .map(
            (item) => `
              <article class="is-${escapeHtml(item.tone || "neutral")}">
                <b>${escapeHtml(cleanCustomerLabel(item.label || ""))}</b>
                <strong>${escapeHtml(premiumCardMetricValue(item) || "확인")}</strong>
                ${item.caption ? `<p>${escapeHtml(cleanPremiumDisplayText(item.caption))}</p>` : ""}
                ${
                  Number.isFinite(Number(item.score))
                    ? `<i aria-label="지표 강도"><em style="width:${Math.max(0, Math.min(100, Number(item.score)))}%"></em></i>`
                    : ""
                }
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderPremiumDomainGuide(section) {
  const guide = premiumDomainGuide(section);
  if (!guide) {
    return "";
  }
  const unitLimit = premiumReadingUnitLimit(section);
  const role = cleanPremiumDisplayText(section?.category_contract?.profile_role || "");
  const readingOrder = Array.isArray(section?.category_contract?.reading_order)
    ? section.category_contract.reading_order.map((item) => cleanCustomerLabel(item || "")).filter(Boolean).slice(0, unitLimit)
    : [];
  return `
    <div class="premium-domain-guide" aria-label="세부 운세 구성">
      <span>${escapeHtml(guide.label)}</span>
      <p>${escapeHtml(guide.body)}</p>
      ${role ? `<p class="premium-domain-guide-role"><b>다루는 내용</b>${escapeHtml(role)}</p>` : ""}
      ${
        readingOrder.length
          ? `<div class="premium-domain-guide-order" aria-label="읽는 순서"><strong>읽는 순서</strong>${readingOrder
              .map((item) => `<em>${escapeHtml(item)}</em>`)
              .join("")}</div>`
          : ""
      }
    </div>
  `;
}

function premiumDomainGuide(section) {
  const contract = section?.category_contract || {};
  const contractLabel = cleanCustomerLabel(contract.guide_label || "");
  const contractBody = cleanPremiumDisplayText(contract.guide_body || "");
  if (contractLabel || contractBody) {
    return {
      label: contractLabel || "세부 운세 구성",
      body: contractBody,
    };
  }
  const domain = premiumSectionDomain(section);
  const guides = {
    personality: {
      label: "성격 구성",
      body: "판단 기준, 대인 태도, 감정 반응, 압박을 받을 때의 모습이 나뉘어 드러납니다.",
    },
    money: {
      label: "재물 세부 운세",
      body: "재물 형성력, 수입 창출력, 자산화 능력, 계약·명의 안정성을 분리해 정리합니다.",
    },
    career: {
      label: "직업 세부 운세",
      body: "성취가 경력, 평가, 권한, 전문성으로 어떻게 남는지 나누어 정리합니다.",
    },
    love: {
      label: "관계 구성",
      body: "인연의 시작, 애정 표현, 관계 지속, 결혼으로 이어지는 현실성을 나누어 정리합니다.",
    },
    marriage: {
      label: "결혼 구성",
      body: "결혼은 감정만이 아니라 생활 기준, 주거, 재정, 가족 책임까지 함께 드러납니다.",
    },
    life: {
      label: "인생 구간 구성",
      body: "초년, 중년, 말년마다 책임과 성취가 강해지는 자리가 달라집니다.",
    },
    honor: {
      label: "명예 구성",
      body: "명예는 유명세보다 공식 평가가 오래 남는 방식을 중심으로 읽습니다.",
    },
    social: {
      label: "대인관계 구성",
      body: "대인관계는 실제 조력을 주는 사람, 오래 가는 신뢰, 부탁이 부담으로 바뀌는 지점에서 결론이 드러납니다.",
    },
  };
  return guides[domain] || null;
}

function premiumDomainSubLabel(section, title) {
  const label = cleanCustomerLabel(section.domain_label || "");
  if (label && label !== title) {
    return label;
  }
  const domain = premiumSectionDomain(section);
  const fallback = {
    personality: "성격 분석",
    money: "재물 세부 운세",
    career: "직업 세부 운세",
    love: "연애 세부 운세",
    marriage: "결혼 세부 운세",
    timing: "주요 연도",
    life: "인생 구간",
    honor: "명예 세부 운세",
    social: "대인관계",
  };
  return fallback[domain] || "프리미엄 항목";
}

function premiumDomainBadge(section) {
  const domain = premiumSectionDomain(section);
  if (domain === "timing") {
    return "연도";
  }
  if (domain === "personality") {
    return "성격 핵심";
  }
  return premiumGradeFromText(premiumSectionText(section), section);
}

function premiumDomainVerdictItems(section) {
  const domain = premiumSectionDomain(section);
  const base = premiumVerdictItems(section);
  if (domain === "personality") {
    const checkpoints = Array.isArray(section.checkpoints) ? section.checkpoints : [];
    const basis = premiumCheckpointValue(checkpoints, "판단 기준") || premiumCheckpointValue(checkpoints, "삶의 기준");
    const emotion = premiumCheckpointValue(checkpoints, "감정 반응") || base[1]?.value || "";
    const pressure = premiumCheckpointValue(checkpoints, "압박 대응") || premiumCheckpointValue(checkpoints, "압박을 받을 때") || base[2]?.value || "";
    return [
      { label: "판단 기준", value: basis },
      { label: "감정 반응", value: emotion },
      { label: "압박 대응", value: pressure },
    ].filter((item) => item.value);
  }
  const labels = {
    money: ["재물 결론", "수익 발생 지점", "금전 권리 안정성"],
    career: ["직업 결론", "평가 확보 지점", "경력 손실 지점"],
    love: ["연애 결론", "관계가 오래 가는 지점", "관계가 흔들리는 지점"],
    marriage: ["결혼 결론", "생활 안정 지점", "생활 주의점"],
    personality: ["성격 결론", "감정 반응", "압박 대응"],
    timing: ["상승 연도", "주의 연도", "인생 전환 연도"],
    life: ["인생 구간 결론", "강한 구간", "주의 구간"],
    honor: ["명예 결론", "공식 인정 지점", "평판 주의점"],
    social: ["대인관계 결론", "조력 관계", "관계 주의점"],
  }[domain] || ["핵심 결론", "강한 지점", "주의점"];
  return base.slice(0, 3).map((item, index) => ({
    label: labels[index] || item.label,
    value: item.value,
  }));
}

function premiumDomainDetailHighlights(section) {
  const domain = premiumSectionDomain(section);
  const dictionaryItems = premiumDictionaryItems(section).slice(0, 2);
  if (Array.isArray(section.detail_blocks) && section.detail_blocks.length) {
    const structuralItems = section.detail_blocks.slice(0, domain === "life" || domain === "honor" || domain === "social" ? 2 : 3).map((item) => ({
      title: cleanCustomerLabel(item.title || ""),
      body: cleanPremiumDisplayText(item.body || ""),
      bullets: Array.isArray(item.bullets) ? item.bullets.slice(0, 2).map(cleanPremiumDisplayText) : [],
      level: item.tone || "",
    }));
    if (dictionaryItems.length && (domain === "life" || domain === "honor" || domain === "social")) {
      const used = new Set(structuralItems.map((item) => premiumTopicMatchKey(item.title)));
      const selectedDetails = dictionaryItems
        .filter((item) => !used.has(premiumTopicMatchKey(item.title)))
        .map((item) => ({
          title: item.title,
          body: premiumDisplayPoint(item.judgment),
          bullets: item.scenes.slice(0, 2).map(premiumDisplayPoint),
          level: item.level,
        }));
      return [...structuralItems, ...selectedDetails].slice(0, 4);
    }
    return structuralItems;
  }
  if (dictionaryItems.length) {
    return dictionaryItems.map((item) => ({
      title: item.title,
      body: premiumDisplayPoint(item.judgment),
      bullets: item.scenes.slice(0, 2).map(premiumDisplayPoint),
      level: item.level,
    }));
  }
  return premiumDetailItems(section)
    .slice(0, 3)
    .map((item) => ({
      title: item.label,
      body: premiumDisplayPoint(item.value),
      bullets: [],
      level: premiumDetailClass(item).includes("strong") ? "strong" : "",
    }));
}

function renderPremiumTopicList(section) {
  const usedTopicKeys = new Set(
    Array.isArray(section?.visual_profile?.items)
      ? section.visual_profile.items
          .flatMap((item) => [item.label, item.source_title, item.title])
          .map(premiumTopicMatchKey)
          .filter(Boolean)
      : [],
  );
  if (Array.isArray(section?.category_contract?.reading_units)) {
    section.category_contract.reading_units.forEach((unit) => {
      [unit.label, unit.topic].forEach((label) => {
        const key = premiumTopicMatchKey(label);
        if (key) {
          usedTopicKeys.add(key);
        }
      });
    });
  }
  let topics = Array.isArray(section.topic_items)
    ? section.topic_items.filter((item) => !usedTopicKeys.has(premiumTopicMatchKey(item.title || ""))).slice(0, 4)
    : [];
  if (!topics.length) {
    return "";
  }
  return `
    <section class="premium-topic-list" aria-label="추가 해석">
      <div class="premium-topic-list-head">
        <span>추가 해석</span>
        <strong>세부 내용</strong>
      </div>
      <div class="premium-topic-items">
        ${topics
          .map(
            (item) => `
              <article class="${item.tone ? `is-${escapeHtml(item.tone)}` : ""}">
                <header>
                  <b>${escapeHtml(cleanCustomerLabel(item.title || ""))}</b>
                  ${item.value ? `<strong>${escapeHtml(cleanCustomerLabel(item.value))}</strong>` : ""}
                </header>
                ${
                  Number.isFinite(Number(item.score))
                    ? `<div class="premium-topic-meter" aria-label="지표 강도"><i style="width:${Math.max(0, Math.min(100, Number(item.score)))}%"></i></div>`
                    : ""
                }
                <p>${escapeHtml(cleanPremiumDisplayText(item.body || ""))}</p>
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function premiumTopicMatchKey(value) {
  const compact = cleanCustomerLabel(value || "").replace(/[·ㆍ\-\s()]/g, "");
  if (!compact) {
    return "";
  }
  const aliases = [
    ["대인조율", "대인거리감"],
    ["대인조율감", "대인거리감"],
    ["감정반응성", "감정반응"],
    ["압박대응력", "압박대응"],
    ["실행속도", "행동속도"],
    ["관심몰입도", "관심몰입"],
    ["재물발생", "재물발생력"],
    ["재물형성", "재물발생력"],
    ["재물형성력", "재물발생력"],
    ["수입전환", "수입창출력"],
    ["수입창출", "수입창출력"],
    ["수익전환", "수입창출력"],
    ["수익전환력", "수입창출력"],
    ["축재", "축재력"],
    ["자산축적", "축재력"],
    ["자산축적력", "축재력"],
    ["공동자금", "공동자금운영력"],
    ["공동재관리", "공동자금운영력"],
    ["공동재관리력", "공동자금운영력"],
    ["계약안정", "계약문서안정성"],
    ["계약안정성", "계약문서안정성"],
    ["계약문서", "계약문서안정성"],
    ["성과", "직업성취력"],
    ["성과증명", "직업성취력"],
    ["성과구현", "직업성취력"],
    ["성과구현력", "직업성취력"],
    ["평가", "업무평가력"],
    ["평가상승", "업무평가력"],
    ["평가확보", "업무평가력"],
    ["평가확보력", "업무평가력"],
    ["조직적합", "조직적합도"],
    ["조직적응", "조직적합도"],
    ["조직적응력", "조직적합도"],
    ["권한과책임", "권한책임균형도"],
    ["권한책임", "권한책임균형도"],
    ["전문성축적", "전문성"],
    ["전문성축적도", "전문성"],
    ["인연형성", "인연형성력"],
    ["호감형성", "인연형성력"],
    ["호감형성력", "인연형성력"],
    ["애정표현", "애정표현력"],
    ["관계안정", "관계안정성"],
    ["관계지속", "관계안정성"],
    ["관계지속력", "관계안정성"],
    ["결혼안정", "결혼안정성"],
    ["생활안정", "생활안정성"],
    ["생활기반안정", "생활안정성"],
    ["생활기반안정성", "생활안정성"],
    ["가족책임수용", "가족책임감"],
    ["가족책임수용력", "가족책임감"],
    ["사회적인정", "사회적인정도"],
    ["평판관리", "명예관리"],
    ["평판지속", "평판유지력"],
    ["평판지속력", "평판유지력"],
    ["관계지속", "관계지속력"],
    ["인맥형성", "사람을얻는방식"],
    ["조력자인연", "도움이되는사람"],
    ["책임경계", "부탁과책임"],
    ["책임경계력", "부탁과책임"],
  ];
  const matched = aliases.find((group) => group.some((alias) => compact.includes(alias) || alias.includes(compact)));
  return matched ? matched[0] : compact;
}

function renderPremiumDomainDetails(items) {
  if (!items.length) {
    return "";
  }
  return `
    <section class="premium-domain-detail-wrap" aria-label="구체적 양상">
      <div class="premium-domain-detail-head">
        <span>구체적 양상</span>
        <strong>주요 장면</strong>
      </div>
      <div class="premium-domain-detail-grid">
        ${items
          .map(
            (item) => `
              <section class="premium-domain-detail ${item.level === "strong" ? "is-strong" : item.level === "risk" ? "is-risk" : ""}">
                <h4>${escapeHtml(premiumDisplayAxisLabel(item.title))}</h4>
                <p>${escapeHtml(item.body)}</p>
                ${
                  item.bullets.length
                    ? `<ul>${item.bullets
                        .map(premiumDetailSceneText)
                        .filter(Boolean)
                        .map((bullet) => `<li>${escapeHtml(bullet)}</li>`)
                        .join("")}</ul>`
                    : ""
                }
              </section>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function premiumDisplayAxisLabel(value) {
  const label = cleanCustomerLabel(value || "");
  const labels = {
    "대인 거리감": "대인 조율감",
    "감정 반응": "감정 반응성",
    "압박 대응": "압박 대응력",
    "단호함과 고집": "기준 조율력",
    "행동 속도": "실행 속도",
    "관심 몰입": "관심 몰입도",
    "재물 발생력": "재물 형성력",
    "타고난 재물의 그릇": "재물 형성력",
    "재물이 들어오는 길": "수입 창출력",
    "수입 발생력": "수입 창출력",
    "재산으로 굳어지는 힘": "자산화 능력",
    "축재력": "자산화 능력",
    "자산 확정력": "자산화 능력",
    "재물에 얽히는 사람 문제": "공동자금 운영력",
    "공동 자금 운영력": "공동자금 운영력",
    "공동 자금 안정성": "공동자금 운영력",
    "돈을 지켜내는 기준": "계약·명의 안정성",
    "계약·문서 안정성": "계약·명의 안정성",
    "직업 성취력": "성취 축적력",
    "직업적 성취의 그릇": "성취 축적력",
    "업무 평가력": "평가·명예 전환력",
    "평가가 따라오는 자리": "평가·명예 전환력",
    "조직 적합도": "조직 적응력",
    "조직 안에서 자리 잡는 힘": "조직 적응력",
    "권한·책임 균형도": "권한 확보력",
    "권한과 책임의 균형": "권한 확보력",
    "전문성": "전문 자산화",
    "전문성으로 남는 힘": "전문 자산화",
    "인연이 들어오는 길": "인연 형성력",
    "인연 형성력": "인연 형성력",
    "애정이 표현되는 방식": "애정 표현성",
    "애정 표현력": "애정 표현성",
    "관계가 오래 가는 힘": "관계 지속력",
    "관계 안정성": "관계 지속력",
    "결혼으로 이어지는 현실성": "결혼 연결력",
    "결혼 현실화": "결혼 연결력",
    "함께 살아가는 기준": "생활 안정성",
    "생활 기준": "생활 안정성",
    "결혼 안정성": "혼인 성향",
    "생활 안정성": "생활 안정",
    "가족 책임감": "가족 책임 경계력",
    "결정 지속성": "유지와 위기",
    "평판 유지력": "평판이 오래 남는 힘",
    "공식 책임": "공식 책임을 맡는 힘",
    "공식 역할 수용력": "공식 책임을 맡는 힘",
    "사람을 얻는 방식": "사람을 얻는 힘",
    "도움이 되는 사람": "도움으로 이어지는 인연",
    "관계 지속력": "관계 지속력",
    "부탁과 책임": "부탁과 책임의 경계",
    "충돌이 생기는 자리": "혼인 갈등 조정력",
    "기록이 없을 때 생기는 손해": "기록·증빙 안정성",
    "부탁이 책임으로 바뀌는 관계": "관계 책임 경계력",
    "주의 연도": "시기 대응력",
    "주의 기준": "시기 대응력",
    "손실 연도": "손실 방어력",
    "위기 연도": "위기 대응력",
    "이별 가능성": "관계 유지력",
    "관계 이별": "관계 유지력",
    "부담 연도": "책임 관리력",
    "결정권 없는 책임": "권한 확보력",
    "계약 문서 손해": "계약·명의 안정성",
    "공동 자금 손실": "공동자금 운영력",
    "공동재 리스크": "공동자금 운영력",
  };
  if (labels[label]) {
    return labels[label];
  }
  if (/주의.*연도/u.test(label)) {
    return "시기 대응력";
  }
  if (/손실/u.test(label)) {
    return "손실 방어력";
  }
  if (/위기/u.test(label)) {
    return "위기 대응력";
  }
  if (/이별/u.test(label)) {
    return "관계 유지력";
  }
  if (/부담/u.test(label)) {
    return "책임 관리력";
  }
  return label;
}

function premiumFinalPointName(value) {
  return cleanCustomerLabel(premiumDisplayPoint(value))
    .replace(/\s*(최상위권|상위권|중상위권|평균권|주의 필요|최상|강함|좋음|보통|낮음)$/g, "")
    .trim();
}

function premiumFinalTitle(strongest) {
  const point = strongest ? premiumFinalPointName(premiumSectionFocus(strongest)) : "";
  if (point.includes("관계 안정") || point.includes("관계 지속") || point.includes("관계가 오래 남는 힘")) {
    return "인연을 오래 가져가고 평판이 단단해지는 사주입니다.";
  }
  if (point.includes("결혼")) {
    return "관계가 생활의 약속으로 이어지는 사주입니다.";
  }
  if (point.includes("혼인") || point.includes("배우자") || point.includes("가정")) {
    return "배우자와 생활의 기준이 인생 후반까지 중요하게 작용하는 사주입니다.";
  }
  if (point.includes("축재")) {
    return "수입이 자산으로 전환되는 사주입니다.";
  }
  if (point.includes("수입")) {
    return "일과 성과가 수입으로 바뀌는 사주입니다.";
  }
  if (point.includes("업무 평가") || point.includes("사회적 인정")) {
    return "사회적 평가와 평판이 크게 높아지는 사주입니다.";
  }
  if (point.includes("전문")) {
    return "전문성으로 평가받는 사주입니다.";
  }
  if (point) {
    return `${point} 중심의 사주입니다.`;
  }
  return "강점과 주의점이 함께 드러나는 사주입니다.";
}

function premiumFinalStrengthSentence(section) {
  if (!section) {
    return "";
  }
  const domain = premiumSectionDomain(section);
  const point = premiumFinalPointName(premiumSectionFocus(section));
  if (domain === "money") {
    if (point.includes("축재")) return "수입이 자산권으로 전환되는 재물운입니다.";
    if (point.includes("수입")) return "일과 성과가 보수, 계약금, 단가로 환산되는 재물운입니다.";
    if (point.includes("공동")) return "공동 자금에서 명의와 몫을 지키는지가 핵심입니다.";
    return "번 돈을 자기 자산으로 굳히는 힘이 강한 재물운입니다.";
  }
  if (domain === "career") {
    if (point.includes("전문")) return "직업운에서는 전문 영역이 분명할수록 직업적 신뢰가 쌓입니다.";
    if (point.includes("평가")) return "직업운에서는 맡은 일의 결과가 평판과 평가로 남습니다.";
    return "직업운에서는 역할이 분명할수록 경력과 평가가 본인 이름으로 남습니다.";
  }
  if (domain === "love") {
    if (point.includes("안정") || point.includes("지속")) return "한 번 깊어진 관계가 오래 유지되는 연애운입니다.";
    if (point.includes("표현")) return "마음이 말과 행동으로 드러날 때 인연의 진전이 분명해집니다.";
    return "상대를 고르는 기준이 분명할수록 연애운이 안정됩니다.";
  }
  if (domain === "marriage") {
    if (point.includes("생활") || point.includes("가정")) return "생활 기준과 책임감이 결혼운의 중심입니다.";
    if (point.includes("배우자")) return "배우자 선택이 결혼 생활의 안정성을 크게 끌어올립니다.";
    return "결혼운은 감정보다 생활의 지속성에서 강하게 드러납니다.";
  }
  if (domain === "honor") {
    return "명예운에서는 공식 평가가 실제 사회적 인정으로 남습니다.";
  }
  if (domain === "social") {
    return "대인관계에서는 넓은 인기보다 오래 남는 신뢰 관계가 강합니다.";
  }
  return point ? `${premiumNavTitle(section)}에서는 ${point}이 두드러집니다.` : "";
}

function premiumFinalRiskSentence(section) {
  if (!section) {
    return "";
  }
  const domain = premiumSectionDomain(section);
  const risk = premiumFinalPointName(premiumSectionRisk(section));
  if (domain === "money") {
    if (risk.includes("지출")) return "수입이 늘어도 고정비와 가족 비용이 앞서면 자산화가 늦어집니다.";
    if (risk.includes("공동")) return "가까운 사람과 자금을 섞으면 명의와 지분이 상대 쪽으로 기울기 쉽습니다. 공동 명의는 특히 신중해야 합니다.";
    if (risk.includes("계약") || risk.includes("문서")) return "계약서, 정산일, 지급 기준이 흐리면 수령액이 늦어지거나 일부 손실로 남습니다.";
  }
  if (domain === "career") {
    if (risk.includes("권한") || risk.includes("책임")) return "책임만 크고 결정권이 약한 자리는 경력에 흠이 남습니다. 성과가 있어도 공로가 다른 사람에게 넘어갈 수 있습니다.";
    return "성과 기준이 흐린 자리는 일한 만큼 인정받기 어렵습니다. 맡은 범위가 분명할수록 평가가 붙습니다.";
  }
  if (domain === "love" || domain === "marriage") {
    return "사랑이 깊어도 생활비, 주거, 가족 문제가 끼어들면 관계가 소모전으로 바뀝니다.";
  }
  return risk ? `${risk}은 별도로 관리해야 할 기준입니다.` : "";
}

function renderPremiumFinalSummary(report, sections) {
  const summary = premiumProfileSummary(report);
  const strongest = premiumStrongestSectionFromReport(report, sections);
  const money = premiumFindSection(sections, "money");
  const career = premiumFindSection(sections, "career");
  const relation = premiumFindSection(sections, "love") || premiumFindSection(sections, "marriage");
  const risk = premiumPrimaryRiskSection(sections, report);
  const conclusion =
    firstSentences(cleanPremiumDisplayText(summary.summary || ""), 2) ||
    premiumFinalTitle(strongest);
  const cards = [
    {
      label: "가장 강한 운",
      title: premiumNavTitle(strongest) || "핵심 강점",
      body: premiumFinalStrengthSentence(strongest) || premiumFinalStrengthSentence(money) || premiumFinalStrengthSentence(career),
      tone: "strong",
    },
    {
      label: "돈과 일",
      title: "성과가 남는 자리",
      body: premiumFinalDomainPairSentence(money, career),
      tone: "strong",
    },
    {
      label: "관계와 생활",
      title: "오래 가는 기준",
      body: premiumFinalStrengthSentence(relation),
      tone: "neutral",
    },
    {
      label: "주의할 지점",
      title: premiumNavTitle(risk) || "관리 기준",
      body: premiumFinalRiskSentence(risk),
      tone: "watch",
    },
  ]
    .map((card) => ({ ...card, body: cleanPremiumDisplayText(card.body || "") }))
    .filter((card) => card.body)
    .filter((card, index, list) => list.findIndex((item) => normalizedSentenceKey(item.body) === normalizedSentenceKey(card.body)) === index);
  const finalRule = cleanPremiumDisplayText(premiumFinalPracticalRule(strongest, risk, money, career));
  return `
    <section class="premium-final-summary">
      <div>
        <p class="eyebrow">최종 요약</p>
        <h2>${escapeHtml(premiumFinalTitle(strongest))}</h2>
      </div>
      ${conclusion ? `<p class="premium-final-lead">${escapeHtml(conclusion)}</p>` : ""}
      ${
        cards.length
          ? `<div class="premium-final-summary-grid">
              ${cards.map(renderPremiumFinalSummaryCard).join("")}
            </div>`
          : ""
      }
      ${finalRule ? `<p class="premium-final-rule">${escapeHtml(finalRule)}</p>` : ""}
    </section>
  `;
}

function renderPremiumFinalSummaryCard(card) {
  return `
    <article class="premium-final-summary-card is-${escapeHtml(card.tone || "neutral")}">
      <span>${escapeHtml(card.label || "요약")}</span>
      <strong>${escapeHtml(card.title || "")}</strong>
      <p>${escapeHtml(card.body || "")}</p>
    </article>
  `;
}

function premiumFinalDomainPairSentence(money, career) {
  const moneyText = premiumFinalStrengthSentence(money);
  const careerText = premiumFinalStrengthSentence(career);
  if (moneyText && careerText) {
    return `${moneyText} ${careerText}`;
  }
  return moneyText || careerText || "";
}

function premiumFinalPracticalRule(strongest, risk, money, career) {
  const riskDomain = premiumSectionDomain(risk);
  if (riskDomain === "money") {
    return "큰돈이 오갈 때는 명의, 지분, 지급일을 먼저 확정해야 합니다.";
  }
  if (riskDomain === "career") {
    return "직업 선택에서는 직함보다 권한과 평가 기준을 먼저 확인해야 합니다.";
  }
  if (riskDomain === "love" || riskDomain === "marriage") {
    return "관계에서는 감정보다 생활 기준을 먼저 맞춰야 오래 갑니다.";
  }
  const strongDomain = premiumSectionDomain(strongest);
  if (strongDomain === "money") {
    return "이 사주는 돈이 들어오는 자리보다 자기 몫으로 남는 구조를 먼저 잡아야 합니다.";
  }
  if (strongDomain === "career") {
    return "이 사주는 맡은 일이 본인 이름과 평가로 남는 자리를 잡을수록 강합니다.";
  }
  if (premiumSectionDomain(money) === "money" && premiumSectionDomain(career) === "career") {
    return "돈과 직업은 따로 움직이기보다 같은 자리에서 결과가 납니다.";
  }
  return "강한 운은 살리고, 약한 지점은 기준을 세워 관리하는 것이 핵심입니다.";
}

function renderPremiumResultFooter() {
  return `
    <section id="premium-result-bottom" class="premium-result-footer" aria-label="추가 확인">
      <div class="premium-result-footer-actions">
        <button class="premium-footer-action" type="button" data-input-target="birth">출생 정보 수정</button>
        <button class="premium-footer-action" type="button" data-view-target="basis">명식표 보기</button>
        <a class="service-blog-button premium-blog-button premium-footer-action is-bottom" href="https://place-leehyeon.tistory.com/" target="_blank" rel="noopener noreferrer">
          사주명리 공간 : 이현 블로그
        </a>
      </div>
    </section>
  `;
}

function premiumSectionDomain(section) {
  const domain = String(section?.domain || "");
  if (domain) {
    return domain;
  }
  return domainKeyFromText([section?.domain_label, section?.heading, section?.section_id].filter(Boolean).join(" "));
}

function premiumFindSection(sections, domains) {
  const target = Array.isArray(domains) ? domains : [domains];
  return sections.find((section) => target.includes(premiumSectionDomain(section))) || null;
}

function premiumSectionText(section) {
  return [
    section?.domain,
    section?.domain_label,
    section?.heading,
    section?.lead,
    section?.caution_label,
    ...(Array.isArray(section?.checkpoints) ? section.checkpoints : []),
    ...(Array.isArray(section?.judgment_axes)
      ? section.judgment_axes.map((axis) => `${axis?.label || ""} ${axis?.value || ""}`)
      : []),
  ]
    .filter(Boolean)
    .join(" ");
}

function premiumGradeFromText(text, section = null) {
  const value = String(text || "");
  const score = Number(section?.strength_score || 0);
  if (/^(주의|위험|손실|불균형|혼선)$/.test(value.trim()) || /^(주의|위험|손실)/.test(value.trim())) {
    return "주의";
  }
  if (score >= 88 || value.includes("최상위권") || value.includes("최상위")) {
    return "최상";
  }
  if (value.includes("중상위권") || value.includes("중상")) {
    return "좋음";
  }
  if (score >= 78 || value.includes("상위권") || value.includes("강세")) {
    return "강함";
  }
  if (score >= 68) {
    return "좋음";
  }
  if (value.includes("평균권") || value.includes("보통")) {
    return "보통";
  }
  if (value.includes("약세") || value.includes("낮음")) {
    return "약함";
  }
  return "확인";
}

function premiumMetricGrade(value, label, section = null) {
  const text = String(value || "");
  if (isInverseMetricLabel(label)) {
    if (/안정|낮은 주의|주의 낮음/.test(text)) return "안정";
    if (/보통|중간/.test(text)) return "보통";
    if (/낮음|약세|약함|주의|높음|강함|위험|저하/.test(text)) return "낮음";
    return "확인";
  }
  return premiumGradeFromText(value, null);
}

function premiumGradeClass(grade) {
  if (/최상|강함|안정/.test(grade)) return "is-strong";
  if (/좋음|보통|확인/.test(grade)) return "is-normal";
  if (/주의|약함|손실|낮음|저하/.test(grade)) return "is-risk";
  return "";
}

function cleanPremiumDisplayText(value) {
  return cleanReportCardHeadline(value || "")
    .replace(/^이 사주는\s*/, "")
    .replaceAll("이 사주는 ", "")
    .replace(/^[가-힣A-Za-z0-9·\s]+형\s*[-–]\s*/, "")
    .replaceAll("사회 평가·관계 안정형", "평판·인연 장기형")
    .replaceAll("관계 안정·사회 평가형", "인연·평판 장기형")
    .replaceAll("관계 안정·평판 축적형", "인연·평판 장기형")
    .replaceAll("사회 평가형", "평판 장기형")
    .replaceAll("평판 축적형", "평판 장기형")
    .replaceAll("관계운이 강합니다. 사회적 평판도 강합니다.", "한 번 맺은 인연이 오래 가고, 시간이 지날수록 평판이 단단해집니다.")
    .replaceAll("관계가 오래 남습니다. 사회적 평가도 따라붙습니다.", "한 번 맺은 인연이 오래 가고, 시간이 지날수록 평판이 단단해집니다.")
    .replaceAll("관계의 지속력과 사회적 평가가 함께 강한 사주입니다.", "인연을 오래 가져가고, 시간이 지날수록 평판이 단단해지는 사주입니다.")
    .replaceAll("한 번 깊어진 관계가 쉽게 끊어지지 않습니다.", "한 번 깊어진 인연은 쉽게 끊어지지 않습니다.")
    .replaceAll("관계가 쉽게 끊기지 않는 힘이 큽니다.", "한 번 깊어진 인연은 쉽게 끊어지지 않습니다.")
    .replaceAll("관계 유지력이 강하게 잡혀 있습니다.", "사람과의 신뢰가 시간이 지나며 사회적 평판으로 남습니다.")
    .replaceAll("관계 유지력과 평판 축적력이 중심입니다.", "인연을 오래 가져가며, 주변의 신뢰가 사회적 평판으로 남습니다.")
    .replaceAll("관계운이 강합니다.", "한 번 맺은 인연이 오래 이어집니다.")
    .replaceAll("사회적 평판도 강합니다.", "사회적 평판이 오래 남습니다.")
    .replaceAll("사회적 평가가 강하게 붙습니다.", "사회적 평판이 오래 남습니다.")
    .replaceAll("따라붙습니다", "오래 남습니다")
    .replaceAll("직업운에서는 역할이 분명할수록 경력과 평가가 본인 이름으로 남습니다.", "직업운은 직함과 평판으로 남는 성취가 강합니다.")
    .replaceAll("당신은 판단의 중심이 분명한 사람입니다.", "당신은 중요한 선택 앞에서 자기 기준을 쉽게 내주지 않는 편입니다.")
    .replaceAll("맡은 일을 결과와 평가로 남기는 직업운입니다.", "맡은 일이 직함과 평판으로 남는 직업운입니다.")
    .replaceAll("맡은 일이 다음 자리의 근거로 남는 직업운입니다.", "맡은 일이 직함과 평판으로 남는 직업운입니다.")
    .replaceAll("결과가 직함으로 남는 힘이 강합니다.", "결과가 직함과 평판으로 굳어집니다.")
    .replaceAll("직업운은 성취가 직함과 평가로 남는 쪽입니다.", "직업운은 성취가 직함과 평판으로 굳어지는 쪽입니다.")
    .replaceAll("필요한 항목을 눌러 확인하세요.", "필요한 항목만 열어 확인하세요.")
    .replaceAll("인생 구간별 강점과 사회적 확장을 확인합니다.", "인생의 전환점과 성취 시기가 분명합니다.")
    .replaceAll("생애 구간마다 강해지는 운이 다릅니다.", "인생의 전환점과 성취 시기가 분명합니다.")
    .replaceAll("초년·중년·말년, 명예운, 대인관계운을 따로 확인합니다.", "초년·중년·말년과 명예·대인관계를 이어서 확인합니다.")
    .replaceAll("세부 기준을 더 좁혀 판정합니다.", "세부 기준이 더 선명하게 드러납니다.")
    .replaceAll("함께 확인됩니다.", "동시에 드러납니다.")
    .replaceAll("함께 읽습니다.", "함께 드러납니다.")
    .replaceAll(["함께", "봅니다."].join(" "), "함께 확인합니다.")
    .replaceAll(["함께", "살핍니다."].join(" "), "세밀하게 따집니다.")
    .replaceAll("20세~79세 전체에서 운이 강해지는 해와 조심해야 할 해가 분명히 갈립니다.", "20세부터 79세까지 상승 연도와 주의 연도가 분명하게 드러납니다.")
    .replaceAll("확인 구간", "분석 범위")
    .replaceAll("사건 주제", "연도별 작용")
    .replaceAll("분리해 판정합니다.", "나누어 정리합니다.")
    .replaceAll("기운이 살아나고", "활력이 붙고")
    .replaceAll("좋은 연도에는 계약, 승진, 자산 취득처럼 결과가 남습니다", "계약, 승진, 자산 확보가 두드러집니다")
    .replaceAll("주의 연도에는 돈, 계약, 관계 중 하나가 크게 흔들립니다", "금전, 계약, 관계에서 관리할 일이 생깁니다")
    .replaceAll("상승 지점과 경계 지점을 연도별로 나눴습니다.", "상승 연도와 주의 연도를 정리했습니다.")
    .replaceAll("연령대별 전체표", "20~70대 연도표")
    .replaceAll("초년 기준 확립형", "초년 자기 기준 확립형")
    .replaceAll("초년부터 주관이 뚜렷합니다.", "어릴 때부터 자기 판단이 뚜렷합니다.")
    .replaceAll("공식 평판 책임형", "책임으로 평판을 얻는 형")
    .replaceAll("공식 책임형", "책임을 맡을수록 명예가 붙는 사주")
    .replaceAll("책임자, 관리자, 대표 역할이 잘 맞습니다.", "책임 있는 자리에서 평판을 얻습니다.")
    .replaceAll("신뢰 축적형", "장기 신뢰형")
    .replaceAll("신뢰 누적형", "오래 쌓은 신뢰가 힘이 되는 사주")
    .replaceAll("연도 사건 집중형", "좋은 해와 주의할 해가 뚜렷한 사주")
    .replaceAll("마음이 살아납니다", "관심이 분명해집니다")
    .replaceAll("관심이 살아납니다", "관심이 분명해집니다")
    .replaceAll("성격의 장점이 살아납니다", "장점이 분명하게 드러납니다")
    .replaceAll("고집이 강해 보입니다", "자기 기준이 완고하게 드러납니다")
    .replaceAll("공동비용 정산 주의", "공동 자금 관리력")
    .replaceAll("책임·권한 불균형", "권한·책임 균형도")
    .replaceAll("수입 발생과 자산 귀속이 함께 드러나는 재물운입니다.", "번 돈을 자기 자산으로 굳히는 힘이 강한 재물운입니다.")
    .replaceAll("감정이 생활 약속으로 이어지는 연애·결혼운입니다.", "결혼운은 생활의 지속성에서 강하게 드러납니다.")
    .replaceAll("연애와 결혼 모두 안정성이 강하게 드러납니다.", "연애운은 오래 이어질 관계를 고르는 힘에서 결론이 납니다.")
    .replaceAll("수입이 커지는 만큼 고정비와 가족 비용이 불어나 자산화가 늦어집니다.", "수입이 늘어도 가족 비용과 고정비가 앞서면 자산화가 늦어집니다.")
    .replaceAll("감정 표현 차이", "감정 표현이 늦어지면 상대가 거리감을 느낍니다")
    .replaceAll("감정 거리 차이", "감정 표현이 늦어지면 상대가 거리감을 느낍니다")
    .replaceAll("대표 판정", "대표 결과")
    .replaceAll("핵심 판정", "핵심 결과")
    .replaceAll("세부 판정", "세부 내용")
    .replaceAll("추가 판정", "추가 내용")
    .replaceAll("판정 기준", "근거 항목")
    .replaceAll("판정 근거", "근거 항목")
    .replaceAll("판정 범위", "분석 범위")
    .replaceAll("판정 배경", "분석 배경")
    .replaceAll("월령 판정", "월령 기준")
    .replaceAll("연도 판정", "연도 결과")
    .replaceAll("주의 판정", "주의 기준")
    .replaceAll("판정합니다", "정리합니다")
    .replaceAll("판정했습니다", "정리했습니다")
    .replaceAll("판정한", "정리한")
    .replaceAll("판정에", "분석에")
    .replaceAll("판정이", "결과가")
    .replaceAll("판정은", "결과는")
    .replaceAll("판정을", "결과를")
    .replaceAll("판정의", "결과의")
    .replaceAll("판정", "결과")
    .replace(/강해 보$/g, "강하게 보입니다")
    .replace(/약해 보$/g, "약하게 보입니다");
}

function renderPremiumVisualDashboard(report, sections) {
  const personality = premiumFindSection(sections, "personality");
  const surface = premiumSurfaceSection(report, "visual_dashboard");
  return `
    <section class="premium-visual-dashboard" aria-label="프리미엄 운세 시각 자료">
      <div class="premium-section-title is-tight">
        <p class="eyebrow">${escapeHtml(surface.eyebrow || "종합 보드")}</p>
        <h2>${escapeHtml(surface.title || "성격 기준과 운세 지표를 분리해 표시합니다.")}</h2>
        ${surface.body ? `<p>${escapeHtml(surface.body)}</p>` : ""}
      </div>
      <div class="premium-visual-grid">
        ${renderPremiumPersonalityVisual(personality)}
        ${renderPremiumMetricBoard(report, sections)}
      </div>
    </section>
  `;
}

function renderPremiumLifeArc(report, sections) {
  const timing = premiumFindSection(sections, "timing");
  const arcSections = ["life", "honor", "social"].map((domain) => premiumFindSection(sections, domain)).filter(Boolean);
  if (!timing && !arcSections.length) {
    return "";
  }
  const surface = premiumSurfaceSection(report, "life_arc");
  const arcTitle =
    cleanPremiumDisplayText(surface.title || "") ||
    "생애 구간마다 강해지는 운의 종류가 다릅니다.";
  const arcBody =
    cleanPremiumDisplayText(surface.body || "") ||
    "주요 연도, 생애 구간, 명예운과 대인관계운을 한 화면에서 정리합니다.";
  return `
    <section class="premium-life-arc" aria-label="인생 구간과 사회적 확장">
      <div class="premium-section-title">
        <p class="eyebrow">${escapeHtml(surface.eyebrow || "인생 구간")}</p>
        <h2>${escapeHtml(arcTitle)}</h2>
        <p>${escapeHtml(arcBody)}</p>
      </div>
      <div class="premium-life-arc-stack">
        ${timing ? renderPremiumTimingProductBoard(report, timing) : ""}
        ${renderPremiumLifeSummaryRail(arcSections)}
        ${renderPremiumLifeDossier(arcSections)}
      </div>
    </section>
  `;
}

function renderPremiumLowerDrawer(title, caption, content) {
  const safeContent = String(content || "").trim();
  if (!safeContent) {
    return "";
  }
  return `
    <details class="premium-lower-drawer">
      <summary>
        <span>${escapeHtml(title)}</span>
        ${caption ? `<em>${escapeHtml(caption)}</em>` : ""}
      </summary>
      <div class="premium-lower-drawer-body">
        ${safeContent}
      </div>
    </details>
  `;
}

function renderPremiumLifeSummaryRail(sections) {
  const cards = (sections || [])
    .map(premiumLifeDossierCard)
    .filter(Boolean);
  if (!cards.length) {
    return "";
  }
  return `
    <section class="premium-life-summary-rail" aria-label="생애 핵심 결과">
      ${cards.map(renderPremiumLifeSummaryCard).join("")}
    </section>
  `;
}

function renderPremiumLifeSummaryCard(card) {
  const strong = premiumLifeDisplayLabel(card?.strong?.label || card?.insights?.find((item) => item?.tone !== "watch")?.value || "");
  const watch = premiumLifeDisplayLabel(card?.watch?.label || card?.insights?.find((item) => item?.tone === "watch")?.value || "");
  const profileType = premiumLifeDisplayLabel(card.profileType || firstSentences(card.verdict || "", 1).replace(/\.$/, ""));
  const verdict = premiumLifeDisplaySentence(card.verdict || "");
  return `
    <article class="premium-life-summary-card domain-${escapeHtml(card.domain || "default")}">
      <span>${escapeHtml(card.title)}</span>
      <strong>${escapeHtml(profileType)}</strong>
      ${verdict ? `<p>${escapeHtml(firstSentences(verdict, 1))}</p>` : ""}
      <div>
        ${strong ? `<b>${escapeHtml(strong)}</b>` : ""}
        ${watch ? `<em>${escapeHtml(watch)}</em>` : ""}
      </div>
    </article>
  `;
}

function premiumLifeDisplayLabel(value) {
  return cleanCustomerLabel(value || "")
    .replaceAll("초년 기준형", "초년 기준 확립형")
    .replaceAll("초년 기준 확립형", "초년 자기 기준 확립형")
    .replaceAll("초년 형성도", "초년 기반 형성력")
    .replaceAll("청년기의 직업 시행착오", "청년기 직업 변동")
    .replaceAll("공식 책임형", "공식 평판 책임형")
    .replaceAll("공식 평판 책임형", "책임으로 평판을 얻는 형")
    .replaceAll("공식 책임 수행력", "공식 책임 수행력")
    .replaceAll("돈 문제로 깎이는 평판", "금전 문제에 따른 평판 검증")
    .replaceAll("신뢰 누적형", "신뢰 축적형")
    .replaceAll("신뢰 축적형", "장기 신뢰형")
    .replaceAll("질투하는 경쟁자", "경쟁·시기 관계")
    .replaceAll("관계 지속력", "관계 지속력")
    .replaceAll("평판 유지력", "평판 유지력")
    .replaceAll("중년 성취도", "중년 성취력")
    .replaceAll("말년 안정도", "말년 안정력")
    .trim();
}

function premiumLifeDisplaySentence(value) {
  return cleanPremiumDisplayText(value || "")
    .replaceAll("초년 기준형", "초년 기준 확립형")
    .replaceAll("초년 기준 확립형", "초년 자기 기준 확립형")
    .replaceAll("초년 형성도", "초년 기반 형성력")
    .replaceAll("청년기의 직업 시행착오", "청년기 직업 변동")
    .replaceAll("공식 책임형", "공식 평판 책임형")
    .replaceAll("공식 평판 책임형", "책임으로 평판을 얻는 형")
    .replaceAll("돈 문제로 깎이는 평판", "금전 문제에 따른 평판 검증")
    .replaceAll("신뢰 누적형", "신뢰 축적형")
    .replaceAll("신뢰 축적형", "장기 신뢰형")
    .replaceAll("질투하는 경쟁자", "경쟁·시기 관계")
    .trim();
}

function renderPremiumLifeDossier(sections) {
  const cards = (sections || [])
    .map(premiumLifeDossierCard)
    .filter(Boolean);
  if (!cards.length) {
    return "";
  }
  return `
    <section class="premium-life-dossier" aria-label="생애 구간 종합 진단">
      <div class="premium-panel-head">
        <div>
          <span>생애 진단</span>
          <h3>인생 구간·명예·관계를 따로 정리합니다.</h3>
        </div>
        <strong>종합판</strong>
      </div>
      <div class="premium-life-dossier-grid">
        ${cards.map(renderPremiumLifeDossierCard).join("")}
      </div>
    </section>
  `;
}

function premiumLifeDossierCard(section) {
  if (!section) {
    return null;
  }
  const domain = premiumSectionDomain(section);
  const profile = section?.section_profile || {};
  const title = premiumNavTitle(section);
  const story = premiumProductStory(section);
  const storyItems = Array.isArray(story.items)
    ? story.items
        .map((item) => ({
          label: cleanCustomerLabel(item?.label || ""),
          value: cleanCustomerLabel(item?.title || ""),
          body: cleanPremiumDisplayText(item?.body || ""),
          tone: item?.role === "watch" ? "watch" : item?.role === "strong" ? "strong" : "neutral",
        }))
        .filter((item) => item.label || item.value || item.body)
    : [];
  const storyStrong = storyItems.find((item) => item.tone === "strong") || storyItems[0] || null;
  const storyWatch = storyItems.find((item) => item.tone === "watch") || null;
  const profileType = premiumLifeDisplayLabel(story.headline || profile.type || premiumSectionFocus(section));
  const verdict = premiumLifeDisplaySentence(story.lead || profile.summary || premiumSectionHeadline(section));
  const visualItems = Array.isArray(section?.visual_profile?.items) ? section.visual_profile.items : [];
  const profileItems = Array.isArray(profile.items) ? profile.items : [];
  const strong = storyStrong || premiumDossierStrongItem(visualItems, profileItems);
  const watch = storyWatch || premiumDossierWatchItem(section, visualItems, profileItems);
  const storyInsights = storyItems.filter((item) => item !== storyStrong && item !== storyWatch).slice(0, 3);
  const insights = storyInsights.length ? storyInsights : premiumLifeDossierInsights(profile, verdict);
  const metrics = premiumLifeDossierMetrics(visualItems, profileItems);
  const scenes = premiumDossierSceneItems(section);
  const basis = premiumSectionReadingBasis(section, domain);
  if (!profileType && !verdict && !strong && !watch && !insights.length && !metrics.length && !scenes.length) {
    return null;
  }
  return {
    domain,
    title,
    profileType,
    verdict,
    strong,
    watch,
    insights,
    metrics,
    scenes,
    basis,
  };
}

function premiumLifeDossierInsights(profile, verdict) {
  const summary = cleanPremiumDisplayText(verdict || "");
  return (Array.isArray(profile?.insights) ? profile.insights : [])
    .map((item) => {
      let body = cleanPremiumDisplayText(item?.body || "");
      if (body && summary.includes(body)) {
        body = "";
      }
      return {
        label: cleanCustomerLabel(item?.label || ""),
        value: cleanCustomerLabel(item?.value || ""),
        body,
        tone: item?.tone === "watch" || item?.tone === "risk" ? "watch" : item?.tone || "neutral",
      };
    })
    .filter((item) => item.label && (item.value || item.body))
    .slice(0, 4);
}

function premiumLifeDossierMetrics(visualItems, profileItems) {
  const rows = [];
  const seen = new Set();
  const push = (source) => {
    const label = cleanCustomerLabel(source?.label || source?.source_title || source?.value || "");
    const key = premiumTopicMatchKey(label);
    if (!label || (key && seen.has(key))) {
      return;
    }
    if (key) {
      seen.add(key);
    }
    const score = Number(source?.score);
    rows.push({
      label,
      value: cleanCustomerLabel(source?.value || source?.grade || premiumMetricValueFromScore(score)),
      score: Number.isFinite(score) ? score : null,
      tone: source?.tone || "",
    });
  };
  (visualItems || []).forEach(push);
  (profileItems || []).forEach(push);
  return rows
    .filter((item) => item.label && (item.value || item.score !== null))
    .slice(0, 4);
}

function premiumDossierStrongItem(visualItems, profileItems) {
  const mappedProfile = (profileItems || []).map((item, index) => ({
    label: cleanCustomerLabel(String(item?.label || "").includes("대표") ? item?.value || item?.label : item?.value || item?.label || ""),
    value: cleanCustomerLabel(item?.grade || item?.value || ""),
    body: cleanPremiumDisplayText(item?.text || item?.caption || item?.body || ""),
    score: Number.isFinite(Number(item?.score))
      ? Number(item.score)
      : String(item?.label || "").includes("대표")
        ? 101
        : item?.tone === "strong"
          ? 90
          : 50,
    tone: item?.tone || "",
    priority: index,
  }));
  const mappedVisual = (visualItems || []).map((item, index) => ({
    label: cleanCustomerLabel(item?.label || item?.source_title || item?.value || ""),
    value: cleanCustomerLabel(item?.value || item?.grade || ""),
    body: cleanPremiumDisplayText(item?.caption || item?.text || item?.body || ""),
    score: Number(item?.score),
    tone: item?.tone || "",
    priority: index + 20,
  }));
  const pool = [...mappedProfile, ...mappedVisual]
    .map((item) => ({
      label: item.label,
      value: cleanCustomerLabel(item?.value || item?.grade || ""),
      body: cleanPremiumDisplayText(item?.caption || item?.text || item?.body || ""),
      score: Number(item?.score),
      tone: item?.tone || "",
      priority: Number.isFinite(Number(item?.priority)) ? Number(item.priority) : 99,
    }))
    .filter((item) => item.label && (item.body || item.value || Number.isFinite(item.score)));
  if (!pool.length) {
    return null;
  }
  return pool.sort((a, b) => {
    const aScore = Number.isFinite(a.score) ? a.score : a.tone === "strong" ? 90 : 50;
    const bScore = Number.isFinite(b.score) ? b.score : b.tone === "strong" ? 90 : 50;
    if (aScore !== bScore) {
      return bScore - aScore;
    }
    return a.priority - b.priority;
  })[0];
}

function premiumDossierWatchItem(section, visualItems, profileItems) {
  const storyWatch = Array.isArray(section?.section_story_cards)
    ? section.section_story_cards.find(
        (card) =>
          card?.tone === "watch" ||
          card?.tone === "risk" ||
          String(card?.label || "").includes("주의") ||
          String(card?.title || "").includes("주의"),
      )
    : null;
  if (storyWatch) {
    return {
      label: cleanCustomerLabel(storyWatch.title || "주의할 자리"),
      value: "주의",
      body: cleanPremiumDisplayText(storyWatch.body || ""),
    };
  }
  const detailWatch = Array.isArray(section?.premium_details)
    ? section.premium_details.find((detail) => detail?.level === "risk" || detail?.level === "watch")
    : null;
  if (detailWatch) {
    return {
      label: cleanCustomerLabel(detailWatch.title || "주의할 자리"),
      value: "주의",
      body: cleanPremiumDisplayText(detailWatch.judgment || ""),
    };
  }
  const pool = [...(visualItems || []), ...(profileItems || [])]
    .map((item) => ({
      label: cleanCustomerLabel(item?.label || item?.source_title || item?.value || ""),
      value: cleanCustomerLabel(item?.value || item?.grade || ""),
      body: cleanPremiumDisplayText(item?.caption || item?.text || item?.body || ""),
      score: Number(item?.score),
      tone: item?.tone || "",
    }))
    .filter((item) => item.label && (item.body || item.value || Number.isFinite(item.score)));
  const watch = pool.find((item) => item.tone === "watch" || item.tone === "risk");
  if (watch) {
    return watch;
  }
  const scored = pool.filter((item) => Number.isFinite(item.score));
  return scored.length ? scored.sort((a, b) => a.score - b.score)[0] : null;
}

function premiumDossierSceneItems(section) {
  const details = Array.isArray(section?.premium_details) ? section.premium_details : [];
  const scenes = [];
  details.forEach((detail) => {
    (detail?.event_scenes || []).forEach((scene) => {
      const text = cleanPremiumDisplayText(scene || "");
      if (text && !scenes.includes(text)) {
        scenes.push(text);
      }
    });
  });
  if (!scenes.length) {
    (section?.detail_blocks || []).forEach((detail) => {
      (detail?.bullets || []).forEach((scene) => {
        const text = cleanPremiumDisplayText(scene || "");
        if (text && !scenes.includes(text)) {
          scenes.push(text);
        }
      });
    });
  }
  return scenes.slice(0, 2);
}

function renderPremiumLifeDossierCard(card) {
  const strong = card.strong;
  const watch = card.watch;
  const profileType = premiumLifeDisplayLabel(card.profileType || "핵심 진단");
  const verdict = premiumLifeDisplaySentence(card.verdict || "");
  const pointLabels = premiumLifeDossierPointLabels(card.domain);
  return `
    <article class="premium-life-dossier-card domain-${escapeHtml(card.domain || "default")}">
      <header>
        <span>${escapeHtml(card.title)}</span>
        <strong>${escapeHtml(profileType)}</strong>
      </header>
      ${verdict ? `<p class="premium-life-dossier-verdict">${escapeHtml(firstSentences(verdict, 2))}</p>` : ""}
      ${
        Array.isArray(card.basis) && card.basis.length
          ? `<div class="premium-life-dossier-basis">
              ${card.basis.slice(0, 2).map((item) => `<p>${escapeHtml(item)}</p>`).join("")}
            </div>`
          : ""
      }
      ${
        card.insights.length
          ? `<div class="premium-life-dossier-insights">
              ${card.insights.map(renderPremiumLifeDossierInsight).join("")}
            </div>`
          : ""
      }
      <div class="premium-life-dossier-points">
        ${
          strong
            ? `<section class="is-strong">
                <b>${escapeHtml(pointLabels.strong)}</b>
                <strong>${escapeHtml(premiumLifeDisplayLabel(strong.label))}</strong>
                <p>${escapeHtml(firstSentences(premiumLifeDisplaySentence(strong.body || strong.value), 1))}</p>
              </section>`
            : ""
        }
        ${
          watch
            ? `<section class="is-watch">
                <b>${escapeHtml(pointLabels.watch)}</b>
                <strong>${escapeHtml(premiumLifeDisplayLabel(watch.label))}</strong>
                <p>${escapeHtml(firstSentences(premiumLifeDisplaySentence(watch.body || watch.value), 1))}</p>
              </section>`
          : ""
      }
      </div>
      ${
        card.metrics.length
          ? `<div class="premium-life-dossier-metrics">
              ${card.metrics.map(renderPremiumLifeDossierMetric).join("")}
            </div>`
          : ""
      }
      ${
        card.scenes.length
          ? `<ul class="premium-life-dossier-scenes">
              ${card.scenes.map((scene) => `<li>${escapeHtml(scene)}</li>`).join("")}
            </ul>`
          : ""
      }
    </article>
  `;
}

function premiumLifeDossierPointLabels(domain) {
  if (domain === "life") {
    return { strong: "강해지는 구간", watch: "주의 구간" };
  }
  if (domain === "honor") {
    return { strong: "인정받는 자리", watch: "평판 주의" };
  }
  if (domain === "social") {
    return { strong: "도움이 되는 관계", watch: "부담 관계" };
  }
  return { strong: "강점", watch: "주의 지점" };
}

function renderPremiumLifeDossierInsight(item) {
  const tone = item?.tone === "watch" || item?.tone === "risk" ? "watch" : item?.tone || "neutral";
  return `
    <section class="is-${escapeHtml(tone)}">
      <span>${escapeHtml(premiumLifeDisplayLabel(item?.label || ""))}</span>
      ${item?.value ? `<strong>${escapeHtml(premiumLifeDisplayLabel(item.value))}</strong>` : ""}
      ${item?.body ? `<p>${escapeHtml(firstSentences(premiumLifeDisplaySentence(item.body), 1))}</p>` : ""}
    </section>
  `;
}

function renderPremiumLifeDossierMetric(item) {
  const score = Number(item?.score);
  const width = Number.isFinite(score) ? Math.max(8, Math.min(100, Math.round(score))) : null;
  const tone = item?.tone === "watch" || item?.tone === "risk" ? "watch" : item?.tone || "neutral";
  return `
    <section class="is-${escapeHtml(tone)}">
      <div>
        <b>${escapeHtml(premiumLifeDisplayLabel(item?.label || ""))}</b>
        ${item?.value ? `<strong>${escapeHtml(premiumLifeDisplayLabel(item.value))}</strong>` : ""}
      </div>
      ${width ? `<i aria-label="지표 강도"><em style="width:${width}%"></em></i>` : ""}
    </section>
  `;
}

function renderPremiumLifeDetailScenes(detail) {
  const scenes = Array.isArray(detail?.bullets)
    ? detail.bullets.map(premiumDetailSceneText).filter(Boolean).slice(0, 2)
    : [];
  if (!scenes.length) {
    return "";
  }
  return `
    <ul class="premium-life-detail-scenes">
      ${scenes.map((scene) => `<li>${escapeHtml(scene)}</li>`).join("")}
    </ul>
  `;
}

function premiumDetailSceneText(value) {
  const text = cleanPremiumDisplayText(value || "");
  if (!text) {
    return "";
  }
  if (/^[가-힣A-Za-z0-9·\s]+:\s*(최상위권|상위권|중상위권|평균권|최상|강함|좋음|보통|주의 필요|주의|낮음|저하)$/.test(text)) {
    return "";
  }
  return text;
}

function renderPremiumLifeArcPanel(section) {
  const domain = premiumSectionDomain(section);
  const title = premiumNavTitle(section);
  const subtitle = premiumDomainSubLabel(section, title);
  const profile = section?.section_profile || {};
  const headline = cleanPremiumDisplayText(profile.summary || premiumSectionHeadline(section));
  const role = cleanPremiumDisplayText(section?.category_contract?.profile_role || "");
  const profileType = cleanCustomerLabel(profile.type || premiumSectionFocus(section));
  const details = premiumDomainDetailHighlights(section).slice(0, 3);
  return `
    <article class="premium-life-arc-card domain-${escapeHtml(domain)}">
      <header>
        <div>
          <span>${escapeHtml(subtitle)}</span>
          <h3>${escapeHtml(title)}</h3>
        </div>
        <strong>${escapeHtml(premiumDomainBadge(section))}</strong>
      </header>
      <div class="premium-life-arc-diagnosis">
        <section class="premium-life-arc-verdict">
          <span>${escapeHtml(profile?.label || "결과 유형")}</span>
          ${profileType ? `<strong>${escapeHtml(profileType)}</strong>` : ""}
          ${headline ? `<p>${escapeHtml(firstSentences(headline, 2))}</p>` : ""}
        </section>
        ${renderPremiumLifeVisualScale(section)}
      </div>
      ${role ? `<p class="premium-life-arc-role">${escapeHtml(role)}</p>` : ""}
      ${renderPremiumLifeDetailList(details)}
    </article>
  `;
}

function renderPremiumLifeDetailList(details) {
  if (!Array.isArray(details) || !details.length) {
    return "";
  }
  return `<div class="premium-life-detail-list">${details
    .map(
      (detail) => `
        <section class="${detail.level === "risk" ? "is-risk" : detail.level === "strong" ? "is-strong" : ""}">
          <b>${escapeHtml(detail.title)}</b>
          <span>${escapeHtml(firstSentences(detail.body, 2))}</span>
          ${renderPremiumLifeDetailScenes(detail)}
        </section>
      `,
    )
    .join("")}</div>`;
}

function renderPremiumLifeVisualScale(section) {
  const profile = section?.visual_profile || {};
  const items = Array.isArray(profile.items)
    ? profile.items
        .map((item) => ({
          label: cleanCustomerLabel(item?.label || item?.source_title || ""),
          value: cleanCustomerLabel(item?.value || ""),
          caption: cleanPremiumDisplayText(item?.caption || ""),
          score: Number(item?.score),
          tone: item?.tone || "",
        }))
        .filter((item) => item.label && Number.isFinite(item.score))
        .slice(0, 4)
    : [];
  if (!items.length) {
    return "";
  }
  return `
    <section class="premium-life-scale-list" aria-label="구간별 강약 지표">
      ${items
        .map((item) => {
          const width = Math.max(8, Math.min(100, Math.round(item.score)));
          const toneClass = item.tone === "watch" || item.tone === "risk" ? " is-risk" : item.score >= 76 ? " is-strong" : "";
          return `
            <article class="${toneClass}">
              <header>
                <span>${escapeHtml(item.label)}</span>
                <strong>${escapeHtml(item.value || `${Math.round(item.score)}점`)}</strong>
              </header>
              <div class="premium-life-scale-bar" aria-hidden="true">
                <i style="width:${width}%"></i>
              </div>
              ${item.caption ? `<p>${escapeHtml(firstSentences(item.caption, 1))}</p>` : ""}
            </article>
          `;
        })
        .join("")}
    </section>
  `;
}

function renderPremiumLifeSignalStrip(units) {
  const items = units
    .map((unit) => ({
      label: cleanCustomerLabel(unit.display_label || unit.label || ""),
      value: cleanCustomerLabel(unit.value || ""),
      result: cleanPremiumDisplayText(unit.result || unit.focus || ""),
    }))
    .filter((item) => item.label && (item.value || item.result))
    .slice(0, 4);
  if (!items.length) {
    return "";
  }
  return `
    <div class="premium-life-signal-strip" aria-label="핵심 지표">
      ${items
        .map(
          (item) => `
            <span>
              <b>${escapeHtml(item.label)}</b>
              <strong>${escapeHtml(item.value || firstSentences(item.result, 1).replace(/\.$/, ""))}</strong>
            </span>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderPremiumLifeUnitList(units) {
  if (!units.length) {
    return "";
  }
  return `<div class="premium-life-unit-list">${units
    .map((unit) => {
      const result = cleanPremiumDisplayText(unit.result || unit.focus || "");
      return `
        <div>
          <b>${escapeHtml(cleanCustomerLabel(unit.display_label || unit.label || ""))}</b>
          <span>${escapeHtml(result)}</span>
        </div>
      `;
    })
    .join("")}</div>`;
}

function renderPremiumLifeStageStrip(units) {
  if (!units.length) {
    return "";
  }
  return `<div class="premium-life-stage-strip">${units
    .map((unit) => {
      const label = cleanCustomerLabel(unit.display_label || unit.label || "");
      const result = cleanPremiumDisplayText(unit.result || unit.focus || "");
      const value = cleanCustomerLabel(unit.value || "");
      return `
        <section>
          <span>${escapeHtml(label)}</span>
          ${value ? `<strong>${escapeHtml(value)}</strong>` : ""}
          <p>${escapeHtml(result)}</p>
        </section>
      `;
    })
    .join("")}</div>`;
}

function renderPremiumLifeProfileStrip(section) {
  const profile = section?.section_profile || {};
  const items = Array.isArray(profile.items) ? profile.items.filter((item) => item?.label && item?.value).slice(0, 2) : [];
  if (!profile.type && !profile.summary && !items.length) {
    return "";
  }
  return `
    <section class="premium-life-profile-strip" aria-label="핵심 유형">
      <div>
        <span>${escapeHtml(cleanCustomerLabel(profile.label || "핵심 유형"))}</span>
        ${profile.type ? `<strong>${escapeHtml(cleanCustomerLabel(profile.type))}</strong>` : ""}
      </div>
      ${profile.summary ? `<p>${escapeHtml(cleanPremiumDisplayText(profile.summary))}</p>` : ""}
      ${
        items.length
          ? `<ul>${items
              .map(
                (item) => `
                  <li>
                    <b>${escapeHtml(cleanCustomerLabel(item.label || ""))}</b>
                    <em>${escapeHtml(cleanCustomerLabel(item.value || ""))}</em>
                  </li>
                `,
              )
              .join("")}</ul>`
          : ""
      }
    </section>
  `;
}

function renderPremiumPersonalityVisual(section) {
  const axes = personalityAxisScores(section);
  const points = radarPolygonPoints(axes.map((axis) => axis.score));
  const checkpoints = section?.checkpoints || [];
  const conclusion = premiumCheckpointValue(checkpoints, "성격 결론") || premiumSectionHeadline(section || {});
  const basis = premiumCheckpointValue(checkpoints, "판단 기준") || premiumCheckpointValue(checkpoints, "삶의 기준") || "판단 기준";
  const pressure = premiumCheckpointValue(checkpoints, "압박 대응") || premiumCheckpointValue(checkpoints, "압박을 받을 때") || premiumCheckpointValue(checkpoints, "주의할 성격") || "압박 대응 확인";
  return `
    <section class="premium-radar-panel">
      <div class="premium-panel-head">
        <div>
          <span>성격 지표</span>
          <h3>성격 핵심</h3>
        </div>
        <strong>시각 자료</strong>
      </div>
      <div class="premium-radar-layout">
        <svg class="premium-radar" viewBox="0 0 420 340" role="img" aria-label="성격 지표 차트">
          <polygon class="radar-ring" points="210,38 352,120 352,284 210,366 68,284 68,120" transform="translate(0 -38) scale(1 .88) translate(0 24)" />
          <polygon class="radar-ring" points="210,82 314,142 314,262 210,322 106,262 106,142" transform="translate(0 -31) scale(1 .88) translate(0 24)" />
          <polygon class="radar-ring" points="210,126 276,164 276,240 210,278 144,240 144,164" transform="translate(0 -24) scale(1 .88) translate(0 24)" />
          <line class="radar-axis" x1="210" y1="170" x2="210" y2="36" />
          <line class="radar-axis" x1="210" y1="170" x2="352" y2="88" />
          <line class="radar-axis" x1="210" y1="170" x2="352" y2="252" />
          <line class="radar-axis" x1="210" y1="170" x2="210" y2="306" />
          <line class="radar-axis" x1="210" y1="170" x2="68" y2="252" />
          <line class="radar-axis" x1="210" y1="170" x2="68" y2="88" />
          <polygon class="radar-shape" points="${escapeHtml(points)}" />
          ${radarPointCircles(points)}
          ${axes
            .map(
              (axis) => `
                <text x="${axis.x}" y="${axis.y}" text-anchor="${axis.anchor}">${escapeHtml(axis.label)}</text>
              `,
            )
            .join("")}
        </svg>
        <div class="premium-personality-copy">
          <strong>${escapeHtml(cleanPremiumDisplayText(conclusion))}</strong>
          <span>${escapeHtml(cleanPremiumDisplayText(basis))}</span>
          <p>${escapeHtml(cleanPremiumDisplayText(pressure))}</p>
        </div>
      </div>
    </section>
  `;
}

function premiumPersonalityBasisText(value) {
  return String(value || "")
    .split(">")
    .map((item) => cleanCustomerLabel(item).trim())
    .filter(Boolean)
    .map((item) => `${item}형`)
    .join(" · ");
}

function personalityAxisScores(section) {
  const base = [
    { key: "판단 기준", label: "판단 기준", score: 58, x: 210, y: 20, anchor: "middle" },
    { key: "대인 거리감", label: "대인 조율감", score: 58, x: 378, y: 83, anchor: "start" },
    { key: "감정 반응", label: "감정 반응성", score: 58, x: 378, y: 258, anchor: "start" },
    { key: "압박 대응", label: "압박 대응력", score: 58, x: 210, y: 326, anchor: "middle" },
    { key: "행동 속도", label: "실행 속도", score: 58, x: 42, y: 258, anchor: "end" },
    { key: "관심 몰입", label: "관심 몰입도", score: 58, x: 42, y: 83, anchor: "end" },
  ];
  const units = Array.isArray(section?.category_contract?.reading_units) ? section.category_contract.reading_units : [];
  const topics = Array.isArray(section?.topic_items) ? section.topic_items : [];
  const lookup = new Map();
  units.forEach((unit) => {
    if (unit?.label) lookup.set(cleanCustomerLabel(unit.label), unit);
  });
  topics.forEach((topic) => {
    if (topic?.title) lookup.set(cleanCustomerLabel(topic.title), topic);
  });
  return base.map((axis) => {
    const item = lookup.get(axis.key) || lookup.get(axis.label);
    const rawScore = Number(item?.score);
    return {
      ...axis,
      score: Number.isFinite(rawScore) ? rawScore : axis.score,
    };
  });
}

function radarPolygonPoints(scores) {
  const centerX = 210;
  const centerY = 170;
  const radius = 132;
  return scores
    .map((score, index) => {
      const angle = -Math.PI / 2 + index * (Math.PI / 3);
      const distance = radius * (Math.max(28, Math.min(96, score)) / 100);
      const x = Math.round(centerX + Math.cos(angle) * distance);
      const y = Math.round(centerY + Math.sin(angle) * distance);
      return `${x},${y}`;
    })
    .join(" ");
}

function radarPointCircles(points) {
  return points
    .split(" ")
    .map((point) => {
      const [x, y] = point.split(",");
      return `<circle class="radar-point" cx="${escapeHtml(x)}" cy="${escapeHtml(y)}" r="4" />`;
    })
    .join("");
}

function renderPremiumMetricBoard(report, sections) {
  const rows = premiumProfileMetricRows(sections);
  const surface = premiumSurfaceSection(report, "metric_board");
  return `
    <section class="premium-metric-panel">
      <div class="premium-panel-head">
        <div>
          <span>${escapeHtml(surface.label || "운세 지표")}</span>
          <h3>${escapeHtml(surface.title || "영역별 운세 분포")}</h3>
        </div>
        <strong>${rows.length}개 항목</strong>
      </div>
      <div class="premium-metric-list">
        ${rows
          .map(
            (row) => `
              <div class="premium-metric-row ${metricToneClass(row)}">
                <div>
                  <b>${escapeHtml(row.label)}</b>
                  <span>${escapeHtml(premiumMetricNarrative(row))}</span>
                  <i><em style="width:${premiumProfileMetricWidth(row)}%"></em></i>
                </div>
                <strong>${escapeHtml(row.grade)}</strong>
              </div>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function premiumProfileMetricRows(sections) {
  const domainOrder = ["money", "career", "love", "marriage", "honor", "social", "life"];
  const rows = [];
  const seen = new Set();
  domainOrder.forEach((domain) => {
    const section = premiumFindSection(sections, domain);
    if (!section) {
      return;
    }
    premiumSectionProfileMetricCandidates(section).forEach((row) => {
      const key = `${domain}:${cleanCustomerLabel(row.label)}`;
      if (seen.has(key)) {
        return;
      }
      seen.add(key);
      rows.push(row);
    });
  });
  return rows.slice(0, 10);
}

function premiumSectionProfileMetricCandidates(section) {
  const domain = premiumSectionDomain(section);
  const domainLabel = premiumNavTitle(section);
  const visualItems = Array.isArray(section?.visual_profile?.items) ? section.visual_profile.items : [];
  const readingUnits = Array.isArray(section?.category_contract?.reading_units) ? section.category_contract.reading_units : [];
  const fromVisual = visualItems.map((item) => premiumProfileMetricRowFromSource(item, domain, domainLabel));
  const fromUnits = readingUnits.map((item) => premiumProfileMetricRowFromSource(item, domain, domainLabel));
  const rows = [...fromVisual, ...fromUnits].filter((row) => row.label && row.value);
  const priority = premiumMetricDomainPriority(domain);
  return rows
    .map((row) => ({
      ...row,
      priority: priority.indexOf(cleanCustomerLabel(row.label)),
    }))
    .sort((a, b) => {
      const aPriority = a.priority >= 0 ? a.priority : 99;
      const bPriority = b.priority >= 0 ? b.priority : 99;
      if (aPriority !== bPriority) {
        return aPriority - bPriority;
      }
      return Number(b.score || 0) - Number(a.score || 0);
    })
    .slice(0, domain === "money" || domain === "career" ? 3 : 2);
}

function premiumProfileMetricRowFromSource(source, domain, domainLabel) {
  const label = cleanCustomerLabel(source?.display_label || source?.label || source?.title || "");
  const rawValue = cleanCustomerLabel(source?.value || "");
  const score = Number(source?.score);
  const value = rawValue || premiumMetricValueFromScore(score);
  const caption = cleanCustomerSentence(source?.caption || source?.body || source?.result || source?.focus || "");
  return {
    domain,
    domainLabel,
    label,
    value: premiumDisplayPoint(value),
    grade: premiumMetricGradeFromValue(value, score),
    caption,
    tone: source?.tone || "",
    score: Number.isFinite(score) ? score : null,
  };
}

function premiumMetricNarrative(row) {
  const domain = row?.domain || "";
  const label = cleanCustomerLabel(row?.label || "");
  const score = Number(row?.score);
  const isWeak = Number.isFinite(score) ? score < 56 : /주의|낮음|약세/.test(`${row?.grade || ""} ${row?.value || ""}`);
  if (domain === "money") {
    if (label.includes("재물 발생") || label.includes("재물 형성")) return "금전 기회가 실제 거래와 수입으로 연결됩니다.";
    if (label.includes("수입") || label.includes("수익 전환")) return "성과가 금액으로 환산됩니다.";
    if (label.includes("축재") || label.includes("자산 축적")) return "수입을 권리와 소유가 남는 자산으로 굳힙니다.";
    if (label.includes("공동") || label.includes("공동재")) {
      return isWeak ? "공동 자금에서는 명의와 지분이 불리하게 기울기 쉽습니다." : "공동 자금도 명의와 지분이 분명하면 안정적으로 관리됩니다.";
    }
    if (label.includes("계약") || label.includes("문서")) return "계약과 명의가 분명할수록 받을 돈이 안정됩니다.";
  }
  if (domain === "career") {
    if (label.includes("성취") || label.includes("성과 구현")) return "성과가 기록되는 업무에서 경력 가치가 올라갑니다.";
    if (label.includes("평가") || label.includes("평가 확보")) return "성과가 직함과 공식 평가로 연결됩니다.";
    if (label.includes("전문") || label.includes("전문성 축적")) return "전문 분야에서 단가와 협상력이 생깁니다.";
    if (label.includes("조직") || label.includes("조직 적응")) return "조직 안에서 맡을 역할이 분명해집니다.";
    if (label.includes("권한") || label.includes("책임")) return "책임과 결정권이 함께 올 때 직업운이 강해집니다.";
  }
  if (domain === "love" || domain === "marriage") {
    if (label.includes("인연") || label.includes("호감 형성")) return "소개와 반복 접점이 실제 만남으로 이어집니다.";
    if (label.includes("표현")) return isWeak ? "마음이 있어도 표현이 늦어져 상대가 거리감을 느낍니다." : "마음이 말과 행동으로 분명하게 드러납니다.";
    if (label.includes("관계 안정") || label.includes("관계 지속") || label.includes("결혼 안정")) return "한 번 깊어진 관계를 오래 유지합니다.";
    if (label.includes("결혼 현실")) return "연애가 약속과 생활 문제까지 넘어갑니다.";
    if (label.includes("생활")) return "재정, 주거, 가족 문제를 현실적으로 맞춰갑니다.";
    if (label.includes("가족 책임")) return "배우자와 가족 문제 앞에서 책임을 피하지 않습니다.";
    if (label.includes("결정 지속")) return "한 번 정한 관계를 쉽게 바꾸지 않습니다.";
  }
  if (domain === "honor") {
    if (label.includes("인정")) return "공식 평가가 따라옵니다.";
    if (label.includes("평판")) return "얻은 신뢰가 쉽게 꺾이지 않습니다.";
    if (label.includes("공식")) return "책임 있는 이름을 맡게 됩니다.";
  }
  if (domain === "social") {
    if (label.includes("사람") || label.includes("인맥")) return "필요한 사람을 알아보는 감각이 좋습니다.";
    if (label.includes("도움") || label.includes("조력자")) return "실질적인 지원을 하는 조력자를 얻습니다.";
    if (label.includes("관계 지속")) return "오래 가는 신뢰 관계가 생깁니다.";
    if (label.includes("책임 경계")) return "부탁과 책임이 섞이는 관계에서는 선을 분명히 해야 합니다.";
  }
  if (domain === "life") {
    if (label.includes("초년")) return "초년부터 성격과 생활 기준이 일찍 자리 잡습니다.";
    if (label.includes("중년")) return "중년에는 직업 성취와 재물 기반이 실제 이력으로 남습니다.";
    if (label.includes("말년")) return "말년에는 자산 유지가 남습니다.";
  }
  return row?.caption || row?.value || "세부 내용이 확인됩니다.";
}

function premiumMetricDomainPriority(domain) {
  const priorities = {
    money: ["재물 형성력", "재물 규모 확장력", "수입 창출력", "재주 수익화", "성과 보상력", "자금 운용 안정성", "자산화 능력", "투자·거래 판단력", "계약·명의 안정성", "채권·미수금 회수력", "공동자금 운영력", "부채·보증 관리력", "가족재산 경계력", "사업 확장성", "재정 방어력", "후반 축재력", "금전 기준성", "재물 강세 연도", "재물 주의 연도"],
    career: ["직업 적성", "직업 분야", "성취 축적력", "평가·명예 전환력", "승진·직함 가능성", "사회적 도약성", "권한 확보력", "책임·권한 균형", "보상 협상력", "전문 자산화", "조직 적응력", "소속 전환력", "독립 가능성", "업무 조건 감별력", "직업 전환 연도"],
    love: ["끌림의 기준", "상대 선택력", "상대 신뢰 감별력", "인연 형성력", "관계 진전력", "관계 주도권", "관계 속도 조절력", "애정 표현성", "정서 수용력", "관계 지속력", "연락·거리 안정성", "오해 조정력", "갈등 관리력", "주변 개입 관리력", "재회 가능성", "결혼 연결력"],
    marriage: ["혼인 성향", "배우자상", "결혼 적기", "결혼 현실화력", "생활 안정", "주거·생활 설계력", "가정 운영력", "부부 재정", "생활비 기준성", "부부 갈등 조정력", "부부 갈등 회복성", "가족 책임 경계력", "배우자 가족 경계", "자녀·양육 책임", "배우자 복", "혼인 위기 대응력", "결혼 지속력"],
    timing: ["대운 구간", "세운 사건", "상승 연도", "수입 강세 연도", "재물 강세 연도", "자산화 연도", "채권·미수금 회수 연도", "공동자금 주의 연도", "계약·명의 주의 연도", "부채·보증 주의 연도", "가족재산 주의 연도", "재물 주의 연도", "직업 상승 연도", "권한 상승 연도", "보상 상승 연도", "직업 분야 전환 연도", "직업 전환 연도", "소속 변화 연도", "직업 부담 연도", "직업 독립 연도", "연애 강세 연도", "새 인연 연도", "관계 진전 연도", "재회·정리 연도", "이별·정리 연도", "관계 주의 연도", "주변 개입 주의 연도", "혼인 결정 연도", "주거·생활 준비 연도", "부부 재정 연도", "가족·주거 변동 연도", "자녀·양육 책임 연도", "결혼 주의 연도", "인생 전환 연도", "주의 연도", "회복 연도", "말년 안정 연도"],
    honor: ["공적 인정 기반", "평판이 오래 남는 힘", "공식 책임을 맡는 힘", "명예를 지켜내는 기준", "직책 상승력", "권한 기반 평판", "사회적 인정이 붙는 자리", "사회적 인정도", "평판 지속력", "공식 책임 수행력", "공식 역할 수용력", "명예 관리력", "평판 유지력"],
    social: ["사람을 얻는 힘", "도움으로 이어지는 인연", "관계가 오래 남는 힘", "부탁과 책임의 경계", "인맥 형성력", "조력자 인연", "관계 지속력", "책임 경계력", "사람을 얻는 방식", "도움이 되는 사람"],
    life: ["중년에 굳어지는 성취", "중년에 커지는 성취", "말년에 남는 안정", "초년에 형성되는 바탕", "운이 바뀌는 전환기", "중년 성취도", "말년 안정도", "초년 형성도", "전환기 대응력", "중년기", "말년기", "초년·청년기"],
  };
  return priorities[domain] || [];
}

function premiumMetricValueFromScore(score) {
  if (!Number.isFinite(score)) {
    return "";
  }
  if (score >= 90) return "최상위권";
  if (score >= 80) return "상위권";
  if (score >= 68) return "중상위권";
  if (score >= 55) return "평균권";
  return "주의 필요";
}

function premiumMetricGradeFromValue(value, score = null) {
  const text = String(value || "");
  if (Number.isFinite(score)) {
    if (score >= 90) return "매우 강함";
    if (score >= 80) return "강함";
    if (score >= 68) return "양호";
    if (score >= 55) return "보통";
    return "주의";
  }
  if (/최상/.test(text)) return "매우 강함";
  if (/상위|강함|안정/.test(text)) return "강함";
  if (/중상|좋음/.test(text)) return "양호";
  if (/평균|보통/.test(text)) return "보통";
  if (/보완|약세|낮음|주의/.test(text)) return "주의";
  return "확인";
}

function premiumProfileMetricWidth(row) {
  if (Number.isFinite(Number(row?.score))) {
    return Math.max(26, Math.min(96, Number(row.score)));
  }
  const text = `${row?.grade || ""} ${row?.value || ""}`;
  if (/최상/.test(text)) return 94;
  if (/강함|상위/.test(text)) return 84;
  if (/좋음|중상/.test(text)) return 74;
  if (/보통|평균/.test(text)) return 56;
  if (/보완|약세|낮음|주의/.test(text)) return 34;
  return 62;
}

function metricToneClass(row) {
  if (/보완|낮음|주의/.test(`${row.grade} ${row.value}`)) {
    return "is-risk";
  }
  if (/최상|강함|상위권/.test(`${row.grade} ${row.value}`)) {
    return "is-strong";
  }
  return "";
}

function renderPremiumTimingProductBoard(report, section) {
  const events = Array.isArray(section?.timing_events) ? section.timing_events : [];
  const groups = Array.isArray(section?.timing_decades) ? section.timing_decades : [];
  const map = section?.timing_map || {};
  const profile = section?.timing_profile || {};
  const goodEvents = Array.isArray(map.goodHighlights) && map.goodHighlights.length
    ? map.goodHighlights
    : events.filter((event) => event.kind === "good").slice(0, 3);
  const cautionEvents = Array.isArray(map.cautionHighlights) && map.cautionHighlights.length
    ? map.cautionHighlights
    : events.filter((event) => event.kind === "caution").slice(0, 3);
  if (!goodEvents.length && !cautionEvents.length && !groups.length) {
    return renderPremiumTimingVisual(report, section);
  }
  const headline = "대운·세운 핵심";
  const lead = cleanPremiumDisplayText(premiumTimingProductLead(profile, map, goodEvents[0], cautionEvents[0]));
  const domainRows = premiumTimingDomainRows(events, goodEvents, cautionEvents);
  return `
    <section class="premium-year-product-board is-life-year-board is-timing-rebuild" aria-label="대운과 세운 핵심">
      <div class="premium-panel-head">
        <div>
          <span>생애 주요 연도</span>
          <h3>${escapeHtml(headline)}</h3>
        </div>
        <strong>${escapeHtml(profile.range || map.rangeLabel || "20세~79세")}</strong>
      </div>
      ${lead ? `<p class="premium-year-lead">${escapeHtml(lead)}</p>` : ""}
      ${renderPremiumTimingFlowSummary(profile, map)}
      ${renderPremiumTimingAgeBandScroller(groups)}
      ${renderPremiumTimingDomainBoard(domainRows)}
      ${renderPremiumTimingMajorList(goodEvents, cautionEvents)}
      ${renderPremiumTimingFullTableDrawer(groups)}
    </section>
  `;
}

function premiumTimingProductLead(profile, map, goodEvent = null, cautionEvent = null) {
  const range = cleanCustomerLabel(profile?.range || map?.rangeLabel || "20세~79세");
  const goodFocus = cleanCustomerLabel(profile?.goodFocus || map?.goodDomains || "");
  const cautionFocus = cleanCustomerLabel(profile?.cautionFocus || map?.cautionDomains || "");
  if (goodFocus && cautionFocus && goodFocus === cautionFocus) {
    return `${range} 전체에서 ${goodFocus}이 가장 크게 움직입니다. 좋은 해에는 역할과 성과가 살아나고, 주의 해에는 책임과 권한 문제가 먼저 드러납니다.`;
  }
  if (goodFocus || cautionFocus) {
    const goodText = goodFocus ? `상승은 ${goodFocus}` : "상승 연도";
    const cautionText = cautionFocus ? `주의는 ${cautionFocus}` : "주의 연도";
    return `${range} 전체를 ${goodText}, ${cautionText} 중심으로 나눴습니다. 아래에서는 연령대별로 강한 해와 관리해야 할 해를 함께 표시합니다.`;
  }
  const good = goodEvent ? `${goodEvent.year}년 ${timingEventMainTitle(goodEvent)}` : "";
  const caution = cautionEvent ? `${cautionEvent.year}년 ${timingEventMainTitle(cautionEvent)}` : "";
  if (good && caution) {
    return `${range} 전체에서 상승과 주의가 함께 잡힙니다. 대표 상승은 ${good}, 대표 주의는 ${caution}입니다.`;
  }
  if (good) {
    return `${range} 기준입니다. 상승이 가장 선명한 해는 ${good}입니다.`;
  }
  if (caution) {
    return `${range} 기준입니다. 주의가 가장 강한 해는 ${caution}입니다.`;
  }
  return map?.boardLeadShort || `${range} 기준으로 분야별 주요 연도를 나눴습니다.`;
}

function renderPremiumTimingMajorList(goodEvents, cautionEvents) {
  const good = (Array.isArray(goodEvents) ? goodEvents : []).filter((event) => event?.year).slice(0, 4);
  const caution = (Array.isArray(cautionEvents) ? cautionEvents : []).filter((event) => event?.year).slice(0, 4);
  if (!good.length && !caution.length) {
    return "";
  }
  return `
    <section class="premium-year-major-list" aria-label="대표 연도 목록">
      ${renderPremiumTimingMajorColumn("강하게 올라오는 해", good, "good")}
      ${renderPremiumTimingMajorColumn("관리해야 할 해", caution, "risk")}
    </section>
  `;
}

function renderPremiumTimingMajorColumn(title, events, tone) {
  if (!Array.isArray(events) || !events.length) {
    return "";
  }
  return `
    <article class="is-${escapeHtml(tone)}">
      <header>
        <span>${escapeHtml(title)}</span>
        <strong>${escapeHtml(`${events.length}개 연도`)}</strong>
      </header>
      <ol>
        ${events
          .map(
            (event) => `
              <li>
                <b>${escapeHtml(`${event.year}년`)}</b>
                ${event.ageLabel ? `<em>${escapeHtml(event.ageLabel)}</em>` : ""}
                <span>${escapeHtml(timingEventMainTitle(event))}</span>
              </li>
            `,
          )
          .join("")}
      </ol>
    </article>
  `;
}

function premiumTimingDomainRows(events, goodEvents = [], cautionEvents = []) {
  const sourceEvents = Array.isArray(events) && events.length ? events : [...goodEvents, ...cautionEvents];
  const domainOrder = [
    { key: "money", label: "재물" },
    { key: "career", label: "직업" },
    { key: "love", label: "연애" },
    { key: "marriage", label: "결혼" },
  ];
  return domainOrder
    .map((domain) => {
      const domainEvents = sourceEvents.filter((event) => event?.domain === domain.key);
      const good = premiumTimingBestDomainEvent(domainEvents, "good");
      const caution = premiumTimingBestDomainEvent(domainEvents, "caution");
      return { ...domain, good, caution };
    })
    .filter((row) => row.good || row.caution);
}

function premiumTimingBestDomainEvent(events, kind) {
  return (Array.isArray(events) ? events : [])
    .filter((event) => event?.kind === kind && event?.year)
    .sort((a, b) => Number(b?.score || 0) - Number(a?.score || 0))[0] || null;
}

function renderPremiumTimingDomainBoard(rows) {
  if (!Array.isArray(rows) || !rows.length) {
    return "";
  }
  return `
    <section class="premium-year-domain-board" aria-label="분야별 주요 연도">
      <header>
        <span>분야별 결과</span>
        <strong>재물·직업·연애·결혼</strong>
      </header>
      <div>
        ${rows.map(renderPremiumTimingDomainRow).join("")}
      </div>
    </section>
  `;
}

function renderPremiumTimingDomainRow(row) {
  return `
    <article class="premium-year-domain-row">
      <strong>${escapeHtml(row.label)}</strong>
      <div>
        ${renderPremiumTimingDomainEvent("상승", row.good, "good")}
        ${renderPremiumTimingDomainEvent("주의", row.caution, "risk")}
      </div>
    </article>
  `;
}

function renderPremiumTimingDomainEvent(label, event, tone) {
  if (!event || !event.year) {
    return `<span class="premium-year-domain-event is-empty"><b>${escapeHtml(label)}</b><em>해당 없음</em></span>`;
  }
  return `
    <span class="premium-year-domain-event is-${escapeHtml(tone)}">
      <b>${escapeHtml(label)}</b>
      <strong>${escapeHtml(`${event.year}년`)}</strong>
      <em>${escapeHtml(timingEventMainTitle(event))}</em>
    </span>
  `;
}

function renderPremiumTimingAgeBandScroller(groups) {
  const usableGroups = (Array.isArray(groups) ? groups : []).filter((group) => group?.good || group?.caution);
  if (!usableGroups.length) {
    return "";
  }
  return `
    <section class="premium-year-age-scroller" aria-label="연령대별 주요 연도">
      <header>
        <span>연령대별 결과</span>
        <strong>20대부터 70대까지</strong>
      </header>
      <div>
        ${usableGroups.map(renderPremiumTimingAgeBandSummary).join("")}
      </div>
    </section>
  `;
}

function renderPremiumTimingAgeBandSummary(group) {
  return `
    <article>
      <header>
        <strong>${escapeHtml(group?.label || "")}</strong>
        <span>${escapeHtml(group?.yearRange || group?.ageRange || "")}</span>
      </header>
      ${renderPremiumTimingAgeSummaryEvent("상승", group?.good, "good")}
      ${renderPremiumTimingAgeSummaryEvent("주의", group?.caution, "risk")}
    </article>
  `;
}

function renderPremiumTimingAgeSummaryEvent(label, event, tone) {
  if (!event || !event.year) {
    return "";
  }
  return `
    <p class="is-${escapeHtml(tone)}">
      <b>${escapeHtml(label)}</b>
      <strong>${escapeHtml(`${event.year}년`)}</strong>
      <em>${escapeHtml(timingEventMainTitle(event))}</em>
    </p>
  `;
}

function renderPremiumTimingSpotlightPair(goodEvent, cautionEvent) {
  if (!goodEvent && !cautionEvent) {
    return "";
  }
  return `
    <div class="premium-year-spotlight-pair" aria-label="상승 연도와 주의 연도">
      ${renderPremiumTimingSpotlightCard("상승 연도", goodEvent, "good")}
      ${renderPremiumTimingSpotlightCard("주의 연도", cautionEvent, "risk")}
    </div>
  `;
}

function renderPremiumTimingSpotlightCard(label, event, tone) {
  if (!event || !event.year) {
    return "";
  }
  const meta = [event?.ageLabel || "", event?.domainLabel || ""].filter(Boolean).join(" · ");
  return `
    <article class="premium-year-spotlight-card is-${escapeHtml(tone)}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(`${event.year}년`)}</strong>
      ${meta ? `<em>${escapeHtml(meta)}</em>` : ""}
      <b>${escapeHtml(timingEventMainTitle(event))}</b>
      ${renderTimingKeywordChips(event, 3, [timingEventMainTitle(event)])}
    </article>
  `;
}

function renderPremiumTimingFullTableDrawer(groups) {
  const board = renderPremiumTimingAgeBandBoard(groups);
  if (!board) {
    return "";
  }
  return `
    <details class="premium-lower-drawer premium-year-full-table">
      <summary>
        <span>20~70대 연도표</span>
        <em>연령대별 대표 연도를 펼쳐서 확인합니다.</em>
      </summary>
      <div class="premium-lower-drawer-body">
        ${board}
      </div>
    </details>
  `;
}

function renderPremiumTimingRankBoard(goodEvents, cautionEvents) {
  const hasGood = Array.isArray(goodEvents) && goodEvents.length;
  const hasCaution = Array.isArray(cautionEvents) && cautionEvents.length;
  if (!hasGood && !hasCaution) {
    return "";
  }
  return `
    <div class="premium-year-rank-board" aria-label="좋은 연도와 주의 연도 목록">
      ${renderPremiumTimingRankColumn("상승 연도", goodEvents, "good")}
      ${renderPremiumTimingRankColumn("주의 연도", cautionEvents, "risk")}
    </div>
  `;
}

function renderPremiumTimingRankColumn(title, events, tone) {
  if (!Array.isArray(events) || !events.length) {
    return "";
  }
  return `
    <article class="premium-year-rank-column is-${escapeHtml(tone)}">
      <header>
        <span>${escapeHtml(title)}</span>
        <strong>${escapeHtml(`${events.slice(0, 3).length}개 연도`)}</strong>
      </header>
      <div>
        ${events.slice(0, 3).map((event) => renderPremiumTimingRankEvent(event)).join("")}
      </div>
    </article>
  `;
}

function renderPremiumTimingRankEvent(event) {
  return `
    <section class="premium-year-rank-event">
      <div>
        <strong>${escapeHtml(event?.year ? `${event.year}년` : "")}</strong>
        ${event?.ageLabel ? `<span>${escapeHtml(event.ageLabel)}</span>` : ""}
      </div>
      <b>${escapeHtml(timingEventTitle(event) || timingEventMainTitle(event))}</b>
      ${renderTimingKeywordChips(event, 3)}
    </section>
  `;
}

function renderPremiumTimingAgeMap(groups) {
  const usableGroups = (Array.isArray(groups) ? groups : []).filter((group) => group?.good || group?.caution);
  if (!usableGroups.length) {
    return "";
  }
  return `
    <section class="premium-year-age-map" aria-label="20대부터 70대까지 핵심 연도">
      <header>
        <span>연령대별 핵심 연도</span>
        <strong>20세~79세</strong>
      </header>
      <div>
        ${usableGroups.map(renderPremiumTimingAgeMapNode).join("")}
      </div>
    </section>
  `;
}

function renderPremiumTimingAgeMapNode(group) {
  return `
    <article class="premium-year-age-map-node">
      <header>
        <strong>${escapeHtml(group?.label || "")}</strong>
        <span>${escapeHtml(group?.yearRange || group?.ageRange || "")}</span>
      </header>
      <div>
        ${renderPremiumTimingAgeMapEvent("좋은", group?.good, "good")}
        ${renderPremiumTimingAgeMapEvent("주의", group?.caution, "risk")}
      </div>
    </article>
  `;
}

function renderPremiumTimingAgeMapEvent(label, event, tone) {
  if (!event || !event.year) {
    return "";
  }
  return `
    <span class="premium-year-age-map-event is-${escapeHtml(tone)}">
      <b>${escapeHtml(label)}</b>
      <strong>${escapeHtml(`${event.year}년`)}</strong>
      <em>${escapeHtml(timingEventMainTitle(event))}</em>
    </span>
  `;
}

function renderPremiumTimingCommandStrip(profile, map) {
  const items = [
    { label: "상승 분야", value: profile?.goodFocus || map?.goodDomains || "" },
    { label: "경계 분야", value: profile?.cautionFocus || map?.cautionDomains || "", tone: "risk" },
    { label: "분석 범위", value: profile?.decisiveAgeBands || map?.rangeLabel || "" },
  ].filter((item) => item.value);
  if (!items.length) {
    return "";
  }
  return `
    <div class="premium-year-command-strip" aria-label="생애 연도 핵심 분야">
      ${items
        .map(
          (item) => `
            <span class="${item.tone === "risk" ? "is-risk" : ""}">
              <b>${escapeHtml(item.label)}</b>
              <strong>${escapeHtml(cleanCustomerLabel(item.value))}</strong>
            </span>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderPremiumTimingFeaturePair(goodEvent, cautionEvent) {
  if (!goodEvent && !cautionEvent) {
    return "";
  }
  return `
    <div class="premium-year-feature-pair" aria-label="상승 연도와 주의 연도">
      ${renderPremiumTimingFeatureCard("상승 연도", goodEvent, "good")}
      ${renderPremiumTimingFeatureCard("주의 연도", cautionEvent, "risk")}
    </div>
  `;
}

function renderPremiumTimingFeatureCard(label, event, tone) {
  if (!event || !event.year) {
    return "";
  }
  const meta = [event?.ageLabel || "", event?.domainLabel || ""].filter(Boolean).join(" · ");
  return `
    <article class="premium-year-feature-card is-${escapeHtml(tone)}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(`${event.year}년`)}</strong>
      ${meta ? `<em>${escapeHtml(meta)}</em>` : ""}
      <b>${escapeHtml(timingEventMainTitle(event))}</b>
      ${renderTimingKeywordChips(event, 3)}
    </article>
  `;
}

function renderPremiumTimingDecisionPair(goodEvent, cautionEvent) {
  if (!goodEvent && !cautionEvent) {
    return "";
  }
  return `
    <div class="premium-year-decision-pair" aria-label="상승 연도와 주의 연도">
      ${renderPremiumTimingDecisionCard("상승 연도", goodEvent, "good")}
      ${renderPremiumTimingDecisionCard("주의 연도", cautionEvent, "risk")}
    </div>
  `;
}

function renderPremiumTimingDecisionCard(label, event, tone) {
  if (!event || !event.year) {
    return "";
  }
  const title = timingEventTitle(event);
  return `
    <article class="premium-year-decision-card is-${escapeHtml(tone)}">
      <div>
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(`${event.year}년`)}</strong>
        ${event.ageLabel ? `<em>${escapeHtml(event.ageLabel)}</em>` : ""}
      </div>
      <b>${escapeHtml(title)}</b>
      ${renderTimingKeywordChips(event)}
    </article>
  `;
}

function renderPremiumTimingAgeBandBoard(groups) {
  const usableGroups = (Array.isArray(groups) ? groups : []).filter((group) => group?.good || group?.caution);
  if (!usableGroups.length) {
    return "";
  }
  return `
    <section class="premium-year-age-band-board" aria-label="20대부터 70대까지 연령대별 주요 연도">
      <header>
        <span>20대~70대 전체 연도표</span>
        <strong>20대~70대</strong>
      </header>
      <div>
        ${usableGroups.map(renderPremiumTimingAgeBandNode).join("")}
      </div>
    </section>
  `;
}

function renderPremiumTimingAgeBandNode(group) {
  return `
    <article class="premium-year-age-band-node">
      <header>
        <strong>${escapeHtml(group?.label || "")}</strong>
        <span>${escapeHtml(group?.yearRange || group?.ageRange || "")}</span>
      </header>
      ${renderPremiumTimingAgeBandEvent("상승 연도", group?.good, "good")}
      ${renderPremiumTimingAgeBandEvent("주의 연도", group?.caution, "risk")}
    </article>
  `;
}

function renderPremiumTimingAgeBandEvent(label, event, tone) {
  if (!event || !event.year) {
    return `<div class="premium-year-age-band-event is-empty"><span>${escapeHtml(label)}</span><strong>해당 없음</strong></div>`;
  }
  return `
    <div class="premium-year-age-band-event is-${escapeHtml(tone)}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(`${event.year}년`)}</strong>
      <b>${escapeHtml(timingEventMainTitle(event))}</b>
      ${renderTimingKeywordChips(event, 2)}
    </div>
  `;
}

function renderPremiumTimingHeroPair(goodEvent, cautionEvent) {
  if (!goodEvent && !cautionEvent) {
    return "";
  }
  return `
    <div class="premium-year-hero-pair" aria-label="상승 연도와 주의 연도">
      ${renderPremiumTimingHeroCard("상승 연도", goodEvent, "good")}
      ${renderPremiumTimingHeroCard("주의 연도", cautionEvent, "risk")}
    </div>
  `;
}

function renderPremiumTimingHeroCard(label, event, tone) {
  if (!event || !event.year) {
    return "";
  }
  return `
    <article class="premium-year-hero-card is-${escapeHtml(tone)}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(`${event.year}년`)}</strong>
      ${event.ageLabel ? `<em>${escapeHtml(event.ageLabel)}</em>` : ""}
      <b>${escapeHtml(timingEventTitle(event))}</b>
      ${event.focusLine ? `<p>${escapeHtml(cleanCustomerLabel(event.focusLine))}</p>` : ""}
      ${renderTimingKeywordChips(event)}
    </article>
  `;
}

function renderPremiumTimingKeywordColumns(goodEvents, cautionEvents) {
  if (!goodEvents.length && !cautionEvents.length) {
    return "";
  }
  return `
    <div class="premium-year-keyword-columns" aria-label="좋은 연도와 주의 연도 목록">
      ${renderPremiumTimingKeywordColumn("상승 연도", goodEvents, "good")}
      ${renderPremiumTimingKeywordColumn("주의 연도", cautionEvents, "risk")}
    </div>
  `;
}

function renderPremiumTimingKeywordDrawer(goodEvents, cautionEvents) {
  const columns = renderPremiumTimingKeywordColumns(goodEvents, cautionEvents);
  if (!columns) {
    return "";
  }
  return `
    <details class="premium-lower-drawer premium-year-keyword-drawer">
      <summary>
        <span>주요 연도 목록</span>
        <em>좋은 해와 주의할 해를 연도별로 정리했습니다.</em>
      </summary>
      <div class="premium-lower-drawer-body">
        ${columns}
      </div>
    </details>
  `;
}

function renderPremiumTimingKeywordColumn(title, events, tone) {
  if (!Array.isArray(events) || !events.length) {
    return "";
  }
  const badge = `${events.slice(0, 3).length}개 연도`;
  return `
    <article class="premium-year-keyword-column is-${escapeHtml(tone)}">
      <header>
        <span>${escapeHtml(title)}</span>
        <strong>${escapeHtml(badge)}</strong>
      </header>
      <div>
        ${events.slice(0, 3).map(renderPremiumTimingKeywordEvent).join("")}
      </div>
    </article>
  `;
}

function renderPremiumTimingKeywordEvent(event) {
  return `
    <section class="premium-year-keyword-event">
      <div>
        <strong>${escapeHtml(timingYearLine(event))}</strong>
        <b>${escapeHtml(timingEventMainTitle(event))}</b>
      </div>
      ${renderTimingKeywordChips(event)}
    </section>
  `;
}

function renderPremiumTimingFlowSummary(profile, map) {
  const items = [
    { label: "상승 분야", value: profile?.goodFocus || map?.goodDomains || "" },
    { label: "경계 분야", value: profile?.cautionFocus || map?.cautionDomains || "", tone: "risk" },
    { label: "분석 범위", value: profile?.decisiveAgeBands || map?.rangeLabel || "" },
  ].filter((item) => item.value);
  if (!items.length) {
    return "";
  }
  return `
    <div class="premium-year-flow-summary" aria-label="연도 요약">
      ${items.map(renderPremiumTimingFlowSummaryItem).join("")}
    </div>
  `;
}

function renderPremiumTimingFlowSummaryItem(item) {
  return `
    <section class="${item.tone === "risk" ? "is-risk" : ""}">
      <span>${escapeHtml(item.label)}</span>
      <strong>${escapeHtml(cleanCustomerLabel(item.value))}</strong>
    </section>
  `;
}

function renderPremiumTimingDecadeStrip(groups) {
  const usableGroups = (Array.isArray(groups) ? groups : []).filter((group) => group?.good || group?.caution);
  if (!usableGroups.length) {
    return "";
  }
  return `
    <section class="premium-year-decade-strip" aria-label="20대부터 70대까지의 연도 지도">
      <header>
        <span>20대~70대 연도 지도</span>
        <strong>20세~79세</strong>
      </header>
      <div>
        ${usableGroups.map(renderPremiumTimingDecadeNode).join("")}
      </div>
    </section>
  `;
}

function renderPremiumTimingDecadeNode(group) {
  const good = group?.good || null;
  const caution = group?.caution || null;
  const goodYear = good?.year ? `${good.year}년` : "";
  const cautionYear = caution?.year ? `${caution.year}년` : "";
  const goodTitle = cleanCustomerLabel(good?.title || good?.domainLabel || "");
  const cautionTitle = cleanCustomerLabel(caution?.title || caution?.domainLabel || "");
  return `
    <article class="premium-year-decade-node">
      <header>
        <strong>${escapeHtml(group?.label || "")}</strong>
        <span>${escapeHtml(group?.yearRange || group?.ageRange || "")}</span>
      </header>
      <div>
        ${good ? `<b class="is-good"><small>성과</small><span>${escapeHtml(goodYear)}</span><em>${escapeHtml(goodTitle)}</em></b>` : ""}
        ${caution ? `<b class="is-risk"><small>주의</small><span>${escapeHtml(cautionYear)}</span><em>${escapeHtml(cautionTitle)}</em></b>` : ""}
      </div>
    </article>
  `;
}

function renderPremiumTimingResultSheet(section) {
  const events = Array.isArray(section?.timing_events) ? section.timing_events : [];
  const map = section?.timing_map || {};
  const goodEvents = Array.isArray(map.goodHighlights) && map.goodHighlights.length
    ? map.goodHighlights
    : events.filter((event) => event.kind === "good").slice(0, 4);
  const cautionEvents = Array.isArray(map.cautionHighlights) && map.cautionHighlights.length
    ? map.cautionHighlights
    : events.filter((event) => event.kind === "caution").slice(0, 4);
  const profile = section?.timing_profile || {};
  const headline = cleanPremiumDisplayText(
    map.headline || profile.summary || section?.section_profile?.summary || section?.lead || "",
  );
  if (!goodEvents.length && !cautionEvents.length && !headline) {
    return "";
  }
  return `
    <section class="premium-timing-result-sheet" aria-label="연도 핵심 요약">
      <header>
        <span>연도 핵심 요약</span>
        <strong>${escapeHtml(profile.range || "20세~79세")}</strong>
      </header>
      ${headline ? `<p>${escapeHtml(headline)}</p>` : ""}
      <div class="premium-timing-result-grid">
        ${renderPremiumTimingResultColumn("좋은 연도", goodEvents, "good")}
        ${renderPremiumTimingResultColumn("주의 연도", cautionEvents, "risk")}
      </div>
    </section>
  `;
}

function renderPremiumTimingResultColumn(title, events, tone) {
  if (!Array.isArray(events) || !events.length) {
    return "";
  }
  return `
    <article class="premium-timing-result-column is-${escapeHtml(tone)}">
      <div>
        <span>${escapeHtml(title)}</span>
        <strong>${escapeHtml(tone === "risk" ? "주의" : "상승")}</strong>
      </div>
      ${events.slice(0, 4).map((event) => renderPremiumTimingResultEvent(event)).join("")}
    </article>
  `;
}

function renderPremiumTimingResultEvent(event) {
  return `
    <section class="premium-timing-result-event">
      <strong>${escapeHtml(timingYearLine(event))}</strong>
      <b>${escapeHtml(timingEventTitle(event) || "운세")}</b>
      ${renderTimingKeywordChips(event)}
    </section>
  `;
}

function renderPremiumTimingVisual(report, section) {
  const decadeGroups = Array.isArray(section?.timing_decades) ? section.timing_decades : [];
  if (decadeGroups.length) {
    return renderPremiumTimingDecadeMap(report, section, decadeGroups);
  }
  const events = Array.isArray(section?.timing_events) ? section.timing_events : [];
  if (events.length) {
    return renderPremiumTimingEventTable(events);
  }
  const checkpoints = Array.isArray(section?.checkpoints) ? section.checkpoints : [];
  const goodYears = premiumCheckpointValue(checkpoints, "상승 연도") || premiumCheckpointValue(checkpoints, "좋은 연도") || premiumCheckpointValue(checkpoints, "앞으로 좋은 연도");
  const cautionYears = premiumCheckpointValue(checkpoints, "주의 연도") || premiumCheckpointValue(checkpoints, "앞으로 주의 연도");
  const pastStrong = premiumCheckpointValue(checkpoints, "과거 상승 연도") || premiumCheckpointValue(checkpoints, "과거 강한 연도") || premiumCheckpointValue(checkpoints, "지나온 강한 연도");
  const pastCaution = premiumCheckpointValue(checkpoints, "과거 주의 연도") || premiumCheckpointValue(checkpoints, "지나온 주의 연도");
  const items = [
    { title: "상승 연도", value: goodYears, tone: "good" },
    { title: "주의 연도", value: cautionYears, tone: "risk" },
    { title: "과거 주요 연도", value: pastStrong, tone: "past" },
    { title: "과거 주의 연도", value: pastCaution, tone: "past-risk" },
  ].filter((item) => item.value && !/해당 없음|뚜렷한 연도 없음/.test(item.value));
  if (!items.length) {
    return "";
  }
  return `
    <section class="premium-year-panel">
      <div class="premium-panel-head">
        <div>
          <span>인생 주요 연도</span>
          <h3>인생 주요 연도</h3>
        </div>
        <strong>20세~79세 기준</strong>
      </div>
      <div class="premium-year-grid">
        ${items
          .map(
            (item) => `
              <article class="premium-year-card is-${item.tone}">
                <span>${escapeHtml(item.title)}</span>
                ${timingSplitItems(item.value)
                  .map((line) => `<strong>${escapeHtml(line)}</strong>`)
                  .join("")}
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderPremiumTimingDecadeMap(report, section, groups) {
  const events = Array.isArray(section?.timing_events) ? section.timing_events : [];
  const map = section?.timing_map || {};
  const profile = section?.timing_profile || {};
  const topGood = Array.isArray(map.goodHighlights) && map.goodHighlights.length
    ? map.goodHighlights
    : events.filter((event) => event.kind === "good").slice(0, 3);
  const topCaution = Array.isArray(map.cautionHighlights) && map.cautionHighlights.length
    ? map.cautionHighlights
    : events.filter((event) => event.kind === "caution").slice(0, 3);
  const surface = premiumSurfaceSection(report, "timing");
  return `
    <section class="premium-year-panel is-life-calendar">
      <div class="premium-panel-head">
        <div>
          <span>${escapeHtml(surface.panel_label || "인생 주요 연도")}</span>
          <h3>${escapeHtml(surface.title || "생애 주요 연도")}</h3>
        </div>
        <strong>${escapeHtml(surface.source_badge || "대운·세운")}</strong>
      </div>
      <p class="premium-year-lead">${escapeHtml(map.headline || surface.lead || "좋은 연도와 주의 연도를 나누고, 각 연도의 사건 주제를 표시합니다.")}</p>
      ${renderPremiumTimingDossier(profile, map, topGood, topCaution)}
      ${renderPremiumTimingPrimeBoard(topGood, topCaution, profile, map)}
      ${renderPremiumTimingLifeLine(groups)}
      <div class="premium-decade-timeline" aria-label="연령대별 사건표">
        <header>
          <span>연령대별 사건표</span>
          <strong>${escapeHtml(surface.decade_badge || "20대부터 70대까지")}</strong>
        </header>
        ${groups.map(renderPremiumTimingDecadeRow).join("")}
      </div>
    </section>
  `;
}

function renderPremiumTimingDossier(profile, map, goodEvents, cautionEvents) {
  const summaryCards = Array.isArray(map?.summaryCards) ? map.summaryCards.slice(0, 3) : [];
  const domainYears = Array.isArray(map?.domainYearHighlights)
    ? map.domainYearHighlights.filter((item) => item?.good || item?.caution)
    : [];
  const goodDomains = Array.isArray(profile?.goodDomainItems) ? profile.goodDomainItems.slice(0, 3) : [];
  const cautionDomains = Array.isArray(profile?.cautionDomainItems) ? profile.cautionDomainItems.slice(0, 3) : [];
  const range = profile?.range || map?.rangeLabel || "20세~79세";
  const summary = cleanPremiumDisplayText(profile?.summary || "");
  if (!summaryCards.length && !domainYears.length && !goodDomains.length && !cautionDomains.length && !summary) {
    return "";
  }
  return `
    <section class="premium-year-dossier" aria-label="연도 요약">
      <header>
        <div>
          <span>연도 요약</span>
          <strong>${escapeHtml(range)}</strong>
        </div>
        ${summary ? `<p>${escapeHtml(summary)}</p>` : ""}
      </header>
      ${
        summaryCards.length
          ? `<div class="premium-year-dossier-cards">
              ${summaryCards.map(renderPremiumTimingDossierCard).join("")}
            </div>`
          : ""
      }
      ${renderPremiumTimingDomainYearHighlights(domainYears)}
      ${
        goodDomains.length || cautionDomains.length
          ? `<div class="premium-year-dossier-domain-grid">
              ${renderPremiumTimingDomainColumn("좋은 분야", goodDomains, "good")}
              ${renderPremiumTimingDomainColumn("주의 분야", cautionDomains, "risk")}
            </div>`
          : ""
      }
    </section>
  `;
}

function renderPremiumTimingDomainYearHighlights(items) {
  if (!Array.isArray(items) || !items.length) {
    return "";
  }
  return `
    <div class="premium-year-domain-years" aria-label="영역별 대표 연도">
      <header>
        <span>영역별 대표 연도</span>
        <strong>재물·직업·연애·결혼 주요 연도</strong>
      </header>
      <div class="premium-year-domain-year-grid">
        ${items.map(renderPremiumTimingDomainYearCard).join("")}
      </div>
    </div>
  `;
}

function renderPremiumTimingDomainYearCard(item) {
  const label = cleanCustomerLabel(item?.domainLabel || "운세");
  return `
    <article class="premium-year-domain-year-card">
      <header>
        <span>${escapeHtml(label)}</span>
      </header>
      <div class="premium-year-domain-year-pair">
        ${renderPremiumTimingDomainYearCell(item?.good, "good")}
        ${renderPremiumTimingDomainYearCell(item?.caution, "risk")}
      </div>
    </article>
  `;
}

function renderPremiumTimingDomainYearCell(event, tone) {
  if (!event) {
    return "";
  }
  const year = event?.year ? `${event.year}년` : "연도 확인";
  const age = event?.age ? `${event.age}세` : "";
  const title = cleanCustomerLabel(event?.title || event?.keywords || "");
  const label = tone === "risk" ? "주의 연도" : "좋은 연도";
  const items = timingKeywordItems(event).slice(0, 3);
  return `
    <section class="is-${tone}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(age ? `${year} · ${age}` : year)}</strong>
      ${title ? `<p>${escapeHtml(title)}</p>` : ""}
      ${items.length ? `<div>${items.map((item) => `<b>${escapeHtml(cleanCustomerLabel(item))}</b>`).join("")}</div>` : ""}
    </section>
  `;
}

function renderPremiumTimingDossierCard(card) {
  const tone = card?.tone === "risk" ? "risk" : card?.tone === "good" ? "good" : "neutral";
  return `
    <article class="is-${escapeHtml(tone)}">
      <span>${escapeHtml(cleanCustomerLabel(card?.label || ""))}</span>
      ${card?.title ? `<strong>${escapeHtml(cleanCustomerLabel(card.title))}</strong>` : ""}
      ${card?.value ? `<p>${escapeHtml(cleanCustomerLabel(card.value))}</p>` : ""}
      ${card?.keywords ? renderTimingKeywordChips({ keywordItems: timingKeywordItems({ keywords: card.keywords }) }) : ""}
    </article>
  `;
}

function renderPremiumTimingDomainColumn(title, items, tone) {
  if (!Array.isArray(items) || !items.length) {
    return "";
  }
  return `
    <article class="premium-year-dossier-domain is-${escapeHtml(tone)}">
      <header>
        <span>${escapeHtml(title)}</span>
        <strong>${escapeHtml(`${items.length}개 영역`)}</strong>
      </header>
      <div>
        ${items.map((item) => renderPremiumTimingDomainItem(item, tone)).join("")}
      </div>
    </article>
  `;
}

function renderPremiumTimingDomainItem(item, tone) {
  const count = Number(item?.count);
  const average = Number(item?.averageScore);
  const width = Number.isFinite(average) ? Math.max(12, Math.min(100, Math.round(tone === "risk" ? 100 - average : average))) : null;
  const countLabel = Number.isFinite(count) ? `${count}개 연도` : "연도 확인";
  return `
    <section>
      <div>
        <b>${escapeHtml(cleanCustomerLabel(item?.label || ""))}</b>
        <strong>${escapeHtml(countLabel)}</strong>
      </div>
      ${width ? `<i aria-label="연도 집중도"><em style="width:${width}%"></em></i>` : ""}
    </section>
  `;
}

function renderPremiumTimingLifeLine(groups) {
  const usableGroups = (Array.isArray(groups) ? groups : []).filter((group) => group?.good || group?.caution);
  if (!usableGroups.length) {
    return "";
  }
  return `
    <section class="premium-year-lifeline" aria-label="생애 주요 연도">
      <header>
        <span>생애 연도</span>
        <strong>20세~79세</strong>
      </header>
      <div class="premium-year-lifeline-track">
        ${usableGroups.map(renderPremiumTimingLifeLineNode).join("")}
      </div>
    </section>
  `;
}

function renderPremiumTimingLifeLineNode(group) {
  const good = group?.good || null;
  const caution = group?.caution || null;
  return `
    <article class="premium-year-lifeline-node">
      <div>
        <strong>${escapeHtml(group?.label || "")}</strong>
        <span>${escapeHtml(group?.yearRange || group?.ageRange || "")}</span>
      </div>
      <section>
        ${good ? `<b class="is-good">${escapeHtml(good.year ? `${good.year}년` : "")}<em>${escapeHtml(cleanCustomerLabel(good.title || good.domainLabel || ""))}</em></b>` : ""}
        ${caution ? `<b class="is-risk">${escapeHtml(caution.year ? `${caution.year}년` : "")}<em>${escapeHtml(cleanCustomerLabel(caution.title || caution.domainLabel || ""))}</em></b>` : ""}
      </section>
    </article>
  `;
}

function renderPremiumTimingPrimeBoard(goodEvents, cautionEvents, profile, map) {
  const focusItems = [
    { label: "상승 분야", value: profile?.goodFocus || map?.goodDomains || "" },
    { label: "경계 분야", value: profile?.cautionFocus || map?.cautionDomains || "", tone: "risk" },
    { label: "분석 범위", value: profile?.decisiveAgeBands || map?.rangeLabel || "" },
  ].filter((item) => item.value);
  return `
    <section class="premium-year-prime-board" aria-label="좋은 연도와 주의 연도">
      <header>
        <div>
          <span>좋은 연도와 주의 연도</span>
          <strong>${escapeHtml(map?.rangeLabel || profile?.range || "20세~79세")}</strong>
        </div>
        ${focusItems.length ? `<div class="premium-year-prime-focus">${focusItems.map(renderPremiumTimingPrimeFocus).join("")}</div>` : ""}
      </header>
      <div class="premium-year-prime-columns">
        ${renderPremiumTimingPrimeColumn("상승 연도", goodEvents, "good")}
        ${renderPremiumTimingPrimeColumn("주의 연도", cautionEvents, "risk")}
      </div>
    </section>
  `;
}

function renderPremiumTimingPrimeFocus(item) {
  return `
    <span class="${item.tone === "risk" ? "is-risk" : ""}">
      <b>${escapeHtml(item.label)}</b>
      <strong>${escapeHtml(cleanCustomerLabel(item.value))}</strong>
    </span>
  `;
}

function renderPremiumTimingPrimeColumn(title, events, tone) {
  if (!Array.isArray(events) || !events.length) {
    return "";
  }
  return `
    <article class="premium-year-prime-column is-${escapeHtml(tone)}">
      <header>
        <span>${escapeHtml(title)}</span>
        <strong>${escapeHtml(events.length)}개</strong>
      </header>
      <div>
        ${events.slice(0, 3).map((event) => renderPremiumTimingPrimeEvent(event)).join("")}
      </div>
    </article>
  `;
}

function renderPremiumTimingPrimeEvent(event) {
  const meta = [event?.ageLabel || "", event?.domainLabel || ""].filter(Boolean).join(" · ");
  const source = cleanPremiumDisplayText(event?.sourcePath || event?.activationLabel || "");
  return `
    <section class="premium-year-prime-event">
      <div>
        <strong>${escapeHtml(event?.year ? `${event.year}년` : "")}</strong>
        ${meta ? `<span>${escapeHtml(meta)}</span>` : ""}
      </div>
      <section class="premium-year-prime-main">
        <b>${escapeHtml(cleanCustomerLabel(event?.title || "주요 작용"))}</b>
        ${source ? `<small>${escapeHtml(firstSentences(source, 1))}</small>` : ""}
      </section>
      ${renderTimingKeywordChips(event)}
    </section>
  `;
}

function renderPremiumTimingProfileStrip(profile) {
  const items = [
    { label: "상승 분야", value: profile?.goodFocus || "" },
    { label: "경계 분야", value: profile?.cautionFocus || "", tone: "risk" },
    { label: "분석 범위", value: profile?.decisiveAgeBands || "" },
  ].filter((item) => item.value);
  if (!items.length) {
    return "";
  }
  return `
    <div class="premium-year-profile-strip is-timing" aria-label="인생 연도 요약">
      ${items
        .map(
          (item) => `
            <span class="${item.tone === "risk" ? "is-risk" : ""}">
              <b>${escapeHtml(item.label)}</b>
              <strong>${escapeHtml(cleanCustomerLabel(item.value))}</strong>
            </span>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderPremiumTimingOutcomeBoard(goodEvents, cautionEvents) {
  if (!goodEvents.length && !cautionEvents.length) {
    return "";
  }
  return `
    <div class="premium-year-outcome-board" aria-label="좋은 연도와 주의 연도">
      ${renderPremiumTimingOutcomeColumn("상승 연도", goodEvents, "good")}
      ${renderPremiumTimingOutcomeColumn("주의 연도", cautionEvents, "risk")}
    </div>
  `;
}

function renderPremiumTimingOutcomeColumn(title, events, tone) {
  if (!events.length) {
    return "";
  }
  const badge = `${events.length}개 연도`;
  return `
    <article class="premium-year-outcome-column is-${escapeHtml(tone)}">
      <header>
        <span>${escapeHtml(title)}</span>
        <strong>${escapeHtml(badge)}</strong>
      </header>
      <div>
        ${events.map((event) => renderPremiumTimingOutcomeEvent(event)).join("")}
      </div>
    </article>
  `;
}

function renderPremiumTimingOutcomeEvent(event) {
  const year = event?.year ? `${event.year}년` : "";
  const age = event?.ageLabel || "";
  const meta = [age, event?.domainLabel || ""].filter(Boolean).join(" · ");
  return `
    <section class="premium-year-outcome-event">
      <div>
        <strong>${escapeHtml(year)}</strong>
        ${meta ? `<span>${escapeHtml(meta)}</span>` : ""}
      </div>
      <b>
        ${escapeHtml(timingEventMainTitle(event))}
      </b>
      ${renderTimingKeywordChips(event)}
    </section>
  `;
}

function renderPremiumTimingSummaryBoard(section) {
  const map = section?.timing_map || {};
  const cards = Array.isArray(map.summaryCards) ? map.summaryCards.filter((item) => item?.label && (item?.title || item?.value)) : [];
  if (!cards.length) {
    return renderPremiumTimingFocusStrip(section);
  }
  return `
    <div class="premium-year-summary-board" aria-label="생애 연도 핵심 요약">
      ${cards
        .map(
          (item) => `
            <article class="is-${escapeHtml(item.tone || "neutral")}">
              <span>${escapeHtml(cleanCustomerLabel(item.label || ""))}</span>
              ${item.title ? `<strong>${escapeHtml(cleanCustomerLabel(item.title || ""))}</strong>` : ""}
              ${item.value ? `<b>${escapeHtml(cleanCustomerLabel(item.value || ""))}</b>` : ""}
              ${item.keywords ? `<p>${escapeHtml(cleanPremiumDisplayText(item.keywords || ""))}</p>` : ""}
            </article>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderPremiumTimingFocusStrip(section) {
  const profile = section?.timing_profile || {};
  const items = [
    { label: "기회 분야", value: profile.goodFocus },
    { label: "주의 분야", value: profile.cautionFocus, tone: "risk" },
    { label: "전환 구간", value: profile.decisiveAgeBands },
  ].filter((item) => item.value);
  if (!items.length) {
    return "";
  }
  return `
    <div class="premium-year-focus-strip" aria-label="주요 연도 요약">
      ${items
        .map(
          (item) => `
            <span class="${item.tone === "risk" ? "is-risk" : ""}">
              <b>${escapeHtml(item.label)}</b>
              <strong>${escapeHtml(cleanCustomerLabel(item.value))}</strong>
            </span>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderPremiumTimingPastCheck(map) {
  const past = Array.isArray(map?.pastCheck) ? map.pastCheck.slice(0, 3) : [];
  const future = Array.isArray(map?.futureCheck) ? map.futureCheck.slice(0, 3) : [];
  const items = [
    { label: "과거 대조", events: past, tone: "past" },
    { label: "이후 주요 연도", events: future, tone: "future" },
  ].filter((item) => item.events.length);
  if (!items.length) {
    return "";
  }
  return `
    <div class="premium-year-check-board" aria-label="과거와 이후 연도 대조">
      ${items
        .map(
          (item) => `
            <section class="premium-year-check-card is-${escapeHtml(item.tone)}">
              <strong>${escapeHtml(item.label)}</strong>
              <div>
                ${item.events
                  .map(
                    (event) => `
                      <span>
                        <b>${escapeHtml(timingYearLine(event))}</b>
                        <em>${escapeHtml(timingEventTitle(event))}</em>
                      </span>
                    `,
                  )
                  .join("")}
              </div>
            </section>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderPremiumTimingProfile(section) {
  const profile = section?.timing_profile || {};
  const items = [
    { label: "좋은 분야", value: profile.goodFocus },
    { label: "주의 분야", value: profile.cautionFocus, tone: "risk" },
    { label: "확인 구간", value: profile.decisiveAgeBands },
  ].filter((item) => item.value);
  if (!items.length && !profile.summary) {
    return "";
  }
  return `
    <div class="premium-year-profile">
      ${profile.summary ? `<p>${escapeHtml(cleanPremiumDisplayText(profile.summary))}</p>` : ""}
      ${
        items.length
          ? `<div>${items
              .map(
                (item) => `
                  <span class="${item.tone === "risk" ? "is-risk" : ""}">
                    <b>${escapeHtml(item.label)}</b>
                    <strong>${escapeHtml(cleanCustomerLabel(item.value))}</strong>
                  </span>
                `,
              )
              .join("")}</div>`
          : ""
      }
    </div>
  `;
}

function renderPremiumTimingMilestoneBoard(goodEvents, cautionEvents) {
  if (!goodEvents.length && !cautionEvents.length) {
    return "";
  }
  return `
    <div class="premium-year-milestones is-calendar-board">
      ${renderPremiumTimingMilestoneColumn("좋은 연도", goodEvents, "good")}
      ${renderPremiumTimingMilestoneColumn("주의 연도", cautionEvents, "risk")}
    </div>
  `;
}

function renderPremiumTimingMilestoneColumn(title, events, tone) {
  if (!events.length) {
    return "";
  }
  return `
    <article class="premium-year-milestone-column is-${escapeHtml(tone)}">
      <span>${escapeHtml(title)}</span>
      <div>
        ${events
          .map((event) => renderPremiumTimingMilestone(event))
          .join("")}
      </div>
    </article>
  `;
}

function renderPremiumTimingMilestone(event) {
  return `
    <section class="premium-year-milestone">
      <strong>${escapeHtml(timingYearLine(event))}</strong>
      <b>${escapeHtml(timingEventTitle(event))}</b>
      ${event?.focusLine ? `<span>${escapeHtml(cleanCustomerLabel(event.focusLine))}</span>` : ""}
      ${renderTimingKeywordChips(event)}
    </section>
  `;
}

function renderPremiumTimingDecadeRow(group) {
  const good = group.good || {};
  const caution = group.caution || {};
  return `
    <article class="premium-decade-row">
      <header>
        <div>
          <span>${escapeHtml(group.label || "")}</span>
          <em>${escapeHtml(group.ageRange || "")}</em>
        </div>
        <strong>${escapeHtml(group.yearRange || "")}</strong>
      </header>
      <div class="premium-decade-row-events">
        ${renderPremiumTimingDecadeEvent("좋은 연도", good, "good")}
        ${renderPremiumTimingDecadeEvent("주의 연도", caution, "risk")}
      </div>
    </article>
  `;
}

function renderPremiumTimingDecadeEvent(label, event, tone) {
  if (!event || !event.year) {
    return "";
  }
  return `
    <div class="premium-decade-event is-${escapeHtml(tone)}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(timingYearLine(event))}</strong>
      <b>${escapeHtml(timingEventMainTitle(event))}</b>
      ${renderTimingKeywordChips(event)}
    </div>
  `;
}

function timingYearLine(event) {
  return [event?.year ? `${event.year}년` : "", event?.ageLabel || ""].filter(Boolean).join(" · ");
}

function timingEventTitle(event) {
  return [event?.domainLabel || "", event?.title || ""]
    .map((item) => cleanCustomerLabel(item))
    .filter(Boolean)
    .join(" · ");
}

function timingEventMainTitle(event) {
  return cleanCustomerLabel(event?.title || event?.domainLabel || "주요 사건");
}

function timingKeywordItems(event) {
  const rawItems = Array.isArray(event?.keywordItems) ? event.keywordItems : [];
  const fromArray = rawItems.map((item) => cleanCustomerLabel(item)).filter(Boolean);
  if (fromArray.length) {
    return fromArray.slice(0, 4);
  }
  return String(event?.keywords || event?.summary || "")
    .split(/[·,/]+/)
    .map((item) => cleanCustomerLabel(item))
    .filter(Boolean)
    .slice(0, 4);
}

function renderTimingKeywordChips(event, limit = 4, excludeValues = []) {
  const excludeKeys = new Set((Array.isArray(excludeValues) ? excludeValues : []).map(normalizedSentenceKey).filter(Boolean));
  const items = timingKeywordItems(event)
    .filter((item) => !excludeKeys.has(normalizedSentenceKey(item)))
    .slice(0, limit);
  if (!items.length) {
    return "";
  }
  return `<em class="premium-year-keywords">${items.map((item) => `<i>${escapeHtml(item)}</i>`).join(" ")}</em>`;
}

function renderPremiumTimingEventTable(events) {
  const byYear = (a, b) => Number(a.year || 0) - Number(b.year || 0);
  const groups = [
    {
      title: "좋은 연도",
      tone: "good",
      items: events.filter((event) => event.kind === "good").sort(byYear),
    },
    {
      title: "주의 연도",
      tone: "risk",
      items: events.filter((event) => event.kind === "caution").sort(byYear),
    },
  ].filter((group) => group.items.length);
  if (!groups.length) {
    return "";
  }
  return `
    <section class="premium-year-panel">
      <div class="premium-panel-head">
        <div>
          <span>인생 주요 연도</span>
          <h3>인생 주요 연도</h3>
        </div>
        <strong>20세~79세 기준</strong>
      </div>
      <div class="premium-year-columns">
        ${groups
          .map(
            (group) => `
              <article class="premium-year-column is-${group.tone}">
                <span>${escapeHtml(group.title)}</span>
                ${group.items
                  .slice(0, 3)
                  .map(
                    (event) => `
                      <div class="premium-year-event">
                        <strong>${escapeHtml([event.year ? `${event.year}년` : "", event.ageLabel || ""].filter(Boolean).join(" · "))}</strong>
                        <b>${escapeHtml(timingEventTitle(event) || "운세")}</b>
                        ${event.focusLine ? `<span>${escapeHtml(cleanCustomerLabel(event.focusLine))}</span>` : ""}
                        <em>${escapeHtml(cleanCustomerLabel(event.keywords || event.summary || ""))}</em>
                      </div>
                    `,
                  )
                  .join("")}
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function timingSplitItems(value) {
  return String(value || "")
    .split("/")
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, 3);
}

function premiumNavTitle(section) {
  const title = premiumSectionTitle(section);
  return title
    .replace("연애 세부 운세", "연애")
    .replace("결혼 세부 운세", "결혼")
    .replace("운 세부 운세", "운")
    .replace("초년·중년·말년", "인생 구간");
}

function premiumDictionaryItems(section) {
  if (!Array.isArray(section.premium_details)) {
    return [];
  }
  return section.premium_details
    .map((detail) => ({
      title: cleanCustomerLabel(detail?.title || ""),
      judgment: cleanReportCardHeadline(detail?.judgment || ""),
      scenes: Array.isArray(detail?.event_scenes)
        ? detail.event_scenes.map((scene) => cleanReportCardSummary(scene)).filter(Boolean).slice(0, 3)
        : [],
      notes: Array.isArray(detail?.premium_notes)
        ? detail.premium_notes.map((note) => cleanReportCardSummary(note)).filter(Boolean).slice(0, 2)
        : [],
      cautionTargets: Array.isArray(detail?.caution_targets)
        ? detail.caution_targets.map((target) => cleanCustomerLabel(target)).filter(Boolean).slice(0, 3)
        : [],
      level: detail?.level || "",
    }))
    .filter((detail) => detail.title && detail.judgment);
}

function premiumDetailItems(section) {
  const verdicts = premiumVerdictItems(section);
  const verdictLabels = new Set(verdicts.map((item) => cleanCustomerLabel(item.label)));
  const verdictValues = new Set(verdicts.map((item) => cleanCustomerLabel(item.value)));
  const items = [];
  premiumAxisItems(section).forEach((axis) => {
    if (!axis?.label || !axis?.value) {
      return;
    }
    items.push({
      label: cleanCustomerLabel(axis.label),
      value: cleanCustomerLabel(axis.value),
    });
  });
  const checkpoints = Array.isArray(section.checkpoints) ? section.checkpoints : [];
  checkpoints.map(parsePremiumDetailCheckpoint).forEach((item) => {
    if (item.label && item.value) {
      items.push(item);
    }
  });

  const seen = new Set();
  return items
    .filter((item) => item.label !== "주의 분야")
    .filter((item) => item.label !== "주의")
    .filter((item) => !verdictLabels.has(item.label))
    .filter((item) => !verdictValues.has(item.value))
    .filter((item) => {
      const key = `${item.label}:${item.value}`;
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    })
    .slice(0, premiumDetailLimit(section));
}

function parsePremiumDetailCheckpoint(point) {
  const text = compactPremiumPoint(point);
  if (!text) {
    return { label: "", value: "" };
  }
  const index = text.indexOf(":");
  if (index >= 0) {
    return {
      label: cleanCustomerLabel(text.slice(0, index)),
      value: cleanCustomerLabel(text.slice(index + 1).trim()),
    };
  }
  return { label: "구체적 양상", value: cleanCustomerLabel(text) };
}

function premiumDetailLimit(section) {
  const title = premiumSectionTitle(section);
  if (title === "인생 주요 연도" || section.domain === "timing") {
    return 4;
  }
  if (title === "초년·중년·말년" || section.domain === "life") {
    return 6;
  }
  return 6;
}

function premiumDetailClass(item) {
  const text = `${item.label} ${item.value}`;
  if (/주의|위험|손실|부담|충돌|변수|혼선|불균형|저하/.test(text)) {
    return "is-risk";
  }
  if (/최상위|상위|강함|강세|성취|축재|전문/.test(text)) {
    return "is-strong";
  }
  return "";
}

function premiumVerdictClass(label) {
  const text = String(label || "");
  if (/주의/.test(text)) {
    return "is-risk";
  }
  if (/대표|좋은|성격 결론|판단 기준|삶의 기준|기본 성격/.test(text)) {
    return "is-primary";
  }
  if (/세부|대인 거리감|감정 반응|압박 대응|행동 속도|관심 몰입|사람을 대하는 방식|압박을 받을 때|감정 처리|방어 반응|정서 반응|내면 반응|반복 태도/.test(text)) {
    return "is-support";
  }
  return "";
}

function premiumSectionTitle(section) {
  if (section.heading) {
    return cleanCustomerSentence(section.heading).replace(/\.$/, "");
  }
  const label = String(section.domain_label || "운세");
  const detailLabel = label !== "운세" ? label.replace(/운$/, "") : label;
  return `${detailLabel} 세부 운세`;
}

function premiumSectionHeadline(section) {
  const supplied = cleanReportCardHeadline(section.headline || section.lead || "");
  if (supplied && !/한국 나이|올해|시기입니다|해입니다/.test(supplied)) {
    return supplied;
  }
  const domain = domainKeyFromText(section.domain_label || section.heading || section.domain);
  if (domain === "money") {
    return "재물은 수입보다 귀속이 더 크게 작용합니다.";
  }
  if (domain === "career") {
    return "직업운은 성취가 직함과 평판으로 굳어지는 쪽입니다.";
  }
  if (domain === "love") {
    return "연애는 가볍게 스치는 인연보다 오래 남는 관계에 강합니다.";
  }
  if (domain === "marriage") {
    return "결혼은 감정보다 생활의 지속성에서 힘을 얻습니다.";
  }
  if (domain === "personality") {
    return "성격은 자기 기준이 분명하고 중요한 선택을 쉽게 넘기지 않는 편입니다.";
  }
  return "이 영역은 강점과 손실 지점이 뚜렷하게 나뉩니다.";
}

function premiumSectionSummary(section) {
  const source = section.narrative_paragraphs?.[0] || section.narrative || "";
  const sentences = sentenceList(cleanReportCardSummary(source))
    .filter((sentence) => !/[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]/.test(sentence))
    .filter((sentence) => !sentence.includes("기운"))
    .filter((sentence) => !sentence.includes("시기입니다"))
    .filter((sentence) => !sentence.includes("해입니다"))
    .slice(0, 2);
  if (sentences.length) {
    return sentences.join(" ");
  }
  return premiumSectionHeadline(section);
}

function percentRank(value) {
  const text = String(value || "");
  const match = text.match(/상위\s*(\d+)%/);
  if (match) return Number(match[1]);
  if (text.includes("최상위권") || text.includes("최상위")) return 10;
  if (text.includes("상위권") || text.includes("강세")) return 15;
  if (text.includes("중상위권") || text.includes("양호")) return 25;
  if (text.includes("평균권")) return 50;
  if (text.includes("보완 필요") || text.includes("주의 필요") || text.includes("평균 이하")) return 70;
  if (text.includes("약세") || text.includes("낮음")) return 85;
  return null;
}

function isRiskAxis(label, key = "", value = "") {
  const keyText = String(key || "");
  const labelText = String(label || "");
  const valueText = String(value || "");
  const weakValue = /주의|낮음|약세|보완|저하|불안/.test(valueText);
  const negativeLabel = /리스크|위험|마찰|변수|지출|손실|부담/.test(labelText);
  const managementLabel = /공동 자금|공동재|계약|문서|권한|책임|감정 조율|생활 기반/.test(labelText);
  return negativeLabel || (weakValue && (/risk|friction|authority/.test(keyText) || managementLabel));
}

function normalizedPremiumPoint(value) {
  return compactPremiumPoint(value)
    .replace(/^주의 축:\s*/, "")
    .replace(/^주의 분야:\s*/, "")
    .replace(/^주의 기준:\s*/, "")
    .replace(/^주의점:\s*/, "")
    .replace(/^주의 관계:\s*/, "")
    .replace(/^주의 선택:\s*/, "")
    .replace(/^주의할 성격:\s*/, "")
    .replace(/^주의할 부분:\s*/, "")
    .replace(/^주의:\s*/, "")
    .replace(/\.$/, "")
    .trim();
}

function premiumAxisItems(section) {
  return Array.isArray(section.judgment_axes) ? section.judgment_axes : [];
}

function premiumAxisPriority(section) {
  const title = premiumSectionTitle(section);
  const label = [section.domain_label, section.domain, title].filter(Boolean).join(" ");
  if (label.includes("재물")) {
    return ["재물 형성력", "수입 창출력", "재주 수익화", "성과 보상력", "자산화 능력", "계약·명의 안정성", "공동자금 운영력", "사업 확장성", "재정 방어력"];
  }
  if (label.includes("직업")) {
    return ["직업 적성", "직업 분야", "성취 축적력", "평가·명예 전환력", "권한 확보력", "전문 자산화", "조직 적응력", "독립 가능성", "부적합 업무 조건"];
  }
  if (label.includes("연애")) {
    return ["상대 선택력", "상대 신뢰 감별력", "인연 형성력", "관계 진전력", "관계 주도권", "애정 표현성", "관계 지속력", "연락·거리 안정성", "결혼 연결력"];
  }
  if (label.includes("결혼")) {
    return ["혼인 성향", "배우자상", "결혼 현실화력", "생활 안정", "가정 운영력", "주거·생활 설계력", "부부 재정", "가족 책임 경계력", "결혼 지속력"];
  }
  if (label.includes("명예")) {
    return ["공적 인정 기반", "성취 축적력", "평가·명예 전환력", "권한 확보력", "전문 자산화"];
  }
  if (label.includes("대인")) {
    return ["관계 지속력", "인연 형성력", "관계 경계선", "갈등 회복력", "애정 표현성"];
  }
  return [];
}

function formatPremiumAxisPoint(axis) {
  return `${cleanCustomerLabel(axis.label)} ${cleanCustomerLabel(axis.value)}`;
}

function premiumStrengthAxisCandidates(section, excluded = new Set()) {
  return premiumAxisItems(section)
    .filter((axis) => axis?.label && axis?.value && !isRiskAxis(axis.label, axis.key, axis.value))
    .map((axis) => ({ ...axis, label: cleanCustomerLabel(axis.label), value: cleanCustomerLabel(axis.value) }))
    .filter((axis) => !excluded.has(axis.label))
    .map((axis) => ({ ...axis, rank: percentRank(axis.value) }))
    .sort((a, b) => {
      const priorities = premiumAxisPriority(section);
      const aPriority = priorities.includes(a.label) ? priorities.indexOf(a.label) : 999;
      const bPriority = priorities.includes(b.label) ? priorities.indexOf(b.label) : 999;
      if (aPriority !== bPriority) {
        return aPriority - bPriority;
      }
      const aRank = a.rank ?? 999;
      const bRank = b.rank ?? 999;
      return aRank - bRank;
    });
}

function premiumStrengthFromAxes(section, excluded = new Set()) {
  const candidates = premiumStrengthAxisCandidates(section, excluded);
  const headline = premiumSectionHeadline(section);
  const headlineAxis = candidates.find((axis) => headline.includes(axis.label));
  if (headlineAxis) {
    return formatPremiumAxisPoint(headlineAxis);
  }
  const picked = candidates[0];
  return picked ? formatPremiumAxisPoint(picked) : "";
}

function premiumStrengthDetailsFromAxes(section, excluded = new Set()) {
  const candidates = premiumStrengthAxisCandidates(section, excluded)
    .filter((axis) => !/보완 필요|주의 필요|약세|낮음/.test(axis.value))
    .slice(0, 2);
  if (!candidates.length) {
    return "";
  }
  return candidates.map(formatPremiumAxisPoint).join(" · ");
}

function premiumRiskFromAxes(section) {
  const riskAxes = premiumAxisItems(section).filter((axis) => axis?.label && axis?.value && isRiskAxis(axis.label, axis.key, axis.value));
  const high = riskAxes.find((axis) => /높음|강함|주의/.test(String(axis.value)));
  const picked = high || riskAxes[0];
  return picked ? premiumRiskAxisPoint(picked) : "";
}

function premiumRiskAxisPoint(axis) {
  const label = cleanCustomerLabel(axis.label || "").replace(/(?:\s*리스크|\s*위험)$/g, "");
  const value = cleanCustomerLabel(axis.value || "");
  if (/높음|강함|주의/.test(value)) {
    if (label.includes("공동재") || label.includes("공동 자금") || label.includes("사람 문제")) {
      return "금전 관계 관리력 낮음";
    }
    if (label.includes("계약") || label.includes("문서") || label.includes("돈을 지켜내는 기준")) {
      return "계약 문서 안정성 낮음";
    }
    if (label.includes("결정권 없는 책임") || label.includes("책임·권한 불균형") || label.includes("권한·책임") || label.includes("권한과 책임")) {
      return "결정권 확보력 낮음";
    }
    if (label.includes("감정 충돌") || label.includes("감정 조율")) {
      return "감정 조율력 낮음";
    }
    if (label.includes("가족") || label.includes("주거")) {
      return "생활 기반 안정성 낮음";
    }
    return `${label} 주의`;
  }
  if (/보통/.test(value)) {
    return `${label} 보통`;
  }
  if (/약세|낮음/.test(value)) {
    return `${label} 저하`;
  }
  return value ? `${label}: ${value}` : label;
}

function premiumSectionFocus(section) {
  const axisPoint = premiumStrengthFromAxes(section);
  if (axisPoint) {
    return axisPoint;
  }
  const checkpoints = section.checkpoints || [];
  const picked = checkpoints.find((point) => !premiumRiskMarkerPattern.test(point)) || section.strategy_paragraph || section.narrative || "";
  return normalizedPremiumPoint(picked) || "운세 기준";
}

function premiumSectionRisk(section) {
  const axisPoint = premiumRiskFromAxes(section);
  if (axisPoint && !/보통|낮음/.test(axisPoint)) {
    return axisPoint;
  }
  const checkpoints = section.checkpoints || [];
  const cautionFallback = normalizedPremiumPoint(section.caution_label || "");
  const picked =
    checkpoints.find(isPremiumCautionCheckpoint) ||
    (cautionFallback ? cautionPoint(cautionFallback) : "") ||
    "";
  const normalizedPicked = normalizedPremiumPoint(picked);
  return normalizedPicked ? cautionPoint(normalizedPicked) : premiumDefaultRisk(section);
}

function isPremiumCautionCheckpoint(point) {
  const text = String(point || "");
  const label = text.split(":")[0]?.trim() || "";
  if (/갈등 회복력|관계 안정성|결혼 안정성|생활 안정성|인연 형성력|애정 표현력/.test(label)) {
    return false;
  }
  return /주의|손실|부담|맞지|말이 생깁니다|문제|불리|약함|낮음|위험|리스크|충돌/.test(text);
}

function cautionPoint(value) {
  const text = normalizedPremiumPoint(value);
  if (!text || /주의|확인|점검|조심/.test(text)) {
    return text;
  }
  if (/불균형|차이|변수|손실|충돌|압박|과중|과다|약화|장기화/.test(text)) {
    return text;
  }
  if (text.length <= 16) {
    return `${text} 주의`;
  }
  return text;
}

function premiumDefaultRisk(section) {
  const label = [section.domain_label, section.heading, section.section_id].filter(Boolean).join(" ");
  if (label.includes("명예")) {
    return "평판 관리 주의";
  }
  if (label.includes("대인")) {
    return "부탁·책임 과다 주의";
  }
  if (label.includes("시기")) {
    return "성급한 확장 주의";
  }
  if (label.includes("초년") || label.includes("중년") || label.includes("말년")) {
    return "결정 지연 주의";
  }
  if (label.includes("성향") || label.includes("성격")) {
    return "고집과 거리감 주의";
  }
  return "주의점";
}

function premiumSectionSupport(section) {
  const focus = premiumSectionFocus(section);
  const focusLabel = premiumAxisItems(section)
    .map((axis) => cleanCustomerLabel(axis?.label || ""))
    .find((label) => label && focus.includes(label));
  const axisPoint = premiumStrengthDetailsFromAxes(section, new Set(focusLabel ? [focusLabel] : []));
  if (axisPoint) {
    return axisPoint;
  }
  const risk = premiumSectionRisk(section);
  const points = (section.checkpoints || [])
    .map(normalizedPremiumPoint)
    .filter(Boolean)
    .filter((point) => point !== focus && point !== risk)
    .filter((point) => !premiumRiskMarkerPattern.test(point));
  const details = points.slice(0, 2).map(formatPremiumDetailPoint).join(" · ");
  return details || "세부 기준 확인";
}

function formatPremiumDetailPoint(value) {
  return normalizedPremiumPoint(value).replace(/^([^:]{2,16}):\s*/, "$1 ");
}

function premiumVerdictItems(section) {
  if (premiumSectionTitle(section) === "인생 주요 연도" || section.domain === "timing") {
    return timingVerdictItems(section);
  }
  if (premiumSectionTitle(section) === "성향" || premiumSectionTitle(section) === "성격" || section.domain === "personality") {
    return personalityVerdictItems(section);
  }
  const labels = premiumVerdictLabels(premiumSectionDomain(section));
  return [
    { label: labels.focus, value: premiumSectionFocus(section) },
    { label: labels.support, value: premiumSectionSupport(section) },
    { label: labels.risk, value: premiumSectionRisk(section) },
  ].filter((item) => item.value);
}

function premiumVerdictLabels(domain) {
  const labels = {
    money: {
      focus: "재물 결론",
      support: "재물 강점",
      risk: "재물 관리 지점",
    },
    career: {
      focus: "직업 결론",
      support: "직업 강점",
      risk: "경력 손실 지점",
    },
    love: {
      focus: "관계 결론",
      support: "관계 강점",
      risk: "주의 관계 기준",
    },
    marriage: {
      focus: "결혼 결론",
      support: "결혼 강점",
      risk: "결혼 관리 지점",
    },
    honor: {
      focus: "명예 결론",
      support: "명예 강점",
      risk: "명예 관리 지점",
    },
    social: {
      focus: "대인 결론",
      support: "관계 강점",
      risk: "관계 관리 지점",
    },
    life: {
      focus: "생애 결론",
      support: "강한 구간",
      risk: "주의 구간",
    },
  };
  return labels[domain] || {
    focus: "핵심 결론",
    support: "강한 기준",
    risk: "주의점",
  };
}

function timingVerdictItems(section) {
  const checkpoints = Array.isArray(section.checkpoints) ? section.checkpoints : [];
  const goodYears = premiumCheckpointValue(checkpoints, "상승 연도") || premiumCheckpointValue(checkpoints, "좋은 연도") || premiumCheckpointValue(checkpoints, "앞으로 좋은 연도");
  const cautionYears = premiumCheckpointValue(checkpoints, "주의 연도") || premiumCheckpointValue(checkpoints, "앞으로 주의 연도");
  const focus = premiumCheckpointValue(checkpoints, "대표 사건") || premiumCheckpointValue(checkpoints, "핵심");
  return [
    { label: "상승 연도", value: goodYears },
    { label: "주의 연도", value: cautionYears },
    { label: "대표 사건", value: focus },
  ].filter((item) => item.value);
}

function personalityVerdictItems(section) {
  const checkpoints = Array.isArray(section.checkpoints) ? section.checkpoints : [];
  const conclusion = premiumCheckpointValue(checkpoints, "성격 결론") || premiumCheckpointValue(checkpoints, "기본 기질") || premiumSectionFocus(section);
  const emotion = premiumCheckpointValue(checkpoints, "감정 반응") || premiumCheckpointValue(checkpoints, "감정 처리") || premiumSectionSupport(section);
  const caution = premiumCheckpointValue(checkpoints, "압박 대응") || premiumCheckpointValue(checkpoints, "주의할 성격") || premiumSectionRisk(section);
  return [
    { label: "성격 결론", value: conclusion },
    { label: "감정 반응", value: emotion },
    { label: "압박 대응", value: caution },
  ].filter((item) => item.value);
}

function premiumCheckpointValue(checkpoints, prefix) {
  const marker = `${prefix}:`;
  const found = checkpoints.find((point) => String(point || "").startsWith(marker));
  return found ? normalizedPremiumPoint(String(found).slice(marker.length)) : "";
}

function compactPremiumPoint(value) {
  const text = cleanReportCardSummary(value || "")
    .replace(/\d{4}-\d{2}-\d{2}부터\s*\d{4}-\d{2}-\d{2}까지는\s*/g, "")
    .replace(/한국 나이\s*\d+세 전후\s*/g, "")
    .replace(/상생상극 판정의 핵심은\s*/g, "")
    .replace(/주의할 부분은\s*/g, "")
    .replace(/의 전략은\s*/g, "에서 ")
    .trim();
  return firstSentences(text, 1).replace(/\.$/, "");
}

function renderFactors(report) {
  const sections = report.factor_sections || [];
  if (!sections.length) {
    panels.factors.innerHTML = `<div class="empty-state">분석에 반영한 주요 명리 요소가 준비되지 않았습니다.</div>`;
    return;
  }
  panels.factors.innerHTML = `
    <section class="section-band">
      <div class="section-title">
        <h2>분석에 반영한 주요 요소</h2>
        <p>월령, 지지, 오행, 십신 중 결과에 직접 쓰인 요소를 요약했습니다.</p>
      </div>
      <div class="factor-grid">
        ${sections.map(renderFactorSection).join("")}
      </div>
    </section>
  `;
}

function renderFactorSection(section) {
  const domainLabels = Array.isArray(section.domain_labels) ? section.domain_labels.map(cleanCustomerLabel).slice(0, 4) : [];
  return `
    <article class="factor-block">
      <p class="eyebrow">${escapeHtml(section.source_label || section.layer)}</p>
      <h3>${escapeHtml(cleanCustomerSentence(section.heading))}</h3>
      <p>${escapeHtml(firstSentences(cleanCustomerSentence(section.lead), 2))}</p>
      ${chipRow(domainLabels)}
    </article>
  `;
}

function renderJudgmentPayload(payload) {
  currentPayload = payload;
  document.body.classList.add("has-judgment");
  renderHead(payload);
  renderFreeProfilePreview(payload.report);
  renderPremiumSections(payload.report);
  renderFactors(payload.report);
  clearStatus();
}

function handleSurfaceAction(event) {
  const button = event.target.closest("button");
  if (!button) {
    return false;
  }
  if (button.dataset.scrollTarget) {
    event.preventDefault();
    setActiveView("premium", { updateHistory: false, keepScroll: true });
    window.requestAnimationFrame(() => {
      const target = document.getElementById(button.dataset.scrollTarget);
      target?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    return true;
  }
  if (button.dataset.upgrade) {
    event.preventDefault();
    applyTierSelection("premium");
    if (!currentPayload) {
      openInputEditor({ tier: "premium" });
      return true;
    }
    submitReport();
    setActiveView("premium");
    return true;
  }
  if (button.dataset.inputTarget) {
    event.preventDefault();
    openInputEditor({ tier: button.dataset.startTier });
    return true;
  }
  if (button.dataset.viewTarget) {
    event.preventDefault();
    const nextView = button.dataset.viewTarget;
    if (nextView !== "home" && !currentPayload) {
      openInputEditor({ tier: nextView === "premium" ? "premium" : tierInput.value });
      return true;
    }
    setActiveView(nextView);
    return true;
  }
  if (button.dataset.cardTarget) {
    event.preventDefault();
    const target = document.querySelector(`#${button.dataset.cardTarget}`);
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
    return true;
  }
  if (button.dataset.tabTarget) {
    event.preventDefault();
    setActiveView(button.dataset.tabTarget);
    return true;
  }
  const linkedIndex = Number(button.dataset.linkedIndex);
  if (linkedIndex) {
    event.preventDefault();
    setActiveView("judgment");
    window.requestAnimationFrame(() => {
      const target = document.querySelector(`#profile-${linkedIndex}`) || document.querySelector(`#detail-${linkedIndex}`);
      target?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    return true;
  }
  return false;
}

async function submitReport(options = {}) {
  if (isReportLoading) {
    return;
  }
  let shouldShowAffiliatePopup = false;
  setReportLoading(true);
  try {
    const payload = await requestJudgment();
    renderJudgmentPayload(payload);
    updateInputSummary();
    persistReportSession(payload);
    removeStoredValue(INPUT_EDITOR_REQUEST_KEY);
    document.body.classList.remove("input-editor-open");
    inputDisclosure?.removeAttribute("open");
    if (options.nextView) {
      setActiveView(options.nextView);
    }
    clearStatus();
    shouldShowAffiliatePopup = true;
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    stopLoadingStatus();
    setReportLoading(false);
    if (shouldShowAffiliatePopup) {
      window.requestAnimationFrame(showCoupangAffiliatePopup);
    }
  }
}

tierButtons.forEach((button) => {
  button.addEventListener("click", () => {
    applyTierSelection(button.dataset.tier);
    if (!currentPayload) {
      openInputEditor({ tier: button.dataset.tier });
      return;
    }
    submitReport({ nextView: button.dataset.tier === "premium" ? "premium" : "judgment" });
  });
});

staticActionButtons.forEach((button) => {
  button.addEventListener("click", (event) => handleSurfaceAction(event));
});

Object.values(panels).forEach((panel) => {
  panel.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) {
      return;
    }
    handleSurfaceAction(event);
  });
});

views.home.addEventListener("click", (event) => {
  handleSurfaceAction(event);
});

inputPanel.addEventListener("click", (event) => {
  handleSurfaceAction(event);
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const submitTier = event.submitter?.dataset?.submitTier;
  if (submitTier) {
    applyTierSelection(submitTier);
  }
  submitReport({ nextView: tierInput.value === "premium" ? "premium" : "judgment" });
});

window.addEventListener("popstate", () => {
  const nextView = viewFromHash();
  if (nextView !== "home" && !currentPayload) {
    window.history.replaceState({}, "", viewUrl("home"));
    setActiveView("home", { updateHistory: false, instant: true });
    openInputEditor({ tier: nextView === "premium" ? "premium" : tierInput.value });
    return;
  }
  if (nextView === "premium" && tierInput.value !== "premium") {
    applyTierSelection("premium");
    submitReport();
  }
  setActiveView(nextView, { updateHistory: false, instant: true });
});

window.addEventListener("blur", () => {
  if (affiliatePopupVisible) {
    markAffiliateDeparture();
  }
});

window.addEventListener("pagehide", () => {
  if (affiliatePopupVisible) {
    markAffiliateDeparture();
  }
});

window.addEventListener("focus", revealReportAfterCoupangReturn);

window.addEventListener("pageshow", () => {
  revealReportAfterCoupangReturn();
});

document.addEventListener("visibilitychange", () => {
  if (!document.hidden) {
    revealReportAfterCoupangReturn();
  }
});

const initialView = viewFromHash();
const initialTier = "premium";
applyTierSelection(initialTier);
renderFortuneSpotlight();
renderHomeFunnel();
clearStatus();
const shouldReturnToPremium = hasFreshAffiliateReturn();
const restoredReport = shouldReturnToPremium ? restoreReportSession() : false;
if (!shouldReturnToPremium) {
  clearAffiliateReturnState();
}
const inputEditorRequested = storedValue(INPUT_EDITOR_REQUEST_KEY) === "1";
if (restoredReport) {
  const shouldShowInputEditor = initialView === "home" && inputEditorRequested && !shouldReturnToPremium;
  if (shouldShowInputEditor) {
    setActiveView("home", { updateHistory: false, instant: true });
    openInputEditor({ tier: initialTier });
  } else {
    setActiveView(initialView === "basis" ? "basis" : "premium", { updateHistory: false, instant: true });
    clearAffiliateReturnState();
    removeStoredValue(INPUT_EDITOR_REQUEST_KEY);
  }
} else {
  setActiveView("home", { updateHistory: false, instant: true });
}
if (!restoredReport && initialView !== "home") {
  window.history.replaceState({}, "", viewUrl("home"));
  openInputEditor({ tier: initialTier });
}
document.documentElement.classList.remove("is-restoring-premium");
