const screens = [...document.querySelectorAll("[data-screen]")];
const form = document.querySelector("#birth-form");
import {
  buildDisplayAdjustment,
  displayGradeForRawGrade,
  gradeFromAverage,
  gradeFromQualityScore,
  gradeRank,
  semanticStateForGrade,
  visualPositionForGrade,
} from "./metric-display-policy.js?v=judgment-display-v43";

const reportRoot = document.querySelector("#report-root");
const detailRoot = document.querySelector("#detail-root");
const detailTitle = document.querySelector("#detail-title");
const reportTitle = document.querySelector("#report-title");
const bottomNav = document.querySelector(".bottom-nav");
const toast = document.querySelector("#toast");
const loadingFill = document.querySelector("#loading-fill");
const loadingPercent = document.querySelector("#loading-percent");
const loadingMessage = document.querySelector("#loading-message");

const state = {
  payload: null,
  detailPayload: null,
  detailToken: "",
  detailLoaded: false,
  detailLoadingPromise: null,
  activeScreen: "splash",
  activeDetail: "domains",
  loadingTimer: null,
  loadingValue: 8,
  loadingStartedAt: 0,
  loadingCeiling: 94,
  navIndex: 0,
  historyReady: false,
  metricDisplayContext: "none",
  metricDisplayAdjustments: {
    domains: buildDisplayAdjustment([]),
    year_2026: buildDisplayAdjustment([]),
    year_2027: buildDisplayAdjustment([]),
  },
};

const appHistoryKey = "saju-ihyeon-v2";
const COUPANG_PARTNERS_URL =
  window.LEEHYEON_COUPANG_PARTNERS_URL ||
  "https://link.coupang.com/re/AFFSDP?lptag=AF3151585&pageKey=8174473713&itemId=23653028364&traceid=V0-201-4d8275f22060fd79";
const COUPANG_POPUP_IFRAME_HTML =
  window.LEEHYEON_COUPANG_POPUP_IFRAME_HTML ||
  '<iframe src="https://coupa.ng/cnBqRZ" width="120" height="240" frameborder="0" scrolling="no" referrerpolicy="unsafe-url" browsingtopics></iframe>';
const REPORT_SESSION_KEY = "leehyeon:v2:lastReport";
const REPORT_SESSION_VERSION = "v2-report-v1";
const AFFILIATE_RETURN_VIEW_KEY = "leehyeon:coupangReturnView";
const AFFILIATE_LEFT_PAGE_KEY = "leehyeon:coupangPageVisited";
const AFFILIATE_LEFT_AT_KEY = "leehyeon:coupangLeftAt";
const AFFILIATE_RETURN_MAX_AGE_MS = 10 * 60 * 1000;

let affiliatePopupVisible = false;
let affiliateRestorePromise = null;
let affiliatePageWasHidden = false;

const loadingMessages = [
  "명식의 기준을 세우고 있습니다.",
  "월령과 오행의 강약을 정리하고 있습니다.",
  "격국과 십신의 작용을 대조하고 있습니다.",
  "시기운의 작용을 대조하고 있습니다.",
  "세부 지표와 근거를 함께 정리하고 있습니다.",
  "결과 화면에 맞게 정돈하고 있습니다.",
];

function storedValue(key) {
  try {
    const value = window.sessionStorage.getItem(key);
    if (value !== null) return value;
  } catch (_error) {}
  try {
    return window.localStorage.getItem(key);
  } catch (_error) {
    return null;
  }
}

function setStoredValue(key, value) {
  try {
    window.sessionStorage.setItem(key, value);
  } catch (_error) {}
  try {
    window.localStorage.setItem(key, value);
  } catch (_error) {}
}

function removeStoredValue(key) {
  try {
    window.sessionStorage.removeItem(key);
  } catch (_error) {}
  try {
    window.localStorage.removeItem(key);
  } catch (_error) {}
}

function currentNickname() {
  return String(new FormData(form).get("nickname") || "").trim();
}

function persistReportSession(initialPayload, requestPayload) {
  if (!(initialPayload && initialPayload.ok)) return;
  const record = {
    version: REPORT_SESSION_VERSION,
    savedAt: Date.now(),
    payload: initialPayload,
    request: requestPayload,
    nickname: currentNickname(),
  };
  setStoredValue(REPORT_SESSION_KEY, JSON.stringify(record));
}

function storedReportSession() {
  try {
    const raw = storedValue(REPORT_SESSION_KEY);
    if (!raw) return null;
    const record = JSON.parse(raw);
    const savedAt = Number(record && record.savedAt);
    const isFresh =
      Number.isFinite(savedAt) &&
      savedAt > 0 &&
      Date.now() - savedAt <= AFFILIATE_RETURN_MAX_AGE_MS;
    if (
      !record ||
      record.version !== REPORT_SESSION_VERSION ||
      !isFresh ||
      !(record.payload && record.payload.ok) ||
      !record.request
    ) {
      removeStoredValue(REPORT_SESSION_KEY);
      return null;
    }
    return record;
  } catch (_error) {
    removeStoredValue(REPORT_SESSION_KEY);
    return null;
  }
}

function applyStoredFormState(record) {
  const request = (record && record.request) || {};
  const nicknameInput = form.elements.namedItem("nickname");
  const birthDateInput = form.elements.namedItem("birthDate");
  const birthTimeInput = form.elements.namedItem("birthTime");
  if (nicknameInput) nicknameInput.value = String(record.nickname || "");
  if (birthDateInput) birthDateInput.value = String(request.birthDate || "");
  if (birthTimeInput) birthTimeInput.value = String(request.birthTime || "");
  form.querySelectorAll('input[name="gender"]').forEach((input) => {
    input.checked = input.value === String(request.gender || "male");
  });
}

function markAffiliateDeparture() {
  setStoredValue(AFFILIATE_RETURN_VIEW_KEY, "premium");
  setStoredValue(AFFILIATE_LEFT_PAGE_KEY, "1");
  setStoredValue(AFFILIATE_LEFT_AT_KEY, String(Date.now()));
}

function clearAffiliateReturnState() {
  removeStoredValue(AFFILIATE_RETURN_VIEW_KEY);
  removeStoredValue(AFFILIATE_LEFT_PAGE_KEY);
  removeStoredValue(AFFILIATE_LEFT_AT_KEY);
  affiliatePageWasHidden = false;
}

function hasFreshAffiliateReturn() {
  const returnView = storedValue(AFFILIATE_RETURN_VIEW_KEY);
  const pageVisited = storedValue(AFFILIATE_LEFT_PAGE_KEY);
  const leftAt = Number(storedValue(AFFILIATE_LEFT_AT_KEY) || 0);
  return Boolean(
    returnView === "premium" &&
      pageVisited === "1" &&
      Number.isFinite(leftAt) &&
      leftAt > 0 &&
      Date.now() - leftAt <= AFFILIATE_RETURN_MAX_AGE_MS,
  );
}

function closeCoupangAffiliatePopup() {
  document.querySelector(".affiliate-popup-backdrop")?.remove();
  affiliatePopupVisible = false;
}

function prepareAffiliateDeparture() {
  affiliatePageWasHidden = false;
  markAffiliateDeparture();
  closeCoupangAffiliatePopup();
  showScreen("report", { replace: true });
}

function showCoupangAffiliatePopup() {
  closeCoupangAffiliatePopup();
  affiliatePopupVisible = true;
  const backdrop = document.createElement("section");
  backdrop.className = "affiliate-popup-backdrop";
  backdrop.setAttribute("aria-label", "쿠팡 제휴 안내");
  backdrop.innerHTML = `
    <div class="affiliate-popup" role="dialog" aria-modal="true" aria-labelledby="affiliate-popup-title">
      <span class="affiliate-popup-help" aria-hidden="true">?</span>
      <h2 id="affiliate-popup-title">쿠팡 방문하기</h2>
      <p class="affiliate-popup-copy">쿠팡 페이지를 방문한 뒤 이 화면으로 돌아오면 분석 결과를 확인할 수 있습니다.</p>
      <div class="affiliate-popup-product" aria-hidden="true">${COUPANG_POPUP_IFRAME_HTML}</div>
      <strong class="affiliate-popup-visit">쿠팡 방문하기</strong>
      <p class="affiliate-popup-disclosure">쿠팡 파트너스 활동의 일환으로 일정액의 수수료를 제공받습니다.</p>
      <div class="affiliate-popup-actions">
        <a class="affiliate-popup-primary" href="${escapeHtml(COUPANG_PARTNERS_URL)}" target="_blank" rel="nofollow sponsored noopener noreferrer">쿠팡 방문하고 결과 보기</a>
      </div>
    </div>
  `;
  backdrop.querySelector(".affiliate-popup-primary")?.addEventListener("click", prepareAffiliateDeparture);
  document.body.appendChild(backdrop);
  backdrop.querySelector(".affiliate-popup-primary")?.focus();
}

async function restoreAffiliateReport() {
  if (affiliateRestorePromise) return affiliateRestorePromise;
  affiliateRestorePromise = (async () => {
    if (!hasFreshAffiliateReturn()) return false;
    const record = storedReportSession();
    if (!record) {
      clearAffiliateReturnState();
      document.documentElement.classList.remove("is-restoring-premium");
      return false;
    }
    applyStoredFormState(record);
    showScreen("loading", { skipHistory: true });
    startLoading();
    updateLoading(84, "저장된 분석 결과를 불러오고 있습니다.");
    try {
      let initialPayload = record.payload;
      let result;
      try {
        result = await hydrateInitialDetailPayload(initialPayload, record.request);
      } catch (_detailError) {
        initialPayload = await requestJudgment(record.request);
        persistReportSession(initialPayload, record.request);
        result = await hydrateInitialDetailPayload(initialPayload, record.request);
      }
      state.payload = result;
      renderReport(result);
      await finishLoading();
      showScreen("report", { replace: true });
      document.documentElement.classList.remove("is-restoring-premium");
      return true;
    } catch (error) {
      cancelLoading();
      clearAffiliateReturnState();
      document.documentElement.classList.remove("is-restoring-premium");
      showToast(error.message || "분석 결과를 다시 불러오지 못했습니다.");
      showScreen("home", { replace: true });
      return false;
    }
  })().finally(() => {
    affiliateRestorePromise = null;
  });
  return affiliateRestorePromise;
}

function revealReportAfterCoupangReturn() {
  if (!hasFreshAffiliateReturn()) return;
  if (state.payload && !affiliatePageWasHidden) return;
  if (state.payload) {
    closeCoupangAffiliatePopup();
    showScreen("report", { replace: true });
    document.documentElement.classList.remove("is-restoring-premium");
    return;
  }
  document.documentElement.classList.add("is-restoring-premium");
  void restoreAffiliateReport();
}

const tongbyeonTextReplacements = [
  ["상승 연도와 주의 연도", "좋은 시기와 조심할 시기"],
  ["상승 연도", "좋은 시기"],
  ["좋은 연도", "좋은 시기"],
  ["주의 연도", "조심할 시기"],
  ["종합 기준", "나의 본질"],
  ["격국 변주", "인생의 굴곡"],
  ["중심 작용", "중심 흐름"],
  ["영역별 적용", "영역별 근거"],
  ["종합 해석", "종합 근거"],
  ["종합 판단", "종합 근거"],
  ["격국·월령·오행 통합", "타고난 바탕과 운의 굴곡"],
  ["십신 생극", "운의 작용"],
  ["격국의 방향과 월령의 작용", "타고난 흐름"],
  ["월령의 압박과 생극의 부담", "운에서 걸리는 부담"],
  ["생극 관계", "운의 작용"],
  ["형충의 압박", "변동과 마찰"],
  ["원국", "사주"],
  ["발동 조건", "드러나는 시점"],
];

function tongbyeonSurfaceText(value) {
  let text = String(value || "").replace(/\s+/g, " ").trim();
  tongbyeonTextReplacements.forEach(([source, target]) => {
    text = text.split(source).join(target);
  });
  return text;
}

const sectionSymbols = {
  personality: "✦",
  money: "財",
  career: "官",
  love: "♡",
  marriage: "合",
  timing: "運",
  year_2026: "26",
  year_2027: "27",
  life: "年",
  honor: "名",
  social: "人",
  default: "☷",
};

const domainPickerHints = {
  personality: "성격·기질·판단",
  money: "재물 형성·자산 관리",
  career: "직업 성취·사회 활동",
  love: "연애 성향·인연 변화",
  marriage: "결혼 안정·생활 기준",
  timing: "좋은 시기·주의 시기",
  year_2026: "2026 병오년",
  year_2027: "2027 정미년",
  life: "인생 구간",
  honor: "명예·평판·공적 인정",
  social: "관계 방식·대인 영향력",
  default: "세부 항목",
};

const primaryReportDomains = ["personality", "money", "career", "love", "marriage"];

const sectionTitleAliases = {
  "재물 세부 운세": "재물운",
  "직업 세부 운세": "직업운",
  "연애 세부 운세": "연애운",
  "결혼 세부 운세": "결혼운",
  "인생 주요 연도": "시기운",
};

const detailMenu = [
  { key: "domains", title: "분야별 총운" },
  { key: "timing", title: "시기운" },
  { key: "year_2026", title: "올해운" },
  { key: "year_2027", title: "내년운" },
  { key: "gyeokguk", title: "격국 분석" },
  { key: "ten_gods", title: "십신 분석" },
  { key: "month", title: "월령 해석" },
  { key: "elements", title: "오행 분석" },
  { key: "temperature", title: "조후 분석" },
  { key: "contextual", title: "종합 근거" },
];

const productTextAliases = {
  "운세 영역": "분야별 총운",
  "영역별 운세": "분야별 총운",
  "분야별 운세": "분야별 총운",
  "보조 영역": "동반 강점",
  "보조 강점": "동반 강점",
  "관리 영역": "주의 영역",
  "관리 지점": "주의 영역",
  "재물·직업·인연의 세부 운세": "재물·직업·인연",
  "평판이 오래 남는 힘": "평판 지속력",
  "공식 책임을 맡는 힘": "공식 책임 수행력",
  "사람을 얻는 힘": "신뢰 형성력",
  "관계가 오래 남는 힘": "관계 지속력",
  "전문성으로 남는 힘": "전문 자산화",
  "가족 책임을 감당하는 힘": "가족 책임 경계력",
  "승진·직함 가능성": "직책 상승운",
  "재회 가능성": "다시 이어질 가능성",
  "독립 가능성": "혼자 일할 가능성",
  "재물 형성력": "재물 형성력",
  "수입 창출력": "수입 창출력",
  "재주 수익화": "재능 수익화",
  "성과 보상력": "성과 보상",
  "자산화 능력": "자산화",
  "자금 운용 안정성": "재정 관리",
  "계약·명의 안정성": "계약·명의 안정",
  "계약·문서 안정성": "문서 안정",
  "공동자금 운영력": "공동재정",
  "공동 자금 운영력": "공동재정",
  "부채·보증 관리력": "부채·보증 관리",
  "채권·미수금 회수력": "채권 회수",
  "재정 방어력": "손실 방어",
  "후반 축재력": "후반 자산운",
  "재물 주의 연도": "재물 관리 시기",
  "재물 강세 연도": "재물 강세 연도",
  "직업 적성": "직업 적합도",
  "직업 분야": "적합 분야",
  "성취 축적력": "경력 축적",
  "평가·명예 전환력": "평가와 인정",
  "권한 확보력": "권한 확보력",
  "책임·권한 균형": "책임과 권한",
  "보상 협상력": "보상 조건",
  "전문 자산화": "전문성 축적",
  "조직 적응력": "조직 적응",
  "소속 전환력": "직업 전환",
  "독립 전환운": "독립 가능성",
  "부적합 업무 조건": "피해야 할 업무",
  "직업 전환 연도": "직업 전환 연도",
  "끌림의 기준": "호감 기준",
  "인연 형성력": "인연 형성",
  "관계 진전력": "관계 진전",
  "애정 표현성": "애정 표현",
  "관계 지속력": "관계 지속",
  "오해 발생점": "오해 지점",
  "갈등 원인": "갈등 원인",
  "재회운": "재회 가능성",
  "결혼 연결력": "결혼 연결",
  "혼인성향": "결혼관",
  "혼인 성향": "결혼관",
  "배우자상": "배우자 조건",
  "결혼 적기": "결혼 적기",
  "생활 안정": "생활 안정",
  "부부 재정": "부부 재정",
  "부부 갈등": "부부 갈등",
  "가족 변수": "가족 변수",
  "배우자 복": "배우자 안정",
  "유지와 위기": "유지와 위기",
  "판단 방식": "자기 신뢰",
  "판단 기준": "자기 신뢰",
  "감정 반응": "감정 조절",
  "감정 반응성": "감정 조절",
  "압박 대응력": "문제 해결력",
  "압박 대응": "문제 해결력",
  "부담이 커질 때": "문제 해결력",
  "부담이 커졌을 때": "문제 해결력",
  "문제 발생 시 해결 능력": "문제 해결력",
  "행동 속도": "실행 속도",
  "움직이는 속도": "실행 속도",
  "실행 속도": "실행 속도",
  "관심 몰입도": "몰입력",
  "대인 거리감": "관계 거리 조절력",
  "관계 거리감": "관계 거리 조절력",
  "표현 전달력": "표현력",
  "관계 경계 설정력": "관계 경계",
  "현실 설계력": "현실 설계",
  "변화 적응력": "변화 적응",
  "위기 회복력": "위기 회복",
  "공적 인정 기반": "공적 인정",
  "명예를 지켜내는 기준": "평판 관리",
  "평판 지속력": "평판 지속",
  "사회적 도약성": "사회적 상승",
  "인맥 형성력": "인맥 형성",
  "도움으로 이어지는 인연": "도움 인연",
  "부탁과 책임의 경계": "부탁과 책임",
  "대인 조율감": "관계 조율",
  "사업 확장성": "사업 확장",
  "투자·거래 판단력": "투자·거래 판단",
  "재물 규모 확장력": "재물 규모 확장",
};

const branchProseReadingLabels = {
  子: "자",
  丑: "축",
  寅: "인",
  卯: "묘",
  辰: "진",
  巳: "사",
  午: "오",
  未: "미",
  申: "신",
  酉: "유",
  戌: "술",
  亥: "해",
};

const productTextReplacements = [
  [/세부 문서에서 확인할 항목입니다\./g, "실제 결과가 달라지는 대목입니다."],
  [/세부\s*운세에서 확인할 항목입니다\./g, "지표별로 결과가 달라지는 대목입니다."],
  [/세부 문서/g, "세부 해석"],
  [/경력의 설득력이 커집니다/g, "직업적 신뢰가 더 분명해집니다"],
  [/까지 받쳐 직업적 신뢰가 더 분명해집니다/g, "까지 함께 올라 직업적 신뢰가 더 분명해집니다"],
  [/승진·직함 가능성까지 함께 올라/g, "직책 상승운과 공식 인정이 함께 올라"],
  [/승진·직함 가능성/g, "직책 상승운"],
  [/직업운은 직책 상승운이/g, "직업운에서는 직책 상승운이"],
  [/승진과 직함 가능성이 함께 올라/g, "직책 상승운과 공식 인정이 함께 올라"],
  [/공식 직책이나 책임 있는 역할로 올라설 가능성입니다\./g, "공식 직책이나 책임 있는 역할로 올라서는 운입니다."],
  [/개인 수입을 넘어 거래와 사업 단위로 재물을 키우는 가능성입니다\./g, "개인 수입을 넘어 거래와 사업 단위로 재물을 키우는 폭입니다."],
  [/거래 조건과 손실 가능성을 읽고 결정하는 감각입니다\./g, "거래 조건과 손실 위험을 읽고 결정하는 감각입니다."],
  [/끊어진 관계가 다시 이어질 여지를 나타냅니다\./g, "끊어진 관계가 다시 이어지는 운입니다."],
  [/배우자와 생활 방식이 맞아갈 가능성입니다\./g, "배우자와 생활 방식이 맞아가는 정도입니다."],
  [/까지 받쳐 재물의 폭이 넓습니다/g, "까지 함께 잡혀 재물의 폭이 넓습니다"],
  [/돈이 생기는 자리/g, "재물이 형성되는 경로"],
  [/재물이 커지는 방식/g, "재물 규모가 확장되는 방식"],
  [/돈이 생기는/g, "재물이 형성되는"],
  [/자산으로 남는 힘/g, "자산으로 확정되는 정도"],
  [/실제로 회수하는 힘/g, "실제 권리로 회수하는 정도"],
  [/관리하는 힘/g, "관리 안정성"],
  [/정리하는 힘/g, "정리 기준"],
  [/구분하는 힘/g, "구분 기준"],
  [/바뀌는 힘/g, "전환되는 구조"],
  [/커지는 힘/g, "확장되는 정도"],
  [/이어지는 힘/g, "이어지는 구조"],
  [/남는 힘/g, "지속되는 정도"],
  [/성과와 평가 기준이 분명한 자리/g, "성과와 평가 기준이 분명한 환경"],
  [/평가 기준이 분명한 자리/g, "평가 기준이 분명한 환경"],
  [/평가 기준이 흐린 자리/g, "평가 기준이 불분명한 환경"],
  [/책임 있는 자리/g, "책임 있는 역할"],
  [/책임만 맡는 자리/g, "책임만 맡는 환경"],
  [/결정권이 없는 자리/g, "결정권이 없는 환경"],
  [/권한 없이 책임지는 자리/g, "권한 없이 책임지는 환경"],
  [/권한 없이 책임만 맡는 자리/g, "권한 없이 책임만 맡는 환경"],
  [/조직 안에서 자리 잡는 힘/g, "조직 적응력"],
  [/조직 안에서 자기 자리가 생기는/g, "조직 안에서 자기 역할이 생기는"],
  [/자기 자리를/g, "자기 역할을"],
  [/자기 자리가/g, "자기 역할이"],
  [/다음 자리/g, "다음 단계"],
  [/큰 자리/g, "큰 역할"],
  [/사회적 자리/g, "사회적 역할"],
  [/공식적인 자리/g, "공식적인 환경"],
  [/좋은 자리와 소모되는 자리/g, "유리한 환경과 불리한 환경"],
  [/맞지 않는 자리/g, "맞지 않는 환경"],
  [/피해야 할 자리/g, "피해야 할 환경"],
  [/주의할 자리/g, "주의할 환경"],
  [/결과가 약해지는 지점/g, "결과가 약해지는 조건"],
  [/주의 지점/g, "주의 대목"],
  [/필요한 지점입니다/g, "필요한 기준입니다"],
  [/분석 기준:/g, "근거:"],
  [/해석·대응책/g, "세부 해석"],
  [/대응책/g, "참고 사항"],
  [/전체 항목 눌렀을 때/g, "전체 항목을 열었을 때"],
  [/보시면 됩니다/g, "이어 볼 수 있습니다"],
  [/정도입니다\./g, "수준입니다."],
  [/항목입니다\./g, "부분입니다."],
  [/작용입니다\./g, "영향입니다."],
  [/힘입니다\./g, "강점입니다."],
  [/구조이 큽니다/g, "작용이 큽니다"],
  [/구조이/g, "구조가"],
  [/자리에서/g, "환경에서"],
  [/자리에/g, "환경에"],
  [/자리는/g, "환경은"],
  [/자리를/g, "환경을"],
  [/자리가/g, "환경이"],
  [/자리로/g, "역할로"],
  [/자리와/g, "환경과"],
  [/자리까지/g, "단계까지"],
  [/나누어/g, "구분해"],
  [/나눕니다/g, "구분합니다"],
];

function normalizeBranchProse(value) {
  return String(value || "")
    .replace(/(^|[\s,·])([子丑寅卯辰巳午未申酉戌亥])\s*월/g, (_, prefix, branch) => `${prefix}${branchProseReadingLabels[branch] || branch}월`)
    .replace(/월지\s*([子丑寅卯辰巳午未申酉戌亥])(?=에서|가|는|은|의|$)/g, (_, branch) => `월지 ${branch}(${branchProseReadingLabels[branch] || branch})`);
}

function productText(value) {
  const text = String(value || "").trim();
  const aliased = productTextAliases[text] || text;
  const normalized = normalizeBranchProse(tongbyeonSurfaceText(aliased));
  return productTextReplacements.reduce((current, [pattern, replacement]) => current.replace(pattern, replacement), normalized);
}

function stableCopyVariant(key, variants) {
  if (!Array.isArray(variants) || !variants.length) return "";
  const source = String(key || "");
  let hash = 0;
  for (let index = 0; index < source.length; index += 1) {
    hash = (hash * 31 + source.charCodeAt(index)) >>> 0;
  }
  return variants[hash % variants.length];
}

const stemElements = {
  甲: "wood",
  乙: "wood",
  丙: "fire",
  丁: "fire",
  戊: "earth",
  己: "earth",
  庚: "metal",
  辛: "metal",
  壬: "water",
  癸: "water",
};

const branchElements = {
  寅: "wood",
  卯: "wood",
  巳: "fire",
  午: "fire",
  辰: "earth",
  戌: "earth",
  丑: "earth",
  未: "earth",
  申: "metal",
  酉: "metal",
  亥: "water",
  子: "water",
};

const branchHiddenStemFallback = {
  子: ["壬", "癸"],
  丑: ["癸", "辛", "己"],
  寅: ["戊", "丙", "甲"],
  卯: ["甲", "乙"],
  辰: ["乙", "癸", "戊"],
  巳: ["戊", "庚", "丙"],
  午: ["丙", "己", "丁"],
  未: ["丁", "乙", "己"],
  申: ["戊", "壬", "庚"],
  酉: ["庚", "辛"],
  戌: ["辛", "丁", "戊"],
  亥: ["戊", "甲", "壬"],
};

const elementLabels = {
  wood: { ko: "목", han: "木", color: "var(--good)", meaning: "성장, 기획, 추진, 확장" },
  fire: { ko: "화", han: "火", color: "var(--warn)", meaning: "표현, 명성, 활력, 온도" },
  earth: { ko: "토", han: "土", color: "var(--earth)", meaning: "안정, 축적, 책임, 기반" },
  metal: { ko: "금", han: "金", color: "var(--metal)", meaning: "기준, 판단, 기술, 절제" },
  water: { ko: "수", han: "水", color: "var(--water)", meaning: "지혜, 유통, 학습, 정보" },
};

const displayTokenLabels = {
  ja: "子",
  chuk: "丑",
  in: "寅",
  myo: "卯",
  jin: "辰",
  sa: "巳",
  o: "午",
  mi: "未",
  sin: "申",
  yu: "酉",
  sul: "戌",
  hae: "亥",
  wood: "목",
  fire: "화",
  earth: "토",
  metal: "금",
  water: "수",
  spring: "봄",
  summer: "여름",
  autumn: "가을",
  fall: "가을",
  winter: "겨울",
  cold: "차가움",
  hot: "뜨거움",
  dry: "건조함",
  wet: "습함",
  very_weak: "매우 약함",
  weak: "약함",
  moderate: "보통",
  balanced: "균형",
  neutral: "중립",
  strong: "강함",
  very_strong: "매우 강함",
  support: "긍정",
  support01: "긍정",
  burden: "부담",
  caution: "주의",
  mixed: "혼합",
  money: "재물",
  career: "직업",
  honor: "명예",
  love: "연애",
  marriage: "결혼",
  social: "대인관계",
  personality: "성격",
  life: "인생 구간",
  timing: "시기운",
  both_supported_by_month_command: "월령이 함께 받치는 상태",
  first_supported_by_month_command: "앞선 작용이 월령에 닿는 상태",
  second_supported_by_month_command: "뒤따르는 작용이 월령에 닿는 상태",
  not_supported_by_month_command: "월령 접점이 약한 상태",
  constructive_action: "생극 작용",
  constructive_dual_action: "생극 결합",
  seonggyeok_chain: "성격 보조",
};

const branchReadingLabels = {
  子: "자",
  丑: "축",
  寅: "인",
  卯: "묘",
  辰: "진",
  巳: "사",
  午: "오",
  未: "미",
  申: "신",
  酉: "유",
  戌: "술",
  亥: "해",
};

function displayToken(value) {
  const text = String(value == null ? "" : value).trim();
  if (!text) return "";
  if (displayTokenLabels[text]) return displayTokenLabels[text];
  if (/^[a-z][a-z0-9_:-]*$/.test(text)) return "";
  return text;
}

function displayBranchReading(value) {
  const token = displayToken(value);
  if (!token) return "";
  const reading = branchReadingLabels[token];
  return reading ? `${token}(${reading})` : token;
}

function displayJoin(values, separator = " · ") {
  return values.map(displayToken).filter(Boolean).join(separator);
}

function displayDomainKeys(value, limit = 4) {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") return item.label || item.domain || item.key || "";
        return "";
      })
      .map(displayToken)
      .filter(Boolean)
      .slice(0, limit);
  }
  if (typeof value === "object") {
    return Object.keys(value)
      .filter((key) => !/^\d+$/.test(key))
      .map(displayToken)
      .filter(Boolean)
      .slice(0, limit);
  }
  return [];
}

function metricScore(item) {
  const score = Number(item && item.score);
  if (!Number.isFinite(score)) return null;
  return Math.max(0, Math.min(100, Math.round(score)));
}

function metricLevel(score, fallback = "") {
  if (fallback) return fallback;
  if (!Number.isFinite(score)) return "확인";
  if (score >= 80) return "매우 좋음";
  if (score >= 65) return "좋음";
  if (score >= 45) return "보통";
  if (score >= 30) return "주의";
  return "위험";
}

const metricGradeBands = Object.freeze([
  Object.freeze({ min: 80, label: "A+", key: "a-plus" }),
  Object.freeze({ min: 75, label: "A", key: "a" }),
  Object.freeze({ min: 70, label: "A-", key: "a-minus" }),
  Object.freeze({ min: 65, label: "B+", key: "b-plus" }),
  Object.freeze({ min: 60, label: "B", key: "b" }),
  Object.freeze({ min: 55, label: "B-", key: "b-minus" }),
  Object.freeze({ min: 50, label: "C+", key: "c-plus" }),
  Object.freeze({ min: 45, label: "C", key: "c" }),
  Object.freeze({ min: 40, label: "C-", key: "c-minus" }),
  Object.freeze({ min: 35, label: "D+", key: "d-plus" }),
  Object.freeze({ min: 30, label: "D", key: "d" }),
  Object.freeze({ min: 0, label: "D-", key: "d-minus" }),
]);

function metricGradeRank(grade) {
  return gradeRank(grade);
}

function metricGradeFromAverage(grades, fallback = "") {
  return gradeFromAverage(asArray(grades), fallback);
}

function metricGradeClassFromLabel(grade) {
  const band = metricGradeBands.find((item) => item.label === grade);
  return band ? `metric-grade-${band.key}` : "metric-grade-unknown";
}

function metricGradeVisualPosition(grade) {
  return visualPositionForGrade(grade);
}

function metricToneClassFromGrade(grade) {
  const rank = metricGradeRank(grade);
  if (rank >= metricGradeRank("A+")) return "metric-great";
  if (rank >= metricGradeRank("B+")) return "metric-good";
  if (rank >= metricGradeRank("C")) return "metric-normal";
  if (rank >= metricGradeRank("D")) return "metric-caution";
  return rank >= 0 ? "metric-risk" : "metric-normal";
}

function renderAggregateGradeBar(grade) {
  const position = metricGradeVisualPosition(grade);
  if (!Number.isFinite(position)) return "";
  return `
    <div class="metric-bar ${metricGradeClassFromLabel(grade)}" aria-hidden="true" title="${escapeHtml(`${grade} 등급`)}">
      <i style="width:${position}%"></i>
    </div>
  `;
}

function renderAggregateGradeBadge(grade) {
  if (metricGradeRank(grade) < 0) return "";
  return `
    <em class="metric-level-badge ${metricGradeClassFromLabel(grade)}" aria-label="${escapeHtml(`${grade} 등급`)}">
      <span>${escapeHtml(grade)}</span>
    </em>
  `;
}

function metricAggregateIdentity(item, index = 0) {
  const label = String(item && (item.label || item.title || item.key || `metric_${index}`) || "")
    .replace(/[\s·ㆍ,./|:;_\-–—()[\]{}#]+/g, "")
    .trim()
    .toLowerCase();
  return label || `metric_${index}`;
}

function uniqueAggregateMetricItems(items) {
  const seen = new Set();
  return asArray(items).filter((item, index) => {
    if (!item || typeof item !== "object") return false;
    const identity = metricAggregateIdentity(item, index);
    if (seen.has(identity)) return false;
    seen.add(identity);
    return true;
  });
}

const adjustedDomainKeys = new Set([
  "personality", "money", "career", "love", "marriage", "honor", "social",
]);

function metricDisplayContextForSection(section) {
  const domain = String(section && section.domain || "").trim();
  if (domain === "year_2026" || domain === "year_2027") return domain;
  if (adjustedDomainKeys.has(domain)) return "domains";
  return "none";
}

function normalizeMetricDisplayContext(contextKey = "") {
  const explicit = String(contextKey || "").trim();
  if (explicit === "none") return "none";
  if (["domains", "year_2026", "year_2027"].includes(explicit)) return explicit;
  const active = String(state.metricDisplayContext || "").trim();
  return ["domains", "year_2026", "year_2027"].includes(active) ? active : "none";
}

function metricDisplayAdjustmentForContext(contextKey = "") {
  const normalized = normalizeMetricDisplayContext(contextKey);
  return (state.metricDisplayAdjustments && state.metricDisplayAdjustments[normalized])
    || buildDisplayAdjustment([]);
}

function withMetricDisplayContext(contextKey, render) {
  const previousContext = state.metricDisplayContext;
  state.metricDisplayContext = normalizeMetricDisplayContext(contextKey);
  try {
    return render();
  } finally {
    state.metricDisplayContext = previousContext;
  }
}

function rawMetricGradeForItem(item, score = metricScore(item)) {
  if (!Number.isFinite(score)) return "";
  return gradeFromQualityScore(metricToneScore(item, score), "");
}

function metricItemDisplayGrade(item, contextKey = "", score = metricScore(item)) {
  const rawGrade = rawMetricGradeForItem(item, score);
  if (!rawGrade) return "";
  return displayGradeForRawGrade(rawGrade, metricDisplayAdjustmentForContext(contextKey));
}

function rawAggregateGradeFromMetricItems(items, fallback = "") {
  const grades = uniqueAggregateMetricItems(items)
    .map((item) => rawMetricGradeForItem(item))
    .filter(Boolean);
  return metricGradeFromAverage(grades, fallback);
}

function aggregateGradeFromMetricItems(items, fallback = "", contextKey = "") {
  const grades = uniqueAggregateMetricItems(items)
    .map((item) => metricItemDisplayGrade(item, contextKey))
    .filter(Boolean);
  return metricGradeFromAverage(grades, fallback);
}

function rawAnnualGroupAggregateGrade(group, fallback = "") {
  return rawAggregateGradeFromMetricItems(group && group.items, fallback);
}

function annualGroupAggregateGrade(group, fallback = "", contextKey = "") {
  return aggregateGradeFromMetricItems(group && group.items, fallback, contextKey);
}

function rawSectionAggregateGrade(section, fallback = "") {
  const groups = asArray(section && section.metric_groups)
    .filter((group) => group && asArray(group.items).length);
  if (groups.length) {
    const groupGrades = groups.map((group) => rawAnnualGroupAggregateGrade(group, "")).filter(Boolean);
    const annualGrade = metricGradeFromAverage(groupGrades, "");
    if (annualGrade) return annualGrade;
  }
  const metrics = [
    ...asArray(section && section.representative_metrics),
    ...asArray(section && section.feature_axes),
  ];
  return rawAggregateGradeFromMetricItems(metrics, fallback);
}

function sectionAggregateGrade(section, fallback = "", contextKey = metricDisplayContextForSection(section)) {
  const groups = asArray(section && section.metric_groups)
    .filter((group) => group && asArray(group.items).length);
  if (groups.length) {
    const groupGrades = groups.map((group) => annualGroupAggregateGrade(group, "", contextKey)).filter(Boolean);
    const annualGrade = metricGradeFromAverage(groupGrades, "");
    if (annualGrade) return annualGrade;
  }
  const metrics = [
    ...asArray(section && section.representative_metrics),
    ...asArray(section && section.feature_axes),
  ];
  return aggregateGradeFromMetricItems(metrics, fallback, contextKey);
}

function rawMetricGradeBand(score) {
  const grade = gradeFromQualityScore(score, "");
  return grade ? metricGradeBands.find((band) => band.label === grade) || null : null;
}

// Original judgment helpers must never read the product display context.
function judgmentGradeForScore(score, fallback = "") {
  const band = rawMetricGradeBand(score);
  return band ? band.label : fallback;
}

// The helpers below are presentation-only. They may adjust grades and bars,
// but their output must not be used to select judgment copy or engine meaning.
function metricGradeBand(score, contextKey = "") {
  const rawBand = rawMetricGradeBand(score);
  if (!rawBand) return null;
  const displayGrade = displayGradeForRawGrade(
    rawBand.label,
    metricDisplayAdjustmentForContext(contextKey),
  );
  return metricGradeBands.find((band) => band.label === displayGrade) || rawBand;
}

function metricGrade(score, fallback = "확인", contextKey = "") {
  const band = metricGradeBand(score, contextKey);
  return band ? band.label : fallback;
}

function metricGradeClass(score, contextKey = "") {
  const band = metricGradeBand(score, contextKey);
  return band ? `metric-grade-${band.key}` : "metric-grade-unknown";
}

function metricToneClass(score, contextKey = "") {
  if (!Number.isFinite(score)) return "metric-normal";
  return metricToneClassFromGrade(metricGrade(score, "", contextKey));
}

function metricPolarity(item) {
  const polarity = String(item && (item.polarity || item.direction || "")).toLowerCase();
  if (["risk", "negative", "burden", "caution", "watch", "loss", "danger"].includes(polarity)) {
    return "risk";
  }
  if (["positive", "good", "strength", "opportunity"].includes(polarity)) {
    return "positive";
  }
  const scoreDirection = String(item && item.score_direction || "").toLowerCase();
  if (["lower_is_better", "risk_is_bad", "negative", "burden"].includes(scoreDirection)) {
    return "risk";
  }
  if (["higher_is_better", "positive"].includes(scoreDirection)) {
    return "positive";
  }
  const labelText = `${item && (item.label || item.title || item.key || "") || ""} ${item && (item.summary || item.meaning || "") || ""}`;
  if (/회피력|방어력|관리력|감지|회복력|회복성|조절|통제력|안정성|유지력|지속성|확보력|수용도|적응성|적응력|판단력|처리력|협상력|보상도|보상력|형성력|창출력|축적|성취도|신뢰도|인정|상승도|확장|지원|기회|활력|탄력성|만족도|잔존 성과|조율성|합의성|책임감|친화성|협력성|덕|도움|연결운/.test(labelText)) {
    return "positive";
  }
  return /위험도|위험성|주의|손실|피해|갈등|충돌|부담|압박|노출|피로|과로|부주의|구설|오해|지연|개입|거리 발생|변동|예상 밖 지출|불가피한 지출|지출 압박|업무 부담|업무 갈등|경쟁 노출|배우자 갈등|상대 의존도|외부 변수 영향|관계 피로도|가족 개입/.test(labelText)
    ? "risk"
    : "positive";
}

function metricToneScore(item, score = metricScore(item)) {
  if (!Number.isFinite(score)) return score;
  const scoreDirection = String(item && item.score_direction || "").toLowerCase();
  if (["higher_is_better", "higher_is_good", "quality"].includes(scoreDirection)) {
    return score;
  }
  if (["lower_is_better", "higher_is_risk", "risk_is_bad"].includes(scoreDirection)) {
    return 100 - score;
  }
  const explicitQualityScore = Number(item && item.quality_score);
  if (Number.isFinite(explicitQualityScore)) {
    return Math.max(0, Math.min(100, Math.round(explicitQualityScore)));
  }
  return metricPolarity(item) === "risk" ? 100 - score : score;
}

function domainAdjustmentSourceGrades(sections) {
  return asArray(sections)
    .filter((section) => section && adjustedDomainKeys.has(String(section.domain || "")))
    .map((section) => rawSectionAggregateGrade(section, ""))
    .filter(Boolean);
}

function annualAdjustmentSourceGrades(sections, domainKey) {
  const section = asArray(sections).find((item) => item && item.domain === domainKey);
  return asArray(section && section.metric_groups)
    .filter((group) => group && asArray(group.items).length)
    .map((group) => rawAnnualGroupAggregateGrade(group, ""))
    .filter(Boolean);
}

function configureMetricDisplayAdjustment(sections) {
  state.metricDisplayAdjustments = {
    domains: buildDisplayAdjustment(domainAdjustmentSourceGrades(sections)),
    year_2026: buildDisplayAdjustment(annualAdjustmentSourceGrades(sections, "year_2026")),
    year_2027: buildDisplayAdjustment(annualAdjustmentSourceGrades(sections, "year_2027")),
  };
  return state.metricDisplayAdjustments;
}

function metricLevelForItem(item, score = metricScore(item), fallback = "") {
  const aggregateGrade = String(item && item.aggregate_grade || "").trim();
  if (metricGradeRank(aggregateGrade) >= 0) return aggregateGrade;
  if (Number.isFinite(score)) return metricItemDisplayGrade(item, "", score) || fallback || "확인";
  return fallback || "확인";
}

function metricToneClassForItem(item, score = metricScore(item)) {
  const aggregateGrade = String(item && item.aggregate_grade || "").trim();
  if (metricGradeRank(aggregateGrade) >= 0) return metricToneClassFromGrade(aggregateGrade);
  return metricToneClassFromGrade(metricItemDisplayGrade(item, "", score));
}

function renderMetricBarForItem(item, score = metricScore(item)) {
  const aggregateGrade = String(item && item.aggregate_grade || "").trim();
  if (metricGradeRank(aggregateGrade) >= 0) return renderAggregateGradeBar(aggregateGrade);
  const grade = Number.isFinite(score) ? metricItemDisplayGrade(item, "", score) : "";
  return grade ? renderAggregateGradeBar(grade) : "";
}

function renderMetricLevelBadgeForItem(item, score = metricScore(item), fallback = "") {
  const aggregateGrade = String(item && item.aggregate_grade || "").trim();
  if (metricGradeRank(aggregateGrade) >= 0) return renderAggregateGradeBadge(aggregateGrade);
  const grade = Number.isFinite(score) ? metricItemDisplayGrade(item, "", score) : "";
  return grade ? renderAggregateGradeBadge(grade) : renderMetricLevelBadge(fallback || "확인", null);
}

function sectionMetricScore(section) {
  const verdict = section && section.section_verdict ? section.section_verdict : {};
  const directScores = [
    section && section.total_score,
    verdict && verdict.score,
    section && section.strength_score,
    section && section.score,
  ];
  for (const item of directScores) {
    const directScore = Number(item);
    if (Number.isFinite(directScore)) {
      return Math.max(0, Math.min(100, Math.round(directScore)));
    }
  }
  const scores = [
    ...asArray(section && section.representative_metrics),
    ...asArray(section && section.feature_axes),
    ...asArray(section && section.topic_items),
  ]
    .map((item) => metricToneScore(item))
    .filter((score) => Number.isFinite(score));
  if (!scores.length) return null;
  return Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length);
}

function metricLabel(item, fallback = "세부 지표") {
  return productText(displayToken(item && (item.label || item.title || item.key || item.domain)) || fallback);
}

const metricDefaultBodies = {
  "감정 반응": "감정이 올라온 뒤 말과 태도가 정돈되는 방식입니다.",
  "감정 반응성": "불편한 상황에서 감정을 드러내는 속도와 강도입니다.",
  "관심 몰입도": "한 가지 주제에 오래 집중하고 결과를 남기는 성향입니다.",
  "대인 거리감": "사람을 가까이 두는 방식과 선을 긋는 기준입니다.",
  "대인 조율감": "상대의 입장과 자신의 기준을 맞추는 감각입니다.",
  "실행 속도": "결정을 실제 행동으로 옮기는 속도입니다.",
  "압박 대응력": "문제가 생겼을 때 순서와 책임을 정리하는 대응 기준입니다.",
  "판단 기준": "중요한 선택 앞에서 자기 결론을 믿고 세우는 기준입니다.",
  "공동자금 운영력": "가까운 사람과 돈이 얽힐 때 내 몫과 책임 범위를 지키는 기준입니다.",
  "계약·명의 안정성": "받을 돈과 권리를 문서, 명의, 지분으로 분명히 남기는 기준입니다.",
  "계약·문서 안정성": "말로 정한 약속을 문서와 권리 관계로 굳히는 기준입니다.",
  "금전 기준성": "돈을 쓰고 남기는 선을 분명하게 세우는 감각입니다.",
  "성과 보상력": "노력과 성과가 실제 보상으로 돌아오는 흐름입니다.",
  "수입 창출력": "일과 성과가 실제 수입으로 이어지는 폭입니다.",
  "자금 운용 안정성": "생활비와 예비금을 따로 나눌수록 재물운이 안정됩니다.",
  "자산화 능력": "들어온 돈이 명의, 권리, 자산으로 남는 흐름입니다.",
  "가족재산 관리력": "가족 돈과 자기 재산이 섞일 때 권리와 부담을 분리하는 기준입니다.",
  "가족재산 경계력": "가족 명의, 지원, 공동 부담 속에서도 자기 몫을 지키는 기준입니다.",
  "계약·명의 변동기": "문서, 명의, 권리 관계를 특히 분명히 해야 하는 시기입니다.",
  "재물 강세 연도": "재물과 관련한 결정이 뚜렷해지는 시기입니다.",
  "재물 규모 확장력": "개인 수입을 넘어 거래와 사업 단위로 재물이 커지는 흐름입니다.",
  "재물 형성력": "수입이 지나가는 돈으로 끝나지 않고 자기 재산으로 남는 흐름입니다.",
  "재정 안정성": "손실이나 변수에도 핵심 자산과 현금 기반이 흔들리지 않는 상태입니다.",
  "재정 방어력": "예상 밖의 지출과 손실이 생겨도 생활 기반을 지키는 관리입니다.",
  "재주 수익화": "기술, 말, 콘텐츠, 서비스가 수입으로 바뀌는 흐름입니다.",
  "채권·미수금 회수력": "늦어진 돈이나 받아야 할 보상을 흐지부지 넘기지 않는 편입니다.",
  "후반 축재력": "나이가 들수록 돈이 생활 기반과 보유 자산으로 자리 잡기 쉽습니다.",
  "부채·보증 관리력": "대여, 보증, 채무 인수에서 남의 책임이 넘어오지 않게 막는 기준입니다.",
  "투자·거래 판단력": "거래 조건과 손실 위험을 읽고 결정하는 감각입니다.",
  "권한 확보력": "맡은 일에 필요한 결정권을 함께 가져오는 흐름입니다.",
  "보상 협상력": "성과를 연봉, 성과급, 수수료, 계약 조건으로 바꾸는 기준입니다.",
  "사회적 도약성": "직업적 성과가 더 높은 역할과 평판으로 이어지는 흐름입니다.",
  "성취 축적력": "해온 일이 경력과 실적으로 오래 남는 흐름입니다.",
  "소속 전환력": "회사, 부서, 직무가 바뀌어도 새 역할을 다시 잡는 적응력입니다.",
  "전환 대응력": "소속이나 역할이 바뀌는 시기에 새 기준을 빠르게 세우는 감각입니다.",
  "승진·직함 가능성": "공식 직책이나 책임 있는 역할로 올라서는 운입니다.",
  "직책 상승운": "공식 직책이나 책임 있는 역할로 올라서는 운입니다.",
  "업무 조건 감별력": "좋은 일과 소모적인 일을 구분하는 감각입니다.",
  "전문 자산화": "기술, 자격, 경험이 직업적 자산으로 쌓이는 흐름입니다.",
  "조직 적응력": "조직의 규칙과 평가 체계 안에서 안정적으로 인정받는 편입니다.",
  "직무 적합성": "맡는 역할과 일하는 방식이 자신의 강점과 맞는지 드러납니다.",
  "직업 적성": "경력이 오래 쌓일수록 능력이 더 잘 드러나는 일의 방향입니다.",
  "직업 전환 연도": "이직, 승진, 독립, 역할 변화가 실제 선택으로 올라오는 시기입니다.",
  "책임·권한 균형": "맡은 책임과 실제 결정권이 함께 주어지는 구조입니다.",
  "평가·명예 전환력": "성과가 평판, 직함, 신뢰로 이어지는 흐름입니다.",
  "결혼 연결력": "연애가 장기 관계와 결혼 논의로 이어지는 흐름입니다.",
  "관계 속도 조절력": "가까워지는 속도를 안정적으로 맞추는 감각입니다.",
  "관계 주도권": "관계의 방향과 거리를 스스로 정하는 성향입니다.",
  "관계 진전력": "호감이 실제 만남과 약속으로 이어지는 속도입니다.",
  "끌림의 기준": "어떤 사람에게 마음이 움직이는지 보여주는 기준입니다.",
  "상대 선택력": "오래 갈 사람과 잠깐 스치는 사람을 구분하는 감각입니다.",
  "상대 신뢰 감별력": "상대의 말과 태도에서 믿을 만한 부분을 가려내는 능력입니다.",
  "애정 표현성": "마음을 말과 행동으로 전달하는 방식입니다.",
  "인연 형성력": "새로운 만남이 생기고 관계가 시작되는 흐름입니다.",
  "재회 가능성": "끊어진 관계가 다시 이어지는 운입니다.",
  "재회운": "끊어진 관계가 다시 이어지는 운입니다.",
  "정서 수용력": "상대의 감정과 불안을 받아내는 폭입니다.",
  "오해 조정력": "말하지 않고 넘긴 감정을 늦기 전에 다시 맞추는 감각입니다.",
  "갈등 관리력": "자존심과 생활 기준이 부딪힐 때 관계를 깨뜨리지 않는 기준입니다.",
  "연락·거리 안정성": "연락, 사생활, 만남의 간격이 안정적으로 맞는 편입니다.",
  "주변 개입 관리력": "가족, 친구, 과거 인연의 말이 관계를 흔들지 않게 막는 기준입니다.",
  "가정 운영력": "가정 안의 책임과 생활 질서를 안정시키는 기준입니다.",
  "결혼 적기": "결혼 논의와 생활 결정을 진행하기 좋은 시기입니다.",
  "결혼 연결력": "결혼 의사가 집, 일정, 가족 협의, 공식 절차로 넘어가는 현실성입니다.",
  "배우자 적합성": "배우자와 생활 방식이 맞아가는 흐름입니다.",
  "배우자운 안정성": "배우자와의 관계가 장기적으로 흔들리지 않는 바탕입니다.",
  "부부 갈등 조정력": "서운함과 현실 문제를 오래 끌지 않고 정리하는 기준입니다.",
  "부부 갈등 회복성": "상한 감정 뒤에도 생활 기준을 다시 세우는 감각입니다.",
  "부부 재정": "결혼 뒤 돈의 기준과 지출 방식이 맞아가는 흐름입니다.",
  "가족 책임 경계력": "양가와 원가족 문제에서 부부의 책임선을 지켜내는 기준입니다.",
  "배우자 가족 경계": "배우자 가족 문제가 부부 생활 안으로 과하게 들어오지 않게 하는 기준입니다.",
  "자녀·양육 책임": "자녀, 돌봄, 교육비가 결혼 생활의 실제 과제로 들어오는 흐름입니다.",
  "혼인 위기 대응력": "돈, 가족, 주거 문제가 겹칠 때 결혼을 다시 세우는 능력입니다.",
  "결혼 지속력": "한 번 정한 결혼의 약속을 오래 유지하려는 성향입니다.",
  "생활 안정": "집, 돈, 역할이 한 생활 안에서 안정되는 바탕입니다.",
  "주거·생활 설계력": "살 곳과 생활비, 책임 분담을 구체화하는 기준입니다.",
  "혼인 안정성": "결혼 생활이 장기적으로 유지되는 바탕입니다.",
  "가족재산 주의 연도": "가족 자산과 내 재산의 경계를 분명히 해야 하는 시기입니다.",
  "계약·명의 주의 연도": "문서, 명의, 권리 관계에서 손익이 갈리는 시기입니다.",
  "공동자금 주의 연도": "동업, 공동비용, 지분 문제가 예민해지는 시기입니다.",
  "두드러지는 영역": "해당 시기에 가장 먼저 움직이는 생활 영역입니다.",
  "부채·보증 주의 연도": "빌린 돈, 보증, 채무 부담을 가볍게 넘기면 안 되는 시기입니다.",
  "상승 연도": "성과와 기회가 비교적 선명하게 드러나는 시기입니다.",
  "재물 주의 연도": "계약, 회수, 지급일을 먼저 확인해야 하는 시기입니다.",
  "주의 연도": "무리한 결정과 관계 변수를 조심해야 하는 시기입니다.",
  "지나온 연도": "이미 지나온 시기 중 사주의 특징이 강하게 드러난 해입니다.",
  "직업 상승 연도": "직업적 성과와 평판이 두드러지는 시기입니다.",
  "말년에 남는 안정": "말년에 유지되는 생활 기반과 관계의 안정감입니다.",
  "운이 바뀌는 전환기": "일, 관계, 생활 방식이 다른 국면으로 넘어가는 구간입니다.",
  "중년에 굳어지는 성취": "중년 이후 경력과 재산이 형태를 갖추는 흐름입니다.",
  "초년에 형성되는 바탕": "초년에 만들어지는 성향, 습관, 생활 기반입니다.",
  "공식 책임 수행력": "공적인 책임을 맡아 끝까지 수행하는 능력입니다.",
  "공적 인정 기반": "실력과 역할이 사회적 신뢰로 인정받는 바탕입니다.",
  "명예를 지켜내는 기준": "평판을 흔드는 일을 피하고 신뢰를 유지하는 기준입니다.",
  "평판 지속력": "한 번 얻은 신뢰와 이름값이 오래 이어지는 흐름입니다.",
  "관계 지속력": "인연을 가볍게 흘려보내지 않고 오래 유지하는 능력입니다.",
  "도움으로 이어지는 인연": "사람과의 연결이 실제 도움이나 기회로 이어지는 흐름입니다.",
  "부탁과 책임의 경계": "타인의 부탁을 어디까지 받아들일지 정하는 기준입니다.",
  "인맥 형성력": "새로운 사람과 연결되고 관계망을 넓히는 흐름입니다.",
};

function currentUserDisplayName() {
  const formName = form ? String(new FormData(form).get("nickname") || "").trim() : "";
  const profileName = String(
    (state.payload && state.payload.profile && (state.payload.profile.name || state.payload.profile.nickname)) ||
      (state.payload && state.payload.report && state.payload.report.profile && (state.payload.report.profile.name || state.payload.report.profile.nickname)) ||
      "",
  ).trim();
  const displayName = productText(formName || profileName || "")
    .replace(/\s+/g, " ")
    .trim();
  if (!displayName || displayName === "고객" || displayName === "고객님") return "";
  return displayName.replace(/님$/, "");
}

function currentUserSubject() {
  const name = currentUserDisplayName();
  return name ? `${name}님은` : "당신은";
}

function metricJudgmentStateType(item, score = metricScore(item)) {
  if (!Number.isFinite(score)) return "normal";
  return semanticStateForGrade(rawMetricGradeForItem(item, score));
}

function metricStateLead(item, score = metricScore(item)) {
  const subject = currentUserSubject();
  const stateType = metricJudgmentStateType(item, score);
  if (stateType === "good") {
    return `${subject} 이 지표가 좋게 나타나는군요.`;
  }
  if (stateType === "bad") {
    return `${subject} 이 지표가 좋지는 않군요.`;
  }
  return `${subject} 이 영역에서 평범한 편입니다.`;
}

function normalizeMetricDescriptionKey(value) {
  return String(value || "")
    .replace(/\s+/g, "")
    .replace(/[·ㆍ,./|:;_\-–—()[\]{}#]/g, "")
    .trim()
    .toLowerCase();
}

function metricDescriptionKeys(item) {
  const keys = [
    item && item.label,
    item && item.title,
    item && item.key,
    item && item.domain,
    item && item.source_label,
    item && item.sourceLabel,
    item && item.metric_label,
    item && item.metricLabel,
    item && item.concept,
    item && item.concept_label,
    item && item.conceptLabel,
    item && item.basis,
    item && item.basis_label,
    item && item.basisLabel,
    item && item.ganji,
    item && item.ten_god,
    item && item.tenGod,
    item && item.element,
    item && item.branch,
    item && item.stem,
  ];
  return [...new Set(keys.map(normalizeMetricDescriptionKey).filter(Boolean))];
}

function curatedMetricDescription(definition, good, bad) {
  return Object.freeze({ definition, good, bad, type: "positive", direct: true });
}

const curatedMetricDescriptionOverrides = Object.freeze({
  "자산전환력": curatedMetricDescription(
    "자산 전환력은 들어온 돈을 소비로 흩뜨리지 않고 예금, 지분, 부동산, 장기 자산처럼 소유권이 남는 형태로 전환하는 성향입니다.",
    "수입이 생기면 일부를 남기고 자산으로 옮기려는 성향이 뚜렷합니다. 시간이 지날수록 소득의 일부가 실질적인 소유 자산으로 축적될 가능성이 큽니다.",
    "수입을 장기 자산으로 전환하는 흐름이 안정적이지 않습니다. 돈이 들어와도 생활비와 단기 지출로 분산되면서 실제 소유 자산으로 남는 비율이 낮아질 가능성이 있습니다.",
  ),
  "독립업무수행력": curatedMetricDescription(
    "독립 업무 수행력은 조직의 지시와 지원이 부족한 상황에서도 고객, 결과물, 일정, 보수 체계를 스스로 조직하는 정도입니다.",
    "독립적으로 업무의 기준과 순서를 세우는 능력이 좋게 나타납니다. 프리랜서, 개인 사업, 단독 프로젝트에서도 업무 흐름을 유지하고 성과를 만들 가능성이 큽니다.",
    "역할과 보상 체계가 분명한 환경에서 능력이 더 안정적으로 드러나는 편입니다. 모든 과정을 혼자 책임지는 상황에서는 업무의 우선순위나 수익 구조가 흔들릴 가능성이 있습니다.",
  ),
  "자기확신": curatedMetricDescription(
    "자기 확신은 자신의 판단 근거를 믿고 결정의 방향을 유지하는 정도입니다. 단순히 주장이 강한 것이 아니라, 주변의 반응과 자신의 판단이 다를 때 기준을 분명히 정하는 정도를 의미합니다.",
    "근거가 충분하다고 판단한 일에서는 주변의 평가가 엇갈려도 결정을 쉽게 거두지 않습니다. 중요한 선택을 스스로 내리고 그 결과까지 책임질 가능성이 큽니다.",
    "결정을 내린 뒤에도 다른 사람의 반응을 여러 차례 확인하는 경향이 있습니다. 의견이 엇갈리는 상황에서는 판단이 늦어지거나 이미 내린 결정을 다시 검토할 가능성이 있습니다.",
  ),
  "실행속도": curatedMetricDescription(
    "실행 속도는 판단을 실제 행동으로 옮기고 결과를 확인하기까지 걸리는 속도를 나타냅니다. 생각이 빠른 것보다, 결론을 내린 뒤 얼마나 신속하게 움직이는지를 다룹니다.",
    "방향이 정해지면 준비에만 머물지 않고 행동으로 옮기는 편입니다. 기회를 포착하면 먼저 움직여 유리한 흐름을 확보할 가능성이 큽니다.",
    "행동하기 전에 조건을 충분히 확인하려는 경향이 강합니다. 검토가 길어지면 결정을 내리고도 적절한 시기를 놓칠 가능성이 있습니다.",
  ),
  "판단신중성": curatedMetricDescription(
    "판단 신중성은 행동하기 전에 정보와 결과, 위험 요소, 타인에게 미칠 영향을 검토하는 정도입니다.",
    "중요한 선택일수록 조건과 이후의 결과를 먼저 검토하는 편입니다. 계약이나 금전처럼 되돌리기 어려운 문제에서 실수를 줄일 가능성이 큽니다.",
    "결론을 빠르게 내리는 대신 이후에 생길 변수까지 충분히 살피지 못할 수 있습니다. 장기적인 책임이 따르는 선택에서는 예상하지 못한 부담이 남을 가능성이 있습니다.",
  ),
  "집중지속력": curatedMetricDescription(
    "집중 지속력은 한 가지 주제나 과제를 깊이 파고들고, 일정한 성과가 나올 때까지 관심과 에너지를 유지하는 정도입니다. 순간적인 열정보다 몰입이 얼마나 오래 지속되는지를 나타냅니다.",
    "관심을 가진 분야에서는 쉽게 이탈하지 않고 경험을 축적하는 편입니다. 시간이 필요한 전문 영역에서 뚜렷한 숙련도와 성과를 만들 가능성이 큽니다.",
    "관심이 여러 방향으로 분산되면서 한 가지 과제를 오래 붙드는 일이 부담스러울 수 있습니다. 시작한 일의 완성도가 충분히 높아지기 전에 다음 일로 넘어갈 가능성이 있습니다.",
  ),
  "관계거리조절력": curatedMetricDescription(
    "관계 거리 조절력은 상대와의 친밀도, 연락의 빈도, 책임의 범위를 관계의 단계에 맞게 조정하는 능력입니다. 가까워지는 힘뿐 아니라 필요할 때 적절한 경계를 세우는 성향도 포함합니다.",
    "관계를 지나치게 서두르거나 불필요하게 밀어내지 않고 상대의 반응에 맞춰 거리를 조절하는 편입니다. 감정이 흔들리는 상황에서도 관계가 쉽게 악화되지 않습니다.",
    "가까워지는 속도와 책임의 범위를 상황에 맞게 조정하는 데 어려움을 느낄 수 있습니다. 관계가 급격히 가까워지거나 반대로 필요한 대화까지 피하면서 거리감이 커질 가능성이 있습니다.",
  ),
  "의사표현력": curatedMetricDescription(
    "의사 표현력은 생각과 감정을 말, 글, 표정, 행동으로 분명하게 전달하는 정도입니다. 표현의 양보다 자신의 의도가 상대에게 정확하게 전달되는지를 나타냅니다.",
    "필요한 상황에서 자신의 입장과 감정을 비교적 분명하게 전달하는 편입니다. 중요한 대화에서 의도가 왜곡되거나 불필요한 오해가 생길 가능성이 낮습니다.",
    "생각이 분명하더라도 그것을 상대가 이해할 수 있는 형태로 드러내는 데 시간이 걸릴 수 있습니다. 충분히 설명하지 못해 의도와 다른 평가를 받을 가능성이 있습니다.",
  ),
  "사회적인정가능성": curatedMetricDescription(
    "사회적 인정 가능성은 자신의 능력과 성과를 외부에서 알아볼 수 있는 형태로 정리하고 드러내는 성향과 관련이 있습니다. 성과가 평가, 직함, 신뢰로 연결될 조건이 갖춰져 있는지를 나타냅니다.",
    "맡은 역할과 성과를 사회적 기준에 맞게 증명하려는 성향이 분명합니다. 꾸준히 결과를 쌓으면 개인적인 만족에 그치지 않고 공식적인 평가와 신뢰로 이어질 가능성이 큽니다.",
    "실제 능력과 별개로 성과를 외부에 드러내거나 평가받는 과정에는 적극적이지 않은 편입니다. 충분한 결과를 만들고도 공식적인 인정이나 기회로 연결하지 못할 가능성이 있습니다.",
  ),
  "위험대응력": curatedMetricDescription(
    "위험 대응력은 손실, 갈등, 실수로 이어질 징후를 미리 알아차리고 대비하는 성향을 나타냅니다. 문제가 발생한 뒤 상황을 수습하고 정상적인 흐름을 회복하는 능력까지 포함합니다.",
    "상황이 크게 나빠지기 전에 불리한 조건을 발견하고 대응 방향을 정하는 편입니다. 예상하지 못한 변수가 발생하더라도 손실의 범위를 줄이고 흐름을 회복할 가능성이 큽니다.",
    "문제가 분명하게 드러난 뒤에야 대응을 시작하는 경향이 있습니다. 작은 이상 신호를 지나치면 해결할 수 있었던 문제가 더 큰 부담으로 이어질 가능성이 있습니다.",
  ),
  "관계주도력": curatedMetricDescription(
    "관계 주도력은 상대의 반응에 끌려가기보다 관계의 속도와 방향, 자신이 감당할 책임의 범위를 스스로 선택하는 정도입니다.",
    "관계 안에서도 자신의 기준을 잃지 않습니다. 상대의 감정을 존중하면서도 필요한 선택을 직접 내리기 때문에 관계가 일방적으로 흘러갈 가능성이 낮습니다.",
    "관계의 방향을 상대에게 맡기는 경향이 나타납니다. 상대의 속도에 맞추다 보면 원하지 않는 책임을 받아들이거나 자신의 입장을 뒤늦게 밝힐 가능성이 있습니다.",
  ),
  "결혼준비성": curatedMetricDescription(
    "결혼 준비성은 연인과의 관계를 결혼이라는 현실적 과제로 발전시키기 위한 노력 정도를 의미합니다. 생활 습관이나 재정, 기타 가족 문제 등 결혼을 위한 현실적 준비라고 할 수 있겠군요.",
    "관계를 현실적인 약속으로 발전시킬 준비가 잘 갖춰져 있습니다. 적절한 상대와 조건이 마련되면 결혼에 필요한 책임과 생활 문제를 구체적으로 조율할 가능성이 큽니다.",
    "감정과 현실 조건을 하나의 결론으로 묶는 과정이 쉽지는 않습니다. 관계가 안정적이어도 재정이나 생활 조건에 대한 확신이 부족하면 결혼 결정이 오래 미뤄질 가능성이 있습니다.",
  ),
  "책임의식": curatedMetricDescription(
    "책임 의식은 조직이나 사회에서 맡은 역할의 범위와 결과를 인식하고, 필요한 결정을 끝까지 수행하는 정도입니다.",
    "권한이 주어졌을 때 그에 따르는 책임까지 함께 감당하는 편입니다. 직책이나 공식 역할이 커질수록 판단과 실행이 안정되어 신뢰를 얻을 가능성이 큽니다.",
    "책임의 범위가 넓고 기준이 불분명한 상황에서 부담을 크게 느낄 수 있습니다. 권한보다 책임이 먼저 주어지면 판단이 위축되거나 역할을 오래 유지하기 어려울 가능성이 있습니다.",
  ),
  "조직영향력": curatedMetricDescription(
    "조직 영향력은 자신의 판단, 설명, 성과가 조직 구성원의 결정과 업무 방향에 반영되는 정도입니다. 단순히 눈에 띄는 것보다 실제 결정에 미치는 영향을 나타냅니다.",
    "결과와 판단을 통해 조직 안에서 영향력을 확보할 가능성이 큽니다. 경험이 쌓일수록 의견을 묻거나 중요한 결정을 맡기는 사람이 늘어날 수 있습니다.",
    "맡은 일을 충실히 수행하더라도 자신의 판단을 조직의 결정으로 연결하는 힘은 약한 편입니다. 성과가 있어도 의사결정 과정에서는 존재감이 충분히 드러나지 않을 가능성이 있습니다.",
  ),
  "인맥관계형성력": curatedMetricDescription(
    "인맥 관계 형성력은 새로운 사람과 자연스럽게 접점을 만들고 대화를 시작하며, 다음 만남으로 관계를 이어가는 정도입니다.",
    "낯선 사람과도 관계의 첫 단계를 비교적 자연스럽게 엽니다. 새로운 환경에서 협력자나 지인을 확보하고 활동 범위를 넓힐 가능성이 큽니다.",
    "상대를 충분히 파악하기 전에는 먼저 관계를 시작하지 않는 편입니다. 신뢰가 형성되면 관계가 깊어질 수 있지만 새로운 인연이 시작되는 속도는 느릴 가능성이 있습니다.",
  ),
  "말의설득력": curatedMetricDescription(
    "말의 설득력은 자신의 생각과 근거를 상대가 이해할 수 있는 순서로 전달하고, 판단이나 행동의 변화를 이끌어내는 정도입니다.",
    "자신의 주장을 근거와 맥락에 맞게 설명하는 능력이 좋게 나타납니다. 협상이나 발표처럼 상대의 동의를 얻어야 하는 상황에서 의견을 실제 결정으로 연결할 가능성이 큽니다.",
    "생각의 내용에 비해 그것을 상대가 납득할 수 있도록 구성하는 과정이 약한 편입니다. 옳은 말을 하고도 설명 방식 때문에 충분한 동의를 얻지 못할 가능성이 있습니다.",
  ),
  "갈등조정력": curatedMetricDescription(
    "갈등 조정력은 의견 차이나 감정 충돌이 커지기 전에 쟁점을 분리하고, 서로 받아들일 수 있는 기준을 찾는 정도입니다.",
    "갈등이 생겼을 때 감정만으로 대응하지 않고 문제의 원인을 정리하는 편입니다. 관계를 끊지 않고도 입장 차이를 조율해 필요한 합의를 만들 가능성이 큽니다.",
    "불편한 상황을 미루다가 갈등이 커진 뒤에야 대응하는 경향이 있습니다. 작은 오해가 반복되면 해결보다 관계 단절을 선택할 가능성이 있습니다.",
  ),
});

const curatedAnnualMetricDescriptionOverrides = Object.freeze({
  "역할확대가능성": curatedMetricDescription(
    "역할 확대 가능성은 새로운 업무와 프로젝트, 책임 범위가 들어오고 이를 감당할 조건이 형성되는 정도입니다.",
    "기존 역할보다 한 단계 넓은 일을 맡을 가능성이 큽니다. 책임과 권한이 함께 주어진다면 경력과 성과를 확장하는 계기가 될 수 있습니다.",
    "새로운 역할이 들어오더라도 이를 안정적으로 정착시킬 조건이 충분하지 않습니다. 당분간은 기존 업무의 완성도와 기반을 다지는 편이 유리할 가능성이 있습니다.",
  ),
  "이직기회": curatedMetricDescription(
    "이직 기회는 새로운 직장이나 직무에 관한 제안과 선택지가 들어오고, 실제 이동으로 이어질 조건이 마련되는 정도입니다.",
    "현재보다 나은 조건을 검토할 수 있는 선택지가 생길 가능성이 큽니다. 준비된 경력과 이동 목적이 분명하다면 이직이 새로운 성장 기회로 이어질 수 있습니다.",
    "직업 이동에 필요한 제안이나 외부 연결이 충분히 형성되지 않습니다. 이동을 서두르면 조건이 나아지기보다 불안정성만 커질 가능성이 있습니다.",
  ),
  "관계확장가능성": curatedMetricDescription(
    "관계 확장 가능성은 새로운 사람과 연결되고 인간관계의 범위가 넓어지며, 그 관계가 실제 활동으로 이어지는 정도입니다.",
    "새로운 관계와 협력의 통로가 활발하게 열릴 가능성이 큽니다. 사람을 통해 일이나 정보, 새로운 기회가 연결될 수 있습니다.",
    "새로운 관계보다 기존 인연을 유지하고 정리하는 흐름이 강합니다. 활동 범위를 무리하게 넓히면 관계의 피로만 커질 가능성이 있습니다.",
  ),
  "연애흐름활성도": curatedMetricDescription(
    "연애 흐름 활성도는 호감, 만남, 감정 교류가 늘어나고 관계가 다음 단계로 움직일 가능성을 나타냅니다.",
    "연애와 감정 관계가 활발하게 움직일 가능성이 큽니다. 새로운 만남이 시작되거나 기존 관계에서 감정 교류가 깊어질 수 있습니다.",
    "연애 관계가 빠르게 진전되기보다 자신의 감정과 기준을 정리하는 흐름이 강합니다. 만남이 생겨도 관계가 본격적으로 시작되기까지 시간이 걸릴 가능성이 있습니다.",
  ),
  "결혼구체화": curatedMetricDescription(
    "결혼 구체화는 혼인에 관한 생각이 약속, 가족 협의, 주거, 재정 계획처럼 현실적인 단계로 이어지는 정도입니다. 혼인 시기가 아니라면, 연인 및 새로운 인연과의 관계를 현실적으로 안정시키고 유지하는 정도를 의미합니다.",
    "결혼에 필요한 현실 조건을 조율하고 결론을 내릴 가능성이 큽니다. 이미 관계가 있다면 장기 계획이 구체적인 약속으로 이어질 수 있습니다.",
    "결혼에 관한 마음과 현실 조건 사이의 간격이 쉽게 좁혀지지 않습니다. 관계가 안정적이어도 일정이나 재정 문제로 결정이 미뤄질 가능성이 있습니다.",
  ),
  "대외활동성": curatedMetricDescription(
    "대외 활동성은 발표, 홍보, 대표 역할, 외부 협력처럼 자신의 이름과 성과가 밖으로 드러나는 활동이 늘어나는 정도입니다.",
    "외부에서 자신의 능력과 성과를 보여줄 기회가 많아질 가능성이 큽니다. 준비된 결과를 적절히 드러내면 새로운 평가와 연결로 이어질 수 있습니다.",
    "외부 노출보다 내부 업무와 기반 정리에 무게가 실립니다. 성과가 있어도 이를 적극적으로 알리지 않으면 평가와 기회가 제한될 가능성이 있습니다.",
  ),
  "사회적영향력확대": curatedMetricDescription(
    "사회적 영향력 확대는 자신의 말과 판단, 성과가 조직이나 주변 사람의 선택에 미치는 범위가 넓어지는 정도입니다.",
    "의견과 결정의 무게가 이전보다 커질 가능성이 높습니다. 공식적인 역할이나 축적된 성과를 바탕으로 더 중요한 판단에 참여할 수 있습니다.",
    "자신의 판단이 주변의 결정으로 이어지는 흐름이 강하지 않습니다. 성과를 쌓더라도 영향력으로 연결하려면 신뢰와 공식적인 역할을 먼저 확보할 필요가 있습니다.",
  ),
});

function metricStatusDescriptionEntry(item) {
  for (const key of metricDescriptionKeys(item)) {
    const curated = curatedMetricDescriptionOverrides[key];
    if (curated) return curated;
  }
  const dictionary = window.sajuMetricStatusDescriptions || {};
  const entries = window.sajuMetricStatusDescriptionEntries || [];
  for (const key of metricDescriptionKeys(item)) {
    const source = dictionary[key];
    const entry = Number.isInteger(source) ? entries[source] : source;
    if (entry) return entry;
  }
  return null;
}

const positiveAxisMetricDescriptionAliases = Object.freeze({
  "관계자립성": "상대의존도",
  "이별리스크관리력": "이별위험도",
  "배우자갈등조정력": "배우자충돌도",
  "경쟁대응력": "경쟁노출도",
  "지인손실방어력": "지인피해손실",
});

function positiveAxisMetricStatusDescriptionEntry(item) {
  const dictionary = window.sajuMetricStatusDescriptions || {};
  const entries = window.sajuMetricStatusDescriptionEntries || [];
  const displayKey = normalizeMetricDescriptionKey(item && (item.label || item.title));
  const sourceKey = positiveAxisMetricDescriptionAliases[displayKey];
  if (!sourceKey) return null;
  const source = dictionary[sourceKey];
  const entry = Number.isInteger(source) ? entries[source] : source;
  return entry || null;
}

function annualMetricDescriptionEntry(item, domainKey) {
  const normalizedDomain = String(domainKey || "").trim();
  if (!normalizedDomain) return null;
  for (const key of metricDescriptionKeys(item)) {
    const curated = curatedAnnualMetricDescriptionOverrides[key];
    if (curated) return curated;
  }
  const dictionaries = window.sajuAnnualMetricDescriptions || {};
  const entriesByDomain = window.sajuAnnualMetricDescriptionEntries || {};
  const dictionary = dictionaries[normalizedDomain] || {};
  const entries = entriesByDomain[normalizedDomain] || [];
  for (const key of metricDescriptionKeys(item)) {
    const source = dictionary[key];
    const entry = Number.isInteger(source) ? entries[source] : source;
    if (entry) return entry;
  }
  return null;
}

function annualMetricStatusActionBody(item, domainKey, stateType) {
  if (stateType === "normal") return "";
  const entry = annualMetricDescriptionEntry(item, domainKey);
  if (!entry) return "";
  const entryType = String(entry.type || "").toLowerCase();
  const riskLike = entryType === "risk" || metricPolarity(item) === "risk";
  const body = stateType === "good"
    ? (riskLike ? entry.low : entry.high)
    : (riskLike ? entry.high : entry.low);
  return String(body || "").replace(/\s+/g, " ").trim();
}

function annualMetricStateLead(item, domainKey, score = metricScore(item)) {
  return metricStateLead(item, score);
}

function metricStatusActionBody(item, stateType) {
  if (stateType === "normal") return "";
  const positiveAxisEntry = positiveAxisMetricStatusDescriptionEntry(item);
  const entry = positiveAxisEntry || metricStatusDescriptionEntry(item);
  const riskLike = positiveAxisEntry || metricPolarity(item) === "risk";
  const entryState = riskLike
    ? (stateType === "good" ? "bad" : "good")
    : stateType;
  const body = entry && entry[entryState];
  if (!body) return "";
  const cleanBody = String(body).replace(/\s+/g, " ").trim();
  if (!cleanBody) return "";
  if (entry && entry.direct) return cleanBody;
  const key = `${metricLabel(item, "지표")}:${stateType}:body`;
  if (positiveAxisEntry) {
    const lead = stateType === "good"
      ? stableCopyVariant(key, [
          "이 관리력이 안정적으로 작동하면",
          "이 방어 기준이 분명할수록",
        ])
      : stableCopyVariant(key, [
          "이 관리력이 약해지면",
          "이 방어 기준이 흔들릴 때",
        ]);
    return `${lead} ${cleanBody}`;
  }
  if (riskLike) {
    const lead = stateType === "good"
      ? stableCopyVariant(key, [
          "이 위험이 낮게 유지되면",
          "이 부담이 적게 나타날 때",
        ])
      : stableCopyVariant(key, [
          "이 위험이 커지면",
          "이 부담이 강하게 나타나면",
        ]);
    return `${lead} ${cleanBody}`;
  }
  if (stateType === "good") {
    const lead = stableCopyVariant(key, [
      "이 강점이 살아나면",
      "이 지표가 안정적으로 작동할 때",
      "이 성향이 분명할수록",
    ]);
    return `${lead} ${cleanBody}`;
  }
  const lead = stableCopyVariant(key, [
    "이 부분이 약해지면",
    "이 지표가 흔들릴 때",
    "이 성향이 부담으로 기울면",
  ]);
  return `${lead} ${cleanBody}`;
}

function metricBaseBody(item, fallback = "지표별로 결과가 달라지는 대목입니다.") {
  const directBody = rawFirstSentence(item && (item.summary || item.meaning || item.body || item.definition || item.result || item.focus), "");
  if (positiveAxisMetricStatusDescriptionEntry(item) && directBody) {
    return directBody;
  }
  const statusEntry = metricStatusDescriptionEntry(item);
  if (statusEntry && statusEntry.definition) {
    return String(statusEntry.definition).replace(/\s+/g, " ").trim();
  }
  const label = metricLabel(item, "");
  const rawLabel = displayToken(item && (item.label || item.title || item.key || item.domain)) || "";
  return directBody
    || metricDefaultBodies[label]
    || metricDefaultBodies[rawLabel]
    || fallback;
}

function metricBody(item, fallback = "지표별로 결과가 달라지는 대목입니다.") {
  return metricBodyParagraphs(item, fallback).join(" ");
}

function metricBodyParagraphs(item, fallback = "지표별로 결과가 달라지는 대목입니다.") {
  const score = metricScore(item);
  const stateType = metricJudgmentStateType(item, score);
  const baseBody = metricBaseBody(item, fallback);
  if (stateType === "normal") {
    return [baseBody, metricStateLead(item, score)].filter(Boolean);
  }
  const actionBody = metricStatusActionBody(item, stateType);
  if (!actionBody) return baseBody ? [baseBody] : [];
  const lead = metricStateLead(item, score);
  return [
    baseBody,
    [lead, actionBody].filter(Boolean).join(" "),
  ].filter(Boolean);
}

function renderMetricBodyParagraphs(item, fallback = "지표별로 결과가 달라지는 대목입니다.") {
  const paragraphs = metricBodyParagraphs(item, fallback);
  if (!paragraphs.length) return "";
  return paragraphs
    .map((paragraph, index) => `<p${index ? ' class="metric-action-copy"' : ""}>${escapeHtml(paragraph)}</p>`)
    .join("");
}

function renderAnnualMetricBodyParagraphs(item, domainKey, fallback = "연간 운세 지표입니다.") {
  const entry = annualMetricDescriptionEntry(item, domainKey);
  if (!entry) return renderMetricBodyParagraphs(item, fallback);
  const score = metricScore(item);
  const stateType = metricJudgmentStateType(item, score);
  const displayKey = normalizeMetricDescriptionKey(item && item.label);
  const sourceKey = normalizeMetricDescriptionKey(item && (item.source_label || item.sourceLabel));
  const convertedToPositiveAxis = Boolean(displayKey && sourceKey && displayKey !== sourceKey);
  const displayDefinition = rawFirstSentence(
    item && (item.summary || item.meaning || item.body || item.definition),
    "",
  );
  const baseBody = (convertedToPositiveAxis ? displayDefinition : "")
    || String(entry.definition || "").replace(/\s+/g, " ").trim()
    || displayDefinition
    || metricBaseBody(item, fallback);
  if (stateType === "normal") {
    return [baseBody, metricStateLead(item, score)]
      .filter(Boolean)
      .map((paragraph, index) => `<p${index ? ' class="metric-action-copy"' : ""}>${escapeHtml(paragraph)}</p>`)
      .join("");
  }
  const actionBody = annualMetricStatusActionBody(item, domainKey, stateType);
  const paragraphs = actionBody
    ? [baseBody, [annualMetricStateLead(item, domainKey, score), actionBody].filter(Boolean).join(" ")]
    : [baseBody];
  return paragraphs
    .filter(Boolean)
    .map((paragraph, index) => `<p${index ? ' class="metric-action-copy"' : ""}>${escapeHtml(paragraph)}</p>`)
    .join("");
}

function metricItemsFrom(section, key, limit = 6) {
  return asArray(section && section[key])
    .filter((item) => item && typeof item === "object" && metricLabel(item, ""))
    .slice(0, limit);
}

function renderMetricBar(score) {
  if (!Number.isFinite(score)) return "";
  return renderAggregateGradeBar(metricGrade(score, ""));
}

function renderMetricLevelBadge(level, score) {
  const grade = Number.isFinite(score) ? metricGrade(score, "") : String(level || "").trim();
  return metricGradeRank(grade) >= 0 ? renderAggregateGradeBadge(grade) : "";
}

function contextualDomainBody(item, includeLabel = true) {
  const label = displayToken((item && (item.label || item.domain)) || "해당 영역") || "해당 영역";
  const topicParticle = subjectParticle(label);
  const state = displayToken(item && item.state);
  const subject = includeLabel ? `${label}${topicParticle} ` : "";
  if (state === "긍정") {
    return `${subject}강점이 먼저 드러나는 분야입니다. 타고난 흐름에서도 비교적 복이 붙는 쪽입니다.`;
  }
  if (state === "주의" || state === "부담") {
    return `${subject}먼저 살펴야 할 분야입니다. 운이 강하게 움직일수록 손실과 구설을 줄이는 태도가 필요합니다.`;
  }
  if (state === "혼재") {
    return `${subject}성과와 부담이 함께 걸린 분야입니다. 얻는 것이 커질수록 정리해야 할 조건도 함께 커집니다.`;
  }
  return `${subject}한 가지 기준만으로 판단하기 어려운 분야입니다. 좋은 점과 조심할 점을 함께 봐야 합니다.`;
}

const contextualConceptBank = {
  재생관: {
    body:
      "재생관은 현실의 돈, 자원, 계약 조건이 사회적 책임과 직책으로 이어지는 작용입니다. 이 작용이 분명하면 실리만 좇기보다 공식 기준, 신용, 체면, 직책을 함께 의식합니다. 돈을 벌어도 그것을 사회적 위치와 책임으로 바꾸려는 성향이 강해집니다.",
    keywords: ["현실 감각", "책임 수행력", "제도 친화성", "명분 확보", "실리적 품위", "체면 관리", "명예 지향", "안정된 상승욕", "직책 욕구", "조직 적응력", "관리자 기질"],
  },
  정재생정관: {
    body:
      "정재생정관은 고정 수입, 소유권, 정산 기준이 공식 책임과 직책으로 이어지는 작용입니다. 돈의 흐름을 안정시키고, 그 안정성을 바탕으로 신용과 직업적 평가를 확보하려는 성향이 나타납니다. 즉흥적인 확장보다 분명한 계약, 직함, 책임 범위가 운을 세웁니다.",
    keywords: ["고정 수입", "소유권 의식", "정산 기준", "공식 계약", "신용 관리", "책임 범위", "직책 상승", "평판 안정", "보상 확정", "조직 신뢰"],
  },
  관인상생: {
    body:
      "관인상생은 책임과 질서가 자격, 문서, 학습, 보호 체계로 이어지는 작용입니다. 이 작용이 분명하면 무작정 밀어붙이기보다 명분을 세우고, 절차를 갖추고, 공적인 신뢰를 확보하려는 태도가 강합니다. 직업적으로는 책임을 감당하면서도 자격과 전문성으로 자신을 보호하는 모습이 나타납니다.",
    keywords: ["공적 신뢰", "자격 확보", "문서 기반", "절차 의식", "조직 질서", "책임 감당", "전문성", "학습 능력", "명분", "평판 관리", "제도권 적응"],
  },
  정관생편인: {
    body:
      "정관생편인은 공식 책임이 특수한 지식, 비공식 자료, 깊은 관찰력으로 이어지는 작용입니다. 겉으로는 규칙을 따르는 듯 보여도 내부적으로는 남들이 쉽게 보지 못하는 정보와 해석을 붙잡습니다. 정해진 조직 안에서도 독자적인 전문성을 만들려는 성향이 강해집니다.",
    keywords: ["특수 전문성", "비공식 자료", "깊은 관찰", "조직 내 독자성", "문서 해석", "연구 기질", "자격과 통찰", "내부 정보", "분석 감각", "조용한 영향력"],
  },
  정관극겁재: {
    body:
      "정관극겁재는 규칙과 책임 기준으로 경쟁, 동업, 주변 사람의 침범을 정리하는 작용입니다. 이 작용이 분명하면 사람 사이의 몫이나 권한이 흐려질 때 원칙을 세워 균형을 잡으려 합니다. 가까운 관계라도 일과 돈이 섞이면 기준을 분명히 하려는 태도가 나타납니다.",
    keywords: ["권한 정리", "경쟁 제어", "원칙 확립", "동업 기준", "몫의 구분", "책임 소재", "계약 의식", "조직 질서", "관계 경계", "공정성", "규칙 적용"],
  },
  식상생재: {
    body:
      "식상생재는 말, 기술, 콘텐츠, 서비스처럼 직접 만들어낸 결과물이 돈으로 이어지는 작용입니다. 이 작용이 분명하면 재물은 단순한 행운보다 생산물과 반복 가능한 성과에서 생깁니다. 무엇을 꾸준히 내놓을 수 있는지가 수입의 질을 결정합니다.",
    keywords: ["성과물", "기술 수익", "콘텐츠", "서비스", "반복 판매", "표현력", "생산성", "고객 반응", "실적 전환", "상품화", "수익 모델"],
  },
  식신생편재: {
    body:
      "식신생편재는 안정적인 기술과 결과물이 유동적인 거래, 영업, 현금 흐름으로 이어지는 작용입니다. 이 작용이 분명하면 한 번의 직책보다 시장에서 팔릴 수 있는 결과물이 중요합니다. 손에 익은 기술을 현실의 거래로 바꾸는 감각이 살아납니다.",
    keywords: ["기술 수익", "거래 감각", "현금 흐름", "시장성", "상품화", "영업력", "실무 결과", "고객 확보", "반복 매출", "유연한 수입"],
  },
  편인도식: {
    body:
      "편인도식은 생각, 정보, 특수한 관심이 결과물의 속도를 늦추거나 방향을 바꾸는 작용입니다. 이 작용이 강하면 재능은 있으나 바로 내놓기보다 더 알고, 더 다듬고, 더 검토하려는 경향이 생깁니다. 좋게 쓰면 깊은 연구와 독자적 전문성이 되고, 과하면 실행이 늦어집니다.",
    keywords: ["깊은 사고", "특수 관심", "정보 탐색", "실행 지연", "연구 기질", "독자성", "검토 습관", "감각적 불안", "몰입", "비표준적 재능"],
  },
  식신중첩: {
    body:
      "식신 중첩은 안정적인 표현, 생산, 돌봄, 실무 능력이 반복해서 드러나는 작용입니다. 이 작용이 분명하면 무리하게 튀기보다 꾸준히 만들어내고, 익숙한 방식으로 성과를 쌓는 힘이 강합니다. 반복 가능한 기술과 성실한 결과물이 운의 기반이 됩니다.",
    keywords: ["꾸준한 생산", "실무 능력", "반복 성과", "안정적 표현", "기술 축적", "생활 감각", "성실성", "완성도", "지속성", "돌봄 기질"],
  },
  "식신·상관 병립": {
    body:
      "식신과 상관이 함께 있으면 안정적인 생산성과 강한 표현 욕구가 동시에 나타납니다. 한쪽으로는 꾸준히 만들고, 다른 한쪽으로는 더 선명하게 드러내고 싶어 합니다. 잘 쓰면 창작과 실무가 함께 살아나지만, 기준 없이 과해지면 말과 결과물의 방향이 흔들릴 수 있습니다.",
    keywords: ["표현 욕구", "생산성", "창작력", "기술 발휘", "말의 힘", "성과 노출", "개성", "실무 감각", "독자성", "완성도"],
  },
  "상관·식신 병립": {
    body:
      "상관과 식신이 함께 있으면 말과 표현이 먼저 살아나고, 그 표현을 실제 결과물로 만들려는 힘이 뒤따릅니다. 이 작용은 창의적인 분야, 기획, 콘텐츠, 서비스에서 장점이 됩니다. 다만 표현이 앞서면 안정적인 생산성이 흔들릴 수 있어 기준이 필요합니다.",
    keywords: ["창의성", "표현력", "기획 감각", "콘텐츠", "서비스", "실행력", "결과물", "말의 영향력", "개성", "조율 능력"],
  },
  재극인: {
    body:
      "재극인은 돈, 현실, 성과 요구가 공부, 보호, 명분, 생각의 영역을 누르는 작용입니다. 좋게 쓰면 이론에 머물던 것을 현실 수익과 계약으로 끌어내고, 과하면 문서나 학업, 보호 관계에서 부담이 생깁니다. 현실 감각이 강해질수록 생각의 세계도 검증을 받습니다.",
    keywords: ["현실 검증", "수익 압박", "문서 부담", "성과 요구", "학업 변동", "계약 감각", "실리 판단", "보호 관계", "현금 기준", "이론의 현실화"],
  },
  정재극편인: {
    body:
      "정재극편인은 안정된 돈, 소유권, 생활 기준이 특수한 지식과 독자적 판단을 압박하거나 현실화하는 작용입니다. 이 작용이 분명하면 막연한 감각보다 실제 비용, 계약, 정산, 수익 기준으로 생각을 검증하려 합니다. 좋게 쓰면 전문성과 현실 감각이 붙고, 흐트러지면 돈 문제와 문서 판단이 서로 부담을 만듭니다.",
    keywords: ["현실 검증", "소유권 의식", "정산 기준", "특수 지식", "계약 감각", "문서 판단", "전문성 현실화", "생활 기준", "수익 압박", "검증 욕구", "돈과 정보"],
  },
  겁재극정재: {
    body:
      "겁재극정재는 주변 사람, 경쟁, 공동 책임이 안정된 돈과 소유 기준을 건드리는 작용입니다. 이 작용이 드러나면 가까운 관계와 돈이 섞일 때 정산, 몫, 권리 기준이 중요해집니다. 좋게 쓰면 시장 감각과 대중 접점이 살아나지만, 흐트러지면 손재와 분배 갈등이 커집니다.",
    keywords: ["몫 의식", "경쟁 민감", "소유권 방어", "정산 기준", "공동 자금", "동업 경계", "대중 영업", "분배 갈등", "손재", "권리 침범", "신뢰 검증"],
  },
  겁재극정재극편인: {
    body:
      "겁재극정재극편인은 사람과 공동 자금의 압력이 안정된 돈과 특수한 판단 영역까지 함께 흔드는 작용입니다. 관계 속 금전 문제와 정보 해석이 얽히기 쉬워, 설득력과 통찰은 살아나지만 검증 없는 확신과 정산 불명확성이 동시에 위험이 됩니다. 돈, 사람, 문서 판단을 한 기준으로 묶어야 안정됩니다.",
    keywords: ["직관적 판단", "경쟁 민감", "공동 자금", "정산 불명확", "특수 자문", "시장 감각", "신뢰 검증", "손재", "설득 관계", "확신 과장", "정보 검증"],
  },
};

const contextualKeywordGroupOrder = ["기질", "재능", "관계", "직업", "리스크"];

const contextualConceptGroupBank = {
  "비견·겁재": {
    기질: ["독립성", "승부욕", "자기주장"],
    재능: ["무리 장악", "생존력", "동료 활용"],
    관계: ["친구·형제 문제", "동업 긴장"],
    직업: ["대중 상대", "경쟁 시장"],
    리스크: ["몫 다툼", "군겁쟁재"],
  },
  "겁재·비견": {
    기질: ["독립성", "승부욕", "자기주장"],
    재능: ["무리 장악", "생존력", "동료 활용"],
    관계: ["친구·형제 문제", "동업 긴장"],
    직업: ["대중 상대", "경쟁 시장"],
    리스크: ["몫 다툼", "군겁쟁재"],
  },
  비겁극재: {
    기질: ["자기 몫 의식", "경쟁 민감", "소유권 방어", "독립성"],
    재능: ["분배 기준", "정산 감각", "협상력", "시장 경쟁력"],
    관계: ["동업 경계", "공동 자금", "역할 분리", "신뢰 검증"],
    직업: ["영업 경쟁", "지분 협상", "수익 배분", "독립 사업"],
    리스크: ["손재", "몫 다툼", "명의 분쟁", "관계 손실"],
  },
  관성극비겁: {
    기질: ["원칙 의식", "책임 기준", "권한 의식", "공정성"],
    재능: ["경쟁 제어", "역할 구분", "규칙 적용", "책임 정리"],
    관계: ["관계 경계", "약속 기준", "권리 조율", "질서 유지"],
    직업: ["조직 관리", "권한 배분", "계약 기준", "통솔력"],
    리스크: ["원칙 충돌", "권위 의식", "관계 냉각", "통제 과다"],
  },
  인성생비겁: {
    기질: ["자기 확신", "학습 지향", "보호 의식", "기준 형성"],
    재능: ["지식 축적", "자격 활용", "자료 해석", "동료 지원"],
    관계: ["연대 의식", "보호 관계", "신뢰 기반", "동료 결속"],
    직업: ["교육", "연구", "문서 업무", "전문 자격"],
    리스크: ["자기 확신 과다", "의존 관계", "실행 지연", "편 가르기"],
  },
  식신제살: {
    기질: ["침착한 대응", "책임 감당", "실무 중심", "문제 해결"],
    재능: ["위험 통제", "현장 대응", "기술 숙련", "압박 처리"],
    관계: ["강한 상대 조율", "갈등 완화", "보호 역할", "신뢰 확보"],
    직업: ["현장 실무", "위기 관리", "전문 기술", "책임 직무"],
    리스크: ["과로", "책임 과다", "기술 의존", "압박 누적"],
  },
  인성제식: {
    기질: ["검토 우선", "내적 기준", "신중성", "학습 지향"],
    재능: ["자료 검증", "문서 정리", "품질 관리", "이론화"],
    관계: ["표현 절제", "거리 유지", "관찰 후 신뢰", "신중한 소통"],
    직업: ["연구", "교육", "심사", "문서 직무"],
    리스크: ["실행 지연", "표현 억제", "결과물 지연", "과잉 검토"],
  },
  식상극관: {
    기질: ["비판 의식", "독자성", "표현 욕구", "개선 지향"],
    재능: ["문제 발견", "제도 개선", "논리 반박", "창의적 해결"],
    관계: ["직설적 소통", "상하 관계 긴장", "기준 충돌", "설득"],
    직업: ["감사", "기획", "개선 업무", "자율 직무"],
    리스크: ["권위 충돌", "평가 손상", "구설", "직업 변동"],
  },
  상관견관: {
    기질: ["권위 의심", "비판성", "독자성", "표현 욕구"],
    재능: ["제도 개선", "문제 발견", "논리 반박", "개혁 기획"],
    관계: ["직설 화법", "상하 갈등", "기준 충돌", "거리 확대"],
    직업: ["감사", "개선", "기획", "자율 직무"],
    리스크: ["구설", "평가 손상", "권위 충돌", "직장 변동"],
  },
  재생관: {
    기질: ["현실 감각", "책임 의식", "체면 관리", "안정된 상승욕"],
    재능: ["제도 활용", "보상 구조 설계", "실리적 판단", "직책 수행"],
    관계: ["신뢰 확보", "약속 이행", "상하 관계 조율"],
    직업: ["조직 적응력", "관리자 기질", "직책 욕구", "명분 확보"],
    리스크: ["책임 과다", "체면 지출", "권한 없는 부담", "실리와 명분 충돌"],
  },
  정재생정관: {
    기질: ["성실한 축적", "소유권 의식", "신용 중시", "책임감"],
    재능: ["정산 기준", "계약 관리", "보상 확정", "평판 안정"],
    관계: ["약속 이행", "공식 관계", "신뢰 유지"],
    직업: ["직책 상승", "조직 신뢰", "책임 범위", "고정 역할"],
    리스크: ["계산 과다", "체면 부담", "책임 고착", "유연성 부족"],
  },
  관인상생: {
    기질: ["명분 의식", "절차 의식", "품위 유지", "안정 지향"],
    재능: ["자격 확보", "문서 기반", "학습 능력", "전문성 축적"],
    관계: ["공적 신뢰", "윗사람 신뢰", "제도권 관계"],
    직업: ["조직 질서", "책임 감당", "평판 관리", "제도권 적응"],
    리스크: ["절차 의존", "결정 지연", "체면 부담", "권위 의식"],
  },
  정관생편인: {
    기질: ["깊은 관찰", "조용한 영향력", "독자성", "연구 기질"],
    재능: ["특수 전문성", "문서 해석", "분석 감각", "내부 정보 활용"],
    관계: ["거리 있는 신뢰", "조직 내 독자성", "선별적 관계"],
    직업: ["연구 직무", "기획 분석", "자격과 통찰", "비공식 자료 활용"],
    리스크: ["고립감", "과도한 해석", "실행 지연", "불신 확대"],
  },
  정관극겁재: {
    기질: ["원칙 확립", "공정성", "관계 경계", "권한 의식"],
    재능: ["경쟁 제어", "몫의 구분", "책임 소재 정리", "동업 기준"],
    관계: ["관계 경계", "약속 기준", "권리 조율"],
    직업: ["조직 질서", "계약 의식", "권한 정리", "규칙 적용"],
    리스크: ["원칙 충돌", "인정 부족", "관계 냉각", "힘겨루기"],
  },
  식상생재: {
    기질: ["표현 욕구", "생산성", "고객 반응 의식", "성과 지향"],
    재능: ["기술 수익", "콘텐츠", "서비스", "상품화"],
    관계: ["고객 확보", "반응 관리", "평판 확산"],
    직업: ["반복 판매", "수익 모델", "실적 전환", "전문 서비스"],
    리스크: ["성과 압박", "과도한 노출", "수익화 지연", "완성도 부담"],
  },
  식신생편재: {
    기질: ["현금 감각", "유연한 수입", "시장 대응", "실무 감각"],
    재능: ["기술 수익", "거래 감각", "상품화", "영업력"],
    관계: ["고객 확보", "거래처 확장", "시장 반응"],
    직업: ["반복 매출", "외주 수익", "서비스 판매", "유통 감각"],
    리스크: ["회수 지연", "거래 변동", "현금 흐름 불안", "확장 과다"],
  },
  편인도식: {
    기질: ["깊은 사고", "특수 관심", "몰입", "감각적 불안"],
    재능: ["정보 탐색", "연구 기질", "독자성", "비표준적 재능"],
    관계: ["거리감", "오해 가능성", "선별적 소통"],
    직업: ["전문 연구", "자료 분석", "기획 검토", "비정형 업무"],
    리스크: ["실행 지연", "검토 과다", "결과물 지연", "고립"],
  },
  식신중첩: {
    기질: ["꾸준함", "성실성", "생활 감각", "돌봄 기질"],
    재능: ["실무 능력", "기술 축적", "반복 성과", "완성도"],
    관계: ["안정적 표현", "신뢰 형성", "생활형 배려"],
    직업: ["꾸준한 생산", "서비스", "교육·돌봄", "반복 업무"],
    리스크: ["안주", "과소 표현", "소비 증가", "변화 둔감"],
  },
  "식신·상관 병립": {
    기질: ["표현 욕구", "개성", "생산성", "독자성"],
    재능: ["창작력", "기술 발휘", "기획 감각", "성과 노출"],
    관계: ["말의 힘", "반응 유도", "인상 형성"],
    직업: ["콘텐츠", "서비스", "실무 기획", "창작 업무"],
    리스크: ["표현 과다", "방향 흔들림", "기준 약화", "평판 충돌"],
  },
  "상관·식신 병립": {
    기질: ["창의성", "표현력", "개성", "조율 욕구"],
    재능: ["기획 감각", "콘텐츠", "실행력", "결과물"],
    관계: ["말의 영향력", "설득", "반응 조율"],
    직업: ["창작 업무", "기획", "서비스", "브랜딩"],
    리스크: ["표현이 앞섬", "권위 충돌", "완성도 저하", "말의 부담"],
  },
  재극인: {
    기질: ["현실 검증", "실리 판단", "독립성", "성과 요구"],
    재능: ["계약 감각", "문서 비용화", "이론의 현실화", "수익 전환"],
    관계: ["보호 관계", "가족 부담", "금전 기준"],
    직업: ["정산", "계약", "성과 관리", "실무 수익"],
    리스크: ["문서 부담", "학업 변동", "보호 약화", "수익 압박"],
  },
  정재극편인: {
    기질: ["현실 검증", "소유권 의식", "생활 기준", "독자적 판단"],
    재능: ["계약 감각", "문서 판단", "전문성 현실화", "정산 기준"],
    관계: ["보호 관계", "금전 기준", "정보 검증", "거리 있는 신뢰"],
    직업: ["전문 자문", "계약 검토", "자료 분석", "수익 구조화"],
    리스크: ["문서 부담", "판단 과신", "비용 압박", "정보 불균형"],
  },
  겁재극정재: {
    기질: ["몫 의식", "경쟁 민감", "소유권 방어", "현실 감각"],
    재능: ["대중 영업", "생활 시장 감각", "분배 기준", "정산 감각"],
    관계: ["가까운 사람 변수", "동업 경계", "몫의 협상", "신뢰 검증"],
    직업: ["공동 사업", "영업·판매", "거래 조율", "수익 배분"],
    리스크: ["손재", "정산 갈등", "공동 자금 손실", "권리 침범"],
  },
  겁재극정재극편인: {
    기질: ["직관적 판단", "경쟁 민감", "독자성", "현실 압박"],
    재능: ["통찰 전달", "특수 자문", "시장 감각", "숨은 돈 분석"],
    관계: ["사람 변수", "설득 관계", "정산 기준", "신뢰 검증"],
    직업: ["상담·자문", "영업형 전문성", "비공식 정보 분석", "거래 조율"],
    리스크: ["확신 과장", "손재", "정산 불명확", "고립감"],
  },
};

const gyeokgukConceptBank = {
  비견: {
    body:
      "비견격은 자기 기준, 독립성, 동료와의 병립이 격국의 중심에 놓이는 구조입니다. 이 격은 혼자 버티는 힘과 같은 편을 만들 힘을 함께 보지만, 몫과 권한이 흐려질 때 경쟁으로 바뀌기 쉽습니다. 강하면 주체성과 지속성이 살아나고, 흐트러지면 고집과 힘겨루기가 먼저 드러납니다.",
    keywords: ["자기 기준", "독립성", "동료 의식", "주체성", "경쟁 관계", "몫의 구분", "지속력", "협업 기준", "권한 의식", "자립 성향"],
  },
  겁재: {
    body:
      "겁재격은 경쟁, 분배, 동업, 주변 사람과의 힘 관계가 격국의 중심에 놓이는 구조입니다. 이 격은 사람을 통해 판이 커질 수 있으나, 돈과 권한이 섞이면 손실과 다툼도 빨라집니다. 강하면 돌파력과 동원력이 생기고, 흐트러지면 내 몫을 지키는 문제가 반복됩니다.",
    keywords: ["경쟁", "분배", "동업", "동원력", "돌파력", "몫의 다툼", "사람 변수", "공동 자원", "권리 의식", "재물 방어"],
  },
  식신: {
    body:
      "식신격은 꾸준한 생산, 기술, 돌봄, 결과물이 격국의 중심에 놓이는 구조입니다. 이 격은 말보다 실제로 만들어내는 힘을 중시하며, 반복 가능한 산출물이 재물과 평판의 근거가 됩니다. 강하면 안정적인 실력과 생활력이 살아나고, 흐트러지면 안주와 과도한 소비가 나타납니다.",
    keywords: ["생산성", "기술", "결과물", "생활력", "꾸준함", "서비스", "교육", "돌봄", "반복 수익", "완성도"],
  },
  상관: {
    body:
      "상관격은 표현, 개선, 비판, 독창성이 격국의 중심에 놓이는 구조입니다. 이 격은 기존 규칙을 그대로 따르기보다 문제를 드러내고 바꾸려는 힘이 강합니다. 강하면 기획력과 표현력이 살아나고, 흐트러지면 말과 태도가 권위나 제도와 충돌하기 쉽습니다.",
    keywords: ["표현력", "개선 능력", "비판 정신", "기획력", "독창성", "말의 힘", "제도 충돌", "성과 노출", "창작성", "개혁 성향"],
  },
  편재: {
    body:
      "편재격은 외부 기회, 거래, 시장성, 큰 자금의 움직임이 격국의 중심에 놓이는 구조입니다. 이 격은 안정된 월급보다 사람과 시장을 읽고 기회를 잡는 감각을 중시합니다. 강하면 사업성, 영업력, 자금 회전이 살아나고, 흐트러지면 확장 과다와 회수 문제가 생깁니다.",
    keywords: ["사업성", "거래 감각", "시장 대응", "외부 기회", "자금 회전", "영업력", "협상", "확장성", "회수 기준", "투자 감각"],
  },
  정재: {
    body:
      "정재격은 고정 수입, 소유권, 정산, 생활 관리가 격국의 중심에 놓이는 구조입니다. 이 격은 크게 벌어 흩뿌리기보다 안정적으로 모으고 지키는 힘을 중시합니다. 강하면 성실한 축적과 신용이 살아나고, 흐트러지면 계산이 많아지거나 돈으로 책임을 증명하려는 태도가 나타납니다.",
    keywords: ["고정 수입", "소유권", "정산", "생활 관리", "축적", "신용", "현금 기준", "가계 운영", "재산 보존", "책임감"],
  },
  편관: {
    body:
      "편관격은 압박, 경쟁, 위험 처리, 강한 책임이 격국의 중심에 놓이는 구조입니다. 이 격은 편한 환경보다 어려운 일을 감당하면서 실력이 드러나는 쪽입니다. 강하면 위기 대응과 실행력이 살아나고, 흐트러지면 부담, 사고, 권위 충돌로 나타납니다.",
    keywords: ["위기 대응", "경쟁", "강한 책임", "실행력", "위험 관리", "압박 처리", "규율", "현장성", "결단력", "권위 충돌"],
  },
  정관: {
    body:
      "정관격은 직책, 규칙, 평판, 공적 신뢰가 격국의 중심에 놓이는 구조입니다. 이 격은 개인적 욕심보다 사회적으로 인정되는 책임과 질서를 중시합니다. 강하면 명예와 신뢰가 붙고, 흐트러지면 체면, 평가, 상하관계의 부담이 커집니다.",
    keywords: ["직책", "규칙", "공적 신뢰", "평판", "명예", "책임 범위", "조직 질서", "절차", "상하관계", "사회적 인정"],
  },
  편인: {
    body:
      "편인격은 특수한 지식, 독자적 해석, 깊은 관찰, 비표준적 감각이 격국의 중심에 놓이는 구조입니다. 이 격은 일반적인 길보다 자기만의 관점과 전문성을 통해 힘을 얻습니다. 강하면 연구력과 통찰이 살아나고, 흐트러지면 실행 지연과 고립감이 나타납니다.",
    keywords: ["특수 지식", "독자성", "관찰력", "연구 기질", "비표준 감각", "전문성", "통찰", "몰입", "실행 지연", "고립감"],
  },
  정인: {
    body:
      "정인격은 학습, 문서, 자격, 보호, 안정된 신뢰가 격국의 중심에 놓이는 구조입니다. 이 격은 무리한 돌파보다 근거를 갖추고 인정받는 과정을 중시합니다. 강하면 자격과 평판이 안정되고, 흐트러지면 생각이 많아 실행이 늦어질 수 있습니다.",
    keywords: ["학습", "문서", "자격", "보호", "신뢰", "근거", "안정성", "명분", "제도권", "전문 자격"],
  },
};

const monthConceptBank = {
  子: {
    body:
      "자월은 한겨울의 수기가 왕한 월령입니다. 기운이 밖으로 펼쳐지기보다 안으로 모이고, 정보와 감정, 준비와 저장의 성격이 강해집니다. 이 월령에서는 눈에 보이는 성과보다 잠긴 기운이 언제 발동되는지가 중요합니다.",
    keywords: ["한겨울", "저장성", "정보", "감정의 깊이", "준비", "잠복", "유통", "지혜", "응축", "발동 시점"],
  },
  丑: {
    body:
      "축월은 겨울의 끝에서 습토가 기운을 붙잡는 월령입니다. 마무리, 축적, 보관, 현실적 부담이 함께 생기며, 성과가 늦더라도 기반을 만드는 힘이 있습니다. 이 월령에서는 속도보다 오래 버틸 수 있는 구조가 중요합니다.",
    keywords: ["습토", "축적", "보관", "마무리", "기반", "지연", "생활 책임", "현실 부담", "저장", "인내"],
  },
  寅: {
    body:
      "인월은 초봄의 목기가 일어나는 월령입니다. 시작, 성장, 기획, 추진의 힘이 강해지고, 아직 완성되지 않은 일을 밀어 올리는 성향이 나타납니다. 이 월령에서는 가능성을 실제 성과로 키우는 방향이 중요합니다.",
    keywords: ["초봄", "시작", "성장", "기획", "추진", "발아", "확장성", "개척", "가능성", "도전"],
  },
  卯: {
    body:
      "묘월은 봄의 목기가 가장 순하게 펼쳐지는 월령입니다. 성장, 관계, 미감, 조율, 확장의 성격이 강하며 사람과 환경의 반응을 예민하게 읽습니다. 이 월령에서는 부드러운 확장력과 지속성이 핵심입니다.",
    keywords: ["중춘", "성장", "관계", "미감", "조율", "확장", "부드러움", "사회성", "감각", "지속성"],
  },
  辰: {
    body:
      "진월은 봄의 끝에서 습토가 목의 기운을 거두고 다음 계절로 넘기는 월령입니다. 전환, 조정, 저장, 현실화의 성격이 강하며 여러 기운이 함께 섞입니다. 이 월령에서는 방향을 정리하고 기반으로 묶는 힘이 중요합니다.",
    keywords: ["전환", "조정", "습토", "저장", "현실화", "복합성", "기반 정리", "계절 전환", "중재", "축적"],
  },
  巳: {
    body:
      "사월은 초여름의 화기가 빠르게 올라오는 월령입니다. 표현, 활동, 기술, 명성, 속도의 성격이 강해지며 숨은 기운이 밖으로 드러나기 시작합니다. 이 월령에서는 열기를 성과와 기술로 정리하는 힘이 중요합니다.",
    keywords: ["초여름", "표현", "활동성", "기술", "명성", "속도", "노출", "열기", "성과화", "발현"],
  },
  午: {
    body:
      "오월은 한여름의 화기가 정점에 이른 월령입니다. 존재감, 주목, 명예욕, 열정, 경쟁심이 강하게 드러납니다. 이 월령에서는 강한 기운을 성과와 책임으로 바꾸는 기준이 중요합니다.",
    keywords: ["한여름", "존재감", "주목", "명예", "열정", "경쟁", "표현력", "강한 양기", "성과 욕구", "책임화"],
  },
  未: {
    body:
      "미월은 여름의 끝에서 조토가 열기를 품고 결실을 준비하는 월령입니다. 생활 기반, 가족, 생산, 관리, 현실 책임이 강해집니다. 이 월령에서는 만들어낸 것을 오래 남기는 관리 능력이 중요합니다.",
    keywords: ["늦여름", "조토", "결실", "생활 기반", "가족", "생산", "관리", "책임", "안정", "보존"],
  },
  申: {
    body:
      "신월은 초가을의 금기가 일어나 사물을 가르고 평가하는 월령입니다. 기술, 경쟁, 판단, 조직 평가, 이동과 변화의 성격이 강합니다. 이 월령에서는 빠른 판단을 신뢰와 권한으로 연결하는 힘이 중요합니다.",
    keywords: ["초가을", "기술", "판단", "경쟁", "평가", "이동", "선별", "조직성", "기준", "권한"],
  },
  酉: {
    body:
      "유월은 가을의 금기가 선명하게 완성되는 월령입니다. 품질, 심사, 미감, 기준, 정밀함, 사회적 평가가 강하게 작동합니다. 이 월령에서는 완성도와 기준이 곧 신뢰와 가치로 이어집니다.",
    keywords: ["한가을", "품질", "심사", "미감", "기준", "정밀함", "완성도", "평가", "브랜드", "가치"],
  },
  戌: {
    body:
      "술월은 가을의 끝에서 조토가 금기를 거두고 신념과 보관의 성격을 세우는 월령입니다. 정리, 원칙, 책임, 보존, 오래 남는 체계가 중요해집니다. 이 월령에서는 굳은 기준을 현실에 맞게 풀어내는 힘이 필요합니다.",
    keywords: ["가을 끝", "조토", "정리", "원칙", "책임", "보존", "신념", "체계", "완결", "현실 조정"],
  },
  亥: {
    body:
      "해월은 초겨울의 수기가 시작되는 월령입니다. 이동, 학습, 상상, 관계의 숨은 흐름, 회복과 잠복의 성격이 강해집니다. 이 월령에서는 보이지 않는 가능성을 현실의 방향으로 끌어올리는 힘이 중요합니다.",
    keywords: ["초겨울", "이동", "학습", "상상력", "회복", "잠복", "관계 흐름", "정보", "유연성", "가능성"],
  },
};

const elementCombinationConceptBank = {
  木火: {
    body:
      "목화 배합은 성장과 표현이 이어지는 물상입니다. 생각, 기획, 배움이 말과 노출, 발표와 콘텐츠로 드러납니다. 강하면 설득력과 창작성이 살아나고, 과하면 말과 계획이 앞서 지속성이 약해질 수 있습니다.",
    keywords: ["기획", "표현", "발표", "콘텐츠", "설득", "교육", "창작", "성장성", "노출", "확산"],
  },
  火土: {
    body:
      "화토 배합은 표현과 명성이 기반, 신뢰, 축적으로 굳어지는 물상입니다. 밖으로 드러난 활동이 생활 기반과 책임으로 이어집니다. 강하면 브랜드와 안정성이 생기고, 과하면 열기가 굳어 고집과 피로로 나타날 수 있습니다.",
    keywords: ["브랜드", "신뢰", "축적", "생활 기반", "책임", "평판", "관리", "안정성", "결실", "피로 관리"],
  },
  土金: {
    body:
      "토금 배합은 기반과 관리가 기준, 기술, 성과물로 정리되는 물상입니다. 흩어진 일을 체계화하고 쓸모 있는 형태로 만드는 힘이 있습니다. 강하면 품질과 시스템이 살아나고, 과하면 규정과 통제가 답답해질 수 있습니다.",
    keywords: ["시스템", "품질", "관리", "기준", "기술", "성과물", "회계", "심사", "자산화", "정리 능력"],
  },
  金水: {
    body:
      "금수 배합은 기준과 기술이 정보, 유통, 전략으로 이어지는 물상입니다. 분석한 것을 흐르게 만들고, 문서와 데이터가 이동성과 결합합니다. 강하면 판단력과 정보력이 살아나고, 과하면 계산은 많아도 결단이 늦어질 수 있습니다.",
    keywords: ["분석", "정보", "전략", "유통", "문서", "데이터", "판단력", "금융", "기술 활용", "결단"],
  },
  水木: {
    body:
      "수목 배합은 정보와 학습이 성장, 기획, 확장으로 이어지는 물상입니다. 배운 것을 새 일로 키우고, 관계와 이동 속에서 기회를 만듭니다. 강하면 기획력과 흡수력이 살아나고, 과하면 가능성은 많으나 결실이 늦어질 수 있습니다.",
    keywords: ["학습", "기획", "확장", "흡수력", "관계", "이동", "아이디어", "성장", "기회 포착", "결실"],
  },
  木土: {
    body:
      "목토 배합은 성장하려는 힘이 현실의 기반과 부딪히는 물상입니다. 새 일을 시작하고 싶어도 토대, 책임, 생활 조건을 함께 고려해야 합니다. 잘 쓰이면 개척과 안정이 함께 가고, 어긋나면 무리한 확장이나 현실 부담이 커집니다.",
    keywords: ["개척", "현실 기반", "생활 조건", "책임", "확장 부담", "토지·자산", "기획의 현실화", "관리", "정착", "조정"],
  },
  火金: {
    body:
      "화금 배합은 표현과 열기가 기준, 기술, 평가와 맞서는 물상입니다. 잘 쓰이면 금을 제련하듯 재능과 기술이 선명해지고, 어긋나면 말과 평판, 규칙 사이의 충돌이 생깁니다. 이 배합은 드러내는 힘과 다듬는 힘을 함께 보아야 합니다.",
    keywords: ["제련", "기술", "평가", "표현", "명성", "규칙 충돌", "완성도", "경쟁", "선명함", "평판 관리"],
  },
  土水: {
    body:
      "토수 배합은 기반과 책임이 돈, 정보, 감정의 흐름을 제어하는 물상입니다. 잘 쓰이면 자금과 정보를 관리하고, 어긋나면 막힘과 지연, 감정의 정체로 나타납니다. 이 배합은 흐름을 막는 것이 아니라 필요한 곳에 머물게 하는 힘을 봅니다.",
    keywords: ["자금 관리", "정보 통제", "감정 조절", "저장", "지연", "부동산", "책임", "유동성 관리", "현금 흐름", "안정"],
  },
  水火: {
    body:
      "수화 배합은 차가운 판단과 뜨거운 표현이 마주 보는 물상입니다. 잘 쓰이면 감정과 이성이 균형을 이루고, 어긋나면 속마음과 겉표현이 엇갈릴 수 있습니다. 이 배합은 온도 차가 운의 체감과 관계 반응을 크게 바꿉니다.",
    keywords: ["감정과 이성", "온도 차", "표현", "관찰", "관계 반응", "긴장", "조율", "명예와 내면", "속마음", "균형"],
  },
  金木: {
    body:
      "금목 배합은 기준과 절제가 성장하려는 힘을 다듬는 물상입니다. 잘 쓰이면 가지치기처럼 방향을 잡고 실력을 정제하지만, 어긋나면 통제와 압박으로 성장성이 꺾일 수 있습니다. 이 배합은 절제와 확장의 균형을 봅니다.",
    keywords: ["가지치기", "기준", "성장 조절", "실력 정제", "절제", "압박", "전문성", "경쟁", "방향 설정", "성장성"],
  },
};

const branchRelationConceptBank = {
  합: {
    body:
      "지지의 합은 현실 조건이 서로 묶이고 결속되는 작용입니다. 사람, 일, 장소, 조건이 쉽게 연결되며 특정 방향으로 힘이 모입니다. 좋은 구조를 합하면 지속력이 생기고, 부담스러운 구조를 합하면 빠져나오기 어려운 묶임이 됩니다.",
    keywords: ["결속", "연결", "협력", "관계 형성", "조건 결합", "지속성", "생활권", "공동 작용", "묶임", "방향성"],
  },
  충: {
    body:
      "지지의 충은 현실 조건이 움직이고 부딪히며 변화를 일으키는 작용입니다. 이동, 이직, 이사, 관계 변화처럼 정지된 것이 흔들리며 사건이 드러납니다. 필요한 글자가 충으로 발동하면 전환이 되고, 불필요한 글자가 충으로 흔들리면 손실과 마찰이 됩니다.",
    keywords: ["변동", "이동", "전환", "충돌", "이직", "이사", "관계 변화", "사건 발동", "분리", "방향 전환"],
  },
  형: {
    body:
      "지지의 형은 겉으로 크게 깨지기보다 내부 압박과 절차적 긴장이 쌓이는 작용입니다. 책임, 규정, 법적 절차, 심리적 부담처럼 스스로를 조이거나 관계 안에서 압력이 생깁니다. 필요한 형은 훈련과 절제가 되고, 과한 형은 피로와 갈등이 됩니다.",
    keywords: ["내부 압박", "절차", "책임", "규정", "심리 부담", "훈련", "절제", "긴장", "갈등", "법적 문제"],
  },
  파: {
    body:
      "지지의 파는 겉으로 유지되던 조건에 균열이 생기는 작용입니다. 약속, 신뢰, 관계, 자금 흐름이 예상보다 쉽게 깨질 수 있습니다. 좋은 구조에서는 낡은 조건을 정리하는 계기가 되고, 나쁜 구조에서는 약속 파기와 손상으로 드러납니다.",
    keywords: ["균열", "약속 파기", "신뢰 손상", "관계 손상", "조건 변화", "정리", "손실", "예상 밖 변수", "불안정", "재조정"],
  },
  해: {
    body:
      "지지의 해는 겉으로 큰 충돌 없이 은근한 손상과 오해가 생기는 작용입니다. 말하지 않은 불만, 미뤄진 약속, 애매한 책임처럼 시간이 지나며 불신이 쌓입니다. 이 작용은 작아 보여도 방치하면 관계와 일의 지속력을 약하게 만듭니다.",
    keywords: ["은근한 손상", "오해", "불신", "지연", "미뤄진 약속", "책임 회피", "관계 피로", "소모", "숨은 변수", "정리 필요"],
  },
  혼재: {
    body:
      "지지 관계가 혼재되면 결속과 변동, 압박과 균열이 함께 작동합니다. 한쪽에서는 관계와 조건이 묶이고, 다른 한쪽에서는 움직임과 마찰이 생깁니다. 이때는 단순히 좋고 나쁨보다 어떤 글자가 필요한지, 어떤 글자가 부담인지가 핵심입니다.",
    keywords: ["결속과 변동", "복합 작용", "관계 변수", "조건 변화", "압박", "균열", "희기 판단", "발동 조건", "현실 사건", "조정"],
  },
};

function normalizedConceptKey(value) {
  return String(value || "").replace(/\s+/g, "").replace(/[ㆍ·]/g, "·").trim();
}

const myungriConceptDescriptionBank = {
  "목木": "목은 시작하고 자라며, 자기 가능성을 밖으로 뻗어내는 기운입니다. 기획력·교육 감각 측면이 실제 장점으로 작동하는 한편, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "木": "목은 시작하고 자라며, 자기 가능성을 밖으로 뻗어내는 기운입니다. 기획력·교육 감각 측면이 실제 장점으로 작동하는 한편, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "木목": "목은 시작하고 자라며, 자기 가능성을 밖으로 뻗어내는 기운입니다. 기획력·교육 감각 측면이 실제 장점으로 작동하는 한편, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "목": "목은 시작하고 자라며, 자기 가능성을 밖으로 뻗어내는 기운입니다. 기획력·교육 감각 측면이 실제 장점으로 작동하는 한편, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "목(木)": "목은 시작하고 자라며, 자기 가능성을 밖으로 뻗어내는 기운입니다. 기획력·교육 감각 측면이 실제 장점으로 작동하는 한편, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "火화": "화는 드러내고 비추며, 자기 존재를 사람들 앞에서 확인하려는 기운입니다. 특히 말과 설득·분위기 장악 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "화火": "화는 드러내고 비추며, 자기 존재를 사람들 앞에서 확인하려는 기운입니다. 특히 말과 설득·분위기 장악 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "火": "화는 드러내고 비추며, 자기 존재를 사람들 앞에서 확인하려는 기운입니다. 특히 말과 설득·분위기 장악 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "화": "화는 드러내고 비추며, 자기 존재를 사람들 앞에서 확인하려는 기운입니다. 특히 말과 설득·분위기 장악 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "화(火)": "화는 드러내고 비추며, 자기 존재를 사람들 앞에서 확인하려는 기운입니다. 특히 말과 설득·분위기 장악 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "토": "토는 받아들이고 묶어두며, 생활과 책임을 현실의 형태로 만드는 기운입니다. 특히 관리 능력·중재 능력 측면에 힘이 실리며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "土": "토는 받아들이고 묶어두며, 생활과 책임을 현실의 형태로 만드는 기운입니다. 특히 관리 능력·중재 능력 측면에 힘이 실리며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "土토": "토는 받아들이고 묶어두며, 생활과 책임을 현실의 형태로 만드는 기운입니다. 특히 관리 능력·중재 능력 측면에 힘이 실리며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "토土": "토는 받아들이고 묶어두며, 생활과 책임을 현실의 형태로 만드는 기운입니다. 특히 관리 능력·중재 능력 측면에 힘이 실리며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "토(土)": "토는 받아들이고 묶어두며, 생활과 책임을 현실의 형태로 만드는 기운입니다. 특히 관리 능력·중재 능력 측면에 힘이 실리며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "금": "금은 가르고 다듬고, 무엇이 맞고 틀린지 기준을 세우는 기운입니다. 정밀함·품질 관리 측면이 실제 장점으로 작동하는 한편, 판단이 날카로워지면 말과 관계가 지나치게 차가워질 수 있습니다.",
  "금(金)": "금은 가르고 다듬고, 무엇이 맞고 틀린지 기준을 세우는 기운입니다. 정밀함·품질 관리 측면이 실제 장점으로 작동하는 한편, 판단이 날카로워지면 말과 관계가 지나치게 차가워질 수 있습니다.",
  "금金": "금은 가르고 다듬고, 무엇이 맞고 틀린지 기준을 세우는 기운입니다. 정밀함·품질 관리 측면이 실제 장점으로 작동하는 한편, 판단이 날카로워지면 말과 관계가 지나치게 차가워질 수 있습니다.",
  "金금": "금은 가르고 다듬고, 무엇이 맞고 틀린지 기준을 세우는 기운입니다. 정밀함·품질 관리 측면이 실제 장점으로 작동하는 한편, 판단이 날카로워지면 말과 관계가 지나치게 차가워질 수 있습니다.",
  "金": "금은 가르고 다듬고, 무엇이 맞고 틀린지 기준을 세우는 기운입니다. 정밀함·품질 관리 측면이 실제 장점으로 작동하는 한편, 판단이 날카로워지면 말과 관계가 지나치게 차가워질 수 있습니다.",
  "수水": "수는 기억하고 흘러가며, 보이지 않는 정보와 감정을 저장하는 기운입니다. 삶에서는 정보 감각·해석 능력 쪽으로 강점이 드러나지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "수": "수는 기억하고 흘러가며, 보이지 않는 정보와 감정을 저장하는 기운입니다. 삶에서는 정보 감각·해석 능력 쪽으로 강점이 드러나지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "水수": "수는 기억하고 흘러가며, 보이지 않는 정보와 감정을 저장하는 기운입니다. 삶에서는 정보 감각·해석 능력 쪽으로 강점이 드러나지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "水": "수는 기억하고 흘러가며, 보이지 않는 정보와 감정을 저장하는 기운입니다. 삶에서는 정보 감각·해석 능력 쪽으로 강점이 드러나지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "수(水)": "수는 기억하고 흘러가며, 보이지 않는 정보와 감정을 저장하는 기운입니다. 삶에서는 정보 감각·해석 능력 쪽으로 강점이 드러나지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "갑목": "갑목은 큰 방향을 세우고, 자기 길을 곧게 밀고 나가려는 천간입니다. 특히 기획력·리더십 측면에 힘이 실리며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "甲갑목": "갑목은 큰 방향을 세우고, 자기 길을 곧게 밀고 나가려는 천간입니다. 특히 기획력·리더십 측면에 힘이 실리며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "갑목甲": "갑목은 큰 방향을 세우고, 자기 길을 곧게 밀고 나가려는 천간입니다. 특히 기획력·리더십 측면에 힘이 실리며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "甲": "갑목은 큰 방향을 세우고, 자기 길을 곧게 밀고 나가려는 천간입니다. 특히 기획력·리더십 측면에 힘이 실리며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "을목": "을목은 유연하게 파고들고, 관계 속에서 살아남는 천간입니다. 관계 감각·미감 측면이 실제 장점으로 작동하는 한편, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "乙을목": "을목은 유연하게 파고들고, 관계 속에서 살아남는 천간입니다. 관계 감각·미감 측면이 실제 장점으로 작동하는 한편, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "을목乙": "을목은 유연하게 파고들고, 관계 속에서 살아남는 천간입니다. 관계 감각·미감 측면이 실제 장점으로 작동하는 한편, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "乙": "을목은 유연하게 파고들고, 관계 속에서 살아남는 천간입니다. 관계 감각·미감 측면이 실제 장점으로 작동하는 한편, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "병화丙": "병화는 세상을 비추고, 자기 존재를 공개적으로 드러내는 천간입니다. 리더십·설득력 측면이 실제 장점으로 작동하는 한편, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "丙병화": "병화는 세상을 비추고, 자기 존재를 공개적으로 드러내는 천간입니다. 리더십·설득력 측면이 실제 장점으로 작동하는 한편, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "병화": "병화는 세상을 비추고, 자기 존재를 공개적으로 드러내는 천간입니다. 리더십·설득력 측면이 실제 장점으로 작동하는 한편, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "丙": "병화는 세상을 비추고, 자기 존재를 공개적으로 드러내는 천간입니다. 리더십·설득력 측면이 실제 장점으로 작동하는 한편, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "丁정화": "정화는 한곳에 집중해 어둠을 밝히고, 섬세한 열로 의미를 만드는 천간입니다. 창작력·상담 감각 측면이 실제 장점으로 작동하는 한편, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "정화": "정화는 한곳에 집중해 어둠을 밝히고, 섬세한 열로 의미를 만드는 천간입니다. 창작력·상담 감각 측면이 실제 장점으로 작동하는 한편, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "丁": "정화는 한곳에 집중해 어둠을 밝히고, 섬세한 열로 의미를 만드는 천간입니다. 창작력·상담 감각 측면이 실제 장점으로 작동하는 한편, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "정화丁": "정화는 한곳에 집중해 어둠을 밝히고, 섬세한 열로 의미를 만드는 천간입니다. 창작력·상담 감각 측면이 실제 장점으로 작동하는 한편, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "戊무토": "무토는 큰 책임과 중심을 세우고, 사람과 일을 받아내는 천간입니다. 운영력·위기 수습 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "무토戊": "무토는 큰 책임과 중심을 세우고, 사람과 일을 받아내는 천간입니다. 운영력·위기 수습 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "무토": "무토는 큰 책임과 중심을 세우고, 사람과 일을 받아내는 천간입니다. 운영력·위기 수습 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "戊": "무토는 큰 책임과 중심을 세우고, 사람과 일을 받아내는 천간입니다. 운영력·위기 수습 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "기토己": "기토는 생활을 돌보고, 필요한 것을 길러내며, 현실을 세밀하게 관리하는 천간입니다. 삶에서는 관리력·조율 쪽으로 강점이 드러나지만, 돌봄과 책임을 오래 끌면 자신의 시간과 감정이 서서히 소진될 수 있습니다.",
  "己": "기토는 생활을 돌보고, 필요한 것을 길러내며, 현실을 세밀하게 관리하는 천간입니다. 삶에서는 관리력·조율 쪽으로 강점이 드러나지만, 돌봄과 책임을 오래 끌면 자신의 시간과 감정이 서서히 소진될 수 있습니다.",
  "기토": "기토는 생활을 돌보고, 필요한 것을 길러내며, 현실을 세밀하게 관리하는 천간입니다. 삶에서는 관리력·조율 쪽으로 강점이 드러나지만, 돌봄과 책임을 오래 끌면 자신의 시간과 감정이 서서히 소진될 수 있습니다.",
  "己기토": "기토는 생활을 돌보고, 필요한 것을 길러내며, 현실을 세밀하게 관리하는 천간입니다. 삶에서는 관리력·조율 쪽으로 강점이 드러나지만, 돌봄과 책임을 오래 끌면 자신의 시간과 감정이 서서히 소진될 수 있습니다.",
  "庚": "경금은 큰 칼처럼 결단하고, 불필요한 것을 잘라내는 천간입니다. 판단력·기술력 분야에서 강점이 살아나며, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "庚경금": "경금은 큰 칼처럼 결단하고, 불필요한 것을 잘라내는 천간입니다. 판단력·기술력 분야에서 강점이 살아나며, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "경금": "경금은 큰 칼처럼 결단하고, 불필요한 것을 잘라내는 천간입니다. 판단력·기술력 분야에서 강점이 살아나며, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "경금庚": "경금은 큰 칼처럼 결단하고, 불필요한 것을 잘라내는 천간입니다. 판단력·기술력 분야에서 강점이 살아나며, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "辛신금": "신금은 세밀하게 가르고 다듬어, 가치와 완성도를 만드는 천간입니다. 미감·정밀함 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "신금辛": "신금은 세밀하게 가르고 다듬어, 가치와 완성도를 만드는 천간입니다. 미감·정밀함 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "辛": "신금은 세밀하게 가르고 다듬어, 가치와 완성도를 만드는 천간입니다. 미감·정밀함 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "신금": "신금은 세밀하게 가르고 다듬어, 가치와 완성도를 만드는 천간입니다. 미감·정밀함 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "壬": "임수는 큰 물처럼 움직이고, 사람과 정보와 기회를 넓게 흐르게 하는 천간입니다. 특히 정보력·전략 감각 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "壬임수": "임수는 큰 물처럼 움직이고, 사람과 정보와 기회를 넓게 흐르게 하는 천간입니다. 특히 정보력·전략 감각 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "임수": "임수는 큰 물처럼 움직이고, 사람과 정보와 기회를 넓게 흐르게 하는 천간입니다. 특히 정보력·전략 감각 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "임수壬": "임수는 큰 물처럼 움직이고, 사람과 정보와 기회를 넓게 흐르게 하는 천간입니다. 특히 정보력·전략 감각 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "癸계수": "계수는 작고 깊게 스며들며, 감정과 기억을 자기 안에서 해석하는 천간입니다. 특히 해석력·상담 감각 측면에 힘이 실리며, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "癸": "계수는 작고 깊게 스며들며, 감정과 기억을 자기 안에서 해석하는 천간입니다. 특히 해석력·상담 감각 측면에 힘이 실리며, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "계수": "계수는 작고 깊게 스며들며, 감정과 기억을 자기 안에서 해석하는 천간입니다. 특히 해석력·상담 감각 측면에 힘이 실리며, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "계수癸": "계수는 작고 깊게 스며들며, 감정과 기억을 자기 안에서 해석하는 천간입니다. 특히 해석력·상담 감각 측면에 힘이 실리며, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "子자수": "자수는 깊은 밤처럼 감정, 기억, 정보가 안쪽으로 고이는 지지입니다. 특히 정보 수집·해석력 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "자수": "자수는 깊은 밤처럼 감정, 기억, 정보가 안쪽으로 고이는 지지입니다. 특히 정보 수집·해석력 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "子": "자수는 깊은 밤처럼 감정, 기억, 정보가 안쪽으로 고이는 지지입니다. 특히 정보 수집·해석력 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "자수子": "자수는 깊은 밤처럼 감정, 기억, 정보가 안쪽으로 고이는 지지입니다. 특히 정보 수집·해석력 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "축토": "축토는 얼어붙은 창고처럼 오래 저장하고 버티는 지지입니다. 축적 능력·관리 감각 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "축토丑": "축토는 얼어붙은 창고처럼 오래 저장하고 버티는 지지입니다. 축적 능력·관리 감각 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "丑축토": "축토는 얼어붙은 창고처럼 오래 저장하고 버티는 지지입니다. 축적 능력·관리 감각 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "丑": "축토는 얼어붙은 창고처럼 오래 저장하고 버티는 지지입니다. 축적 능력·관리 감각 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "인목": "인목은 새해의 문이 열리듯 시작하고 치고 나가는 지지입니다. 시작 능력·리더십 측면이 실제 장점으로 작동하는 한편, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "寅": "인목은 새해의 문이 열리듯 시작하고 치고 나가는 지지입니다. 시작 능력·리더십 측면이 실제 장점으로 작동하는 한편, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "寅인목": "인목은 새해의 문이 열리듯 시작하고 치고 나가는 지지입니다. 시작 능력·리더십 측면이 실제 장점으로 작동하는 한편, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "인목寅": "인목은 새해의 문이 열리듯 시작하고 치고 나가는 지지입니다. 시작 능력·리더십 측면이 실제 장점으로 작동하는 한편, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "卯": "묘목은 관계, 미감, 호감, 부드러운 확장이 살아나는 지지입니다. 특히 관계 조율·디자인 감각 측면에 힘이 실리며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "묘목卯": "묘목은 관계, 미감, 호감, 부드러운 확장이 살아나는 지지입니다. 특히 관계 조율·디자인 감각 측면에 힘이 실리며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "卯묘목": "묘목은 관계, 미감, 호감, 부드러운 확장이 살아나는 지지입니다. 특히 관계 조율·디자인 감각 측면에 힘이 실리며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "묘목": "묘목은 관계, 미감, 호감, 부드러운 확장이 살아나는 지지입니다. 특히 관계 조율·디자인 감각 측면에 힘이 실리며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "진토辰": "진토는 봄의 끝에서 성장, 기억, 현실 기반을 한꺼번에 품은 지지입니다. 특히 저장과 기획·전환 능력 측면에 힘이 실리며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "辰": "진토는 봄의 끝에서 성장, 기억, 현실 기반을 한꺼번에 품은 지지입니다. 특히 저장과 기획·전환 능력 측면에 힘이 실리며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "辰진토": "진토는 봄의 끝에서 성장, 기억, 현실 기반을 한꺼번에 품은 지지입니다. 특히 저장과 기획·전환 능력 측면에 힘이 실리며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "진토": "진토는 봄의 끝에서 성장, 기억, 현실 기반을 한꺼번에 품은 지지입니다. 특히 저장과 기획·전환 능력 측면에 힘이 실리며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "사화巳": "사화는 열, 욕망, 기술, 속도가 한꺼번에 올라오는 지지입니다. 기술 감각·연출력 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "巳사화": "사화는 열, 욕망, 기술, 속도가 한꺼번에 올라오는 지지입니다. 기술 감각·연출력 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "巳": "사화는 열, 욕망, 기술, 속도가 한꺼번에 올라오는 지지입니다. 기술 감각·연출력 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "사화": "사화는 열, 욕망, 기술, 속도가 한꺼번에 올라오는 지지입니다. 기술 감각·연출력 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "午오화": "오화는 한낮처럼 드러나고, 자존심과 존재감이 강해지는 지지입니다. 특히 대중성·무대 감각 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "오화": "오화는 한낮처럼 드러나고, 자존심과 존재감이 강해지는 지지입니다. 특히 대중성·무대 감각 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "午": "오화는 한낮처럼 드러나고, 자존심과 존재감이 강해지는 지지입니다. 특히 대중성·무대 감각 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "오화午": "오화는 한낮처럼 드러나고, 자존심과 존재감이 강해지는 지지입니다. 특히 대중성·무대 감각 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "미토未": "미토는 뜨거운 생활과 가족, 돌봄, 미련을 품은 지지입니다. 생활 기획·교육·복지 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "未미토": "미토는 뜨거운 생활과 가족, 돌봄, 미련을 품은 지지입니다. 생활 기획·교육·복지 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "未": "미토는 뜨거운 생활과 가족, 돌봄, 미련을 품은 지지입니다. 생활 기획·교육·복지 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "미토": "미토는 뜨거운 생활과 가족, 돌봄, 미련을 품은 지지입니다. 생활 기획·교육·복지 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "申신금": "신금은 기술, 이동, 정보, 경쟁이 빠르게 살아나는 지지입니다. 기술력·정보 처리 분야에서 강점이 살아나며, 효율을 좇다가 관계와 방향을 자주 바꿀 수 있습니다.",
  "申": "신금은 기술, 이동, 정보, 경쟁이 빠르게 살아나는 지지입니다. 기술력·정보 처리 분야에서 강점이 살아나며, 효율을 좇다가 관계와 방향을 자주 바꿀 수 있습니다.",
  "신금申": "신금은 기술, 이동, 정보, 경쟁이 빠르게 살아나는 지지입니다. 기술력·정보 처리 분야에서 강점이 살아나며, 효율을 좇다가 관계와 방향을 자주 바꿀 수 있습니다.",
  "유금": "유금은 미감, 기준, 평가, 완성도가 강하게 드러나는 지지입니다. 삶에서는 품질 감각·브랜딩 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "酉유금": "유금은 미감, 기준, 평가, 완성도가 강하게 드러나는 지지입니다. 삶에서는 품질 감각·브랜딩 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "유금酉": "유금은 미감, 기준, 평가, 완성도가 강하게 드러나는 지지입니다. 삶에서는 품질 감각·브랜딩 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "酉": "유금은 미감, 기준, 평가, 완성도가 강하게 드러나는 지지입니다. 삶에서는 품질 감각·브랜딩 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "술토戌": "술토는 마른 땅 속에 불씨와 기준을 품은 책임의 지지입니다. 특히 보호 능력·위기 수습 측면에 힘이 실리며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "술토": "술토는 마른 땅 속에 불씨와 기준을 품은 책임의 지지입니다. 특히 보호 능력·위기 수습 측면에 힘이 실리며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "戌술토": "술토는 마른 땅 속에 불씨와 기준을 품은 책임의 지지입니다. 특히 보호 능력·위기 수습 측면에 힘이 실리며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "戌": "술토는 마른 땅 속에 불씨와 기준을 품은 책임의 지지입니다. 특히 보호 능력·위기 수습 측면에 힘이 실리며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "亥": "해수는 큰물과 씨앗이 함께 있어 이동, 감정, 철학성이 깊은 지지입니다. 삶에서는 직관·상담 감각 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "해수": "해수는 큰물과 씨앗이 함께 있어 이동, 감정, 철학성이 깊은 지지입니다. 삶에서는 직관·상담 감각 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "亥해수": "해수는 큰물과 씨앗이 함께 있어 이동, 감정, 철학성이 깊은 지지입니다. 삶에서는 직관·상담 감각 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "해수亥": "해수는 큰물과 씨앗이 함께 있어 이동, 감정, 철학성이 깊은 지지입니다. 삶에서는 직관·상담 감각 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "子자수지장간": "자수의 지장간은 깊은 감정과 기억이 안쪽으로 고이는 구조입니다. 삶에서는 정보 감각·해석력 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "지장간": "자수의 지장간은 깊은 감정과 기억이 안쪽으로 고이는 구조입니다. 삶에서는 정보 감각·해석력 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "子지장간": "자수의 지장간은 깊은 감정과 기억이 안쪽으로 고이는 구조입니다. 삶에서는 정보 감각·해석력 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "자수지장간": "자수의 지장간은 깊은 감정과 기억이 안쪽으로 고이는 구조입니다. 삶에서는 정보 감각·해석력 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "지장간子": "자수의 지장간은 깊은 감정과 기억이 안쪽으로 고이는 구조입니다. 삶에서는 정보 감각·해석력 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "丑축토지장간": "축토의 지장간은 감정과 가치와 생활 기반이 얼어붙은 창고처럼 작동합니다. 축적 능력·정밀 실무 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "丑지장간": "축토의 지장간은 감정과 가치와 생활 기반이 얼어붙은 창고처럼 작동합니다. 축적 능력·정밀 실무 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "축토지장간": "축토의 지장간은 감정과 가치와 생활 기반이 얼어붙은 창고처럼 작동합니다. 축적 능력·정밀 실무 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "지장간丑": "축토의 지장간은 감정과 가치와 생활 기반이 얼어붙은 창고처럼 작동합니다. 축적 능력·정밀 실무 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "寅지장간": "인목의 지장간은 기반을 딛고, 드러내고, 주체적으로 밀고 나가는 구조입니다. 시작 능력·리더십 분야에서 강점이 살아나며, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "寅인목지장간": "인목의 지장간은 기반을 딛고, 드러내고, 주체적으로 밀고 나가는 구조입니다. 시작 능력·리더십 분야에서 강점이 살아나며, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "지장간寅": "인목의 지장간은 기반을 딛고, 드러내고, 주체적으로 밀고 나가는 구조입니다. 시작 능력·리더십 분야에서 강점이 살아나며, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "인목지장간": "인목의 지장간은 기반을 딛고, 드러내고, 주체적으로 밀고 나가는 구조입니다. 시작 능력·리더십 분야에서 강점이 살아나며, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "卯묘목지장간": "묘목의 지장간은 큰 방향의 흔적을 품은 순수한 관계성과 미감으로 나타납니다. 삶에서는 관계 조율·디자인 감각 쪽으로 강점이 드러나지만, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "卯지장간": "묘목의 지장간은 큰 방향의 흔적을 품은 순수한 관계성과 미감으로 나타납니다. 삶에서는 관계 조율·디자인 감각 쪽으로 강점이 드러나지만, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "지장간卯": "묘목의 지장간은 큰 방향의 흔적을 품은 순수한 관계성과 미감으로 나타납니다. 삶에서는 관계 조율·디자인 감각 쪽으로 강점이 드러나지만, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "묘목지장간": "묘목의 지장간은 큰 방향의 흔적을 품은 순수한 관계성과 미감으로 나타납니다. 삶에서는 관계 조율·디자인 감각 쪽으로 강점이 드러나지만, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "辰지장간": "진토의 지장간은 성장의 잔기와 숨은 감정, 현실 기반이 함께 저장된 구조입니다. 삶에서는 저장과 기획·전환 능력 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "지장간辰": "진토의 지장간은 성장의 잔기와 숨은 감정, 현실 기반이 함께 저장된 구조입니다. 삶에서는 저장과 기획·전환 능력 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "진토지장간": "진토의 지장간은 성장의 잔기와 숨은 감정, 현실 기반이 함께 저장된 구조입니다. 삶에서는 저장과 기획·전환 능력 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "辰진토지장간": "진토의 지장간은 성장의 잔기와 숨은 감정, 현실 기반이 함께 저장된 구조입니다. 삶에서는 저장과 기획·전환 능력 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "巳지장간": "사화의 지장간은 기반, 기술, 열이 함께 들어 있어 욕망과 실무 속도가 빠르게 나타납니다. 특히 기술 감각·연출력 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "사화지장간": "사화의 지장간은 기반, 기술, 열이 함께 들어 있어 욕망과 실무 속도가 빠르게 나타납니다. 특히 기술 감각·연출력 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "巳사화지장간": "사화의 지장간은 기반, 기술, 열이 함께 들어 있어 욕망과 실무 속도가 빠르게 나타납니다. 특히 기술 감각·연출력 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "지장간巳": "사화의 지장간은 기반, 기술, 열이 함께 들어 있어 욕망과 실무 속도가 빠르게 나타납니다. 특히 기술 감각·연출력 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "오화지장간": "오화의 지장간은 공개성, 생활 책임, 감정의 불이 함께 있는 구조입니다. 삶에서는 대중성·무대 감각 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "午지장간": "오화의 지장간은 공개성, 생활 책임, 감정의 불이 함께 있는 구조입니다. 삶에서는 대중성·무대 감각 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "午오화지장간": "오화의 지장간은 공개성, 생활 책임, 감정의 불이 함께 있는 구조입니다. 삶에서는 대중성·무대 감각 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "지장간午": "오화의 지장간은 공개성, 생활 책임, 감정의 불이 함께 있는 구조입니다. 삶에서는 대중성·무대 감각 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "지장간未": "미토의 지장간은 감정과 관계와 생활 책임이 함께 마른 흙 속에 남은 구조입니다. 생활 기획·교육·복지 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "미토지장간": "미토의 지장간은 감정과 관계와 생활 책임이 함께 마른 흙 속에 남은 구조입니다. 생활 기획·교육·복지 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "未지장간": "미토의 지장간은 감정과 관계와 생활 책임이 함께 마른 흙 속에 남은 구조입니다. 생활 기획·교육·복지 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "未미토지장간": "미토의 지장간은 감정과 관계와 생활 책임이 함께 마른 흙 속에 남은 구조입니다. 생활 기획·교육·복지 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "지장간申": "신금의 지장간은 기반, 정보, 기술이 함께 있어 실전 감각이 빠른 구조입니다. 특히 기술력·정보 처리 측면에 힘이 실리며, 효율을 좇다가 관계와 방향을 자주 바꿀 수 있습니다.",
  "申신금지장간": "신금의 지장간은 기반, 정보, 기술이 함께 있어 실전 감각이 빠른 구조입니다. 특히 기술력·정보 처리 측면에 힘이 실리며, 효율을 좇다가 관계와 방향을 자주 바꿀 수 있습니다.",
  "신금지장간": "신금의 지장간은 기반, 정보, 기술이 함께 있어 실전 감각이 빠른 구조입니다. 특히 기술력·정보 처리 측면에 힘이 실리며, 효율을 좇다가 관계와 방향을 자주 바꿀 수 있습니다.",
  "申지장간": "신금의 지장간은 기반, 정보, 기술이 함께 있어 실전 감각이 빠른 구조입니다. 특히 기술력·정보 처리 측면에 힘이 실리며, 효율을 좇다가 관계와 방향을 자주 바꿀 수 있습니다.",
  "유금지장간": "유금의 지장간은 큰 절단의 흔적을 품은 순수한 평가와 완성도로 나타납니다. 품질 감각·브랜딩 측면이 실제 장점으로 작동하는 한편, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "酉유금지장간": "유금의 지장간은 큰 절단의 흔적을 품은 순수한 평가와 완성도로 나타납니다. 품질 감각·브랜딩 측면이 실제 장점으로 작동하는 한편, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "지장간酉": "유금의 지장간은 큰 절단의 흔적을 품은 순수한 평가와 완성도로 나타납니다. 품질 감각·브랜딩 측면이 실제 장점으로 작동하는 한편, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "酉지장간": "유금의 지장간은 큰 절단의 흔적을 품은 순수한 평가와 완성도로 나타납니다. 품질 감각·브랜딩 측면이 실제 장점으로 작동하는 한편, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "술토지장간": "술토의 지장간은 기준과 불씨와 책임이 마른 흙 속에 저장된 구조입니다. 삶에서는 보호 능력·위기 수습 쪽으로 강점이 드러나지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "지장간戌": "술토의 지장간은 기준과 불씨와 책임이 마른 흙 속에 저장된 구조입니다. 삶에서는 보호 능력·위기 수습 쪽으로 강점이 드러나지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "戌술토지장간": "술토의 지장간은 기준과 불씨와 책임이 마른 흙 속에 저장된 구조입니다. 삶에서는 보호 능력·위기 수습 쪽으로 강점이 드러나지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "戌지장간": "술토의 지장간은 기준과 불씨와 책임이 마른 흙 속에 저장된 구조입니다. 삶에서는 보호 능력·위기 수습 쪽으로 강점이 드러나지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "지장간亥": "해수의 지장간은 큰물 속에 현실의 경계와 새 시작의 씨앗이 함께 있는 구조입니다. 직관·상담 감각 측면이 실제 장점으로 작동하는 한편, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "亥해수지장간": "해수의 지장간은 큰물 속에 현실의 경계와 새 시작의 씨앗이 함께 있는 구조입니다. 직관·상담 감각 측면이 실제 장점으로 작동하는 한편, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "亥지장간": "해수의 지장간은 큰물 속에 현실의 경계와 새 시작의 씨앗이 함께 있는 구조입니다. 직관·상담 감각 측면이 실제 장점으로 작동하는 한편, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "해수지장간": "해수의 지장간은 큰물 속에 현실의 경계와 새 시작의 씨앗이 함께 있는 구조입니다. 직관·상담 감각 측면이 실제 장점으로 작동하는 한편, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "목화木火": "목화는 생각과 가능성을 밖으로 드러내는 배합입니다. 삶에서는 기획력·발표력 쪽으로 강점이 드러나지만, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "목화": "목화는 생각과 가능성을 밖으로 드러내는 배합입니다. 삶에서는 기획력·발표력 쪽으로 강점이 드러나지만, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "木火목화": "목화는 생각과 가능성을 밖으로 드러내는 배합입니다. 삶에서는 기획력·발표력 쪽으로 강점이 드러나지만, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "목화(木火)": "목화는 생각과 가능성을 밖으로 드러내는 배합입니다. 삶에서는 기획력·발표력 쪽으로 강점이 드러나지만, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "木火": "목화는 생각과 가능성을 밖으로 드러내는 배합입니다. 삶에서는 기획력·발표력 쪽으로 강점이 드러나지만, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "목토": "목토는 성장하려는 힘과 현실의 무게가 맞서는 배합입니다. 삶에서는 개척력·생활 설계 쪽으로 강점이 드러나지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "목토(木土)": "목토는 성장하려는 힘과 현실의 무게가 맞서는 배합입니다. 삶에서는 개척력·생활 설계 쪽으로 강점이 드러나지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "木土": "목토는 성장하려는 힘과 현실의 무게가 맞서는 배합입니다. 삶에서는 개척력·생활 설계 쪽으로 강점이 드러나지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "목토木土": "목토는 성장하려는 힘과 현실의 무게가 맞서는 배합입니다. 삶에서는 개척력·생활 설계 쪽으로 강점이 드러나지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "木土목토": "목토는 성장하려는 힘과 현실의 무게가 맞서는 배합입니다. 삶에서는 개척력·생활 설계 쪽으로 강점이 드러나지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "목금(木金)": "목금은 성장하려는 힘과 자르려는 기준이 부딪히는 배합입니다. 교정 능력·전략 감각 분야에서 강점이 살아나며, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "목금": "목금은 성장하려는 힘과 자르려는 기준이 부딪히는 배합입니다. 교정 능력·전략 감각 분야에서 강점이 살아나며, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "木金": "목금은 성장하려는 힘과 자르려는 기준이 부딪히는 배합입니다. 교정 능력·전략 감각 분야에서 강점이 살아나며, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "목금木金": "목금은 성장하려는 힘과 자르려는 기준이 부딪히는 배합입니다. 교정 능력·전략 감각 분야에서 강점이 살아나며, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "木金목금": "목금은 성장하려는 힘과 자르려는 기준이 부딪히는 배합입니다. 교정 능력·전략 감각 분야에서 강점이 살아나며, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "木水": "목수는 축적한 감각과 지식에서 새로운 방향을 뽑아내는 배합입니다. 기획력·언어 감각 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "목수(木水)": "목수는 축적한 감각과 지식에서 새로운 방향을 뽑아내는 배합입니다. 기획력·언어 감각 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "木水목수": "목수는 축적한 감각과 지식에서 새로운 방향을 뽑아내는 배합입니다. 기획력·언어 감각 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "목수木水": "목수는 축적한 감각과 지식에서 새로운 방향을 뽑아내는 배합입니다. 기획력·언어 감각 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "목수": "목수는 축적한 감각과 지식에서 새로운 방향을 뽑아내는 배합입니다. 기획력·언어 감각 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "화토(火土)": "화토는 드러난 것을 책임과 결과로 굳히는 배합입니다. 운영 능력·관리력 분야에서 강점이 살아나며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "火土": "화토는 드러난 것을 책임과 결과로 굳히는 배합입니다. 운영 능력·관리력 분야에서 강점이 살아나며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "화토": "화토는 드러난 것을 책임과 결과로 굳히는 배합입니다. 운영 능력·관리력 분야에서 강점이 살아나며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "火土화토": "화토는 드러난 것을 책임과 결과로 굳히는 배합입니다. 운영 능력·관리력 분야에서 강점이 살아나며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "화토火土": "화토는 드러난 것을 책임과 결과로 굳히는 배합입니다. 운영 능력·관리력 분야에서 강점이 살아나며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "火金": "화금은 드러내는 힘과 다듬는 기준이 맞부딪히는 배합입니다. 삶에서는 브랜딩·무대 감각 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "화금": "화금은 드러내는 힘과 다듬는 기준이 맞부딪히는 배합입니다. 삶에서는 브랜딩·무대 감각 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "화금(火金)": "화금은 드러내는 힘과 다듬는 기준이 맞부딪히는 배합입니다. 삶에서는 브랜딩·무대 감각 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "火金화금": "화금은 드러내는 힘과 다듬는 기준이 맞부딪히는 배합입니다. 삶에서는 브랜딩·무대 감각 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "화금火金": "화금은 드러내는 힘과 다듬는 기준이 맞부딪히는 배합입니다. 삶에서는 브랜딩·무대 감각 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "火水화수": "화수는 드러내려는 마음과 숨기려는 마음이 동시에 움직이는 배합입니다. 특히 분위기 감지·심리 감각 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "화수(火水)": "화수는 드러내려는 마음과 숨기려는 마음이 동시에 움직이는 배합입니다. 특히 분위기 감지·심리 감각 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "화수火水": "화수는 드러내려는 마음과 숨기려는 마음이 동시에 움직이는 배합입니다. 특히 분위기 감지·심리 감각 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "화수": "화수는 드러내려는 마음과 숨기려는 마음이 동시에 움직이는 배합입니다. 특히 분위기 감지·심리 감각 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "火水": "화수는 드러내려는 마음과 숨기려는 마음이 동시에 움직이는 배합입니다. 특히 분위기 감지·심리 감각 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "土金": "토금은 경험과 생활을 기준·기술·완성도로 바꾸는 배합입니다. 삶에서는 기술력·품질 관리 쪽으로 강점이 드러나지만, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "토금": "토금은 경험과 생활을 기준·기술·완성도로 바꾸는 배합입니다. 삶에서는 기술력·품질 관리 쪽으로 강점이 드러나지만, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "토금土金": "토금은 경험과 생활을 기준·기술·완성도로 바꾸는 배합입니다. 삶에서는 기술력·품질 관리 쪽으로 강점이 드러나지만, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "土金토금": "토금은 경험과 생활을 기준·기술·완성도로 바꾸는 배합입니다. 삶에서는 기술력·품질 관리 쪽으로 강점이 드러나지만, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "토금(土金)": "토금은 경험과 생활을 기준·기술·완성도로 바꾸는 배합입니다. 삶에서는 기술력·품질 관리 쪽으로 강점이 드러나지만, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "토수(土水)": "토수는 생활 기반과 흐르는 돈·감정이 부딪히는 배합입니다. 특히 재무 감각·위험 관리 측면에 힘이 실리며, 안전을 지키려다 자금과 감정의 흐름을 지나치게 묶어 둘 수 있습니다.",
  "土水토수": "토수는 생활 기반과 흐르는 돈·감정이 부딪히는 배합입니다. 특히 재무 감각·위험 관리 측면에 힘이 실리며, 안전을 지키려다 자금과 감정의 흐름을 지나치게 묶어 둘 수 있습니다.",
  "토수": "토수는 생활 기반과 흐르는 돈·감정이 부딪히는 배합입니다. 특히 재무 감각·위험 관리 측면에 힘이 실리며, 안전을 지키려다 자금과 감정의 흐름을 지나치게 묶어 둘 수 있습니다.",
  "土水": "토수는 생활 기반과 흐르는 돈·감정이 부딪히는 배합입니다. 특히 재무 감각·위험 관리 측면에 힘이 실리며, 안전을 지키려다 자금과 감정의 흐름을 지나치게 묶어 둘 수 있습니다.",
  "토수土水": "토수는 생활 기반과 흐르는 돈·감정이 부딪히는 배합입니다. 특히 재무 감각·위험 관리 측면에 힘이 실리며, 안전을 지키려다 자금과 감정의 흐름을 지나치게 묶어 둘 수 있습니다.",
  "금수": "금수는 분별한 것을 정보와 지식으로 저장하고 흘려보내는 배합입니다. 분석력·정보 처리 측면이 실제 장점으로 작동하는 한편, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "금수(金水)": "금수는 분별한 것을 정보와 지식으로 저장하고 흘려보내는 배합입니다. 분석력·정보 처리 측면이 실제 장점으로 작동하는 한편, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "金水": "금수는 분별한 것을 정보와 지식으로 저장하고 흘려보내는 배합입니다. 분석력·정보 처리 측면이 실제 장점으로 작동하는 한편, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "금수金水": "금수는 분별한 것을 정보와 지식으로 저장하고 흘려보내는 배합입니다. 분석력·정보 처리 측면이 실제 장점으로 작동하는 한편, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "金水금수": "금수는 분별한 것을 정보와 지식으로 저장하고 흘려보내는 배합입니다. 분석력·정보 처리 측면이 실제 장점으로 작동하는 한편, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "목화토木火土": "목화토는 가능성을 드러내고 현실 기반으로 굳히는 배합입니다. 특히 기획 발표·조직 운영 측면에 힘이 실리며, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "木火土목화토": "목화토는 가능성을 드러내고 현실 기반으로 굳히는 배합입니다. 특히 기획 발표·조직 운영 측면에 힘이 실리며, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "木火土": "목화토는 가능성을 드러내고 현실 기반으로 굳히는 배합입니다. 특히 기획 발표·조직 운영 측면에 힘이 실리며, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "목화토": "목화토는 가능성을 드러내고 현실 기반으로 굳히는 배합입니다. 특히 기획 발표·조직 운영 측면에 힘이 실리며, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "목화토(木火土)": "목화토는 가능성을 드러내고 현실 기반으로 굳히는 배합입니다. 특히 기획 발표·조직 운영 측면에 힘이 실리며, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "木火金목화금": "목화금은 성장한 재능을 사람들 앞에 내놓고 평가받는 배합입니다. 무대감·브랜딩 측면이 실제 장점으로 작동하는 한편, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "목화금": "목화금은 성장한 재능을 사람들 앞에 내놓고 평가받는 배합입니다. 무대감·브랜딩 측면이 실제 장점으로 작동하는 한편, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "목화금(木火金)": "목화금은 성장한 재능을 사람들 앞에 내놓고 평가받는 배합입니다. 무대감·브랜딩 측면이 실제 장점으로 작동하는 한편, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "木火金": "목화금은 성장한 재능을 사람들 앞에 내놓고 평가받는 배합입니다. 무대감·브랜딩 측면이 실제 장점으로 작동하는 한편, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "목화금木火金": "목화금은 성장한 재능을 사람들 앞에 내놓고 평가받는 배합입니다. 무대감·브랜딩 측면이 실제 장점으로 작동하는 한편, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "목화수": "목화수는 상상과 감정을 말과 표현으로 끌어올리는 배합입니다. 삶에서는 스토리텔링·상담 감각 쪽으로 강점이 드러나지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "목화수(木火水)": "목화수는 상상과 감정을 말과 표현으로 끌어올리는 배합입니다. 삶에서는 스토리텔링·상담 감각 쪽으로 강점이 드러나지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "木火水": "목화수는 상상과 감정을 말과 표현으로 끌어올리는 배합입니다. 삶에서는 스토리텔링·상담 감각 쪽으로 강점이 드러나지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "목화수木火水": "목화수는 상상과 감정을 말과 표현으로 끌어올리는 배합입니다. 삶에서는 스토리텔링·상담 감각 쪽으로 강점이 드러나지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "木火水목화수": "목화수는 상상과 감정을 말과 표현으로 끌어올리는 배합입니다. 삶에서는 스토리텔링·상담 감각 쪽으로 강점이 드러나지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "목토금木土金": "목토금은 계획을 현실로 밀어 넣고 기준으로 완성하려는 배합입니다. 사업 설계·품질 구축 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "목토금": "목토금은 계획을 현실로 밀어 넣고 기준으로 완성하려는 배합입니다. 사업 설계·품질 구축 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "木土金": "목토금은 계획을 현실로 밀어 넣고 기준으로 완성하려는 배합입니다. 사업 설계·품질 구축 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "木土金목토금": "목토금은 계획을 현실로 밀어 넣고 기준으로 완성하려는 배합입니다. 사업 설계·품질 구축 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "목토금(木土金)": "목토금은 계획을 현실로 밀어 넣고 기준으로 완성하려는 배합입니다. 사업 설계·품질 구축 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "목토수": "목토수는 성장 욕구와 생활 안정, 감정과 돈의 흐름이 함께 꼬이는 배합입니다. 삶에서는 생활 기획·재무 설계 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "목토수(木土水)": "목토수는 성장 욕구와 생활 안정, 감정과 돈의 흐름이 함께 꼬이는 배합입니다. 삶에서는 생활 기획·재무 설계 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "목토수木土水": "목토수는 성장 욕구와 생활 안정, 감정과 돈의 흐름이 함께 꼬이는 배합입니다. 삶에서는 생활 기획·재무 설계 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "木土水목토수": "목토수는 성장 욕구와 생활 안정, 감정과 돈의 흐름이 함께 꼬이는 배합입니다. 삶에서는 생활 기획·재무 설계 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "木土水": "목토수는 성장 욕구와 생활 안정, 감정과 돈의 흐름이 함께 꼬이는 배합입니다. 삶에서는 생활 기획·재무 설계 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "木金水": "목금수는 가능성을 날카롭게 분석하고 정보로 확장하는 배합입니다. 분석 기획·정보 설계 분야에서 강점이 살아나며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "목금수(木金水)": "목금수는 가능성을 날카롭게 분석하고 정보로 확장하는 배합입니다. 분석 기획·정보 설계 분야에서 강점이 살아나며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "木金水목금수": "목금수는 가능성을 날카롭게 분석하고 정보로 확장하는 배합입니다. 분석 기획·정보 설계 분야에서 강점이 살아나며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "목금수": "목금수는 가능성을 날카롭게 분석하고 정보로 확장하는 배합입니다. 분석 기획·정보 설계 분야에서 강점이 살아나며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "목금수木金水": "목금수는 가능성을 날카롭게 분석하고 정보로 확장하는 배합입니다. 분석 기획·정보 설계 분야에서 강점이 살아나며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "화토금": "화토금은 평판과 책임을 실무 기준과 완성도로 굳히는 배합입니다. 특히 관리와 검수·공개 설득 측면에 힘이 실리며, 완성도를 높이려다 과로하고 주변을 지나치게 평가할 수 있습니다.",
  "화토금(火土金)": "화토금은 평판과 책임을 실무 기준과 완성도로 굳히는 배합입니다. 특히 관리와 검수·공개 설득 측면에 힘이 실리며, 완성도를 높이려다 과로하고 주변을 지나치게 평가할 수 있습니다.",
  "火土金화토금": "화토금은 평판과 책임을 실무 기준과 완성도로 굳히는 배합입니다. 특히 관리와 검수·공개 설득 측면에 힘이 실리며, 완성도를 높이려다 과로하고 주변을 지나치게 평가할 수 있습니다.",
  "화토금火土金": "화토금은 평판과 책임을 실무 기준과 완성도로 굳히는 배합입니다. 특히 관리와 검수·공개 설득 측면에 힘이 실리며, 완성도를 높이려다 과로하고 주변을 지나치게 평가할 수 있습니다.",
  "火土金": "화토금은 평판과 책임을 실무 기준과 완성도로 굳히는 배합입니다. 특히 관리와 검수·공개 설득 측면에 힘이 실리며, 완성도를 높이려다 과로하고 주변을 지나치게 평가할 수 있습니다.",
  "화토수": "화토수는 드러난 책임과 숨은 불안, 생활과 돈의 긴장이 함께 있는 배합입니다. 생활 운영·위험 관리 분야에서 강점이 살아나며, 겉의 역할을 유지하느라 속의 불안과 피로를 늦게 알아차릴 수 있습니다.",
  "화토수火土水": "화토수는 드러난 책임과 숨은 불안, 생활과 돈의 긴장이 함께 있는 배합입니다. 생활 운영·위험 관리 분야에서 강점이 살아나며, 겉의 역할을 유지하느라 속의 불안과 피로를 늦게 알아차릴 수 있습니다.",
  "火土水화토수": "화토수는 드러난 책임과 숨은 불안, 생활과 돈의 긴장이 함께 있는 배합입니다. 생활 운영·위험 관리 분야에서 강점이 살아나며, 겉의 역할을 유지하느라 속의 불안과 피로를 늦게 알아차릴 수 있습니다.",
  "화토수(火土水)": "화토수는 드러난 책임과 숨은 불안, 생활과 돈의 긴장이 함께 있는 배합입니다. 생활 운영·위험 관리 분야에서 강점이 살아나며, 겉의 역할을 유지하느라 속의 불안과 피로를 늦게 알아차릴 수 있습니다.",
  "火土水": "화토수는 드러난 책임과 숨은 불안, 생활과 돈의 긴장이 함께 있는 배합입니다. 생활 운영·위험 관리 분야에서 강점이 살아나며, 겉의 역할을 유지하느라 속의 불안과 피로를 늦게 알아차릴 수 있습니다.",
  "화금수": "화금수는 노출과 평가, 정보와 비밀이 함께 움직이는 배합입니다. 삶에서는 브랜딩 분석·전략 홍보 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "火金水화금수": "화금수는 노출과 평가, 정보와 비밀이 함께 움직이는 배합입니다. 삶에서는 브랜딩 분석·전략 홍보 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "화금수火金水": "화금수는 노출과 평가, 정보와 비밀이 함께 움직이는 배합입니다. 삶에서는 브랜딩 분석·전략 홍보 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "화금수(火金水)": "화금수는 노출과 평가, 정보와 비밀이 함께 움직이는 배합입니다. 삶에서는 브랜딩 분석·전략 홍보 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "火金水": "화금수는 노출과 평가, 정보와 비밀이 함께 움직이는 배합입니다. 삶에서는 브랜딩 분석·전략 홍보 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "토금수土金水": "토금수는 생활 기반을 정리해 정보와 돈의 흐름으로 바꾸는 배합입니다. 삶에서는 재무 분석·운영 정리 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "토금수": "토금수는 생활 기반을 정리해 정보와 돈의 흐름으로 바꾸는 배합입니다. 삶에서는 재무 분석·운영 정리 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "土金水토금수": "토금수는 생활 기반을 정리해 정보와 돈의 흐름으로 바꾸는 배합입니다. 삶에서는 재무 분석·운영 정리 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "토금수(土金水)": "토금수는 생활 기반을 정리해 정보와 돈의 흐름으로 바꾸는 배합입니다. 삶에서는 재무 분석·운영 정리 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "土金水": "토금수는 생활 기반을 정리해 정보와 돈의 흐름으로 바꾸는 배합입니다. 삶에서는 재무 분석·운영 정리 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "甲乙": "갑을은 큰 방향과 유연한 적응이 함께 있는 목의 배합입니다. 삶에서는 기획력·관계 조율 쪽으로 강점이 드러나지만, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "을목+甲乙갑목": "갑을은 큰 방향과 유연한 적응이 함께 있는 목의 배합입니다. 삶에서는 기획력·관계 조율 쪽으로 강점이 드러나지만, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "을목甲乙": "갑을은 큰 방향과 유연한 적응이 함께 있는 목의 배합입니다. 삶에서는 기획력·관계 조율 쪽으로 강점이 드러나지만, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "甲乙을목": "갑을은 큰 방향과 유연한 적응이 함께 있는 목의 배합입니다. 삶에서는 기획력·관계 조율 쪽으로 강점이 드러나지만, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "甲乙갑목+을목": "갑을은 큰 방향과 유연한 적응이 함께 있는 목의 배합입니다. 삶에서는 기획력·관계 조율 쪽으로 강점이 드러나지만, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "갑목을목": "갑을은 큰 방향과 유연한 적응이 함께 있는 목의 배합입니다. 삶에서는 기획력·관계 조율 쪽으로 강점이 드러나지만, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "병화甲丙": "갑병은 큰 방향을 세상에 드러내고 지위 상승을 노리는 배합입니다. 삶에서는 리더십·발표력 쪽으로 강점이 드러나지만, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "甲丙": "갑병은 큰 방향을 세상에 드러내고 지위 상승을 노리는 배합입니다. 삶에서는 리더십·발표력 쪽으로 강점이 드러나지만, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "병화+甲丙갑목": "갑병은 큰 방향을 세상에 드러내고 지위 상승을 노리는 배합입니다. 삶에서는 리더십·발표력 쪽으로 강점이 드러나지만, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "甲丙병화": "갑병은 큰 방향을 세상에 드러내고 지위 상승을 노리는 배합입니다. 삶에서는 리더십·발표력 쪽으로 강점이 드러나지만, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "甲丙갑목+병화": "갑병은 큰 방향을 세상에 드러내고 지위 상승을 노리는 배합입니다. 삶에서는 리더십·발표력 쪽으로 강점이 드러나지만, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "갑목병화": "갑병은 큰 방향을 세상에 드러내고 지위 상승을 노리는 배합입니다. 삶에서는 리더십·발표력 쪽으로 강점이 드러나지만, 계획과 표현이 앞서면 실행과 마무리가 약해질 수 있습니다.",
  "甲丁갑목+정화": "갑정은 큰 목표를 섬세한 표현과 집중력으로 태우는 배합입니다. 삶에서는 창작력·교육 감각 쪽으로 강점이 드러나지만, 이상적인 기준을 지키려다 현실의 실행 시점을 놓칠 수 있습니다.",
  "갑목정화": "갑정은 큰 목표를 섬세한 표현과 집중력으로 태우는 배합입니다. 삶에서는 창작력·교육 감각 쪽으로 강점이 드러나지만, 이상적인 기준을 지키려다 현실의 실행 시점을 놓칠 수 있습니다.",
  "甲丁": "갑정은 큰 목표를 섬세한 표현과 집중력으로 태우는 배합입니다. 삶에서는 창작력·교육 감각 쪽으로 강점이 드러나지만, 이상적인 기준을 지키려다 현실의 실행 시점을 놓칠 수 있습니다.",
  "정화甲丁": "갑정은 큰 목표를 섬세한 표현과 집중력으로 태우는 배합입니다. 삶에서는 창작력·교육 감각 쪽으로 강점이 드러나지만, 이상적인 기준을 지키려다 현실의 실행 시점을 놓칠 수 있습니다.",
  "甲丁정화": "갑정은 큰 목표를 섬세한 표현과 집중력으로 태우는 배합입니다. 삶에서는 창작력·교육 감각 쪽으로 강점이 드러나지만, 이상적인 기준을 지키려다 현실의 실행 시점을 놓칠 수 있습니다.",
  "정화+甲丁갑목": "갑정은 큰 목표를 섬세한 표현과 집중력으로 태우는 배합입니다. 삶에서는 창작력·교육 감각 쪽으로 강점이 드러나지만, 이상적인 기준을 지키려다 현실의 실행 시점을 놓칠 수 있습니다.",
  "甲戊갑목+무토": "갑무는 큰 계획이 큰 땅과 책임을 밀어붙이는 배합입니다. 삶에서는 사업 설계·조직 구축 쪽으로 강점이 드러나지만, 규모를 먼저 키우면 자금과 책임이 감당 범위를 넘을 수 있습니다.",
  "甲戊": "갑무는 큰 계획이 큰 땅과 책임을 밀어붙이는 배합입니다. 삶에서는 사업 설계·조직 구축 쪽으로 강점이 드러나지만, 규모를 먼저 키우면 자금과 책임이 감당 범위를 넘을 수 있습니다.",
  "甲戊무토": "갑무는 큰 계획이 큰 땅과 책임을 밀어붙이는 배합입니다. 삶에서는 사업 설계·조직 구축 쪽으로 강점이 드러나지만, 규모를 먼저 키우면 자금과 책임이 감당 범위를 넘을 수 있습니다.",
  "무토+甲戊갑목": "갑무는 큰 계획이 큰 땅과 책임을 밀어붙이는 배합입니다. 삶에서는 사업 설계·조직 구축 쪽으로 강점이 드러나지만, 규모를 먼저 키우면 자금과 책임이 감당 범위를 넘을 수 있습니다.",
  "갑목무토": "갑무는 큰 계획이 큰 땅과 책임을 밀어붙이는 배합입니다. 삶에서는 사업 설계·조직 구축 쪽으로 강점이 드러나지만, 규모를 먼저 키우면 자금과 책임이 감당 범위를 넘을 수 있습니다.",
  "무토甲戊": "갑무는 큰 계획이 큰 땅과 책임을 밀어붙이는 배합입니다. 삶에서는 사업 설계·조직 구축 쪽으로 강점이 드러나지만, 규모를 먼저 키우면 자금과 책임이 감당 범위를 넘을 수 있습니다.",
  "갑목기토": "갑기는 큰 방향을 생활과 현실의 형태로 묶는 배합입니다. 특히 관리 기획·교육 운영 측면에 힘이 실리며, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "甲己갑목+기토": "갑기는 큰 방향을 생활과 현실의 형태로 묶는 배합입니다. 특히 관리 기획·교육 운영 측면에 힘이 실리며, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "기토甲己": "갑기는 큰 방향을 생활과 현실의 형태로 묶는 배합입니다. 특히 관리 기획·교육 운영 측면에 힘이 실리며, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "기토+甲己갑목": "갑기는 큰 방향을 생활과 현실의 형태로 묶는 배합입니다. 특히 관리 기획·교육 운영 측면에 힘이 실리며, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "甲己": "갑기는 큰 방향을 생활과 현실의 형태로 묶는 배합입니다. 특히 관리 기획·교육 운영 측면에 힘이 실리며, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "甲己기토": "갑기는 큰 방향을 생활과 현실의 형태로 묶는 배합입니다. 특히 관리 기획·교육 운영 측면에 힘이 실리며, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "경금+甲庚갑목": "갑경은 큰 나무와 큰 칼의 배합으로, 성장과 절단이 정면으로 부딪힙니다. 교정력·전략성 측면이 실제 장점으로 작동하는 한편, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "甲庚경금": "갑경은 큰 나무와 큰 칼의 배합으로, 성장과 절단이 정면으로 부딪힙니다. 교정력·전략성 측면이 실제 장점으로 작동하는 한편, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "경금甲庚": "갑경은 큰 나무와 큰 칼의 배합으로, 성장과 절단이 정면으로 부딪힙니다. 교정력·전략성 측면이 실제 장점으로 작동하는 한편, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "甲庚": "갑경은 큰 나무와 큰 칼의 배합으로, 성장과 절단이 정면으로 부딪힙니다. 교정력·전략성 측면이 실제 장점으로 작동하는 한편, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "甲庚갑목+경금": "갑경은 큰 나무와 큰 칼의 배합으로, 성장과 절단이 정면으로 부딪힙니다. 교정력·전략성 측면이 실제 장점으로 작동하는 한편, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "갑목경금": "갑경은 큰 나무와 큰 칼의 배합으로, 성장과 절단이 정면으로 부딪힙니다. 교정력·전략성 측면이 실제 장점으로 작동하는 한편, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "甲辛": "갑신은 큰 방향을 세밀한 기준으로 다듬는 배합입니다. 디테일 교정·브랜딩 측면이 실제 장점으로 작동하는 한편, 기준이 높아질수록 자신과 주변의 작은 부족함까지 과하게 평가할 수 있습니다.",
  "신금+甲辛갑목": "갑신은 큰 방향을 세밀한 기준으로 다듬는 배합입니다. 디테일 교정·브랜딩 측면이 실제 장점으로 작동하는 한편, 기준이 높아질수록 자신과 주변의 작은 부족함까지 과하게 평가할 수 있습니다.",
  "甲辛갑목+신금": "갑신은 큰 방향을 세밀한 기준으로 다듬는 배합입니다. 디테일 교정·브랜딩 측면이 실제 장점으로 작동하는 한편, 기준이 높아질수록 자신과 주변의 작은 부족함까지 과하게 평가할 수 있습니다.",
  "甲辛신금": "갑신은 큰 방향을 세밀한 기준으로 다듬는 배합입니다. 디테일 교정·브랜딩 측면이 실제 장점으로 작동하는 한편, 기준이 높아질수록 자신과 주변의 작은 부족함까지 과하게 평가할 수 있습니다.",
  "갑목신금": "갑신은 큰 방향을 세밀한 기준으로 다듬는 배합입니다. 디테일 교정·브랜딩 측면이 실제 장점으로 작동하는 한편, 기준이 높아질수록 자신과 주변의 작은 부족함까지 과하게 평가할 수 있습니다.",
  "신금甲辛": "갑신은 큰 방향을 세밀한 기준으로 다듬는 배합입니다. 디테일 교정·브랜딩 측면이 실제 장점으로 작동하는 한편, 기준이 높아질수록 자신과 주변의 작은 부족함까지 과하게 평가할 수 있습니다.",
  "甲壬임수": "갑임은 큰 물이 큰 나무를 키우듯, 지식과 경험이 큰 방향을 만듭니다. 전략 기획·연구력 분야에서 강점이 살아나며, 계획과 가능성을 넓히느라 우선순위와 착수가 늦어질 수 있습니다.",
  "임수甲壬": "갑임은 큰 물이 큰 나무를 키우듯, 지식과 경험이 큰 방향을 만듭니다. 전략 기획·연구력 분야에서 강점이 살아나며, 계획과 가능성을 넓히느라 우선순위와 착수가 늦어질 수 있습니다.",
  "甲壬": "갑임은 큰 물이 큰 나무를 키우듯, 지식과 경험이 큰 방향을 만듭니다. 전략 기획·연구력 분야에서 강점이 살아나며, 계획과 가능성을 넓히느라 우선순위와 착수가 늦어질 수 있습니다.",
  "甲壬갑목+임수": "갑임은 큰 물이 큰 나무를 키우듯, 지식과 경험이 큰 방향을 만듭니다. 전략 기획·연구력 분야에서 강점이 살아나며, 계획과 가능성을 넓히느라 우선순위와 착수가 늦어질 수 있습니다.",
  "임수+甲壬갑목": "갑임은 큰 물이 큰 나무를 키우듯, 지식과 경험이 큰 방향을 만듭니다. 전략 기획·연구력 분야에서 강점이 살아나며, 계획과 가능성을 넓히느라 우선순위와 착수가 늦어질 수 있습니다.",
  "갑목임수": "갑임은 큰 물이 큰 나무를 키우듯, 지식과 경험이 큰 방향을 만듭니다. 전략 기획·연구력 분야에서 강점이 살아나며, 계획과 가능성을 넓히느라 우선순위와 착수가 늦어질 수 있습니다.",
  "甲癸": "갑계는 조용한 감수성과 기억이 큰 성장의 씨앗이 되는 배합입니다. 학습력·상담 감각 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "계수甲癸": "갑계는 조용한 감수성과 기억이 큰 성장의 씨앗이 되는 배합입니다. 학습력·상담 감각 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "계수+甲癸갑목": "갑계는 조용한 감수성과 기억이 큰 성장의 씨앗이 되는 배합입니다. 학습력·상담 감각 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "甲癸갑목+계수": "갑계는 조용한 감수성과 기억이 큰 성장의 씨앗이 되는 배합입니다. 학습력·상담 감각 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "甲癸계수": "갑계는 조용한 감수성과 기억이 큰 성장의 씨앗이 되는 배합입니다. 학습력·상담 감각 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "갑목계수": "갑계는 조용한 감수성과 기억이 큰 성장의 씨앗이 되는 배합입니다. 학습력·상담 감각 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "乙丙": "을병은 섬세한 감각을 밝게 드러내 호감을 만드는 배합입니다. 이미지 연출·대중 감각 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "병화+乙丙을목": "을병은 섬세한 감각을 밝게 드러내 호감을 만드는 배합입니다. 이미지 연출·대중 감각 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "을목병화": "을병은 섬세한 감각을 밝게 드러내 호감을 만드는 배합입니다. 이미지 연출·대중 감각 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "乙丙병화": "을병은 섬세한 감각을 밝게 드러내 호감을 만드는 배합입니다. 이미지 연출·대중 감각 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "병화乙丙": "을병은 섬세한 감각을 밝게 드러내 호감을 만드는 배합입니다. 이미지 연출·대중 감각 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "乙丙을목+병화": "을병은 섬세한 감각을 밝게 드러내 호감을 만드는 배합입니다. 이미지 연출·대중 감각 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "정화乙丁": "을정은 섬세한 감각과 깊은 표현이 살아나는 배합입니다. 창작력·미감 분야에서 강점이 살아나며, 작은 변화에도 감정과 집중력이 쉽게 흔들릴 수 있습니다.",
  "乙丁을목+정화": "을정은 섬세한 감각과 깊은 표현이 살아나는 배합입니다. 창작력·미감 분야에서 강점이 살아나며, 작은 변화에도 감정과 집중력이 쉽게 흔들릴 수 있습니다.",
  "을목정화": "을정은 섬세한 감각과 깊은 표현이 살아나는 배합입니다. 창작력·미감 분야에서 강점이 살아나며, 작은 변화에도 감정과 집중력이 쉽게 흔들릴 수 있습니다.",
  "乙丁정화": "을정은 섬세한 감각과 깊은 표현이 살아나는 배합입니다. 창작력·미감 분야에서 강점이 살아나며, 작은 변화에도 감정과 집중력이 쉽게 흔들릴 수 있습니다.",
  "乙丁": "을정은 섬세한 감각과 깊은 표현이 살아나는 배합입니다. 창작력·미감 분야에서 강점이 살아나며, 작은 변화에도 감정과 집중력이 쉽게 흔들릴 수 있습니다.",
  "정화+乙丁을목": "을정은 섬세한 감각과 깊은 표현이 살아나는 배합입니다. 창작력·미감 분야에서 강점이 살아나며, 작은 변화에도 감정과 집중력이 쉽게 흔들릴 수 있습니다.",
  "乙戊을목+무토": "을무는 부드러운 관계성이 큰 현실과 자리를 타고 오르려는 배합입니다. 관계 활용·조직 적응 분야에서 강점이 살아나며, 사람을 실리 중심으로 판단하면 진심과 신뢰가 약해질 수 있습니다.",
  "무토+乙戊을목": "을무는 부드러운 관계성이 큰 현실과 자리를 타고 오르려는 배합입니다. 관계 활용·조직 적응 분야에서 강점이 살아나며, 사람을 실리 중심으로 판단하면 진심과 신뢰가 약해질 수 있습니다.",
  "무토乙戊": "을무는 부드러운 관계성이 큰 현실과 자리를 타고 오르려는 배합입니다. 관계 활용·조직 적응 분야에서 강점이 살아나며, 사람을 실리 중심으로 판단하면 진심과 신뢰가 약해질 수 있습니다.",
  "乙戊무토": "을무는 부드러운 관계성이 큰 현실과 자리를 타고 오르려는 배합입니다. 관계 활용·조직 적응 분야에서 강점이 살아나며, 사람을 실리 중심으로 판단하면 진심과 신뢰가 약해질 수 있습니다.",
  "乙戊": "을무는 부드러운 관계성이 큰 현실과 자리를 타고 오르려는 배합입니다. 관계 활용·조직 적응 분야에서 강점이 살아나며, 사람을 실리 중심으로 판단하면 진심과 신뢰가 약해질 수 있습니다.",
  "을목무토": "을무는 부드러운 관계성이 큰 현실과 자리를 타고 오르려는 배합입니다. 관계 활용·조직 적응 분야에서 강점이 살아나며, 사람을 실리 중심으로 판단하면 진심과 신뢰가 약해질 수 있습니다.",
  "을목기토": "을기는 생활 속에서 사람을 살피고 실속을 만드는 배합입니다. 서비스 감각·돌봄 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "乙己": "을기는 생활 속에서 사람을 살피고 실속을 만드는 배합입니다. 서비스 감각·돌봄 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "乙己기토": "을기는 생활 속에서 사람을 살피고 실속을 만드는 배합입니다. 서비스 감각·돌봄 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "기토乙己": "을기는 생활 속에서 사람을 살피고 실속을 만드는 배합입니다. 서비스 감각·돌봄 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "乙己을목+기토": "을기는 생활 속에서 사람을 살피고 실속을 만드는 배합입니다. 서비스 감각·돌봄 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "기토+乙己을목": "을기는 생활 속에서 사람을 살피고 실속을 만드는 배합입니다. 서비스 감각·돌봄 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "경금乙庚": "을경은 부드러운 생존력이 강한 기준과 만나 냉정한 실력으로 바뀌는 배합입니다. 특히 협상력·교정력 측면에 힘이 실리며, 상대를 고치거나 기준에 맞추려다 관계의 긴장이 커질 수 있습니다.",
  "乙庚을목+경금": "을경은 부드러운 생존력이 강한 기준과 만나 냉정한 실력으로 바뀌는 배합입니다. 특히 협상력·교정력 측면에 힘이 실리며, 상대를 고치거나 기준에 맞추려다 관계의 긴장이 커질 수 있습니다.",
  "乙庚": "을경은 부드러운 생존력이 강한 기준과 만나 냉정한 실력으로 바뀌는 배합입니다. 특히 협상력·교정력 측면에 힘이 실리며, 상대를 고치거나 기준에 맞추려다 관계의 긴장이 커질 수 있습니다.",
  "乙庚경금": "을경은 부드러운 생존력이 강한 기준과 만나 냉정한 실력으로 바뀌는 배합입니다. 특히 협상력·교정력 측면에 힘이 실리며, 상대를 고치거나 기준에 맞추려다 관계의 긴장이 커질 수 있습니다.",
  "을목경금": "을경은 부드러운 생존력이 강한 기준과 만나 냉정한 실력으로 바뀌는 배합입니다. 특히 협상력·교정력 측면에 힘이 실리며, 상대를 고치거나 기준에 맞추려다 관계의 긴장이 커질 수 있습니다.",
  "경금+乙庚을목": "을경은 부드러운 생존력이 강한 기준과 만나 냉정한 실력으로 바뀌는 배합입니다. 특히 협상력·교정력 측면에 힘이 실리며, 상대를 고치거나 기준에 맞추려다 관계의 긴장이 커질 수 있습니다.",
  "신금+乙辛을목": "을신은 섬세한 미감과 날카로운 평가가 함께 있는 배합입니다. 특히 디자인 감각·편집·교정 측면에 힘이 실리며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "乙辛신금": "을신은 섬세한 미감과 날카로운 평가가 함께 있는 배합입니다. 특히 디자인 감각·편집·교정 측면에 힘이 실리며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "乙辛": "을신은 섬세한 미감과 날카로운 평가가 함께 있는 배합입니다. 특히 디자인 감각·편집·교정 측면에 힘이 실리며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "乙辛을목+신금": "을신은 섬세한 미감과 날카로운 평가가 함께 있는 배합입니다. 특히 디자인 감각·편집·교정 측면에 힘이 실리며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "을목신금": "을신은 섬세한 미감과 날카로운 평가가 함께 있는 배합입니다. 특히 디자인 감각·편집·교정 측면에 힘이 실리며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "신금乙辛": "을신은 섬세한 미감과 날카로운 평가가 함께 있는 배합입니다. 특히 디자인 감각·편집·교정 측면에 힘이 실리며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "임수+乙壬을목": "을임은 넓은 물을 타고 관계와 가능성을 확장하는 배합입니다. 삶에서는 언어·상담·네트워크 쪽으로 강점이 드러나지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "乙壬임수": "을임은 넓은 물을 타고 관계와 가능성을 확장하는 배합입니다. 삶에서는 언어·상담·네트워크 쪽으로 강점이 드러나지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "乙壬": "을임은 넓은 물을 타고 관계와 가능성을 확장하는 배합입니다. 삶에서는 언어·상담·네트워크 쪽으로 강점이 드러나지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "乙壬을목+임수": "을임은 넓은 물을 타고 관계와 가능성을 확장하는 배합입니다. 삶에서는 언어·상담·네트워크 쪽으로 강점이 드러나지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "임수乙壬": "을임은 넓은 물을 타고 관계와 가능성을 확장하는 배합입니다. 삶에서는 언어·상담·네트워크 쪽으로 강점이 드러나지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "을목임수": "을임은 넓은 물을 타고 관계와 가능성을 확장하는 배합입니다. 삶에서는 언어·상담·네트워크 쪽으로 강점이 드러나지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "乙癸을목+계수": "을계는 섬세한 감수성이 관계와 표현의 씨앗이 되는 배합입니다. 삶에서는 상담 감각·글·표현 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "계수+乙癸을목": "을계는 섬세한 감수성이 관계와 표현의 씨앗이 되는 배합입니다. 삶에서는 상담 감각·글·표현 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "을목계수": "을계는 섬세한 감수성이 관계와 표현의 씨앗이 되는 배합입니다. 삶에서는 상담 감각·글·표현 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "乙癸계수": "을계는 섬세한 감수성이 관계와 표현의 씨앗이 되는 배합입니다. 삶에서는 상담 감각·글·표현 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "계수乙癸": "을계는 섬세한 감수성이 관계와 표현의 씨앗이 되는 배합입니다. 삶에서는 상담 감각·글·표현 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "乙癸": "을계는 섬세한 감수성이 관계와 표현의 씨앗이 되는 배합입니다. 삶에서는 상담 감각·글·표현 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "정화丙丁": "병정은 공개적인 빛과 내면의 불이 함께 있어 표현성이 강한 배합입니다. 발표력·창작력 분야에서 강점이 살아나며, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "丙丁병화+정화": "병정은 공개적인 빛과 내면의 불이 함께 있어 표현성이 강한 배합입니다. 발표력·창작력 분야에서 강점이 살아나며, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "병화정화": "병정은 공개적인 빛과 내면의 불이 함께 있어 표현성이 강한 배합입니다. 발표력·창작력 분야에서 강점이 살아나며, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "丙丁": "병정은 공개적인 빛과 내면의 불이 함께 있어 표현성이 강한 배합입니다. 발표력·창작력 분야에서 강점이 살아나며, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "정화+丙丁병화": "병정은 공개적인 빛과 내면의 불이 함께 있어 표현성이 강한 배합입니다. 발표력·창작력 분야에서 강점이 살아나며, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "丙丁정화": "병정은 공개적인 빛과 내면의 불이 함께 있어 표현성이 강한 배합입니다. 발표력·창작력 분야에서 강점이 살아나며, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "병화무토": "병무는 공개성과 큰 책임이 만나 사회적 중심을 만드는 배합입니다. 리더십·조직 운영 분야에서 강점이 살아나며, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "丙戊": "병무는 공개성과 큰 책임이 만나 사회적 중심을 만드는 배합입니다. 리더십·조직 운영 분야에서 강점이 살아나며, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "丙戊병화+무토": "병무는 공개성과 큰 책임이 만나 사회적 중심을 만드는 배합입니다. 리더십·조직 운영 분야에서 강점이 살아나며, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "丙戊무토": "병무는 공개성과 큰 책임이 만나 사회적 중심을 만드는 배합입니다. 리더십·조직 운영 분야에서 강점이 살아나며, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "무토丙戊": "병무는 공개성과 큰 책임이 만나 사회적 중심을 만드는 배합입니다. 리더십·조직 운영 분야에서 강점이 살아나며, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "무토+丙戊병화": "병무는 공개성과 큰 책임이 만나 사회적 중심을 만드는 배합입니다. 리더십·조직 운영 분야에서 강점이 살아나며, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "丙己기토": "병기는 밝은 표현을 생활과 실무로 내려앉히는 배합입니다. 교육 운영·서비스 기획 측면이 실제 장점으로 작동하는 한편, 좋은 인상을 유지하려다 생활 에너지와 비용을 과하게 쓸 수 있습니다.",
  "丙己병화+기토": "병기는 밝은 표현을 생활과 실무로 내려앉히는 배합입니다. 교육 운영·서비스 기획 측면이 실제 장점으로 작동하는 한편, 좋은 인상을 유지하려다 생활 에너지와 비용을 과하게 쓸 수 있습니다.",
  "병화기토": "병기는 밝은 표현을 생활과 실무로 내려앉히는 배합입니다. 교육 운영·서비스 기획 측면이 실제 장점으로 작동하는 한편, 좋은 인상을 유지하려다 생활 에너지와 비용을 과하게 쓸 수 있습니다.",
  "기토丙己": "병기는 밝은 표현을 생활과 실무로 내려앉히는 배합입니다. 교육 운영·서비스 기획 측면이 실제 장점으로 작동하는 한편, 좋은 인상을 유지하려다 생활 에너지와 비용을 과하게 쓸 수 있습니다.",
  "기토+丙己병화": "병기는 밝은 표현을 생활과 실무로 내려앉히는 배합입니다. 교육 운영·서비스 기획 측면이 실제 장점으로 작동하는 한편, 좋은 인상을 유지하려다 생활 에너지와 비용을 과하게 쓸 수 있습니다.",
  "丙己": "병기는 밝은 표현을 생활과 실무로 내려앉히는 배합입니다. 교육 운영·서비스 기획 측면이 실제 장점으로 작동하는 한편, 좋은 인상을 유지하려다 생활 에너지와 비용을 과하게 쓸 수 있습니다.",
  "丙庚병화+경금": "병경은 큰 비전과 강한 실적을 만들려는 배합입니다. 특히 실적 창출·결단력 측면에 힘이 실리며, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "丙庚경금": "병경은 큰 비전과 강한 실적을 만들려는 배합입니다. 특히 실적 창출·결단력 측면에 힘이 실리며, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "丙庚": "병경은 큰 비전과 강한 실적을 만들려는 배합입니다. 특히 실적 창출·결단력 측면에 힘이 실리며, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "경금丙庚": "병경은 큰 비전과 강한 실적을 만들려는 배합입니다. 특히 실적 창출·결단력 측면에 힘이 실리며, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "경금+丙庚병화": "병경은 큰 비전과 강한 실적을 만들려는 배합입니다. 특히 실적 창출·결단력 측면에 힘이 실리며, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "병화경금": "병경은 큰 비전과 강한 실적을 만들려는 배합입니다. 특히 실적 창출·결단력 측면에 힘이 실리며, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "丙辛": "병신은 공개성과 세련된 이미지가 만나 강한 상징성을 만드는 배합입니다. 특히 브랜딩·미감 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "병화신금": "병신은 공개성과 세련된 이미지가 만나 강한 상징성을 만드는 배합입니다. 특히 브랜딩·미감 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "丙辛신금": "병신은 공개성과 세련된 이미지가 만나 강한 상징성을 만드는 배합입니다. 특히 브랜딩·미감 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "신금+丙辛병화": "병신은 공개성과 세련된 이미지가 만나 강한 상징성을 만드는 배합입니다. 특히 브랜딩·미감 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "丙辛병화+신금": "병신은 공개성과 세련된 이미지가 만나 강한 상징성을 만드는 배합입니다. 특히 브랜딩·미감 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "신금丙辛": "병신은 공개성과 세련된 이미지가 만나 강한 상징성을 만드는 배합입니다. 특히 브랜딩·미감 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "丙壬병화+임수": "병임은 큰 빛과 큰 물이 만나 사회적 논의와 큰 긴장을 만드는 배합입니다. 삶에서는 정치 감각·대중 설득 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "丙壬임수": "병임은 큰 빛과 큰 물이 만나 사회적 논의와 큰 긴장을 만드는 배합입니다. 삶에서는 정치 감각·대중 설득 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "丙壬": "병임은 큰 빛과 큰 물이 만나 사회적 논의와 큰 긴장을 만드는 배합입니다. 삶에서는 정치 감각·대중 설득 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "임수+丙壬병화": "병임은 큰 빛과 큰 물이 만나 사회적 논의와 큰 긴장을 만드는 배합입니다. 삶에서는 정치 감각·대중 설득 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "임수丙壬": "병임은 큰 빛과 큰 물이 만나 사회적 논의와 큰 긴장을 만드는 배합입니다. 삶에서는 정치 감각·대중 설득 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "병화임수": "병임은 큰 빛과 큰 물이 만나 사회적 논의와 큰 긴장을 만드는 배합입니다. 삶에서는 정치 감각·대중 설득 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "丙癸계수": "병계는 공개된 관점과 개인적 감수성이 만나는 배합입니다. 삶에서는 소통력·상담적 표현 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "계수丙癸": "병계는 공개된 관점과 개인적 감수성이 만나는 배합입니다. 삶에서는 소통력·상담적 표현 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "丙癸": "병계는 공개된 관점과 개인적 감수성이 만나는 배합입니다. 삶에서는 소통력·상담적 표현 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "병화계수": "병계는 공개된 관점과 개인적 감수성이 만나는 배합입니다. 삶에서는 소통력·상담적 표현 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "계수+丙癸병화": "병계는 공개된 관점과 개인적 감수성이 만나는 배합입니다. 삶에서는 소통력·상담적 표현 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "丙癸병화+계수": "병계는 공개된 관점과 개인적 감수성이 만나는 배합입니다. 삶에서는 소통력·상담적 표현 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "丁戊정화+무토": "정무는 내면의 열을 큰 책임과 기반으로 굳히는 배합입니다. 전문 관리·연구 운영 분야에서 강점이 살아나며, 책임과 감정을 겉으로 드러내지 않아 내부 피로가 오래 쌓일 수 있습니다.",
  "무토丁戊": "정무는 내면의 열을 큰 책임과 기반으로 굳히는 배합입니다. 전문 관리·연구 운영 분야에서 강점이 살아나며, 책임과 감정을 겉으로 드러내지 않아 내부 피로가 오래 쌓일 수 있습니다.",
  "무토+丁戊정화": "정무는 내면의 열을 큰 책임과 기반으로 굳히는 배합입니다. 전문 관리·연구 운영 분야에서 강점이 살아나며, 책임과 감정을 겉으로 드러내지 않아 내부 피로가 오래 쌓일 수 있습니다.",
  "丁戊무토": "정무는 내면의 열을 큰 책임과 기반으로 굳히는 배합입니다. 전문 관리·연구 운영 분야에서 강점이 살아나며, 책임과 감정을 겉으로 드러내지 않아 내부 피로가 오래 쌓일 수 있습니다.",
  "丁戊": "정무는 내면의 열을 큰 책임과 기반으로 굳히는 배합입니다. 전문 관리·연구 운영 분야에서 강점이 살아나며, 책임과 감정을 겉으로 드러내지 않아 내부 피로가 오래 쌓일 수 있습니다.",
  "정화무토": "정무는 내면의 열을 큰 책임과 기반으로 굳히는 배합입니다. 전문 관리·연구 운영 분야에서 강점이 살아나며, 책임과 감정을 겉으로 드러내지 않아 내부 피로가 오래 쌓일 수 있습니다.",
  "丁己정화+기토": "정기는 섬세한 열이 생활과 돌봄으로 내려앉는 배합입니다. 돌봄·교육·상담 측면이 실제 장점으로 작동하는 한편, 돌봄과 배려를 우선하다 자신의 시간과 에너지를 잃기 쉽습니다.",
  "丁己기토": "정기는 섬세한 열이 생활과 돌봄으로 내려앉는 배합입니다. 돌봄·교육·상담 측면이 실제 장점으로 작동하는 한편, 돌봄과 배려를 우선하다 자신의 시간과 에너지를 잃기 쉽습니다.",
  "정화기토": "정기는 섬세한 열이 생활과 돌봄으로 내려앉는 배합입니다. 돌봄·교육·상담 측면이 실제 장점으로 작동하는 한편, 돌봄과 배려를 우선하다 자신의 시간과 에너지를 잃기 쉽습니다.",
  "기토+丁己정화": "정기는 섬세한 열이 생활과 돌봄으로 내려앉는 배합입니다. 돌봄·교육·상담 측면이 실제 장점으로 작동하는 한편, 돌봄과 배려를 우선하다 자신의 시간과 에너지를 잃기 쉽습니다.",
  "丁己": "정기는 섬세한 열이 생활과 돌봄으로 내려앉는 배합입니다. 돌봄·교육·상담 측면이 실제 장점으로 작동하는 한편, 돌봄과 배려를 우선하다 자신의 시간과 에너지를 잃기 쉽습니다.",
  "기토丁己": "정기는 섬세한 열이 생활과 돌봄으로 내려앉는 배합입니다. 돌봄·교육·상담 측면이 실제 장점으로 작동하는 한편, 돌봄과 배려를 우선하다 자신의 시간과 에너지를 잃기 쉽습니다.",
  "경금丁庚": "정경은 섬세한 불로 큰 쇠를 다듬는 기술형 배합입니다. 특히 기술 단련·수리·교정 측면에 힘이 실리며, 성과를 밀어붙이다 몸이 지치고 말이 거칠어질 수 있습니다.",
  "정화경금": "정경은 섬세한 불로 큰 쇠를 다듬는 기술형 배합입니다. 특히 기술 단련·수리·교정 측면에 힘이 실리며, 성과를 밀어붙이다 몸이 지치고 말이 거칠어질 수 있습니다.",
  "丁庚경금": "정경은 섬세한 불로 큰 쇠를 다듬는 기술형 배합입니다. 특히 기술 단련·수리·교정 측면에 힘이 실리며, 성과를 밀어붙이다 몸이 지치고 말이 거칠어질 수 있습니다.",
  "丁庚정화+경금": "정경은 섬세한 불로 큰 쇠를 다듬는 기술형 배합입니다. 특히 기술 단련·수리·교정 측면에 힘이 실리며, 성과를 밀어붙이다 몸이 지치고 말이 거칠어질 수 있습니다.",
  "丁庚": "정경은 섬세한 불로 큰 쇠를 다듬는 기술형 배합입니다. 특히 기술 단련·수리·교정 측면에 힘이 실리며, 성과를 밀어붙이다 몸이 지치고 말이 거칠어질 수 있습니다.",
  "경금+丁庚정화": "정경은 섬세한 불로 큰 쇠를 다듬는 기술형 배합입니다. 특히 기술 단련·수리·교정 측면에 힘이 실리며, 성과를 밀어붙이다 몸이 지치고 말이 거칠어질 수 있습니다.",
  "신금丁辛": "정신은 작은 빛이 보석을 비추듯 미감과 완성도를 만드는 배합입니다. 특히 디자인·편집 측면에 힘이 실리며, 완성도 기준이 높아져 자신을 지나치게 깎아내릴 수 있습니다.",
  "丁辛신금": "정신은 작은 빛이 보석을 비추듯 미감과 완성도를 만드는 배합입니다. 특히 디자인·편집 측면에 힘이 실리며, 완성도 기준이 높아져 자신을 지나치게 깎아내릴 수 있습니다.",
  "丁辛": "정신은 작은 빛이 보석을 비추듯 미감과 완성도를 만드는 배합입니다. 특히 디자인·편집 측면에 힘이 실리며, 완성도 기준이 높아져 자신을 지나치게 깎아내릴 수 있습니다.",
  "신금+丁辛정화": "정신은 작은 빛이 보석을 비추듯 미감과 완성도를 만드는 배합입니다. 특히 디자인·편집 측면에 힘이 실리며, 완성도 기준이 높아져 자신을 지나치게 깎아내릴 수 있습니다.",
  "정화신금": "정신은 작은 빛이 보석을 비추듯 미감과 완성도를 만드는 배합입니다. 특히 디자인·편집 측면에 힘이 실리며, 완성도 기준이 높아져 자신을 지나치게 깎아내릴 수 있습니다.",
  "丁辛정화+신금": "정신은 작은 빛이 보석을 비추듯 미감과 완성도를 만드는 배합입니다. 특히 디자인·편집 측면에 힘이 실리며, 완성도 기준이 높아져 자신을 지나치게 깎아내릴 수 있습니다.",
  "丁壬": "정임은 깊은 물과 작은 불이 만나 상상력과 생명력을 만드는 배합입니다. 삶에서는 창작력·철학성 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "丁壬정화+임수": "정임은 깊은 물과 작은 불이 만나 상상력과 생명력을 만드는 배합입니다. 삶에서는 창작력·철학성 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "丁壬임수": "정임은 깊은 물과 작은 불이 만나 상상력과 생명력을 만드는 배합입니다. 삶에서는 창작력·철학성 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "임수+丁壬정화": "정임은 깊은 물과 작은 불이 만나 상상력과 생명력을 만드는 배합입니다. 삶에서는 창작력·철학성 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "임수丁壬": "정임은 깊은 물과 작은 불이 만나 상상력과 생명력을 만드는 배합입니다. 삶에서는 창작력·철학성 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "정화임수": "정임은 깊은 물과 작은 불이 만나 상상력과 생명력을 만드는 배합입니다. 삶에서는 창작력·철학성 쪽으로 강점이 드러나지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "丁癸계수": "정계는 작은 불과 작은 물이 만나 섬세한 불안과 직관을 만드는 배합입니다. 삶에서는 심리 감지·세밀한 글 쪽으로 강점이 드러나지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "丁癸정화+계수": "정계는 작은 불과 작은 물이 만나 섬세한 불안과 직관을 만드는 배합입니다. 삶에서는 심리 감지·세밀한 글 쪽으로 강점이 드러나지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "계수丁癸": "정계는 작은 불과 작은 물이 만나 섬세한 불안과 직관을 만드는 배합입니다. 삶에서는 심리 감지·세밀한 글 쪽으로 강점이 드러나지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "丁癸": "정계는 작은 불과 작은 물이 만나 섬세한 불안과 직관을 만드는 배합입니다. 삶에서는 심리 감지·세밀한 글 쪽으로 강점이 드러나지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "정화계수": "정계는 작은 불과 작은 물이 만나 섬세한 불안과 직관을 만드는 배합입니다. 삶에서는 심리 감지·세밀한 글 쪽으로 강점이 드러나지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "계수+丁癸정화": "정계는 작은 불과 작은 물이 만나 섬세한 불안과 직관을 만드는 배합입니다. 삶에서는 심리 감지·세밀한 글 쪽으로 강점이 드러나지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "戊己기토": "무기는 큰 기반과 생활 관리가 함께 있는 토의 배합입니다. 운영력·생활 관리 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "기토+戊己무토": "무기는 큰 기반과 생활 관리가 함께 있는 토의 배합입니다. 운영력·생활 관리 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "기토戊己": "무기는 큰 기반과 생활 관리가 함께 있는 토의 배합입니다. 운영력·생활 관리 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "무토기토": "무기는 큰 기반과 생활 관리가 함께 있는 토의 배합입니다. 운영력·생활 관리 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "戊己": "무기는 큰 기반과 생활 관리가 함께 있는 토의 배합입니다. 운영력·생활 관리 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "戊己무토+기토": "무기는 큰 기반과 생활 관리가 함께 있는 토의 배합입니다. 운영력·생활 관리 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "경금戊庚": "무경은 큰 기반에서 강한 기술과 결단이 나오는 배합입니다. 특히 기술력·위기 수습 측면에 힘이 실리며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "경금+戊庚무토": "무경은 큰 기반에서 강한 기술과 결단이 나오는 배합입니다. 특히 기술력·위기 수습 측면에 힘이 실리며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "戊庚무토+경금": "무경은 큰 기반에서 강한 기술과 결단이 나오는 배합입니다. 특히 기술력·위기 수습 측면에 힘이 실리며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "戊庚": "무경은 큰 기반에서 강한 기술과 결단이 나오는 배합입니다. 특히 기술력·위기 수습 측면에 힘이 실리며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "무토경금": "무경은 큰 기반에서 강한 기술과 결단이 나오는 배합입니다. 특히 기술력·위기 수습 측면에 힘이 실리며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "戊庚경금": "무경은 큰 기반에서 강한 기술과 결단이 나오는 배합입니다. 특히 기술력·위기 수습 측면에 힘이 실리며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "戊辛무토+신금": "무신은 큰 기반 속에 가치 있는 보석을 품는 배합입니다. 특히 브랜드 감각·자산 관리 측면에 힘이 실리며, 가치와 품질을 따지다 사람과 경험까지 가격처럼 평가할 수 있습니다.",
  "戊辛": "무신은 큰 기반 속에 가치 있는 보석을 품는 배합입니다. 특히 브랜드 감각·자산 관리 측면에 힘이 실리며, 가치와 품질을 따지다 사람과 경험까지 가격처럼 평가할 수 있습니다.",
  "무토신금": "무신은 큰 기반 속에 가치 있는 보석을 품는 배합입니다. 특히 브랜드 감각·자산 관리 측면에 힘이 실리며, 가치와 품질을 따지다 사람과 경험까지 가격처럼 평가할 수 있습니다.",
  "戊辛신금": "무신은 큰 기반 속에 가치 있는 보석을 품는 배합입니다. 특히 브랜드 감각·자산 관리 측면에 힘이 실리며, 가치와 품질을 따지다 사람과 경험까지 가격처럼 평가할 수 있습니다.",
  "신금戊辛": "무신은 큰 기반 속에 가치 있는 보석을 품는 배합입니다. 특히 브랜드 감각·자산 관리 측면에 힘이 실리며, 가치와 품질을 따지다 사람과 경험까지 가격처럼 평가할 수 있습니다.",
  "신금+戊辛무토": "무신은 큰 기반 속에 가치 있는 보석을 품는 배합입니다. 특히 브랜드 감각·자산 관리 측면에 힘이 실리며, 가치와 품질을 따지다 사람과 경험까지 가격처럼 평가할 수 있습니다.",
  "戊壬무토+임수": "무임은 큰 땅과 큰물이 만나 돈, 조직, 권한의 규모가 커지는 배합입니다. 삶에서는 재무 관리·조직 장악 쪽으로 강점이 드러나지만, 규모를 키우는 과정에서 부채와 책임이 함께 커질 수 있습니다.",
  "임수戊壬": "무임은 큰 땅과 큰물이 만나 돈, 조직, 권한의 규모가 커지는 배합입니다. 삶에서는 재무 관리·조직 장악 쪽으로 강점이 드러나지만, 규모를 키우는 과정에서 부채와 책임이 함께 커질 수 있습니다.",
  "임수+戊壬무토": "무임은 큰 땅과 큰물이 만나 돈, 조직, 권한의 규모가 커지는 배합입니다. 삶에서는 재무 관리·조직 장악 쪽으로 강점이 드러나지만, 규모를 키우는 과정에서 부채와 책임이 함께 커질 수 있습니다.",
  "戊壬임수": "무임은 큰 땅과 큰물이 만나 돈, 조직, 권한의 규모가 커지는 배합입니다. 삶에서는 재무 관리·조직 장악 쪽으로 강점이 드러나지만, 규모를 키우는 과정에서 부채와 책임이 함께 커질 수 있습니다.",
  "무토임수": "무임은 큰 땅과 큰물이 만나 돈, 조직, 권한의 규모가 커지는 배합입니다. 삶에서는 재무 관리·조직 장악 쪽으로 강점이 드러나지만, 규모를 키우는 과정에서 부채와 책임이 함께 커질 수 있습니다.",
  "戊壬": "무임은 큰 땅과 큰물이 만나 돈, 조직, 권한의 규모가 커지는 배합입니다. 삶에서는 재무 관리·조직 장악 쪽으로 강점이 드러나지만, 규모를 키우는 과정에서 부채와 책임이 함께 커질 수 있습니다.",
  "戊癸": "무계는 큰 책임 속에 숨은 감정과 열이 들어 있는 배합입니다. 삶에서는 생활 통찰·관리 감각 쪽으로 강점이 드러나지만, 책임을 우선하다 감정을 눌러 뒤늦게 피로와 불만이 터질 수 있습니다.",
  "계수+戊癸무토": "무계는 큰 책임 속에 숨은 감정과 열이 들어 있는 배합입니다. 삶에서는 생활 통찰·관리 감각 쪽으로 강점이 드러나지만, 책임을 우선하다 감정을 눌러 뒤늦게 피로와 불만이 터질 수 있습니다.",
  "戊癸계수": "무계는 큰 책임 속에 숨은 감정과 열이 들어 있는 배합입니다. 삶에서는 생활 통찰·관리 감각 쪽으로 강점이 드러나지만, 책임을 우선하다 감정을 눌러 뒤늦게 피로와 불만이 터질 수 있습니다.",
  "무토계수": "무계는 큰 책임 속에 숨은 감정과 열이 들어 있는 배합입니다. 삶에서는 생활 통찰·관리 감각 쪽으로 강점이 드러나지만, 책임을 우선하다 감정을 눌러 뒤늦게 피로와 불만이 터질 수 있습니다.",
  "戊癸무토+계수": "무계는 큰 책임 속에 숨은 감정과 열이 들어 있는 배합입니다. 삶에서는 생활 통찰·관리 감각 쪽으로 강점이 드러나지만, 책임을 우선하다 감정을 눌러 뒤늦게 피로와 불만이 터질 수 있습니다.",
  "계수戊癸": "무계는 큰 책임 속에 숨은 감정과 열이 들어 있는 배합입니다. 삶에서는 생활 통찰·관리 감각 쪽으로 강점이 드러나지만, 책임을 우선하다 감정을 눌러 뒤늦게 피로와 불만이 터질 수 있습니다.",
  "己庚경금": "기경은 생활 실무에서 강한 기술과 결단이 나오는 배합입니다. 수리·제작·기술 운용 분야에서 강점이 살아나며, 빠른 해결을 중시하다 말이 거칠고 단정적으로 들릴 수 있습니다.",
  "경금+己庚기토": "기경은 생활 실무에서 강한 기술과 결단이 나오는 배합입니다. 수리·제작·기술 운용 분야에서 강점이 살아나며, 빠른 해결을 중시하다 말이 거칠고 단정적으로 들릴 수 있습니다.",
  "己庚기토+경금": "기경은 생활 실무에서 강한 기술과 결단이 나오는 배합입니다. 수리·제작·기술 운용 분야에서 강점이 살아나며, 빠른 해결을 중시하다 말이 거칠고 단정적으로 들릴 수 있습니다.",
  "기토경금": "기경은 생활 실무에서 강한 기술과 결단이 나오는 배합입니다. 수리·제작·기술 운용 분야에서 강점이 살아나며, 빠른 해결을 중시하다 말이 거칠고 단정적으로 들릴 수 있습니다.",
  "己庚": "기경은 생활 실무에서 강한 기술과 결단이 나오는 배합입니다. 수리·제작·기술 운용 분야에서 강점이 살아나며, 빠른 해결을 중시하다 말이 거칠고 단정적으로 들릴 수 있습니다.",
  "경금己庚": "기경은 생활 실무에서 강한 기술과 결단이 나오는 배합입니다. 수리·제작·기술 운용 분야에서 강점이 살아나며, 빠른 해결을 중시하다 말이 거칠고 단정적으로 들릴 수 있습니다.",
  "신금己辛": "기신은 생활 속에서 미감과 품질을 세밀하게 뽑아내는 배합입니다. 서비스 품질·미감 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "己辛기토+신금": "기신은 생활 속에서 미감과 품질을 세밀하게 뽑아내는 배합입니다. 서비스 품질·미감 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "己辛신금": "기신은 생활 속에서 미감과 품질을 세밀하게 뽑아내는 배합입니다. 서비스 품질·미감 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "신금+己辛기토": "기신은 생활 속에서 미감과 품질을 세밀하게 뽑아내는 배합입니다. 서비스 품질·미감 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "己辛": "기신은 생활 속에서 미감과 품질을 세밀하게 뽑아내는 배합입니다. 서비스 품질·미감 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "기토신금": "기신은 생활 속에서 미감과 품질을 세밀하게 뽑아내는 배합입니다. 서비스 품질·미감 분야에서 강점이 살아나며, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "己壬임수": "기임은 생활 기반과 큰 흐름이 만나 현실적 불안과 관리 욕구를 만드는 배합입니다. 특히 재무·복지·생활 기획 측면에 힘이 실리며, 큰 변화와 일상 관리가 충돌하면 생활 리듬이 쉽게 흔들릴 수 있습니다.",
  "己壬": "기임은 생활 기반과 큰 흐름이 만나 현실적 불안과 관리 욕구를 만드는 배합입니다. 특히 재무·복지·생활 기획 측면에 힘이 실리며, 큰 변화와 일상 관리가 충돌하면 생활 리듬이 쉽게 흔들릴 수 있습니다.",
  "기토임수": "기임은 생활 기반과 큰 흐름이 만나 현실적 불안과 관리 욕구를 만드는 배합입니다. 특히 재무·복지·생활 기획 측면에 힘이 실리며, 큰 변화와 일상 관리가 충돌하면 생활 리듬이 쉽게 흔들릴 수 있습니다.",
  "임수+己壬기토": "기임은 생활 기반과 큰 흐름이 만나 현실적 불안과 관리 욕구를 만드는 배합입니다. 특히 재무·복지·생활 기획 측면에 힘이 실리며, 큰 변화와 일상 관리가 충돌하면 생활 리듬이 쉽게 흔들릴 수 있습니다.",
  "임수己壬": "기임은 생활 기반과 큰 흐름이 만나 현실적 불안과 관리 욕구를 만드는 배합입니다. 특히 재무·복지·생활 기획 측면에 힘이 실리며, 큰 변화와 일상 관리가 충돌하면 생활 리듬이 쉽게 흔들릴 수 있습니다.",
  "己壬기토+임수": "기임은 생활 기반과 큰 흐름이 만나 현실적 불안과 관리 욕구를 만드는 배합입니다. 특히 재무·복지·생활 기획 측면에 힘이 실리며, 큰 변화와 일상 관리가 충돌하면 생활 리듬이 쉽게 흔들릴 수 있습니다.",
  "계수+己癸기토": "기계는 생활의 흙과 섬세한 감정이 섞인 배합입니다. 특히 상담·관리·생활 정리 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "기토계수": "기계는 생활의 흙과 섬세한 감정이 섞인 배합입니다. 특히 상담·관리·생활 정리 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "己癸계수": "기계는 생활의 흙과 섬세한 감정이 섞인 배합입니다. 특히 상담·관리·생활 정리 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "계수己癸": "기계는 생활의 흙과 섬세한 감정이 섞인 배합입니다. 특히 상담·관리·생활 정리 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "己癸": "기계는 생활의 흙과 섬세한 감정이 섞인 배합입니다. 특히 상담·관리·생활 정리 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "己癸기토+계수": "기계는 생활의 흙과 섬세한 감정이 섞인 배합입니다. 특히 상담·관리·생활 정리 측면에 힘이 실리며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "신금+庚辛경금": "경신은 큰 칼과 작은 칼이 함께 있어 기준과 완성도가 강한 배합입니다. 삶에서는 정밀 판단·기술·품질 쪽으로 강점이 드러나지만, 판단이 날카로워지면 말과 관계가 지나치게 차가워질 수 있습니다.",
  "신금庚辛": "경신은 큰 칼과 작은 칼이 함께 있어 기준과 완성도가 강한 배합입니다. 삶에서는 정밀 판단·기술·품질 쪽으로 강점이 드러나지만, 판단이 날카로워지면 말과 관계가 지나치게 차가워질 수 있습니다.",
  "경금신금": "경신은 큰 칼과 작은 칼이 함께 있어 기준과 완성도가 강한 배합입니다. 삶에서는 정밀 판단·기술·품질 쪽으로 강점이 드러나지만, 판단이 날카로워지면 말과 관계가 지나치게 차가워질 수 있습니다.",
  "庚辛신금": "경신은 큰 칼과 작은 칼이 함께 있어 기준과 완성도가 강한 배합입니다. 삶에서는 정밀 판단·기술·품질 쪽으로 강점이 드러나지만, 판단이 날카로워지면 말과 관계가 지나치게 차가워질 수 있습니다.",
  "庚辛": "경신은 큰 칼과 작은 칼이 함께 있어 기준과 완성도가 강한 배합입니다. 삶에서는 정밀 판단·기술·품질 쪽으로 강점이 드러나지만, 판단이 날카로워지면 말과 관계가 지나치게 차가워질 수 있습니다.",
  "庚辛경금+신금": "경신은 큰 칼과 작은 칼이 함께 있어 기준과 완성도가 강한 배합입니다. 삶에서는 정밀 판단·기술·품질 쪽으로 강점이 드러나지만, 판단이 날카로워지면 말과 관계가 지나치게 차가워질 수 있습니다.",
  "경금임수": "경임은 강한 판단이 큰 정보와 전략으로 흘러가는 배합입니다. 정보 분석·기술 전략 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "庚壬경금+임수": "경임은 강한 판단이 큰 정보와 전략으로 흘러가는 배합입니다. 정보 분석·기술 전략 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "임수+庚壬경금": "경임은 강한 판단이 큰 정보와 전략으로 흘러가는 배합입니다. 정보 분석·기술 전략 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "임수庚壬": "경임은 강한 판단이 큰 정보와 전략으로 흘러가는 배합입니다. 정보 분석·기술 전략 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "庚壬임수": "경임은 강한 판단이 큰 정보와 전략으로 흘러가는 배합입니다. 정보 분석·기술 전략 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "庚壬": "경임은 강한 판단이 큰 정보와 전략으로 흘러가는 배합입니다. 정보 분석·기술 전략 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "계수+庚癸경금": "경계는 큰 결단과 섬세한 정보가 만나 날카로운 분석을 만드는 배합입니다. 데이터 분석·문제 진단 측면이 실제 장점으로 작동하는 한편, 작은 정보에도 지나치게 경계해 결론을 서두를 수 있습니다.",
  "경금계수": "경계는 큰 결단과 섬세한 정보가 만나 날카로운 분석을 만드는 배합입니다. 데이터 분석·문제 진단 측면이 실제 장점으로 작동하는 한편, 작은 정보에도 지나치게 경계해 결론을 서두를 수 있습니다.",
  "庚癸경금+계수": "경계는 큰 결단과 섬세한 정보가 만나 날카로운 분석을 만드는 배합입니다. 데이터 분석·문제 진단 측면이 실제 장점으로 작동하는 한편, 작은 정보에도 지나치게 경계해 결론을 서두를 수 있습니다.",
  "계수庚癸": "경계는 큰 결단과 섬세한 정보가 만나 날카로운 분석을 만드는 배합입니다. 데이터 분석·문제 진단 측면이 실제 장점으로 작동하는 한편, 작은 정보에도 지나치게 경계해 결론을 서두를 수 있습니다.",
  "庚癸계수": "경계는 큰 결단과 섬세한 정보가 만나 날카로운 분석을 만드는 배합입니다. 데이터 분석·문제 진단 측면이 실제 장점으로 작동하는 한편, 작은 정보에도 지나치게 경계해 결론을 서두를 수 있습니다.",
  "庚癸": "경계는 큰 결단과 섬세한 정보가 만나 날카로운 분석을 만드는 배합입니다. 데이터 분석·문제 진단 측면이 실제 장점으로 작동하는 한편, 작은 정보에도 지나치게 경계해 결론을 서두를 수 있습니다.",
  "辛壬": "신임은 세련된 기준이 넓은 정보와 시장으로 흘러가는 배합입니다. 브랜딩 전략·금융 감각 측면이 실제 장점으로 작동하는 한편, 필요에 따라 관계를 바꾸다 신뢰의 지속성이 약해질 수 있습니다.",
  "辛壬신금+임수": "신임은 세련된 기준이 넓은 정보와 시장으로 흘러가는 배합입니다. 브랜딩 전략·금융 감각 측면이 실제 장점으로 작동하는 한편, 필요에 따라 관계를 바꾸다 신뢰의 지속성이 약해질 수 있습니다.",
  "辛壬임수": "신임은 세련된 기준이 넓은 정보와 시장으로 흘러가는 배합입니다. 브랜딩 전략·금융 감각 측면이 실제 장점으로 작동하는 한편, 필요에 따라 관계를 바꾸다 신뢰의 지속성이 약해질 수 있습니다.",
  "임수辛壬": "신임은 세련된 기준이 넓은 정보와 시장으로 흘러가는 배합입니다. 브랜딩 전략·금융 감각 측면이 실제 장점으로 작동하는 한편, 필요에 따라 관계를 바꾸다 신뢰의 지속성이 약해질 수 있습니다.",
  "신금임수": "신임은 세련된 기준이 넓은 정보와 시장으로 흘러가는 배합입니다. 브랜딩 전략·금융 감각 측면이 실제 장점으로 작동하는 한편, 필요에 따라 관계를 바꾸다 신뢰의 지속성이 약해질 수 있습니다.",
  "임수+辛壬신금": "신임은 세련된 기준이 넓은 정보와 시장으로 흘러가는 배합입니다. 브랜딩 전략·금융 감각 측면이 실제 장점으로 작동하는 한편, 필요에 따라 관계를 바꾸다 신뢰의 지속성이 약해질 수 있습니다.",
  "辛癸신금+계수": "신계는 보석 위의 이슬처럼 섬세한 감각과 기억이 강한 배합입니다. 정밀 분석·미감 측면이 실제 장점으로 작동하는 한편, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "계수+辛癸신금": "신계는 보석 위의 이슬처럼 섬세한 감각과 기억이 강한 배합입니다. 정밀 분석·미감 측면이 실제 장점으로 작동하는 한편, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "辛癸계수": "신계는 보석 위의 이슬처럼 섬세한 감각과 기억이 강한 배합입니다. 정밀 분석·미감 측면이 실제 장점으로 작동하는 한편, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "신금계수": "신계는 보석 위의 이슬처럼 섬세한 감각과 기억이 강한 배합입니다. 정밀 분석·미감 측면이 실제 장점으로 작동하는 한편, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "辛癸": "신계는 보석 위의 이슬처럼 섬세한 감각과 기억이 강한 배합입니다. 정밀 분석·미감 측면이 실제 장점으로 작동하는 한편, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "계수辛癸": "신계는 보석 위의 이슬처럼 섬세한 감각과 기억이 강한 배합입니다. 정밀 분석·미감 측면이 실제 장점으로 작동하는 한편, 비교와 질투가 커지면 직접 말하지 못한 불만과 관계 피로가 쌓일 수 있습니다.",
  "계수壬癸": "임계는 큰 물과 작은 물이 함께 있어 정보와 감정의 깊이가 큰 배합입니다. 정보 수집·심리 감지 분야에서 강점이 살아나며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "壬癸임수+계수": "임계는 큰 물과 작은 물이 함께 있어 정보와 감정의 깊이가 큰 배합입니다. 정보 수집·심리 감지 분야에서 강점이 살아나며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "계수+壬癸임수": "임계는 큰 물과 작은 물이 함께 있어 정보와 감정의 깊이가 큰 배합입니다. 정보 수집·심리 감지 분야에서 강점이 살아나며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "임수계수": "임계는 큰 물과 작은 물이 함께 있어 정보와 감정의 깊이가 큰 배합입니다. 정보 수집·심리 감지 분야에서 강점이 살아나며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "壬癸": "임계는 큰 물과 작은 물이 함께 있어 정보와 감정의 깊이가 큰 배합입니다. 정보 수집·심리 감지 분야에서 강점이 살아나며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "壬癸계수": "임계는 큰 물과 작은 물이 함께 있어 정보와 감정의 깊이가 큰 배합입니다. 정보 수집·심리 감지 분야에서 강점이 살아나며, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "比肩비견": "비견은 자기 기준과 독립성을 지키며 동등한 사람과 나란히 서는 기운입니다. 자기 주도·지속력 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "비견比肩": "비견은 자기 기준과 독립성을 지키며 동등한 사람과 나란히 서는 기운입니다. 자기 주도·지속력 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "비견(比肩)": "비견은 자기 기준과 독립성을 지키며 동등한 사람과 나란히 서는 기운입니다. 자기 주도·지속력 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "比肩": "비견은 자기 기준과 독립성을 지키며 동등한 사람과 나란히 서는 기운입니다. 자기 주도·지속력 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "비견": "비견은 자기 기준과 독립성을 지키며 동등한 사람과 나란히 서는 기운입니다. 자기 주도·지속력 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "겁재(劫財)": "겁재는 사람을 끌어들이고 무리 속에서 경쟁과 분배를 만드는 기운입니다. 사람 끌기·경쟁 감각 측면이 실제 장점으로 작동하는 한편, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "겁재劫財": "겁재는 사람을 끌어들이고 무리 속에서 경쟁과 분배를 만드는 기운입니다. 사람 끌기·경쟁 감각 측면이 실제 장점으로 작동하는 한편, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "劫財": "겁재는 사람을 끌어들이고 무리 속에서 경쟁과 분배를 만드는 기운입니다. 사람 끌기·경쟁 감각 측면이 실제 장점으로 작동하는 한편, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "겁재": "겁재는 사람을 끌어들이고 무리 속에서 경쟁과 분배를 만드는 기운입니다. 사람 끌기·경쟁 감각 측면이 실제 장점으로 작동하는 한편, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "劫財겁재": "겁재는 사람을 끌어들이고 무리 속에서 경쟁과 분배를 만드는 기운입니다. 사람 끌기·경쟁 감각 측면이 실제 장점으로 작동하는 한편, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "식신": "식신은 내가 만든 것으로 먹고사는 재주와 안정된 생산력을 뜻합니다. 생산력·기술력 분야에서 강점이 살아나며, 결과물은 쌓여도 가격 책정과 판매가 늦어질 수 있습니다.",
  "食神식신": "식신은 내가 만든 것으로 먹고사는 재주와 안정된 생산력을 뜻합니다. 생산력·기술력 분야에서 강점이 살아나며, 결과물은 쌓여도 가격 책정과 판매가 늦어질 수 있습니다.",
  "食神": "식신은 내가 만든 것으로 먹고사는 재주와 안정된 생산력을 뜻합니다. 생산력·기술력 분야에서 강점이 살아나며, 결과물은 쌓여도 가격 책정과 판매가 늦어질 수 있습니다.",
  "식신食神": "식신은 내가 만든 것으로 먹고사는 재주와 안정된 생산력을 뜻합니다. 생산력·기술력 분야에서 강점이 살아나며, 결과물은 쌓여도 가격 책정과 판매가 늦어질 수 있습니다.",
  "식신(食神)": "식신은 내가 만든 것으로 먹고사는 재주와 안정된 생산력을 뜻합니다. 생산력·기술력 분야에서 강점이 살아나며, 결과물은 쌓여도 가격 책정과 판매가 늦어질 수 있습니다.",
  "傷官상관": "상관은 말, 끼, 재능 과시, 비판과 반항이 강한 표현의 기운입니다. 삶에서는 언변·창의성 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "傷官": "상관은 말, 끼, 재능 과시, 비판과 반항이 강한 표현의 기운입니다. 삶에서는 언변·창의성 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "상관": "상관은 말, 끼, 재능 과시, 비판과 반항이 강한 표현의 기운입니다. 삶에서는 언변·창의성 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "상관傷官": "상관은 말, 끼, 재능 과시, 비판과 반항이 강한 표현의 기운입니다. 삶에서는 언변·창의성 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "상관(傷官)": "상관은 말, 끼, 재능 과시, 비판과 반항이 강한 표현의 기운입니다. 삶에서는 언변·창의성 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "정재正財": "정재는 안정된 돈, 생활비, 고정 수입, 현실 책임의 기운입니다. 관리 능력·생활 설계 측면이 실제 장점으로 작동하는 한편, 안정을 지키려다 돈과 생활 기준을 지나치게 통제할 수 있습니다.",
  "정재": "정재는 안정된 돈, 생활비, 고정 수입, 현실 책임의 기운입니다. 관리 능력·생활 설계 측면이 실제 장점으로 작동하는 한편, 안정을 지키려다 돈과 생활 기준을 지나치게 통제할 수 있습니다.",
  "正財": "정재는 안정된 돈, 생활비, 고정 수입, 현실 책임의 기운입니다. 관리 능력·생활 설계 측면이 실제 장점으로 작동하는 한편, 안정을 지키려다 돈과 생활 기준을 지나치게 통제할 수 있습니다.",
  "正財정재": "정재는 안정된 돈, 생활비, 고정 수입, 현실 책임의 기운입니다. 관리 능력·생활 설계 측면이 실제 장점으로 작동하는 한편, 안정을 지키려다 돈과 생활 기준을 지나치게 통제할 수 있습니다.",
  "정재(正財)": "정재는 안정된 돈, 생활비, 고정 수입, 현실 책임의 기운입니다. 관리 능력·생활 설계 측면이 실제 장점으로 작동하는 한편, 안정을 지키려다 돈과 생활 기준을 지나치게 통제할 수 있습니다.",
  "편재": "편재는 큰돈, 바깥돈, 거래, 인맥, 기회, 유동성의 기운입니다. 삶에서는 사업 감각·영업력 쪽으로 강점이 드러나지만, 기회를 크게 좇으면 지출과 위험한 선택의 폭도 커질 수 있습니다.",
  "偏財편재": "편재는 큰돈, 바깥돈, 거래, 인맥, 기회, 유동성의 기운입니다. 삶에서는 사업 감각·영업력 쪽으로 강점이 드러나지만, 기회를 크게 좇으면 지출과 위험한 선택의 폭도 커질 수 있습니다.",
  "偏財": "편재는 큰돈, 바깥돈, 거래, 인맥, 기회, 유동성의 기운입니다. 삶에서는 사업 감각·영업력 쪽으로 강점이 드러나지만, 기회를 크게 좇으면 지출과 위험한 선택의 폭도 커질 수 있습니다.",
  "편재(偏財)": "편재는 큰돈, 바깥돈, 거래, 인맥, 기회, 유동성의 기운입니다. 삶에서는 사업 감각·영업력 쪽으로 강점이 드러나지만, 기회를 크게 좇으면 지출과 위험한 선택의 폭도 커질 수 있습니다.",
  "편재偏財": "편재는 큰돈, 바깥돈, 거래, 인맥, 기회, 유동성의 기운입니다. 삶에서는 사업 감각·영업력 쪽으로 강점이 드러나지만, 기회를 크게 좇으면 지출과 위험한 선택의 폭도 커질 수 있습니다.",
  "정관正官": "정관은 직장, 직함, 책임, 명예, 공식 관계와 평판의 기운입니다. 삶에서는 조직 적응·공적 신뢰 쪽으로 강점이 드러나지만, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "정관": "정관은 직장, 직함, 책임, 명예, 공식 관계와 평판의 기운입니다. 삶에서는 조직 적응·공적 신뢰 쪽으로 강점이 드러나지만, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "正官정관": "정관은 직장, 직함, 책임, 명예, 공식 관계와 평판의 기운입니다. 삶에서는 조직 적응·공적 신뢰 쪽으로 강점이 드러나지만, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "正官": "정관은 직장, 직함, 책임, 명예, 공식 관계와 평판의 기운입니다. 삶에서는 조직 적응·공적 신뢰 쪽으로 강점이 드러나지만, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "정관(正官)": "정관은 직장, 직함, 책임, 명예, 공식 관계와 평판의 기운입니다. 삶에서는 조직 적응·공적 신뢰 쪽으로 강점이 드러나지만, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "편관": "편관은 압박, 위험, 권력, 경쟁, 강한 상대와 실전 통솔의 기운입니다. 특히 통솔력·돌파력 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "偏官편관": "편관은 압박, 위험, 권력, 경쟁, 강한 상대와 실전 통솔의 기운입니다. 특히 통솔력·돌파력 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "偏官": "편관은 압박, 위험, 권력, 경쟁, 강한 상대와 실전 통솔의 기운입니다. 특히 통솔력·돌파력 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "편관偏官": "편관은 압박, 위험, 권력, 경쟁, 강한 상대와 실전 통솔의 기운입니다. 특히 통솔력·돌파력 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "편관(偏官)": "편관은 압박, 위험, 권력, 경쟁, 강한 상대와 실전 통솔의 기운입니다. 특히 통솔력·돌파력 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "정인(正印)": "정인은 보호, 학문, 자격, 문서, 제도권 지식의 기운입니다. 삶에서는 이론 정리·자격 취득 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "정인正印": "정인은 보호, 학문, 자격, 문서, 제도권 지식의 기운입니다. 삶에서는 이론 정리·자격 취득 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "正印": "정인은 보호, 학문, 자격, 문서, 제도권 지식의 기운입니다. 삶에서는 이론 정리·자격 취득 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "정인": "정인은 보호, 학문, 자격, 문서, 제도권 지식의 기운입니다. 삶에서는 이론 정리·자격 취득 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "正印정인": "정인은 보호, 학문, 자격, 문서, 제도권 지식의 기운입니다. 삶에서는 이론 정리·자격 취득 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "偏印": "편인은 비정형 지식, 직관, 몰입, 특수 재능, 의심과 고독의 기운입니다. 특히 비정형 지식·통찰력 측면에 힘이 실리며, 생각과 해석이 많아져 생산과 표현, 일상의 리듬을 막을 수 있습니다.",
  "편인(偏印)": "편인은 비정형 지식, 직관, 몰입, 특수 재능, 의심과 고독의 기운입니다. 특히 비정형 지식·통찰력 측면에 힘이 실리며, 생각과 해석이 많아져 생산과 표현, 일상의 리듬을 막을 수 있습니다.",
  "偏印편인": "편인은 비정형 지식, 직관, 몰입, 특수 재능, 의심과 고독의 기운입니다. 특히 비정형 지식·통찰력 측면에 힘이 실리며, 생각과 해석이 많아져 생산과 표현, 일상의 리듬을 막을 수 있습니다.",
  "편인偏印": "편인은 비정형 지식, 직관, 몰입, 특수 재능, 의심과 고독의 기운입니다. 특히 비정형 지식·통찰력 측면에 힘이 실리며, 생각과 해석이 많아져 생산과 표현, 일상의 리듬을 막을 수 있습니다.",
  "편인": "편인은 비정형 지식, 직관, 몰입, 특수 재능, 의심과 고독의 기운입니다. 특히 비정형 지식·통찰력 측면에 힘이 실리며, 생각과 해석이 많아져 생산과 표현, 일상의 리듬을 막을 수 있습니다.",
  "비견겁재": "비견과 겁재는 자기 기준이 강해지고, 사람 속에서 몫과 주도권을 다투는 배합입니다. 특히 무리 장악·생존력 측면에 힘이 실리며, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "비견+겁재": "비견과 겁재는 자기 기준이 강해지고, 사람 속에서 몫과 주도권을 다투는 배합입니다. 특히 무리 장악·생존력 측면에 힘이 실리며, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "겁재+비견": "비견과 겁재는 자기 기준이 강해지고, 사람 속에서 몫과 주도권을 다투는 배합입니다. 특히 무리 장악·생존력 측면에 힘이 실리며, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "비견+식신": "비견과 식신은 자기 힘으로 기술과 결과물을 꾸준히 만들어내는 배합입니다. 특히 기술 숙련·콘텐츠 생산 측면에 힘이 실리며, 결과물은 쌓여도 가격 책정과 판매가 늦어질 수 있습니다.",
  "식신+비견": "비견과 식신은 자기 힘으로 기술과 결과물을 꾸준히 만들어내는 배합입니다. 특히 기술 숙련·콘텐츠 생산 측면에 힘이 실리며, 결과물은 쌓여도 가격 책정과 판매가 늦어질 수 있습니다.",
  "비견식신": "비견과 식신은 자기 힘으로 기술과 결과물을 꾸준히 만들어내는 배합입니다. 특히 기술 숙련·콘텐츠 생산 측면에 힘이 실리며, 결과물은 쌓여도 가격 책정과 판매가 늦어질 수 있습니다.",
  "상관+비견": "비견과 상관은 자기 생각을 직접 드러내고 기존 기준에 맞서려는 배합입니다. 특히 언변·콘텐츠 감각 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "비견상관": "비견과 상관은 자기 생각을 직접 드러내고 기존 기준에 맞서려는 배합입니다. 특히 언변·콘텐츠 감각 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "비견+상관": "비견과 상관은 자기 생각을 직접 드러내고 기존 기준에 맞서려는 배합입니다. 특히 언변·콘텐츠 감각 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "비견정재": "비견과 정재는 자기 몫과 안정된 돈이 맞물려 소유와 정산을 강하게 의식하는 배합입니다. 특히 생활 관리·정산 감각 측면에 힘이 실리며, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "정재+비견": "비견과 정재는 자기 몫과 안정된 돈이 맞물려 소유와 정산을 강하게 의식하는 배합입니다. 특히 생활 관리·정산 감각 측면에 힘이 실리며, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "비견+정재": "비견과 정재는 자기 몫과 안정된 돈이 맞물려 소유와 정산을 강하게 의식하는 배합입니다. 특히 생활 관리·정산 감각 측면에 힘이 실리며, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "비견+편재": "비견과 편재는 큰돈과 기회를 자기 손으로 잡으려 하지만 사람과 분배 문제가 생기는 배합입니다. 사업성·시장 감각 분야에서 강점이 살아나며, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "편재+비견": "비견과 편재는 큰돈과 기회를 자기 손으로 잡으려 하지만 사람과 분배 문제가 생기는 배합입니다. 사업성·시장 감각 분야에서 강점이 살아나며, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "비견편재": "비견과 편재는 큰돈과 기회를 자기 손으로 잡으려 하지만 사람과 분배 문제가 생기는 배합입니다. 사업성·시장 감각 분야에서 강점이 살아나며, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "비견정관": "비견과 정관은 자기 기준을 사회적 책임과 공식 질서 안에 세우려는 배합입니다. 특히 조직 내 독립성·역할 수행 측면에 힘이 실리며, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "비견+정관": "비견과 정관은 자기 기준을 사회적 책임과 공식 질서 안에 세우려는 배합입니다. 특히 조직 내 독립성·역할 수행 측면에 힘이 실리며, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "정관+비견": "비견과 정관은 자기 기준을 사회적 책임과 공식 질서 안에 세우려는 배합입니다. 특히 조직 내 독립성·역할 수행 측면에 힘이 실리며, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "비견편관": "비견과 편관은 자기 힘으로 압박과 경쟁을 정면에서 버티는 배합입니다. 실전력·돌파력 분야에서 강점이 살아나며, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "비견+편관": "비견과 편관은 자기 힘으로 압박과 경쟁을 정면에서 버티는 배합입니다. 실전력·돌파력 분야에서 강점이 살아나며, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "편관+비견": "비견과 편관은 자기 힘으로 압박과 경쟁을 정면에서 버티는 배합입니다. 실전력·돌파력 분야에서 강점이 살아나며, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "비견정인": "비견과 정인은 배운 것을 자기 것으로 만들고 자기 기준의 전문성을 세우는 배합입니다. 특히 지식 축적·자격 취득 측면에 힘이 실리며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "정인+비견": "비견과 정인은 배운 것을 자기 것으로 만들고 자기 기준의 전문성을 세우는 배합입니다. 특히 지식 축적·자격 취득 측면에 힘이 실리며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "비견+정인": "비견과 정인은 배운 것을 자기 것으로 만들고 자기 기준의 전문성을 세우는 배합입니다. 특히 지식 축적·자격 취득 측면에 힘이 실리며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "비견+편인": "비견과 편인은 자기 세계와 비정형 지식이 강해져 독특한 전문성으로 가는 배합입니다. 비정형 지식·직관 분야에서 강점이 살아나며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "비견편인": "비견과 편인은 자기 세계와 비정형 지식이 강해져 독특한 전문성으로 가는 배합입니다. 비정형 지식·직관 분야에서 강점이 살아나며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "편인+비견": "비견과 편인은 자기 세계와 비정형 지식이 강해져 독특한 전문성으로 가는 배합입니다. 비정형 지식·직관 분야에서 강점이 살아나며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "겁재+식신": "겁재와 식신은 사람을 모아 결과물을 만들고 대중 친화적인 생산력을 키우는 배합입니다. 삶에서는 교육·생산·팬덤 활용 쪽으로 강점이 드러나지만, 사람을 많이 모을수록 성과와 수익의 분배 기준이 흐려질 수 있습니다.",
  "식신+겁재": "겁재와 식신은 사람을 모아 결과물을 만들고 대중 친화적인 생산력을 키우는 배합입니다. 삶에서는 교육·생산·팬덤 활용 쪽으로 강점이 드러나지만, 사람을 많이 모을수록 성과와 수익의 분배 기준이 흐려질 수 있습니다.",
  "겁재식신": "겁재와 식신은 사람을 모아 결과물을 만들고 대중 친화적인 생산력을 키우는 배합입니다. 삶에서는 교육·생산·팬덤 활용 쪽으로 강점이 드러나지만, 사람을 많이 모을수록 성과와 수익의 분배 기준이 흐려질 수 있습니다.",
  "겁재+상관": "겁재와 상관은 무리의 힘과 말의 도발이 합쳐져 대중성, 반항성, 구설이 강해지는 배합입니다. 삶에서는 말의 힘·이슈화 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "겁재상관": "겁재와 상관은 무리의 힘과 말의 도발이 합쳐져 대중성, 반항성, 구설이 강해지는 배합입니다. 삶에서는 말의 힘·이슈화 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "상관+겁재": "겁재와 상관은 무리의 힘과 말의 도발이 합쳐져 대중성, 반항성, 구설이 강해지는 배합입니다. 삶에서는 말의 힘·이슈화 쪽으로 강점이 드러나지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "겁재정재": "겁재와 정재는 가까운 사람과 안정된 돈이 섞여 정산과 손재가 생기기 쉬운 배합입니다. 삶에서는 대중 영업·생활 시장 감각 쪽으로 강점이 드러나지만, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "겁재+정재": "겁재와 정재는 가까운 사람과 안정된 돈이 섞여 정산과 손재가 생기기 쉬운 배합입니다. 삶에서는 대중 영업·생활 시장 감각 쪽으로 강점이 드러나지만, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "정재+겁재": "겁재와 정재는 가까운 사람과 안정된 돈이 섞여 정산과 손재가 생기기 쉬운 배합입니다. 삶에서는 대중 영업·생활 시장 감각 쪽으로 강점이 드러나지만, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "편재+겁재": "사람, 큰돈, 동업 기회가 한꺼번에 움직이며 시장을 넓게 공략하는 배합입니다. 영업과 확장에는 강하지만, 관계와 자금이 복잡해지면 큰 손실도 빠르게 커질 수 있습니다.",
  "겁재+편재": "사람, 큰돈, 동업 기회가 한꺼번에 움직이며 시장을 넓게 공략하는 배합입니다. 영업과 확장에는 강하지만, 관계와 자금이 복잡해지면 큰 손실도 빠르게 커질 수 있습니다.",
  "겁재편재": "사람, 큰돈, 동업 기회가 한꺼번에 움직이며 시장을 넓게 공략하는 배합입니다. 영업과 확장에는 강하지만, 관계와 자금이 복잡해지면 큰 손실도 빠르게 커질 수 있습니다.",
  "겁재정관": "겁재와 정관은 거친 경쟁성과 대중성을 공식 질서 안에 넣어 사회화하는 배합입니다. 삶에서는 대중 관리·규칙 부여 쪽으로 강점이 드러나지만, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "겁재+정관": "겁재와 정관은 거친 경쟁성과 대중성을 공식 질서 안에 넣어 사회화하는 배합입니다. 삶에서는 대중 관리·규칙 부여 쪽으로 강점이 드러나지만, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "정관+겁재": "겁재와 정관은 거친 경쟁성과 대중성을 공식 질서 안에 넣어 사회화하는 배합입니다. 삶에서는 대중 관리·규칙 부여 쪽으로 강점이 드러나지만, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "겁재편관": "겁재와 편관은 강한 사람과 강한 무리 속에서 권력과 생존 경쟁이 커지는 배합입니다. 특히 강한 통솔·현장 대응 측면에 힘이 실리며, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "편관+겁재": "겁재와 편관은 강한 사람과 강한 무리 속에서 권력과 생존 경쟁이 커지는 배합입니다. 특히 강한 통솔·현장 대응 측면에 힘이 실리며, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "겁재+편관": "겁재와 편관은 강한 사람과 강한 무리 속에서 권력과 생존 경쟁이 커지는 배합입니다. 특히 강한 통솔·현장 대응 측면에 힘이 실리며, 주도권을 둘러싼 갈등이 커지지 않도록 역할과 경계를 분명히 해야 합니다.",
  "겁재+정인": "겁재와 정인은 대중에게 인정받는 지식과 자격을 갖추고 사람들을 가르치는 배합입니다. 삶에서는 강의력·자격 활용 쪽으로 강점이 드러나지만, 가까운 관계에서도 자신의 시간과 책임 범위를 분명히 할 필요가 있습니다.",
  "겁재정인": "겁재와 정인은 대중에게 인정받는 지식과 자격을 갖추고 사람들을 가르치는 배합입니다. 삶에서는 강의력·자격 활용 쪽으로 강점이 드러나지만, 가까운 관계에서도 자신의 시간과 책임 범위를 분명히 할 필요가 있습니다.",
  "정인+겁재": "겁재와 정인은 대중에게 인정받는 지식과 자격을 갖추고 사람들을 가르치는 배합입니다. 삶에서는 강의력·자격 활용 쪽으로 강점이 드러나지만, 가까운 관계에서도 자신의 시간과 책임 범위를 분명히 할 필요가 있습니다.",
  "편인+겁재": "겁재와 편인은 특수한 지식과 직관을 대중에게 설득하려는 배합입니다. 특히 통찰 전달·신비감 측면에 힘이 실리며, 특수한 지식과 확신을 과장하면 신뢰를 잃을 수 있습니다.",
  "겁재+편인": "겁재와 편인은 특수한 지식과 직관을 대중에게 설득하려는 배합입니다. 특히 통찰 전달·신비감 측면에 힘이 실리며, 특수한 지식과 확신을 과장하면 신뢰를 잃을 수 있습니다.",
  "겁재편인": "겁재와 편인은 특수한 지식과 직관을 대중에게 설득하려는 배합입니다. 특히 통찰 전달·신비감 측면에 힘이 실리며, 특수한 지식과 확신을 과장하면 신뢰를 잃을 수 있습니다.",
  "상관+식신": "식신과 상관은 안정된 생산력과 튀는 표현력이 함께 있는 재능형 배합입니다. 삶에서는 기술과 말·콘텐츠 생산 쪽으로 강점이 드러나지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "식신상관": "식신과 상관은 안정된 생산력과 튀는 표현력이 함께 있는 재능형 배합입니다. 삶에서는 기술과 말·콘텐츠 생산 쪽으로 강점이 드러나지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "식신+상관": "식신과 상관은 안정된 생산력과 튀는 표현력이 함께 있는 재능형 배합입니다. 삶에서는 기술과 말·콘텐츠 생산 쪽으로 강점이 드러나지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "정재+식신": "식신과 정재는 만든 것을 안정된 수입과 생활비로 바꾸는 배합입니다. 삶에서는 기술 수익화·제품 생산 쪽으로 강점이 드러나지만, 작은 손익에 집착하면 더 큰 기회와 관계의 여유를 놓칠 수 있습니다.",
  "식신+정재": "식신과 정재는 만든 것을 안정된 수입과 생활비로 바꾸는 배합입니다. 삶에서는 기술 수익화·제품 생산 쪽으로 강점이 드러나지만, 작은 손익에 집착하면 더 큰 기회와 관계의 여유를 놓칠 수 있습니다.",
  "식신정재": "식신과 정재는 만든 것을 안정된 수입과 생활비로 바꾸는 배합입니다. 삶에서는 기술 수익화·제품 생산 쪽으로 강점이 드러나지만, 작은 손익에 집착하면 더 큰 기회와 관계의 여유를 놓칠 수 있습니다.",
  "편재+식신": "식신과 편재는 만든 것을 시장에 내놓고 큰돈으로 바꾸려는 배합입니다. 특히 상품화·판매 감각 측면에 힘이 실리며, 판매와 확장을 서두르면 비용이 수익보다 먼저 커질 수 있습니다.",
  "식신편재": "식신과 편재는 만든 것을 시장에 내놓고 큰돈으로 바꾸려는 배합입니다. 특히 상품화·판매 감각 측면에 힘이 실리며, 판매와 확장을 서두르면 비용이 수익보다 먼저 커질 수 있습니다.",
  "식신+편재": "식신과 편재는 만든 것을 시장에 내놓고 큰돈으로 바꾸려는 배합입니다. 특히 상품화·판매 감각 측면에 힘이 실리며, 판매와 확장을 서두르면 비용이 수익보다 먼저 커질 수 있습니다.",
  "식신정관": "식신과 정관은 기술과 성실함이 조직의 신뢰로 이어지는 배합입니다. 삶에서는 실무 신뢰·교육·관리 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "정관+식신": "식신과 정관은 기술과 성실함이 조직의 신뢰로 이어지는 배합입니다. 삶에서는 실무 신뢰·교육·관리 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "식신+정관": "식신과 정관은 기술과 성실함이 조직의 신뢰로 이어지는 배합입니다. 삶에서는 실무 신뢰·교육·관리 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "식신편관": "기술과 숙련으로 압박을 다루고 어려운 상황을 실력으로 안정시키는 배합입니다. 위기 대응과 전문 역량에 강하지만, 계속 버티는 방식은 과로와 긴장을 일상화할 수 있습니다.",
  "편관+식신": "기술과 숙련으로 압박을 다루고 어려운 상황을 실력으로 안정시키는 배합입니다. 위기 대응과 전문 역량에 강하지만, 계속 버티는 방식은 과로와 긴장을 일상화할 수 있습니다.",
  "식신+편관": "기술과 숙련으로 압박을 다루고 어려운 상황을 실력으로 안정시키는 배합입니다. 위기 대응과 전문 역량에 강하지만, 계속 버티는 방식은 과로와 긴장을 일상화할 수 있습니다.",
  "식신정인": "식신과 정인은 배운 것을 부드럽게 풀어내고 안정적인 교육·설명 능력을 만드는 배합입니다. 삶에서는 교육 능력·정리와 생산 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "식신+정인": "식신과 정인은 배운 것을 부드럽게 풀어내고 안정적인 교육·설명 능력을 만드는 배합입니다. 삶에서는 교육 능력·정리와 생산 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "정인+식신": "식신과 정인은 배운 것을 부드럽게 풀어내고 안정적인 교육·설명 능력을 만드는 배합입니다. 삶에서는 교육 능력·정리와 생산 쪽으로 강점이 드러나지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "식신편인": "생산 능력과 직관적 지식이 만나 독특한 기술과 통찰을 만드는 배합입니다. 생각과 해석이 지나치게 많아지면 실제로 만들고 표현하는 힘이 막힐 수 있습니다.",
  "식신+편인": "생산 능력과 직관적 지식이 만나 독특한 기술과 통찰을 만드는 배합입니다. 생각과 해석이 지나치게 많아지면 실제로 만들고 표현하는 힘이 막힐 수 있습니다.",
  "편인+식신": "생산 능력과 직관적 지식이 만나 독특한 기술과 통찰을 만드는 배합입니다. 생각과 해석이 지나치게 많아지면 실제로 만들고 표현하는 힘이 막힐 수 있습니다.",
  "정재+상관": "상관과 정재는 말과 재능을 실속 있는 돈으로 바꾸려는 배합입니다. 삶에서는 판매 언변·기획 수익화 쪽으로 강점이 드러나지만, 표현과 거래가 얽히면 가격과 약속을 둘러싼 다툼이 생길 수 있습니다.",
  "상관+정재": "상관과 정재는 말과 재능을 실속 있는 돈으로 바꾸려는 배합입니다. 삶에서는 판매 언변·기획 수익화 쪽으로 강점이 드러나지만, 표현과 거래가 얽히면 가격과 약속을 둘러싼 다툼이 생길 수 있습니다.",
  "상관정재": "상관과 정재는 말과 재능을 실속 있는 돈으로 바꾸려는 배합입니다. 삶에서는 판매 언변·기획 수익화 쪽으로 강점이 드러나지만, 표현과 거래가 얽히면 가격과 약속을 둘러싼 다툼이 생길 수 있습니다.",
  "상관편재": "상관과 편재는 말, 끼, 기술을 시장에 던져 큰돈과 이슈를 만들려는 배합입니다. 특히 마케팅 감각·이슈화 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "편재+상관": "상관과 편재는 말, 끼, 기술을 시장에 던져 큰돈과 이슈를 만들려는 배합입니다. 특히 마케팅 감각·이슈화 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "상관+편재": "상관과 편재는 말, 끼, 기술을 시장에 던져 큰돈과 이슈를 만들려는 배합입니다. 특히 마케팅 감각·이슈화 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "상관정관": "자기 표현과 공식 질서가 부딪혀 기존 제도의 문제를 드러내고 고치려는 배합입니다. 개선과 문제 제기에는 강하지만, 표현 방식이 거칠면 직장 관계와 평판이 흔들릴 수 있습니다.",
  "정관+상관": "자기 표현과 공식 질서가 부딪혀 기존 제도의 문제를 드러내고 고치려는 배합입니다. 개선과 문제 제기에는 강하지만, 표현 방식이 거칠면 직장 관계와 평판이 흔들릴 수 있습니다.",
  "상관+정관": "자기 표현과 공식 질서가 부딪혀 기존 제도의 문제를 드러내고 고치려는 배합입니다. 개선과 문제 제기에는 강하지만, 표현 방식이 거칠면 직장 관계와 평판이 흔들릴 수 있습니다.",
  "편관+상관": "상관과 편관은 강한 압박에 말과 재능으로 맞서는 배합입니다. 특히 위기 언변·전략적 공격 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "상관+편관": "상관과 편관은 강한 압박에 말과 재능으로 맞서는 배합입니다. 특히 위기 언변·전략적 공격 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "상관편관": "상관과 편관은 강한 압박에 말과 재능으로 맞서는 배합입니다. 특히 위기 언변·전략적 공격 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "상관정인": "상관과 정인은 거친 표현이 학문과 문서로 다듬어지는 배합입니다. 삶에서는 글과 이론·강의력 쪽으로 강점이 드러나지만, 설명과 논리가 길어지면 실제 행동과 상대의 반응을 놓칠 수 있습니다.",
  "정인+상관": "상관과 정인은 거친 표현이 학문과 문서로 다듬어지는 배합입니다. 삶에서는 글과 이론·강의력 쪽으로 강점이 드러나지만, 설명과 논리가 길어지면 실제 행동과 상대의 반응을 놓칠 수 있습니다.",
  "상관+정인": "상관과 정인은 거친 표현이 학문과 문서로 다듬어지는 배합입니다. 삶에서는 글과 이론·강의력 쪽으로 강점이 드러나지만, 설명과 논리가 길어지면 실제 행동과 상대의 반응을 놓칠 수 있습니다.",
  "상관+편인": "상관과 편인은 독특한 말과 비정형 지식이 결합해 강한 개성과 불안을 만드는 배합입니다. 특히 특수 콘텐츠·심리 해석 측면에 힘이 실리며, 독특한 해석을 사실처럼 단정하면 관계와 평판이 흔들릴 수 있습니다.",
  "상관편인": "상관과 편인은 독특한 말과 비정형 지식이 결합해 강한 개성과 불안을 만드는 배합입니다. 특히 특수 콘텐츠·심리 해석 측면에 힘이 실리며, 독특한 해석을 사실처럼 단정하면 관계와 평판이 흔들릴 수 있습니다.",
  "편인+상관": "상관과 편인은 독특한 말과 비정형 지식이 결합해 강한 개성과 불안을 만드는 배합입니다. 특히 특수 콘텐츠·심리 해석 측면에 힘이 실리며, 독특한 해석을 사실처럼 단정하면 관계와 평판이 흔들릴 수 있습니다.",
  "정재편재": "정재와 편재는 안정된 돈과 큰돈의 기회가 함께 있어 재물 욕구와 소비 규모가 커지는 배합입니다. 특히 돈 감각·자산과 거래 측면에 힘이 실리며, 안정과 큰 기회를 동시에 좇으면 돈의 기준과 관계가 복잡해질 수 있습니다.",
  "정재+편재": "정재와 편재는 안정된 돈과 큰돈의 기회가 함께 있어 재물 욕구와 소비 규모가 커지는 배합입니다. 특히 돈 감각·자산과 거래 측면에 힘이 실리며, 안정과 큰 기회를 동시에 좇으면 돈의 기준과 관계가 복잡해질 수 있습니다.",
  "편재+정재": "정재와 편재는 안정된 돈과 큰돈의 기회가 함께 있어 재물 욕구와 소비 규모가 커지는 배합입니다. 특히 돈 감각·자산과 거래 측면에 힘이 실리며, 안정과 큰 기회를 동시에 좇으면 돈의 기준과 관계가 복잡해질 수 있습니다.",
  "정재+정관": "정재와 정관은 돈과 생활 책임이 직장·명예·공식 지위로 이어지는 배합입니다. 삶에서는 관리 능력·조직 신뢰 쪽으로 강점이 드러나지만, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "정재정관": "정재와 정관은 돈과 생활 책임이 직장·명예·공식 지위로 이어지는 배합입니다. 삶에서는 관리 능력·조직 신뢰 쪽으로 강점이 드러나지만, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "정관+정재": "정재와 정관은 돈과 생활 책임이 직장·명예·공식 지위로 이어지는 배합입니다. 삶에서는 관리 능력·조직 신뢰 쪽으로 강점이 드러나지만, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "정재편관": "정재와 편관은 안정된 돈이 강한 책임과 압박으로 연결되는 배합입니다. 특히 리스크 관리·계약 대응 측면에 힘이 실리며, 안정된 수입을 지키려다 부담스러운 책임과 계약을 끌고 갈 수 있습니다.",
  "편관+정재": "정재와 편관은 안정된 돈이 강한 책임과 압박으로 연결되는 배합입니다. 특히 리스크 관리·계약 대응 측면에 힘이 실리며, 안정된 수입을 지키려다 부담스러운 책임과 계약을 끌고 갈 수 있습니다.",
  "정재+편관": "정재와 편관은 안정된 돈이 강한 책임과 압박으로 연결되는 배합입니다. 특히 리스크 관리·계약 대응 측면에 힘이 실리며, 안정된 수입을 지키려다 부담스러운 책임과 계약을 끌고 갈 수 있습니다.",
  "정인+정재": "정재와 정인은 돈과 생활 현실이 공부·문서·보호를 누르거나, 문서로 돈을 지키는 배합입니다. 삶에서는 문서 재무·자격 활용 쪽으로 강점이 드러나지만, 현실적 이익을 앞세우다 배움과 회복, 장기 준비를 소홀히 할 수 있습니다.",
  "정재+정인": "정재와 정인은 돈과 생활 현실이 공부·문서·보호를 누르거나, 문서로 돈을 지키는 배합입니다. 삶에서는 문서 재무·자격 활용 쪽으로 강점이 드러나지만, 현실적 이익을 앞세우다 배움과 회복, 장기 준비를 소홀히 할 수 있습니다.",
  "정재정인": "정재와 정인은 돈과 생활 현실이 공부·문서·보호를 누르거나, 문서로 돈을 지키는 배합입니다. 삶에서는 문서 재무·자격 활용 쪽으로 강점이 드러나지만, 현실적 이익을 앞세우다 배움과 회복, 장기 준비를 소홀히 할 수 있습니다.",
  "정재+편인": "정재와 편인은 현실의 돈과 특수한 지식이 부딪히거나 결합하는 배합입니다. 특히 특수 자문·숨은 돈 분석 측면에 힘이 실리며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "정재편인": "정재와 편인은 현실의 돈과 특수한 지식이 부딪히거나 결합하는 배합입니다. 특히 특수 자문·숨은 돈 분석 측면에 힘이 실리며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "편인+정재": "정재와 편인은 현실의 돈과 특수한 지식이 부딪히거나 결합하는 배합입니다. 특히 특수 자문·숨은 돈 분석 측면에 힘이 실리며, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "편재+정관": "편재와 정관은 큰돈과 외부 기회가 직위·명예·공식 계약으로 정리되는 배합입니다. 특히 사업 제도화·대외 신뢰 측면에 힘이 실리며, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "편재정관": "편재와 정관은 큰돈과 외부 기회가 직위·명예·공식 계약으로 정리되는 배합입니다. 특히 사업 제도화·대외 신뢰 측면에 힘이 실리며, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "정관+편재": "편재와 정관은 큰돈과 외부 기회가 직위·명예·공식 계약으로 정리되는 배합입니다. 특히 사업 제도화·대외 신뢰 측면에 힘이 실리며, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "편재편관": "편재와 편관은 큰돈, 권력, 위험, 강한 책임이 함께 움직이는 배합입니다. 대형 사업·위기 거래 분야에서 강점이 살아나며, 큰돈과 권한을 함께 다룰 때 과감한 판단이 큰 손실로 번질 수 있습니다.",
  "편관+편재": "편재와 편관은 큰돈, 권력, 위험, 강한 책임이 함께 움직이는 배합입니다. 대형 사업·위기 거래 분야에서 강점이 살아나며, 큰돈과 권한을 함께 다룰 때 과감한 판단이 큰 손실로 번질 수 있습니다.",
  "편재+편관": "편재와 편관은 큰돈, 권력, 위험, 강한 책임이 함께 움직이는 배합입니다. 대형 사업·위기 거래 분야에서 강점이 살아나며, 큰돈과 권한을 함께 다룰 때 과감한 판단이 큰 손실로 번질 수 있습니다.",
  "편재+정인": "편재와 정인은 큰돈과 외부 기회를 문서·자격·보호로 정리하려는 배합입니다. 특히 계약 문서·사업 지식 측면에 힘이 실리며, 현실적 이익을 앞세우다 배움과 회복, 장기 준비를 소홀히 할 수 있습니다.",
  "정인+편재": "편재와 정인은 큰돈과 외부 기회를 문서·자격·보호로 정리하려는 배합입니다. 특히 계약 문서·사업 지식 측면에 힘이 실리며, 현실적 이익을 앞세우다 배움과 회복, 장기 준비를 소홀히 할 수 있습니다.",
  "편재정인": "편재와 정인은 큰돈과 외부 기회를 문서·자격·보호로 정리하려는 배합입니다. 특히 계약 문서·사업 지식 측면에 힘이 실리며, 현실적 이익을 앞세우다 배움과 회복, 장기 준비를 소홀히 할 수 있습니다.",
  "편재+편인": "편재와 편인은 비주류 지식이나 특수 감각을 시장과 돈으로 연결하는 배합입니다. 특수 상담·시장형 통찰 분야에서 강점이 살아나며, 특수한 정보와 큰 수익을 함께 좇을 때 검증 절차를 놓치기 쉽습니다.",
  "편재편인": "편재와 편인은 비주류 지식이나 특수 감각을 시장과 돈으로 연결하는 배합입니다. 특수 상담·시장형 통찰 분야에서 강점이 살아나며, 특수한 정보와 큰 수익을 함께 좇을 때 검증 절차를 놓치기 쉽습니다.",
  "편인+편재": "편재와 편인은 비주류 지식이나 특수 감각을 시장과 돈으로 연결하는 배합입니다. 특수 상담·시장형 통찰 분야에서 강점이 살아나며, 특수한 정보와 큰 수익을 함께 좇을 때 검증 절차를 놓치기 쉽습니다.",
  "편관+정관": "정관과 편관은 공식 책임과 강한 압박이 섞여 직장·배우자·권력 기준이 복잡해지는 배합입니다. 특히 위기 조직화·권한 처리 측면에 힘이 실리며, 여러 책임과 권위가 겹치면 누구의 기준을 따라야 할지 혼란스러울 수 있습니다.",
  "정관+편관": "정관과 편관은 공식 책임과 강한 압박이 섞여 직장·배우자·권력 기준이 복잡해지는 배합입니다. 특히 위기 조직화·권한 처리 측면에 힘이 실리며, 여러 책임과 권위가 겹치면 누구의 기준을 따라야 할지 혼란스러울 수 있습니다.",
  "정관편관": "정관과 편관은 공식 책임과 강한 압박이 섞여 직장·배우자·권력 기준이 복잡해지는 배합입니다. 특히 위기 조직화·권한 처리 측면에 힘이 실리며, 여러 책임과 권위가 겹치면 누구의 기준을 따라야 할지 혼란스러울 수 있습니다.",
  "정관+정인": "책임과 직위가 학습, 자격, 문서의 힘으로 안정적으로 뒷받침되는 배합입니다. 조직의 신뢰를 얻기 좋지만, 제도와 권위에 기대면 자기 판단과 유연성이 약해질 수 있습니다.",
  "정관정인": "책임과 직위가 학습, 자격, 문서의 힘으로 안정적으로 뒷받침되는 배합입니다. 조직의 신뢰를 얻기 좋지만, 제도와 권위에 기대면 자기 판단과 유연성이 약해질 수 있습니다.",
  "정인+정관": "책임과 직위가 학습, 자격, 문서의 힘으로 안정적으로 뒷받침되는 배합입니다. 조직의 신뢰를 얻기 좋지만, 제도와 권위에 기대면 자기 판단과 유연성이 약해질 수 있습니다.",
  "정관편인": "정관과 편인은 공식 책임이 비정형 지식과 만나 특수 전문성으로 가는 배합입니다. 특히 전문 해석·특수 자격 측면에 힘이 실리며, 독특한 판단 방식이 조직의 공식 절차와 어긋나 소외감을 느낄 수 있습니다.",
  "편인+정관": "정관과 편인은 공식 책임이 비정형 지식과 만나 특수 전문성으로 가는 배합입니다. 특히 전문 해석·특수 자격 측면에 힘이 실리며, 독특한 판단 방식이 조직의 공식 절차와 어긋나 소외감을 느낄 수 있습니다.",
  "정관+편인": "정관과 편인은 공식 책임이 비정형 지식과 만나 특수 전문성으로 가는 배합입니다. 특히 전문 해석·특수 자격 측면에 힘이 실리며, 독특한 판단 방식이 조직의 공식 절차와 어긋나 소외감을 느낄 수 있습니다.",
  "편관+정인": "강한 압박과 위기를 학습, 자격, 문서의 힘으로 체계화해 다루는 배합입니다. 전문 책임에는 강하지만, 오래 버티는 데 익숙해져 긴장과 피로를 늦게 알아차릴 수 있습니다.",
  "편관정인": "강한 압박과 위기를 학습, 자격, 문서의 힘으로 체계화해 다루는 배합입니다. 전문 책임에는 강하지만, 오래 버티는 데 익숙해져 긴장과 피로를 늦게 알아차릴 수 있습니다.",
  "정인+편관": "강한 압박과 위기를 학습, 자격, 문서의 힘으로 체계화해 다루는 배합입니다. 전문 책임에는 강하지만, 오래 버티는 데 익숙해져 긴장과 피로를 늦게 알아차릴 수 있습니다.",
  "편관+편인": "편관과 편인은 압박과 불안, 직관과 특수 지식이 결합해 강한 비정형 전문성을 만드는 배합입니다. 비정형 전문성·심리·위기 해석 분야에서 강점이 살아나며, 압박이 커지면 불안한 해석과 과도한 경계가 강해질 수 있습니다.",
  "편관편인": "편관과 편인은 압박과 불안, 직관과 특수 지식이 결합해 강한 비정형 전문성을 만드는 배합입니다. 비정형 전문성·심리·위기 해석 분야에서 강점이 살아나며, 압박이 커지면 불안한 해석과 과도한 경계가 강해질 수 있습니다.",
  "편인+편관": "편관과 편인은 압박과 불안, 직관과 특수 지식이 결합해 강한 비정형 전문성을 만드는 배합입니다. 비정형 전문성·심리·위기 해석 분야에서 강점이 살아나며, 압박이 커지면 불안한 해석과 과도한 경계가 강해질 수 있습니다.",
  "정인+편인": "정인과 편인은 제도권 지식과 비정형 지식이 함께 있어 공부와 해석이 깊어지지만 실행이 늦어지는 배합입니다. 특히 정통과 비정형 지식·깊은 연구 측면에 힘이 실리며, 생각과 해석이 복잡해져 실제 선택과 실행이 늦어질 수 있습니다.",
  "정인편인": "정인과 편인은 제도권 지식과 비정형 지식이 함께 있어 공부와 해석이 깊어지지만 실행이 늦어지는 배합입니다. 특히 정통과 비정형 지식·깊은 연구 측면에 힘이 실리며, 생각과 해석이 복잡해져 실제 선택과 실행이 늦어질 수 있습니다.",
  "편인+정인": "정인과 편인은 제도권 지식과 비정형 지식이 함께 있어 공부와 해석이 깊어지지만 실행이 늦어지는 배합입니다. 특히 정통과 비정형 지식·깊은 연구 측면에 힘이 실리며, 생각과 해석이 복잡해져 실제 선택과 실행이 늦어질 수 있습니다.",
  "자축합(子丑合)": "두 기운이 서로 묶이며 주된 반응이 은근한 집착·생활 안정 욕구 쪽으로 모이는 작용입니다. 축적력·관리 감각에 힘이 실리지만, 가까운 사람의 문제를 자신의 책임으로 모두 떠안지 않도록 경계를 세워야 합니다.",
  "자축합": "두 기운이 서로 묶이며 주된 반응이 은근한 집착·생활 안정 욕구 쪽으로 모이는 작용입니다. 축적력·관리 감각에 힘이 실리지만, 가까운 사람의 문제를 자신의 책임으로 모두 떠안지 않도록 경계를 세워야 합니다.",
  "子丑合자축합": "두 기운이 서로 묶이며 주된 반응이 은근한 집착·생활 안정 욕구 쪽으로 모이는 작용입니다. 축적력·관리 감각에 힘이 실리지만, 가까운 사람의 문제를 자신의 책임으로 모두 떠안지 않도록 경계를 세워야 합니다.",
  "자축합子丑合": "두 기운이 서로 묶이며 주된 반응이 은근한 집착·생활 안정 욕구 쪽으로 모이는 작용입니다. 축적력·관리 감각에 힘이 실리지만, 가까운 사람의 문제를 자신의 책임으로 모두 떠안지 않도록 경계를 세워야 합니다.",
  "子丑合": "두 기운이 서로 묶이며 주된 반응이 은근한 집착·생활 안정 욕구 쪽으로 모이는 작용입니다. 축적력·관리 감각에 힘이 실리지만, 가까운 사람의 문제를 자신의 책임으로 모두 떠안지 않도록 경계를 세워야 합니다.",
  "인해합": "두 기운이 서로 묶이며 주된 반응이 호기심·정서적 깊이 쪽으로 모이는 작용입니다. 학습 확장·상상력에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "寅亥合인해합": "두 기운이 서로 묶이며 주된 반응이 호기심·정서적 깊이 쪽으로 모이는 작용입니다. 학습 확장·상상력에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "인해합寅亥合": "두 기운이 서로 묶이며 주된 반응이 호기심·정서적 깊이 쪽으로 모이는 작용입니다. 학습 확장·상상력에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "寅亥合": "두 기운이 서로 묶이며 주된 반응이 호기심·정서적 깊이 쪽으로 모이는 작용입니다. 학습 확장·상상력에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "인해합(寅亥合)": "두 기운이 서로 묶이며 주된 반응이 호기심·정서적 깊이 쪽으로 모이는 작용입니다. 학습 확장·상상력에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "卯戌合": "두 기운이 서로 묶이며 주된 반응이 가능성 집착·사람을 키우려는 마음 쪽으로 모이는 작용입니다. 교정 능력·교육 감각에 힘이 실리지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "卯戌合묘술합": "두 기운이 서로 묶이며 주된 반응이 가능성 집착·사람을 키우려는 마음 쪽으로 모이는 작용입니다. 교정 능력·교육 감각에 힘이 실리지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "묘술합(卯戌合)": "두 기운이 서로 묶이며 주된 반응이 가능성 집착·사람을 키우려는 마음 쪽으로 모이는 작용입니다. 교정 능력·교육 감각에 힘이 실리지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "묘술합": "두 기운이 서로 묶이며 주된 반응이 가능성 집착·사람을 키우려는 마음 쪽으로 모이는 작용입니다. 교정 능력·교육 감각에 힘이 실리지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "묘술합卯戌合": "두 기운이 서로 묶이며 주된 반응이 가능성 집착·사람을 키우려는 마음 쪽으로 모이는 작용입니다. 교정 능력·교육 감각에 힘이 실리지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "辰酉合진유합": "두 기운이 서로 묶이며 주된 반응이 현실 감각·계산적 판단 쪽으로 모이는 작용입니다. 정리 능력·품질 감각에 힘이 실리지만, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "진유합": "두 기운이 서로 묶이며 주된 반응이 현실 감각·계산적 판단 쪽으로 모이는 작용입니다. 정리 능력·품질 감각에 힘이 실리지만, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "진유합辰酉合": "두 기운이 서로 묶이며 주된 반응이 현실 감각·계산적 판단 쪽으로 모이는 작용입니다. 정리 능력·품질 감각에 힘이 실리지만, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "辰酉合": "두 기운이 서로 묶이며 주된 반응이 현실 감각·계산적 판단 쪽으로 모이는 작용입니다. 정리 능력·품질 감각에 힘이 실리지만, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "진유합(辰酉合)": "두 기운이 서로 묶이며 주된 반응이 현실 감각·계산적 판단 쪽으로 모이는 작용입니다. 정리 능력·품질 감각에 힘이 실리지만, 사람과 돈이 얽히면 몫과 정산을 둘러싼 갈등이 커질 수 있습니다.",
  "사신합(巳申合)": "두 기운이 서로 묶이며 주된 반응이 빠른 눈치·전략적 태도 쪽으로 모이는 작용입니다. 기술 감각·협상력에 힘이 실리지만, 작은 말과 약속의 어긋남이 누적되면 신뢰가 빠르게 약해질 수 있습니다.",
  "巳申合": "두 기운이 서로 묶이며 주된 반응이 빠른 눈치·전략적 태도 쪽으로 모이는 작용입니다. 기술 감각·협상력에 힘이 실리지만, 작은 말과 약속의 어긋남이 누적되면 신뢰가 빠르게 약해질 수 있습니다.",
  "사신합": "두 기운이 서로 묶이며 주된 반응이 빠른 눈치·전략적 태도 쪽으로 모이는 작용입니다. 기술 감각·협상력에 힘이 실리지만, 작은 말과 약속의 어긋남이 누적되면 신뢰가 빠르게 약해질 수 있습니다.",
  "사신합巳申合": "두 기운이 서로 묶이며 주된 반응이 빠른 눈치·전략적 태도 쪽으로 모이는 작용입니다. 기술 감각·협상력에 힘이 실리지만, 작은 말과 약속의 어긋남이 누적되면 신뢰가 빠르게 약해질 수 있습니다.",
  "巳申合사신합": "두 기운이 서로 묶이며 주된 반응이 빠른 눈치·전략적 태도 쪽으로 모이는 작용입니다. 기술 감각·협상력에 힘이 실리지만, 작은 말과 약속의 어긋남이 누적되면 신뢰가 빠르게 약해질 수 있습니다.",
  "오미합午未合": "두 기운이 서로 묶이며 주된 반응이 따뜻한 결속·체면 의식 쪽으로 모이는 작용입니다. 사람 챙김·분위기 조성에 힘이 실리지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "오미합(午未合)": "두 기운이 서로 묶이며 주된 반응이 따뜻한 결속·체면 의식 쪽으로 모이는 작용입니다. 사람 챙김·분위기 조성에 힘이 실리지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "午未合오미합": "두 기운이 서로 묶이며 주된 반응이 따뜻한 결속·체면 의식 쪽으로 모이는 작용입니다. 사람 챙김·분위기 조성에 힘이 실리지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "午未合": "두 기운이 서로 묶이며 주된 반응이 따뜻한 결속·체면 의식 쪽으로 모이는 작용입니다. 사람 챙김·분위기 조성에 힘이 실리지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "오미합": "두 기운이 서로 묶이며 주된 반응이 따뜻한 결속·체면 의식 쪽으로 모이는 작용입니다. 사람 챙김·분위기 조성에 힘이 실리지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "신자진수국(申子辰三合水局)": "세 기운이 한 방향으로 모이며 주된 반응이 정보 민감·이동성 쪽으로 모이는 작용입니다. 네트워크 감각·정보 수집력에 힘이 실리지만, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "신자진수국": "세 기운이 한 방향으로 모이며 주된 반응이 정보 민감·이동성 쪽으로 모이는 작용입니다. 네트워크 감각·정보 수집력에 힘이 실리지만, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "신자진": "세 기운이 한 방향으로 모이며 주된 반응이 정보 민감·이동성 쪽으로 모이는 작용입니다. 네트워크 감각·정보 수집력에 힘이 실리지만, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "申子辰三合水局": "세 기운이 한 방향으로 모이며 주된 반응이 정보 민감·이동성 쪽으로 모이는 작용입니다. 네트워크 감각·정보 수집력에 힘이 실리지만, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "申子辰三合水局수국": "세 기운이 한 방향으로 모이며 주된 반응이 정보 민감·이동성 쪽으로 모이는 작용입니다. 네트워크 감각·정보 수집력에 힘이 실리지만, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "수국申子辰三合水局": "세 기운이 한 방향으로 모이며 주된 반응이 정보 민감·이동성 쪽으로 모이는 작용입니다. 네트워크 감각·정보 수집력에 힘이 실리지만, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "수국": "세 기운이 한 방향으로 모이며 주된 반응이 정보 민감·이동성 쪽으로 모이는 작용입니다. 네트워크 감각·정보 수집력에 힘이 실리지만, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "亥卯未三合木局": "세 기운이 한 방향으로 모이며 주된 반응이 성장 욕구·이상 추구 쪽으로 모이는 작용입니다. 교육 감각·예술·상담 감각에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "해묘미": "세 기운이 한 방향으로 모이며 주된 반응이 성장 욕구·이상 추구 쪽으로 모이는 작용입니다. 교육 감각·예술·상담 감각에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "亥卯未三合木局목국": "세 기운이 한 방향으로 모이며 주된 반응이 성장 욕구·이상 추구 쪽으로 모이는 작용입니다. 교육 감각·예술·상담 감각에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "해묘미목국(亥卯未三合木局)": "세 기운이 한 방향으로 모이며 주된 반응이 성장 욕구·이상 추구 쪽으로 모이는 작용입니다. 교육 감각·예술·상담 감각에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "해묘미목국": "세 기운이 한 방향으로 모이며 주된 반응이 성장 욕구·이상 추구 쪽으로 모이는 작용입니다. 교육 감각·예술·상담 감각에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "목국": "세 기운이 한 방향으로 모이며 주된 반응이 성장 욕구·이상 추구 쪽으로 모이는 작용입니다. 교육 감각·예술·상담 감각에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "목국亥卯未三合木局": "세 기운이 한 방향으로 모이며 주된 반응이 성장 욕구·이상 추구 쪽으로 모이는 작용입니다. 교육 감각·예술·상담 감각에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "화국寅午戌三合火局": "세 기운이 한 방향으로 모이며 주된 반응이 표현 욕구·명예 욕구 쪽으로 모이는 작용입니다. 리더십·설득력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "寅午戌三合火局": "세 기운이 한 방향으로 모이며 주된 반응이 표현 욕구·명예 욕구 쪽으로 모이는 작용입니다. 리더십·설득력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "화국": "세 기운이 한 방향으로 모이며 주된 반응이 표현 욕구·명예 욕구 쪽으로 모이는 작용입니다. 리더십·설득력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "寅午戌三合火局화국": "세 기운이 한 방향으로 모이며 주된 반응이 표현 욕구·명예 욕구 쪽으로 모이는 작용입니다. 리더십·설득력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "인오술화국(寅午戌三合火局)": "세 기운이 한 방향으로 모이며 주된 반응이 표현 욕구·명예 욕구 쪽으로 모이는 작용입니다. 리더십·설득력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "인오술": "세 기운이 한 방향으로 모이며 주된 반응이 표현 욕구·명예 욕구 쪽으로 모이는 작용입니다. 리더십·설득력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "인오술화국": "세 기운이 한 방향으로 모이며 주된 반응이 표현 욕구·명예 욕구 쪽으로 모이는 작용입니다. 리더십·설득력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "금국": "세 기운이 한 방향으로 모이며 주된 반응이 분별력·완성도 의식 쪽으로 모이는 작용입니다. 품질 관리·금전 감각에 힘이 실리지만, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "巳酉丑三合金局": "세 기운이 한 방향으로 모이며 주된 반응이 분별력·완성도 의식 쪽으로 모이는 작용입니다. 품질 관리·금전 감각에 힘이 실리지만, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "사유축": "세 기운이 한 방향으로 모이며 주된 반응이 분별력·완성도 의식 쪽으로 모이는 작용입니다. 품질 관리·금전 감각에 힘이 실리지만, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "사유축금국": "세 기운이 한 방향으로 모이며 주된 반응이 분별력·완성도 의식 쪽으로 모이는 작용입니다. 품질 관리·금전 감각에 힘이 실리지만, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "사유축금국(巳酉丑三合金局)": "세 기운이 한 방향으로 모이며 주된 반응이 분별력·완성도 의식 쪽으로 모이는 작용입니다. 품질 관리·금전 감각에 힘이 실리지만, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "금국巳酉丑三合金局": "세 기운이 한 방향으로 모이며 주된 반응이 분별력·완성도 의식 쪽으로 모이는 작용입니다. 품질 관리·금전 감각에 힘이 실리지만, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "巳酉丑三合金局금국": "세 기운이 한 방향으로 모이며 주된 반응이 분별력·완성도 의식 쪽으로 모이는 작용입니다. 품질 관리·금전 감각에 힘이 실리지만, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "신자반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 정보 반응·빠른 이동감 쪽으로 모이는 작용입니다. 네트워크 감각·거래 촉에 힘이 실리지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "신자반합(申子半合水)": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 정보 반응·빠른 이동감 쪽으로 모이는 작용입니다. 네트워크 감각·거래 촉에 힘이 실리지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "申子半合水": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 정보 반응·빠른 이동감 쪽으로 모이는 작용입니다. 네트워크 감각·거래 촉에 힘이 실리지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "신자반합申子半合水": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 정보 반응·빠른 이동감 쪽으로 모이는 작용입니다. 네트워크 감각·거래 촉에 힘이 실리지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "申子半合水신자반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 정보 반응·빠른 이동감 쪽으로 모이는 작용입니다. 네트워크 감각·거래 촉에 힘이 실리지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "자진반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 깊은 저장성·현실적 계산 쪽으로 모이는 작용입니다. 자금 관리·정보 축적에 힘이 실리지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "자진반합子辰半合水": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 깊은 저장성·현실적 계산 쪽으로 모이는 작용입니다. 자금 관리·정보 축적에 힘이 실리지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "자진반합(子辰半合水)": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 깊은 저장성·현실적 계산 쪽으로 모이는 작용입니다. 자금 관리·정보 축적에 힘이 실리지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "子辰半合水": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 깊은 저장성·현실적 계산 쪽으로 모이는 작용입니다. 자금 관리·정보 축적에 힘이 실리지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "子辰半合水자진반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 깊은 저장성·현실적 계산 쪽으로 모이는 작용입니다. 자금 관리·정보 축적에 힘이 실리지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "신진공합申辰拱水": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 잠재 이동성·기회 대기 쪽으로 모이는 작용입니다. 기술 축적·정보 대기력에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "申辰拱水": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 잠재 이동성·기회 대기 쪽으로 모이는 작용입니다. 기술 축적·정보 대기력에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "신진공합(申辰拱水)": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 잠재 이동성·기회 대기 쪽으로 모이는 작용입니다. 기술 축적·정보 대기력에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "신진공합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 잠재 이동성·기회 대기 쪽으로 모이는 작용입니다. 기술 축적·정보 대기력에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "申辰拱水신진공합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 잠재 이동성·기회 대기 쪽으로 모이는 작용입니다. 기술 축적·정보 대기력에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "해묘반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 감성 확장·이상 지향 쪽으로 모이는 작용입니다. 상담 감각·창작 감각에 힘이 실리지만, 가까운 관계에서도 자신의 시간과 책임 범위를 분명히 할 필요가 있습니다.",
  "亥卯半合木": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 감성 확장·이상 지향 쪽으로 모이는 작용입니다. 상담 감각·창작 감각에 힘이 실리지만, 가까운 관계에서도 자신의 시간과 책임 범위를 분명히 할 필요가 있습니다.",
  "해묘반합亥卯半合木": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 감성 확장·이상 지향 쪽으로 모이는 작용입니다. 상담 감각·창작 감각에 힘이 실리지만, 가까운 관계에서도 자신의 시간과 책임 범위를 분명히 할 필요가 있습니다.",
  "亥卯半合木해묘반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 감성 확장·이상 지향 쪽으로 모이는 작용입니다. 상담 감각·창작 감각에 힘이 실리지만, 가까운 관계에서도 자신의 시간과 책임 범위를 분명히 할 필요가 있습니다.",
  "해묘반합(亥卯半合木)": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 감성 확장·이상 지향 쪽으로 모이는 작용입니다. 상담 감각·창작 감각에 힘이 실리지만, 가까운 관계에서도 자신의 시간과 책임 범위를 분명히 할 필요가 있습니다.",
  "묘미반합卯未半合木": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 관계 돌봄·생활형 이상 쪽으로 모이는 작용입니다. 사람 키움·공동체 감각에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "묘미반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 관계 돌봄·생활형 이상 쪽으로 모이는 작용입니다. 사람 키움·공동체 감각에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "묘미반합(卯未半合木)": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 관계 돌봄·생활형 이상 쪽으로 모이는 작용입니다. 사람 키움·공동체 감각에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "卯未半合木묘미반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 관계 돌봄·생활형 이상 쪽으로 모이는 작용입니다. 사람 키움·공동체 감각에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "卯未半合木": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 관계 돌봄·생활형 이상 쪽으로 모이는 작용입니다. 사람 키움·공동체 감각에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "해미공합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 내면 이상·상상 속 성장 쪽으로 모이는 작용입니다. 기획 상상력·장기 교육 감각에 힘이 실리지만, 가능성을 오래 그리다 현실의 실행과 검증이 늦어질 수 있습니다.",
  "해미공합(亥未拱木)": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 내면 이상·상상 속 성장 쪽으로 모이는 작용입니다. 기획 상상력·장기 교육 감각에 힘이 실리지만, 가능성을 오래 그리다 현실의 실행과 검증이 늦어질 수 있습니다.",
  "亥未拱木": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 내면 이상·상상 속 성장 쪽으로 모이는 작용입니다. 기획 상상력·장기 교육 감각에 힘이 실리지만, 가능성을 오래 그리다 현실의 실행과 검증이 늦어질 수 있습니다.",
  "亥未拱木해미공합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 내면 이상·상상 속 성장 쪽으로 모이는 작용입니다. 기획 상상력·장기 교육 감각에 힘이 실리지만, 가능성을 오래 그리다 현실의 실행과 검증이 늦어질 수 있습니다.",
  "해미공합亥未拱木": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 내면 이상·상상 속 성장 쪽으로 모이는 작용입니다. 기획 상상력·장기 교육 감각에 힘이 실리지만, 가능성을 오래 그리다 현실의 실행과 검증이 늦어질 수 있습니다.",
  "寅午半合火인오반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 강한 추진·표현 욕구 쪽으로 모이는 작용입니다. 설득력·대외 존재감에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "인오반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 강한 추진·표현 욕구 쪽으로 모이는 작용입니다. 설득력·대외 존재감에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "寅午半合火": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 강한 추진·표현 욕구 쪽으로 모이는 작용입니다. 설득력·대외 존재감에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "인오반합寅午半合火": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 강한 추진·표현 욕구 쪽으로 모이는 작용입니다. 설득력·대외 존재감에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "인오반합(寅午半合火)": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 강한 추진·표현 욕구 쪽으로 모이는 작용입니다. 설득력·대외 존재감에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "午戌半合火": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 명예 의식·의리 쪽으로 모이는 작용입니다. 조직 결속·책임감에 힘이 실리지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "오술반합午戌半合火": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 명예 의식·의리 쪽으로 모이는 작용입니다. 조직 결속·책임감에 힘이 실리지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "午戌半合火오술반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 명예 의식·의리 쪽으로 모이는 작용입니다. 조직 결속·책임감에 힘이 실리지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "오술반합(午戌半合火)": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 명예 의식·의리 쪽으로 모이는 작용입니다. 조직 결속·책임감에 힘이 실리지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "오술반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 명예 의식·의리 쪽으로 모이는 작용입니다. 조직 결속·책임감에 힘이 실리지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "인술공합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 잠재 명예욕·의로운 고집 쪽으로 모이는 작용입니다. 비전 제시·조직 구상에 힘이 실리지만, 명분과 구상이 앞서면 실제 행동이 늦고 의견 충돌이 커질 수 있습니다.",
  "인술공합(寅戌拱火)": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 잠재 명예욕·의로운 고집 쪽으로 모이는 작용입니다. 비전 제시·조직 구상에 힘이 실리지만, 명분과 구상이 앞서면 실제 행동이 늦고 의견 충돌이 커질 수 있습니다.",
  "인술공합寅戌拱火": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 잠재 명예욕·의로운 고집 쪽으로 모이는 작용입니다. 비전 제시·조직 구상에 힘이 실리지만, 명분과 구상이 앞서면 실제 행동이 늦고 의견 충돌이 커질 수 있습니다.",
  "寅戌拱火인술공합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 잠재 명예욕·의로운 고집 쪽으로 모이는 작용입니다. 비전 제시·조직 구상에 힘이 실리지만, 명분과 구상이 앞서면 실제 행동이 늦고 의견 충돌이 커질 수 있습니다.",
  "寅戌拱火": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 잠재 명예욕·의로운 고집 쪽으로 모이는 작용입니다. 비전 제시·조직 구상에 힘이 실리지만, 명분과 구상이 앞서면 실제 행동이 늦고 의견 충돌이 커질 수 있습니다.",
  "사유반합巳酉半合金": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 정교한 판단·세련됨 쪽으로 모이는 작용입니다. 품질 감각·금전 감각에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "사유반합(巳酉半合金)": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 정교한 판단·세련됨 쪽으로 모이는 작용입니다. 품질 감각·금전 감각에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "巳酉半合金사유반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 정교한 판단·세련됨 쪽으로 모이는 작용입니다. 품질 감각·금전 감각에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "사유반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 정교한 판단·세련됨 쪽으로 모이는 작용입니다. 품질 감각·금전 감각에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "巳酉半合金": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 정교한 판단·세련됨 쪽으로 모이는 작용입니다. 품질 감각·금전 감각에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "유축반합酉丑半合金": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 실속·보수적 평가 쪽으로 모이는 작용입니다. 자산 보존·정밀 관리에 힘이 실리지만, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "유축반합(酉丑半合金)": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 실속·보수적 평가 쪽으로 모이는 작용입니다. 자산 보존·정밀 관리에 힘이 실리지만, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "酉丑半合金유축반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 실속·보수적 평가 쪽으로 모이는 작용입니다. 자산 보존·정밀 관리에 힘이 실리지만, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "酉丑半合金": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 실속·보수적 평가 쪽으로 모이는 작용입니다. 자산 보존·정밀 관리에 힘이 실리지만, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "유축반합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 실속·보수적 평가 쪽으로 모이는 작용입니다. 자산 보존·정밀 관리에 힘이 실리지만, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "巳丑拱金사축공합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 숨은 기준·내부 계산 쪽으로 모이는 작용입니다. 기술 축적·품질 잠재력에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "巳丑拱金": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 숨은 기준·내부 계산 쪽으로 모이는 작용입니다. 기술 축적·품질 잠재력에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "사축공합巳丑拱金": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 숨은 기준·내부 계산 쪽으로 모이는 작용입니다. 기술 축적·품질 잠재력에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "사축공합(巳丑拱金)": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 숨은 기준·내부 계산 쪽으로 모이는 작용입니다. 기술 축적·품질 잠재력에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "사축공합": "완전한 결속보다 특정 방향의 가능성을 키우며 주된 반응이 숨은 기준·내부 계산 쪽으로 모이는 작용입니다. 기술 축적·품질 잠재력에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "寅卯辰方合木": "같은 계절의 기운이 모여 주된 반응이 성장 본능·확장 욕구 쪽으로 모이는 작용입니다. 기획력·교육 감각에 힘이 실리지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "인묘진목방합": "같은 계절의 기운이 모여 주된 반응이 성장 본능·확장 욕구 쪽으로 모이는 작용입니다. 기획력·교육 감각에 힘이 실리지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "목방합": "같은 계절의 기운이 모여 주된 반응이 성장 본능·확장 욕구 쪽으로 모이는 작용입니다. 기획력·교육 감각에 힘이 실리지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "인묘진": "같은 계절의 기운이 모여 주된 반응이 성장 본능·확장 욕구 쪽으로 모이는 작용입니다. 기획력·교육 감각에 힘이 실리지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "寅卯辰方合木목방합": "같은 계절의 기운이 모여 주된 반응이 성장 본능·확장 욕구 쪽으로 모이는 작용입니다. 기획력·교육 감각에 힘이 실리지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "인묘진목방합(寅卯辰方合木)": "같은 계절의 기운이 모여 주된 반응이 성장 본능·확장 욕구 쪽으로 모이는 작용입니다. 기획력·교육 감각에 힘이 실리지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "목방합寅卯辰方合木": "같은 계절의 기운이 모여 주된 반응이 성장 본능·확장 욕구 쪽으로 모이는 작용입니다. 기획력·교육 감각에 힘이 실리지만, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "사오미화방합": "같은 계절의 기운이 모여 주된 반응이 표현 과잉·열정 쪽으로 모이는 작용입니다. 무대 감각·설득력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "화방합巳午未方合火": "같은 계절의 기운이 모여 주된 반응이 표현 과잉·열정 쪽으로 모이는 작용입니다. 무대 감각·설득력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "사오미": "같은 계절의 기운이 모여 주된 반응이 표현 과잉·열정 쪽으로 모이는 작용입니다. 무대 감각·설득력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "巳午未方合火": "같은 계절의 기운이 모여 주된 반응이 표현 과잉·열정 쪽으로 모이는 작용입니다. 무대 감각·설득력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "사오미화방합(巳午未方合火)": "같은 계절의 기운이 모여 주된 반응이 표현 과잉·열정 쪽으로 모이는 작용입니다. 무대 감각·설득력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "화방합": "같은 계절의 기운이 모여 주된 반응이 표현 과잉·열정 쪽으로 모이는 작용입니다. 무대 감각·설득력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "巳午未方合火화방합": "같은 계절의 기운이 모여 주된 반응이 표현 과잉·열정 쪽으로 모이는 작용입니다. 무대 감각·설득력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "금방합": "같은 계절의 기운이 모여 주된 반응이 분별력·완성도 집착 쪽으로 모이는 작용입니다. 정리·절단 능력·품질 관리에 힘이 실리지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "금방합申酉戌方合金": "같은 계절의 기운이 모여 주된 반응이 분별력·완성도 집착 쪽으로 모이는 작용입니다. 정리·절단 능력·품질 관리에 힘이 실리지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "申酉戌方合金": "같은 계절의 기운이 모여 주된 반응이 분별력·완성도 집착 쪽으로 모이는 작용입니다. 정리·절단 능력·품질 관리에 힘이 실리지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "신유술": "같은 계절의 기운이 모여 주된 반응이 분별력·완성도 집착 쪽으로 모이는 작용입니다. 정리·절단 능력·품질 관리에 힘이 실리지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "申酉戌方合金금방합": "같은 계절의 기운이 모여 주된 반응이 분별력·완성도 집착 쪽으로 모이는 작용입니다. 정리·절단 능력·품질 관리에 힘이 실리지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "신유술금방합(申酉戌方合金)": "같은 계절의 기운이 모여 주된 반응이 분별력·완성도 집착 쪽으로 모이는 작용입니다. 정리·절단 능력·품질 관리에 힘이 실리지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "신유술금방합": "같은 계절의 기운이 모여 주된 반응이 분별력·완성도 집착 쪽으로 모이는 작용입니다. 정리·절단 능력·품질 관리에 힘이 실리지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "수방합亥子丑方合水": "같은 계절의 기운이 모여 주된 반응이 깊은 내면·저장성 쪽으로 모이는 작용입니다. 정보 축적·위기 감지에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "해자축수방합": "같은 계절의 기운이 모여 주된 반응이 깊은 내면·저장성 쪽으로 모이는 작용입니다. 정보 축적·위기 감지에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "수방합": "같은 계절의 기운이 모여 주된 반응이 깊은 내면·저장성 쪽으로 모이는 작용입니다. 정보 축적·위기 감지에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "해자축수방합(亥子丑方合水)": "같은 계절의 기운이 모여 주된 반응이 깊은 내면·저장성 쪽으로 모이는 작용입니다. 정보 축적·위기 감지에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "亥子丑方合水": "같은 계절의 기운이 모여 주된 반응이 깊은 내면·저장성 쪽으로 모이는 작용입니다. 정보 축적·위기 감지에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "해자축": "같은 계절의 기운이 모여 주된 반응이 깊은 내면·저장성 쪽으로 모이는 작용입니다. 정보 축적·위기 감지에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "亥子丑方合水수방합": "같은 계절의 기운이 모여 주된 반응이 깊은 내면·저장성 쪽으로 모이는 작용입니다. 정보 축적·위기 감지에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "자오충": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 감정 기복·즉각 반응 쪽으로 모이는 작용입니다. 분위기 감지·빠른 판단에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "자오충(子午冲)": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 감정 기복·즉각 반응 쪽으로 모이는 작용입니다. 분위기 감지·빠른 판단에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "子午冲": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 감정 기복·즉각 반응 쪽으로 모이는 작용입니다. 분위기 감지·빠른 판단에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "子午冲자오충": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 감정 기복·즉각 반응 쪽으로 모이는 작용입니다. 분위기 감지·빠른 판단에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "자오충子午冲": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 감정 기복·즉각 반응 쪽으로 모이는 작용입니다. 분위기 감지·빠른 판단에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "축미충(丑未冲)": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 생활 압박·묵은 불만 쪽으로 모이는 작용입니다. 생활 관리·자산 감각에 힘이 실리지만, 생활과 책임의 차이를 오래 끌면 가족 안의 감정과 돈 문제가 함께 커질 수 있습니다.",
  "丑未冲": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 생활 압박·묵은 불만 쪽으로 모이는 작용입니다. 생활 관리·자산 감각에 힘이 실리지만, 생활과 책임의 차이를 오래 끌면 가족 안의 감정과 돈 문제가 함께 커질 수 있습니다.",
  "축미충丑未冲": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 생활 압박·묵은 불만 쪽으로 모이는 작용입니다. 생활 관리·자산 감각에 힘이 실리지만, 생활과 책임의 차이를 오래 끌면 가족 안의 감정과 돈 문제가 함께 커질 수 있습니다.",
  "축미충": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 생활 압박·묵은 불만 쪽으로 모이는 작용입니다. 생활 관리·자산 감각에 힘이 실리지만, 생활과 책임의 차이를 오래 끌면 가족 안의 감정과 돈 문제가 함께 커질 수 있습니다.",
  "丑未冲축미충": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 생활 압박·묵은 불만 쪽으로 모이는 작용입니다. 생활 관리·자산 감각에 힘이 실리지만, 생활과 책임의 차이를 오래 끌면 가족 안의 감정과 돈 문제가 함께 커질 수 있습니다.",
  "寅申冲": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 이동 욕구·경쟁심 쪽으로 모이는 작용입니다. 현장 대응·기술 개척에 힘이 실리지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "인신충(寅申冲)": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 이동 욕구·경쟁심 쪽으로 모이는 작용입니다. 현장 대응·기술 개척에 힘이 실리지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "인신충寅申冲": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 이동 욕구·경쟁심 쪽으로 모이는 작용입니다. 현장 대응·기술 개척에 힘이 실리지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "인신충": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 이동 욕구·경쟁심 쪽으로 모이는 작용입니다. 현장 대응·기술 개척에 힘이 실리지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "寅申冲인신충": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 이동 욕구·경쟁심 쪽으로 모이는 작용입니다. 현장 대응·기술 개척에 힘이 실리지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "묘유충卯酉冲": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 눈치 빠름·예민한 반응 쪽으로 모이는 작용입니다. 미감 발달·브랜딩 감각에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "묘유충": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 눈치 빠름·예민한 반응 쪽으로 모이는 작용입니다. 미감 발달·브랜딩 감각에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "묘유충(卯酉冲)": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 눈치 빠름·예민한 반응 쪽으로 모이는 작용입니다. 미감 발달·브랜딩 감각에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "卯酉冲": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 눈치 빠름·예민한 반응 쪽으로 모이는 작용입니다. 미감 발달·브랜딩 감각에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "卯酉冲묘유충": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 눈치 빠름·예민한 반응 쪽으로 모이는 작용입니다. 미감 발달·브랜딩 감각에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "진술충辰戌冲": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 내부 압박·고집 쪽으로 모이는 작용입니다. 위기 수습·자산 재편에 힘이 실리지만, 묵은 문제를 미루면 자산과 관계의 갈등이 한꺼번에 커질 수 있습니다.",
  "진술충": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 내부 압박·고집 쪽으로 모이는 작용입니다. 위기 수습·자산 재편에 힘이 실리지만, 묵은 문제를 미루면 자산과 관계의 갈등이 한꺼번에 커질 수 있습니다.",
  "辰戌冲": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 내부 압박·고집 쪽으로 모이는 작용입니다. 위기 수습·자산 재편에 힘이 실리지만, 묵은 문제를 미루면 자산과 관계의 갈등이 한꺼번에 커질 수 있습니다.",
  "진술충(辰戌冲)": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 내부 압박·고집 쪽으로 모이는 작용입니다. 위기 수습·자산 재편에 힘이 실리지만, 묵은 문제를 미루면 자산과 관계의 갈등이 한꺼번에 커질 수 있습니다.",
  "辰戌冲진술충": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 내부 압박·고집 쪽으로 모이는 작용입니다. 위기 수습·자산 재편에 힘이 실리지만, 묵은 문제를 미루면 자산과 관계의 갈등이 한꺼번에 커질 수 있습니다.",
  "巳亥冲사해충": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 비밀성·욕망과 불안 쪽으로 모이는 작용입니다. 감지력·위험 예측에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "사해충(巳亥冲)": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 비밀성·욕망과 불안 쪽으로 모이는 작용입니다. 감지력·위험 예측에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "巳亥冲": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 비밀성·욕망과 불안 쪽으로 모이는 작용입니다. 감지력·위험 예측에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "사해충": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 비밀성·욕망과 불안 쪽으로 모이는 작용입니다. 감지력·위험 예측에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "사해충巳亥冲": "서로 반대되는 기준이 정면으로 부딪혀 주된 반응이 비밀성·욕망과 불안 쪽으로 모이는 작용입니다. 감지력·위험 예측에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "인사형": "갈등과 압박이 반복되어 주된 반응이 성급한 추진·욕망 과열 쪽으로 모이는 작용입니다. 실행력·사업 추진에 힘이 실리지만, 규모를 먼저 키우면 자금과 책임이 감당 범위를 넘을 수 있습니다.",
  "寅巳刑": "갈등과 압박이 반복되어 주된 반응이 성급한 추진·욕망 과열 쪽으로 모이는 작용입니다. 실행력·사업 추진에 힘이 실리지만, 규모를 먼저 키우면 자금과 책임이 감당 범위를 넘을 수 있습니다.",
  "인사형寅巳刑": "갈등과 압박이 반복되어 주된 반응이 성급한 추진·욕망 과열 쪽으로 모이는 작용입니다. 실행력·사업 추진에 힘이 실리지만, 규모를 먼저 키우면 자금과 책임이 감당 범위를 넘을 수 있습니다.",
  "인사형(寅巳刑)": "갈등과 압박이 반복되어 주된 반응이 성급한 추진·욕망 과열 쪽으로 모이는 작용입니다. 실행력·사업 추진에 힘이 실리지만, 규모를 먼저 키우면 자금과 책임이 감당 범위를 넘을 수 있습니다.",
  "寅巳刑인사형": "갈등과 압박이 반복되어 주된 반응이 성급한 추진·욕망 과열 쪽으로 모이는 작용입니다. 실행력·사업 추진에 힘이 실리지만, 규모를 먼저 키우면 자금과 책임이 감당 범위를 넘을 수 있습니다.",
  "巳申刑": "갈등과 압박이 반복되어 주된 반응이 전략적 긴장·의심 쪽으로 모이는 작용입니다. 기술 분석·협상 감각에 힘이 실리지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "사신형巳申刑": "갈등과 압박이 반복되어 주된 반응이 전략적 긴장·의심 쪽으로 모이는 작용입니다. 기술 분석·협상 감각에 힘이 실리지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "巳申刑사신형": "갈등과 압박이 반복되어 주된 반응이 전략적 긴장·의심 쪽으로 모이는 작용입니다. 기술 분석·협상 감각에 힘이 실리지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "사신형": "갈등과 압박이 반복되어 주된 반응이 전략적 긴장·의심 쪽으로 모이는 작용입니다. 기술 분석·협상 감각에 힘이 실리지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "사신형(巳申刑)": "갈등과 압박이 반복되어 주된 반응이 전략적 긴장·의심 쪽으로 모이는 작용입니다. 기술 분석·협상 감각에 힘이 실리지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "인신형(寅申刑)": "갈등과 압박이 반복되어 주된 반응이 강한 독립성·주도권 욕구 쪽으로 모이는 작용입니다. 개척력·위기 대응에 힘이 실리지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "인신형寅申刑": "갈등과 압박이 반복되어 주된 반응이 강한 독립성·주도권 욕구 쪽으로 모이는 작용입니다. 개척력·위기 대응에 힘이 실리지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "寅申刑인신형": "갈등과 압박이 반복되어 주된 반응이 강한 독립성·주도권 욕구 쪽으로 모이는 작용입니다. 개척력·위기 대응에 힘이 실리지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "寅申刑": "갈등과 압박이 반복되어 주된 반응이 강한 독립성·주도권 욕구 쪽으로 모이는 작용입니다. 개척력·위기 대응에 힘이 실리지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "인신형": "갈등과 압박이 반복되어 주된 반응이 강한 독립성·주도권 욕구 쪽으로 모이는 작용입니다. 개척력·위기 대응에 힘이 실리지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "寅巳申三刑": "갈등과 압박이 반복되어 주된 반응이 강한 승부욕·압박 속 각성 쪽으로 모이는 작용입니다. 위기 돌파·권력 감각에 힘이 실리지만, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "인사신": "갈등과 압박이 반복되어 주된 반응이 강한 승부욕·압박 속 각성 쪽으로 모이는 작용입니다. 위기 돌파·권력 감각에 힘이 실리지만, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "삼형寅巳申三刑": "갈등과 압박이 반복되어 주된 반응이 강한 승부욕·압박 속 각성 쪽으로 모이는 작용입니다. 위기 돌파·권력 감각에 힘이 실리지만, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "인사신삼형": "갈등과 압박이 반복되어 주된 반응이 강한 승부욕·압박 속 각성 쪽으로 모이는 작용입니다. 위기 돌파·권력 감각에 힘이 실리지만, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "인사신삼형(寅巳申三刑)": "갈등과 압박이 반복되어 주된 반응이 강한 승부욕·압박 속 각성 쪽으로 모이는 작용입니다. 위기 돌파·권력 감각에 힘이 실리지만, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "寅巳申三刑삼형": "갈등과 압박이 반복되어 주된 반응이 강한 승부욕·압박 속 각성 쪽으로 모이는 작용입니다. 위기 돌파·권력 감각에 힘이 실리지만, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "삼형": "갈등과 압박이 반복되어 주된 반응이 강한 승부욕·압박 속 각성 쪽으로 모이는 작용입니다. 위기 돌파·권력 감각에 힘이 실리지만, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "丑戌刑축술형": "갈등과 압박이 반복되어 주된 반응이 묵은 불만·보수성 쪽으로 모이는 작용입니다. 자산 관리·장기 버팀에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "축술형(丑戌刑)": "갈등과 압박이 반복되어 주된 반응이 묵은 불만·보수성 쪽으로 모이는 작용입니다. 자산 관리·장기 버팀에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "丑戌刑": "갈등과 압박이 반복되어 주된 반응이 묵은 불만·보수성 쪽으로 모이는 작용입니다. 자산 관리·장기 버팀에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "축술형丑戌刑": "갈등과 압박이 반복되어 주된 반응이 묵은 불만·보수성 쪽으로 모이는 작용입니다. 자산 관리·장기 버팀에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "축술형": "갈등과 압박이 반복되어 주된 반응이 묵은 불만·보수성 쪽으로 모이는 작용입니다. 자산 관리·장기 버팀에 힘이 실리지만, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "戌未刑": "갈등과 압박이 반복되어 주된 반응이 책임 강박·가족 고집 쪽으로 모이는 작용입니다. 조직 유지·생활 관리에 힘이 실리지만, 생활과 책임의 차이를 오래 끌면 가족 안의 감정과 돈 문제가 함께 커질 수 있습니다.",
  "술미형戌未刑": "갈등과 압박이 반복되어 주된 반응이 책임 강박·가족 고집 쪽으로 모이는 작용입니다. 조직 유지·생활 관리에 힘이 실리지만, 생활과 책임의 차이를 오래 끌면 가족 안의 감정과 돈 문제가 함께 커질 수 있습니다.",
  "술미형": "갈등과 압박이 반복되어 주된 반응이 책임 강박·가족 고집 쪽으로 모이는 작용입니다. 조직 유지·생활 관리에 힘이 실리지만, 생활과 책임의 차이를 오래 끌면 가족 안의 감정과 돈 문제가 함께 커질 수 있습니다.",
  "戌未刑술미형": "갈등과 압박이 반복되어 주된 반응이 책임 강박·가족 고집 쪽으로 모이는 작용입니다. 조직 유지·생활 관리에 힘이 실리지만, 생활과 책임의 차이를 오래 끌면 가족 안의 감정과 돈 문제가 함께 커질 수 있습니다.",
  "술미형(戌未刑)": "갈등과 압박이 반복되어 주된 반응이 책임 강박·가족 고집 쪽으로 모이는 작용입니다. 조직 유지·생활 관리에 힘이 실리지만, 생활과 책임의 차이를 오래 끌면 가족 안의 감정과 돈 문제가 함께 커질 수 있습니다.",
  "축미형": "갈등과 압박이 반복되어 주된 반응이 생활 긴장·현실 불안 쪽으로 모이는 작용입니다. 저축·축적·살림 능력에 힘이 실리지만, 생활 문제를 참아 넘기다 돈과 감정의 갈등이 함께 커질 수 있습니다.",
  "丑未刑축미형": "갈등과 압박이 반복되어 주된 반응이 생활 긴장·현실 불안 쪽으로 모이는 작용입니다. 저축·축적·살림 능력에 힘이 실리지만, 생활 문제를 참아 넘기다 돈과 감정의 갈등이 함께 커질 수 있습니다.",
  "축미형丑未刑": "갈등과 압박이 반복되어 주된 반응이 생활 긴장·현실 불안 쪽으로 모이는 작용입니다. 저축·축적·살림 능력에 힘이 실리지만, 생활 문제를 참아 넘기다 돈과 감정의 갈등이 함께 커질 수 있습니다.",
  "축미형(丑未刑)": "갈등과 압박이 반복되어 주된 반응이 생활 긴장·현실 불안 쪽으로 모이는 작용입니다. 저축·축적·살림 능력에 힘이 실리지만, 생활 문제를 참아 넘기다 돈과 감정의 갈등이 함께 커질 수 있습니다.",
  "丑未刑": "갈등과 압박이 반복되어 주된 반응이 생활 긴장·현실 불안 쪽으로 모이는 작용입니다. 저축·축적·살림 능력에 힘이 실리지만, 생활 문제를 참아 넘기다 돈과 감정의 갈등이 함께 커질 수 있습니다.",
  "삼형丑戌未三刑": "갈등과 압박이 반복되어 주된 반응이 무거운 책임감·묵은 분노 쪽으로 모이는 작용입니다. 대형 관리·위기 버팀에 힘이 실리지만, 책임과 자산 문제가 얽히면 가족 갈등이 법적 분쟁으로 커질 수 있습니다.",
  "丑戌未三刑": "갈등과 압박이 반복되어 주된 반응이 무거운 책임감·묵은 분노 쪽으로 모이는 작용입니다. 대형 관리·위기 버팀에 힘이 실리지만, 책임과 자산 문제가 얽히면 가족 갈등이 법적 분쟁으로 커질 수 있습니다.",
  "축술미삼형(丑戌未三刑)": "갈등과 압박이 반복되어 주된 반응이 무거운 책임감·묵은 분노 쪽으로 모이는 작용입니다. 대형 관리·위기 버팀에 힘이 실리지만, 책임과 자산 문제가 얽히면 가족 갈등이 법적 분쟁으로 커질 수 있습니다.",
  "축술미": "갈등과 압박이 반복되어 주된 반응이 무거운 책임감·묵은 분노 쪽으로 모이는 작용입니다. 대형 관리·위기 버팀에 힘이 실리지만, 책임과 자산 문제가 얽히면 가족 갈등이 법적 분쟁으로 커질 수 있습니다.",
  "丑戌未三刑삼형": "갈등과 압박이 반복되어 주된 반응이 무거운 책임감·묵은 분노 쪽으로 모이는 작용입니다. 대형 관리·위기 버팀에 힘이 실리지만, 책임과 자산 문제가 얽히면 가족 갈등이 법적 분쟁으로 커질 수 있습니다.",
  "축술미삼형": "갈등과 압박이 반복되어 주된 반응이 무거운 책임감·묵은 분노 쪽으로 모이는 작용입니다. 대형 관리·위기 버팀에 힘이 실리지만, 책임과 자산 문제가 얽히면 가족 갈등이 법적 분쟁으로 커질 수 있습니다.",
  "자묘형(子卯刑)": "갈등과 압박이 반복되어 주된 반응이 예의 민감·감정 예민 쪽으로 모이는 작용입니다. 관계 감지·상담 감각에 힘이 실리지만, 감정과 원망을 오래 품으면 관계와 회복에 필요한 에너지가 크게 줄어들 수 있습니다.",
  "자묘형子卯刑": "갈등과 압박이 반복되어 주된 반응이 예의 민감·감정 예민 쪽으로 모이는 작용입니다. 관계 감지·상담 감각에 힘이 실리지만, 감정과 원망을 오래 품으면 관계와 회복에 필요한 에너지가 크게 줄어들 수 있습니다.",
  "子卯刑자묘형": "갈등과 압박이 반복되어 주된 반응이 예의 민감·감정 예민 쪽으로 모이는 작용입니다. 관계 감지·상담 감각에 힘이 실리지만, 감정과 원망을 오래 품으면 관계와 회복에 필요한 에너지가 크게 줄어들 수 있습니다.",
  "자묘형": "갈등과 압박이 반복되어 주된 반응이 예의 민감·감정 예민 쪽으로 모이는 작용입니다. 관계 감지·상담 감각에 힘이 실리지만, 감정과 원망을 오래 품으면 관계와 회복에 필요한 에너지가 크게 줄어들 수 있습니다.",
  "子卯刑": "갈등과 압박이 반복되어 주된 반응이 예의 민감·감정 예민 쪽으로 모이는 작용입니다. 관계 감지·상담 감각에 힘이 실리지만, 감정과 원망을 오래 품으면 관계와 회복에 필요한 에너지가 크게 줄어들 수 있습니다.",
  "辰辰自刑": "갈등과 압박이 반복되어 주된 반응이 자기 압박·내부 고집 쪽으로 모이는 작용입니다. 깊은 저장·장기 기획에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "진진자형": "갈등과 압박이 반복되어 주된 반응이 자기 압박·내부 고집 쪽으로 모이는 작용입니다. 깊은 저장·장기 기획에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "진진자형(辰辰自刑)": "갈등과 압박이 반복되어 주된 반응이 자기 압박·내부 고집 쪽으로 모이는 작용입니다. 깊은 저장·장기 기획에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "辰辰自刑진진자형": "갈등과 압박이 반복되어 주된 반응이 자기 압박·내부 고집 쪽으로 모이는 작용입니다. 깊은 저장·장기 기획에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "진진자형辰辰自刑": "갈등과 압박이 반복되어 주된 반응이 자기 압박·내부 고집 쪽으로 모이는 작용입니다. 깊은 저장·장기 기획에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "오오자형午午自刑": "갈등과 압박이 반복되어 주된 반응이 자존심 과열·감정 폭주 쪽으로 모이는 작용입니다. 대외 존재감·표현력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "오오자형": "갈등과 압박이 반복되어 주된 반응이 자존심 과열·감정 폭주 쪽으로 모이는 작용입니다. 대외 존재감·표현력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "午午自刑": "갈등과 압박이 반복되어 주된 반응이 자존심 과열·감정 폭주 쪽으로 모이는 작용입니다. 대외 존재감·표현력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "오오자형(午午自刑)": "갈등과 압박이 반복되어 주된 반응이 자존심 과열·감정 폭주 쪽으로 모이는 작용입니다. 대외 존재감·표현력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "午午自刑오오자형": "갈등과 압박이 반복되어 주된 반응이 자존심 과열·감정 폭주 쪽으로 모이는 작용입니다. 대외 존재감·표현력에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "酉酉自刑유유자형": "갈등과 압박이 반복되어 주된 반응이 완성도 강박·자기 비판 쪽으로 모이는 작용입니다. 미감 정밀도·품질 검수에 힘이 실리지만, 감정과 원망을 오래 품으면 관계와 회복에 필요한 에너지가 크게 줄어들 수 있습니다.",
  "유유자형(酉酉自刑)": "갈등과 압박이 반복되어 주된 반응이 완성도 강박·자기 비판 쪽으로 모이는 작용입니다. 미감 정밀도·품질 검수에 힘이 실리지만, 감정과 원망을 오래 품으면 관계와 회복에 필요한 에너지가 크게 줄어들 수 있습니다.",
  "酉酉自刑": "갈등과 압박이 반복되어 주된 반응이 완성도 강박·자기 비판 쪽으로 모이는 작용입니다. 미감 정밀도·품질 검수에 힘이 실리지만, 감정과 원망을 오래 품으면 관계와 회복에 필요한 에너지가 크게 줄어들 수 있습니다.",
  "유유자형酉酉自刑": "갈등과 압박이 반복되어 주된 반응이 완성도 강박·자기 비판 쪽으로 모이는 작용입니다. 미감 정밀도·품질 검수에 힘이 실리지만, 감정과 원망을 오래 품으면 관계와 회복에 필요한 에너지가 크게 줄어들 수 있습니다.",
  "유유자형": "갈등과 압박이 반복되어 주된 반응이 완성도 강박·자기 비판 쪽으로 모이는 작용입니다. 미감 정밀도·품질 검수에 힘이 실리지만, 감정과 원망을 오래 품으면 관계와 회복에 필요한 에너지가 크게 줄어들 수 있습니다.",
  "해해자형亥亥自刑": "갈등과 압박이 반복되어 주된 반응이 내면 과다·불안 상상 쪽으로 모이는 작용입니다. 직관·상징 해석에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "해해자형": "갈등과 압박이 반복되어 주된 반응이 내면 과다·불안 상상 쪽으로 모이는 작용입니다. 직관·상징 해석에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "亥亥自刑": "갈등과 압박이 반복되어 주된 반응이 내면 과다·불안 상상 쪽으로 모이는 작용입니다. 직관·상징 해석에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "해해자형(亥亥自刑)": "갈등과 압박이 반복되어 주된 반응이 내면 과다·불안 상상 쪽으로 모이는 작용입니다. 직관·상징 해석에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "亥亥自刑해해자형": "갈등과 압박이 반복되어 주된 반응이 내면 과다·불안 상상 쪽으로 모이는 작용입니다. 직관·상징 해석에 힘이 실리지만, 생각과 감정이 안으로 깊어져 행동과 소통이 줄어들 수 있습니다.",
  "子未害자미해": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 정서 부담·미안함 쪽으로 모이는 작용입니다. 돌봄 감각·세심한 관리에 힘이 실리지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "자미해子未害": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 정서 부담·미안함 쪽으로 모이는 작용입니다. 돌봄 감각·세심한 관리에 힘이 실리지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "자미해(子未害)": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 정서 부담·미안함 쪽으로 모이는 작용입니다. 돌봄 감각·세심한 관리에 힘이 실리지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "자미해": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 정서 부담·미안함 쪽으로 모이는 작용입니다. 돌봄 감각·세심한 관리에 힘이 실리지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "子未害": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 정서 부담·미안함 쪽으로 모이는 작용입니다. 돌봄 감각·세심한 관리에 힘이 실리지만, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "축오해(丑午害)": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 체면과 불안·속열 쪽으로 모이는 작용입니다. 실무 버팀·위기 관리에 힘이 실리지만, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "丑午害": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 체면과 불안·속열 쪽으로 모이는 작용입니다. 실무 버팀·위기 관리에 힘이 실리지만, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "축오해丑午害": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 체면과 불안·속열 쪽으로 모이는 작용입니다. 실무 버팀·위기 관리에 힘이 실리지만, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "丑午害축오해": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 체면과 불안·속열 쪽으로 모이는 작용입니다. 실무 버팀·위기 관리에 힘이 실리지만, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "축오해": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 체면과 불안·속열 쪽으로 모이는 작용입니다. 실무 버팀·위기 관리에 힘이 실리지만, 보여지는 모습에 힘을 쓰다 실속과 회복을 놓치지 않도록 주의해야 합니다.",
  "인사해(寅巳害)": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 성급한 욕심·자기 압박 쪽으로 모이는 작용입니다. 추진력·영업 감각에 힘이 실리지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "寅巳害": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 성급한 욕심·자기 압박 쪽으로 모이는 작용입니다. 추진력·영업 감각에 힘이 실리지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "인사해": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 성급한 욕심·자기 압박 쪽으로 모이는 작용입니다. 추진력·영업 감각에 힘이 실리지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "인사해寅巳害": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 성급한 욕심·자기 압박 쪽으로 모이는 작용입니다. 추진력·영업 감각에 힘이 실리지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "寅巳害인사해": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 성급한 욕심·자기 압박 쪽으로 모이는 작용입니다. 추진력·영업 감각에 힘이 실리지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "卯辰害": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 관계 불편감·예민한 체면 쪽으로 모이는 작용입니다. 관계 조율·기획 수정에 힘이 실리지만, 불만을 말하지 않으면 작은 어긋남이 관계의 신뢰를 약하게 만들 수 있습니다.",
  "卯辰害묘진해": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 관계 불편감·예민한 체면 쪽으로 모이는 작용입니다. 관계 조율·기획 수정에 힘이 실리지만, 불만을 말하지 않으면 작은 어긋남이 관계의 신뢰를 약하게 만들 수 있습니다.",
  "묘진해": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 관계 불편감·예민한 체면 쪽으로 모이는 작용입니다. 관계 조율·기획 수정에 힘이 실리지만, 불만을 말하지 않으면 작은 어긋남이 관계의 신뢰를 약하게 만들 수 있습니다.",
  "묘진해(卯辰害)": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 관계 불편감·예민한 체면 쪽으로 모이는 작용입니다. 관계 조율·기획 수정에 힘이 실리지만, 불만을 말하지 않으면 작은 어긋남이 관계의 신뢰를 약하게 만들 수 있습니다.",
  "묘진해卯辰害": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 관계 불편감·예민한 체면 쪽으로 모이는 작용입니다. 관계 조율·기획 수정에 힘이 실리지만, 불만을 말하지 않으면 작은 어긋남이 관계의 신뢰를 약하게 만들 수 있습니다.",
  "신해해": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 이동 불안·의심 쪽으로 모이는 작용입니다. 정보 감지·전략적 판단에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "신해해申亥害": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 이동 불안·의심 쪽으로 모이는 작용입니다. 정보 감지·전략적 판단에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "신해해(申亥害)": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 이동 불안·의심 쪽으로 모이는 작용입니다. 정보 감지·전략적 판단에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "申亥害신해해": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 이동 불안·의심 쪽으로 모이는 작용입니다. 정보 감지·전략적 판단에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "申亥害": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 이동 불안·의심 쪽으로 모이는 작용입니다. 정보 감지·전략적 판단에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "유술해": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 차가운 서운함·평가 의식 쪽으로 모이는 작용입니다. 품질 감각·관계 정리에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "酉戌害": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 차가운 서운함·평가 의식 쪽으로 모이는 작용입니다. 품질 감각·관계 정리에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "酉戌害유술해": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 차가운 서운함·평가 의식 쪽으로 모이는 작용입니다. 품질 감각·관계 정리에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "유술해酉戌害": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 차가운 서운함·평가 의식 쪽으로 모이는 작용입니다. 품질 감각·관계 정리에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "유술해(酉戌害)": "겉으로 큰 충돌 없이 작은 불편이 스며들어 주된 반응이 차가운 서운함·평가 의식 쪽으로 모이는 작용입니다. 품질 감각·관계 정리에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해를 만들 수 있습니다.",
  "자유파子酉破": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 차가운 감지·말투 민감 쪽으로 모이는 작용입니다. 분석 감각·미감 판단에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "자유파": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 차가운 감지·말투 민감 쪽으로 모이는 작용입니다. 분석 감각·미감 판단에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "子酉破": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 차가운 감지·말투 민감 쪽으로 모이는 작용입니다. 분석 감각·미감 판단에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "子酉破자유파": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 차가운 감지·말투 민감 쪽으로 모이는 작용입니다. 분석 감각·미감 판단에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "자유파(子酉破)": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 차가운 감지·말투 민감 쪽으로 모이는 작용입니다. 분석 감각·미감 판단에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "축진파": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 묵은 계산·생활 불안 쪽으로 모이는 작용입니다. 자산 정리·장부 감각에 힘이 실리지만, 오래된 돈 문제를 방치하면 작은 균열이 실제 손실로 이어질 수 있습니다.",
  "丑辰破축진파": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 묵은 계산·생활 불안 쪽으로 모이는 작용입니다. 자산 정리·장부 감각에 힘이 실리지만, 오래된 돈 문제를 방치하면 작은 균열이 실제 손실로 이어질 수 있습니다.",
  "축진파丑辰破": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 묵은 계산·생활 불안 쪽으로 모이는 작용입니다. 자산 정리·장부 감각에 힘이 실리지만, 오래된 돈 문제를 방치하면 작은 균열이 실제 손실로 이어질 수 있습니다.",
  "축진파(丑辰破)": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 묵은 계산·생활 불안 쪽으로 모이는 작용입니다. 자산 정리·장부 감각에 힘이 실리지만, 오래된 돈 문제를 방치하면 작은 균열이 실제 손실로 이어질 수 있습니다.",
  "丑辰破": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 묵은 계산·생활 불안 쪽으로 모이는 작용입니다. 자산 정리·장부 감각에 힘이 실리지만, 오래된 돈 문제를 방치하면 작은 균열이 실제 손실로 이어질 수 있습니다.",
  "인해파": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 이상과 이동·정서 방황 쪽으로 모이는 작용입니다. 확장 감각·학습력에 힘이 실리지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "인해파(寅亥破)": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 이상과 이동·정서 방황 쪽으로 모이는 작용입니다. 확장 감각·학습력에 힘이 실리지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "寅亥破인해파": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 이상과 이동·정서 방황 쪽으로 모이는 작용입니다. 확장 감각·학습력에 힘이 실리지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "寅亥破": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 이상과 이동·정서 방황 쪽으로 모이는 작용입니다. 확장 감각·학습력에 힘이 실리지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "인해파寅亥破": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 이상과 이동·정서 방황 쪽으로 모이는 작용입니다. 확장 감각·학습력에 힘이 실리지만, 불안이 커지면 속마음을 숨기고 혼자 판단하려는 경향이 강해질 수 있습니다.",
  "묘오파(卯午破)": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 감정 과열·싫증 쪽으로 모이는 작용입니다. 표현력·감각적 연출에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "묘오파卯午破": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 감정 과열·싫증 쪽으로 모이는 작용입니다. 표현력·감각적 연출에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "묘오파": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 감정 과열·싫증 쪽으로 모이는 작용입니다. 표현력·감각적 연출에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "卯午破": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 감정 과열·싫증 쪽으로 모이는 작용입니다. 표현력·감각적 연출에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "卯午破묘오파": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 감정 과열·싫증 쪽으로 모이는 작용입니다. 표현력·감각적 연출에 힘이 실리지만, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "巳申破": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 전략 변화·속도 불안 쪽으로 모이는 작용입니다. 기술 전환·거래 감각에 힘이 실리지만, 작은 말과 약속의 어긋남이 누적되면 신뢰가 빠르게 약해질 수 있습니다.",
  "사신파": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 전략 변화·속도 불안 쪽으로 모이는 작용입니다. 기술 전환·거래 감각에 힘이 실리지만, 작은 말과 약속의 어긋남이 누적되면 신뢰가 빠르게 약해질 수 있습니다.",
  "사신파(巳申破)": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 전략 변화·속도 불안 쪽으로 모이는 작용입니다. 기술 전환·거래 감각에 힘이 실리지만, 작은 말과 약속의 어긋남이 누적되면 신뢰가 빠르게 약해질 수 있습니다.",
  "巳申破사신파": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 전략 변화·속도 불안 쪽으로 모이는 작용입니다. 기술 전환·거래 감각에 힘이 실리지만, 작은 말과 약속의 어긋남이 누적되면 신뢰가 빠르게 약해질 수 있습니다.",
  "사신파巳申破": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 전략 변화·속도 불안 쪽으로 모이는 작용입니다. 기술 전환·거래 감각에 힘이 실리지만, 작은 말과 약속의 어긋남이 누적되면 신뢰가 빠르게 약해질 수 있습니다.",
  "未戌破": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 가족 책임·묵은 서운함 쪽으로 모이는 작용입니다. 돌봄 운영·자산 유지에 힘이 실리지만, 가족과 자산 문제를 방치하면 장기적인 손실과 피로가 함께 커질 수 있습니다.",
  "未戌破미술파": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 가족 책임·묵은 서운함 쪽으로 모이는 작용입니다. 돌봄 운영·자산 유지에 힘이 실리지만, 가족과 자산 문제를 방치하면 장기적인 손실과 피로가 함께 커질 수 있습니다.",
  "미술파(未戌破)": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 가족 책임·묵은 서운함 쪽으로 모이는 작용입니다. 돌봄 운영·자산 유지에 힘이 실리지만, 가족과 자산 문제를 방치하면 장기적인 손실과 피로가 함께 커질 수 있습니다.",
  "미술파未戌破": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 가족 책임·묵은 서운함 쪽으로 모이는 작용입니다. 돌봄 운영·자산 유지에 힘이 실리지만, 가족과 자산 문제를 방치하면 장기적인 손실과 피로가 함께 커질 수 있습니다.",
  "미술파": "작은 어긋남이 연결과 신뢰를 흔들어 주된 반응이 가족 책임·묵은 서운함 쪽으로 모이는 작용입니다. 돌봄 운영·자산 유지에 힘이 실리지만, 가족과 자산 문제를 방치하면 장기적인 손실과 피로가 함께 커질 수 있습니다.",
  "劫煞겁살": "강제로 빼앗기거나 급하게 판이 흔들리는 보조 신호입니다. 위기 돌파·실전 대응 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "劫煞": "강제로 빼앗기거나 급하게 판이 흔들리는 보조 신호입니다. 위기 돌파·실전 대응 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "겁살": "강제로 빼앗기거나 급하게 판이 흔들리는 보조 신호입니다. 위기 돌파·실전 대응 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "겁살(劫煞)": "강제로 빼앗기거나 급하게 판이 흔들리는 보조 신호입니다. 위기 돌파·실전 대응 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "겁살劫煞": "강제로 빼앗기거나 급하게 판이 흔들리는 보조 신호입니다. 위기 돌파·실전 대응 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "재살(災煞)": "위험을 먼저 맞닥뜨리고 방어와 통제가 강해지는 보조 신호입니다. 특히 보안 감각·리스크 관리 측면에 힘이 실리며, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "災煞재살": "위험을 먼저 맞닥뜨리고 방어와 통제가 강해지는 보조 신호입니다. 특히 보안 감각·리스크 관리 측면에 힘이 실리며, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "재살": "위험을 먼저 맞닥뜨리고 방어와 통제가 강해지는 보조 신호입니다. 특히 보안 감각·리스크 관리 측면에 힘이 실리며, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "災煞": "위험을 먼저 맞닥뜨리고 방어와 통제가 강해지는 보조 신호입니다. 특히 보안 감각·리스크 관리 측면에 힘이 실리며, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "재살災煞": "위험을 먼저 맞닥뜨리고 방어와 통제가 강해지는 보조 신호입니다. 특히 보안 감각·리스크 관리 측면에 힘이 실리며, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "천살天煞": "사람 힘으로 밀어붙이기 어려운 큰 환경의 보조 신호입니다. 특히 큰 흐름 감지·장기 인내 측면에 힘이 실리며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "천살": "사람 힘으로 밀어붙이기 어려운 큰 환경의 보조 신호입니다. 특히 큰 흐름 감지·장기 인내 측면에 힘이 실리며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "天煞": "사람 힘으로 밀어붙이기 어려운 큰 환경의 보조 신호입니다. 특히 큰 흐름 감지·장기 인내 측면에 힘이 실리며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "天煞천살": "사람 힘으로 밀어붙이기 어려운 큰 환경의 보조 신호입니다. 특히 큰 흐름 감지·장기 인내 측면에 힘이 실리며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "천살(天煞)": "사람 힘으로 밀어붙이기 어려운 큰 환경의 보조 신호입니다. 특히 큰 흐름 감지·장기 인내 측면에 힘이 실리며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "地煞": "몸이 움직이고 현장에서 길을 찾는 보조 신호입니다. 현장 감각·지역 네트워크 분야에서 강점이 살아나며, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "지살(地煞)": "몸이 움직이고 현장에서 길을 찾는 보조 신호입니다. 현장 감각·지역 네트워크 분야에서 강점이 살아나며, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "지살地煞": "몸이 움직이고 현장에서 길을 찾는 보조 신호입니다. 현장 감각·지역 네트워크 분야에서 강점이 살아나며, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "地煞지살": "몸이 움직이고 현장에서 길을 찾는 보조 신호입니다. 현장 감각·지역 네트워크 분야에서 강점이 살아나며, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "지살": "몸이 움직이고 현장에서 길을 찾는 보조 신호입니다. 현장 감각·지역 네트워크 분야에서 강점이 살아나며, 새로운 가능성을 좇다가 집중과 지속성이 분산될 수 있습니다.",
  "연살年煞": "시선과 호감을 끌어오고 관계 노출을 만드는 보조 신호입니다. 이미지 연출·분위기 장악 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "年煞연살": "시선과 호감을 끌어오고 관계 노출을 만드는 보조 신호입니다. 이미지 연출·분위기 장악 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "연살(年煞)": "시선과 호감을 끌어오고 관계 노출을 만드는 보조 신호입니다. 이미지 연출·분위기 장악 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "연살": "시선과 호감을 끌어오고 관계 노출을 만드는 보조 신호입니다. 이미지 연출·분위기 장악 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "年煞": "시선과 호감을 끌어오고 관계 노출을 만드는 보조 신호입니다. 이미지 연출·분위기 장악 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "月煞월살": "바로 드러나지 않고 뒤에서 지연과 그늘을 만드는 보조 신호입니다. 후방 기획·숨은 정리 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "월살月煞": "바로 드러나지 않고 뒤에서 지연과 그늘을 만드는 보조 신호입니다. 후방 기획·숨은 정리 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "월살(月煞)": "바로 드러나지 않고 뒤에서 지연과 그늘을 만드는 보조 신호입니다. 후방 기획·숨은 정리 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "月煞": "바로 드러나지 않고 뒤에서 지연과 그늘을 만드는 보조 신호입니다. 후방 기획·숨은 정리 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "월살": "바로 드러나지 않고 뒤에서 지연과 그늘을 만드는 보조 신호입니다. 후방 기획·숨은 정리 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "亡身煞망신살": "감추려던 것이 드러나고 체면과 평판이 흔들리는 보조 신호입니다. 특히 노출 감각·대외 표현 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "망신살": "감추려던 것이 드러나고 체면과 평판이 흔들리는 보조 신호입니다. 특히 노출 감각·대외 표현 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "亡身煞": "감추려던 것이 드러나고 체면과 평판이 흔들리는 보조 신호입니다. 특히 노출 감각·대외 표현 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "망신살(亡身煞)": "감추려던 것이 드러나고 체면과 평판이 흔들리는 보조 신호입니다. 특히 노출 감각·대외 표현 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "망신살亡身煞": "감추려던 것이 드러나고 체면과 평판이 흔들리는 보조 신호입니다. 특히 노출 감각·대외 표현 측면에 힘이 실리며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "將星煞": "주도권과 승부욕이 강해지는 보조 신호입니다. 결단력·통솔력 분야에서 강점이 살아나며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "將星煞장성살": "주도권과 승부욕이 강해지는 보조 신호입니다. 결단력·통솔력 분야에서 강점이 살아나며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "장성살將星煞": "주도권과 승부욕이 강해지는 보조 신호입니다. 결단력·통솔력 분야에서 강점이 살아나며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "장성살(將星煞)": "주도권과 승부욕이 강해지는 보조 신호입니다. 결단력·통솔력 분야에서 강점이 살아나며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "장성살": "주도권과 승부욕이 강해지는 보조 신호입니다. 결단력·통솔력 분야에서 강점이 살아나며, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "반안살攀鞍煞": "좋은 자리와 안정된 기반, 품격 있는 사회적 역할을 중시하는 보조 신호입니다. 의전과 정리에는 강하지만, 익숙한 대우와 후원에 기대어 변화를 미루지 않도록 주의해야 합니다.",
  "반안살": "좋은 자리와 안정된 기반, 품격 있는 사회적 역할을 중시하는 보조 신호입니다. 의전과 정리에는 강하지만, 익숙한 대우와 후원에 기대어 변화를 미루지 않도록 주의해야 합니다.",
  "반안살(攀鞍煞)": "좋은 자리와 안정된 기반, 품격 있는 사회적 역할을 중시하는 보조 신호입니다. 의전과 정리에는 강하지만, 익숙한 대우와 후원에 기대어 변화를 미루지 않도록 주의해야 합니다.",
  "攀鞍煞": "좋은 자리와 안정된 기반, 품격 있는 사회적 역할을 중시하는 보조 신호입니다. 의전과 정리에는 강하지만, 익숙한 대우와 후원에 기대어 변화를 미루지 않도록 주의해야 합니다.",
  "攀鞍煞반안살": "좋은 자리와 안정된 기반, 품격 있는 사회적 역할을 중시하는 보조 신호입니다. 의전과 정리에는 강하지만, 익숙한 대우와 후원에 기대어 변화를 미루지 않도록 주의해야 합니다.",
  "驛馬煞역마살": "움직여야 길이 열리고 한곳에 묶이기 어려운 보조 신호입니다. 현장력·정보 수집 분야에서 강점이 살아나며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "역마살(驛馬煞)": "움직여야 길이 열리고 한곳에 묶이기 어려운 보조 신호입니다. 현장력·정보 수집 분야에서 강점이 살아나며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "역마살": "움직여야 길이 열리고 한곳에 묶이기 어려운 보조 신호입니다. 현장력·정보 수집 분야에서 강점이 살아나며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "역마살驛馬煞": "움직여야 길이 열리고 한곳에 묶이기 어려운 보조 신호입니다. 현장력·정보 수집 분야에서 강점이 살아나며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "驛馬煞": "움직여야 길이 열리고 한곳에 묶이기 어려운 보조 신호입니다. 현장력·정보 수집 분야에서 강점이 살아나며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "육해살(六害煞)": "큰 사건보다 자잘한 손상과 누적 부담을 만드는 보조 신호입니다. 특히 수리·보완·뒤처리 측면에 힘이 실리며, 작은 불편을 계속 넘기면 생활의 피로와 관계의 마찰이 서서히 커질 수 있습니다.",
  "六害煞": "큰 사건보다 자잘한 손상과 누적 부담을 만드는 보조 신호입니다. 특히 수리·보완·뒤처리 측면에 힘이 실리며, 작은 불편을 계속 넘기면 생활의 피로와 관계의 마찰이 서서히 커질 수 있습니다.",
  "六害煞육해살": "큰 사건보다 자잘한 손상과 누적 부담을 만드는 보조 신호입니다. 특히 수리·보완·뒤처리 측면에 힘이 실리며, 작은 불편을 계속 넘기면 생활의 피로와 관계의 마찰이 서서히 커질 수 있습니다.",
  "육해살": "큰 사건보다 자잘한 손상과 누적 부담을 만드는 보조 신호입니다. 특히 수리·보완·뒤처리 측면에 힘이 실리며, 작은 불편을 계속 넘기면 생활의 피로와 관계의 마찰이 서서히 커질 수 있습니다.",
  "육해살六害煞": "큰 사건보다 자잘한 손상과 누적 부담을 만드는 보조 신호입니다. 특히 수리·보완·뒤처리 측면에 힘이 실리며, 작은 불편을 계속 넘기면 생활의 피로와 관계의 마찰이 서서히 커질 수 있습니다.",
  "華蓋煞": "혼자 깊이 몰입하며 예술, 종교, 철학적 의미를 탐색하는 성향을 상징하는 보조 신호입니다. 창작과 사색에는 강하지만, 현실과 관계에서 지나치게 멀어지지 않도록 균형이 필요합니다.",
  "화개살華蓋煞": "혼자 깊이 몰입하며 예술, 종교, 철학적 의미를 탐색하는 성향을 상징하는 보조 신호입니다. 창작과 사색에는 강하지만, 현실과 관계에서 지나치게 멀어지지 않도록 균형이 필요합니다.",
  "華蓋煞화개살": "혼자 깊이 몰입하며 예술, 종교, 철학적 의미를 탐색하는 성향을 상징하는 보조 신호입니다. 창작과 사색에는 강하지만, 현실과 관계에서 지나치게 멀어지지 않도록 균형이 필요합니다.",
  "화개살(華蓋煞)": "혼자 깊이 몰입하며 예술, 종교, 철학적 의미를 탐색하는 성향을 상징하는 보조 신호입니다. 창작과 사색에는 강하지만, 현실과 관계에서 지나치게 멀어지지 않도록 균형이 필요합니다.",
  "화개살": "혼자 깊이 몰입하며 예술, 종교, 철학적 의미를 탐색하는 성향을 상징하는 보조 신호입니다. 창작과 사색에는 강하지만, 현실과 관계에서 지나치게 멀어지지 않도록 균형이 필요합니다.",
  "天乙貴人천을귀인": "막힌 상황에서 도움을 받을 통로와 관계의 완충력이 살아나는 대표적인 길한 보조 신호입니다. 중재와 위기 안정에 강하지만, 귀인만 기다리기보다 스스로 결정하고 움직이는 힘도 필요합니다.",
  "천을귀인": "막힌 상황에서 도움을 받을 통로와 관계의 완충력이 살아나는 대표적인 길한 보조 신호입니다. 중재와 위기 안정에 강하지만, 귀인만 기다리기보다 스스로 결정하고 움직이는 힘도 필요합니다.",
  "천을귀인(天乙貴人)": "막힌 상황에서 도움을 받을 통로와 관계의 완충력이 살아나는 대표적인 길한 보조 신호입니다. 중재와 위기 안정에 강하지만, 귀인만 기다리기보다 스스로 결정하고 움직이는 힘도 필요합니다.",
  "天乙貴人": "막힌 상황에서 도움을 받을 통로와 관계의 완충력이 살아나는 대표적인 길한 보조 신호입니다. 중재와 위기 안정에 강하지만, 귀인만 기다리기보다 스스로 결정하고 움직이는 힘도 필요합니다.",
  "천을귀인天乙貴人": "막힌 상황에서 도움을 받을 통로와 관계의 완충력이 살아나는 대표적인 길한 보조 신호입니다. 중재와 위기 안정에 강하지만, 귀인만 기다리기보다 스스로 결정하고 움직이는 힘도 필요합니다.",
  "천덕귀인": "불리한 일을 크게 상하지 않게 누그러뜨리는 길한 보조 신호입니다. 특히 갈등 완화·사람 살림 측면에 힘이 실리며, 도움을 기대하며 위험 신호를 가볍게 넘기지 않도록 주의해야 합니다.",
  "天德貴人천덕귀인": "불리한 일을 크게 상하지 않게 누그러뜨리는 길한 보조 신호입니다. 특히 갈등 완화·사람 살림 측면에 힘이 실리며, 도움을 기대하며 위험 신호를 가볍게 넘기지 않도록 주의해야 합니다.",
  "천덕귀인天德貴人": "불리한 일을 크게 상하지 않게 누그러뜨리는 길한 보조 신호입니다. 특히 갈등 완화·사람 살림 측면에 힘이 실리며, 도움을 기대하며 위험 신호를 가볍게 넘기지 않도록 주의해야 합니다.",
  "천덕귀인(天德貴人)": "불리한 일을 크게 상하지 않게 누그러뜨리는 길한 보조 신호입니다. 특히 갈등 완화·사람 살림 측면에 힘이 실리며, 도움을 기대하며 위험 신호를 가볍게 넘기지 않도록 주의해야 합니다.",
  "天德貴人": "불리한 일을 크게 상하지 않게 누그러뜨리는 길한 보조 신호입니다. 특히 갈등 완화·사람 살림 측면에 힘이 실리며, 도움을 기대하며 위험 신호를 가볍게 넘기지 않도록 주의해야 합니다.",
  "월덕귀인月德貴人": "사회적 관계와 시기 속에서 도움과 완충을 붙이는 길한 보조 신호입니다. 대인 완충·명분 만들기 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "월덕귀인(月德貴人)": "사회적 관계와 시기 속에서 도움과 완충을 붙이는 길한 보조 신호입니다. 대인 완충·명분 만들기 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "月德貴人월덕귀인": "사회적 관계와 시기 속에서 도움과 완충을 붙이는 길한 보조 신호입니다. 대인 완충·명분 만들기 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "월덕귀인": "사회적 관계와 시기 속에서 도움과 완충을 붙이는 길한 보조 신호입니다. 대인 완충·명분 만들기 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "月德貴人": "사회적 관계와 시기 속에서 도움과 완충을 붙이는 길한 보조 신호입니다. 대인 완충·명분 만들기 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "太極貴人태극귀인": "큰 의미와 원리를 찾고 학문·철학으로 들어가는 귀인 작용을 뜻하는 보조 신호입니다. 철학성·깊은 학습 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "태극귀인": "큰 의미와 원리를 찾고 학문·철학으로 들어가는 귀인 작용을 뜻하는 보조 신호입니다. 철학성·깊은 학습 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "太極貴人": "큰 의미와 원리를 찾고 학문·철학으로 들어가는 귀인 작용을 뜻하는 보조 신호입니다. 철학성·깊은 학습 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "태극귀인太極貴人": "큰 의미와 원리를 찾고 학문·철학으로 들어가는 귀인 작용을 뜻하는 보조 신호입니다. 철학성·깊은 학습 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "태극귀인(太極貴人)": "큰 의미와 원리를 찾고 학문·철학으로 들어가는 귀인 작용을 뜻하는 보조 신호입니다. 철학성·깊은 학습 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "문창귀인文昌貴人": "말과 글, 정리된 지식이 살아나는 길한 보조 신호입니다. 글쓰기·학습력 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "文昌貴人문창귀인": "말과 글, 정리된 지식이 살아나는 길한 보조 신호입니다. 글쓰기·학습력 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "文昌貴人": "말과 글, 정리된 지식이 살아나는 길한 보조 신호입니다. 글쓰기·학습력 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "문창귀인(文昌貴人)": "말과 글, 정리된 지식이 살아나는 길한 보조 신호입니다. 글쓰기·학습력 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "문창귀인": "말과 글, 정리된 지식이 살아나는 길한 보조 신호입니다. 글쓰기·학습력 분야에서 강점이 살아나며, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "학당귀인學堂貴人": "배우고 가르치는 자리에서 힘이 붙는 길한 보조 신호입니다. 교육 능력·자격 취득 분야에서 강점이 살아나며, 배움이 길어지면 실제 적용과 경험이 뒤로 밀릴 수 있습니다.",
  "학당귀인(學堂貴人)": "배우고 가르치는 자리에서 힘이 붙는 길한 보조 신호입니다. 교육 능력·자격 취득 분야에서 강점이 살아나며, 배움이 길어지면 실제 적용과 경험이 뒤로 밀릴 수 있습니다.",
  "學堂貴人학당귀인": "배우고 가르치는 자리에서 힘이 붙는 길한 보조 신호입니다. 교육 능력·자격 취득 분야에서 강점이 살아나며, 배움이 길어지면 실제 적용과 경험이 뒤로 밀릴 수 있습니다.",
  "학당귀인": "배우고 가르치는 자리에서 힘이 붙는 길한 보조 신호입니다. 교육 능력·자격 취득 분야에서 강점이 살아나며, 배움이 길어지면 실제 적용과 경험이 뒤로 밀릴 수 있습니다.",
  "學堂貴人": "배우고 가르치는 자리에서 힘이 붙는 길한 보조 신호입니다. 교육 능력·자격 취득 분야에서 강점이 살아나며, 배움이 길어지면 실제 적용과 경험이 뒤로 밀릴 수 있습니다.",
  "국인귀인(國印貴人)": "공적 문서와 직함, 도장과 책임이 붙는 귀인 작용을 뜻하는 보조 신호입니다. 문서 관리·권한 처리 분야에서 강점이 살아나며, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "국인귀인": "공적 문서와 직함, 도장과 책임이 붙는 귀인 작용을 뜻하는 보조 신호입니다. 문서 관리·권한 처리 분야에서 강점이 살아나며, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "국인귀인國印貴人": "공적 문서와 직함, 도장과 책임이 붙는 귀인 작용을 뜻하는 보조 신호입니다. 문서 관리·권한 처리 분야에서 강점이 살아나며, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "國印貴人": "공적 문서와 직함, 도장과 책임이 붙는 귀인 작용을 뜻하는 보조 신호입니다. 문서 관리·권한 처리 분야에서 강점이 살아나며, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "國印貴人국인귀인": "공적 문서와 직함, 도장과 책임이 붙는 귀인 작용을 뜻하는 보조 신호입니다. 문서 관리·권한 처리 분야에서 강점이 살아나며, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "금여": "품격, 좋은 대우, 안정된 생활과 배우자 인연을 상징하는 길한 보조 신호입니다. 이미지와 의전 감각은 좋지만, 체면 소비와 상대에 대한 기대가 지나치게 커질 수 있습니다.",
  "金輿금여": "품격, 좋은 대우, 안정된 생활과 배우자 인연을 상징하는 길한 보조 신호입니다. 이미지와 의전 감각은 좋지만, 체면 소비와 상대에 대한 기대가 지나치게 커질 수 있습니다.",
  "金輿": "품격, 좋은 대우, 안정된 생활과 배우자 인연을 상징하는 길한 보조 신호입니다. 이미지와 의전 감각은 좋지만, 체면 소비와 상대에 대한 기대가 지나치게 커질 수 있습니다.",
  "금여(金輿)": "품격, 좋은 대우, 안정된 생활과 배우자 인연을 상징하는 길한 보조 신호입니다. 이미지와 의전 감각은 좋지만, 체면 소비와 상대에 대한 기대가 지나치게 커질 수 있습니다.",
  "금여金輿": "품격, 좋은 대우, 안정된 생활과 배우자 인연을 상징하는 길한 보조 신호입니다. 이미지와 의전 감각은 좋지만, 체면 소비와 상대에 대한 기대가 지나치게 커질 수 있습니다.",
  "桃花煞도화살": "사람의 시선과 호감, 관계 노출을 끌어오는 보조 신호입니다. 이미지 연출·분위기 조성 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "도화살桃花煞": "사람의 시선과 호감, 관계 노출을 끌어오는 보조 신호입니다. 이미지 연출·분위기 조성 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "桃花煞": "사람의 시선과 호감, 관계 노출을 끌어오는 보조 신호입니다. 이미지 연출·분위기 조성 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "도화살(桃花煞)": "사람의 시선과 호감, 관계 노출을 끌어오는 보조 신호입니다. 이미지 연출·분위기 조성 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "도화살": "사람의 시선과 호감, 관계 노출을 끌어오는 보조 신호입니다. 이미지 연출·분위기 조성 분야에서 강점이 살아나며, 표현과 노출이 앞서면 말과 이미지가 불필요한 오해와 평판 부담을 만들 수 있습니다.",
  "紅艶煞": "감정과 이성적 끌림이 진하게 드러나며 매력과 감성 표현이 강해지는 보조 신호입니다. 관계가 과열되면 질투와 집착, 평판 부담이 함께 커질 수 있습니다.",
  "홍염살": "감정과 이성적 끌림이 진하게 드러나며 매력과 감성 표현이 강해지는 보조 신호입니다. 관계가 과열되면 질투와 집착, 평판 부담이 함께 커질 수 있습니다.",
  "홍염살(紅艶煞)": "감정과 이성적 끌림이 진하게 드러나며 매력과 감성 표현이 강해지는 보조 신호입니다. 관계가 과열되면 질투와 집착, 평판 부담이 함께 커질 수 있습니다.",
  "홍염살紅艶煞": "감정과 이성적 끌림이 진하게 드러나며 매력과 감성 표현이 강해지는 보조 신호입니다. 관계가 과열되면 질투와 집착, 평판 부담이 함께 커질 수 있습니다.",
  "紅艶煞홍염살": "감정과 이성적 끌림이 진하게 드러나며 매력과 감성 표현이 강해지는 보조 신호입니다. 관계가 과열되면 질투와 집착, 평판 부담이 함께 커질 수 있습니다.",
  "양인살(羊刃煞)": "자존심과 칼 같은 결단이 강해지는 보조 신호입니다. 삶에서는 돌파력·위기 대응 쪽으로 강점이 드러나지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "羊刃煞양인살": "자존심과 칼 같은 결단이 강해지는 보조 신호입니다. 삶에서는 돌파력·위기 대응 쪽으로 강점이 드러나지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "羊刃煞": "자존심과 칼 같은 결단이 강해지는 보조 신호입니다. 삶에서는 돌파력·위기 대응 쪽으로 강점이 드러나지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "양인살羊刃煞": "자존심과 칼 같은 결단이 강해지는 보조 신호입니다. 삶에서는 돌파력·위기 대응 쪽으로 강점이 드러나지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "양인살": "자존심과 칼 같은 결단이 강해지는 보조 신호입니다. 삶에서는 돌파력·위기 대응 쪽으로 강점이 드러나지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "魁罡煞": "강한 기상과 권위, 비범한 독주성이 붙는 보조 신호입니다. 장악력·극한 돌파 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "魁罡煞괴강살": "강한 기상과 권위, 비범한 독주성이 붙는 보조 신호입니다. 장악력·극한 돌파 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "괴강살": "강한 기상과 권위, 비범한 독주성이 붙는 보조 신호입니다. 장악력·극한 돌파 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "괴강살(魁罡煞)": "강한 기상과 권위, 비범한 독주성이 붙는 보조 신호입니다. 장악력·극한 돌파 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "괴강살魁罡煞": "강한 기상과 권위, 비범한 독주성이 붙는 보조 신호입니다. 장악력·극한 돌파 측면이 실제 장점으로 작동하는 한편, 자기 기준이 굳으면 타인의 방식과 타협하기 어려울 수 있습니다.",
  "백호대살(白虎大煞)": "강한 사건성, 상처, 수술성, 거친 결단을 품은 보조 신호입니다. 응급 대응·절단 결단 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "白虎大煞": "강한 사건성, 상처, 수술성, 거친 결단을 품은 보조 신호입니다. 응급 대응·절단 결단 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "白虎大煞백호대살": "강한 사건성, 상처, 수술성, 거친 결단을 품은 보조 신호입니다. 응급 대응·절단 결단 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "백호대살白虎大煞": "강한 사건성, 상처, 수술성, 거친 결단을 품은 보조 신호입니다. 응급 대응·절단 결단 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "백호대살": "강한 사건성, 상처, 수술성, 거친 결단을 품은 보조 신호입니다. 응급 대응·절단 결단 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "鬼門關煞귀문관살": "보이지 않는 뜻을 읽고 직관과 의심이 강해지는 보조 신호입니다. 비정형 해석·심리 감지 분야에서 강점이 살아나며, 직관을 사실로 확정하면 상대의 의도와 현실을 잘못 해석할 수 있습니다.",
  "鬼門關煞": "보이지 않는 뜻을 읽고 직관과 의심이 강해지는 보조 신호입니다. 비정형 해석·심리 감지 분야에서 강점이 살아나며, 직관을 사실로 확정하면 상대의 의도와 현실을 잘못 해석할 수 있습니다.",
  "귀문관살鬼門關煞": "보이지 않는 뜻을 읽고 직관과 의심이 강해지는 보조 신호입니다. 비정형 해석·심리 감지 분야에서 강점이 살아나며, 직관을 사실로 확정하면 상대의 의도와 현실을 잘못 해석할 수 있습니다.",
  "귀문관살": "보이지 않는 뜻을 읽고 직관과 의심이 강해지는 보조 신호입니다. 비정형 해석·심리 감지 분야에서 강점이 살아나며, 직관을 사실로 확정하면 상대의 의도와 현실을 잘못 해석할 수 있습니다.",
  "귀문관살(鬼門關煞)": "보이지 않는 뜻을 읽고 직관과 의심이 강해지는 보조 신호입니다. 비정형 해석·심리 감지 분야에서 강점이 살아나며, 직관을 사실로 확정하면 상대의 의도와 현실을 잘못 해석할 수 있습니다.",
  "원진살": "가까운 관계에서 원망과 미움이 꼬이는 보조 신호입니다. 상대 약점 파악·감정 분석 분야에서 강점이 살아나며, 감정과 원망을 오래 품으면 관계와 회복에 필요한 에너지가 크게 줄어들 수 있습니다.",
  "怨嗔煞원진살": "가까운 관계에서 원망과 미움이 꼬이는 보조 신호입니다. 상대 약점 파악·감정 분석 분야에서 강점이 살아나며, 감정과 원망을 오래 품으면 관계와 회복에 필요한 에너지가 크게 줄어들 수 있습니다.",
  "원진살(怨嗔煞)": "가까운 관계에서 원망과 미움이 꼬이는 보조 신호입니다. 상대 약점 파악·감정 분석 분야에서 강점이 살아나며, 감정과 원망을 오래 품으면 관계와 회복에 필요한 에너지가 크게 줄어들 수 있습니다.",
  "원진살怨嗔煞": "가까운 관계에서 원망과 미움이 꼬이는 보조 신호입니다. 상대 약점 파악·감정 분석 분야에서 강점이 살아나며, 감정과 원망을 오래 품으면 관계와 회복에 필요한 에너지가 크게 줄어들 수 있습니다.",
  "怨嗔煞": "가까운 관계에서 원망과 미움이 꼬이는 보조 신호입니다. 상대 약점 파악·감정 분석 분야에서 강점이 살아나며, 감정과 원망을 오래 품으면 관계와 회복에 필요한 에너지가 크게 줄어들 수 있습니다.",
  "空亡공망": "있어도 비고, 잡아도 빠지는 허전한 상태를 뜻하는 보조 개념입니다. 비움 감각·탈속성 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "공망(空亡)": "있어도 비고, 잡아도 빠지는 허전한 상태를 뜻하는 보조 개념입니다. 비움 감각·탈속성 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "공망空亡": "있어도 비고, 잡아도 빠지는 허전한 상태를 뜻하는 보조 개념입니다. 비움 감각·탈속성 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "공망": "있어도 비고, 잡아도 빠지는 허전한 상태를 뜻하는 보조 개념입니다. 비움 감각·탈속성 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "空亡": "있어도 비고, 잡아도 빠지는 허전한 상태를 뜻하는 보조 개념입니다. 비움 감각·탈속성 측면이 실제 장점으로 작동하는 한편, 충분히 살피려다 결정과 실행이 늦어질 수 있습니다.",
  "懸針煞": "말과 손끝이 날카롭고 찌르는 힘이 생기는 보조 신호입니다. 특히 수술·시술 감각·정교한 작업 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "懸針煞현침살": "말과 손끝이 날카롭고 찌르는 힘이 생기는 보조 신호입니다. 특히 수술·시술 감각·정교한 작업 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "현침살": "말과 손끝이 날카롭고 찌르는 힘이 생기는 보조 신호입니다. 특히 수술·시술 감각·정교한 작업 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "현침살(懸針煞)": "말과 손끝이 날카롭고 찌르는 힘이 생기는 보조 신호입니다. 특히 수술·시술 감각·정교한 작업 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "현침살懸針煞": "말과 손끝이 날카롭고 찌르는 힘이 생기는 보조 신호입니다. 특히 수술·시술 감각·정교한 작업 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "孤辰煞고진살": "혼자 책임지고 버티는 힘과 가까운 관계에서도 일정한 거리를 두려는 성향을 상징하는 보조 신호입니다. 독립성과 집중력은 좋지만, 고립과 갑작스러운 단절로 굳지 않도록 주의해야 합니다.",
  "고진살(孤辰煞)": "혼자 책임지고 버티는 힘과 가까운 관계에서도 일정한 거리를 두려는 성향을 상징하는 보조 신호입니다. 독립성과 집중력은 좋지만, 고립과 갑작스러운 단절로 굳지 않도록 주의해야 합니다.",
  "孤辰煞": "혼자 책임지고 버티는 힘과 가까운 관계에서도 일정한 거리를 두려는 성향을 상징하는 보조 신호입니다. 독립성과 집중력은 좋지만, 고립과 갑작스러운 단절로 굳지 않도록 주의해야 합니다.",
  "고진살孤辰煞": "혼자 책임지고 버티는 힘과 가까운 관계에서도 일정한 거리를 두려는 성향을 상징하는 보조 신호입니다. 독립성과 집중력은 좋지만, 고립과 갑작스러운 단절로 굳지 않도록 주의해야 합니다.",
  "고진살": "혼자 책임지고 버티는 힘과 가까운 관계에서도 일정한 거리를 두려는 성향을 상징하는 보조 신호입니다. 독립성과 집중력은 좋지만, 고립과 갑작스러운 단절로 굳지 않도록 주의해야 합니다.",
  "寡宿煞": "정서적 고독과 친밀 관계에서의 거리감을 상징하는 보조 신호입니다. 혼자 마음을 정리하는 힘은 좋지만, 외로움과 관계 공백을 당연한 것으로 굳히지 않는 것이 중요합니다.",
  "과숙살(寡宿煞)": "정서적 고독과 친밀 관계에서의 거리감을 상징하는 보조 신호입니다. 혼자 마음을 정리하는 힘은 좋지만, 외로움과 관계 공백을 당연한 것으로 굳히지 않는 것이 중요합니다.",
  "과숙살": "정서적 고독과 친밀 관계에서의 거리감을 상징하는 보조 신호입니다. 혼자 마음을 정리하는 힘은 좋지만, 외로움과 관계 공백을 당연한 것으로 굳히지 않는 것이 중요합니다.",
  "寡宿煞과숙살": "정서적 고독과 친밀 관계에서의 거리감을 상징하는 보조 신호입니다. 혼자 마음을 정리하는 힘은 좋지만, 외로움과 관계 공백을 당연한 것으로 굳히지 않는 것이 중요합니다.",
  "과숙살寡宿煞": "정서적 고독과 친밀 관계에서의 거리감을 상징하는 보조 신호입니다. 혼자 마음을 정리하는 힘은 좋지만, 외로움과 관계 공백을 당연한 것으로 굳히지 않는 것이 중요합니다.",
  "천라지망(天羅地網)": "갇히고 묶이며 빠져나오기 어려운 제약의 보조 신호입니다. 복잡한 제도 이해·위기 인내 측면이 실제 장점으로 작동하는 한편, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "천라지망天羅地網": "갇히고 묶이며 빠져나오기 어려운 제약의 보조 신호입니다. 복잡한 제도 이해·위기 인내 측면이 실제 장점으로 작동하는 한편, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "天羅地網천라지망": "갇히고 묶이며 빠져나오기 어려운 제약의 보조 신호입니다. 복잡한 제도 이해·위기 인내 측면이 실제 장점으로 작동하는 한편, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "천라지망": "갇히고 묶이며 빠져나오기 어려운 제약의 보조 신호입니다. 복잡한 제도 이해·위기 인내 측면이 실제 장점으로 작동하는 한편, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "天羅地網": "갇히고 묶이며 빠져나오기 어려운 제약의 보조 신호입니다. 복잡한 제도 이해·위기 인내 측면이 실제 장점으로 작동하는 한편, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "암록": "겉으로 드러나지 않은 도움과 비상 자원, 조용한 준비력을 상징하는 보조 신호입니다. 위기 때 숨은 힘을 꺼내 쓰기 좋지만, 막연한 기대보다 실제 준비와 자립을 유지해야 합니다.",
  "暗祿": "겉으로 드러나지 않은 도움과 비상 자원, 조용한 준비력을 상징하는 보조 신호입니다. 위기 때 숨은 힘을 꺼내 쓰기 좋지만, 막연한 기대보다 실제 준비와 자립을 유지해야 합니다.",
  "暗祿암록": "겉으로 드러나지 않은 도움과 비상 자원, 조용한 준비력을 상징하는 보조 신호입니다. 위기 때 숨은 힘을 꺼내 쓰기 좋지만, 막연한 기대보다 실제 준비와 자립을 유지해야 합니다.",
  "암록暗祿": "겉으로 드러나지 않은 도움과 비상 자원, 조용한 준비력을 상징하는 보조 신호입니다. 위기 때 숨은 힘을 꺼내 쓰기 좋지만, 막연한 기대보다 실제 준비와 자립을 유지해야 합니다.",
  "암록(暗祿)": "겉으로 드러나지 않은 도움과 비상 자원, 조용한 준비력을 상징하는 보조 신호입니다. 위기 때 숨은 힘을 꺼내 쓰기 좋지만, 막연한 기대보다 실제 준비와 자립을 유지해야 합니다.",
  "천희성天喜星": "경사, 혼인, 축하, 밝은 인연을 부르는 보조 신호입니다. 분위기 상승·관계 연결 측면이 실제 장점으로 작동하는 한편, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "천희성(天喜星)": "경사, 혼인, 축하, 밝은 인연을 부르는 보조 신호입니다. 분위기 상승·관계 연결 측면이 실제 장점으로 작동하는 한편, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "天喜星천희성": "경사, 혼인, 축하, 밝은 인연을 부르는 보조 신호입니다. 분위기 상승·관계 연결 측면이 실제 장점으로 작동하는 한편, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "천희성": "경사, 혼인, 축하, 밝은 인연을 부르는 보조 신호입니다. 분위기 상승·관계 연결 측면이 실제 장점으로 작동하는 한편, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "天喜星": "경사, 혼인, 축하, 밝은 인연을 부르는 보조 신호입니다. 분위기 상승·관계 연결 측면이 실제 장점으로 작동하는 한편, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "홍란성紅鸞星": "연애와 혼인 쪽으로 마음과 상황이 움직이는 보조 신호입니다. 삶에서는 애정 표현·분위기 조성 쪽으로 강점이 드러나지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "홍란성(紅鸞星)": "연애와 혼인 쪽으로 마음과 상황이 움직이는 보조 신호입니다. 삶에서는 애정 표현·분위기 조성 쪽으로 강점이 드러나지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "홍란성": "연애와 혼인 쪽으로 마음과 상황이 움직이는 보조 신호입니다. 삶에서는 애정 표현·분위기 조성 쪽으로 강점이 드러나지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "紅鸞星": "연애와 혼인 쪽으로 마음과 상황이 움직이는 보조 신호입니다. 삶에서는 애정 표현·분위기 조성 쪽으로 강점이 드러나지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "紅鸞星홍란성": "연애와 혼인 쪽으로 마음과 상황이 움직이는 보조 신호입니다. 삶에서는 애정 표현·분위기 조성 쪽으로 강점이 드러나지만, 속도가 지나치면 판단이 거칠어지고 회복 전에 에너지가 소진될 수 있습니다.",
  "천의성天醫星": "치유, 돌봄, 의료·건강 관리의 감각을 붙이는 보조 신호입니다. 삶에서는 치유 감각·관리 능력 쪽으로 강점이 드러나지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "天醫星": "치유, 돌봄, 의료·건강 관리의 감각을 붙이는 보조 신호입니다. 삶에서는 치유 감각·관리 능력 쪽으로 강점이 드러나지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "천의성": "치유, 돌봄, 의료·건강 관리의 감각을 붙이는 보조 신호입니다. 삶에서는 치유 감각·관리 능력 쪽으로 강점이 드러나지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "天醫星천의성": "치유, 돌봄, 의료·건강 관리의 감각을 붙이는 보조 신호입니다. 삶에서는 치유 감각·관리 능력 쪽으로 강점이 드러나지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "천의성(天醫星)": "치유, 돌봄, 의료·건강 관리의 감각을 붙이는 보조 신호입니다. 삶에서는 치유 감각·관리 능력 쪽으로 강점이 드러나지만, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "천문성(天門星)": "하늘의 문처럼 직관, 종교성, 비정형 감각을 여는 보조 신호입니다. 명상·사색·비정형 해석 측면이 실제 장점으로 작동하는 한편, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "天門星": "하늘의 문처럼 직관, 종교성, 비정형 감각을 여는 보조 신호입니다. 명상·사색·비정형 해석 측면이 실제 장점으로 작동하는 한편, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "天門星천문성": "하늘의 문처럼 직관, 종교성, 비정형 감각을 여는 보조 신호입니다. 명상·사색·비정형 해석 측면이 실제 장점으로 작동하는 한편, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "천문성": "하늘의 문처럼 직관, 종교성, 비정형 감각을 여는 보조 신호입니다. 명상·사색·비정형 해석 측면이 실제 장점으로 작동하는 한편, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "천문성天門星": "하늘의 문처럼 직관, 종교성, 비정형 감각을 여는 보조 신호입니다. 명상·사색·비정형 해석 측면이 실제 장점으로 작동하는 한편, 관계를 감당한 뒤 혼자 물러나거나 정서적 피로를 오래 품을 수 있습니다.",
  "鐵鎖開金": "막힌 문제의 자물쇠를 여는 실무형 보조 개념입니다. 특히 원인 추적·수리·교정 측면에 힘이 실리며, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "鐵鎖開金철쇄개금": "막힌 문제의 자물쇠를 여는 실무형 보조 개념입니다. 특히 원인 추적·수리·교정 측면에 힘이 실리며, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "철쇄개금鐵鎖開金": "막힌 문제의 자물쇠를 여는 실무형 보조 개념입니다. 특히 원인 추적·수리·교정 측면에 힘이 실리며, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "철쇄개금(鐵鎖開金)": "막힌 문제의 자물쇠를 여는 실무형 보조 개념입니다. 특히 원인 추적·수리·교정 측면에 힘이 실리며, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "철쇄개금": "막힌 문제의 자물쇠를 여는 실무형 보조 개념입니다. 특히 원인 추적·수리·교정 측면에 힘이 실리며, 책임 범위를 넓게 잡으면 자신의 한계를 넘겨 소진되기 쉽습니다.",
  "탕화살": "불, 열, 물, 급한 반응과 사고성을 상징하는 보조 개념입니다. 위험 현장 감각·응급 처리 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "湯火煞": "불, 열, 물, 급한 반응과 사고성을 상징하는 보조 개념입니다. 위험 현장 감각·응급 처리 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "湯火煞탕화살": "불, 열, 물, 급한 반응과 사고성을 상징하는 보조 개념입니다. 위험 현장 감각·응급 처리 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "탕화살湯火煞": "불, 열, 물, 급한 반응과 사고성을 상징하는 보조 개념입니다. 위험 현장 감각·응급 처리 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "탕화살(湯火煞)": "불, 열, 물, 급한 반응과 사고성을 상징하는 보조 개념입니다. 위험 현장 감각·응급 처리 측면이 실제 장점으로 작동하는 한편, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "급각살急脚煞": "발과 이동, 급한 움직임에서 손상이 생긴다는 보조 개념입니다. 특히 빠른 현장 대응·기동력 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "급각살": "발과 이동, 급한 움직임에서 손상이 생긴다는 보조 개념입니다. 특히 빠른 현장 대응·기동력 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "急脚煞급각살": "발과 이동, 급한 움직임에서 손상이 생긴다는 보조 개념입니다. 특히 빠른 현장 대응·기동력 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "급각살(急脚煞)": "발과 이동, 급한 움직임에서 손상이 생긴다는 보조 개념입니다. 특히 빠른 현장 대응·기동력 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "急脚煞": "발과 이동, 급한 움직임에서 손상이 생긴다는 보조 개념입니다. 특히 빠른 현장 대응·기동력 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "斷橋關": "길이 끊기고 이동·관계가 중간에서 막히는 보조 개념입니다. 위험 회피·우회로 찾기 분야에서 강점이 살아나며, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "단교관斷橋關": "길이 끊기고 이동·관계가 중간에서 막히는 보조 개념입니다. 위험 회피·우회로 찾기 분야에서 강점이 살아나며, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "斷橋關단교관": "길이 끊기고 이동·관계가 중간에서 막히는 보조 개념입니다. 위험 회피·우회로 찾기 분야에서 강점이 살아나며, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "단교관(斷橋關)": "길이 끊기고 이동·관계가 중간에서 막히는 보조 개념입니다. 위험 회피·우회로 찾기 분야에서 강점이 살아나며, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "단교관": "길이 끊기고 이동·관계가 중간에서 막히는 보조 개념입니다. 위험 회피·우회로 찾기 분야에서 강점이 살아나며, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "落井關낙정관": "아래로 떨어지는 물상과 실수·방심을 다루는 보조 개념입니다. 삶에서는 위험 감지·안전 점검 쪽으로 강점이 드러나지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "낙정관": "아래로 떨어지는 물상과 실수·방심을 다루는 보조 개념입니다. 삶에서는 위험 감지·안전 점검 쪽으로 강점이 드러나지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "落井關": "아래로 떨어지는 물상과 실수·방심을 다루는 보조 개념입니다. 삶에서는 위험 감지·안전 점검 쪽으로 강점이 드러나지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "낙정관(落井關)": "아래로 떨어지는 물상과 실수·방심을 다루는 보조 개념입니다. 삶에서는 위험 감지·안전 점검 쪽으로 강점이 드러나지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "낙정관落井關": "아래로 떨어지는 물상과 실수·방심을 다루는 보조 개념입니다. 삶에서는 위험 감지·안전 점검 쪽으로 강점이 드러나지만, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "血刃": "피, 칼, 상처, 절개성 사건과 연결되는 보조 개념입니다. 특히 의료 감각·절개 결단 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "혈인(血刃)": "피, 칼, 상처, 절개성 사건과 연결되는 보조 개념입니다. 특히 의료 감각·절개 결단 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "혈인血刃": "피, 칼, 상처, 절개성 사건과 연결되는 보조 개념입니다. 특히 의료 감각·절개 결단 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "혈인": "피, 칼, 상처, 절개성 사건과 연결되는 보조 개념입니다. 특히 의료 감각·절개 결단 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "血刃혈인": "피, 칼, 상처, 절개성 사건과 연결되는 보조 개념입니다. 특히 의료 감각·절개 결단 측면에 힘이 실리며, 긴장과 속도를 높이는 상황에서는 안전 절차와 신체 신호를 먼저 확인해야 합니다.",
  "음양차착": "남녀·관계·결혼에서 결이 어긋난다는 보조 개념입니다. 삶에서는 차이 감지·관계 분석 쪽으로 강점이 드러나지만, 차이를 운명적 문제로 단정하면 관계 조율의 가능성을 놓칠 수 있습니다.",
  "陰陽差錯음양차착": "남녀·관계·결혼에서 결이 어긋난다는 보조 개념입니다. 삶에서는 차이 감지·관계 분석 쪽으로 강점이 드러나지만, 차이를 운명적 문제로 단정하면 관계 조율의 가능성을 놓칠 수 있습니다.",
  "음양차착陰陽差錯": "남녀·관계·결혼에서 결이 어긋난다는 보조 개념입니다. 삶에서는 차이 감지·관계 분석 쪽으로 강점이 드러나지만, 차이를 운명적 문제로 단정하면 관계 조율의 가능성을 놓칠 수 있습니다.",
  "음양차착(陰陽差錯)": "남녀·관계·결혼에서 결이 어긋난다는 보조 개념입니다. 삶에서는 차이 감지·관계 분석 쪽으로 강점이 드러나지만, 차이를 운명적 문제로 단정하면 관계 조율의 가능성을 놓칠 수 있습니다.",
  "陰陽差錯": "남녀·관계·결혼에서 결이 어긋난다는 보조 개념입니다. 삶에서는 차이 감지·관계 분석 쪽으로 강점이 드러나지만, 차이를 운명적 문제로 단정하면 관계 조율의 가능성을 놓칠 수 있습니다.",
  "고란살": "배우자 인연의 고독과 정서적 쓸쓸함을 말하는 보조 개념입니다. 삶에서는 혼자 버팀·내면 몰입 쪽으로 강점이 드러나지만, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "고란살孤鸞煞": "배우자 인연의 고독과 정서적 쓸쓸함을 말하는 보조 개념입니다. 삶에서는 혼자 버팀·내면 몰입 쪽으로 강점이 드러나지만, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "孤鸞煞": "배우자 인연의 고독과 정서적 쓸쓸함을 말하는 보조 개념입니다. 삶에서는 혼자 버팀·내면 몰입 쪽으로 강점이 드러나지만, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "고란살(孤鸞煞)": "배우자 인연의 고독과 정서적 쓸쓸함을 말하는 보조 개념입니다. 삶에서는 혼자 버팀·내면 몰입 쪽으로 강점이 드러나지만, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "孤鸞煞고란살": "배우자 인연의 고독과 정서적 쓸쓸함을 말하는 보조 개념입니다. 삶에서는 혼자 버팀·내면 몰입 쪽으로 강점이 드러나지만, 불편을 오래 참다가 관계나 일을 갑자기 정리할 수 있습니다.",
  "八專煞": "한 기운이 치우쳐 고집과 반복성이 강해진다는 보조 개념입니다. 전문 몰입·반복 숙련 측면이 실제 장점으로 작동하는 한편, 한 방식만 반복하면 생각과 관계의 폭이 좁아질 수 있습니다.",
  "팔전살": "한 기운이 치우쳐 고집과 반복성이 강해진다는 보조 개념입니다. 전문 몰입·반복 숙련 측면이 실제 장점으로 작동하는 한편, 한 방식만 반복하면 생각과 관계의 폭이 좁아질 수 있습니다.",
  "팔전살八專煞": "한 기운이 치우쳐 고집과 반복성이 강해진다는 보조 개념입니다. 전문 몰입·반복 숙련 측면이 실제 장점으로 작동하는 한편, 한 방식만 반복하면 생각과 관계의 폭이 좁아질 수 있습니다.",
  "팔전살(八專煞)": "한 기운이 치우쳐 고집과 반복성이 강해진다는 보조 개념입니다. 전문 몰입·반복 숙련 측면이 실제 장점으로 작동하는 한편, 한 방식만 반복하면 생각과 관계의 폭이 좁아질 수 있습니다.",
  "八專煞팔전살": "한 기운이 치우쳐 고집과 반복성이 강해진다는 보조 개념입니다. 전문 몰입·반복 숙련 측면이 실제 장점으로 작동하는 한편, 한 방식만 반복하면 생각과 관계의 폭이 좁아질 수 있습니다.",
  "九醜妨害구추방해": "추함과 방해라는 이름으로 관계·이미지 손상을 말하던 보조 개념입니다. 약점 감지·이미지 보완 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "구추방해九醜妨害": "추함과 방해라는 이름으로 관계·이미지 손상을 말하던 보조 개념입니다. 약점 감지·이미지 보완 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "구추방해(九醜妨害)": "추함과 방해라는 이름으로 관계·이미지 손상을 말하던 보조 개념입니다. 약점 감지·이미지 보완 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "구추방해": "추함과 방해라는 이름으로 관계·이미지 손상을 말하던 보조 개념입니다. 약점 감지·이미지 보완 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "九醜妨害": "추함과 방해라는 이름으로 관계·이미지 손상을 말하던 보조 개념입니다. 약점 감지·이미지 보완 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "십악대패(十惡大敗)": "크게 잃고 무너지는 이름의 고전 보조 개념입니다. 위험 인식·재정 경계 분야에서 강점이 살아나며, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "십악대패十惡大敗": "크게 잃고 무너지는 이름의 고전 보조 개념입니다. 위험 인식·재정 경계 분야에서 강점이 살아나며, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "十惡大敗": "크게 잃고 무너지는 이름의 고전 보조 개념입니다. 위험 인식·재정 경계 분야에서 강점이 살아나며, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "十惡大敗십악대패": "크게 잃고 무너지는 이름의 고전 보조 개념입니다. 위험 인식·재정 경계 분야에서 강점이 살아나며, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "십악대패": "크게 잃고 무너지는 이름의 고전 보조 개념입니다. 위험 인식·재정 경계 분야에서 강점이 살아나며, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "喪門": "상실·애도·집안의 무거운 일을 상징하는 연운성 보조 개념입니다. 특히 위로 능력·의례 감각 측면에 힘이 실리며, 무거운 감정을 혼자 감당하면 일상과 관계의 활력이 떨어질 수 있습니다.",
  "상문喪門": "상실·애도·집안의 무거운 일을 상징하는 연운성 보조 개념입니다. 특히 위로 능력·의례 감각 측면에 힘이 실리며, 무거운 감정을 혼자 감당하면 일상과 관계의 활력이 떨어질 수 있습니다.",
  "상문(喪門)": "상실·애도·집안의 무거운 일을 상징하는 연운성 보조 개념입니다. 특히 위로 능력·의례 감각 측면에 힘이 실리며, 무거운 감정을 혼자 감당하면 일상과 관계의 활력이 떨어질 수 있습니다.",
  "상문": "상실·애도·집안의 무거운 일을 상징하는 연운성 보조 개념입니다. 특히 위로 능력·의례 감각 측면에 힘이 실리며, 무거운 감정을 혼자 감당하면 일상과 관계의 활력이 떨어질 수 있습니다.",
  "喪門상문": "상실·애도·집안의 무거운 일을 상징하는 연운성 보조 개념입니다. 특히 위로 능력·의례 감각 측면에 힘이 실리며, 무거운 감정을 혼자 감당하면 일상과 관계의 활력이 떨어질 수 있습니다.",
  "弔客": "조문·상실·밖에서 들어오는 무거운 소식을 상징하는 보조 개념입니다. 특히 의례 처리·위로 표현 측면에 힘이 실리며, 주변의 무거운 일을 지나치게 흡수하면 자신의 일상까지 위축될 수 있습니다.",
  "조객": "조문·상실·밖에서 들어오는 무거운 소식을 상징하는 보조 개념입니다. 특히 의례 처리·위로 표현 측면에 힘이 실리며, 주변의 무거운 일을 지나치게 흡수하면 자신의 일상까지 위축될 수 있습니다.",
  "弔客조객": "조문·상실·밖에서 들어오는 무거운 소식을 상징하는 보조 개념입니다. 특히 의례 처리·위로 표현 측면에 힘이 실리며, 주변의 무거운 일을 지나치게 흡수하면 자신의 일상까지 위축될 수 있습니다.",
  "조객弔客": "조문·상실·밖에서 들어오는 무거운 소식을 상징하는 보조 개념입니다. 특히 의례 처리·위로 표현 측면에 힘이 실리며, 주변의 무거운 일을 지나치게 흡수하면 자신의 일상까지 위축될 수 있습니다.",
  "조객(弔客)": "조문·상실·밖에서 들어오는 무거운 소식을 상징하는 보조 개념입니다. 특히 의례 처리·위로 표현 측면에 힘이 실리며, 주변의 무거운 일을 지나치게 흡수하면 자신의 일상까지 위축될 수 있습니다.",
  "관부(官符)": "관청, 문서, 규정, 시비가 따라붙는 보조 개념입니다. 문서 검토·규정 이해 분야에서 강점이 살아나며, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "관부": "관청, 문서, 규정, 시비가 따라붙는 보조 개념입니다. 문서 검토·규정 이해 분야에서 강점이 살아나며, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "官符": "관청, 문서, 규정, 시비가 따라붙는 보조 개념입니다. 문서 검토·규정 이해 분야에서 강점이 살아나며, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "官符관부": "관청, 문서, 규정, 시비가 따라붙는 보조 개념입니다. 문서 검토·규정 이해 분야에서 강점이 살아나며, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "관부官符": "관청, 문서, 규정, 시비가 따라붙는 보조 개념입니다. 문서 검토·규정 이해 분야에서 강점이 살아나며, 규정과 문서가 얽힌 일에서는 감정보다 절차와 기록을 우선하는 편이 안전합니다.",
  "병부病符": "병치레와 컨디션 저하를 상징하는 연운성 보조 개념입니다. 삶에서는 건강 관리·돌봄 감각 쪽으로 강점이 드러나지만, 몸의 신호를 살피되 불안을 키우는 자기진단과 과도한 걱정은 줄일 필요가 있습니다.",
  "病符": "병치레와 컨디션 저하를 상징하는 연운성 보조 개념입니다. 삶에서는 건강 관리·돌봄 감각 쪽으로 강점이 드러나지만, 몸의 신호를 살피되 불안을 키우는 자기진단과 과도한 걱정은 줄일 필요가 있습니다.",
  "병부": "병치레와 컨디션 저하를 상징하는 연운성 보조 개념입니다. 삶에서는 건강 관리·돌봄 감각 쪽으로 강점이 드러나지만, 몸의 신호를 살피되 불안을 키우는 자기진단과 과도한 걱정은 줄일 필요가 있습니다.",
  "病符병부": "병치레와 컨디션 저하를 상징하는 연운성 보조 개념입니다. 삶에서는 건강 관리·돌봄 감각 쪽으로 강점이 드러나지만, 몸의 신호를 살피되 불안을 키우는 자기진단과 과도한 걱정은 줄일 필요가 있습니다.",
  "병부(病符)": "병치레와 컨디션 저하를 상징하는 연운성 보조 개념입니다. 삶에서는 건강 관리·돌봄 감각 쪽으로 강점이 드러나지만, 몸의 신호를 살피되 불안을 키우는 자기진단과 과도한 걱정은 줄일 필요가 있습니다.",
  "사부死符": "끝, 정지, 기운 저하를 상징하는 보관용 보조 개념입니다. 정리 능력·마감 처리 측면이 실제 장점으로 작동하는 한편, 끝내야 할 것을 정리하는 힘은 있지만 의욕과 활동이 지나치게 줄 수 있습니다.",
  "死符사부": "끝, 정지, 기운 저하를 상징하는 보관용 보조 개념입니다. 정리 능력·마감 처리 측면이 실제 장점으로 작동하는 한편, 끝내야 할 것을 정리하는 힘은 있지만 의욕과 활동이 지나치게 줄 수 있습니다.",
  "사부": "끝, 정지, 기운 저하를 상징하는 보관용 보조 개념입니다. 정리 능력·마감 처리 측면이 실제 장점으로 작동하는 한편, 끝내야 할 것을 정리하는 힘은 있지만 의욕과 활동이 지나치게 줄 수 있습니다.",
  "死符": "끝, 정지, 기운 저하를 상징하는 보관용 보조 개념입니다. 정리 능력·마감 처리 측면이 실제 장점으로 작동하는 한편, 끝내야 할 것을 정리하는 힘은 있지만 의욕과 활동이 지나치게 줄 수 있습니다.",
  "사부(死符)": "끝, 정지, 기운 저하를 상징하는 보관용 보조 개념입니다. 정리 능력·마감 처리 측면이 실제 장점으로 작동하는 한편, 끝내야 할 것을 정리하는 힘은 있지만 의욕과 활동이 지나치게 줄 수 있습니다.",
  "대모": "큰 지출과 빠른 소모를 상징하는 보조 개념입니다. 규모 감각·자금 운용 분야에서 강점이 살아나며, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "大耗": "큰 지출과 빠른 소모를 상징하는 보조 개념입니다. 규모 감각·자금 운용 분야에서 강점이 살아나며, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "大耗대모": "큰 지출과 빠른 소모를 상징하는 보조 개념입니다. 규모 감각·자금 운용 분야에서 강점이 살아나며, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "대모大耗": "큰 지출과 빠른 소모를 상징하는 보조 개념입니다. 규모 감각·자금 운용 분야에서 강점이 살아나며, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "대모(大耗)": "큰 지출과 빠른 소모를 상징하는 보조 개념입니다. 규모 감각·자금 운용 분야에서 강점이 살아나며, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "소모": "자잘한 지출과 잔손실을 상징하는 보조 개념입니다. 소액 관리·누수 점검 분야에서 강점이 살아나며, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "소모(小耗)": "자잘한 지출과 잔손실을 상징하는 보조 개념입니다. 소액 관리·누수 점검 분야에서 강점이 살아나며, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "小耗소모": "자잘한 지출과 잔손실을 상징하는 보조 개념입니다. 소액 관리·누수 점검 분야에서 강점이 살아나며, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "小耗": "자잘한 지출과 잔손실을 상징하는 보조 개념입니다. 소액 관리·누수 점검 분야에서 강점이 살아나며, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "소모小耗": "자잘한 지출과 잔손실을 상징하는 보조 개념입니다. 소액 관리·누수 점검 분야에서 강점이 살아나며, 돈과 에너지가 예상보다 빠르게 새지 않도록 한도와 정산 기준이 필요합니다.",
  "천주귀인天廚貴人": "먹을 복, 음식, 접대, 생활 풍요를 상징하는 보조 신호입니다. 요리 감각·서비스 감각 측면이 실제 장점으로 작동하는 한편, 즐거움과 접대가 지나치면 소비와 생활 리듬이 흐트러질 수 있습니다.",
  "天廚貴人": "먹을 복, 음식, 접대, 생활 풍요를 상징하는 보조 신호입니다. 요리 감각·서비스 감각 측면이 실제 장점으로 작동하는 한편, 즐거움과 접대가 지나치면 소비와 생활 리듬이 흐트러질 수 있습니다.",
  "천주귀인(天廚貴人)": "먹을 복, 음식, 접대, 생활 풍요를 상징하는 보조 신호입니다. 요리 감각·서비스 감각 측면이 실제 장점으로 작동하는 한편, 즐거움과 접대가 지나치면 소비와 생활 리듬이 흐트러질 수 있습니다.",
  "천주귀인": "먹을 복, 음식, 접대, 생활 풍요를 상징하는 보조 신호입니다. 요리 감각·서비스 감각 측면이 실제 장점으로 작동하는 한편, 즐거움과 접대가 지나치면 소비와 생활 리듬이 흐트러질 수 있습니다.",
  "天廚貴人천주귀인": "먹을 복, 음식, 접대, 생활 풍요를 상징하는 보조 신호입니다. 요리 감각·서비스 감각 측면이 실제 장점으로 작동하는 한편, 즐거움과 접대가 지나치면 소비와 생활 리듬이 흐트러질 수 있습니다.",
  "孤病煞고병살": "고독과 병약성을 함께 묶어 말하던 보관용 보조 개념입니다. 삶에서는 자기 관찰·회복 관리 쪽으로 강점이 드러나지만, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "고병살孤病煞": "고독과 병약성을 함께 묶어 말하던 보관용 보조 개념입니다. 삶에서는 자기 관찰·회복 관리 쪽으로 강점이 드러나지만, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "孤病煞": "고독과 병약성을 함께 묶어 말하던 보관용 보조 개념입니다. 삶에서는 자기 관찰·회복 관리 쪽으로 강점이 드러나지만, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "고병살": "고독과 병약성을 함께 묶어 말하던 보관용 보조 개념입니다. 삶에서는 자기 관찰·회복 관리 쪽으로 강점이 드러나지만, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "고병살(孤病煞)": "고독과 병약성을 함께 묶어 말하던 보관용 보조 개념입니다. 삶에서는 자기 관찰·회복 관리 쪽으로 강점이 드러나지만, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "형옥살(刑獄煞)": "형벌·구속·관재를 거칠게 말하던 보관용 보조 개념입니다. 법적 감각·위험 경계 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "刑獄煞형옥살": "형벌·구속·관재를 거칠게 말하던 보관용 보조 개념입니다. 법적 감각·위험 경계 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "형옥살": "형벌·구속·관재를 거칠게 말하던 보관용 보조 개념입니다. 법적 감각·위험 경계 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "刑獄煞": "형벌·구속·관재를 거칠게 말하던 보관용 보조 개념입니다. 법적 감각·위험 경계 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "형옥살刑獄煞": "형벌·구속·관재를 거칠게 말하던 보관용 보조 개념입니다. 법적 감각·위험 경계 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "倒插桃花도삽도화": "비정상적 도화·관계 혼란을 말하던 보관용 보조 개념입니다. 이성 감각·노출성 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "도삽도화倒插桃花": "비정상적 도화·관계 혼란을 말하던 보관용 보조 개념입니다. 이성 감각·노출성 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "도삽도화": "비정상적 도화·관계 혼란을 말하던 보관용 보조 개념입니다. 이성 감각·노출성 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "도삽도화(倒插桃花)": "비정상적 도화·관계 혼란을 말하던 보관용 보조 개념입니다. 이성 감각·노출성 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "倒插桃花": "비정상적 도화·관계 혼란을 말하던 보관용 보조 개념입니다. 이성 감각·노출성 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "裸體桃花나체도화": "노골적 성적 이미지로 쓰이던 보관용 도화 보조 개념입니다. 삶에서는 몸 이미지·무대성 쪽으로 강점이 드러나지만, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "나체도화裸體桃花": "노골적 성적 이미지로 쓰이던 보관용 도화 보조 개념입니다. 삶에서는 몸 이미지·무대성 쪽으로 강점이 드러나지만, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "나체도화(裸體桃花)": "노골적 성적 이미지로 쓰이던 보관용 도화 보조 개념입니다. 삶에서는 몸 이미지·무대성 쪽으로 강점이 드러나지만, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "裸體桃花": "노골적 성적 이미지로 쓰이던 보관용 도화 보조 개념입니다. 삶에서는 몸 이미지·무대성 쪽으로 강점이 드러나지만, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "나체도화": "노골적 성적 이미지로 쓰이던 보관용 도화 보조 개념입니다. 삶에서는 몸 이미지·무대성 쪽으로 강점이 드러나지만, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "음욕살": "욕망을 낙인찍는 식으로 쓰이던 보관용 보조 개념입니다. 삶에서는 감각 표현·매력 사용 쪽으로 강점이 드러나지만, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "음욕살淫慾煞": "욕망을 낙인찍는 식으로 쓰이던 보관용 보조 개념입니다. 삶에서는 감각 표현·매력 사용 쪽으로 강점이 드러나지만, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "淫慾煞": "욕망을 낙인찍는 식으로 쓰이던 보관용 보조 개념입니다. 삶에서는 감각 표현·매력 사용 쪽으로 강점이 드러나지만, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "淫慾煞음욕살": "욕망을 낙인찍는 식으로 쓰이던 보관용 보조 개념입니다. 삶에서는 감각 표현·매력 사용 쪽으로 강점이 드러나지만, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "음욕살(淫慾煞)": "욕망을 낙인찍는 식으로 쓰이던 보관용 보조 개념입니다. 삶에서는 감각 표현·매력 사용 쪽으로 강점이 드러나지만, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "과부살": "여성의 배우자 인연을 낙인찍어 말하던 보관용 보조 개념입니다. 독립 생활·내면 몰입 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "과부살寡婦煞": "여성의 배우자 인연을 낙인찍어 말하던 보관용 보조 개념입니다. 독립 생활·내면 몰입 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "寡婦煞": "여성의 배우자 인연을 낙인찍어 말하던 보관용 보조 개념입니다. 독립 생활·내면 몰입 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "寡婦煞과부살": "여성의 배우자 인연을 낙인찍어 말하던 보관용 보조 개념입니다. 독립 생활·내면 몰입 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "과부살(寡婦煞)": "여성의 배우자 인연을 낙인찍어 말하던 보관용 보조 개념입니다. 독립 생활·내면 몰입 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "傷處煞": "몸의 상처와 흉터를 단정적으로 말하던 보관용 보조 개념입니다. 특히 안전 감각·치료 관심 측면에 힘이 실리며, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "상처살(傷處煞)": "몸의 상처와 흉터를 단정적으로 말하던 보관용 보조 개념입니다. 특히 안전 감각·치료 관심 측면에 힘이 실리며, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "상처살傷處煞": "몸의 상처와 흉터를 단정적으로 말하던 보관용 보조 개념입니다. 특히 안전 감각·치료 관심 측면에 힘이 실리며, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "상처살": "몸의 상처와 흉터를 단정적으로 말하던 보관용 보조 개념입니다. 특히 안전 감각·치료 관심 측면에 힘이 실리며, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "傷處煞상처살": "몸의 상처와 흉터를 단정적으로 말하던 보관용 보조 개념입니다. 특히 안전 감각·치료 관심 측면에 힘이 실리며, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "下賤煞": "신분·격을 낮춰 말하던 역사적 보관용 보조 개념입니다. 현장 감각·끈질김 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "하천살下賤煞": "신분·격을 낮춰 말하던 역사적 보관용 보조 개념입니다. 현장 감각·끈질김 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "하천살(下賤煞)": "신분·격을 낮춰 말하던 역사적 보관용 보조 개념입니다. 현장 감각·끈질김 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "下賤煞하천살": "신분·격을 낮춰 말하던 역사적 보관용 보조 개념입니다. 현장 감각·끈질김 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "하천살": "신분·격을 낮춰 말하던 역사적 보관용 보조 개념입니다. 현장 감각·끈질김 측면이 실제 장점으로 작동하는 한편, 이 이름을 사람의 가치나 관계를 단정하는 낙인으로 사용해서는 안 됩니다.",
  "01.甲子갑자일주": "새로운 정보와 분위기를 빠르게 흡수해 자기 방식의 아이디어로 바꾸는 성향입니다. 생각이 많아지면 불안과 감정 기복을 숨긴 채 관계에서 거리를 둘 수 있습니다.",
  "甲子": "새로운 정보와 분위기를 빠르게 흡수해 자기 방식의 아이디어로 바꾸는 성향입니다. 생각이 많아지면 불안과 감정 기복을 숨긴 채 관계에서 거리를 둘 수 있습니다.",
  "갑자일주甲子": "새로운 정보와 분위기를 빠르게 흡수해 자기 방식의 아이디어로 바꾸는 성향입니다. 생각이 많아지면 불안과 감정 기복을 숨긴 채 관계에서 거리를 둘 수 있습니다.",
  "갑자일주": "새로운 정보와 분위기를 빠르게 흡수해 자기 방식의 아이디어로 바꾸는 성향입니다. 생각이 많아지면 불안과 감정 기복을 숨긴 채 관계에서 거리를 둘 수 있습니다.",
  "甲子갑자일주": "새로운 정보와 분위기를 빠르게 흡수해 자기 방식의 아이디어로 바꾸는 성향입니다. 생각이 많아지면 불안과 감정 기복을 숨긴 채 관계에서 거리를 둘 수 있습니다.",
  "을축일주": "생활의 작은 손익과 흐름을 세심하게 살피며 천천히 신뢰를 쌓는 성향입니다. 오래 버티는 힘이 좋지만, 걱정과 서운함을 안에 저장하면 관계가 답답해질 수 있습니다.",
  "乙丑을축일주": "생활의 작은 손익과 흐름을 세심하게 살피며 천천히 신뢰를 쌓는 성향입니다. 오래 버티는 힘이 좋지만, 걱정과 서운함을 안에 저장하면 관계가 답답해질 수 있습니다.",
  "02.乙丑을축일주": "생활의 작은 손익과 흐름을 세심하게 살피며 천천히 신뢰를 쌓는 성향입니다. 오래 버티는 힘이 좋지만, 걱정과 서운함을 안에 저장하면 관계가 답답해질 수 있습니다.",
  "乙丑": "생활의 작은 손익과 흐름을 세심하게 살피며 천천히 신뢰를 쌓는 성향입니다. 오래 버티는 힘이 좋지만, 걱정과 서운함을 안에 저장하면 관계가 답답해질 수 있습니다.",
  "을축일주乙丑": "생활의 작은 손익과 흐름을 세심하게 살피며 천천히 신뢰를 쌓는 성향입니다. 오래 버티는 힘이 좋지만, 걱정과 서운함을 안에 저장하면 관계가 답답해질 수 있습니다.",
  "丙寅": "큰 그림을 빠르게 잡고 사람들 앞에서 분위기와 방향을 이끄는 성향입니다. 개척과 추진에는 강하지만, 인정 욕구와 속도가 앞서면 과열과 성급한 결론이 생길 수 있습니다.",
  "丙寅병인일주": "큰 그림을 빠르게 잡고 사람들 앞에서 분위기와 방향을 이끄는 성향입니다. 개척과 추진에는 강하지만, 인정 욕구와 속도가 앞서면 과열과 성급한 결론이 생길 수 있습니다.",
  "병인일주": "큰 그림을 빠르게 잡고 사람들 앞에서 분위기와 방향을 이끄는 성향입니다. 개척과 추진에는 강하지만, 인정 욕구와 속도가 앞서면 과열과 성급한 결론이 생길 수 있습니다.",
  "병인일주丙寅": "큰 그림을 빠르게 잡고 사람들 앞에서 분위기와 방향을 이끄는 성향입니다. 개척과 추진에는 강하지만, 인정 욕구와 속도가 앞서면 과열과 성급한 결론이 생길 수 있습니다.",
  "03.丙寅병인일주": "큰 그림을 빠르게 잡고 사람들 앞에서 분위기와 방향을 이끄는 성향입니다. 개척과 추진에는 강하지만, 인정 욕구와 속도가 앞서면 과열과 성급한 결론이 생길 수 있습니다.",
  "丁卯정묘일주": "말투와 분위기의 미세한 차이를 읽고 아름답고 부드러운 방식으로 표현하는 성향입니다. 관계 반응에 예민해지면 질투와 상처 기억이 쌓여 친밀감에 피로를 느낄 수 있습니다.",
  "정묘일주": "말투와 분위기의 미세한 차이를 읽고 아름답고 부드러운 방식으로 표현하는 성향입니다. 관계 반응에 예민해지면 질투와 상처 기억이 쌓여 친밀감에 피로를 느낄 수 있습니다.",
  "丁卯": "말투와 분위기의 미세한 차이를 읽고 아름답고 부드러운 방식으로 표현하는 성향입니다. 관계 반응에 예민해지면 질투와 상처 기억이 쌓여 친밀감에 피로를 느낄 수 있습니다.",
  "정묘일주丁卯": "말투와 분위기의 미세한 차이를 읽고 아름답고 부드러운 방식으로 표현하는 성향입니다. 관계 반응에 예민해지면 질투와 상처 기억이 쌓여 친밀감에 피로를 느낄 수 있습니다.",
  "04.丁卯정묘일주": "말투와 분위기의 미세한 차이를 읽고 아름답고 부드러운 방식으로 표현하는 성향입니다. 관계 반응에 예민해지면 질투와 상처 기억이 쌓여 친밀감에 피로를 느낄 수 있습니다.",
  "무진일주": "현실의 기반과 자원을 오래 지키며 큰 책임을 묵묵히 감당하는 성향입니다. 판단은 안정적이지만 변화에 저항하거나 억울함을 쌓으면 통제와 고집이 강해질 수 있습니다.",
  "05.戊辰무진일주": "현실의 기반과 자원을 오래 지키며 큰 책임을 묵묵히 감당하는 성향입니다. 판단은 안정적이지만 변화에 저항하거나 억울함을 쌓으면 통제와 고집이 강해질 수 있습니다.",
  "무진일주戊辰": "현실의 기반과 자원을 오래 지키며 큰 책임을 묵묵히 감당하는 성향입니다. 판단은 안정적이지만 변화에 저항하거나 억울함을 쌓으면 통제와 고집이 강해질 수 있습니다.",
  "戊辰": "현실의 기반과 자원을 오래 지키며 큰 책임을 묵묵히 감당하는 성향입니다. 판단은 안정적이지만 변화에 저항하거나 억울함을 쌓으면 통제와 고집이 강해질 수 있습니다.",
  "戊辰무진일주": "현실의 기반과 자원을 오래 지키며 큰 책임을 묵묵히 감당하는 성향입니다. 판단은 안정적이지만 변화에 저항하거나 억울함을 쌓으면 통제와 고집이 강해질 수 있습니다.",
  "기사일주": "사람과 상황의 미세한 변화를 빨리 읽고 생활과 실무를 깔끔하게 정리하는 성향입니다. 완성도와 평판을 지나치게 의식하면 속으로 긴장하고 과로하기 쉽습니다.",
  "기사일주己巳": "사람과 상황의 미세한 변화를 빨리 읽고 생활과 실무를 깔끔하게 정리하는 성향입니다. 완성도와 평판을 지나치게 의식하면 속으로 긴장하고 과로하기 쉽습니다.",
  "己巳기사일주": "사람과 상황의 미세한 변화를 빨리 읽고 생활과 실무를 깔끔하게 정리하는 성향입니다. 완성도와 평판을 지나치게 의식하면 속으로 긴장하고 과로하기 쉽습니다.",
  "06.己巳기사일주": "사람과 상황의 미세한 변화를 빨리 읽고 생활과 실무를 깔끔하게 정리하는 성향입니다. 완성도와 평판을 지나치게 의식하면 속으로 긴장하고 과로하기 쉽습니다.",
  "己巳": "사람과 상황의 미세한 변화를 빨리 읽고 생활과 실무를 깔끔하게 정리하는 성향입니다. 완성도와 평판을 지나치게 의식하면 속으로 긴장하고 과로하기 쉽습니다.",
  "07.庚午경오일주": "판단과 실행이 빠르고 승부가 필요한 자리에서 정면으로 밀어붙이는 성향입니다. 강한 존재감은 장점이지만, 말과 결론이 거칠어지면 충돌과 빠른 단절로 이어질 수 있습니다.",
  "경오일주庚午": "판단과 실행이 빠르고 승부가 필요한 자리에서 정면으로 밀어붙이는 성향입니다. 강한 존재감은 장점이지만, 말과 결론이 거칠어지면 충돌과 빠른 단절로 이어질 수 있습니다.",
  "경오일주": "판단과 실행이 빠르고 승부가 필요한 자리에서 정면으로 밀어붙이는 성향입니다. 강한 존재감은 장점이지만, 말과 결론이 거칠어지면 충돌과 빠른 단절로 이어질 수 있습니다.",
  "庚午경오일주": "판단과 실행이 빠르고 승부가 필요한 자리에서 정면으로 밀어붙이는 성향입니다. 강한 존재감은 장점이지만, 말과 결론이 거칠어지면 충돌과 빠른 단절로 이어질 수 있습니다.",
  "庚午": "판단과 실행이 빠르고 승부가 필요한 자리에서 정면으로 밀어붙이는 성향입니다. 강한 존재감은 장점이지만, 말과 결론이 거칠어지면 충돌과 빠른 단절로 이어질 수 있습니다.",
  "신미일주辛未": "생활 속 품질과 균형을 세심하게 다듬으며 절제된 품격을 지키는 성향입니다. 기준과 애착이 깊은 만큼 비교와 서운함을 오래 품어 관계 피로가 커질 수 있습니다.",
  "辛未": "생활 속 품질과 균형을 세심하게 다듬으며 절제된 품격을 지키는 성향입니다. 기준과 애착이 깊은 만큼 비교와 서운함을 오래 품어 관계 피로가 커질 수 있습니다.",
  "08.辛未신미일주": "생활 속 품질과 균형을 세심하게 다듬으며 절제된 품격을 지키는 성향입니다. 기준과 애착이 깊은 만큼 비교와 서운함을 오래 품어 관계 피로가 커질 수 있습니다.",
  "辛未신미일주": "생활 속 품질과 균형을 세심하게 다듬으며 절제된 품격을 지키는 성향입니다. 기준과 애착이 깊은 만큼 비교와 서운함을 오래 품어 관계 피로가 커질 수 있습니다.",
  "신미일주": "생활 속 품질과 균형을 세심하게 다듬으며 절제된 품격을 지키는 성향입니다. 기준과 애착이 깊은 만큼 비교와 서운함을 오래 품어 관계 피로가 커질 수 있습니다.",
  "임신일주壬申": "정보와 기회를 빠르게 포착하고 변화하는 환경에 전략적으로 적응하는 성향입니다. 자유와 새로움을 좇다가 집중이 흩어지거나 필요할 때 갑자기 관계와 일을 철수할 수 있습니다.",
  "임신일주": "정보와 기회를 빠르게 포착하고 변화하는 환경에 전략적으로 적응하는 성향입니다. 자유와 새로움을 좇다가 집중이 흩어지거나 필요할 때 갑자기 관계와 일을 철수할 수 있습니다.",
  "壬申": "정보와 기회를 빠르게 포착하고 변화하는 환경에 전략적으로 적응하는 성향입니다. 자유와 새로움을 좇다가 집중이 흩어지거나 필요할 때 갑자기 관계와 일을 철수할 수 있습니다.",
  "09.壬申임신일주": "정보와 기회를 빠르게 포착하고 변화하는 환경에 전략적으로 적응하는 성향입니다. 자유와 새로움을 좇다가 집중이 흩어지거나 필요할 때 갑자기 관계와 일을 철수할 수 있습니다.",
  "壬申임신일주": "정보와 기회를 빠르게 포착하고 변화하는 환경에 전략적으로 적응하는 성향입니다. 자유와 새로움을 좇다가 집중이 흩어지거나 필요할 때 갑자기 관계와 일을 철수할 수 있습니다.",
  "10.癸酉계유일주": "이미지와 말의 완성도를 세밀하게 조정하며 사람과 사물을 정확히 선별하는 성향입니다. 비교와 의심이 심해지면 감정을 차갑게 처리하고 혼자 분석하다 지치기 쉽습니다.",
  "癸酉": "이미지와 말의 완성도를 세밀하게 조정하며 사람과 사물을 정확히 선별하는 성향입니다. 비교와 의심이 심해지면 감정을 차갑게 처리하고 혼자 분석하다 지치기 쉽습니다.",
  "계유일주癸酉": "이미지와 말의 완성도를 세밀하게 조정하며 사람과 사물을 정확히 선별하는 성향입니다. 비교와 의심이 심해지면 감정을 차갑게 처리하고 혼자 분석하다 지치기 쉽습니다.",
  "癸酉계유일주": "이미지와 말의 완성도를 세밀하게 조정하며 사람과 사물을 정확히 선별하는 성향입니다. 비교와 의심이 심해지면 감정을 차갑게 처리하고 혼자 분석하다 지치기 쉽습니다.",
  "계유일주": "이미지와 말의 완성도를 세밀하게 조정하며 사람과 사물을 정확히 선별하는 성향입니다. 비교와 의심이 심해지면 감정을 차갑게 처리하고 혼자 분석하다 지치기 쉽습니다.",
  "11.甲戌갑술일주": "원칙과 명예를 중심으로 사람과 조직을 보호하며 장기 책임을 맡는 성향입니다. 불합리함을 오래 기억하면 자기 정당화와 분노가 굳어 관계를 단호하게 끊을 수 있습니다.",
  "甲戌갑술일주": "원칙과 명예를 중심으로 사람과 조직을 보호하며 장기 책임을 맡는 성향입니다. 불합리함을 오래 기억하면 자기 정당화와 분노가 굳어 관계를 단호하게 끊을 수 있습니다.",
  "갑술일주甲戌": "원칙과 명예를 중심으로 사람과 조직을 보호하며 장기 책임을 맡는 성향입니다. 불합리함을 오래 기억하면 자기 정당화와 분노가 굳어 관계를 단호하게 끊을 수 있습니다.",
  "갑술일주": "원칙과 명예를 중심으로 사람과 조직을 보호하며 장기 책임을 맡는 성향입니다. 불합리함을 오래 기억하면 자기 정당화와 분노가 굳어 관계를 단호하게 끊을 수 있습니다.",
  "甲戌": "원칙과 명예를 중심으로 사람과 조직을 보호하며 장기 책임을 맡는 성향입니다. 불합리함을 오래 기억하면 자기 정당화와 분노가 굳어 관계를 단호하게 끊을 수 있습니다.",
  "乙亥": "사람의 감정과 보이지 않는 분위기를 부드럽게 흡수해 상상과 공감으로 풀어내는 성향입니다. 경계가 약해지면 상처와 의존을 품은 채 현실의 갈등을 피하려 할 수 있습니다.",
  "을해일주乙亥": "사람의 감정과 보이지 않는 분위기를 부드럽게 흡수해 상상과 공감으로 풀어내는 성향입니다. 경계가 약해지면 상처와 의존을 품은 채 현실의 갈등을 피하려 할 수 있습니다.",
  "乙亥을해일주": "사람의 감정과 보이지 않는 분위기를 부드럽게 흡수해 상상과 공감으로 풀어내는 성향입니다. 경계가 약해지면 상처와 의존을 품은 채 현실의 갈등을 피하려 할 수 있습니다.",
  "12.乙亥을해일주": "사람의 감정과 보이지 않는 분위기를 부드럽게 흡수해 상상과 공감으로 풀어내는 성향입니다. 경계가 약해지면 상처와 의존을 품은 채 현실의 갈등을 피하려 할 수 있습니다.",
  "을해일주": "사람의 감정과 보이지 않는 분위기를 부드럽게 흡수해 상상과 공감으로 풀어내는 성향입니다. 경계가 약해지면 상처와 의존을 품은 채 현실의 갈등을 피하려 할 수 있습니다.",
  "13.丙子병자일주": "밝은 말재치와 이미지 감각으로 긴장된 분위기를 빠르게 전환하는 성향입니다. 겉의 활기와 속의 불안 차이가 커지면 관계에서 밀고 당기거나 갑자기 차가워질 수 있습니다.",
  "丙子": "밝은 말재치와 이미지 감각으로 긴장된 분위기를 빠르게 전환하는 성향입니다. 겉의 활기와 속의 불안 차이가 커지면 관계에서 밀고 당기거나 갑자기 차가워질 수 있습니다.",
  "병자일주丙子": "밝은 말재치와 이미지 감각으로 긴장된 분위기를 빠르게 전환하는 성향입니다. 겉의 활기와 속의 불안 차이가 커지면 관계에서 밀고 당기거나 갑자기 차가워질 수 있습니다.",
  "丙子병자일주": "밝은 말재치와 이미지 감각으로 긴장된 분위기를 빠르게 전환하는 성향입니다. 겉의 활기와 속의 불안 차이가 커지면 관계에서 밀고 당기거나 갑자기 차가워질 수 있습니다.",
  "병자일주": "밝은 말재치와 이미지 감각으로 긴장된 분위기를 빠르게 전환하는 성향입니다. 겉의 활기와 속의 불안 차이가 커지면 관계에서 밀고 당기거나 갑자기 차가워질 수 있습니다.",
  "정축일주丁丑": "작은 일에도 정성과 기술을 쌓아 말보다 행동으로 신뢰를 보여 주는 성향입니다. 감정 표현이 늦고 걱정을 오래 품으면 참는 습관과 보수적인 애정 방식이 굳을 수 있습니다.",
  "丁丑": "작은 일에도 정성과 기술을 쌓아 말보다 행동으로 신뢰를 보여 주는 성향입니다. 감정 표현이 늦고 걱정을 오래 품으면 참는 습관과 보수적인 애정 방식이 굳을 수 있습니다.",
  "丁丑정축일주": "작은 일에도 정성과 기술을 쌓아 말보다 행동으로 신뢰를 보여 주는 성향입니다. 감정 표현이 늦고 걱정을 오래 품으면 참는 습관과 보수적인 애정 방식이 굳을 수 있습니다.",
  "정축일주": "작은 일에도 정성과 기술을 쌓아 말보다 행동으로 신뢰를 보여 주는 성향입니다. 감정 표현이 늦고 걱정을 오래 품으면 참는 습관과 보수적인 애정 방식이 굳을 수 있습니다.",
  "14.丁丑정축일주": "작은 일에도 정성과 기술을 쌓아 말보다 행동으로 신뢰를 보여 주는 성향입니다. 감정 표현이 늦고 걱정을 오래 품으면 참는 습관과 보수적인 애정 방식이 굳을 수 있습니다.",
  "戊寅무인일주": "큰 목표를 잡으면 넓게 움직이며 사람과 자원을 이끄는 개척형 성향입니다. 확장과 책임을 한꺼번에 떠안으면 약속이 커지고 멈추지 못해 자신과 주변을 압박할 수 있습니다.",
  "무인일주": "큰 목표를 잡으면 넓게 움직이며 사람과 자원을 이끄는 개척형 성향입니다. 확장과 책임을 한꺼번에 떠안으면 약속이 커지고 멈추지 못해 자신과 주변을 압박할 수 있습니다.",
  "戊寅": "큰 목표를 잡으면 넓게 움직이며 사람과 자원을 이끄는 개척형 성향입니다. 확장과 책임을 한꺼번에 떠안으면 약속이 커지고 멈추지 못해 자신과 주변을 압박할 수 있습니다.",
  "무인일주戊寅": "큰 목표를 잡으면 넓게 움직이며 사람과 자원을 이끄는 개척형 성향입니다. 확장과 책임을 한꺼번에 떠안으면 약속이 커지고 멈추지 못해 자신과 주변을 압박할 수 있습니다.",
  "15.戊寅무인일주": "큰 목표를 잡으면 넓게 움직이며 사람과 자원을 이끄는 개척형 성향입니다. 확장과 책임을 한꺼번에 떠안으면 약속이 커지고 멈추지 못해 자신과 주변을 압박할 수 있습니다.",
  "己卯": "상대의 반응과 생활의 세부를 살피며 부드럽고 실용적인 방식으로 돕는 성향입니다. 좋은 사람으로 보이려다 거절과 경계가 늦어지면 감정 노동과 관계 피로가 쌓일 수 있습니다.",
  "己卯기묘일주": "상대의 반응과 생활의 세부를 살피며 부드럽고 실용적인 방식으로 돕는 성향입니다. 좋은 사람으로 보이려다 거절과 경계가 늦어지면 감정 노동과 관계 피로가 쌓일 수 있습니다.",
  "기묘일주": "상대의 반응과 생활의 세부를 살피며 부드럽고 실용적인 방식으로 돕는 성향입니다. 좋은 사람으로 보이려다 거절과 경계가 늦어지면 감정 노동과 관계 피로가 쌓일 수 있습니다.",
  "기묘일주己卯": "상대의 반응과 생활의 세부를 살피며 부드럽고 실용적인 방식으로 돕는 성향입니다. 좋은 사람으로 보이려다 거절과 경계가 늦어지면 감정 노동과 관계 피로가 쌓일 수 있습니다.",
  "16.己卯기묘일주": "상대의 반응과 생활의 세부를 살피며 부드럽고 실용적인 방식으로 돕는 성향입니다. 좋은 사람으로 보이려다 거절과 경계가 늦어지면 감정 노동과 관계 피로가 쌓일 수 있습니다.",
  "경진일주庚辰": "복잡한 문제의 구조를 파악하고 불필요한 부분을 잘라 현실적인 체계로 고치는 성향입니다. 압박과 불신을 오래 저장하면 갑작스러운 결단과 완고한 기준으로 나타날 수 있습니다.",
  "경진일주": "복잡한 문제의 구조를 파악하고 불필요한 부분을 잘라 현실적인 체계로 고치는 성향입니다. 압박과 불신을 오래 저장하면 갑작스러운 결단과 완고한 기준으로 나타날 수 있습니다.",
  "17.庚辰경진일주": "복잡한 문제의 구조를 파악하고 불필요한 부분을 잘라 현실적인 체계로 고치는 성향입니다. 압박과 불신을 오래 저장하면 갑작스러운 결단과 완고한 기준으로 나타날 수 있습니다.",
  "庚辰경진일주": "복잡한 문제의 구조를 파악하고 불필요한 부분을 잘라 현실적인 체계로 고치는 성향입니다. 압박과 불신을 오래 저장하면 갑작스러운 결단과 완고한 기준으로 나타날 수 있습니다.",
  "庚辰": "복잡한 문제의 구조를 파악하고 불필요한 부분을 잘라 현실적인 체계로 고치는 성향입니다. 압박과 불신을 오래 저장하면 갑작스러운 결단과 완고한 기준으로 나타날 수 있습니다.",
  "18.辛巳신사일주": "세련된 이미지와 날카로운 표현을 결합해 사람의 시선을 끌고 품질을 선별하는 성향입니다. 비교와 수치심이 커지면 자기 편집과 비판이 지나쳐 관계와 자기관리에 무리가 갈 수 있습니다.",
  "辛巳신사일주": "세련된 이미지와 날카로운 표현을 결합해 사람의 시선을 끌고 품질을 선별하는 성향입니다. 비교와 수치심이 커지면 자기 편집과 비판이 지나쳐 관계와 자기관리에 무리가 갈 수 있습니다.",
  "신사일주": "세련된 이미지와 날카로운 표현을 결합해 사람의 시선을 끌고 품질을 선별하는 성향입니다. 비교와 수치심이 커지면 자기 편집과 비판이 지나쳐 관계와 자기관리에 무리가 갈 수 있습니다.",
  "辛巳": "세련된 이미지와 날카로운 표현을 결합해 사람의 시선을 끌고 품질을 선별하는 성향입니다. 비교와 수치심이 커지면 자기 편집과 비판이 지나쳐 관계와 자기관리에 무리가 갈 수 있습니다.",
  "신사일주辛巳": "세련된 이미지와 날카로운 표현을 결합해 사람의 시선을 끌고 품질을 선별하는 성향입니다. 비교와 수치심이 커지면 자기 편집과 비판이 지나쳐 관계와 자기관리에 무리가 갈 수 있습니다.",
  "임오일주壬午": "사람과 현장을 넓게 움직이며 열정적인 말과 친화력으로 분위기를 끌어올리는 성향입니다. 기분과 욕망이 앞서면 즉흥적 선택이 늘고, 열기가 식은 뒤 급격히 거리를 둘 수 있습니다.",
  "임오일주": "사람과 현장을 넓게 움직이며 열정적인 말과 친화력으로 분위기를 끌어올리는 성향입니다. 기분과 욕망이 앞서면 즉흥적 선택이 늘고, 열기가 식은 뒤 급격히 거리를 둘 수 있습니다.",
  "壬午임오일주": "사람과 현장을 넓게 움직이며 열정적인 말과 친화력으로 분위기를 끌어올리는 성향입니다. 기분과 욕망이 앞서면 즉흥적 선택이 늘고, 열기가 식은 뒤 급격히 거리를 둘 수 있습니다.",
  "19.壬午임오일주": "사람과 현장을 넓게 움직이며 열정적인 말과 친화력으로 분위기를 끌어올리는 성향입니다. 기분과 욕망이 앞서면 즉흥적 선택이 늘고, 열기가 식은 뒤 급격히 거리를 둘 수 있습니다.",
  "壬午": "사람과 현장을 넓게 움직이며 열정적인 말과 친화력으로 분위기를 끌어올리는 성향입니다. 기분과 욕망이 앞서면 즉흥적 선택이 늘고, 열기가 식은 뒤 급격히 거리를 둘 수 있습니다.",
  "20.癸未계미일주": "상대의 마음과 생활의 필요를 섬세하게 읽고 작은 정성으로 돌보는 성향입니다. 말하지 못한 서운함과 가족 의무가 쌓이면 경계가 흐려지고 조용한 저항으로 나타날 수 있습니다.",
  "계미일주": "상대의 마음과 생활의 필요를 섬세하게 읽고 작은 정성으로 돌보는 성향입니다. 말하지 못한 서운함과 가족 의무가 쌓이면 경계가 흐려지고 조용한 저항으로 나타날 수 있습니다.",
  "癸未계미일주": "상대의 마음과 생활의 필요를 섬세하게 읽고 작은 정성으로 돌보는 성향입니다. 말하지 못한 서운함과 가족 의무가 쌓이면 경계가 흐려지고 조용한 저항으로 나타날 수 있습니다.",
  "계미일주癸未": "상대의 마음과 생활의 필요를 섬세하게 읽고 작은 정성으로 돌보는 성향입니다. 말하지 못한 서운함과 가족 의무가 쌓이면 경계가 흐려지고 조용한 저항으로 나타날 수 있습니다.",
  "癸未": "상대의 마음과 생활의 필요를 섬세하게 읽고 작은 정성으로 돌보는 성향입니다. 말하지 못한 서운함과 가족 의무가 쌓이면 경계가 흐려지고 조용한 저항으로 나타날 수 있습니다.",
  "21.甲申갑신일주": "새로운 판을 읽는 속도가 빠르고 명분과 실리를 함께 계산해 전략적으로 움직이는 성향입니다. 경쟁과 변화가 과해지면 권위와 충돌하거나 방향을 갑자기 바꿀 수 있습니다.",
  "갑신일주": "새로운 판을 읽는 속도가 빠르고 명분과 실리를 함께 계산해 전략적으로 움직이는 성향입니다. 경쟁과 변화가 과해지면 권위와 충돌하거나 방향을 갑자기 바꿀 수 있습니다.",
  "甲申": "새로운 판을 읽는 속도가 빠르고 명분과 실리를 함께 계산해 전략적으로 움직이는 성향입니다. 경쟁과 변화가 과해지면 권위와 충돌하거나 방향을 갑자기 바꿀 수 있습니다.",
  "갑신일주甲申": "새로운 판을 읽는 속도가 빠르고 명분과 실리를 함께 계산해 전략적으로 움직이는 성향입니다. 경쟁과 변화가 과해지면 권위와 충돌하거나 방향을 갑자기 바꿀 수 있습니다.",
  "甲申갑신일주": "새로운 판을 읽는 속도가 빠르고 명분과 실리를 함께 계산해 전략적으로 움직이는 성향입니다. 경쟁과 변화가 과해지면 권위와 충돌하거나 방향을 갑자기 바꿀 수 있습니다.",
  "乙酉": "외형과 말투, 관계의 온도를 정교하게 다듬어 세련된 인상을 만드는 성향입니다. 비교와 질투를 속으로 품으면 상처받은 자존심이 관계 선별과 친밀감 피로로 이어질 수 있습니다.",
  "을유일주": "외형과 말투, 관계의 온도를 정교하게 다듬어 세련된 인상을 만드는 성향입니다. 비교와 질투를 속으로 품으면 상처받은 자존심이 관계 선별과 친밀감 피로로 이어질 수 있습니다.",
  "乙酉을유일주": "외형과 말투, 관계의 온도를 정교하게 다듬어 세련된 인상을 만드는 성향입니다. 비교와 질투를 속으로 품으면 상처받은 자존심이 관계 선별과 친밀감 피로로 이어질 수 있습니다.",
  "22.乙酉을유일주": "외형과 말투, 관계의 온도를 정교하게 다듬어 세련된 인상을 만드는 성향입니다. 비교와 질투를 속으로 품으면 상처받은 자존심이 관계 선별과 친밀감 피로로 이어질 수 있습니다.",
  "을유일주乙酉": "외형과 말투, 관계의 온도를 정교하게 다듬어 세련된 인상을 만드는 성향입니다. 비교와 질투를 속으로 품으면 상처받은 자존심이 관계 선별과 친밀감 피로로 이어질 수 있습니다.",
  "丙戌병술일주": "책임과 명예를 공개적으로 드러내며 사람과 조직을 보호하는 역할에 힘이 실리는 성향입니다. 인정과 체면을 과하게 짊어지면 고집과 분노, 리더 역할의 피로가 오래 남을 수 있습니다.",
  "병술일주丙戌": "책임과 명예를 공개적으로 드러내며 사람과 조직을 보호하는 역할에 힘이 실리는 성향입니다. 인정과 체면을 과하게 짊어지면 고집과 분노, 리더 역할의 피로가 오래 남을 수 있습니다.",
  "병술일주": "책임과 명예를 공개적으로 드러내며 사람과 조직을 보호하는 역할에 힘이 실리는 성향입니다. 인정과 체면을 과하게 짊어지면 고집과 분노, 리더 역할의 피로가 오래 남을 수 있습니다.",
  "丙戌": "책임과 명예를 공개적으로 드러내며 사람과 조직을 보호하는 역할에 힘이 실리는 성향입니다. 인정과 체면을 과하게 짊어지면 고집과 분노, 리더 역할의 피로가 오래 남을 수 있습니다.",
  "23.丙戌병술일주": "책임과 명예를 공개적으로 드러내며 사람과 조직을 보호하는 역할에 힘이 실리는 성향입니다. 인정과 체면을 과하게 짊어지면 고집과 분노, 리더 역할의 피로가 오래 남을 수 있습니다.",
  "정해일주丁亥": "깊은 감정과 직관을 시적이고 섬세한 표현으로 바꾸는 내면형 성향입니다. 상처를 받으면 감정을 안개처럼 품고 혼자 물러나 관계의 불안을 오래 끌 수 있습니다.",
  "丁亥정해일주": "깊은 감정과 직관을 시적이고 섬세한 표현으로 바꾸는 내면형 성향입니다. 상처를 받으면 감정을 안개처럼 품고 혼자 물러나 관계의 불안을 오래 끌 수 있습니다.",
  "丁亥": "깊은 감정과 직관을 시적이고 섬세한 표현으로 바꾸는 내면형 성향입니다. 상처를 받으면 감정을 안개처럼 품고 혼자 물러나 관계의 불안을 오래 끌 수 있습니다.",
  "24.丁亥정해일주": "깊은 감정과 직관을 시적이고 섬세한 표현으로 바꾸는 내면형 성향입니다. 상처를 받으면 감정을 안개처럼 품고 혼자 물러나 관계의 불안을 오래 끌 수 있습니다.",
  "정해일주": "깊은 감정과 직관을 시적이고 섬세한 표현으로 바꾸는 내면형 성향입니다. 상처를 받으면 감정을 안개처럼 품고 혼자 물러나 관계의 불안을 오래 끌 수 있습니다.",
  "戊子무자일주": "돈과 자원의 흐름을 현실적으로 계산하며 위험을 줄이고 자기 기반을 지키는 성향입니다. 불안과 통제 욕구가 커지면 속마음을 숨기고 가까운 관계까지 감시하듯 살필 수 있습니다.",
  "무자일주戊子": "돈과 자원의 흐름을 현실적으로 계산하며 위험을 줄이고 자기 기반을 지키는 성향입니다. 불안과 통제 욕구가 커지면 속마음을 숨기고 가까운 관계까지 감시하듯 살필 수 있습니다.",
  "25.戊子무자일주": "돈과 자원의 흐름을 현실적으로 계산하며 위험을 줄이고 자기 기반을 지키는 성향입니다. 불안과 통제 욕구가 커지면 속마음을 숨기고 가까운 관계까지 감시하듯 살필 수 있습니다.",
  "무자일주": "돈과 자원의 흐름을 현실적으로 계산하며 위험을 줄이고 자기 기반을 지키는 성향입니다. 불안과 통제 욕구가 커지면 속마음을 숨기고 가까운 관계까지 감시하듯 살필 수 있습니다.",
  "戊子": "돈과 자원의 흐름을 현실적으로 계산하며 위험을 줄이고 자기 기반을 지키는 성향입니다. 불안과 통제 욕구가 커지면 속마음을 숨기고 가까운 관계까지 감시하듯 살필 수 있습니다.",
  "己丑기축일주": "생활과 자산을 꾸준히 관리하며 작은 축적을 오래 이어 가는 안정형 성향입니다. 책임과 감정을 혼자 저장하면 변화가 늦어지고 오래 참은 부담이 한꺼번에 드러날 수 있습니다.",
  "기축일주己丑": "생활과 자산을 꾸준히 관리하며 작은 축적을 오래 이어 가는 안정형 성향입니다. 책임과 감정을 혼자 저장하면 변화가 늦어지고 오래 참은 부담이 한꺼번에 드러날 수 있습니다.",
  "기축일주": "생활과 자산을 꾸준히 관리하며 작은 축적을 오래 이어 가는 안정형 성향입니다. 책임과 감정을 혼자 저장하면 변화가 늦어지고 오래 참은 부담이 한꺼번에 드러날 수 있습니다.",
  "己丑": "생활과 자산을 꾸준히 관리하며 작은 축적을 오래 이어 가는 안정형 성향입니다. 책임과 감정을 혼자 저장하면 변화가 늦어지고 오래 참은 부담이 한꺼번에 드러날 수 있습니다.",
  "26.己丑기축일주": "생활과 자산을 꾸준히 관리하며 작은 축적을 오래 이어 가는 안정형 성향입니다. 책임과 감정을 혼자 저장하면 변화가 늦어지고 오래 참은 부담이 한꺼번에 드러날 수 있습니다.",
  "경인일주庚寅": "새로운 문제에 몸부터 던져 길을 만들고 불편한 구조를 과감히 고치는 성향입니다. 정의감과 승부욕이 앞서면 위험을 크게 감수하거나 권위와 거칠게 충돌할 수 있습니다.",
  "27.庚寅경인일주": "새로운 문제에 몸부터 던져 길을 만들고 불편한 구조를 과감히 고치는 성향입니다. 정의감과 승부욕이 앞서면 위험을 크게 감수하거나 권위와 거칠게 충돌할 수 있습니다.",
  "경인일주": "새로운 문제에 몸부터 던져 길을 만들고 불편한 구조를 과감히 고치는 성향입니다. 정의감과 승부욕이 앞서면 위험을 크게 감수하거나 권위와 거칠게 충돌할 수 있습니다.",
  "庚寅": "새로운 문제에 몸부터 던져 길을 만들고 불편한 구조를 과감히 고치는 성향입니다. 정의감과 승부욕이 앞서면 위험을 크게 감수하거나 권위와 거칠게 충돌할 수 있습니다.",
  "庚寅경인일주": "새로운 문제에 몸부터 던져 길을 만들고 불편한 구조를 과감히 고치는 성향입니다. 정의감과 승부욕이 앞서면 위험을 크게 감수하거나 권위와 거칠게 충돌할 수 있습니다.",
  "신묘일주辛卯": "말과 이미지의 미세한 균형을 읽고 우아하고 정제된 방식으로 자신을 표현하는 성향입니다. 승인과 비교에 민감해지면 작은 흠도 크게 느끼며 관계와 사회적 노출에 쉽게 지칠 수 있습니다.",
  "辛卯신묘일주": "말과 이미지의 미세한 균형을 읽고 우아하고 정제된 방식으로 자신을 표현하는 성향입니다. 승인과 비교에 민감해지면 작은 흠도 크게 느끼며 관계와 사회적 노출에 쉽게 지칠 수 있습니다.",
  "辛卯": "말과 이미지의 미세한 균형을 읽고 우아하고 정제된 방식으로 자신을 표현하는 성향입니다. 승인과 비교에 민감해지면 작은 흠도 크게 느끼며 관계와 사회적 노출에 쉽게 지칠 수 있습니다.",
  "28.辛卯신묘일주": "말과 이미지의 미세한 균형을 읽고 우아하고 정제된 방식으로 자신을 표현하는 성향입니다. 승인과 비교에 민감해지면 작은 흠도 크게 느끼며 관계와 사회적 노출에 쉽게 지칠 수 있습니다.",
  "신묘일주": "말과 이미지의 미세한 균형을 읽고 우아하고 정제된 방식으로 자신을 표현하는 성향입니다. 승인과 비교에 민감해지면 작은 흠도 크게 느끼며 관계와 사회적 노출에 쉽게 지칠 수 있습니다.",
  "壬辰": "많은 정보와 사람을 연결해 복잡한 문제를 장기 전략으로 풀어내는 성향입니다. 가능성을 넓게 보다가 생각과 자료가 과해지면 결정을 미루고 속마음을 보류할 수 있습니다.",
  "임진일주": "많은 정보와 사람을 연결해 복잡한 문제를 장기 전략으로 풀어내는 성향입니다. 가능성을 넓게 보다가 생각과 자료가 과해지면 결정을 미루고 속마음을 보류할 수 있습니다.",
  "壬辰임진일주": "많은 정보와 사람을 연결해 복잡한 문제를 장기 전략으로 풀어내는 성향입니다. 가능성을 넓게 보다가 생각과 자료가 과해지면 결정을 미루고 속마음을 보류할 수 있습니다.",
  "임진일주壬辰": "많은 정보와 사람을 연결해 복잡한 문제를 장기 전략으로 풀어내는 성향입니다. 가능성을 넓게 보다가 생각과 자료가 과해지면 결정을 미루고 속마음을 보류할 수 있습니다.",
  "29.壬辰임진일주": "많은 정보와 사람을 연결해 복잡한 문제를 장기 전략으로 풀어내는 성향입니다. 가능성을 넓게 보다가 생각과 자료가 과해지면 결정을 미루고 속마음을 보류할 수 있습니다.",
  "癸巳": "사람의 반응과 위험 신호를 빠르게 읽고 말과 이미지로 세련되게 대응하는 성향입니다. 긴장과 의심이 높아지면 질투와 과잉 분석이 쌓이고 관계에서 갑자기 냉각될 수 있습니다.",
  "30.癸巳계사일주": "사람의 반응과 위험 신호를 빠르게 읽고 말과 이미지로 세련되게 대응하는 성향입니다. 긴장과 의심이 높아지면 질투와 과잉 분석이 쌓이고 관계에서 갑자기 냉각될 수 있습니다.",
  "계사일주": "사람의 반응과 위험 신호를 빠르게 읽고 말과 이미지로 세련되게 대응하는 성향입니다. 긴장과 의심이 높아지면 질투와 과잉 분석이 쌓이고 관계에서 갑자기 냉각될 수 있습니다.",
  "계사일주癸巳": "사람의 반응과 위험 신호를 빠르게 읽고 말과 이미지로 세련되게 대응하는 성향입니다. 긴장과 의심이 높아지면 질투와 과잉 분석이 쌓이고 관계에서 갑자기 냉각될 수 있습니다.",
  "癸巳계사일주": "사람의 반응과 위험 신호를 빠르게 읽고 말과 이미지로 세련되게 대응하는 성향입니다. 긴장과 의심이 높아지면 질투와 과잉 분석이 쌓이고 관계에서 갑자기 냉각될 수 있습니다.",
  "31.甲午갑오일주": "자신의 방향을 공개적으로 드러내고 빠르게 사람과 일을 움직이는 추진형 성향입니다. 박수와 속도에 취하면 과감한 결정이 과속으로 바뀌고 체면과 에너지를 크게 소모할 수 있습니다.",
  "갑오일주甲午": "자신의 방향을 공개적으로 드러내고 빠르게 사람과 일을 움직이는 추진형 성향입니다. 박수와 속도에 취하면 과감한 결정이 과속으로 바뀌고 체면과 에너지를 크게 소모할 수 있습니다.",
  "갑오일주": "자신의 방향을 공개적으로 드러내고 빠르게 사람과 일을 움직이는 추진형 성향입니다. 박수와 속도에 취하면 과감한 결정이 과속으로 바뀌고 체면과 에너지를 크게 소모할 수 있습니다.",
  "甲午갑오일주": "자신의 방향을 공개적으로 드러내고 빠르게 사람과 일을 움직이는 추진형 성향입니다. 박수와 속도에 취하면 과감한 결정이 과속으로 바뀌고 체면과 에너지를 크게 소모할 수 있습니다.",
  "甲午": "자신의 방향을 공개적으로 드러내고 빠르게 사람과 일을 움직이는 추진형 성향입니다. 박수와 속도에 취하면 과감한 결정이 과속으로 바뀌고 체면과 에너지를 크게 소모할 수 있습니다.",
  "을미일주乙未": "생활 공간과 관계의 온도를 따뜻하게 다듬으며 사람을 오래 돌보는 성향입니다. 가족과 공동체에 대한 기대를 말하지 않으면 의무감과 질투, 돌봄 피로가 안에 쌓일 수 있습니다.",
  "乙未": "생활 공간과 관계의 온도를 따뜻하게 다듬으며 사람을 오래 돌보는 성향입니다. 가족과 공동체에 대한 기대를 말하지 않으면 의무감과 질투, 돌봄 피로가 안에 쌓일 수 있습니다.",
  "32.乙未을미일주": "생활 공간과 관계의 온도를 따뜻하게 다듬으며 사람을 오래 돌보는 성향입니다. 가족과 공동체에 대한 기대를 말하지 않으면 의무감과 질투, 돌봄 피로가 안에 쌓일 수 있습니다.",
  "을미일주": "생활 공간과 관계의 온도를 따뜻하게 다듬으며 사람을 오래 돌보는 성향입니다. 가족과 공동체에 대한 기대를 말하지 않으면 의무감과 질투, 돌봄 피로가 안에 쌓일 수 있습니다.",
  "乙未을미일주": "생활 공간과 관계의 온도를 따뜻하게 다듬으며 사람을 오래 돌보는 성향입니다. 가족과 공동체에 대한 기대를 말하지 않으면 의무감과 질투, 돌봄 피로가 안에 쌓일 수 있습니다.",
  "丙申병신일주": "빠른 지성과 유머, 발표 감각으로 기회와 정보를 매력적인 콘텐츠로 바꾸는 성향입니다. 흥미와 노출이 분산되면 집중력이 흔들리고 관계를 실리 위주로 대할 수 있습니다.",
  "33.丙申병신일주": "빠른 지성과 유머, 발표 감각으로 기회와 정보를 매력적인 콘텐츠로 바꾸는 성향입니다. 흥미와 노출이 분산되면 집중력이 흔들리고 관계를 실리 위주로 대할 수 있습니다.",
  "丙申": "빠른 지성과 유머, 발표 감각으로 기회와 정보를 매력적인 콘텐츠로 바꾸는 성향입니다. 흥미와 노출이 분산되면 집중력이 흔들리고 관계를 실리 위주로 대할 수 있습니다.",
  "병신일주丙申": "빠른 지성과 유머, 발표 감각으로 기회와 정보를 매력적인 콘텐츠로 바꾸는 성향입니다. 흥미와 노출이 분산되면 집중력이 흔들리고 관계를 실리 위주로 대할 수 있습니다.",
  "병신일주": "빠른 지성과 유머, 발표 감각으로 기회와 정보를 매력적인 콘텐츠로 바꾸는 성향입니다. 흥미와 노출이 분산되면 집중력이 흔들리고 관계를 실리 위주로 대할 수 있습니다.",
  "정유일주丁酉": "말과 이미지의 선을 정교하게 다듬어 높은 품질과 세련된 인상을 만드는 성향입니다. 완성도와 비교 기준이 지나치면 구설을 경계하며 감정과 관계를 차갑게 선별할 수 있습니다.",
  "丁酉": "말과 이미지의 선을 정교하게 다듬어 높은 품질과 세련된 인상을 만드는 성향입니다. 완성도와 비교 기준이 지나치면 구설을 경계하며 감정과 관계를 차갑게 선별할 수 있습니다.",
  "34.丁酉정유일주": "말과 이미지의 선을 정교하게 다듬어 높은 품질과 세련된 인상을 만드는 성향입니다. 완성도와 비교 기준이 지나치면 구설을 경계하며 감정과 관계를 차갑게 선별할 수 있습니다.",
  "정유일주": "말과 이미지의 선을 정교하게 다듬어 높은 품질과 세련된 인상을 만드는 성향입니다. 완성도와 비교 기준이 지나치면 구설을 경계하며 감정과 관계를 차갑게 선별할 수 있습니다.",
  "丁酉정유일주": "말과 이미지의 선을 정교하게 다듬어 높은 품질과 세련된 인상을 만드는 성향입니다. 완성도와 비교 기준이 지나치면 구설을 경계하며 감정과 관계를 차갑게 선별할 수 있습니다.",
  "戊戌무술일주": "자기 영역과 원칙을 단단히 지키며 책임과 권한을 직접 감당하려는 성향입니다. 무시와 불공정에 예민해지면 감정을 오래 쌓고 흑백 판단과 단호한 단절로 대응할 수 있습니다.",
  "무술일주戊戌": "자기 영역과 원칙을 단단히 지키며 책임과 권한을 직접 감당하려는 성향입니다. 무시와 불공정에 예민해지면 감정을 오래 쌓고 흑백 판단과 단호한 단절로 대응할 수 있습니다.",
  "35.戊戌무술일주": "자기 영역과 원칙을 단단히 지키며 책임과 권한을 직접 감당하려는 성향입니다. 무시와 불공정에 예민해지면 감정을 오래 쌓고 흑백 판단과 단호한 단절로 대응할 수 있습니다.",
  "戊戌": "자기 영역과 원칙을 단단히 지키며 책임과 권한을 직접 감당하려는 성향입니다. 무시와 불공정에 예민해지면 감정을 오래 쌓고 흑백 판단과 단호한 단절로 대응할 수 있습니다.",
  "무술일주": "자기 영역과 원칙을 단단히 지키며 책임과 권한을 직접 감당하려는 성향입니다. 무시와 불공정에 예민해지면 감정을 오래 쌓고 흑백 판단과 단호한 단절로 대응할 수 있습니다.",
  "36.己亥기해일주": "겉으로 드러내기보다 뒤에서 생활을 돕고 감정과 필요를 조용히 흡수하는 성향입니다. 돌봄과 공감이 과해지면 자기 경계가 흐려지고 혼자 물러나 피로를 정리하려 할 수 있습니다.",
  "기해일주己亥": "겉으로 드러내기보다 뒤에서 생활을 돕고 감정과 필요를 조용히 흡수하는 성향입니다. 돌봄과 공감이 과해지면 자기 경계가 흐려지고 혼자 물러나 피로를 정리하려 할 수 있습니다.",
  "己亥": "겉으로 드러내기보다 뒤에서 생활을 돕고 감정과 필요를 조용히 흡수하는 성향입니다. 돌봄과 공감이 과해지면 자기 경계가 흐려지고 혼자 물러나 피로를 정리하려 할 수 있습니다.",
  "기해일주": "겉으로 드러내기보다 뒤에서 생활을 돕고 감정과 필요를 조용히 흡수하는 성향입니다. 돌봄과 공감이 과해지면 자기 경계가 흐려지고 혼자 물러나 피로를 정리하려 할 수 있습니다.",
  "己亥기해일주": "겉으로 드러내기보다 뒤에서 생활을 돕고 감정과 필요를 조용히 흡수하는 성향입니다. 돌봄과 공감이 과해지면 자기 경계가 흐려지고 혼자 물러나 피로를 정리하려 할 수 있습니다.",
  "경자일주": "정보를 빠르게 정리해 효율적인 결론을 내리고 직접적인 말로 문제를 자르는 성향입니다. 감정을 절제한 채 속도를 높이면 차갑게 보이거나 관계를 너무 빨리 정리할 수 있습니다.",
  "경자일주庚子": "정보를 빠르게 정리해 효율적인 결론을 내리고 직접적인 말로 문제를 자르는 성향입니다. 감정을 절제한 채 속도를 높이면 차갑게 보이거나 관계를 너무 빨리 정리할 수 있습니다.",
  "37.庚子경자일주": "정보를 빠르게 정리해 효율적인 결론을 내리고 직접적인 말로 문제를 자르는 성향입니다. 감정을 절제한 채 속도를 높이면 차갑게 보이거나 관계를 너무 빨리 정리할 수 있습니다.",
  "庚子경자일주": "정보를 빠르게 정리해 효율적인 결론을 내리고 직접적인 말로 문제를 자르는 성향입니다. 감정을 절제한 채 속도를 높이면 차갑게 보이거나 관계를 너무 빨리 정리할 수 있습니다.",
  "庚子": "정보를 빠르게 정리해 효율적인 결론을 내리고 직접적인 말로 문제를 자르는 성향입니다. 감정을 절제한 채 속도를 높이면 차갑게 보이거나 관계를 너무 빨리 정리할 수 있습니다.",
  "辛丑신축일주": "시간을 들여 품질과 자산을 정교하게 지키며 오래 쓸 수 있는 결과를 만드는 성향입니다. 작은 손상과 서운함을 저장하면 기준이 굳고 자신과 주변을 지나치게 평가할 수 있습니다.",
  "辛丑": "시간을 들여 품질과 자산을 정교하게 지키며 오래 쓸 수 있는 결과를 만드는 성향입니다. 작은 손상과 서운함을 저장하면 기준이 굳고 자신과 주변을 지나치게 평가할 수 있습니다.",
  "신축일주辛丑": "시간을 들여 품질과 자산을 정교하게 지키며 오래 쓸 수 있는 결과를 만드는 성향입니다. 작은 손상과 서운함을 저장하면 기준이 굳고 자신과 주변을 지나치게 평가할 수 있습니다.",
  "38.辛丑신축일주": "시간을 들여 품질과 자산을 정교하게 지키며 오래 쓸 수 있는 결과를 만드는 성향입니다. 작은 손상과 서운함을 저장하면 기준이 굳고 자신과 주변을 지나치게 평가할 수 있습니다.",
  "신축일주": "시간을 들여 품질과 자산을 정교하게 지키며 오래 쓸 수 있는 결과를 만드는 성향입니다. 작은 손상과 서운함을 저장하면 기준이 굳고 자신과 주변을 지나치게 평가할 수 있습니다.",
  "39.壬寅임인일주": "사람과 정보, 장소를 넓게 연결하며 큰 미래 가능성을 찾아 움직이는 확장형 성향입니다. 새 출발이 많아지면 마무리가 흔들리고 자유를 지키려다 안정된 기반을 놓칠 수 있습니다.",
  "壬寅임인일주": "사람과 정보, 장소를 넓게 연결하며 큰 미래 가능성을 찾아 움직이는 확장형 성향입니다. 새 출발이 많아지면 마무리가 흔들리고 자유를 지키려다 안정된 기반을 놓칠 수 있습니다.",
  "壬寅": "사람과 정보, 장소를 넓게 연결하며 큰 미래 가능성을 찾아 움직이는 확장형 성향입니다. 새 출발이 많아지면 마무리가 흔들리고 자유를 지키려다 안정된 기반을 놓칠 수 있습니다.",
  "임인일주壬寅": "사람과 정보, 장소를 넓게 연결하며 큰 미래 가능성을 찾아 움직이는 확장형 성향입니다. 새 출발이 많아지면 마무리가 흔들리고 자유를 지키려다 안정된 기반을 놓칠 수 있습니다.",
  "임인일주": "사람과 정보, 장소를 넓게 연결하며 큰 미래 가능성을 찾아 움직이는 확장형 성향입니다. 새 출발이 많아지면 마무리가 흔들리고 자유를 지키려다 안정된 기반을 놓칠 수 있습니다.",
  "癸卯": "말투와 분위기를 섬세하게 읽고 글과 디자인, 공감으로 부드럽게 표현하는 성향입니다. 감정을 많이 흡수하면 갈등을 피한 채 의심과 우울감을 안에 품어 관계에서 지칠 수 있습니다.",
  "40.癸卯계묘일주": "말투와 분위기를 섬세하게 읽고 글과 디자인, 공감으로 부드럽게 표현하는 성향입니다. 감정을 많이 흡수하면 갈등을 피한 채 의심과 우울감을 안에 품어 관계에서 지칠 수 있습니다.",
  "계묘일주癸卯": "말투와 분위기를 섬세하게 읽고 글과 디자인, 공감으로 부드럽게 표현하는 성향입니다. 감정을 많이 흡수하면 갈등을 피한 채 의심과 우울감을 안에 품어 관계에서 지칠 수 있습니다.",
  "계묘일주": "말투와 분위기를 섬세하게 읽고 글과 디자인, 공감으로 부드럽게 표현하는 성향입니다. 감정을 많이 흡수하면 갈등을 피한 채 의심과 우울감을 안에 품어 관계에서 지칠 수 있습니다.",
  "癸卯계묘일주": "말투와 분위기를 섬세하게 읽고 글과 디자인, 공감으로 부드럽게 표현하는 성향입니다. 감정을 많이 흡수하면 갈등을 피한 채 의심과 우울감을 안에 품어 관계에서 지칠 수 있습니다.",
  "甲辰갑진일주": "큰 방향을 현실의 기반과 장기 계획으로 연결해 천천히 확장하는 성향입니다. 오래된 과제와 책임을 안고 가다 보면 미완성에 대한 불안과 완고한 계획이 커질 수 있습니다.",
  "갑진일주": "큰 방향을 현실의 기반과 장기 계획으로 연결해 천천히 확장하는 성향입니다. 오래된 과제와 책임을 안고 가다 보면 미완성에 대한 불안과 완고한 계획이 커질 수 있습니다.",
  "갑진일주甲辰": "큰 방향을 현실의 기반과 장기 계획으로 연결해 천천히 확장하는 성향입니다. 오래된 과제와 책임을 안고 가다 보면 미완성에 대한 불안과 완고한 계획이 커질 수 있습니다.",
  "甲辰": "큰 방향을 현실의 기반과 장기 계획으로 연결해 천천히 확장하는 성향입니다. 오래된 과제와 책임을 안고 가다 보면 미완성에 대한 불안과 완고한 계획이 커질 수 있습니다.",
  "41.甲辰갑진일주": "큰 방향을 현실의 기반과 장기 계획으로 연결해 천천히 확장하는 성향입니다. 오래된 과제와 책임을 안고 가다 보면 미완성에 대한 불안과 완고한 계획이 커질 수 있습니다.",
  "을사일주乙巳": "빠른 눈치와 이미지 감각으로 사람과 상황에 맞추면서도 실리를 챙기는 성향입니다. 비교와 지위 의식이 커지면 친절이 계산적으로 보이거나 관계 운영에 지나치게 긴장할 수 있습니다.",
  "42.乙巳을사일주": "빠른 눈치와 이미지 감각으로 사람과 상황에 맞추면서도 실리를 챙기는 성향입니다. 비교와 지위 의식이 커지면 친절이 계산적으로 보이거나 관계 운영에 지나치게 긴장할 수 있습니다.",
  "을사일주": "빠른 눈치와 이미지 감각으로 사람과 상황에 맞추면서도 실리를 챙기는 성향입니다. 비교와 지위 의식이 커지면 친절이 계산적으로 보이거나 관계 운영에 지나치게 긴장할 수 있습니다.",
  "乙巳을사일주": "빠른 눈치와 이미지 감각으로 사람과 상황에 맞추면서도 실리를 챙기는 성향입니다. 비교와 지위 의식이 커지면 친절이 계산적으로 보이거나 관계 운영에 지나치게 긴장할 수 있습니다.",
  "乙巳": "빠른 눈치와 이미지 감각으로 사람과 상황에 맞추면서도 실리를 챙기는 성향입니다. 비교와 지위 의식이 커지면 친절이 계산적으로 보이거나 관계 운영에 지나치게 긴장할 수 있습니다.",
  "43.丙午병오일주": "강한 존재감과 열정으로 사람들 앞에서 분위기를 주도하고 즐거움을 확산하는 성향입니다. 인정과 감정이 과열되면 즉흥적 선택, 급한 화, 과도한 노출로 소모될 수 있습니다.",
  "丙午병오일주": "강한 존재감과 열정으로 사람들 앞에서 분위기를 주도하고 즐거움을 확산하는 성향입니다. 인정과 감정이 과열되면 즉흥적 선택, 급한 화, 과도한 노출로 소모될 수 있습니다.",
  "병오일주": "강한 존재감과 열정으로 사람들 앞에서 분위기를 주도하고 즐거움을 확산하는 성향입니다. 인정과 감정이 과열되면 즉흥적 선택, 급한 화, 과도한 노출로 소모될 수 있습니다.",
  "병오일주丙午": "강한 존재감과 열정으로 사람들 앞에서 분위기를 주도하고 즐거움을 확산하는 성향입니다. 인정과 감정이 과열되면 즉흥적 선택, 급한 화, 과도한 노출로 소모될 수 있습니다.",
  "丙午": "강한 존재감과 열정으로 사람들 앞에서 분위기를 주도하고 즐거움을 확산하는 성향입니다. 인정과 감정이 과열되면 즉흥적 선택, 급한 화, 과도한 노출로 소모될 수 있습니다.",
  "丁未정미일주": "생활의 작은 부분을 따뜻하게 다듬고 말보다 돌봄과 정성으로 애정을 표현하는 성향입니다. 책임과 애착이 쌓이면 자기희생과 관계 피로, 정리되지 않은 서운함이 남을 수 있습니다.",
  "정미일주": "생활의 작은 부분을 따뜻하게 다듬고 말보다 돌봄과 정성으로 애정을 표현하는 성향입니다. 책임과 애착이 쌓이면 자기희생과 관계 피로, 정리되지 않은 서운함이 남을 수 있습니다.",
  "丁未": "생활의 작은 부분을 따뜻하게 다듬고 말보다 돌봄과 정성으로 애정을 표현하는 성향입니다. 책임과 애착이 쌓이면 자기희생과 관계 피로, 정리되지 않은 서운함이 남을 수 있습니다.",
  "44.丁未정미일주": "생활의 작은 부분을 따뜻하게 다듬고 말보다 돌봄과 정성으로 애정을 표현하는 성향입니다. 책임과 애착이 쌓이면 자기희생과 관계 피로, 정리되지 않은 서운함이 남을 수 있습니다.",
  "정미일주丁未": "생활의 작은 부분을 따뜻하게 다듬고 말보다 돌봄과 정성으로 애정을 표현하는 성향입니다. 책임과 애착이 쌓이면 자기희생과 관계 피로, 정리되지 않은 서운함이 남을 수 있습니다.",
  "45.戊申무신일주": "기회와 자원을 빠르게 계산해 효율적인 구조와 실질적인 성과로 바꾸는 성향입니다. 권한과 결과를 지나치게 중시하면 사람을 수단처럼 보거나 관계를 갑자기 잘라낼 수 있습니다.",
  "무신일주": "기회와 자원을 빠르게 계산해 효율적인 구조와 실질적인 성과로 바꾸는 성향입니다. 권한과 결과를 지나치게 중시하면 사람을 수단처럼 보거나 관계를 갑자기 잘라낼 수 있습니다.",
  "무신일주戊申": "기회와 자원을 빠르게 계산해 효율적인 구조와 실질적인 성과로 바꾸는 성향입니다. 권한과 결과를 지나치게 중시하면 사람을 수단처럼 보거나 관계를 갑자기 잘라낼 수 있습니다.",
  "戊申무신일주": "기회와 자원을 빠르게 계산해 효율적인 구조와 실질적인 성과로 바꾸는 성향입니다. 권한과 결과를 지나치게 중시하면 사람을 수단처럼 보거나 관계를 갑자기 잘라낼 수 있습니다.",
  "戊申": "기회와 자원을 빠르게 계산해 효율적인 구조와 실질적인 성과로 바꾸는 성향입니다. 권한과 결과를 지나치게 중시하면 사람을 수단처럼 보거나 관계를 갑자기 잘라낼 수 있습니다.",
  "기유일주": "생활과 서비스의 세부를 깔끔하게 관리하며 실용적인 세련미와 신뢰를 만드는 성향입니다. 작은 오류와 비교에 민감해지면 웃으며 비판하고 속으로 피로를 쌓을 수 있습니다.",
  "己酉기유일주": "생활과 서비스의 세부를 깔끔하게 관리하며 실용적인 세련미와 신뢰를 만드는 성향입니다. 작은 오류와 비교에 민감해지면 웃으며 비판하고 속으로 피로를 쌓을 수 있습니다.",
  "己酉": "생활과 서비스의 세부를 깔끔하게 관리하며 실용적인 세련미와 신뢰를 만드는 성향입니다. 작은 오류와 비교에 민감해지면 웃으며 비판하고 속으로 피로를 쌓을 수 있습니다.",
  "기유일주己酉": "생활과 서비스의 세부를 깔끔하게 관리하며 실용적인 세련미와 신뢰를 만드는 성향입니다. 작은 오류와 비교에 민감해지면 웃으며 비판하고 속으로 피로를 쌓을 수 있습니다.",
  "46.己酉기유일주": "생활과 서비스의 세부를 깔끔하게 관리하며 실용적인 세련미와 신뢰를 만드는 성향입니다. 작은 오류와 비교에 민감해지면 웃으며 비판하고 속으로 피로를 쌓을 수 있습니다.",
  "庚戌": "강한 원칙과 의리로 자기 영역을 지키며 잘못된 구조를 직접 수정하려는 성향입니다. 책임과 분노를 오래 품으면 비판이 거칠어지고 관계를 원칙대로 끊어낼 수 있습니다.",
  "47.庚戌경술일주": "강한 원칙과 의리로 자기 영역을 지키며 잘못된 구조를 직접 수정하려는 성향입니다. 책임과 분노를 오래 품으면 비판이 거칠어지고 관계를 원칙대로 끊어낼 수 있습니다.",
  "경술일주庚戌": "강한 원칙과 의리로 자기 영역을 지키며 잘못된 구조를 직접 수정하려는 성향입니다. 책임과 분노를 오래 품으면 비판이 거칠어지고 관계를 원칙대로 끊어낼 수 있습니다.",
  "경술일주": "강한 원칙과 의리로 자기 영역을 지키며 잘못된 구조를 직접 수정하려는 성향입니다. 책임과 분노를 오래 품으면 비판이 거칠어지고 관계를 원칙대로 끊어낼 수 있습니다.",
  "庚戌경술일주": "강한 원칙과 의리로 자기 영역을 지키며 잘못된 구조를 직접 수정하려는 성향입니다. 책임과 분노를 오래 품으면 비판이 거칠어지고 관계를 원칙대로 끊어낼 수 있습니다.",
  "신해일주": "깊은 직관과 예술적 감각을 정제된 언어와 이미지로 표현하는 성향입니다. 사생활을 지키려는 마음이 강해지면 감정과 관계가 모호해지고 상상 속으로 물러날 수 있습니다.",
  "辛亥": "깊은 직관과 예술적 감각을 정제된 언어와 이미지로 표현하는 성향입니다. 사생활을 지키려는 마음이 강해지면 감정과 관계가 모호해지고 상상 속으로 물러날 수 있습니다.",
  "신해일주辛亥": "깊은 직관과 예술적 감각을 정제된 언어와 이미지로 표현하는 성향입니다. 사생활을 지키려는 마음이 강해지면 감정과 관계가 모호해지고 상상 속으로 물러날 수 있습니다.",
  "辛亥신해일주": "깊은 직관과 예술적 감각을 정제된 언어와 이미지로 표현하는 성향입니다. 사생활을 지키려는 마음이 강해지면 감정과 관계가 모호해지고 상상 속으로 물러날 수 있습니다.",
  "48.辛亥신해일주": "깊은 직관과 예술적 감각을 정제된 언어와 이미지로 표현하는 성향입니다. 사생활을 지키려는 마음이 강해지면 감정과 관계가 모호해지고 상상 속으로 물러날 수 있습니다.",
  "49.壬子임자일주": "정보와 감정을 깊고 넓게 받아들이며 상황에 따라 빠르게 흐름을 바꾸는 성향입니다. 생각과 자극이 많아지면 집중이 파도처럼 흔들리고 관계의 경계도 불분명해질 수 있습니다.",
  "임자일주壬子": "정보와 감정을 깊고 넓게 받아들이며 상황에 따라 빠르게 흐름을 바꾸는 성향입니다. 생각과 자극이 많아지면 집중이 파도처럼 흔들리고 관계의 경계도 불분명해질 수 있습니다.",
  "임자일주": "정보와 감정을 깊고 넓게 받아들이며 상황에 따라 빠르게 흐름을 바꾸는 성향입니다. 생각과 자극이 많아지면 집중이 파도처럼 흔들리고 관계의 경계도 불분명해질 수 있습니다.",
  "壬子": "정보와 감정을 깊고 넓게 받아들이며 상황에 따라 빠르게 흐름을 바꾸는 성향입니다. 생각과 자극이 많아지면 집중이 파도처럼 흔들리고 관계의 경계도 불분명해질 수 있습니다.",
  "壬子임자일주": "정보와 감정을 깊고 넓게 받아들이며 상황에 따라 빠르게 흐름을 바꾸는 성향입니다. 생각과 자극이 많아지면 집중이 파도처럼 흔들리고 관계의 경계도 불분명해질 수 있습니다.",
  "50.癸丑계축일주": "작은 변화와 대우를 오래 기억하며 안전한 생활 구조를 조용히 지키는 성향입니다. 손실을 두려워하면 결정을 늦추고 서운함과 불안을 말없이 축적할 수 있습니다.",
  "계축일주癸丑": "작은 변화와 대우를 오래 기억하며 안전한 생활 구조를 조용히 지키는 성향입니다. 손실을 두려워하면 결정을 늦추고 서운함과 불안을 말없이 축적할 수 있습니다.",
  "계축일주": "작은 변화와 대우를 오래 기억하며 안전한 생활 구조를 조용히 지키는 성향입니다. 손실을 두려워하면 결정을 늦추고 서운함과 불안을 말없이 축적할 수 있습니다.",
  "癸丑": "작은 변화와 대우를 오래 기억하며 안전한 생활 구조를 조용히 지키는 성향입니다. 손실을 두려워하면 결정을 늦추고 서운함과 불안을 말없이 축적할 수 있습니다.",
  "癸丑계축일주": "작은 변화와 대우를 오래 기억하며 안전한 생활 구조를 조용히 지키는 성향입니다. 손실을 두려워하면 결정을 늦추고 서운함과 불안을 말없이 축적할 수 있습니다.",
  "甲寅": "자기 방향을 선명하게 세우고 새로운 일을 정면으로 시작하는 순도 높은 개척형 성향입니다. 확신과 확장이 과하면 간섭을 견디지 못하고 무리한 판을 벌일 수 있습니다.",
  "51.甲寅갑인일주": "자기 방향을 선명하게 세우고 새로운 일을 정면으로 시작하는 순도 높은 개척형 성향입니다. 확신과 확장이 과하면 간섭을 견디지 못하고 무리한 판을 벌일 수 있습니다.",
  "甲寅갑인일주": "자기 방향을 선명하게 세우고 새로운 일을 정면으로 시작하는 순도 높은 개척형 성향입니다. 확신과 확장이 과하면 간섭을 견디지 못하고 무리한 판을 벌일 수 있습니다.",
  "갑인일주甲寅": "자기 방향을 선명하게 세우고 새로운 일을 정면으로 시작하는 순도 높은 개척형 성향입니다. 확신과 확장이 과하면 간섭을 견디지 못하고 무리한 판을 벌일 수 있습니다.",
  "갑인일주": "자기 방향을 선명하게 세우고 새로운 일을 정면으로 시작하는 순도 높은 개척형 성향입니다. 확신과 확장이 과하면 간섭을 견디지 못하고 무리한 판을 벌일 수 있습니다.",
  "乙卯을묘일주": "관계의 분위기와 아름다움을 자연스럽게 읽고 부드러운 설득과 매력으로 연결하는 성향입니다. 비교와 애착이 커지면 직접 말하지 못한 질투와 의존이 관계 안에 남을 수 있습니다.",
  "을묘일주": "관계의 분위기와 아름다움을 자연스럽게 읽고 부드러운 설득과 매력으로 연결하는 성향입니다. 비교와 애착이 커지면 직접 말하지 못한 질투와 의존이 관계 안에 남을 수 있습니다.",
  "乙卯": "관계의 분위기와 아름다움을 자연스럽게 읽고 부드러운 설득과 매력으로 연결하는 성향입니다. 비교와 애착이 커지면 직접 말하지 못한 질투와 의존이 관계 안에 남을 수 있습니다.",
  "을묘일주乙卯": "관계의 분위기와 아름다움을 자연스럽게 읽고 부드러운 설득과 매력으로 연결하는 성향입니다. 비교와 애착이 커지면 직접 말하지 못한 질투와 의존이 관계 안에 남을 수 있습니다.",
  "52.乙卯을묘일주": "관계의 분위기와 아름다움을 자연스럽게 읽고 부드러운 설득과 매력으로 연결하는 성향입니다. 비교와 애착이 커지면 직접 말하지 못한 질투와 의존이 관계 안에 남을 수 있습니다.",
  "병진일주丙辰": "복잡한 내용을 말과 이야기로 구조화해 사람들이 이해할 수 있는 결과물로 만드는 성향입니다. 역할과 평판을 지나치게 의식하면 설명과 책임이 늘어 관계와 실무에서 피로해질 수 있습니다.",
  "53.丙辰병진일주": "복잡한 내용을 말과 이야기로 구조화해 사람들이 이해할 수 있는 결과물로 만드는 성향입니다. 역할과 평판을 지나치게 의식하면 설명과 책임이 늘어 관계와 실무에서 피로해질 수 있습니다.",
  "丙辰병진일주": "복잡한 내용을 말과 이야기로 구조화해 사람들이 이해할 수 있는 결과물로 만드는 성향입니다. 역할과 평판을 지나치게 의식하면 설명과 책임이 늘어 관계와 실무에서 피로해질 수 있습니다.",
  "丙辰": "복잡한 내용을 말과 이야기로 구조화해 사람들이 이해할 수 있는 결과물로 만드는 성향입니다. 역할과 평판을 지나치게 의식하면 설명과 책임이 늘어 관계와 실무에서 피로해질 수 있습니다.",
  "병진일주": "복잡한 내용을 말과 이야기로 구조화해 사람들이 이해할 수 있는 결과물로 만드는 성향입니다. 역할과 평판을 지나치게 의식하면 설명과 책임이 늘어 관계와 실무에서 피로해질 수 있습니다.",
  "丁巳": "집중된 열정과 감각적 표현으로 이미지와 결과물의 완성도를 끌어올리는 성향입니다. 비교와 완벽주의가 심해지면 감정 온도차와 집착, 소진 위험이 커질 수 있습니다.",
  "정사일주": "집중된 열정과 감각적 표현으로 이미지와 결과물의 완성도를 끌어올리는 성향입니다. 비교와 완벽주의가 심해지면 감정 온도차와 집착, 소진 위험이 커질 수 있습니다.",
  "丁巳정사일주": "집중된 열정과 감각적 표현으로 이미지와 결과물의 완성도를 끌어올리는 성향입니다. 비교와 완벽주의가 심해지면 감정 온도차와 집착, 소진 위험이 커질 수 있습니다.",
  "54.丁巳정사일주": "집중된 열정과 감각적 표현으로 이미지와 결과물의 완성도를 끌어올리는 성향입니다. 비교와 완벽주의가 심해지면 감정 온도차와 집착, 소진 위험이 커질 수 있습니다.",
  "정사일주丁巳": "집중된 열정과 감각적 표현으로 이미지와 결과물의 완성도를 끌어올리는 성향입니다. 비교와 완벽주의가 심해지면 감정 온도차와 집착, 소진 위험이 커질 수 있습니다.",
  "戊午": "큰 책임과 권한을 직접 쥐고 사람과 조직을 빠르게 움직이는 강한 지도형 성향입니다. 확신과 열기가 과하면 강압적 태도와 체면 지출, 외로운 책임으로 이어질 수 있습니다.",
  "무오일주戊午": "큰 책임과 권한을 직접 쥐고 사람과 조직을 빠르게 움직이는 강한 지도형 성향입니다. 확신과 열기가 과하면 강압적 태도와 체면 지출, 외로운 책임으로 이어질 수 있습니다.",
  "戊午무오일주": "큰 책임과 권한을 직접 쥐고 사람과 조직을 빠르게 움직이는 강한 지도형 성향입니다. 확신과 열기가 과하면 강압적 태도와 체면 지출, 외로운 책임으로 이어질 수 있습니다.",
  "55.戊午무오일주": "큰 책임과 권한을 직접 쥐고 사람과 조직을 빠르게 움직이는 강한 지도형 성향입니다. 확신과 열기가 과하면 강압적 태도와 체면 지출, 외로운 책임으로 이어질 수 있습니다.",
  "무오일주": "큰 책임과 권한을 직접 쥐고 사람과 조직을 빠르게 움직이는 강한 지도형 성향입니다. 확신과 열기가 과하면 강압적 태도와 체면 지출, 외로운 책임으로 이어질 수 있습니다.",
  "56.己未기미일주": "생활과 가정의 흐름을 꾸준히 돌보며 작은 안정과 자원을 지키는 성향입니다. 책임을 말없이 떠안으면 걱정과 원망, 자기희생이 쌓여 사적인 피로가 커질 수 있습니다.",
  "기미일주": "생활과 가정의 흐름을 꾸준히 돌보며 작은 안정과 자원을 지키는 성향입니다. 책임을 말없이 떠안으면 걱정과 원망, 자기희생이 쌓여 사적인 피로가 커질 수 있습니다.",
  "己未기미일주": "생활과 가정의 흐름을 꾸준히 돌보며 작은 안정과 자원을 지키는 성향입니다. 책임을 말없이 떠안으면 걱정과 원망, 자기희생이 쌓여 사적인 피로가 커질 수 있습니다.",
  "기미일주己未": "생활과 가정의 흐름을 꾸준히 돌보며 작은 안정과 자원을 지키는 성향입니다. 책임을 말없이 떠안으면 걱정과 원망, 자기희생이 쌓여 사적인 피로가 커질 수 있습니다.",
  "己未": "생활과 가정의 흐름을 꾸준히 돌보며 작은 안정과 자원을 지키는 성향입니다. 책임을 말없이 떠안으면 걱정과 원망, 자기희생이 쌓여 사적인 피로가 커질 수 있습니다.",
  "庚申경신일주": "높은 기술력과 판단 기준으로 문제를 빠르게 해결하고 혼자서도 결과를 만드는 성향입니다. 능력과 효율을 앞세우면 말이 날카로워지고 감정 표현과 협력이 부족해질 수 있습니다.",
  "57.庚申경신일주": "높은 기술력과 판단 기준으로 문제를 빠르게 해결하고 혼자서도 결과를 만드는 성향입니다. 능력과 효율을 앞세우면 말이 날카로워지고 감정 표현과 협력이 부족해질 수 있습니다.",
  "庚申": "높은 기술력과 판단 기준으로 문제를 빠르게 해결하고 혼자서도 결과를 만드는 성향입니다. 능력과 효율을 앞세우면 말이 날카로워지고 감정 표현과 협력이 부족해질 수 있습니다.",
  "경신일주庚申": "높은 기술력과 판단 기준으로 문제를 빠르게 해결하고 혼자서도 결과를 만드는 성향입니다. 능력과 효율을 앞세우면 말이 날카로워지고 감정 표현과 협력이 부족해질 수 있습니다.",
  "경신일주": "높은 기술력과 판단 기준으로 문제를 빠르게 해결하고 혼자서도 결과를 만드는 성향입니다. 능력과 효율을 앞세우면 말이 날카로워지고 감정 표현과 협력이 부족해질 수 있습니다.",
  "58.辛酉신유일주": "미감과 품질 기준이 매우 선명해 이미지, 말, 결과물을 정교하게 다듬는 성향입니다. 비교와 완벽주의가 과해지면 구설을 경계하며 관계를 차갑게 선별하고 쉽게 지칠 수 있습니다.",
  "辛酉": "미감과 품질 기준이 매우 선명해 이미지, 말, 결과물을 정교하게 다듬는 성향입니다. 비교와 완벽주의가 과해지면 구설을 경계하며 관계를 차갑게 선별하고 쉽게 지칠 수 있습니다.",
  "신유일주": "미감과 품질 기준이 매우 선명해 이미지, 말, 결과물을 정교하게 다듬는 성향입니다. 비교와 완벽주의가 과해지면 구설을 경계하며 관계를 차갑게 선별하고 쉽게 지칠 수 있습니다.",
  "신유일주辛酉": "미감과 품질 기준이 매우 선명해 이미지, 말, 결과물을 정교하게 다듬는 성향입니다. 비교와 완벽주의가 과해지면 구설을 경계하며 관계를 차갑게 선별하고 쉽게 지칠 수 있습니다.",
  "辛酉신유일주": "미감과 품질 기준이 매우 선명해 이미지, 말, 결과물을 정교하게 다듬는 성향입니다. 비교와 완벽주의가 과해지면 구설을 경계하며 관계를 차갑게 선별하고 쉽게 지칠 수 있습니다.",
  "임술일주": "사람과 조직의 문제를 넓게 받아들이며 오래된 의리와 책임을 지키는 성향입니다. 감정과 부담을 오래 흡수하면 늦게 분노하거나 신뢰를 시험한 뒤 갑자기 철수할 수 있습니다.",
  "壬戌": "사람과 조직의 문제를 넓게 받아들이며 오래된 의리와 책임을 지키는 성향입니다. 감정과 부담을 오래 흡수하면 늦게 분노하거나 신뢰를 시험한 뒤 갑자기 철수할 수 있습니다.",
  "壬戌임술일주": "사람과 조직의 문제를 넓게 받아들이며 오래된 의리와 책임을 지키는 성향입니다. 감정과 부담을 오래 흡수하면 늦게 분노하거나 신뢰를 시험한 뒤 갑자기 철수할 수 있습니다.",
  "임술일주壬戌": "사람과 조직의 문제를 넓게 받아들이며 오래된 의리와 책임을 지키는 성향입니다. 감정과 부담을 오래 흡수하면 늦게 분노하거나 신뢰를 시험한 뒤 갑자기 철수할 수 있습니다.",
  "59.壬戌임술일주": "사람과 조직의 문제를 넓게 받아들이며 오래된 의리와 책임을 지키는 성향입니다. 감정과 부담을 오래 흡수하면 늦게 분노하거나 신뢰를 시험한 뒤 갑자기 철수할 수 있습니다.",
  "癸亥계해일주": "깊은 직관과 공감으로 사람의 감정과 보이지 않는 흐름을 섬세하게 읽는 성향입니다. 상처와 불안을 많이 흡수하면 경계가 흐려지고 현실보다 내면과 상상으로 물러날 수 있습니다.",
  "계해일주癸亥": "깊은 직관과 공감으로 사람의 감정과 보이지 않는 흐름을 섬세하게 읽는 성향입니다. 상처와 불안을 많이 흡수하면 경계가 흐려지고 현실보다 내면과 상상으로 물러날 수 있습니다.",
  "60.癸亥계해일주": "깊은 직관과 공감으로 사람의 감정과 보이지 않는 흐름을 섬세하게 읽는 성향입니다. 상처와 불안을 많이 흡수하면 경계가 흐려지고 현실보다 내면과 상상으로 물러날 수 있습니다.",
  "癸亥": "깊은 직관과 공감으로 사람의 감정과 보이지 않는 흐름을 섬세하게 읽는 성향입니다. 상처와 불안을 많이 흡수하면 경계가 흐려지고 현실보다 내면과 상상으로 물러날 수 있습니다.",
  "계해일주": "깊은 직관과 공감으로 사람의 감정과 보이지 않는 흐름을 섬세하게 읽는 성향입니다. 상처와 불안을 많이 흡수하면 경계가 흐려지고 현실보다 내면과 상상으로 물러날 수 있습니다.",
  "01.寅月인월": "새로운 가능성을 보면 먼저 방향을 세우고 빠르게 시작하려는 성향이 강해집니다. 개척과 선점에는 유리하지만, 확장 욕구가 앞서면 마무리와 현실 계산이 약해질 수 있습니다.",
  "인월寅月": "새로운 가능성을 보면 먼저 방향을 세우고 빠르게 시작하려는 성향이 강해집니다. 개척과 선점에는 유리하지만, 확장 욕구가 앞서면 마무리와 현실 계산이 약해질 수 있습니다.",
  "寅月": "새로운 가능성을 보면 먼저 방향을 세우고 빠르게 시작하려는 성향이 강해집니다. 개척과 선점에는 유리하지만, 확장 욕구가 앞서면 마무리와 현실 계산이 약해질 수 있습니다.",
  "寅月인월": "새로운 가능성을 보면 먼저 방향을 세우고 빠르게 시작하려는 성향이 강해집니다. 개척과 선점에는 유리하지만, 확장 욕구가 앞서면 마무리와 현실 계산이 약해질 수 있습니다.",
  "인월": "새로운 가능성을 보면 먼저 방향을 세우고 빠르게 시작하려는 성향이 강해집니다. 개척과 선점에는 유리하지만, 확장 욕구가 앞서면 마무리와 현실 계산이 약해질 수 있습니다.",
  "묘월": "표정과 말투, 취향의 미세한 차이를 읽어 관계와 이미지를 부드럽게 조율하는 성향이 강해집니다. 비교와 호감 관리가 과하면 질투와 관계 피로가 쌓일 수 있습니다.",
  "卯月": "표정과 말투, 취향의 미세한 차이를 읽어 관계와 이미지를 부드럽게 조율하는 성향이 강해집니다. 비교와 호감 관리가 과하면 질투와 관계 피로가 쌓일 수 있습니다.",
  "卯月묘월": "표정과 말투, 취향의 미세한 차이를 읽어 관계와 이미지를 부드럽게 조율하는 성향이 강해집니다. 비교와 호감 관리가 과하면 질투와 관계 피로가 쌓일 수 있습니다.",
  "02.卯月묘월": "표정과 말투, 취향의 미세한 차이를 읽어 관계와 이미지를 부드럽게 조율하는 성향이 강해집니다. 비교와 호감 관리가 과하면 질투와 관계 피로가 쌓일 수 있습니다.",
  "묘월卯月": "표정과 말투, 취향의 미세한 차이를 읽어 관계와 이미지를 부드럽게 조율하는 성향이 강해집니다. 비교와 호감 관리가 과하면 질투와 관계 피로가 쌓일 수 있습니다.",
  "진월辰月": "감정과 실리, 계획과 현실을 함께 보며 가능성을 오래 저장하고 전환 시점을 기다리는 성향이 강해집니다. 미련과 계산이 겹치면 결정이 늦고 묵은 문제가 반복될 수 있습니다.",
  "진월": "감정과 실리, 계획과 현실을 함께 보며 가능성을 오래 저장하고 전환 시점을 기다리는 성향이 강해집니다. 미련과 계산이 겹치면 결정이 늦고 묵은 문제가 반복될 수 있습니다.",
  "03.辰月진월": "감정과 실리, 계획과 현실을 함께 보며 가능성을 오래 저장하고 전환 시점을 기다리는 성향이 강해집니다. 미련과 계산이 겹치면 결정이 늦고 묵은 문제가 반복될 수 있습니다.",
  "辰月진월": "감정과 실리, 계획과 현실을 함께 보며 가능성을 오래 저장하고 전환 시점을 기다리는 성향이 강해집니다. 미련과 계산이 겹치면 결정이 늦고 묵은 문제가 반복될 수 있습니다.",
  "辰月": "감정과 실리, 계획과 현실을 함께 보며 가능성을 오래 저장하고 전환 시점을 기다리는 성향이 강해집니다. 미련과 계산이 겹치면 결정이 늦고 묵은 문제가 반복될 수 있습니다.",
  "사월": "긴장과 경쟁이 생길수록 집중력이 높아지고 기술·거래·이미지를 빠르게 연결하는 성향이 강해집니다. 욕망과 속도가 과열되면 신경이 예민해지고 선택 뒤 소진이 커질 수 있습니다.",
  "巳月": "긴장과 경쟁이 생길수록 집중력이 높아지고 기술·거래·이미지를 빠르게 연결하는 성향이 강해집니다. 욕망과 속도가 과열되면 신경이 예민해지고 선택 뒤 소진이 커질 수 있습니다.",
  "04.巳月사월": "긴장과 경쟁이 생길수록 집중력이 높아지고 기술·거래·이미지를 빠르게 연결하는 성향이 강해집니다. 욕망과 속도가 과열되면 신경이 예민해지고 선택 뒤 소진이 커질 수 있습니다.",
  "사월巳月": "긴장과 경쟁이 생길수록 집중력이 높아지고 기술·거래·이미지를 빠르게 연결하는 성향이 강해집니다. 욕망과 속도가 과열되면 신경이 예민해지고 선택 뒤 소진이 커질 수 있습니다.",
  "巳月사월": "긴장과 경쟁이 생길수록 집중력이 높아지고 기술·거래·이미지를 빠르게 연결하는 성향이 강해집니다. 욕망과 속도가 과열되면 신경이 예민해지고 선택 뒤 소진이 커질 수 있습니다.",
  "午月": "감정과 존재감이 밖으로 빠르게 드러나며 인정과 반응을 행동의 동력으로 삼는 성향이 강해집니다. 무시와 평가에 예민해지면 말실수, 체면 지출, 감정 폭발이 커질 수 있습니다.",
  "오월": "감정과 존재감이 밖으로 빠르게 드러나며 인정과 반응을 행동의 동력으로 삼는 성향이 강해집니다. 무시와 평가에 예민해지면 말실수, 체면 지출, 감정 폭발이 커질 수 있습니다.",
  "午月오월": "감정과 존재감이 밖으로 빠르게 드러나며 인정과 반응을 행동의 동력으로 삼는 성향이 강해집니다. 무시와 평가에 예민해지면 말실수, 체면 지출, 감정 폭발이 커질 수 있습니다.",
  "05.午月오월": "감정과 존재감이 밖으로 빠르게 드러나며 인정과 반응을 행동의 동력으로 삼는 성향이 강해집니다. 무시와 평가에 예민해지면 말실수, 체면 지출, 감정 폭발이 커질 수 있습니다.",
  "오월午月": "감정과 존재감이 밖으로 빠르게 드러나며 인정과 반응을 행동의 동력으로 삼는 성향이 강해집니다. 무시와 평가에 예민해지면 말실수, 체면 지출, 감정 폭발이 커질 수 있습니다.",
  "未月미월": "생활과 관계를 오래 돌보며 가족과 공동체 안에서 필요한 역할을 맡으려는 성향이 강해집니다. 정과 의무가 과해지면 거절이 늦고 돈과 감정이 관계에 묶일 수 있습니다.",
  "미월": "생활과 관계를 오래 돌보며 가족과 공동체 안에서 필요한 역할을 맡으려는 성향이 강해집니다. 정과 의무가 과해지면 거절이 늦고 돈과 감정이 관계에 묶일 수 있습니다.",
  "06.未月미월": "생활과 관계를 오래 돌보며 가족과 공동체 안에서 필요한 역할을 맡으려는 성향이 강해집니다. 정과 의무가 과해지면 거절이 늦고 돈과 감정이 관계에 묶일 수 있습니다.",
  "미월未月": "생활과 관계를 오래 돌보며 가족과 공동체 안에서 필요한 역할을 맡으려는 성향이 강해집니다. 정과 의무가 과해지면 거절이 늦고 돈과 감정이 관계에 묶일 수 있습니다.",
  "未月": "생활과 관계를 오래 돌보며 가족과 공동체 안에서 필요한 역할을 맡으려는 성향이 강해집니다. 정과 의무가 과해지면 거절이 늦고 돈과 감정이 관계에 묶일 수 있습니다.",
  "신월": "정보와 기회를 빠르게 처리하고 기술·거래·협상으로 실질적인 돌파구를 찾는 성향이 강해집니다. 효율만 앞세우면 검증이 짧아지고 관계와 돈의 흐름이 지나치게 빨라질 수 있습니다.",
  "신월申月": "정보와 기회를 빠르게 처리하고 기술·거래·협상으로 실질적인 돌파구를 찾는 성향이 강해집니다. 효율만 앞세우면 검증이 짧아지고 관계와 돈의 흐름이 지나치게 빨라질 수 있습니다.",
  "07.申月신월": "정보와 기회를 빠르게 처리하고 기술·거래·협상으로 실질적인 돌파구를 찾는 성향이 강해집니다. 효율만 앞세우면 검증이 짧아지고 관계와 돈의 흐름이 지나치게 빨라질 수 있습니다.",
  "申月": "정보와 기회를 빠르게 처리하고 기술·거래·협상으로 실질적인 돌파구를 찾는 성향이 강해집니다. 효율만 앞세우면 검증이 짧아지고 관계와 돈의 흐름이 지나치게 빨라질 수 있습니다.",
  "申月신월": "정보와 기회를 빠르게 처리하고 기술·거래·협상으로 실질적인 돌파구를 찾는 성향이 강해집니다. 효율만 앞세우면 검증이 짧아지고 관계와 돈의 흐름이 지나치게 빨라질 수 있습니다.",
  "酉月": "작은 차이와 값어치를 선별해 말, 이미지, 결과물의 완성도를 높이는 성향이 강해집니다. 기준과 비교가 과하면 흠집에 집착하고 관계와 자기평가에서 쉽게 지칠 수 있습니다.",
  "유월酉月": "작은 차이와 값어치를 선별해 말, 이미지, 결과물의 완성도를 높이는 성향이 강해집니다. 기준과 비교가 과하면 흠집에 집착하고 관계와 자기평가에서 쉽게 지칠 수 있습니다.",
  "유월": "작은 차이와 값어치를 선별해 말, 이미지, 결과물의 완성도를 높이는 성향이 강해집니다. 기준과 비교가 과하면 흠집에 집착하고 관계와 자기평가에서 쉽게 지칠 수 있습니다.",
  "酉月유월": "작은 차이와 값어치를 선별해 말, 이미지, 결과물의 완성도를 높이는 성향이 강해집니다. 기준과 비교가 과하면 흠집에 집착하고 관계와 자기평가에서 쉽게 지칠 수 있습니다.",
  "08.酉月유월": "작은 차이와 값어치를 선별해 말, 이미지, 결과물의 완성도를 높이는 성향이 강해집니다. 기준과 비교가 과하면 흠집에 집착하고 관계와 자기평가에서 쉽게 지칠 수 있습니다.",
  "술월": "자기 기준과 책임, 명예를 단단히 지키며 사람과 영역을 보호하려는 성향이 강해집니다. 감정과 분노를 굳히면 흑백 판단과 단호한 단절, 고립으로 이어질 수 있습니다.",
  "술월戌月": "자기 기준과 책임, 명예를 단단히 지키며 사람과 영역을 보호하려는 성향이 강해집니다. 감정과 분노를 굳히면 흑백 판단과 단호한 단절, 고립으로 이어질 수 있습니다.",
  "戌月술월": "자기 기준과 책임, 명예를 단단히 지키며 사람과 영역을 보호하려는 성향이 강해집니다. 감정과 분노를 굳히면 흑백 판단과 단호한 단절, 고립으로 이어질 수 있습니다.",
  "09.戌月술월": "자기 기준과 책임, 명예를 단단히 지키며 사람과 영역을 보호하려는 성향이 강해집니다. 감정과 분노를 굳히면 흑백 판단과 단호한 단절, 고립으로 이어질 수 있습니다.",
  "戌月": "자기 기준과 책임, 명예를 단단히 지키며 사람과 영역을 보호하려는 성향이 강해집니다. 감정과 분노를 굳히면 흑백 판단과 단호한 단절, 고립으로 이어질 수 있습니다.",
  "亥月": "직관과 상상, 의미 탐색이 깊어지며 사람과 지식을 넓게 연결하려는 성향이 강해집니다. 감정과 가능성에 몰입하면 경계가 약해지고 현실의 결정과 실행이 늦어질 수 있습니다.",
  "해월": "직관과 상상, 의미 탐색이 깊어지며 사람과 지식을 넓게 연결하려는 성향이 강해집니다. 감정과 가능성에 몰입하면 경계가 약해지고 현실의 결정과 실행이 늦어질 수 있습니다.",
  "亥月해월": "직관과 상상, 의미 탐색이 깊어지며 사람과 지식을 넓게 연결하려는 성향이 강해집니다. 감정과 가능성에 몰입하면 경계가 약해지고 현실의 결정과 실행이 늦어질 수 있습니다.",
  "10.亥月해월": "직관과 상상, 의미 탐색이 깊어지며 사람과 지식을 넓게 연결하려는 성향이 강해집니다. 감정과 가능성에 몰입하면 경계가 약해지고 현실의 결정과 실행이 늦어질 수 있습니다.",
  "해월亥月": "직관과 상상, 의미 탐색이 깊어지며 사람과 지식을 넓게 연결하려는 성향이 강해집니다. 감정과 가능성에 몰입하면 경계가 약해지고 현실의 결정과 실행이 늦어질 수 있습니다.",
  "子月자월": "감정과 정보가 안쪽으로 모이며 작은 변화와 숨은 흐름을 오래 관찰하는 성향이 강해집니다. 불안과 비밀이 늘면 결정을 미루고 관계에서 갑자기 마음을 닫을 수 있습니다.",
  "자월": "감정과 정보가 안쪽으로 모이며 작은 변화와 숨은 흐름을 오래 관찰하는 성향이 강해집니다. 불안과 비밀이 늘면 결정을 미루고 관계에서 갑자기 마음을 닫을 수 있습니다.",
  "11.子月자월": "감정과 정보가 안쪽으로 모이며 작은 변화와 숨은 흐름을 오래 관찰하는 성향이 강해집니다. 불안과 비밀이 늘면 결정을 미루고 관계에서 갑자기 마음을 닫을 수 있습니다.",
  "자월子月": "감정과 정보가 안쪽으로 모이며 작은 변화와 숨은 흐름을 오래 관찰하는 성향이 강해집니다. 불안과 비밀이 늘면 결정을 미루고 관계에서 갑자기 마음을 닫을 수 있습니다.",
  "子月": "감정과 정보가 안쪽으로 모이며 작은 변화와 숨은 흐름을 오래 관찰하는 성향이 강해집니다. 불안과 비밀이 늘면 결정을 미루고 관계에서 갑자기 마음을 닫을 수 있습니다.",
  "축월丑月": "검증된 방식과 생활 기반을 지키며 돈, 감정, 자원을 천천히 축적하는 성향이 강해집니다. 변화와 손실을 지나치게 경계하면 묵은 문제와 관계를 오래 끌 수 있습니다.",
  "丑月": "검증된 방식과 생활 기반을 지키며 돈, 감정, 자원을 천천히 축적하는 성향이 강해집니다. 변화와 손실을 지나치게 경계하면 묵은 문제와 관계를 오래 끌 수 있습니다.",
  "축월": "검증된 방식과 생활 기반을 지키며 돈, 감정, 자원을 천천히 축적하는 성향이 강해집니다. 변화와 손실을 지나치게 경계하면 묵은 문제와 관계를 오래 끌 수 있습니다.",
  "12.丑月축월": "검증된 방식과 생활 기반을 지키며 돈, 감정, 자원을 천천히 축적하는 성향이 강해집니다. 변화와 손실을 지나치게 경계하면 묵은 문제와 관계를 오래 끌 수 있습니다.",
  "丑月축월": "검증된 방식과 생활 기반을 지키며 돈, 감정, 자원을 천천히 축적하는 성향이 강해집니다. 변화와 손실을 지나치게 경계하면 묵은 문제와 관계를 오래 끌 수 있습니다."
};

function myungriDescriptionLookup(...values) {
  const candidates = values
    .flatMap((value) => asArray(value))
    .map(displayToken)
    .filter(Boolean)
    .flatMap((value) => {
      const noNumber = value.replace(/^\d+\.\s*/, "");
      const noParen = noNumber.replace(/\s*\([^)]*\)/g, "");
      const noSuffix = noParen.replace(/(격|월령|배합|작용|구조|근거)$/g, "");
      const hanja = (noNumber.match(/[\u3400-\u9fff]+/g) || []).join("");
      const hangul = (noNumber.match(/[가-힣]+/g) || []).join("");
      return [value, noNumber, noParen, noSuffix, hanja, hangul];
    })
    .map(normalizedConceptKey)
    .filter(Boolean);
  for (const key of candidates) {
    if (myungriConceptDescriptionBank[key]) return myungriConceptDescriptionBank[key];
  }
  for (const key of candidates.filter((item) => item.length >= 2)) {
    const found = Object.keys(myungriConceptDescriptionBank).find((candidate) => candidate === key || candidate.includes(key) || key.includes(candidate));
    if (found) return myungriConceptDescriptionBank[found];
  }
  return "";
}

function contextualActionDescription(action, concept) {
  const actors = asArray(action && action.actors).map((actor) => displayToken(actor && actor.label)).filter(Boolean);
  const pairCandidates = actors.length >= 2
    ? [actors.slice(0, 2).join("+"), actors.slice(0, 2).reverse().join("+")]
    : [];
  const conceptKey = contextualBankKeyForName(concept && concept.name, contextualConceptBank);
  const isExactConcept = conceptKey && normalizedConceptKey(conceptKey) === normalizedConceptKey(concept && concept.name);
  if (isExactConcept && concept && concept.body) {
    return humanizeContextualActionBody(concept.body);
  }
  return humanizeContextualActionBody(myungriDescriptionLookup(
    pairCandidates,
    concept && concept.name,
    action && action.action_name,
    action && action.pattern_label,
    action && action.rule_key,
  ) || "");
}

function conceptDescriptionBody(name, fallback, ...extraCandidates) {
  return myungriDescriptionLookup(name, extraCandidates) || fallback || "";
}

function contextualBankKeyForName(name, bank) {
  const key = normalizedConceptKey(name);
  const bankKeys = Object.keys(bank || {});
  const exact = bankKeys.find((candidate) => normalizedConceptKey(candidate) === key);
  if (exact) return exact;
  const included = bankKeys
    .map((candidate) => ({ candidate, normalized: normalizedConceptKey(candidate) }))
    .filter((entry) => entry.normalized && key.includes(entry.normalized))
    .sort((a, b) => b.normalized.length - a.normalized.length);
  if (included.length) return included[0].candidate;
  const direct = bankKeys.find((candidate) => {
    const normalized = normalizedConceptKey(candidate);
    return normalized && key.includes(normalized);
  });
  if (direct) return direct;
  const hasAll = (...tokens) => tokens.every((token) => key.includes(token));
  const aliases = [
    ["겁재극정재극편인", () => hasAll("겁재", "정재", "편인", "극")],
    ["정재극편인", () => hasAll("정재", "편인", "극")],
    ["겁재극정재", () => hasAll("겁재", "정재", "극")],
    ["정재생정관", () => hasAll("정재", "정관", "생")],
    ["정관생편인", () => hasAll("정관", "편인", "생")],
    ["정관극겁재", () => hasAll("정관", "겁재", "극") || (key.includes("관극") && key.includes("겁재"))],
    ["식신생편재", () => hasAll("식신", "편재", "생")],
    ["식상생재", () => key.includes("식상생재") || (key.includes("식") && key.includes("생") && key.includes("재")) || (key.includes("상관") && key.includes("생") && key.includes("재"))],
    ["재극인", () => key.includes("재극") && (key.includes("인") || key.includes("정인") || key.includes("편인"))],
    ["재생관", () => key.includes("재생") && key.includes("관")],
    ["관인상생", () => key.includes("관") && key.includes("인") && (key.includes("상생") || key.includes("생"))],
    ["편인도식", () => key.includes("편인") && (key.includes("도식") || key.includes("식신") || key.includes("상관"))],
  ];
  const matched = aliases.find(([alias, test]) => bank && bank[alias] && test());
  return matched ? matched[0] : null;
}

function tenGodTokensFromText(value) {
  const text = String(value || "");
  const order = ["비견", "겁재", "식신", "상관", "편재", "정재", "편관", "정관", "편인", "정인"];
  return order.filter((token) => text.includes(token));
}

function contextualActionDisplayTitle(action, concept) {
  const bankKey = contextualBankKeyForName(concept && concept.name, contextualConceptBank);
  if (bankKey === "겁재극정재극편인") return "겁재·편인";
  if (bankKey === "정재극편인") return "정재·편인";
  if (bankKey === "겁재극정재") return "겁재·정재";
  const actorLabels = unique(
    asArray(action && action.actors)
      .map((actor) => displayToken(actor && actor.label))
      .filter(Boolean),
    4,
  );
  const tokens = actorLabels.length ? actorLabels : tenGodTokensFromText(concept && concept.name);
  if (tokens.length >= 3) {
    if (tokens.includes("겁재") && tokens.includes("편인")) return "겁재·편인";
    if (tokens.includes("정재") && tokens.includes("편인")) return "정재·편인";
    return `${tokens[0]}·${tokens[tokens.length - 1]}`;
  }
  if (tokens.length >= 2) return tokens.slice(0, 2).join("·");
  return displayToken(concept && concept.name) || "종합 근거";
}

function humanizeContextualActionBody(body) {
  return String(body || "")
    .replace(/겁재극정재극편인/g, "겁재와 편인")
    .replace(/정재극편인/g, "정재와 편인")
    .replace(/겁재극정재/g, "겁재와 정재");
}

function contextualConceptCopy(action, options = {}) {
  const rawName = displayToken((action && (action.action_name || action.pattern_label || action.rule_key)) || "중심 작용");
  const name = rawName || "중심 작용";
  const bankKey = contextualBankKeyForName(name, contextualConceptBank);
  const copy = bankKey ? contextualConceptBank[bankKey] : null;
  const groups = textList((action && action.group_labels) || [], 4);
  const fallbackKeywords = groups.length
    ? groups.map((label) => `${label} 작용`)
    : ["격국 기준", "월령 작용", "오행 보정", "현실 작용", "운의 체감"];
  const body = copy
    ? copy.body
    : `${name}은 사주의 작용 방향을 잡는 근거입니다.`;
  return {
    name,
    body: options.fullBody ? body : compactText(body, 140),
    keywords: (copy && copy.keywords && copy.keywords.length ? copy.keywords : fallbackKeywords).slice(0, 12),
  };
}

function renderConceptExplanationSection(title, concepts, anchor, options = {}) {
  const limit = Number.isFinite(options.limit) ? Math.max(1, Number(options.limit)) : 6;
  const visible = asArray(concepts).filter((concept) => concept && concept.name && concept.body).slice(0, limit);
  if (!visible.length) return "";
  const showProfile = options.showProfile !== false;
  const compactBody = options.compactBody !== false;
  return `
    <section class="paper-card concept-explanation-section" ${anchor ? `data-scroll-anchor="${escapeHtml(anchor)}"` : ""}>
      <h2>${escapeHtml(title)}</h2>
      <div class="factor-grid">
        ${visible
          .map((concept) => {
            const labels = unique(asArray(concept.keywords).map(displayToken).filter(Boolean), 12);
            return `
              <article class="factor-block">
                <header><strong>${escapeHtml(concept.name)}</strong></header>
                <p>${escapeHtml(compactBody ? compactText(concept.body, 128) : concept.body)}</p>
                ${showProfile && concept.profile ? renderContextualOperationProfile(concept.profile) : ""}
                ${labels.length ? `<div class="tag-row">${labels.map((label) => `<span>${escapeHtml(label)}</span>`).join("")}</div>` : ""}
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function detailConceptIntro(sourceLabel) {
  const label = displayToken(sourceLabel);
  if (label.includes("월령 심화")) return "월령 심화는 태어난 달의 본기와 월률분야가 실제로 어떤 순서로 작동하는지를 가르는 근거입니다.";
  if (label.includes("월령")) return "월령 기준은 사주의 기본 환경과 필요한 오행을 정하는 근거입니다.";
  if (label.includes("생극") || label.includes("십신")) return "생극·십신은 재물, 책임, 표현, 보호가 서로 이어지거나 제어되는 경로를 설명하는 근거입니다.";
  if (label.includes("상생상극")) return "상생상극은 오행 사이의 충돌과 통관 여부를 구분하는 근거입니다.";
  if (label.includes("오행·십신")) return "오행·십신 통합은 천간과 지지의 오행 배합이 실제 역할과 사건으로 바뀌는 지점을 설명합니다.";
  if (label.includes("오행")) return "오행 배합은 특정 오행 조합이 성향과 사건의 질감을 만드는 방식을 설명합니다.";
  if (label.includes("지지") || label.includes("지장간")) return "지지와 지장간은 겉으로 드러나지 않았지만 현실 사건으로 올라오는 조건을 설명합니다.";
  if (label.includes("합충") || label.includes("형") || label.includes("파") || label.includes("해")) return "합충형파해는 지지가 묶이고 흔들리고 손상되는 방식이 어느 영역의 사건으로 드러나는지를 설명합니다.";
  if (label.includes("일간")) return "일간 수용값은 특정 천간을 일간이 받아들이는 방식이 성향과 판단으로 나타나는 지점을 설명합니다.";
  return "이 항목은 원국 안에서 실제 판단에 사용되는 판단 근거입니다.";
}

function detailConceptDomainSentence(card) {
  const domains = unique(asArray(card && card.domain_labels).map(displayToken).filter(Boolean), 4);
  if (!domains.length) return "원국 전체의 작용 방향을 좁히는 데 사용합니다.";
  return `${displayJoin(domains, "·")} 영역에서 이 작용이 어떤 방식으로 드러나는지 판단할 때 사용합니다.`;
}

function detailConceptKeywords(card) {
  const direct = unique(asArray(card && card.keywords).map(displayToken), 12);
  if (direct.length) return direct;
  return unique(asArray(card && card.tags).map(displayToken), 12);
}

function detailCardToConcept(card) {
  if (!card) return null;
  const name = displayToken(card.title || card.heading || card.source_label || "판단 근거");
  const source = displayToken(card.source_label || card.layer || "");
  const body = productText(card.body || card.lead || card.summary || "");
  const parts = [
    body || detailConceptIntro(source || name),
  ].filter(Boolean);
  return {
    name,
    body: parts.join(" "),
    keywords: detailConceptKeywords(card),
    kind: displayToken(card.layer || card.source_label || "concept"),
    sourceLabel: displayToken(card.source_label || ""),
  };
}

function factorToDetailConcept(factor) {
  if (!factor) return null;
  const name = displayToken(factor.heading || factor.source_label || "판단 근거");
  const body = productText(factor.lead || factor.body || "");
  return {
    name,
    body: body || detailConceptIntro(factor.source_label || factor.layer || name),
    keywords: detailConceptKeywords(factor),
    kind: displayToken(factor.layer || factor.source_label || "concept"),
    sourceLabel: displayToken(factor.source_label || ""),
  };
}

function detailUnitConcepts(unit, fallbackFactors = []) {
  const cards = asArray(unit && unit.cards).map(detailCardToConcept).filter(Boolean);
  const factors = cards.length ? [] : asArray(fallbackFactors).map(factorToDetailConcept).filter(Boolean);
  return [...cards, ...factors];
}

function mergeConcepts(concepts, limit = 10) {
  const seen = new Set();
  return asArray(concepts)
    .filter((concept) => concept && concept.name && concept.body)
    .filter((concept) => {
      const key = normalizedConceptKey(concept.name);
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, limit);
}

function gyeokgukConceptCopy(contract = {}) {
  const patternLabel = displayToken(contract.primary_pattern_label || contract.primary_pattern);
  const tenGodLabel = displayToken(contract.primary_ten_god_label || contract.month_command_label);
  const name = patternLabel || (tenGodLabel ? `${tenGodLabel}격` : "격국");
  const copy = gyeokgukConceptBank[name] || gyeokgukConceptBank[tenGodLabel] || null;
  if (!name && !copy) return null;
  const body = copy
    ? copy.body.replace(new RegExp(`^${tenGodLabel}격`), name)
    : "격국은 월령을 중심으로 어떤 십신이 사회적 성취와 사건의 기준이 되는지를 정하는 틀입니다. 격은 이름표가 아니라 원국이 무엇을 통해 균형과 성패를 얻는지를 보는 기준입니다.";
  return {
    name,
    body,
    keywords: copy ? copy.keywords : ["월령", "격국", "사회적 역할", "성패 기준", "성격 조건", "희기 판단", "성취 방식", "운의 방향"],
  };
}

function monthConceptCopy(contract = {}) {
  const branch = displayToken(contract.month_branch_label || contract.month_branch);
  const element = displayToken(contract.month_element_label || contract.month_element);
  const command = displayToken(contract.month_command_label || contract.month_command_ten_god);
  const copy = monthConceptBank[branch] || null;
  if (!branch && !element && !command) return null;
  const name = branch ? `${displayBranchReading(branch)}월` : "월령";
  const fallbackBody = "월령은 사주에서 계절의 권한입니다. 같은 글자와 같은 십신도 월령을 얻으면 현실에서 먼저 작동하고, 월령 밖의 글자는 드러나더라도 지속력과 체감이 달라집니다.";
  const body = copy ? copy.body : fallbackBody;
  const extra = displayJoin([element ? `${element} 기운` : "", command ? `${command} 월령` : ""], " · ");
  return {
    name,
    body: `${body}${extra ? ` 이 명식의 월령 바탕은 ${extra}입니다.` : ""}`,
    keywords: copy ? copy.keywords : ["계절 권한", "월지", "현실 조건", "지속력", "체감 기운", "사회적 역할", "지장간", "발동 기준"],
  };
}

const stemToElementHan = {
  甲: "木",
  乙: "木",
  丙: "火",
  丁: "火",
  戊: "土",
  己: "土",
  庚: "金",
  辛: "金",
  壬: "水",
  癸: "水",
};

const elementKoreanToHan = {
  목: "木",
  화: "火",
  토: "土",
  금: "金",
  수: "水",
};

function elementPairKeyFromSignal(signal) {
  const raw = [
    signalName(signal),
    signal && signal.element_pair_label,
    signal && signal.combination_key,
    signal && signal.direction_key,
    signal && signal.element_direction_key,
    signal && signal.summary_interpretation,
  ]
    .map((value) => String(value || ""))
    .join(" ");
  const tokens = [];
  Array.from(raw).forEach((char) => {
    if ("木火土金水".includes(char)) tokens.push(char);
    else if (stemToElementHan[char]) tokens.push(stemToElementHan[char]);
    else if (elementKoreanToHan[char]) tokens.push(elementKoreanToHan[char]);
  });
  if (tokens.length >= 2) return `${tokens[0]}${tokens[1]}`;
  const asciiTokens = String(raw)
    .split(/[^a-z]+/i)
    .map((part) => signalTokenLabels[part])
    .filter((part) => part && "木火土金水".includes(part));
  return asciiTokens.length >= 2 ? `${asciiTokens[0]}${asciiTokens[1]}` : "";
}

function elementCombinationConceptCopy(signal) {
  if (!signal) return null;
  const rawName =
    signalName(signal) ||
    displayToken(signal.element_pair_label) ||
    displaySignalToken(signal.element_direction_key || signal.direction_key) ||
    "오행 배합";
  const name = /^[목화토금수]$/.test(rawName) ? `${rawName} 기운` : rawName;
  const key = elementPairKeyFromSignal(signal);
  const reversedKey = key.length === 2 ? `${key[1]}${key[0]}` : "";
  const copy = elementCombinationConceptBank[key] || elementCombinationConceptBank[reversedKey] || null;
  const dictionaryDescription = displayToken(signal.dictionary_description);
  const engineInterpretation = displayToken(signal.interpretation || signal.summary_interpretation);
  const body = dictionaryDescription || engineInterpretation || (
    copy && key === reversedKey
      ? copy.body
      : copy
        ? copy.body
        : ""
  );
  if (!body) return null;
  const labels = displaySignalLabels([signal.layer, signal.strength, signal.polarity, ...(signal.domain_links || []), ...(signal.trait_keywords || [])], 8);
  return {
    name,
    kind: "element_combination",
    body,
    keywords: asArray(signal.dictionary_keywords).length
      ? asArray(signal.dictionary_keywords)
      : asArray(signal.trait_keywords).length
        ? asArray(signal.trait_keywords)
        : copy
          ? copy.keywords
          : labels,
  };
}

function climateConceptCopy(contract = {}) {
  const anchor = contract.anchor || {};
  const variation = contract.pattern_variation || {};
  const climate = variation.climate_adjustment || variation.climate_profile || {};
  const branch = displayToken(anchor.month_branch);
  const monthName = branch ? `${displayBranchReading(branch)}월` : "월령";
  const temperature = displayToken(climate.temperature_balance_label || displaySignalToken(climate.temperature_balance));
  const moisture = displayToken(climate.moisture_balance_label || displaySignalToken(climate.moisture_balance));
  const needs = unique(asArray(climate.climate_need_labels || climate.climate_needs).map(displaySignalToken).map(displayToken).filter(Boolean), 5);
  const interpretation = displayToken(climate.interpretation);
  if (!temperature && !moisture && !needs.length && !interpretation) return null;
  const climateState = displayJoin([temperature, moisture], " · ");
  const lead = `${monthName}${evidenceTopicParticle(monthName)} ${climateState || "계절의 온도와 건습"}${evidenceObjectParticle(climateState || "계절의 온도와 건습")} 기준으로 판단합니다.`;
  const needSentence = needs.length ? ` 조후상 필요한 오행은 ${displayJoin(needs, " · ")}입니다.` : "";
  return {
    name: "월령·조후",
    kind: "climate_adjustment",
    body: `${lead}${needSentence}${interpretation ? ` ${interpretation}` : ""}`,
    keywords: unique([climateState, ...needs.map((item) => `${item} 보완`), "온도 조절", "건습 조절", "조후 균형"].map(displayToken).filter(Boolean), 8),
  };
}

function detectBranchRelationKey(value) {
  const text = String(value || "");
  if (text.includes("혼재")) return "혼재";
  if (text.includes("충")) return "충";
  if (text.includes("형")) return "형";
  if (text.includes("파")) return "파";
  if (text.includes("해")) return "해";
  if (text.includes("합") || text.includes("받침") || text.includes("결속")) return "합";
  return "";
}

function branchRelationConceptCopy(source) {
  const rawSummary = source && (source.branch_relation_summary || source.position_summary || source.relation_label || source.relation_type);
  const summary = typeof rawSummary === "object" && rawSummary
    ? [
        ...(rawSummary.relation_type_labels || []),
        ...(rawSummary.grade_labels || []),
        ...(rawSummary.relation_position_labels || []),
        ...(rawSummary.effect_element_labels || []),
      ]
        .map(displayToken)
        .filter(Boolean)
        .join(" · ")
    : displayToken(rawSummary);
  const key = detectBranchRelationKey(summary);
  const copy = branchRelationConceptBank[key] || (summary ? branchRelationConceptBank.혼재 : null);
  if (!copy) return null;
  const name = key ? `지지 ${key}` : "지지 합충형파해";
  return {
    name,
    kind: "branch_relation_generic",
    body: `${copy.body} 당신의 사주에서는 지지 관계의 결속, 변동, 충돌 가능성을 판단 근거에 반영합니다.`,
    keywords: copy.keywords,
    profile: source,
  };
}

function contextualStructuralConcepts(contract = {}) {
  const anchor = contract.anchor || {};
  const variation = contract.pattern_variation || {};
  const elementSignal = variation.elemental_materiality || asArray(contract.element_combination_signals)[0];
  const relationSource = asArray(contract.contextual_actions).find((action) => action && action.branch_relation_summary);
  return [
    monthConceptCopy({
      month_branch_label: anchor.month_branch,
      month_element_label: anchor.month_element,
      month_command_label: displaySignalToken(anchor.month_command_ten_god),
    }),
    gyeokgukConceptCopy({
      primary_pattern_label: anchor.primary_pattern_label,
      primary_pattern: anchor.primary_pattern,
      primary_ten_god_label: anchor.primary_ten_god_label,
      month_command_label: anchor.month_command_ten_god,
    }),
    climateConceptCopy(contract),
    elementCombinationConceptCopy(elementSignal),
    branchRelationConceptCopy(relationSource),
  ].filter(Boolean);
}

function contextualActionBody(action) {
  return tongbyeonSurfaceText(contextualConceptCopy(action).body);
}

function contextualOperationLabel(operationProfile) {
  const state = String((operationProfile && operationProfile.operation_state) || "");
  if (state === "dominant_supported") return "타고난 바탕과 현실 조건이 함께 받쳐 강하게 드러납니다.";
  if (state === "visible_supported") return "겉으로 보이는 성향이 생활 속 결과로 이어집니다.";
  if (state === "eventful_pressure") return "힘은 분명하지만 변동과 마찰이 함께 따릅니다.";
  if (state === "weakened_by_context") return "기운은 있으나 시기와 환경을 가려야 합니다.";
  if (state === "latent_or_weak") return "사주 안에 잠긴 기운이 운에서 드러나는 시점을 봅니다.";
  if (state === "mixed_operation") return "성과와 부담이 함께 나타납니다.";
  if (state === "ordinary_operation") return "사주 안에서 일정하게 작동하는 요소입니다.";
  return "";
}

function renderContextualOperationProfile(action) {
  const profile = action && action.operation_profile;
  if (!profile) return "";
  const items = [
    { label: "작용 강도", value: profile.salience_score, score: profile.salience_score },
    { label: "맥락 보정", value: signedNumber(profile.context_score_delta), score: normalizeSignedScore(profile.context_score_delta, 24) },
    { label: "현실성", value: signedNumber(profile.reality_score_delta), score: normalizeSignedScore(profile.reality_score_delta, 36) },
  ].filter((item) => item.value !== "" && item.value !== null && item.value !== undefined);
  if (!items.length) return "";
  return `
    <div class="operation-profile">
      ${items.map((item) => `
        <div class="operation-profile-item ${metricToneClass(item.score)}">
          <span>${escapeHtml(item.label)}</span>
          <strong class="metric-grade-value ${metricGradeClass(item.score)}">${escapeHtml(metricGrade(item.score))}</strong>
          ${renderMetricBar(item.score)}
        </div>
      `).join("")}
    </div>
  `;
}

function signedNumber(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "";
  return number > 0 ? `+${number}` : String(number);
}

function normalizeSignedScore(value, span = 24) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 55;
  const bounded = Math.max(-span, Math.min(span, number));
  return Math.round(55 + (bounded / span) * 30);
}

function branchRelationSentence(label) {
  if (String(label).includes("받침")) return "지지 관계가 이 작용을 받쳐줍니다.";
  if (String(label).includes("압박")) return "지지 관계에서 형충의 압박이 작용합니다.";
  if (String(label).includes("혼재")) return "지지 관계는 도움과 부담이 함께 나타납니다.";
  if (String(label).includes("약함")) return "지지 관계의 직접 접점은 강하지 않습니다.";
  return `${label} 상태입니다.`;
}

function subjectParticle(text) {
  const chars = Array.from(String(text || "").trim());
  const last = chars[chars.length - 1];
  if (!last) return "은";
  const code = last.charCodeAt(0);
  if (code < 0xac00 || code > 0xd7a3) return "은";
  return (code - 0xac00) % 28 === 0 ? "는" : "은";
}

function nominativeParticle(text) {
  const chars = Array.from(String(text || "").trim());
  const last = chars[chars.length - 1];
  if (!last) return "가";
  const code = last.charCodeAt(0);
  if (code < 0xac00 || code > 0xd7a3) return "가";
  return (code - 0xac00) % 28 === 0 ? "가" : "이";
}

function instrumentParticle(text) {
  const chars = Array.from(String(text || "").trim());
  const last = chars[chars.length - 1];
  if (!last) return "로";
  const code = last.charCodeAt(0);
  if (code < 0xac00 || code > 0xd7a3) return "로";
  const jong = (code - 0xac00) % 28;
  return jong && jong !== 8 ? "으로" : "로";
}

function startInitialScreen() {
  if (hasFreshAffiliateReturn() && storedReportSession()) {
    document.documentElement.classList.add("is-restoring-premium");
    void restoreAffiliateReport().then((restored) => {
      if (!restored && state.activeScreen === "splash") {
        showScreen("home", { replace: true });
      }
    });
    return;
  }
  clearAffiliateReturnState();
  document.documentElement.classList.remove("is-restoring-premium");
  window.setTimeout(() => showScreen("home", { replace: true }), 880);
}

startInitialScreen();

form.addEventListener("submit", (event) => {
  event.preventDefault();
  void submitReport();
});

document.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) {
    return;
  }
  const action = button.dataset.action;
  if (!action) {
    return;
  }
  if (action === "back-home" || action === "go-home") {
    clearAffiliateReturnState();
    showScreen("home", action === "back-home" ? { replace: true } : {});
    return;
  }
  if (action === "go-report" || action === "back-report") {
    if (state.payload) {
      showScreen("report", action === "back-report" ? { replace: true } : {});
    } else {
      showScreen("home", { replace: true });
    }
    return;
  }
  if (action === "share") {
    void sharePage();
    return;
  }
  if (action === "copy-full-analysis") {
    void copyFullAnalysisResult(button);
    return;
  }
  if (action === "open-basis") {
    openDetail("contextual");
    return;
  }
  if (action === "open-timing") {
    openDetail("timing");
    return;
  }
});

function currentHistoryEntry(screenName = state.activeScreen, options = {}) {
  return {
    app: appHistoryKey,
    screen: screenName,
    detail: screenName === "detail" ? String(options.detail || state.activeDetail || "domains") : "",
    index: state.navIndex,
  };
}

function urlForHistoryScreen(screenName, options = {}) {
  const url = new URL(window.location.href);
  if (screenName === "report") {
    url.hash = "premium";
    return url.toString();
  }
  if (screenName === "detail") {
    const detailKey = String(options.detail || state.activeDetail || "domains").split(":")[0];
    const hashByDetail = {
      domains: "premium-section-1",
      timing: "timing",
      year_2026: "year-2026",
      year_2027: "year-2027",
      contextual: "basis",
    };
    url.hash = hashByDetail[detailKey] || detailKey || "premium";
    return url.toString();
  }
  if (screenName === "home") {
    url.hash = "";
    return url.toString();
  }
  return url.toString();
}

function sameHistoryEntry(a, b) {
  return Boolean(
    a &&
      b &&
      a.app === appHistoryKey &&
      b.app === appHistoryKey &&
      a.screen === b.screen &&
      String(a.detail || "") === String(b.detail || ""),
  );
}

function syncHistoryForScreen(name, options = {}) {
  if (options.skipHistory || !window.history || !window.history.pushState) {
    return;
  }
  const replace = Boolean(options.replace || !state.historyReady);
  const current = window.history.state && window.history.state.app === appHistoryKey
    ? window.history.state
    : null;
  const nextIndex = replace ? state.navIndex : state.navIndex + 1;
  const entry = { ...currentHistoryEntry(name, options), index: nextIndex };
  if (sameHistoryEntry(current, entry)) {
    return;
  }
  const targetUrl = urlForHistoryScreen(name, options);
  if (replace) {
    window.history.replaceState(entry, "", targetUrl);
  } else {
    window.history.pushState(entry, "", targetUrl);
  }
  state.navIndex = nextIndex;
  state.historyReady = true;
}

function showScreen(name, options = {}) {
  state.activeScreen = name;
  document.body.classList.toggle("is-report-view", name === "report");
  document.body.classList.toggle("is-detail-view", name === "detail");
  screens.forEach((screen) => {
    screen.classList.toggle("is-active", screen.dataset.screen === name);
  });
  bottomNav.classList.toggle("is-hidden", name === "splash" || name === "loading" || name === "home");
  const activeDetailKey = String(state.activeDetail || "").split(":")[0];
  [...bottomNav.querySelectorAll("button")].forEach((button) => {
    const action = button.dataset.action;
    button.classList.toggle(
      "is-active",
      (name === "home" && action === "go-home") ||
        (name === "report" && action === "go-report") ||
        (name === "detail" && !["timing", "contextual"].includes(activeDetailKey) && action === "go-report") ||
        (name === "detail" && activeDetailKey === "timing" && action === "open-timing") ||
        (name === "detail" && activeDetailKey === "contextual" && action === "open-basis"),
    );
  });
  if (name !== "splash") {
    window.requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "instant" }));
  }
  syncHistoryForScreen(name, options);
}

function restoreScreenFromHistory(entry) {
  if (!entry || entry.app !== appHistoryKey) {
    return;
  }
  const nextIndex = Number(entry.index);
  state.navIndex = Number.isFinite(nextIndex) ? nextIndex : 0;
  state.historyReady = true;
  const screenName = String(entry.screen || "home");
  if (screenName === "detail") {
    if (state.payload && state.detailPayload) {
      renderDetailScreen(entry.detail || "summary");
      showScreen("detail", { skipHistory: true });
    } else {
      showScreen("home", { skipHistory: true });
    }
    return;
  }
  if (screenName === "report") {
    showScreen(state.payload ? "report" : "home", { skipHistory: true });
    return;
  }
  if (screenName === "loading" || screenName === "splash") {
    showScreen(state.payload ? "report" : "home", { skipHistory: true });
    return;
  }
  const knownScreen = screens.some((screen) => screen.dataset.screen === screenName);
  showScreen(knownScreen ? screenName : "home", { skipHistory: true });
}

window.addEventListener("popstate", (event) => {
  restoreScreenFromHistory(event.state);
});

window.addEventListener("blur", () => {
  if (affiliatePopupVisible) markAffiliateDeparture();
});

window.addEventListener("pagehide", () => {
  if (affiliatePopupVisible) markAffiliateDeparture();
  if (hasFreshAffiliateReturn()) affiliatePageWasHidden = true;
});

window.addEventListener("focus", revealReportAfterCoupangReturn);
window.addEventListener("pageshow", revealReportAfterCoupangReturn);

document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    if (affiliatePopupVisible) markAffiliateDeparture();
    if (hasFreshAffiliateReturn()) affiliatePageWasHidden = true;
    return;
  }
  revealReportAfterCoupangReturn();
});

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function firstSentence(value, fallback = "") {
  const text = productText(value || "").trim();
  if (!text) {
    return fallback;
  }
  const found = text.match(/.*?[.!?。]/);
  return found ? found[0].trim() : text;
}

function rawFirstSentence(value, fallback = "") {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (!text) {
    return fallback;
  }
  const found = text.match(/.*?[.!?。]/);
  return found ? found[0].trim() : text;
}

function compactText(value, limit = 96) {
  const text = productText(value || "").replace(/\s+/g, " ").trim();
  if (text.length <= limit) {
    return text;
  }
  return `${text.slice(0, limit).replace(/\s+\S*$/, "")}...`;
}

function displayListValue(value) {
  if (value && typeof value === "object") {
    return (
      value.display_name ||
      value.displayName ||
      value.label ||
      value.title ||
      value.name ||
      value.status_label ||
      value.value ||
      ""
    );
  }
  return value;
}

function unique(values, limit = 6) {
  return [...new Set(values.filter(Boolean).map((value) => String(displayListValue(value) || "").trim()).filter(Boolean))].slice(0, limit);
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function textList(value, limit = 6) {
  return unique(asArray(value), limit);
}

function sectionDisplayTitle(section) {
  const raw = String((section && (section.title || section.domain_label)) || "상세 분석").trim();
  return productText(sectionTitleAliases[raw] || raw);
}

function formPayload() {
  const data = new FormData(form);
  return {
    birthDate: String(data.get("birthDate") || "").trim(),
    birthTime: String(data.get("birthTime") || "").trim(),
    gender: String(data.get("gender") || "male"),
    calendarType: "solar",
    tier: String(data.get("tier") || "public_mvp"),
    relationshipStatus: "unknown",
    targetYear: "2026",
  };
}

function validatePayload(payload) {
  if (!/^\d{8}$|^\d{4}-\d{2}-\d{2}$/.test(payload.birthDate)) {
    throw new Error("생년월일은 19990101 또는 1999-01-01 형식으로 입력해야 합니다.");
  }
  if (!payload.birthTime) {
    throw new Error("태어난 시간을 선택해야 합니다. 모르는 경우에는 '시간 모름'을 선택하면 됩니다.");
  }
}

async function submitReport() {
  const payload = formPayload();
  try {
    validatePayload(payload);
  } catch (error) {
    showToast(error.message);
    return;
  }
  showScreen("loading", { skipHistory: true });
  startLoading();
  try {
    const initialResult = await requestJudgment(payload);
    persistReportSession(initialResult, payload);
    const result = await hydrateInitialDetailPayload(initialResult, payload);
    state.payload = result;
    renderReport(result);
    await finishLoading();
    showScreen("report");
    window.requestAnimationFrame(showCoupangAffiliatePopup);
  } catch (error) {
    cancelLoading();
    showToast(error.message || "분석 결과를 불러오지 못했습니다.");
    showScreen("home");
  }
}

const RETRYABLE_ANALYSIS_STATUSES = new Set([408, 425, 429, 500, 502, 503, 504]);

function pendingAnalysisMessage(data) {
  const status = String((data && data.status) || "queued");
  const jobsAhead = Math.max(0, Number((data && data.jobsAhead) || 0));
  const estimatedWaitSeconds = Math.max(0, Number((data && data.estimatedWaitSeconds) || 0));
  if (status === "queued" && jobsAhead > 0) {
    const waitCopy = estimatedWaitSeconds > 0 ? ` 약 ${estimatedWaitSeconds}초 내외가 예상됩니다.` : "";
    return `앞선 분석 ${jobsAhead}건을 순서대로 처리하고 있습니다.${waitCopy}`;
  }
  if (status === "queued") return "분석 순서를 확보했습니다. 잠시 후 계산을 시작합니다.";
  if (status === "running") return "명식을 계산하고 운의 강약을 정리하고 있습니다.";
  return String((data && data.message) || "분석 결과를 준비하고 있습니다.");
}

async function fetchAnalysisJson(url, options = {}, maxAttempts = 4) {
  let lastError = null;
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 25000);
    try {
      const response = await fetch(url, { ...options, signal: controller.signal });
      const data = await response.json().catch(() => null);
      if (RETRYABLE_ANALYSIS_STATUSES.has(response.status) && attempt + 1 < maxAttempts) {
        const retryAfterMs = Number(data && data.retryAfterMs);
        if (response.status === 429) {
          state.loadingCeiling = Math.min(state.loadingCeiling, 42);
          updateLoading(
            Math.max(state.loadingValue, 34),
            (data && (data.message || (data.error && data.error.message))) ||
              "현재 분석 요청이 많아 잠시 순서를 조정하고 있습니다.",
          );
        }
        await wait(
          Number.isFinite(retryAfterMs) && retryAfterMs > 0
            ? Math.min(retryAfterMs, 6000)
            : Math.min(700 * (2 ** attempt), 2800),
        );
        continue;
      }
      return { response, data };
    } catch (error) {
      lastError = error;
      if (attempt + 1 >= maxAttempts) break;
      await wait(Math.min(700 * (2 ** attempt), 2800));
    } finally {
      window.clearTimeout(timeoutId);
    }
  }
  throw new Error(
    lastError && lastError.name === "AbortError"
      ? "분석 서버의 응답이 늦어지고 있습니다. 연결을 다시 시도해 주세요."
      : "분석 서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.",
  );
}

async function requestJudgment(payload, recoveryDepth = 0) {
  const { response, data } = await fetchAnalysisJson("/api/judgment", {
    method: "POST",
    headers: { "Content-Type": "application/json; charset=utf-8", Accept: "application/json" },
    body: JSON.stringify({ ...payload, async: true }),
  }, 30);
  if (response.status === 202 && data && data.pending && data.jobId) {
    state.loadingCeiling = data.status === "running" ? 94 : 58;
    updateLoading(Math.max(state.loadingValue, 24), pendingAnalysisMessage(data));
    return pollJudgment(data.jobId, payload, recoveryDepth);
  }
  if (!response.ok || !(data && data.ok)) {
    throw new Error((data && data.error && data.error.message) || "분석 결과 생성에 실패했습니다.");
  }
  return data;
}

async function pollJudgment(jobId, payload, recoveryDepth = 0) {
  for (let index = 0; index < 150; index += 1) {
    await wait(index < 4 ? 900 : 1400);
    const { response, data } = await fetchAnalysisJson(`/api/judgment-status?jobId=${encodeURIComponent(jobId)}`, {
      headers: { Accept: "application/json" },
    }, 3);
    if (response.status === 202 && data && data.pending) {
      state.loadingCeiling = data.status === "running" ? 94 : 58;
      updateLoading(Math.max(state.loadingValue, data.status === "running" ? 46 : 28), pendingAnalysisMessage(data));
      continue;
    }
    if ([404, 409, 500].includes(response.status) && recoveryDepth < 2) {
      updateLoading(Math.max(state.loadingValue, 86), "분석 서버와 결과를 다시 연결하고 있습니다.");
      return requestJudgment(payload, recoveryDepth + 1);
    }
    if (!response.ok || !(data && data.ok)) {
      throw new Error((data && data.error && data.error.message) || "분석 결과 생성에 실패했습니다.");
    }
    return data;
  }
  throw new Error("분석 시간이 길어지고 있습니다. 잠시 후 다시 시도해 주세요.");
}

async function requestJudgmentDetail(token, requestPayload, recoveryDepth = 0) {
  for (let index = 0; index < 150; index += 1) {
    const { response, data } = await fetchAnalysisJson(
      `/api/judgment-detail?token=${encodeURIComponent(token)}`,
      { headers: { Accept: "application/json" } },
      3,
    );
    if (response.status === 202 && data && data.pending) {
      await wait(900);
      continue;
    }
    if ([404, 409, 500].includes(response.status) && requestPayload && recoveryDepth < 2) {
      updateLoading(Math.max(state.loadingValue, 94), "세부 결과를 다시 연결하고 있습니다.");
      const recovered = await requestJudgment(requestPayload, recoveryDepth + 1);
      const recoveredReport = (recovered && recovered.report && typeof recovered.report === "object")
        ? recovered.report
        : {};
      const recoveredToken = String(
        (recovered && (recovered.detailToken || recovered.detail_token)) ||
          recoveredReport.detail_token ||
          recoveredReport.detailToken ||
          "",
      ).trim();
      const recoveredDeferred = Boolean(
        (recovered && recovered.detailDeferred) || recoveredReport.detail_deferred,
      );
      if (!recoveredDeferred || !recoveredToken) return recovered;
      return requestJudgmentDetail(recoveredToken, requestPayload, recoveryDepth + 1);
    }
    if (!response.ok || !(data && data.ok)) {
      throw new Error((data && data.error && data.error.message) || "상세 결과를 불러오지 못했습니다.");
    }
    return data;
  }
  throw new Error("세부 분석 시간이 길어지고 있습니다. 잠시 후 다시 시도해 주세요.");
}

function mergePayloads(basePayload, detailPayload) {
  if (!basePayload || !detailPayload) return basePayload || detailPayload;
  const baseReport = (basePayload.report && typeof basePayload.report === "object") ? basePayload.report : {};
  const detailReport = (detailPayload.report && typeof detailPayload.report === "object") ? detailPayload.report : {};
  return {
    ...basePayload,
    ...detailPayload,
    chart: {
      ...(basePayload.chart || {}),
      ...(detailPayload.chart || {}),
    },
    report: {
      ...baseReport,
      ...detailReport,
      detail_deferred: false,
    },
    detailDeferred: false,
  };
}

async function hydrateInitialDetailPayload(payload, requestPayload = null) {
  const report = (payload && payload.report && typeof payload.report === "object") ? payload.report : {};
  const token = String(
    (payload && (payload.detailToken || payload.detail_token)) ||
      report.detail_token ||
      report.detailToken ||
      "",
  ).trim();
  const deferred = Boolean((payload && payload.detailDeferred) || report.detail_deferred);
  if (!deferred || !token) return payload;
  updateLoading(Math.max(state.loadingValue, 92), "세부 지표와 근거를 함께 정리하고 있습니다.");
  const detailPayload = await requestJudgmentDetail(token, requestPayload);
  return mergePayloads(payload, detailPayload);
}

function mergeDeferredDetailPayload(detailPayload) {
  if (!state.payload || !detailPayload) return;
  state.payload = mergePayloads(state.payload, detailPayload);
  state.detailLoaded = true;
  state.detailLoadingPromise = null;
  const normalized = normalizeReportPayload(state.payload);
  configureMetricDisplayAdjustment(normalized.sections);
  state.detailPayload = {
    report: normalized.report,
    chart: normalized.chart,
    profile: normalized.profile,
    sections: normalized.sections,
    factors: normalized.factors,
    detailUnits: normalized.detailUnits,
    engineContract: normalized.engineContract,
    screenContract: normalized.screenContract,
    elementBalance: normalized.elementBalance,
  };
}

function detailKeyNeedsDeferredPayload(key) {
  const [baseKey, rawIndex] = String(key || "domains").split(":");
  const normalizedBaseKey = baseKey === "basis" ? "contextual" : baseKey;
  if (normalizedBaseKey === "domains" && rawIndex) return true;
  return ["timing", "year_2026", "year_2027", "contextual", "gyeokguk", "ten_gods", "month", "elements", "temperature"].includes(normalizedBaseKey);
}

async function ensureDeferredDetailPayload(key) {
  if (!detailKeyNeedsDeferredPayload(key) || state.detailLoaded) return;
  const token = String(state.detailToken || "").trim();
  if (!token) return;
  if (!state.detailLoadingPromise) {
    state.detailLoadingPromise = requestJudgmentDetail(token).then((detailPayload) => {
      mergeDeferredDetailPayload(detailPayload);
      return detailPayload;
    }).catch((error) => {
      state.detailLoadingPromise = null;
      throw error;
    });
  }
  await state.detailLoadingPromise;
}

function renderDetailLoading() {
  return `
    <div class="light-surface">
      <section class="paper-card detail-loading-card">
        <span>상세 분석 준비</span>
        <h2>필요한 근거를 불러오고 있습니다.</h2>
        <p>세부 지표와 근거를 정리하는 중입니다. 잠시 후 결과가 이어집니다.</p>
      </section>
    </div>
  `;
}

function wait(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function startLoading() {
  cancelLoading();
  state.loadingValue = 8;
  state.loadingStartedAt = Date.now();
  state.loadingCeiling = 94;
  loadingFill.classList.remove("is-completing");
  updateLoading(8, loadingMessages[0]);
  state.loadingTimer = window.setInterval(() => {
    const elapsed = Math.max(0, Date.now() - state.loadingStartedAt);
    const estimated = Math.min(state.loadingCeiling, 8 + 86 * (1 - Math.exp(-elapsed / 16000)));
    const next = Math.max(state.loadingValue, estimated);
    const messageIndex = Math.min(
      loadingMessages.length - 1,
      Math.max(0, Math.floor(((next - 8) / 86) * loadingMessages.length)),
    );
    updateLoading(next, loadingMessages[messageIndex]);
  }, 80);
}

function cancelLoading() {
  if (state.loadingTimer) {
    window.clearInterval(state.loadingTimer);
    state.loadingTimer = null;
  }
}

async function finishLoading() {
  cancelLoading();
  const elapsed = Math.max(0, Date.now() - state.loadingStartedAt);
  if (elapsed < 900) {
    await wait(900 - elapsed);
  }
  loadingFill.classList.add("is-completing");
  updateLoading(100, "분석을 마쳤습니다. 결과 화면을 열고 있습니다.");
  await wait(560);
  loadingFill.classList.remove("is-completing");
}

function updateLoading(percent, message) {
  const normalized = Math.max(0, Math.min(100, Number(percent) || 0));
  state.loadingValue = Math.max(state.loadingValue, normalized);
  loadingPercent.textContent = `${Math.round(state.loadingValue)}%`;
  loadingFill.style.transform = `scaleX(${(state.loadingValue / 100).toFixed(4)})`;
  loadingMessage.textContent = message;
}

function renderReport(payload) {
  const normalized = normalizeReportPayload(payload);
  const {
    report,
    chart,
    profile,
    sections,
    factors,
    detailUnits,
    engineContract,
    screenContract,
    elementBalance,
  } = normalized;
  configureMetricDisplayAdjustment(sections);
  const nickname = String(new FormData(form).get("nickname") || "").trim() || "고객";
  reportTitle.textContent = "사주 분석 결과";

  const reportParts = [
    renderReportHero(profile, screenContract, sections, nickname, chart),
    renderReportEntryBoard(screenContract, sections),
  ];
  reportRoot.innerHTML = reportParts.join("");

  reportRoot.querySelectorAll("[data-open-detail]").forEach((button) => {
    button.addEventListener("click", () => openDetail(button.dataset.openDetail));
  });

  state.detailToken = String(
    payload.detailToken ||
      payload.detail_token ||
      report.detail_token ||
      report.detailToken ||
      "",
  );
  state.detailLoaded = !Boolean(payload.detailDeferred || report.detail_deferred);
  state.detailLoadingPromise = null;
  state.detailPayload = { report, chart, profile, sections, factors, detailUnits, engineContract, screenContract, elementBalance };
}

function normalizeReportPayload(payload) {
  const report = (payload && payload.report) || {};
  const chart = (payload && payload.chart) || {};
  const profile = report.analysis_profile_summary || report.premium_profile_summary || {};
  const sections = Array.isArray(report.analysis_sections)
    ? report.analysis_sections
    : Array.isArray(report.premium_sections)
      ? report.premium_sections
      : [];
  const factors = Array.isArray(report.factor_sections) ? report.factor_sections : [];
  const detailUnits = report.analysis_detail_units || {};
  const engineContract = report.analysis_engine_contract || {};
  const screenContract = report.analysis_screen_contract || {};
  return {
    report,
    chart,
    profile,
    sections,
    factors,
    detailUnits,
    engineContract,
    screenContract,
    elementBalance: calculateElementBalance(chart),
  };
}

function renderReportHero(profile, screenContract, sections = [], nickname = "고객", chart = {}) {
  const title = productText(profile.profile_type || "사주 분석 결과");
  const summaryContract = (screenContract && screenContract.summary) || {};
  const headline = firstSentence(
    summaryContract.headline || profile.headline || profile.summary,
    "명식의 중심과 생활 영역별 운세를 종합했습니다.",
  );
  return `
    <section class="report-hero">
      <div class="seal-icon" aria-hidden="true">✥</div>
      <span class="report-hero-kicker">타고난 기질 유형</span>
      <h2>${escapeHtml(title)}</h2>
      <p>${escapeHtml(headline)}</p>
    </section>
  `;
}

function getScreenMenu(screenContract, sections) {
  const detailMenuCopyByKey = {
    domains: "7개 분야 총운",
    timing: "좋은 시기·조심할 시기",
    year_2026: "2026년 흐름",
    year_2027: "2027년 흐름",
    gyeokguk: "월지와 격국의 기준",
    ten_gods: "십신 조합과 사건 작용",
    month: "태어난 계절의 바탕",
    elements: "오행 배합과 생극",
    temperature: "조후와 건습의 균형",
    contextual: "명식·격국·작용",
  };
  const fallbackCards = [
    { key: "domains", title: "분야별 총운", copy: "7개 분야 총운", icon: "運" },
    { key: "timing", title: "시기운", copy: "좋은 시기·조심할 시기", icon: "年" },
    { key: "year_2026", title: "올해운", copy: "2026년 흐름", icon: "26" },
    { key: "year_2027", title: "내년운", copy: "2027년 흐름", icon: "27" },
    { key: "gyeokguk", title: "격국 분석", copy: "월지와 사회적 방향", icon: "格" },
    { key: "ten_gods", title: "십신 조합", copy: "역할과 사건", icon: "十" },
    { key: "month", title: "월령 해석", copy: "계절과 현실 조건", icon: "月" },
    { key: "elements", title: "오행 분석", copy: "기질과 작용의 분포", icon: "五" },
    { key: "temperature", title: "조후 분석", copy: "기운의 온도와 균형", icon: "水" },
    { key: "contextual", title: "종합 근거", copy: "명식·격국·작용", icon: "綜" },
  ];
  const contractCards = screenContract && Array.isArray(screenContract.detail_menu) ? screenContract.detail_menu : [];
  const cards = contractCards.length
    ? [
        ...contractCards,
        ...fallbackCards.filter((fallback) => !contractCards.some((card) => card && card.key === fallback.key)),
      ]
    : fallbackCards;
  return cards
    .filter((card) => card && card.key)
    .filter((card) => !["basis", "summary"].includes(String(card.key || "")))
    .map((card) => {
      const key = String(card.key || "");
      return {
        key,
        title: key === "timing" ? "시기운" : productText(card.title || key),
        copy: productText(detailMenuCopyByKey[key] || card.copy || ""),
        icon: card.icon || "✦",
        cta: key === "domains" ? "분야 총운" : "상세",
      };
    });
}

function renderReportEntryBoard(screenContract, sections) {
  const cards = getScreenMenu(screenContract, sections);
  const byKey = new Map(cards.map((card) => [card.key, card]));
  const entryOrder = ["timing", "year_2026", "year_2027", "contextual"];
  const entries = entryOrder
    .map((key) => byKey.get(key))
    .filter(Boolean);
  const domainBoard = renderSectionPreviewList(sections);
  if (!entries.length) return domainBoard;
  return `
    ${domainBoard}
    <section class="report-entry-board report-entry-secondary" aria-label="시기와 분석 근거">
      <div class="report-entry-head">
        <strong>다른 분석</strong>
      </div>
      <div class="report-entry-grid">
        ${entries.map((card) => `
          <button class="report-entry-card report-entry-${escapeHtml(card.key)}" type="button" data-open-detail="${escapeHtml(card.key)}" aria-label="${escapeHtml(card.title)} 열기">
            <span class="report-entry-symbol">${escapeHtml(card.icon)}</span>
            <span class="report-entry-copy">
              <strong>${escapeHtml(card.title)}</strong>
              <small>${escapeHtml(card.copy)}</small>
            </span>
          </button>
        `).join("")}
      </div>
    </section>
  `;
}

function renderReportComposition(sections, screenContract) {
  const cards = getScreenMenu(screenContract, sections);
  const depthKeys = ["timing", "year_2026", "year_2027", "contextual", "elements", "gyeokguk", "month", "temperature", "ten_gods"];
  const depthCards = depthKeys.map((key) => cards.find((card) => card.key === key)).filter(Boolean);
  if (!depthCards.length) return "";
  const renderCompositionCard = (card, index) => {
    const featured = card.key === "timing" || card.key === "contextual" ? " is-featured" : "";
    return `
      <button class="section-card report-toc-card${featured}" type="button" data-open-detail="${card.key}">
        <span class="section-symbol">${escapeHtml(card.icon)}</span>
        <span class="section-card-copy">
          <small>${String(index + 1).padStart(2, "0")}</small>
          <h3>${escapeHtml(card.title)}</h3>
          <p>${escapeHtml(card.copy)}</p>
        </span>
      </button>
    `;
  };
  return `
    <details class="report-composition report-toc report-composition-compact">
      <summary>
        <span>
          <b>종합 근거</b>
          <small>팔자 · 월령 · 격국 · 오행</small>
        </span>
        <em>보기</em>
      </summary>
      <div class="report-list report-toc-list report-toc-secondary">
        ${depthCards.map((card, index) => renderCompositionCard(card, index)).join("")}
      </div>
    </details>
  `;
}

function renderCoreSummary(profile, elementBalance, screenContract) {
  const primary = profile.primary || {};
  const secondary = profile.secondary || {};
  const management = profile.management || {};
  const summaryContract = (screenContract && screenContract.summary) || {};
  const contractCards = asArray(summaryContract.cards).slice(0, 4);
  const miniCards = contractCards.length
    ? contractCards.map((card) => ({
        label: productText(card.label || ""),
        title: productText(card.title || card.value || ""),
        value: productText(card.value || ""),
      }))
    : [
        { label: "강한 영역", title: primary.domain_label || "직업운", value: primary.value || "분석 중" },
        { label: "동반 강점", title: secondary.domain_label || "결혼운", value: secondary.value || "분석 중" },
        { label: "주의 영역", title: management.domain_label || "재물운", value: management.value || "분석 중" },
      ];
  const profileType = productText(profile.profile_type || "사주 유형");
  const headline = productText(summaryContract.headline || profile.summary || profile.headline || "전체 운세의 중심을 정리했습니다.");
  const topElement = elementLabels[elementBalance.top.key] || elementLabels.wood;
  return `
    <section class="summary-dashboard">
      <header>
        <span>종합 기준</span>
        <h2>${escapeHtml(profileType)}</h2>
        <p>${escapeHtml(headline)}</p>
      </header>
      <div class="summary-orb" aria-hidden="true">
        <strong>${escapeHtml(topElement.han)}</strong>
        <small>${escapeHtml(topElement.ko)} ${elementBalance.top.percent}%</small>
      </div>
      <div class="summary-metrics">
        ${miniCards.slice(0, 4).map((card, index) => renderMiniStat(card.label, card.title, card.value, index)).join("")}
      </div>
      <div class="summary-keyword-block" aria-label="사주 핵심 키워드">
        <strong>사주 핵심 키워드</strong>
        <div class="tag-row summary-tags">
          ${unique([
            primary.label,
            secondary.label,
            management.label,
            `${topElement.ko} 기운 중심`,
          ])
            .map((tag) => `<span>${escapeHtml(productText(tag))}</span>`)
            .join(" ")}
        </div>
      </div>
    </section>
  `;
}

function renderDomainScoreBoard(sections) {
  const visible = asArray(sections)
    .map((section, index) => ({ section, index }))
    .filter(({ section }) => section && !["timing", "life"].includes(section.domain))
    .slice(0, 7);
  if (!visible.length) return "";
  return `
    <section class="domain-score-board">
      <div class="domain-score-board-head">
        <span>분야별 등급</span>
        <strong>강하게 드러나는 운과 함께 확인할 운을 나누었습니다.</strong>
      </div>
      <div class="domain-score-list">
        ${visible.map(({ section, index }) => {
          const grade = sectionAggregateGrade(section, "");
          const metric = domainRouteMetric(section);
          const domain = section.domain || "default";
          const title = sectionDisplayTitle(section);
          return `
            <button class="domain-score-row ${metricToneClassFromGrade(grade)}" type="button" data-open-detail="domains:${index}" aria-label="${escapeHtml(title)} 열기">
              <span class="section-symbol">${escapeHtml(sectionSymbols[domain] || sectionSymbols.default)}</span>
              <span class="domain-score-copy">
                <strong>${escapeHtml(title)}</strong>
                <small>${escapeHtml(metric ? metric.label : compactText(section.lead || section.headline || section.summary, 34))}</small>
              </span>
              <span class="domain-score-value">
                ${grade
                  ? `<b class="metric-grade-value ${metricGradeClassFromLabel(grade)}">${escapeHtml(grade)}</b>`
                  : "<b>-</b>"}
              </span>
            </button>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

function sectionDetailKeyForDomain(sections, domain) {
  const normalizedDomain = String(domain || "").trim();
  const index = sections.findIndex((section) => section && section.domain === normalizedDomain);
  return index >= 0 ? `domains:${index}` : "domains";
}

function sectionDetailKeyForPanel(sections, panel) {
  if (!panel) return "domains";
  return sectionDetailKeyForDomain(
    sections,
    panel.domain || panel.domain_key || panel.key || panel.section_domain,
  );
}

function renderMiniStat(label, title, value, index = 0) {
  const displayLabel = productText(label);
  const displayTitle = productText(title);
  const displayValue = compactText(productText(value), 18);
  const marker = `${displayLabel || ""} ${displayTitle || ""} ${displayValue || ""}`;
  const tone = /관리|주의|위험|보완|약점/.test(marker) || index === 2 ? "watch" : "good";
  return `
    <article class="mini-stat ${tone === "watch" ? "is-watch" : "is-good"}">
      <span>${escapeHtml(displayLabel)}</span>
      <strong>${escapeHtml(displayTitle)}</strong>
      ${displayValue && displayValue !== displayTitle ? `<em>${escapeHtml(displayValue)}</em>` : ""}
    </article>
  `;
}

function calculateElementBalance(chart) {
  const rows = Array.isArray(chart.pillarRows) ? chart.pillarRows : [];
  const counts = { wood: 0, fire: 0, earth: 0, metal: 0, water: 0 };
  rows.forEach((row) => {
    if (stemElements[row.stem]) counts[stemElements[row.stem]] += 2.1;
    if (branchElements[row.branch]) counts[branchElements[row.branch]] += 2.3;
    (row.hiddenStems || []).forEach((stem) => {
      if (stemElements[stem]) counts[stemElements[stem]] += 0.7;
    });
  });
  const total = Object.values(counts).reduce((sum, value) => sum + value, 0) || 1;
  const values = Object.entries(counts).map(([key, value]) => ({
    key,
    percent: Math.round((value / total) * 100),
  }));
  values.sort((a, b) => b.percent - a.percent);
  return {
    values,
    top: values[0] || { key: "wood", percent: 0 },
    counts,
  };
}

function renderElementSummary(balance) {
  const css = balance.values.map((item) => `--${item.key}:${item.percent}`).join(";");
  return `
    <section class="paper-card element-board">
      <div>
        <h2>오행 균형 요약</h2>
        <p>천간, 지지, 지장간에서 강하게 드러나는 기운을 정리했습니다. 월령과 조후를 함께 보면 실제 작용이 더 분명해집니다.</p>
      </div>
      <div class="element-chart" style="${css}">
        <strong>${elementLabels[balance.top.key].ko}<small>${balance.top.percent}%</small></strong>
      </div>
      <div class="element-bars">
        ${balance.values.map(renderElementRow).join("")}
      </div>
    </section>
  `;
}

function renderElementBalanceSnapshot(balance) {
  const values = Array.isArray(balance && balance.values) ? balance.values : [];
  if (!values.length) return "";
  const css = values.map((item) => `--${item.key}:${item.percent}`).join(";");
  const top = balance.top || values[0] || { key: "wood", percent: 0 };
  const weakest = [...values].reverse().find((item) => item && item.percent > 0) || values[values.length - 1] || top;
  const topLabel = elementLabels[top.key] || elementLabels.wood;
  const weakLabel = elementLabels[weakest.key] || topLabel;
  return `
    <section class="element-snapshot">
      <button class="element-snapshot-card" type="button" data-open-detail="elements" aria-label="오행 균형 상세 열기">
        <div class="element-snapshot-head">
          <span>오행 균형</span>
          <strong>오행의 강약과 보완점을 정리했습니다</strong>
          <p>명식의 오행 분포를 요약했습니다. 월령과 조후를 함께 보면 실제 작용이 더 분명해집니다.</p>
        </div>
        <div class="element-snapshot-body">
          <div class="element-snapshot-chart" style="${css}" aria-hidden="true">
            <strong>${escapeHtml(topLabel.han)}<small>${top.percent}%</small></strong>
          </div>
          <div class="element-snapshot-list">
            <div class="element-snapshot-badges">
              <span>강세 ${escapeHtml(topLabel.ko)}(${escapeHtml(topLabel.han)})</span>
              <span>보완 ${escapeHtml(weakLabel.ko)}(${escapeHtml(weakLabel.han)})</span>
            </div>
            <div class="element-snapshot-bars">
              ${values.map(renderElementSnapshotRow).join("")}
            </div>
          </div>
        </div>
        <em>오행 상세</em>
      </button>
    </section>
  `;
}

function renderElementRow(item) {
  const label = elementLabels[item.key];
  return `
    <div class="element-row">
      <span>${label.ko}(${label.han})</span>
      <i><b style="--value:${item.percent}%; --bar:${label.color};"></b></i>
      <strong>${item.percent}%</strong>
    </div>
  `;
}

function renderElementSnapshotRow(item) {
  const label = elementLabels[item.key] || elementLabels.wood;
  return `
    <div class="element-snapshot-row">
      <span>${escapeHtml(label.han)}</span>
      <i><b style="--value:${item.percent}%; --bar:${label.color};"></b></i>
      <strong>${item.percent}%</strong>
    </div>
  `;
}

function renderTimingPreview(profile, sections) {
  const timing = profile.timing || {};
  const timingSection = sections.find((section) => section.domain === "timing");
  const timingMap = timingSection && timingSection.timing_map ? timingSection.timing_map : {};
  const goodEvents = asArray(timingMap.goodHighlights).slice(0, 3);
  const cautionEvents = asArray(timingMap.cautionHighlights).slice(0, 3);
  const fallbackGood = timingPreviewEventsFromText(timing.good, "good").slice(0, 3);
  const fallbackCaution = timingPreviewEventsFromText(timing.caution, "caution").slice(0, 3);
  const visibleGood = goodEvents.length ? goodEvents : fallbackGood;
  const visibleCaution = cautionEvents.length ? cautionEvents : fallbackCaution;
  return `
    <section class="dark-card timing-preview-board">
      <div class="timing-preview-head">
        <span>시기운</span>
        <strong>좋은 시기와 조심할 시기</strong>
      </div>
      <div class="timing-preview-columns">
        ${renderTimingPreviewColumn("좋은 시기", visibleGood, "good", "뚜렷한 연도 없음")}
        ${renderTimingPreviewColumn("조심할 시기", visibleCaution, "caution", "뚜렷한 연도 없음")}
      </div>
      <button class="timing-preview-link" type="button" data-open-detail="timing">시기운 자세히 보기</button>
    </section>
  `;
}

function renderTimingPreviewColumn(title, events, tone = "good", fallback = "") {
  const visible = timingYearOnlyItems(events, 6);
  const toneClass = tone === "caution" ? "is-caution" : "is-good";
  return `
    <div class="timing-preview-column ${toneClass}">
      <strong>${escapeHtml(title)}</strong>
      ${visible.length ? `<div class="timing-year-pills">${visible.map((year) => `<b>${escapeHtml(year)}</b>`).join("")}</div>` : `<p>${escapeHtml(fallback)}</p>`}
    </div>
  `;
}

function renderTimingPreviewMiniCard(event, tone = "good") {
  const title = productText(event.title || event.focus || "주요 시기");
  const keywords = filterTimingKeywordsForTitle(timingEventKeywords(event, 4), title, 3);
  const line = compactText(productText(stripTimingTitlePrefix(event.productLine || event.decisionLine || event.summary || event.body || "", title)), 56);
  return `
    <article class="timing-preview-mini ${tone === "caution" ? "is-caution" : "is-good"}">
      <span>${escapeHtml(timingEventYearAge(event))}</span>
      <strong>${escapeHtml(title)}</strong>
      ${keywords.length ? `<em>${keywords.map((keyword) => escapeHtml(keyword)).join(" · ")}</em>` : ""}
      ${line ? `<p>${escapeHtml(line)}</p>` : ""}
    </article>
  `;
}

function timingPreviewEventsFromText(value, tone = "good") {
  const text = String(value || "").trim();
  if (!text) {
    return [];
  }
  return text
    .split(/\s*[\/,]\s*|\s+·\s+/)
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => {
      const match = part.match(/(\d{4})년(?:\(([^)]+)\))?\s*(.*)/);
      if (!match) {
        return { title: part, summary: part, tone };
      }
      return {
        year: match[1],
        ageLabel: match[2] || "",
        title: productText((match[3] || "").trim() || (tone === "caution" ? "조심할 시기" : "좋은 시기")),
        summary: productText(part),
        tone,
      };
    });
}

function timingYearOnlyItems(events, limit = 8) {
  const years = [];
  const seen = new Set();
  asArray(events).forEach((event) => {
    const source = typeof event === "object" && event !== null ? event.year : event;
    const text = String(source || "").trim();
    const match = text.match(/\d{4}/);
    if (!match) return;
    const label = `${match[0]}년`;
    if (seen.has(label)) return;
    seen.add(label);
    years.push(label);
  });
  return years.slice(0, limit);
}

function renderSectionPreviewList(sections) {
  const domainRoutes = sortReportDomainRoutes(asArray(sections)
    .map((section, index) => ({ section, index }))
    .filter(({ section }) => section && !["timing", "life", "year_2026", "year_2027"].includes(section.domain))
  ).slice(0, 7);
  if (!domainRoutes.length) return "";
  return `
    <section class="domain-route-board report-entry-domain-board" aria-label="분야별 총운">
      <div class="domain-route-head">
        <strong>분야별 총운</strong>
      </div>
      <div class="domain-direct-grid">
        ${domainRoutes.map(renderDomainDirectCard).join("")}
      </div>
    </section>
  `;
}

function sortReportDomainRoutes(routes) {
  const order = new Map(primaryReportDomains.map((domain, index) => [domain, index]));
  return [...routes].sort((a, b) => {
    const aDomain = a.section && a.section.domain;
    const bDomain = b.section && b.section.domain;
    const aRank = order.has(aDomain) ? order.get(aDomain) : 100 + (a.index || 0);
    const bRank = order.has(bDomain) ? order.get(bDomain) : 100 + (b.index || 0);
    return aRank - bRank;
  });
}

function renderDomainDirectCard({ section, index }) {
  const domain = section.domain || "default";
  const title = sectionDisplayTitle(section);
  const grade = sectionAggregateGrade(section, "");
  const meta = domainLandingMeta(section);
  const focusLabel = meta.strongLabel || meta.primaryLabel || meta.watchLabel || "";
  return `
    <button class="domain-direct-card ${metricToneClassFromGrade(grade)}" type="button" data-open-detail="domains:${index}" aria-label="${escapeHtml(title)} 열기">
      <span class="section-symbol">${escapeHtml(sectionSymbols[domain] || sectionSymbols.default)}</span>
      <span class="domain-direct-copy">
        <strong>${escapeHtml(title)}</strong>
        <small>${escapeHtml(focusLabel || (domainPickerHints[domain] || domainPickerHints.default))}</small>
      </span>
      <span class="domain-direct-score">
        ${grade
          ? `<b class="metric-grade-value ${metricGradeClassFromLabel(grade)}">${escapeHtml(grade)}</b>`
          : "<em>상세</em>"}
      </span>
    </button>
  `;
}

function domainRouteMetric(section) {
  const candidates = [
    ...metricItemsFrom(section, "representative_metrics", 6),
    ...metricItemsFrom(section, "feature_axes", 8),
  ];
  if (!candidates.length) return null;
  const scored = candidates
    .map((item) => ({ item, score: metricScore(item) }))
    .filter(({ score }) => Number.isFinite(score));
  if (!scored.length) return null;
  scored.sort((a, b) => (
    Math.abs(metricToneScore(b.item, b.score) - 62) -
    Math.abs(metricToneScore(a.item, a.score) - 62)
  ));
  const picked = scored[0];
  return {
    label: metricLabel(picked.item),
    score: picked.score,
    level: metricLevelForItem(picked.item, picked.score, picked.item.level || picked.item.value || ""),
  };
}

async function openDetail(key) {
  if (!state.payload || !state.detailPayload) {
    showScreen("home", { replace: true });
    return;
  }
  const detailKey = String(key || "domains") === "basis" ? "contextual" : (key || "domains");
  if (detailKeyNeedsDeferredPayload(detailKey) && !state.detailLoaded) {
    state.activeDetail = detailKey;
    detailTitle.textContent = getActiveDetailTitle(detailKey);
    detailRoot.innerHTML = renderDetailLoading();
    showScreen("detail", { detail: detailKey });
    try {
      await ensureDeferredDetailPayload(detailKey);
    } catch (error) {
      showToast(error.message || "상세 결과를 불러오지 못했습니다.");
      return;
    }
  }
  renderDetailScreen(detailKey);
  showScreen("detail", { detail: detailKey });
}

function bindDetailScreenEvents() {
  detailRoot.querySelectorAll("[data-detail-key]").forEach((button) => {
    button.addEventListener("click", () => openDetail(button.dataset.detailKey));
  });
  const activeTab = detailRoot.querySelector(".detail-tabs [data-detail-key].is-active");
  if (activeTab) {
    window.requestAnimationFrame(() => activeTab.scrollIntoView({ block: "nearest", inline: "center" }));
  }
  detailRoot.querySelectorAll("[data-scroll-target]").forEach((button) => {
    button.addEventListener("click", () => scrollDetailTarget(button.dataset.scrollTarget));
  });
}

function renderDetailScreen(detailKey) {
  state.activeDetail = detailKey;
  detailTitle.textContent = getActiveDetailTitle(detailKey);
  detailRoot.innerHTML = renderDetail(detailKey);
  bindDetailScreenEvents();
}

function scrollDetailTarget(targetName) {
  if (!targetName) return;
  const target = detailRoot.querySelector(`[data-scroll-anchor="${targetName}"]`);
  if (!target) return;
  const details = target.closest("details");
  if (details) details.open = true;
  target.scrollIntoView({ behavior: "smooth", block: "start" });
}

function getActiveDetailTitle(key) {
  const [baseKey, rawIndex] = String(key || "domains").split(":");
  const normalizedBaseKey = baseKey === "basis" ? "contextual" : baseKey;
  if (baseKey === "domains") {
    const domainIndex = Number(rawIndex);
    const sections = (state.detailPayload && state.detailPayload.sections) || [];
    if (Number.isFinite(domainIndex) && sections[domainIndex]) {
      const title = sectionDisplayTitle(sections[domainIndex]);
      return title.endsWith("분석") ? title : `${title} 분석`;
    }
  }
  const activeDetailItem = getScreenMenu(
    (state.detailPayload && state.detailPayload.screenContract) || {},
    (state.detailPayload && state.detailPayload.sections) || [],
  ).find((item) => item.key === key || item.key === normalizedBaseKey);
  return (activeDetailItem && activeDetailItem.title) || "상세 분석";
}

function renderDetail(key) {
  const baseKey = String(key || "domains").split(":")[0];
  const normalizedBaseKey = baseKey === "basis" ? "contextual" : baseKey;
  const contextKey = normalizedBaseKey === "domains"
    ? "domains"
    : (["year_2026", "year_2027"].includes(normalizedBaseKey) ? normalizedBaseKey : "none");
  return withMetricDisplayContext(contextKey, () => renderDetailWithContext(key));
}

function renderDetailWithContext(key) {
  const { report, chart, profile, sections, factors, detailUnits, engineContract, screenContract, elementBalance } = state.detailPayload;
  const [baseKey, rawIndex] = String(key || "domains").split(":");
  const normalizedBaseKey = baseKey === "basis" ? "contextual" : baseKey;
  const selectedIndex = Number(rawIndex);
  const tabs = renderDetailTabs(normalizedBaseKey);
  const insight = shouldShowScreenInsight(normalizedBaseKey) ? renderScreenInsights(getDetailScreenContract(screenContract, normalizedBaseKey), normalizedBaseKey) : "";
  if (normalizedBaseKey === "elements") return wrapLight(tabs + insight + renderElementDetail(elementBalance, detailUnits.elements, engineContract.elements));
  if (normalizedBaseKey === "timing") return wrapLight(tabs + renderTimingDetail(profile, sections, chart, engineContract.timing, detailUnits.timing));
  if (normalizedBaseKey === "year_2026" || normalizedBaseKey === "year_2027") {
    return wrapLight(tabs + renderAnnualDetail(findSectionByDomain(sections, normalizedBaseKey), normalizedBaseKey));
  }
  if (normalizedBaseKey === "domains") {
    if (!rawIndex) {
      return wrapLight(tabs + renderDomainLanding(sections));
    }
    const domainIndex = Number.isFinite(selectedIndex) ? selectedIndex : 0;
    return wrapLight(tabs + renderDomainDetail(sections[domainIndex] || sections[0], sections, engineContract.domains, domainIndex, detailUnits.domains));
  }
  if (normalizedBaseKey === "gyeokguk") return wrapLight(tabs + insight + renderGyeokgukDetail(engineContract.gyeokguk, detailUnits.gyeokguk, factors));
  if (normalizedBaseKey === "ten_gods") return wrapLight(tabs + insight + renderTenGodDetail(engineContract.ten_gods, detailUnits.ten_gods, engineContract.gyeokguk_contextual));
  if (normalizedBaseKey === "month") return wrapLight(tabs + insight + renderMonthDetail(engineContract.month, detailUnits.month, factors));
  if (normalizedBaseKey === "temperature") return wrapLight(tabs + insight + renderTemperatureDetail(elementBalance, factors, detailUnits.temperature, engineContract.temperature));
  if (normalizedBaseKey === "contextual") return wrapLight(tabs + insight + renderContextualDetail(engineContract.gyeokguk_contextual, detailUnits.contextual, chart, factors, detailUnits.basis));
  return wrapLight(tabs + insight + renderDomainLanding(sections));
}

function shouldShowScreenInsight(baseKey) {
  return !["domains", "year_2026", "year_2027", "gyeokguk", "ten_gods", "month", "elements", "temperature", "contextual"].includes(String(baseKey || ""));
}

function wrapLight(content) {
  return `<div class="light-surface">${content}</div>`;
}

function renderDetailTabs(activeKey) {
  const baseActiveKey = String(activeKey || "domains").split(":")[0];
  const primaryKeys = new Set(["domains", "timing", "year_2026", "year_2027", "contextual"]);
  const menuItems = getScreenMenu(
    (state.detailPayload && state.detailPayload.screenContract) || {},
    (state.detailPayload && state.detailPayload.sections) || [],
  ).filter((item) => primaryKeys.has(item.key) || item.key === baseActiveKey);
  return `
    <nav class="detail-tabs" aria-label="상세 분석 메뉴">
      ${menuItems
        .map(
          (item) => `
            <button type="button" class="${item.key === baseActiveKey ? "is-active" : ""}" data-detail-key="${escapeHtml(item.key)}" aria-label="${escapeHtml(item.title)} 열기"${item.key === baseActiveKey ? ' aria-current="page"' : ""}>
              <span class="detail-tab-icon" aria-hidden="true">${escapeHtml(item.icon || "✦")}</span>
              <span class="detail-tab-copy">
                <strong>${escapeHtml(item.title)}</strong>
                <small>${escapeHtml(item.copy || "")}</small>
              </span>
            </button>
          `,
        )
        .join("")}
    </nav>
  `;
}

function domainCtaLabel(title) {
  const cleanTitle = String(title || "").trim();
  return cleanTitle ? "열기" : "열기";
}

function getDetailScreenContract(screenContract, key) {
  const screens = screenContract && screenContract.detail_screens;
  if (!screens || !screens[key]) {
    return {};
  }
  return screens[key];
}

function insightLimitForScreen(key) {
  if (key === "contextual") return 8;
  if (key === "gyeokguk" || key === "elements") return 5;
  return 4;
}

function screenInsightMeta(key = "") {
  const byKey = {
    summary: { icon: "要", eyebrow: "요약", tone: "summary" },
    domains: { icon: "運", eyebrow: "분야", tone: "domains" },
    timing: { icon: "年", eyebrow: "시기", tone: "timing" },
    gyeokguk: { icon: "格", eyebrow: "격국", tone: "gyeokguk" },
    month: { icon: "月", eyebrow: "월령", tone: "month" },
    elements: { icon: "五", eyebrow: "오행", tone: "elements" },
    temperature: { icon: "水", eyebrow: "조후", tone: "temperature" },
    contextual: { icon: "綜", eyebrow: "종합", tone: "contextual" },
    basis: { icon: "命", eyebrow: "명식", tone: "basis" },
  };
  return byKey[key] || { icon: "✦", eyebrow: "해석", tone: "default" };
}

function renderScreenInsights(screen, key = "") {
  const blocks = asArray(screen && screen.insight_blocks)
    .filter((block) => block && (block.title || block.value || block.body))
    .slice(0, insightLimitForScreen(key));
  if (!blocks.length) {
    return "";
  }
  const meta = screenInsightMeta(key);
  const hero = blocks[0] || {};
  const rest = blocks.slice(1);
  return `
    <section class="contract-card screen-insights screen-insights-${escapeHtml(meta.tone)}">
      <div class="screen-insight-hero">
        <div class="screen-insight-seal" aria-hidden="true">${escapeHtml(meta.icon)}</div>
        <div>
          <span>${escapeHtml(productText(meta.eyebrow))}</span>
          <h3>${escapeHtml(productText((screen && screen.title) || hero.title || "핵심 해석"))}</h3>
          ${(screen && screen.lead) ? `<p>${escapeHtml(screen.lead)}</p>` : hero.body ? `<p>${escapeHtml(hero.body)}</p>` : ""}
        </div>
      </div>
      <article class="insight-block insight-block-primary">
        <header>
          <span>${escapeHtml(productText(hero.tag || "주요 흐름"))}</span>
          <strong>${escapeHtml(productText(hero.title || ""))}</strong>
        </header>
        ${hero.value ? `<b>${escapeHtml(productText(hero.value))}</b>` : ""}
        ${(screen && screen.lead) && hero.body ? `<p>${escapeHtml(hero.body)}</p>` : ""}
        ${asArray(hero.evidence).length ? `<div class="tag-row">${asArray(hero.evidence).map((label) => `<span>${escapeHtml(label)}</span>`).join("")}</div>` : ""}
      </article>
      ${rest.length ? `
        <div class="insight-grid">
          ${rest
            .map(
              (block) => `
                <article class="insight-block">
                  <header>
                    <span>${escapeHtml(productText(block.tag || "핵심"))}</span>
                    <strong>${escapeHtml(productText(block.title || ""))}</strong>
                  </header>
                  ${block.value ? `<b>${escapeHtml(productText(block.value))}</b>` : ""}
                  ${block.body ? `<p>${escapeHtml(block.body)}</p>` : ""}
                  ${asArray(block.evidence).length ? `<div class="tag-row">${asArray(block.evidence).map((label) => `<span>${escapeHtml(label)}</span>`).join("")}</div>` : ""}
                </article>
              `,
            )
            .join("")}
        </div>
      ` : ""}
    </section>
  `;
}

function renderAnalysisDetailUnit(unit, fallbackTitle, fallbackLead, fallbackFactors = [], fallbackKeywords = []) {
  const cards = Array.isArray(unit && unit.cards) ? unit.cards : [];
  if (!cards.length) {
    return renderFactorCategory(fallbackTitle, fallbackLead, fallbackFactors, fallbackKeywords);
  }
  const layers = unique(unit.source_layers || [], 5);
  return `
    <section class="paper-card">
      <h2>${escapeHtml(unit.title || fallbackTitle)}</h2>
      <p>${escapeHtml(unit.lead || fallbackLead)}</p>
      ${layers.length ? `<div class="tag-row">${layers.map((label) => `<span>${escapeHtml(label)}</span>`).join("")}</div>` : ""}
      <div class="factor-grid">
        ${cards.map(renderAnalysisDetailCard).join("")}
      </div>
    </section>
  `;
}

function renderAnalysisEvidenceDrawer(unit, fallbackTitle, fallbackLead, options = {}) {
  const cards = Array.isArray(unit && unit.cards) ? unit.cards : [];
  if (!cards.length) return "";
  const limit = Number.isFinite(options.limit) ? Math.max(1, Number(options.limit)) : 4;
  const visibleCards = cards.slice(0, limit);
  const layers = unique(unit.source_layers || [], 5);
  const hiddenCount = Math.max(0, cards.length - visibleCards.length);
  const drawerTitle = productText(options.title || unit.title || fallbackTitle);
  return `
    <details class="evidence-drawer">
      <summary>
        <span>${escapeHtml(drawerTitle)}</span>
        <small>${cards.length}개 요소</small>
      </summary>
      <div class="evidence-drawer-body">
        <p>${escapeHtml(unit.lead || fallbackLead)}</p>
        ${layers.length ? `<div class="tag-row">${layers.map((label) => `<span>${escapeHtml(label)}</span>`).join("")}</div>` : ""}
        <div class="factor-grid">
          ${visibleCards.map(renderAnalysisDetailCard).join("")}
        </div>
        ${hiddenCount ? `<p class="evidence-more-note">나머지 ${hiddenCount}개 요소는 격국·월령·오행 상세 화면에서 따로 다룹니다.</p>` : ""}
      </div>
    </details>
  `;
}

function renderAnalysisDetailCard(card) {
  const labels = unique([card.source_label, ...(card.domain_labels || [])], 4);
  return `
    <article class="factor-block">
      <header>
        <strong>${escapeHtml(card.title || "해석 근거")}</strong>
      </header>
      <p>${escapeHtml(firstSentence(card.body, "명식에서 확인된 요소입니다."))}</p>
      <div class="tag-row">
        ${labels.map((label) => `<span>${escapeHtml(label)}</span>`).join("")}
      </div>
    </article>
  `;
}

function renderContractSummary(title, lead, items = [], chips = []) {
  const visibleItems = items.filter((item) => item && item.label && item.value).slice(0, 6);
  const visibleChips = unique(chips, 8);
  if (!visibleItems.length && !visibleChips.length) {
    return "";
  }
  return `
    <section class="contract-card">
      <h3>${escapeHtml(title)}</h3>
      ${lead ? `<p>${escapeHtml(lead)}</p>` : ""}
      ${
        visibleItems.length
          ? `<div class="contract-kv-grid">
              ${visibleItems
                .map(
                  (item) => `
                    <div>
                      <span>${escapeHtml(item.label)}</span>
                      <strong>${escapeHtml(displayToken(item.value) || item.value)}</strong>
                    </div>
                  `,
                )
                .join("")}
            </div>`
          : ""
      }
      ${visibleChips.length ? `<div class="tag-row">${visibleChips.map((chip) => `<span>${escapeHtml(displayToken(chip) || chip)}</span>`).join("")}</div>` : ""}
    </section>
  `;
}

function renderContractActionList(actions = [], title = "핵심 작용") {
  const visible = asArray(actions).filter((action) => action && (action.pair_name || action.title)).slice(0, 3);
  if (!visible.length) {
    return "";
  }
  return `
    <section class="paper-card">
      <h2>${escapeHtml(title)}</h2>
      <div class="contract-action-list">
        ${visible
          .map((action) => {
            const labels = unique(
              [action.pair_name || action.title, action.judgment_axis && action.judgment_axis.label, ...(action.domains || [])]
                .map((label) => displayToken(label))
                .filter(Boolean),
              5,
            );
            const body =
              action.summary_interpretation ||
              action.domain_projection ||
              action.effect ||
              action.mechanism ||
              action.timing ||
              "격국과 월령 기준에서 중심으로 선택된 지표입니다.";
            return `
              <article>
                <strong>${escapeHtml(action.pair_name || action.title)}</strong>
                <p>${escapeHtml(compactText(body, 116))}</p>
                ${labels.length ? `<div class="tag-row">${labels.map((label) => `<span>${escapeHtml(label)}</span>`).join("")}</div>` : ""}
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function renderStructureReadingPath(items = [], title = "읽는 순서", lead = "핵심을 먼저 잡고 필요한 항목으로 넘어갑니다.") {
  const visible = asArray(items).filter((item) => item && item.target && item.title).slice(0, 5);
  if (!visible.length) return "";
  return `
    <section class="domain-reading-guide structure-reading-guide is-structure-flow">
      <div class="domain-reading-head">
        <strong>${escapeHtml(title)}</strong>
        <span>${escapeHtml(lead)}</span>
      </div>
      <div class="domain-reading-path structure-reading-path">
        ${visible
          .map(
            (item, index) => `
              <button type="button" class="${item.primary ? "is-detail" : ""}" data-scroll-target="${escapeHtml(item.target)}">
                <span>${String(index + 1).padStart(2, "0")}</span>
                <strong>${escapeHtml(item.title)}</strong>
                ${item.caption ? `<p>${escapeHtml(item.caption)}</p>` : ""}
              </button>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function actionDisplayName(action) {
  if (!action) return "";
  return displayToken(action.pair_name || action.action_name || action.title || action.pattern_label || "");
}

function actionDisplayBody(action, fallback) {
  if (!action) return fallback;
  const body =
    action.summary_interpretation ||
    action.domain_projection ||
    action.effect ||
    action.mechanism ||
    action.timing ||
    fallback;
  return compactText(body, 118);
}

function actionFocusBody(action, fallback) {
  const name = actionDisplayName(action);
  if (name.includes("재생관") || name.includes("생정관") || name.includes("생편관") || (name.includes("재") && name.includes("생관"))) {
    return "재물과 현실 기반이 직책, 신용, 공식 계약으로 이어집니다.";
  }
  if (name.includes("관인상생")) {
    return "책임이 문서, 자격, 명분을 갖추며 안정됩니다.";
  }
  if (name.includes("식신제살")) {
    return "압박이 큰 일일수록 실무 능력과 처리력으로 풀어갑니다.";
  }
  if (name.includes("식상생재")) {
    return "기술과 결과물이 수입으로 연결됩니다.";
  }
  if (name.includes("재극인")) {
    return "돈과 성과 요구가 문서, 공부, 보호의 성격을 강하게 압박합니다.";
  }
  if (name.includes("관성") && name.includes("비겁")) {
    return "규칙과 책임 기준이 경쟁, 분배 문제를 정리합니다.";
  }
  return compactText(firstSentence(actionDisplayBody(action, fallback), fallback), 76);
}

function renderGyeokgukFocusBoard(contract, detailUnit) {
  if (!contract) return "";
  const primary = contract.primary_ten_god_label || contract.primary_pattern_label || contract.primary_pattern || "격국";
  const month = contract.month_branch_label || "";
  const command = contract.month_command_label || "";
  const formation = contract.formation_state || "";
  const centerAction = asArray(contract.center_core_actions)[0];
  const flowAction = asArray(contract.flow_activated_core_actions)[0];
  const useful = textList(contract.favorable_elements || contract.success_conditions || [], 3);
  const caution = textList(contract.unfavorable_elements || contract.failure_conditions || [], 3);
  const detailLead = detailUnit && detailUnit.lead ? detailUnit.lead : "태어난 달에서 잡힌 격이 사회적 방식과 운의 방향을 정합니다.";
  const cards = [
    {
      label: "기준이 되는 달",
      title: displayJoin([month, primary]) || primary,
      body: month && primary ? `월지 ${displayBranchReading(month)}가 ${primary}의 기준을 세우며, 사회적 역할과 선택 방식에 먼저 반영됩니다.` : displayJoin([command, formation]) || "월지에서 잡힌 기본 기준입니다.",
    },
    {
      label: "중심 작용",
      title: actionDisplayName(centerAction) || "십신 작용",
      body: actionFocusBody(centerAction, "격국이 실제 사건으로 드러날 때 중심이 됩니다."),
    },
    {
      label: "시기 작용",
      title: actionDisplayName(flowAction) || "시기운",
      body: actionFocusBody(flowAction, "대운과 세운에서 자극될 때 강하게 드러납니다."),
    },
    {
      label: "보정 기준",
      title: "유불리 오행",
      body: displayJoin([...useful, ...caution], " / ")
        ? `${displayJoin([...useful, ...caution], " / ")}의 강약에 따라 같은 격국도 결과가 달라집니다.`
        : "필요한 오행과 부담 오행에 따라 같은 격국도 결과가 달라집니다.",
    },
  ].filter((item) => item.title || item.body);
  return `
    <section class="gyeokguk-focus-card" data-scroll-anchor="gyeokguk-overview">
      <div class="gyeokguk-focus-head">
        <div class="gyeokguk-focus-seal" aria-hidden="true">格</div>
        <div>
          <span>격국의 중심</span>
          <h2>${escapeHtml(displayJoin([month, primary]) || primary)}</h2>
          <p>${escapeHtml(compactText(detailLead, 130))}</p>
        </div>
      </div>
      <div class="gyeokguk-focus-grid">
        ${cards
          .map(
            (item) => `
              <article>
                <span>${escapeHtml(item.label)}</span>
                <strong>${escapeHtml(item.title)}</strong>
                <p>${escapeHtml(item.body)}</p>
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderStructureFocusCard(options = {}) {
  const cards = asArray(options.cards).filter((item) => item && (item.title || item.body)).slice(0, 4);
  if (!options.title && !cards.length) return "";
  return `
    <section class="structure-focus-card structure-focus-${escapeHtml(options.tone || "default")}" ${options.anchor ? `data-scroll-anchor="${escapeHtml(options.anchor)}"` : ""}>
      <div class="structure-focus-head">
        <div class="structure-focus-seal" aria-hidden="true">${escapeHtml(options.icon || "命")}</div>
        <div>
          ${options.eyebrow ? `<span>${escapeHtml(options.eyebrow)}</span>` : ""}
          ${options.title ? `<h2>${escapeHtml(options.title)}</h2>` : ""}
          ${options.lead ? `<p>${escapeHtml(options.lead)}</p>` : ""}
        </div>
      </div>
      ${
        cards.length
          ? `<div class="structure-focus-grid">
              ${cards
                .map(
                  (item) => `
                    <article>
                      ${item.label ? `<span>${escapeHtml(item.label)}</span>` : ""}
                      ${item.title ? `<strong>${escapeHtml(item.title)}</strong>` : ""}
                      ${item.body ? `<p>${escapeHtml(item.body)}</p>` : ""}
                    </article>
                  `,
                )
                .join("")}
            </div>`
          : ""
      }
    </section>
  `;
}

function renderMonthFocusBoard(contract, detailUnit) {
  if (!contract) return "";
  const phase = contract.active_hidden_phase || {};
  const monthBranch = displayToken(contract.month_branch_label || contract.month_branch);
  const monthElement = displayToken(contract.month_element_label || contract.month_element);
  const monthCommand = displayToken(contract.month_command_label || contract.month_command_ten_god);
  const monthTitle = displayJoin([monthBranch, monthElement]) || monthBranch || "월령";
  const useful = textList(contract.useful_elements || contract.support_fits || [], 3);
  const caution = textList(contract.caution_elements || contract.pressure_fits || [], 3);
  const phaseTitle = displayJoin([phase.active_phase_label || phase.active_phase, phase.active_stem_label || phase.active_stem, phase.active_ten_god_label || phase.active_ten_god]);
  const cautionLabel = displayJoin(caution, " / ");
  const lead = detailUnit && detailUnit.lead
    ? compactText(detailUnit.lead, 126)
    : "월령은 태어난 계절과 현실 조건을 함께 잡는 기준입니다.";
  return renderStructureFocusCard({
    anchor: "month-overview",
    tone: "month",
    icon: "月",
    eyebrow: "월령의 바탕",
    title: monthTitle,
    lead,
    cards: [
      {
        label: "태어난 계절",
        title: monthBranch || "월지",
        body: monthElement ? `${monthElement}의 기운이 강하게 깔려 성향과 생활 조건의 바탕을 이룹니다.` : "월지가 사주의 기본 환경을 정합니다.",
      },
      {
        label: "월령 십신",
        title: monthCommand || "십신",
        body: monthCommand ? "일과 관계에서 어떤 역할로 움직이는지 판단하는 기준입니다." : "월령의 십신이 현실에서 드러나는 역할을 정합니다.",
      },
      {
        label: "숨은 작용",
        title: phaseTitle || "지장간",
        body: phaseTitle ? "겉으로 바로 보이지 않아도 운에서 자극되면 사건으로 드러나는 부분입니다." : "지장간은 현실 속에 숨어 있는 동기와 사건의 씨앗입니다.",
      },
      {
        label: "필요 기준",
        title: useful.length ? displayJoin(useful, " / ") : "필요 오행",
        body: cautionLabel ? `부담 기운은 ${cautionLabel}${instrumentParticle(cautionLabel)} 잡힙니다. 강해질수록 월령의 균형을 흐립니다.` : "필요한 오행이 들어올 때 판단과 실행이 안정됩니다.",
      },
    ],
  });
}

function renderGyeokgukDetail(contract, detailUnit, factors) {
  const actionNames = textList(asArray(contract && contract.center_core_actions).map((action) => action.pair_name || action.title), 4);
  const summary = renderContractSummary(
    "격국 기준",
    "태어난 달에서 잡힌 중심 구조와 실제 사건으로 이어지는 십신 조합입니다.",
    [
      { label: "주격", value: contract && (contract.primary_ten_god_label || contract.primary_pattern_label || contract.primary_pattern) },
      { label: "월지", value: contract && contract.month_branch_label },
      { label: "월령 십신", value: contract && contract.month_command_label },
      { label: "성립 상태", value: contract && contract.formation_state },
    ],
    [
      ...((contract && contract.favorable_elements) || []),
      ...((contract && contract.unfavorable_elements) || []),
      ...actionNames,
    ],
  );
  return `
    ${renderGyeokgukFocusBoard(contract, detailUnit)}
    ${renderConceptExplanationSection("격국 개념", [gyeokgukConceptCopy(contract)], "gyeokguk-concept")}
    ${renderStructureReadingPath(
      [
        { target: "gyeokguk-overview", title: "요약", caption: "격국의 기준", primary: true },
        { target: "gyeokguk-concept", title: "개념", caption: "격국의 성립" },
        { target: "gyeokguk-standard", title: "기준", caption: "월령과 성립 상태" },
        { target: "gyeokguk-core", title: "중심 작용", caption: "십신 조합" },
        { target: "gyeokguk-flow", title: "운의 발동", caption: "시기운" },
      ],
      "해석 순서",
      "태어난 달의 기준을 먼저 잡고, 원국의 작용과 운에서 드러나는 시점을 구분합니다.",
    )}
    <div data-scroll-anchor="gyeokguk-standard">${summary}</div>
    <div data-scroll-anchor="gyeokguk-core">${renderContractActionList(contract && contract.center_core_actions, "격국의 중심 작용")}</div>
    <div data-scroll-anchor="gyeokguk-flow">${renderContractActionList(contract && contract.flow_activated_core_actions, "시기운에서 발동되는 작용")}</div>
    <div data-scroll-anchor="gyeokguk-evidence">${renderAnalysisDetailUnit(detailUnit, "격국 분석", "월지를 기준으로 격과 십신의 작용을 판별합니다.", factors, ["격", "십신", "구조"])}</div>
  `;
}

function renderTenGodFocusBoard(contract, detailUnit) {
  if (!contract) return "";
  const primary = contract.primary_ten_god_label || contract.primary_pattern_label || contract.primary_pattern || "십신";
  const month = contract.month_branch_label || "";
  const command = contract.month_command_label || "";
  const singleAction = asArray(contract.single_actions)[0];
  const dualAction = asArray(contract.dual_actions)[0];
  const centerAction = asArray(contract.center_actions)[0];
  const lead = detailUnit && detailUnit.lead
    ? compactText(detailUnit.lead, 126)
    : "십신이 실제 생활에서 맡는 역할과 사건의 방향입니다.";
  return renderStructureFocusCard({
    anchor: "ten-gods-overview",
    tone: "gyeokguk",
    icon: "十",
    eyebrow: "십신 요약",
    title: displayJoin([month, primary]) || primary,
    lead,
    cards: [
      {
        label: "월령 십신",
        title: command || primary,
        body: command ? `월령에서 ${command}이 중심으로 잡히며, 사회적 역할을 해석하는 기준이 됩니다.` : "월령에서 잡힌 십신이 판단의 기준이 됩니다.",
      },
      {
        label: "단일 작용",
        title: actionDisplayName(singleAction) || "기본 역할",
        body: actionFocusBody(singleAction, "한 십신이 격국 안에서 맡는 기본 역할입니다."),
      },
      {
        label: "이중 작용",
        title: actionDisplayName(dualAction) || "조합 작용",
        body: actionFocusBody(dualAction, "두 십신이 이어질 때 사건의 결론과 부담이 달라집니다."),
      },
      {
        label: "중심 작용",
        title: actionDisplayName(centerAction) || "격국 작용",
        body: actionFocusBody(centerAction, "격국 안에서 실제 결과를 만드는 중심 흐름입니다."),
      },
    ],
  });
}

function renderTenGodDomainMap(contract) {
  const map = contract && contract.domain_action_map ? contract.domain_action_map : {};
  const entries = Object.values(map)
    .filter((item) => item && (item.label || item.domain || asArray(item.action_labels).length || asArray(item.lead_actions).length))
    .slice(0, 6);
  if (!entries.length) return "";
  return `
    <section class="paper-card" data-scroll-anchor="ten-gods-domains">
      <h2>생활 영역별 적용</h2>
      <div class="topic-grid">
        ${entries
          .map((item) => {
            const labels = unique([...(item.action_labels || []), ...(item.basis_codes || [])].map(displayToken), 5);
            const state = displayToken(item.state || "");
            const support = Number(item.support);
            const burden = Number(item.burden);
            const domainLabel = displayToken(item.label || item.domain || "해당 영역");
            const body = Number.isFinite(support) || Number.isFinite(burden)
              ? `${domainLabel}에서는 ${support >= burden ? "보강 작용이 더 우세하게 잡힙니다." : "부담 작용을 먼저 확인해야 합니다."}`
              : "십신 작용이 실제 생활 영역으로 내려가는 지점입니다.";
            return `
              <article class="topic-card">
                <header>
                  <strong>${escapeHtml(displayToken(item.label || item.domain || "영역"))}</strong>
                  ${state ? `<em>${escapeHtml(state)}</em>` : ""}
                </header>
                <p>${escapeHtml(body)}</p>
                ${labels.length ? `<div class="tag-row">${labels.map((label) => `<span>${escapeHtml(label)}</span>`).join("")}</div>` : ""}
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function renderTenGodDetail(contract, detailUnit, contextualContract) {
  if (!contract) {
    return `<section class="paper-card"><h2>십신 분석</h2><p>십신 작용을 표시할 산출값이 없습니다.</p></section>`;
  }
  const counts = contract.action_match_counts || {};
  const actionLabels = textList(contract.action_labels || [], 8);
  const summary = renderContractSummary(
    "십신 기준",
    "월령과 격국을 기준으로 십신의 역할과 사건 방향을 판별합니다.",
    [
      { label: "주격", value: contract.primary_ten_god_label || contract.primary_pattern_label || contract.primary_pattern },
      { label: "월지", value: contract.month_branch_label },
      { label: "월령 십신", value: contract.month_command_label },
      { label: "단일 작용", value: Number.isFinite(Number(counts.single)) ? `${counts.single}개` : "" },
      { label: "이중 작용", value: Number.isFinite(Number(counts.dual)) ? `${counts.dual}개` : "" },
      { label: "영역 작용", value: Number.isFinite(Number(counts.contextual)) ? `${counts.contextual}개` : "" },
    ],
    actionLabels,
  );
  return `
    ${renderTenGodFocusBoard(contract, detailUnit)}
    ${renderStructureReadingPath(
      [
        { target: "ten-gods-overview", title: "요약", caption: "월령 십신", primary: true },
        { target: "ten-gods-standard", title: "기준", caption: "격국과 십신" },
        { target: "ten-gods-single", title: "단일 작용", caption: "기본 역할" },
        { target: "ten-gods-dual", title: "이중 작용", caption: "생극 조합" },
        { target: "ten-gods-domains", title: "영역 적용", caption: "재물·직업 등" },
      ],
      "해석 순서",
      "월령 십신을 기준으로 단일 작용과 조합 작용을 나눕니다.",
    )}
    <div data-scroll-anchor="ten-gods-standard">${summary}</div>
    <div data-scroll-anchor="ten-gods-single">${renderContractActionList(contract.single_actions, "단일 십신 작용")}</div>
    <div data-scroll-anchor="ten-gods-dual">${renderContractActionList(contract.dual_actions, "이중 십신 작용")}</div>
    <div data-scroll-anchor="ten-gods-center">${renderContractActionList(contract.center_actions, "격국 중심 작용")}</div>
    ${renderTenGodDomainMap(contract)}
    <div data-scroll-anchor="ten-gods-evidence">${renderAnalysisDetailUnit(detailUnit, "십신 분석", "십신의 단일 작용, 이중 작용, 생극 연쇄가 운세 영역으로 닿는 지점입니다.")}</div>
  `;
}

function renderMonthDetail(contract, detailUnit, factors) {
  const phase = (contract && contract.active_hidden_phase) || {};
  const summary = renderContractSummary(
    "월령의 기준",
    "월지는 사주가 놓인 계절과 현실 조건의 중심축입니다.",
    [
      { label: "월지", value: contract && contract.month_branch_label },
      { label: "월령 오행", value: contract && contract.month_element_label },
      { label: "월령 십신", value: contract && contract.month_command_label },
      { label: "지장간 단계", value: phase.active_phase_label || phase.active_phase },
      { label: "작동 천간", value: phase.active_stem_label || phase.active_stem },
      { label: "작동 십신", value: phase.active_ten_god_label || phase.active_ten_god },
    ],
    [
      ...((contract && contract.useful_elements) || []),
      ...((contract && contract.caution_elements) || []),
      ...((contract && contract.support_fits) || []),
      ...((contract && contract.pressure_fits) || []),
    ],
  );
  return `
    ${renderMonthFocusBoard(contract, detailUnit)}
    ${renderConceptExplanationSection("월령 개념", [monthConceptCopy(contract)], "month-concept")}
    ${renderStructureReadingPath(
      [
        { target: "month-overview", title: "요약", caption: "월령의 기준", primary: true },
        { target: "month-concept", title: "개념", caption: "계절 권한" },
        { target: "month-standard", title: "월지 작용", caption: "계절과 십신" },
        { target: "month-evidence", title: "해석 근거", caption: "지지·지장간" },
      ],
      "해석 순서",
      "태어난 계절과 월지의 작용을 먼저 잡고, 지장간과 보완 기운을 구분합니다.",
    )}
    <div data-scroll-anchor="month-standard">${summary}</div>
    <div data-scroll-anchor="month-evidence">${renderAnalysisDetailUnit(detailUnit, "월령 해석", "월령과 지장간이 실제 해석의 기준이 되는 지점입니다.", factors, ["월", "월령", "월지", "계절"])}</div>
  `;
}

function signalName(signal) {
  const raw =
    (signal &&
      (signal.display_name ||
        signal.title ||
        signal.classical_name ||
        signal.combination_key ||
        signal.direction_key ||
        signal.element_direction_key ||
        signal.ten_god_direction_key ||
        signal.signal_id)) ||
    "";
  return displaySignalToken(raw);
}

const signalTokenLabels = {
  gap: "甲",
  eul: "乙",
  byeong: "丙",
  jeong: "丁",
  mu: "戊",
  gi: "己",
  gyeong: "庚",
  sin: "辛",
  im: "壬",
  gye: "癸",
  wood: "木",
  fire: "火",
  earth: "土",
  metal: "金",
  water: "水",
  heavenly_stem: "천간",
  visible_stem: "천간",
  earthly_branch: "지지",
  stem_branch: "천간·지지",
  hidden_stem: "지장간",
  visible_pair: "드러난 배합",
  stem_branch_pair: "천간·지지 배합",
  hidden_pair: "지장간 배합",
  ten_god_chain: "십신 연쇄",
  high: "강함",
  moderate: "중간",
  medium: "중간",
  low: "약함",
  positive: "길하게 작용",
  caution: "주의 필요",
  negative: "부담",
  money: "재물",
  career: "직업",
  love: "연애",
  marriage: "결혼",
  relationship: "관계",
  personality: "성향",
  honor: "명예",
  social: "대인관계",
  timing: "시기",
  bi_gyeon: "비견",
  geob_jae: "겁재",
  sik_sin: "식신",
  sang_gwan: "상관",
  pyeon_jae: "편재",
  jeong_jae: "정재",
  pyeon_gwan: "편관",
  jeong_gwan: "정관",
  pyeon_in: "편인",
  jeong_in: "정인",
};

function displaySignalToken(value) {
  const raw = String(value || "").trim();
  if (!raw) {
    return "";
  }
  if (signalTokenLabels[raw]) {
    return signalTokenLabels[raw];
  }
  if (raw.includes("->")) {
    return raw
      .split("->")
      .map((part) => displaySignalToken(part))
      .filter(Boolean)
      .join("→");
  }
  if (raw.includes("-")) {
    const parts = raw.split("-").map((part) => displaySignalToken(part)).filter(Boolean);
    if (parts.length >= 2) {
      return parts.join("");
    }
  }
  return raw.replace(/_/g, " ");
}

function displaySignalLabels(values, limit = 4) {
  return unique(
    asArray(values)
      .map(displaySignalToken)
      .filter((label) => label && !/^[a-z0-9_ -]+$/i.test(label)),
    limit,
  );
}

function timingYearLabel(item) {
  if (item == null) {
    return "";
  }
  if (typeof item === "number" || typeof item === "string") {
    const text = String(item).trim();
    const match = text.match(/\d{4}/);
    return match ? `${match[0]}년` : text;
  }
  const year = item.year ? String(item.year).match(/\d{4}/) : null;
  return year ? `${year[0]}년` : "";
}

function renderSignalCards(signals, title) {
  const visible = asArray(signals).filter((signal) => signal && signalName(signal)).slice(0, 4);
  if (!visible.length) {
    return "";
  }
  return `
    <section class="paper-card">
      <h2>${escapeHtml(title)}</h2>
      <div class="factor-grid">
        ${visible
          .map((signal) => {
            const labels = displaySignalLabels([signal.layer, signal.strength, signal.polarity, ...(signal.domain_links || [])], 4);
            const body =
              signal.summary_interpretation ||
              signal.interpretation ||
              signal.combined_interpretation ||
              signal.core_interpretation ||
              signal.element_interpretation ||
              signal.decision_reason ||
              signal.classical_theory ||
              "성향과 사건이 어느 영역에서 두드러지는지를 가르는 기준입니다.";
            return `
              <article class="factor-block">
                <header><strong>${escapeHtml(signalName(signal))}</strong></header>
                <p>${escapeHtml(compactText(body, 112))}</p>
                ${labels.length ? `<div class="tag-row">${labels.map((label) => `<span>${escapeHtml(label)}</span>`).join("")}</div>` : ""}
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function renderElementContract(contract) {
  if (!contract) {
    return "";
  }
  return `
    ${renderContractSummary(
      "오행·십신 적용값",
      "오행 분포에 그치지 않고, 배합의 방향과 십신 역할이 드러나는 지점을 판별합니다.",
      [],
      contract.detail_source_layers || [],
    )}
    ${renderSignalCards(contract.element_combination_signals, "오행 배합")}
    ${renderSignalCards(contract.integrated_saju_signals, "오행·십신 통합")}
  `;
}

function signalTraitBody(signal, fallback) {
  const traits = textList(signal && signal.trait_keywords, 3);
  if (traits.length) {
    return `${displayJoin(traits, " · ")} 쪽으로 성향과 사건이 드러납니다.`;
  }
  const domains = displaySignalLabels(signal && signal.domain_links, 4);
  if (domains.length) {
    return `${displayJoin(domains, " · ")} 영역에서 실제 작용이 두드러집니다.`;
  }
  const body =
    signal &&
    (signal.summary_interpretation ||
      signal.interpretation ||
      signal.combined_interpretation ||
      signal.core_interpretation ||
      signal.element_interpretation);
  return body ? compactText(body, 78) : fallback;
}

function renderElementFocusBoard(balance, contract, detailUnit) {
  const values = asArray(balance && balance.values);
  if (!values.length) return "";
  const top = balance.top || values[0];
  const low = values.reduce((picked, item) => (Number(item.percent) < Number(picked.percent) ? item : picked), values[0]);
  const topMeta = elementLabels[top.key] || {};
  const lowMeta = elementLabels[low.key] || {};
  const combo = asArray(contract && contract.element_combination_signals)[0];
  const integrated = asArray(contract && contract.integrated_saju_signals)[0];
  const tenGod = asArray(contract && contract.ten_god_interaction_signals)[0];
  const integratedTitle = displayJoin([displaySignalToken(integrated && integrated.element_direction_key), displaySignalToken(integrated && integrated.ten_god_direction_key)]) || signalName(integrated);
  const tenGodTitle = displaySignalToken(tenGod && tenGod.direction_key) || signalName(tenGod);
  const lead = detailUnit && detailUnit.lead
    ? compactText(detailUnit.lead, 126)
    : "오행은 성향의 결을 만들고, 십신은 그 성향이 사회적 역할로 드러나는 방식을 정합니다.";
  return renderStructureFocusCard({
    anchor: "elements-overview",
    tone: "elements",
    icon: "五",
    eyebrow: "오행 요약",
    title: topMeta.ko ? `${topMeta.ko} 기운 ${top.percent}%` : "오행 분석",
    lead,
    cards: [
      {
        label: "중심 오행",
        title: topMeta.han ? `${topMeta.ko}(${topMeta.han})` : "강한 오행",
        body: topMeta.meaning ? `${topMeta.meaning} 성향이 사주의 기본 기질로 먼저 드러납니다.` : "가장 강하게 드러나는 오행입니다.",
      },
      {
        label: "부족 오행",
        title: lowMeta.han ? `${lowMeta.ko}(${lowMeta.han})` : "약한 오행",
        body: lowMeta.meaning ? `${lowMeta.meaning} 성향이 약해질 때 판단의 균형이 흔들릴 수 있습니다.` : "상대적으로 부족한 오행입니다.",
      },
      {
        label: "오행 배합",
        title: signalName(combo) || "배합",
        body: signalTraitBody(combo, "오행끼리 만나는 방식이 성향과 사건의 질감을 만듭니다."),
      },
      {
        label: "십신 결합",
        title: integratedTitle || tenGodTitle || "오행·십신",
        body: integrated
          ? "오행의 생극이 실제 역할과 사건 방향으로 이어지는 지점입니다."
          : signalTraitBody(tenGod, "오행의 성향이 사회적 역할로 드러나는 지점입니다."),
      },
    ],
  });
}

function renderElementDetail(balance, detailUnit, elementContract) {
  const elementConcepts = [
    ...asArray(elementContract && elementContract.element_combination_signals).slice(0, 2).map(elementCombinationConceptCopy),
    ...asArray(elementContract && elementContract.integrated_saju_signals).slice(0, 1).map(elementCombinationConceptCopy),
  ].filter(Boolean);
  return `
    ${renderElementFocusBoard(balance, elementContract, detailUnit)}
    ${renderConceptExplanationSection("오행 배합 개념", elementConcepts, "elements-concept")}
    ${renderStructureReadingPath(
      [
        { target: "elements-overview", title: "요약", caption: "중심 오행", primary: true },
        { target: "elements-concept", title: "개념", caption: "물상과 배합" },
        { target: "elements-balance", title: "오행 분포", caption: "강약과 보완" },
        { target: "elements-combination", title: "배합", caption: "오행·십신" },
      ],
      "해석 순서",
      "강한 오행과 약한 오행을 먼저 가른 뒤, 배합과 십신 결합을 함께 판별합니다.",
    )}
    <section class="paper-card" data-scroll-anchor="elements-balance">
      <h2>오행 분석</h2>
      <p>오행은 성향의 결을 만들고, 십신은 그 성향이 사회적 역할로 드러나는 방식을 정합니다.</p>
      <div class="element-board" style="margin-top: 18px;">
        <div class="element-chart" style="${balance.values.map((item) => `--${item.key}:${item.percent}`).join(";")}">
          <strong>${elementLabels[balance.top.key].ko}<small>${balance.top.percent}%</small></strong>
        </div>
        <div class="element-bars">${balance.values.map(renderElementRow).join("")}</div>
      </div>
      <div class="detail-grid">
        ${balance.values
          .map((item) => {
            const meta = elementLabels[item.key];
            return `
              <article class="detail-block">
                <strong>${meta.ko}(${meta.han})의 작용</strong>
                <p>${meta.ko}(${meta.han})은 ${meta.meaning} 쪽으로 성향을 기울게 합니다. 이 명식에서는 ${item.percent}%로 잡힙니다.</p>
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
    <div data-scroll-anchor="elements-combination">${renderElementContract(elementContract)}</div>
    <div data-scroll-anchor="elements-evidence">${detailUnit ? renderAnalysisDetailUnit(detailUnit, "오행 배합", "오행 배합과 십신 역할이 실제 성향과 운세 영역으로 닿는 지점입니다.") : ""}</div>
  `;
}

function renderFactorCategory(title, lead, factors, keywords) {
  const matched = factors.filter((factor) => {
    const text = [factor.layer, factor.source_label, factor.heading, factor.lead, ...(factor.domain_labels || [])].join(" ");
    return keywords.some((keyword) => text.includes(keyword));
  });
  const picked = matched.length ? matched : factors.slice(0, 4);
  return `
    <section class="paper-card">
      <h2>${escapeHtml(title)}</h2>
      <p>${escapeHtml(lead)}</p>
      <div class="factor-grid">
        ${picked.map(renderFactorBlock).join("")}
      </div>
    </section>
  `;
}

function renderFactorBlock(factor) {
  const labels = unique(factor.domain_labels || [], 4);
  return `
    <article class="factor-block">
      <header>
        <strong>${escapeHtml(factor.heading || factor.source_label || "해석 근거")}</strong>
      </header>
      <p>${escapeHtml(firstSentence(factor.lead, "명식에서 확인된 요소입니다."))}</p>
      <div class="tag-row">
        ${labels.map((label) => `<span>${escapeHtml(label)}</span>`).join("")}
      </div>
    </article>
  `;
}

function renderTemperatureContract(contract) {
  if (!contract) {
    return "";
  }
  return `
    ${renderContractSummary(
      "조후 적용값",
      "계절, 온도, 건습, 필요한 오행을 기준으로 체감 기운을 정리했습니다.",
      [
        { label: "계절", value: contract.season_label },
        { label: "온도", value: contract.temperature_balance },
        { label: "건습", value: contract.moisture_balance },
        { label: "일간 강약", value: contract.day_master_strength },
      ],
      [
        ...(contract.useful_elements || []),
        ...(contract.caution_elements || []),
        ...(contract.dominant_elements || []),
      ],
    )}
    ${renderSignalCards(contract.cycle_regulation_signals, "상생상극 조절")}
  `;
}

function renderTemperatureFocusBoard(balance, contract, detailUnit) {
  if (!contract) return "";
  const fireItem = balance.values.find((item) => item.key === "fire");
  const waterItem = balance.values.find((item) => item.key === "water");
  const fire = (fireItem && fireItem.percent) || 0;
  const water = (waterItem && waterItem.percent) || 0;
  const useful = textList(contract.useful_elements || contract.climate_needs || [], 4);
  const caution = textList(contract.caution_elements || contract.dominant_elements || [], 4);
  const season = displayToken(contract.season_label || contract.season);
  const monthElement = displayToken(contract.month_element_label || contract.month_element);
  const temperature = displayToken(contract.temperature_balance);
  const moisture = displayToken(contract.moisture_balance);
  const title = displayJoin([season, temperature, moisture]) || "조후";
  const lead = detailUnit && detailUnit.lead
    ? compactText(detailUnit.lead, 126)
    : "조후는 온도와 건습을 통해 사주의 체감 기운을 판별합니다.";
  return renderStructureFocusCard({
    anchor: "temperature-overview",
    tone: "temperature",
    icon: "水",
    eyebrow: "조후 요약",
    title,
    lead,
    cards: [
      {
        label: "계절 기준",
        title: season || "계절",
        body: monthElement ? `${monthElement} 월령이 체감 기운의 출발점입니다.` : "월령의 계절감이 사주의 체감 속도를 정합니다.",
      },
      {
        label: "온도 균형",
        title: temperature || "온도",
        body: `화 ${fire}%와 수 ${water}%의 차이로 표현력과 저장성이 갈립니다.`,
      },
      {
        label: "필요 오행",
        title: useful.length ? displayJoin(useful, " / ") : "보완 기운",
        body: "이 기운이 들어올 때 판단, 실행, 회복의 질이 달라집니다.",
      },
      {
        label: "주의 기운",
        title: caution.length ? displayJoin(caution, " / ") : "과다 기운",
        body: "이미 강한 기운이 더해지면 같은 격국도 부담으로 바뀔 수 있습니다.",
      },
    ],
  });
}

function renderTemperatureDetail(balance, factors, detailUnit, temperatureContract) {
  const fireItem = balance.values.find((item) => item.key === "fire");
  const waterItem = balance.values.find((item) => item.key === "water");
  const fire = (fireItem && fireItem.percent) || 0;
  const water = (waterItem && waterItem.percent) || 0;
  const warmState = fire > water + 8 ? "따뜻한 기운이 앞서는 편입니다." : water > fire + 8 ? "차가운 기운이 앞서는 편입니다." : "차가움과 따뜻함이 비교적 맞물려 있습니다.";
  return `
    ${renderTemperatureFocusBoard(balance, temperatureContract, detailUnit)}
    ${renderStructureReadingPath(
      [
        { target: "temperature-overview", title: "요약", caption: "체감 기운", primary: true },
        { target: "temperature-balance", title: "온도·건습", caption: "화와 수의 균형" },
        { target: "temperature-standard", title: "조후 기준", caption: "필요 오행" },
        { target: "temperature-evidence", title: "해석 근거", caption: "생극 조절" },
      ],
      "해석 순서",
      "체감 기운을 먼저 잡고, 필요한 오행과 생극 조절을 함께 판별합니다.",
    )}
    <section class="paper-card" data-scroll-anchor="temperature-balance">
      <h2>조후 분석</h2>
      <p>${warmState} 조후는 사주의 온도와 건습을 살피는 층입니다. 같은 격국이라도 조후가 다르면 성향과 운의 체감이 달라집니다.</p>
      <div class="topic-grid">
        <article class="topic-card">
          <header><strong>따뜻함</strong><em>${fire}%</em></header>
          <p>표현력, 활력, 명예욕, 추진의 온도와 연결됩니다.</p>
        </article>
        <article class="topic-card">
          <header><strong>차가움</strong><em>${water}%</em></header>
          <p>지혜, 관찰, 유통, 저장, 감정의 깊이와 연결됩니다.</p>
        </article>
      </div>
    </section>
    <div data-scroll-anchor="temperature-standard">${renderTemperatureContract(temperatureContract)}</div>
    <div data-scroll-anchor="temperature-evidence">${renderAnalysisDetailUnit(detailUnit, "조후 해석 요소", "조후와 함께 작동하는 월령, 오행, 생극 작용입니다.", factors, ["조후", "기운", "오행", "월령"])}</div>
  `;
}

function renderContextualFocusBoard(contract, detailUnit) {
  if (!contract) return "";
  const anchor = contract.anchor || {};
  const element = contract.element_context || {};
  const actions = asArray(contract.contextual_actions);
  const domains = asArray(contract.domain_synthesis);
  const mainAction = actions[0];
  const topDomain = domains
    .filter((item) => Number.isFinite(Number(item.net)))
    .sort((a, b) => Number(b.net) - Number(a.net))[0] || domains[0];
  const useful = textList(element.useful_element_labels || element.climate_needs || [], 3);
  const caution = textList(element.caution_element_labels || element.dominant_elements || [], 3);
  const concept = mainAction ? contextualConceptCopy(mainAction) : null;
  const title = displayJoin([anchor.month_branch, anchor.primary_ten_god_label || anchor.primary_pattern_label, anchor.season_label]) || "종합 근거";
  const lead = detailUnit && detailUnit.lead
    ? compactText(detailUnit.lead, 126)
    : "격국, 월령, 오행, 조후를 합쳐 최종 판단의 근거를 정리합니다.";
  return renderStructureFocusCard({
    anchor: "contextual-overview",
    tone: "contextual",
    icon: "綜",
    eyebrow: "종합 근거",
    title,
    lead,
    cards: [
      {
        label: "월령 기준",
        title: displayJoin([anchor.primary_ten_god_label || anchor.primary_pattern_label, anchor.month_branch]) || "월령의 기준",
        body: "월령을 중심에 두고 격국과 조후를 함께 대조합니다.",
      },
      {
        label: "중심 개념",
        title: concept ? concept.name : "십신 작용",
        body: concept ? compactText(concept.body, 138) : "가장 강하게 작동하는 십신 조합입니다.",
      },
      {
        label: "필요 기준",
        title: displayJoin(useful, " / ") || "오행·조후",
        body: useful.length && caution.length
          ? `이 기운은 필요한 기준이고, ${displayJoin(caution, " / ")} 기운은 과해질 때 부담으로 잡습니다.`
          : useful.length
            ? "이 기운이 갖춰질수록 전체 흐름이 안정됩니다."
            : "필요 오행과 부담 오행이 최종 강약을 조정합니다.",
      },
    ],
  });
}

function contextualActionScore(action) {
  if (!action) return 0;
  const profile = action.operation_profile || {};
  const candidates = [
    action.salience_score,
    action.net_score,
    action.priority,
    action.support_score,
    action.weight,
    profile.salience_score,
    profile.net_score,
    profile.structure_score,
  ].map(Number).filter(Number.isFinite);
  return candidates.length ? Math.max(...candidates.map((score) => Math.abs(score))) : 0;
}

function contextualActionKey(action) {
  return normalizedConceptKey(
    [
      action && (action.action_name || action.pattern_label || action.rule_key || action.pair_name || action.title),
      action && JSON.stringify(action.branch_relation_summary || ""),
    ]
      .filter(Boolean)
      .join("|"),
  );
}

function splitContextualActions(actions) {
  const seen = new Set();
  const normalized = asArray(actions)
    .filter(Boolean)
    .filter((action) => {
      const key = contextualActionKey(action);
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .map((action, index) => ({ action, index, score: contextualActionScore(action) }))
    .sort((a, b) => (b.score - a.score) || (a.index - b.index));
  if (!normalized.length) {
    return { core: [], partial: [] };
  }
  const threshold = normalized.length >= 5 ? 70 : 62;
  const core = [];
  const partial = [];
  normalized.forEach((item, order) => {
    const groups = asArray(item.action.group_labels).map(displayToken).join(" ");
    const isAnchored = /월령|격국|조후|지지|오행/.test(groups);
    if (order < 2 || item.score >= threshold || isAnchored) {
      core.push(item.action);
    } else {
      partial.push(item.action);
    }
  });
  if (!partial.length && core.length > 3) {
    return { core: core.slice(0, 3), partial: core.slice(3) };
  }
  return { core, partial };
}

function renderContextualActionConceptCard(action) {
  const concept = contextualConceptCopy(action);
  const labels = unique(concept.keywords.map(displayToken), 7);
  return `
    <article class="factor-block">
      <header><strong>${escapeHtml(concept.name)}</strong></header>
      <p>${escapeHtml(compactText(concept.body, 118))}</p>
      ${labels.length ? `<div class="tag-row">${labels.map((label) => `<span>${escapeHtml(label)}</span>`).join("")}</div>` : ""}
    </article>
  `;
}

function renderContextualActionSection(title, lead, actions, anchor) {
  const visible = asArray(actions).filter(Boolean);
  if (!visible.length) return "";
  const leadText = productText(String(lead || "").trim());
  return `
    <section class="paper-card" data-scroll-anchor="${escapeHtml(anchor)}">
      <h2>${escapeHtml(title)}</h2>
      ${leadText ? `<p>${escapeHtml(leadText)}</p>` : ""}
      <div class="factor-grid">
        ${visible.map(renderContextualActionConceptCard).join("")}
      </div>
    </section>
  `;
}

function keywordProfileTitle(profile) {
  const name = displayToken(profile && profile.name);
  const hanja = displayToken(profile && profile.hanja);
  if (hanja && name) return `${hanja} · ${name}`;
  return name || hanja || "보조 근거";
}

function renderKeywordProfileGroups(profile) {
  const groups = asArray(profile && profile.groups)
    .map((group) => {
      const tag = displayToken(group && group.tag);
      const words = unique(asArray(group && group.words).map(displayToken).filter(Boolean), 6);
      return { tag, words };
    })
    .filter((group) => group.tag && group.words.length)
    .slice(0, 5);
  if (!groups.length) return "";
  return `
    <div class="keyword-profile-list">
      ${groups
        .map(
          (group) => `
            <div class="keyword-profile-row">
              <b>${escapeHtml(group.tag)}</b>
              <span>${group.words.map(escapeHtml).join(" · ")}</span>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderKeywordProfileCard(profile) {
  const title = keywordProfileTitle(profile);
  const meta = displayToken(profile && (profile.type || profile.category));
  const groups = renderKeywordProfileGroups(profile);
  if (!groups) return "";
  return `
    <article class="factor-block keyword-profile-card">
      <header>
        <strong>${escapeHtml(title)}</strong>
        ${meta ? `<em>${escapeHtml(meta)}</em>` : ""}
      </header>
      ${groups}
    </article>
  `;
}

function renderKeywordProfileSection(title, profiles, anchor) {
  const visible = asArray(profiles)
    .filter(Boolean)
    .map(renderKeywordProfileCard)
    .filter(Boolean);
  if (!visible.length) return "";
  return `
    <section class="paper-card" data-scroll-anchor="${escapeHtml(anchor)}">
      <h2>${escapeHtml(title)}</h2>
      <div class="factor-grid">
        ${visible.join("")}
      </div>
    </section>
  `;
}

function contextualGroupObjectToArray(groupObject) {
  if (!groupObject) return [];
  return contextualKeywordGroupOrder
    .map((tag) => {
      const words = unique(asArray(groupObject[tag]).map(displayToken).filter(Boolean), 6);
      return { tag, words };
    })
    .filter((group) => group.words.length);
}

function contextualGroupBankForName(name) {
  const bankKey = contextualBankKeyForName(name, contextualConceptGroupBank);
  return bankKey ? contextualConceptGroupBank[bankKey] : null;
}

function deriveContextualGroupsFromKeywords(keywords) {
  const words = unique(asArray(keywords).map(displayToken).filter(Boolean), 18);
  if (!words.length) return [];
  const slices = [
    ["기질", words.slice(0, 3)],
    ["재능", words.slice(3, 6)],
    ["관계", words.slice(6, 9)],
    ["직업", words.slice(9, 12)],
    ["리스크", words.slice(12, 15)],
  ];
  return slices
    .map(([tag, values]) => ({ tag, words: values.filter(Boolean) }))
    .filter((group) => group.words.length);
}

function normalizeContextualKeywordGroups(source, fallbackKeywords = []) {
  const sourceGroups = asArray(source && source.groups);
  const grouped = contextualKeywordGroupOrder
    .map((tag) => {
      const directWords = asArray(source && source[tag]);
      const groupWords = sourceGroups
        .filter((group) => displayToken(group && group.tag) === tag)
        .flatMap((group) => asArray(group && group.words));
      const words = unique([...directWords, ...groupWords].map(displayToken).filter(Boolean), 6);
      return { tag, words };
    })
    .filter((group) => group.words.length);
  if (grouped.length) return grouped;
  return deriveContextualGroupsFromKeywords(fallbackKeywords);
}

function contextualConceptGroups(concept) {
  const name = concept && concept.name;
  const bank = contextualGroupBankForName(name);
  if (bank) return contextualGroupObjectToArray(bank);
  return deriveContextualGroupsFromKeywords(concept && concept.keywords);
}

function contextualEvidenceCardKey(card) {
  return normalizedConceptKey((card && card.dedupeKey) || (card && card.title));
}

function contextualActionGroups(action, concept) {
  const groups = contextualConceptGroups(concept);
  const wordCount = groups.reduce((count, group) => count + asArray(group && group.words).length, 0);
  if (wordCount >= 3) return groups;
  const titleBank = contextualGroupBankForName(contextualActionDisplayTitle(action, concept));
  return titleBank ? contextualGroupObjectToArray(titleBank) : groups;
}

function contextualActionEvidenceCard(action) {
  if (!action) return null;
  const concept = contextualConceptCopy(action, { fullBody: true });
  const bankKey = contextualBankKeyForName(concept && concept.name, contextualConceptBank);
  const body = contextualActionDescription(action, concept);
  const groups = contextualActionGroups(action, concept);
  const keywordCount = groups.reduce((count, group) => count + asArray(group && group.words).length, 0);
  if (!body && keywordCount < 3) return null;
  return {
    sourceType: "action",
    kind: "action",
    evidenceSection: "action",
    dedupeKey: bankKey || concept.name,
    title: contextualActionDisplayTitle(action, concept),
    meta: displayJoin([displayToken(action.pattern_label), "십신 배합"]).replace(/^ · /, ""),
    body,
    groups,
    score: contextualActionScore(action),
  };
}

function contextualEvidenceContentKey(card) {
  if (!card || card.sourceType !== "action") return "";
  const body = normalizedConceptKey(card.body);
  const words = asArray(card.groups)
    .flatMap((group) => asArray(group && group.words))
    .map(normalizedConceptKey)
    .filter(Boolean)
    .sort()
    .join("|");
  return body && words ? `${body}::${words}` : "";
}

function contextualActionPairKey(card) {
  if (!card || card.evidenceSection !== "action") return "";
  const actors = displayToken(card.title)
    .split("·")
    .map(displayToken)
    .filter(Boolean);
  const tenGodLabels = new Set([
    "비견", "겁재", "식신", "상관", "편재",
    "정재", "편관", "정관", "편인", "정인",
  ]);
  if (actors.length !== 2 || actors.some((actor) => !tenGodLabels.has(actor))) return "";
  return [...actors].sort().join("·");
}

function keywordProfileDescription(profile, title) {
  return myungriDescriptionLookup(
    title,
    profile && profile.name,
    profile && profile.hanja,
    profile && profile.type,
    profile && profile.category,
    profile && profile.kind,
    profile && profile.branch_labels,
  );
}

function keywordProfileEvidenceCard(profile) {
  if (!profile) return null;
  const title = keywordProfileTitle(profile);
  const rawKind = String(profile.kind || "");
  const meta = displayJoin([displayToken(profile.type || profile.category), displayToken(profile.hanja)], " · ");
  const keywords = asArray(profile.groups).flatMap((group) => asArray(group && group.words));
  return {
    sourceType: "keyword",
    kind: rawKind || displayToken(profile.kind) || "keyword",
    evidenceSection: contextualKeywordEvidenceSection(profile, title),
    title,
    meta,
    body: keywordProfileDescription(profile, title),
    groups: normalizeContextualKeywordGroups(profile, keywords),
    score: Number(profile.priority) || 0,
  };
}

function conceptEvidenceCard(concept) {
  if (!concept || !concept.name || !concept.body) return null;
  const title = contextualConceptEvidenceTitle(concept);
  const body = contextualConceptEvidenceBody(concept, title);
  if (!body) return null;
  const evidenceSection = contextualConceptEvidenceSection(concept.name, concept.kind);
  const groups = evidenceSection === "action"
    ? contextualConceptGroups(concept)
    : contextualConceptEvidenceGroups(concept, title);
  return {
    sourceType: "concept",
    kind: String(concept.kind || "concept"),
    evidenceSection,
    dedupeKey: concept.name,
    title,
    meta: contextualConceptEvidenceMeta(concept, title),
    body,
    groups,
    score: 0,
  };
}

function contextualConceptDisplayTitle(name) {
  const title = displayToken(name);
  if (/^[목화토금수]{2}$/.test(title)) return `${title} 배합`;
  if (/^월지\s.+기준$/.test(title)) return "월령·조후 기준";
  return title || "구조 근거";
}

const branchEvidenceTexture = {
  子: ["정보 감각", "현금 흐름", "정산 감각", "숨은 변수", "감정 저장", "유통성"],
  丑: ["축적", "검증", "생활 기반", "보존성", "묵은 책임", "현실 감각"],
  寅: ["시작력", "확장성", "기획", "성장 욕구", "진입 기회", "초기 추진"],
  卯: ["관계 감각", "조율", "미감", "선별", "유연성", "인연성"],
  辰: ["조정력", "전환기", "저장된 변수", "기반 재편", "현실 조율", "변화의 준비"],
  巳: ["표현", "기술성", "노출", "판단 속도", "전문성", "열기"],
  午: ["명예", "확장", "표현력", "사회적 노출", "활력", "결정성"],
  未: ["생활 기준", "보호", "정리", "가족성", "축적", "완충력"],
  申: ["실무", "기술", "이동성", "거래", "분석", "현장성"],
  酉: ["평판", "완성도", "선별력", "금전 감각", "정교함", "평가"],
  戌: ["책임", "생활 기준", "보존성", "자기 기준", "내부 불만", "보호 욕구"],
  亥: ["직관", "정보 확장", "이동성", "학습", "연결성", "내면성"],
};

const tenGodEvidenceMeaning = {
  비견: "자기 기준과 독립성",
  겁재: "경쟁, 분배, 공동 책임",
  식신: "기술, 결과물, 꾸준한 생산",
  상관: "표현, 문제 제기, 방식의 변형",
  편재: "거래성, 현금 흐름, 외부 기회",
  정재: "소유권, 정산, 고정 수입",
  편관: "압박, 경쟁, 위험 대응",
  정관: "책임, 규칙, 공식 평가",
  편인: "특수 지식, 정보 해석, 독자적 판단",
  정인: "자격, 보호, 문서, 학습 기반",
};

const branchReadingForParticle = {
  子: "자",
  丑: "축",
  寅: "인",
  卯: "묘",
  辰: "진",
  巳: "사",
  午: "오",
  未: "미",
  申: "신",
  酉: "유",
  戌: "술",
  亥: "해",
};

function particleBaseText(text) {
  const value = displayToken(text);
  return branchReadingForParticle[value] || value;
}

function evidenceTopicParticle(text) {
  return subjectParticle(particleBaseText(text));
}

function evidenceNominativeParticle(text) {
  return nominativeParticle(particleBaseText(text));
}

function evidenceObjectParticle(text) {
  const value = particleBaseText(text);
  const chars = Array.from(value);
  const last = chars[chars.length - 1];
  if (!last) return "을";
  const code = last.charCodeAt(0);
  if (code < 0xac00 || code > 0xd7a3) return "을";
  return (code - 0xac00) % 28 === 0 ? "를" : "을";
}

function tenGodEvidenceText(label) {
  const text = displayToken(label);
  return tenGodEvidenceMeaning[text] || text || "해당 작용";
}

function parseMonthGovernanceEvidence(rawName, body) {
  const raw = displayToken(rawName);
  const source = displayToken(body);
  const branch = (raw.match(/^([子丑寅卯辰巳午未申酉戌亥])월/) || [])[1] || "";
  const gyeok = (raw.match(/([가-힣]+격)/) || source.match(/([가-힣]+격)/) || [])[1] || "";
  const active = (source.match(/월률분야는[^.]*\(([가-힣]+)\)입니다/) || [])[1] || "";
  const command = (source.match(/월지 본기\s+[^()]*\(([가-힣]+)\)/) || [])[1] || gyeok.replace(/격$/, "");
  const commandStem = (source.match(/월지 본기\s+([甲乙丙丁戊己庚辛壬癸])/) || [])[1] || "";
  const activeSegment = (source.match(/월률분야는\s*([^.]+?)입니다/) || [])[1] || "";
  const activeStem = (activeSegment.match(/([甲乙丙丁戊己庚辛壬癸])\([가-힣]+\)/) || [])[1] || "";
  const activePhase = (activeSegment.match(/(여기|중기|정기)\(/) || [])[1] || "";
  return { branch, gyeok, active, command, commandStem, activeStem, activePhase };
}

function parseBranchRealityEvidence(rawName, body) {
  const raw = displayToken(rawName);
  const source = displayToken(body);
  const match = raw.match(/^(월지|일지|시지|연지)\s*([子丑寅卯辰巳午未申酉戌亥])의 현실 작용$/);
  const position = match ? match[1] : "";
  const branch = match ? match[2] : "";
  const action = (source.match(/에서\s+([가-힣]+)\s+([가-힣]+)\s+작용/) || [])[2] || "";
  const hidden = (source.match(/지장간\s+(.+?)(?:은|는)\s+시간이/) || [])[1] || "";
  const protruded = (source.match(/그중\s+(.+?)(?:은|는|이|가)\s+천간에 투출/) || [])[1] || "";
  return { position, branch, action, hidden, protruded };
}

function contextualConceptEvidenceTitle(concept) {
  const raw = displayToken(concept && concept.name);
  const body = displayToken(concept && concept.body);
  if (/월령 심화/.test(raw)) {
    const parsed = parseMonthGovernanceEvidence(raw, body);
    if (parsed.active) return parsed.active;
    return "월률분야";
  }
  const branch = parseBranchRealityEvidence(raw, body);
  if (branch.position && branch.branch) {
    const label = {
      연지: "초년 배경",
      월지: "사회 환경",
      일지: "관계 기준",
      시지: "후반 흐름",
    }[branch.position] || "현실 작용";
    return `${branch.position} ${branch.branch} · ${label}`;
  }
  return contextualConceptDisplayTitle(raw);
}

function contextualConceptEvidenceMeta(concept, title) {
  const raw = displayToken(concept && concept.name);
  const rawKind = String((concept && concept.kind) || "");
  if (rawKind.includes("branch_pair")) return "지지 배합";
  if (rawKind.includes("element_combination")) return "천간 배합";
  if (/^[甲乙丙丁戊己庚辛壬癸]{2}\s*[가-힣]+\+[가-힣]+$/.test(raw)) return "천간 배합";
  if (/^[子丑寅卯辰巳午未申酉戌亥]\(.+\)월$/.test(raw)) return "월령";
  if (/월령 심화/.test(raw)) return "월률분야";
  if (/격/.test(title)) return "격국";
  if (/월령·조후|조후/.test(title)) return "조후 기준";
  if (/^[연월일시]지\s/.test(title)) return "지지·지장간";
  if (/배합/.test(title)) return "오행 배합";
  if (/^(비겁극재|재극인|재생관|식상생재|관인상생|식신제살|인성제식|상관견관)$/.test(raw)) return "십신 작용";
  return "구조 근거";
}

function contextualMonthGovernanceBody(concept) {
  const parsed = parseMonthGovernanceEvidence(concept && concept.name, concept && concept.body);
  if (!parsed.gyeok && !parsed.command) return "";
  const commandMeaning = tenGodEvidenceText(parsed.command);
  const activeMeaning = tenGodEvidenceText(parsed.active);
  if (parsed.active && parsed.active !== parsed.command) {
    const commandDisplay = displayJoin([parsed.commandStem, parsed.command ? `(${parsed.command})` : ""], "");
    const activeDisplay = displayJoin([
      parsed.activePhase,
      parsed.activeStem,
      parsed.active ? `(${parsed.active})` : "",
    ], " ").replace(/\s+\(/g, "(");
    return `${parsed.branch ? `${parsed.branch}월의 ` : ""}월지 본기 ${commandDisplay || parsed.command}${evidenceTopicParticle(parsed.command)} ${commandMeaning}${evidenceObjectParticle(commandMeaning)} 월령의 바탕으로 둡니다. 출생 절기 구간에서는 ${activeDisplay || parsed.active}${evidenceNominativeParticle(parsed.active)} 먼저 작동합니다. 이는 별도의 격을 하나 더 세운다는 뜻이 아니라, 같은 월령 안에서 ${activeMeaning}${evidenceNominativeParticle(activeMeaning)} 실제 반응의 입구가 된다는 뜻입니다.`;
  }
  return "";
}

function contextualSeasonEvidenceBody(concept) {
  const raw = displayToken(concept && concept.name);
  const body = displayToken(concept && concept.body);
  const branch = (raw.match(/월지\s*([子丑寅卯辰巳午未申酉戌亥])/) || [])[1] || "";
  const needed = (body.match(/필요한 오행은\s*([^.]+?)입니다/) || [])[1] || "";
  if (branch === "子") {
    return `子월은 수기가 강한 계절이라 정보, 현금 흐름, 감정의 저장성이 커집니다. 이 명식에서 보완축은 ${needed || "화와 토"}입니다. 화는 드러남과 활력, 성과 표시를 열고 토는 기준과 보존, 현실화를 맡습니다. 화가 약하면 알아도 드러내는 속도가 늦고, 토가 약하면 벌어도 정리와 보존이 흔들립니다. 따라서 돈과 정보를 읽는 힘이 실제 결과로 남으려면 표현력과 정리 기준이 함께 필요합니다.`;
  }
  if (needed) {
    return `${branch || "월지"}월의 계절 기운을 기준으로 보완해야 할 오행은 ${needed}입니다. 조후는 오행의 개수보다 기운이 현실에서 무리 없이 작동하는 조건을 정합니다. 같은 격국이라도 과열, 냉각, 건조, 습함의 정도에 따라 판단 속도와 실행력, 회복력이 달라집니다.`;
  }
  return "";
}

function contextualBranchDomainSentence(position, branch) {
  if (position === "월지" && branch === "子") return "사회에서는 돈과 정보의 흐름, 정산 기준, 직업 환경의 변화를 빨리 읽는 쪽으로 나타납니다.";
  if (position === "시지" && branch === "子") return "후반으로 갈수록 장기 수입, 보유 자산, 현금 흐름을 안정적으로 관리하는 문제가 중요해집니다.";
  if (position === "일지" && branch === "戌") return "가까운 관계에서는 감정만으로 움직이기보다 생활 기준, 책임 분담, 서로의 독립성이 먼저 문제로 올라옵니다.";
  if (position === "월지") return "사회 환경과 직업의 바탕에서 반복해서 체감되는 현실 조건입니다.";
  if (position === "일지") return "가까운 관계와 결혼 생활에서 반복해서 드러나는 생활 조건입니다.";
  if (position === "시지") return "후반 성취와 장기 결과에서 점점 중요해지는 현실 조건입니다.";
  if (position === "연지") return "초년 배경과 바깥 관계에서 기본 분위기를 만드는 조건입니다.";
  return "현실에서 반복해서 작동하는 조건입니다.";
}

function contextualBranchActionSentence(position, action) {
  const label = displayToken(action);
  const base = {
    정재: "정재가 놓인 영역은 돈의 크기보다 소유권, 정산, 안정된 수입의 기준이 중요합니다.",
    편재: "편재가 놓인 영역은 고정된 틀보다 거래, 유통, 기회 포착, 현금의 이동성이 먼저 드러납니다.",
    비견: "비견이 놓인 영역은 자기 기준, 독립성, 동등한 몫에 대한 감각이 강하게 작동합니다.",
    겁재: "겁재가 놓인 영역은 경쟁, 분배, 공동 책임, 사람 사이의 몫 문제가 민감하게 작동합니다.",
    식신: "식신이 놓인 영역은 꾸준히 만든 결과물, 생활 기술, 오래 반복한 실력이 힘이 됩니다.",
    상관: "상관이 놓인 영역은 표현, 문제 제기, 기존 방식의 변형이 강하게 드러납니다.",
    정관: "정관이 놓인 영역은 규칙, 책임, 공식 평가, 신뢰를 지키는 태도가 중요합니다.",
    편관: "편관이 놓인 영역은 압박, 경쟁, 위험 대응, 강한 책임을 처리하는 방식이 관건입니다.",
    정인: "정인이 놓인 영역은 보호, 자격, 문서, 학습 기반이 안정감을 만듭니다.",
    편인: "편인이 놓인 영역은 특수 지식, 정보 해석, 독자적 판단이 강하게 작동합니다.",
  }[label];
  if (!base) return "";
  if (position === "일지" && (label === "비견" || label === "겁재")) {
    return `${base} 관계에서는 상대에게 맞추는 힘만큼 자신의 기준을 어떻게 세우느냐가 핵심입니다.`;
  }
  if (position === "월지" && (label === "정재" || label === "편재")) {
    return `${base} 사회생활에서는 수입의 발생보다 정산, 명의, 계약 조건을 어떻게 확정하느냐가 더 크게 작용합니다.`;
  }
  if (position === "시지" && (label === "정재" || label === "편재")) {
    return `${base} 후반 운에서는 일시적인 수입보다 현금 흐름과 보유 자산의 안정성이 더 중요해집니다.`;
  }
  return base;
}

function contextualHiddenStemsSentence(hidden, protruded) {
  const hiddenItems = displayToken(hidden).split(/[,\s·]+/).map(displayToken).filter(Boolean);
  const meanings = unique(hiddenItems.map(tenGodEvidenceText).filter(Boolean), 4);
  const hiddenLabel = displayJoin(hiddenItems, ", ");
  const hiddenMeaningText = displayJoin(meanings, ", ");
  const hiddenSentence = meanings.length
    ? `지장간 ${hiddenLabel}에는 ${hiddenMeaningText}${evidenceNominativeParticle(meanings[meanings.length - 1])} 내재합니다.`
    : "";
  const protrudedText = displayToken(protruded);
  const protrudedSentence = protrudedText
    ? ` 그중 ${protrudedText}${evidenceNominativeParticle(protrudedText)} 천간으로 드러나 있어 이 지지의 기준은 실제 말과 선택으로 비교적 쉽게 표면화됩니다.`
    : "";
  return `${hiddenSentence}${protrudedSentence}`;
}

function contextualMonthBranchBody(concept) {
  const title = displayToken(concept && concept.name);
  const body = displayToken(concept && concept.body);
  const branch = (title.match(/^([子丑寅卯辰巳午未申酉戌亥])/) || [])[1] || "";
  if (branch === "子") {
    return "子월은 한겨울 수기가 왕한 월령입니다. 기운이 밖으로 바로 펼쳐지기보다 안으로 모이고, 정보와 감정, 준비와 저장의 성격이 강해집니다. 이 명식에서는 돈과 정보의 흐름을 읽는 감각이 기본 바탕이 되지만, 결과를 밖으로 드러내고 현실 기준으로 고정하는 힘이 함께 필요합니다. 그래서 子월의 작용은 재물, 직업, 관계를 볼 때 체감은 빠르지만 결론은 늦게 굳어지는 구조로 읽습니다.";
  }
  return body.replace(/당신의 사주에서는\s*.+?판단 근거에 반영합니다\.?/g, "").trim();
}

function contextualGyeokBody(concept, title) {
  const name = displayToken(title || (concept && concept.name));
  const body = displayToken(concept && concept.body);
  if (name === "정재격") {
    return "정재격은 고정 수입, 소유권, 정산, 생활 관리가 격국의 중심에 놓이는 구조입니다. 이 격은 크게 벌어 흩뿌리는 힘보다, 들어온 돈과 역할을 자기 기준 안에 안정적으로 남기는 힘을 중시합니다. 이 명식에서 정재격은 수입의 크기보다 명의, 정산, 계약 조건, 생활 기준을 어떻게 확정하느냐로 작동합니다. 강하면 성실한 축적과 신용이 살아나고, 흐트러지면 계산은 많아도 실제 보존력은 약해질 수 있습니다.";
  }
  return body.replace(/당신의 사주에서는\s*.+?판단 근거에 반영합니다\.?/g, "").trim();
}

function contextualBranchRealityBody(concept) {
  const parsed = parseBranchRealityEvidence(concept && concept.name, concept && concept.body);
  if (!parsed.position || !parsed.branch) return "";
  const positionRole = {
    연지: "초년 배경과 바깥 관계",
    월지: "사회 환경과 직업 바탕",
    일지: "가까운 관계와 결혼 생활",
    시지: "후반 성취와 장기 결과",
  }[parsed.position] || "현실 영역";
  const texture = displayJoin(branchEvidenceTexture[parsed.branch] || [], " · ");
  const actionSentence = contextualBranchActionSentence(parsed.position, parsed.action);
  const hiddenSentence = contextualHiddenStemsSentence(parsed.hidden, parsed.protruded);
  return `${parsed.position} ${parsed.branch}${evidenceTopicParticle(parsed.branch)} ${positionRole}에서 ${texture}${evidenceNominativeParticle(texture)} 생활 조건으로 작동합니다. ${actionSentence}${hiddenSentence ? ` ${hiddenSentence}` : ""}`;
}

function contextualConceptEvidenceBody(concept, title) {
  const raw = displayToken(concept && concept.name);
  const rawKind = String((concept && concept.kind) || "");
  if (rawKind.includes("element_combination")) {
    return displayToken(concept && concept.body);
  }
  if (/^[子丑寅卯辰巳午未申酉戌亥]\(.+\)월$/.test(raw)) {
    const body = contextualMonthBranchBody(concept);
    if (body) return body;
  }
  if (/^[가-힣]{1,4}격$/.test(raw)) {
    const body = contextualGyeokBody(concept, title);
    if (body) return body;
  }
  if (/월령 심화/.test(raw)) {
    return contextualMonthGovernanceBody(concept);
  }
  if (/^월지\s.+기준$/.test(raw) || title === "월령·조후 기준") {
    const body = contextualSeasonEvidenceBody(concept);
    if (body) return body;
  }
  if (/^(월지|일지|시지|연지)\s*[子丑寅卯辰巳午未申酉戌亥]의 현실 작용$/.test(raw)) {
    const body = contextualBranchRealityBody(concept);
    if (body) return body;
  }
  return displayToken(conceptDescriptionBody(concept.name, "") || concept.body || "")
    .replace(/당신의 사주에서는\s*.+?판단 근거에 반영합니다\.?/g, "")
    .trim();
}

function contextualConceptEvidenceWords(concept, title) {
  const raw = displayToken(concept && concept.name);
  if (String(concept && concept.kind) === "climate_adjustment") {
    return unique(asArray(concept && concept.keywords).map(displayToken).filter(Boolean), 8);
  }
  if (/월령 심화/.test(raw)) {
    const parsed = parseMonthGovernanceEvidence(concept && concept.name, concept && concept.body);
    return unique([
      "월지 본기",
      parsed.command && `${parsed.command} 월령`,
      parsed.active && `${parsed.active} 선작용`,
      tenGodEvidenceText(parsed.command),
      tenGodEvidenceText(parsed.active),
      "월률분야",
    ].map(displayToken).filter(Boolean), 8);
  }
  if (/월령·조후|조후/.test(title)) {
    const body = displayToken(concept && concept.body);
    const needed = (body.match(/필요한 오행은\s*([^.]+?)입니다/) || [])[1] || "";
    return unique(["계절 기운", needed, "보완 오행", "활력", "기준", "보존", "현실화", "체감 균형"].map(displayToken).filter(Boolean), 8);
  }
  const branch = parseBranchRealityEvidence(concept && concept.name, concept && concept.body);
  if (branch.position && branch.branch) {
    const exactWords = unique(
      asArray(concept && concept.keywords)
        .map(displayToken)
        .filter((word) => word && !/^(지지·지장간|사회 환경|직업 바탕|관계 기준|배우자 자리|후반 흐름|장기 결과)$/.test(word)),
      12,
    );
    if (exactWords.length >= 10) return exactWords;
    const positionWords = {
      연지: ["초년 배경", "바깥 관계"],
      월지: ["사회 환경", "직업 바탕"],
      일지: ["관계 기준", "배우자 자리"],
      시지: ["후반 흐름", "장기 결과"],
    }[branch.position] || [];
    return unique([...positionWords, ...(branchEvidenceTexture[branch.branch] || []), tenGodEvidenceText(branch.action)].map(displayToken).filter(Boolean), 12);
  }
  const noisy = /^(월지|본기|여기|월률분야|격국|십신 작용|현실 작용|생활 기반|지지|지장간|투출|통근)$/;
  return unique(asArray(concept && concept.keywords).map(displayToken).filter((word) => word && !noisy.test(word)), 12);
}

function contextualConceptEvidenceGroups(concept, title) {
  const words = contextualConceptEvidenceWords(concept, title);
  return words.length ? [{ tag: "핵심어", words }] : [];
}

function contextualConceptEvidenceSection(name, kind) {
  const raw = displayToken(name);
  const title = contextualConceptDisplayTitle(raw);
  const rawKind = String(kind || "");
  if (rawKind.includes("branch_pair")) return "branch";
  if (rawKind.includes("element_combination")) return "element";
  if (/^[甲乙丙丁戊己庚辛壬癸]{2}\s*[가-힣]+\+[가-힣]+$/.test(raw)) return "element";
  if (/^(월지|일지|시지|연지)\s*[子丑寅卯辰巳午未申酉戌亥]의 현실 작용$/.test(raw)) return "position";
  if (/월령|월지|월률|월\s*기준|조후|격/.test(`${raw} ${title}`)) return "foundation";
  if (/^[목화토금수]{2}$/.test(raw) || /배합|오행/.test(title) || rawKind.includes("element")) return "element";
  if (/^(비겁극재|재극인|재생관|식상생재|관인상생|식신제살|인성제식|상관견관)$/.test(raw)) return "action";
  if (/(비겁|비견|겁재|식상|식신|상관|재성|편재|정재|관성|편관|정관|인성|편인|정인).*(생|극|제|합|상생|상극)/.test(raw)) return "action";
  if (rawKind.includes("branch_relation")) return "branch";
  return "foundation";
}

function contextualKeywordEvidenceSection(profile, title) {
  const rawKind = String((profile && profile.kind) || "");
  const rawType = String((profile && (profile.type || profile.category)) || "");
  const label = displayToken(title);
  if (rawKind.includes("branch_relation") || /합|충|형|파|해/.test(label)) return "branch";
  if (rawKind.includes("shinsal") || /귀인|살|마|록|문창|홍염|도화|역마/.test(`${label} ${rawType}`)) return "auxiliary";
  return "keyword";
}

function contextualEvidenceRank(card) {
  const title = displayToken(card && card.title);
  const kind = String((card && card.kind) || "");
  const section = String((card && card.evidenceSection) || "");
  const sectionOrder = {
    foundation: 10,
    position: 20,
    element: 30,
    action: 40,
    branch: 50,
    auxiliary: 60,
    keyword: 70,
  };
  let rank = sectionOrder[section] || 80;
  if (section === "foundation") {
    if (/^[子丑寅卯辰巳午未申酉戌亥]\(.+\)월$/.test(title)) return 1;
    if (/^[가-힣]{1,4}격$/.test(title)) return 2;
    if (/격 속|격의 실제 작용/.test(title)) return 3;
    if (/월령 심화/.test(title)) return 3;
    if (/월령·조후|조후/.test(title)) return 4;
    if (/^월지\s.+현실 작용$/.test(title)) return 5;
    if (/^일지\s.+현실 작용$/.test(title)) return 6;
    if (/^월지\s/.test(title)) return 5;
    if (/^일지\s/.test(title)) return 6;
    if (/^시지\s/.test(title)) return 7;
    if (/월령|월지|\(.+\)월|子월|丑월|寅월|卯월|辰월|巳월|午월|未월|申월|酉월|戌월|亥월/.test(title)) rank -= 4;
    if (/격/.test(title)) rank -= 2;
  }
  if (section === "branch" && kind.includes("branch_relation")) rank -= 2;
  return rank;
}

function buildContextualEvidenceCards(actionGroups, keywordProfiles, mergedConcepts) {
  const hasSpecificBranchRelations = asArray(keywordProfiles).some((profile) => String((profile && profile.kind) || "").includes("branch_relation"));
  const cards = [
    ...asArray(actionGroups && actionGroups.core).map(contextualActionEvidenceCard),
    ...asArray(actionGroups && actionGroups.partial).map(contextualActionEvidenceCard),
    ...asArray(keywordProfiles).map(keywordProfileEvidenceCard),
    ...asArray(mergedConcepts).map(conceptEvidenceCard),
  ]
    .filter(Boolean)
    .filter((card) => !(hasSpecificBranchRelations && card.kind === "branch_relation_generic"))
    .map((card, index) => ({ ...card, evidenceOrder: index }));
  const specificActionTitles = cards
    .filter((card) => card.sourceType === "action")
    .map((card) => displayToken(card.title));
  const genericActionCovered = (title) => {
    const patterns = {
      비겁극재: /(?:비견|겁재)·(?:편재|정재)|(?:편재|정재)·(?:비견|겁재)/,
      재극인: /(?:편재|정재)·(?:편인|정인)|(?:편인|정인)·(?:편재|정재)/,
      재생관: /(?:편재|정재)·(?:편관|정관)|(?:편관|정관)·(?:편재|정재)/,
      식상생재: /(?:식신|상관)·(?:편재|정재)|(?:편재|정재)·(?:식신|상관)/,
      관인상생: /(?:편관|정관)·(?:편인|정인)|(?:편인|정인)·(?:편관|정관)/,
      식신제살: /식신·편관|편관·식신/,
      인성제식: /(?:편인|정인)·(?:식신|상관)|(?:식신|상관)·(?:편인|정인)/,
      상관견관: /상관·(?:편관|정관)|(?:편관|정관)·상관/,
    };
    const pattern = patterns[displayToken(title)];
    return Boolean(pattern && specificActionTitles.some((specificTitle) => pattern.test(specificTitle)));
  };
  const seen = new Set();
  const seenContent = new Set();
  const seenActionPairs = new Set();
  return cards.filter((card) => {
    if (card.sourceType === "concept" && genericActionCovered(card.title)) return false;
    const key = contextualEvidenceCardKey(card);
    if (!key || seen.has(key)) return false;
    const contentKey = contextualEvidenceContentKey(card);
    if (contentKey && seenContent.has(contentKey)) return false;
    const actionPairKey = contextualActionPairKey(card);
    if (actionPairKey && seenActionPairs.has(actionPairKey)) return false;
    seen.add(key);
    if (contentKey) seenContent.add(contentKey);
    if (actionPairKey) seenActionPairs.add(actionPairKey);
    return true;
  }).sort((a, b) => (
    contextualEvidenceRank(a) - contextualEvidenceRank(b)
    || ((Number(b.score) || 0) - (Number(a.score) || 0))
    || ((Number(a.evidenceOrder) || 0) - (Number(b.evidenceOrder) || 0))
  ));
}

function renderContextualEvidenceGroups(groups) {
  const rawGroups = asArray(groups)
    .map((group) => {
      const tag = String((group && group.tag) || "").trim();
      const words = unique(
        asArray(group && group.words).map((word) => String(word || "").trim()).filter(Boolean),
        tag === "핵심어" ? 12 : 8,
      );
      return { tag, words };
    })
    .filter((group) => group.tag && group.words.length);
  const visible = rawGroups.length ? rawGroups.slice(0, 5) : normalizeContextualKeywordGroups({ groups });
  if (!visible.length) return "";
  return `
    <div class="contextual-keyword-groups">
      ${visible
        .map(
          (group) => `
            <div class="contextual-keyword-group">
              <b>${escapeHtml(group.tag)}</b>
              <span>${group.words.map(escapeHtml).join(" · ")}</span>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

const contextualEvidenceCopularNounStems = new Set([
  "구조",
  "완성도",
  "창고",
  "화토",
  "지지",
]);

const contextualEvidenceIntrinsicDaNouns = new Set([
  "바다",
]);

function contextualEvidenceHangulSyllable(char) {
  const code = String(char || "").codePointAt(0);
  if (!Number.isInteger(code) || code < 0xac00 || code > 0xd7a3) return null;
  const offset = code - 0xac00;
  return { code, jong: offset % 28 };
}

function contextualEvidenceReplaceJong(char, nextJong) {
  const syllable = contextualEvidenceHangulSyllable(char);
  if (!syllable) return char;
  return String.fromCodePoint(syllable.code - syllable.jong + nextJong);
}

function contextualEvidenceFormalStem(value) {
  const chars = Array.from(String(value || ""));
  if (!chars.length) return "";
  const lastIndex = chars.length - 1;
  const syllable = contextualEvidenceHangulSyllable(chars[lastIndex]);
  if (!syllable) return `${chars.join("")}입니다`;
  if (syllable.jong === 0 || syllable.jong === 8) {
    chars[lastIndex] = contextualEvidenceReplaceJong(chars[lastIndex], 17);
    return `${chars.join("")}니다`;
  }
  return `${chars.join("")}습니다`;
}

function honorificContextualEvidenceSentence(value) {
  const body = String(value || "").trim();
  if (!body || /(?:니다|세요|십시오|군요|네요|예요|이에요|해요|돼요|어요|아요|죠)$/u.test(body)) {
    return body;
  }
  if (body.endsWith("는다")) {
    return contextualEvidenceFormalStem(body.slice(0, -2));
  }
  if ([...contextualEvidenceIntrinsicDaNouns].some((noun) => body.endsWith(noun))) {
    return `${body}입니다`;
  }
  if (body.endsWith("다")) {
    let stem = body.slice(0, -1);
    const stemChars = Array.from(stem);
    const lastIndex = stemChars.length - 1;
    const lastSyllable = contextualEvidenceHangulSyllable(stemChars[lastIndex]);
    if (lastSyllable && lastSyllable.jong === 4) {
      stemChars[lastIndex] = contextualEvidenceReplaceJong(stemChars[lastIndex], 0);
      return contextualEvidenceFormalStem(stemChars.join(""));
    }
    if ([...contextualEvidenceCopularNounStems].some((noun) => stem.endsWith(noun))) {
      return `${stem}입니다`;
    }
    return contextualEvidenceFormalStem(stem);
  }
  return `${body}입니다`;
}

function honorificContextualEvidenceCopy(value) {
  const source = String(value || "").trim();
  if (!source) return "";
  return source.replace(/([^.!?]+)([.!?]+|$)/gu, (full, rawBody, punctuation) => {
    const leading = (rawBody.match(/^\s*/) || [""])[0];
    const trailing = (rawBody.match(/\s*$/) || [""])[0];
    const body = rawBody.trim();
    if (!body) return full;
    return `${leading}${honorificContextualEvidenceSentence(body)}${punctuation}${trailing}`;
  });
}

function renderContextualEvidenceCard(card) {
  if (!card) return "";
  const bodyParts = asArray(card.bodyParts)
    .map((part) => String(part || "").trim())
    .filter(Boolean);
  if (!bodyParts.length && card.body) bodyParts.push(String(card.body).trim());
  const groupCount = asArray(card.groups).filter((group) => asArray(group && group.words).length).length;
  const densityClass = card.evidenceSection === "action" && groupCount < 3
    ? " is-compact-evidence"
    : "";
  return `
    <article class="contextual-evidence-card${densityClass}">
      <header>
        <strong>${escapeHtml(card.title || "종합 근거")}</strong>
        ${card.meta ? `<em>${escapeHtml(card.meta)}</em>` : ""}
      </header>
      ${bodyParts.map((part) => `<p>${escapeHtml(honorificContextualEvidenceCopy(part))}</p>`).join("")}
      ${renderContextualEvidenceGroups(card.groups)}
    </article>
  `;
}

const contextualEvidenceGroupLabels = {
  foundation: "월령과 격국",
  position: "지지의 핵심어",
  element: "천간의 배합",
  action: "십신의 주요 작용",
  branch: "지지 배합과 관계",
  auxiliary: "신살·보조 표지",
  keyword: "보조 핵심어",
};

function renderContextualEvidenceGroup(section, cards) {
  const visibleCards = asArray(cards).filter(Boolean);
  if (!visibleCards.length) return "";
  const visible = visibleCards.map(renderContextualEvidenceCard).filter(Boolean);
  const title = contextualEvidenceGroupLabels[section] || "그 밖의 근거";
  const isSecondary = section === "auxiliary" || section === "keyword";
  if (isSecondary) {
    return `
      <details class="contextual-evidence-group is-secondary">
        <summary>
          <span><strong>${escapeHtml(title)}</strong></span>
          <small>펼쳐보기</small>
        </summary>
        <div class="contextual-evidence-stack is-compact">
          ${visible.join("")}
        </div>
      </details>
    `;
  }
  const sourceOnly = visibleCards.every((card) => card && card.sourceType === "source");
  if (sourceOnly && section !== "foundation") {
    return `
      <details class="contextual-evidence-group is-collapsible">
        <summary>
          <span><strong>${escapeHtml(title)}</strong></span>
          <small>펼쳐보기</small>
        </summary>
        <div class="contextual-evidence-group-body contextual-evidence-stack">
          ${visible.join("")}
        </div>
      </details>
    `;
  }
  if (section === "action") {
    const richCards = [];
    const sparseCards = [];
    visibleCards.forEach((card) => {
      const groupCount = asArray(card.groups).filter((group) => asArray(group && group.words).length).length;
      if (groupCount >= 3) {
        richCards.push(card);
      } else {
        sparseCards.push(card);
      }
    });
    const primaryCards = richCards.length ? richCards : sparseCards.slice(0, 2);
    const supportingCards = richCards.length ? sparseCards : sparseCards.slice(2);
    const primary = primaryCards.map(renderContextualEvidenceCard).filter(Boolean);
    const supporting = supportingCards.map(renderContextualEvidenceCard).filter(Boolean);
    return `
      <details class="contextual-evidence-group is-collapsible">
        <summary>
          <span><strong>${escapeHtml(title)}</strong></span>
          <small>펼쳐보기</small>
        </summary>
        <div class="contextual-evidence-group-body">
          <div class="contextual-evidence-stack">
            ${primary.join("")}
          </div>
          ${supporting.length ? `
            <details class="contextual-evidence-subgroup">
              <summary>
                <strong>함께 작용하는 십신 배합</strong>
                <span>${supporting.length}개 보기</span>
              </summary>
              <div class="contextual-evidence-stack is-compact">
                ${supporting.join("")}
              </div>
            </details>
          ` : ""}
        </div>
      </details>
    `;
  }
  if (section === "position") {
    const primaryCards = visibleCards.filter((card) => /(?:월지|일지)/.test(displayToken(card.title)));
    const supportingCards = visibleCards.filter((card) => !primaryCards.includes(card));
    const primarySource = primaryCards.length ? primaryCards : visibleCards.slice(0, 2);
    const supportingSource = primaryCards.length ? supportingCards : visibleCards.slice(2);
    const primary = primarySource.map(renderContextualEvidenceCard).filter(Boolean);
    const supporting = supportingSource.map(renderContextualEvidenceCard).filter(Boolean);
    return `
      <details class="contextual-evidence-group is-collapsible">
        <summary>
          <span><strong>${escapeHtml(title)}</strong></span>
          <small>펼쳐보기</small>
        </summary>
        <div class="contextual-evidence-group-body">
          <div class="contextual-evidence-stack">
            ${primary.join("")}
          </div>
          ${supporting.length ? `
            <details class="contextual-evidence-subgroup is-position-supporting">
              <summary>
                <strong>다른 기둥에서 이어지는 작용</strong>
                <span>${supporting.length}개 보기</span>
              </summary>
              <div class="contextual-evidence-stack is-compact">
                ${supporting.join("")}
              </div>
            </details>
          ` : ""}
        </div>
      </details>
    `;
  }
  if (section !== "foundation") {
    return `
      <details class="contextual-evidence-group is-collapsible">
        <summary>
          <span><strong>${escapeHtml(title)}</strong></span>
          <small>펼쳐보기</small>
        </summary>
        <div class="contextual-evidence-group-body contextual-evidence-stack">
          ${visible.join("")}
        </div>
      </details>
    `;
  }
  const foundationGroups = [
    {
      title: "월령",
      cards: visibleCards.filter((card) => !/격/.test(displayToken(card && card.title))),
    },
    {
      title: "격국",
      cards: visibleCards.filter((card) => /격/.test(displayToken(card && card.title))),
    },
  ].filter((group) => group.cards.length);
  const resolvedGroups = foundationGroups.length ? foundationGroups : [{ title, cards: visibleCards }];
  return resolvedGroups
    .map((group) => `
      <details class="contextual-evidence-group is-collapsible is-foundation">
        <summary>
          <span><strong>${escapeHtml(group.title)}</strong></span>
          <small>펼쳐보기</small>
        </summary>
        <div class="contextual-evidence-group-body contextual-evidence-stack">
          ${group.cards.map(renderContextualEvidenceCard).filter(Boolean).join("")}
        </div>
      </details>
    `)
    .join("");
}

function renderContextualEvidenceSection(cards) {
  const grouped = asArray(cards).reduce((result, card) => {
    const section = String((card && card.evidenceSection) || "foundation");
    if (!result[section]) result[section] = [];
    result[section].push(card);
    return result;
  }, {});
  const order = ["foundation", "action", "element", "position", "branch", "auxiliary", "keyword"];
  const visible = order.map((section) => renderContextualEvidenceGroup(section, grouped[section])).filter(Boolean);
  if (!visible.length) return "";
  return `
    <section class="paper-card contextual-evidence-section" data-scroll-anchor="contextual-evidence">
      <div class="contextual-evidence-section-head">
        <h2>명리 원문 근거</h2>
      </div>
      <div class="contextual-evidence-groups">
        ${visible.join("")}
      </div>
    </section>
  `;
}

const pillarBasisLabels = {
  hour: "생시",
  day: "생일",
  month: "생월",
  year: "생년",
};

const tenGodKoreanLabels = {
  比肩: "비견",
  劫財: "겁재",
  食神: "식신",
  傷官: "상관",
  偏財: "편재",
  正財: "정재",
  偏官: "편관",
  正官: "정관",
  偏印: "편인",
  正印: "정인",
  일간: "일간",
};

function pillarBasisLabel(row) {
  return pillarBasisLabels[row && row.key] || (row && row.label ? `${displayToken(row.label)}주` : "기둥");
}

function tenGodDisplay(value) {
  const token = displayToken(value);
  return tenGodKoreanLabels[token] || token || "-";
}

function elementKeyOf(token) {
  return stemElements[token] || branchElements[token] || "";
}

function elementBadge(token) {
  const key = elementKeyOf(token);
  const meta = elementLabels[key];
  if (!meta) return "";
  return `<span class="manse-element-badge is-${escapeHtml(key)}">${escapeHtml(meta.ko)}(${escapeHtml(meta.han)})</span>`;
}

function renderManseToken(token) {
  const key = elementKeyOf(token);
  const className = key ? `manse-token is-${key}` : "manse-token";
  return `<strong class="${escapeHtml(className)}">${escapeHtml(token || "-")}</strong>`;
}

function renderManseHidden(row) {
  const branch = displayToken(row && row.branch);
  const sourceStems = asArray(row && row.hiddenStems).map(displayToken).filter(Boolean);
  const fallbackStems = asArray(branchHiddenStemFallback[branch]).map(displayToken).filter(Boolean);
  const stems = unique([...fallbackStems, ...sourceStems], 6);
  const rawGods = asArray(row && row.hiddenTenGods);
  const godByStem = {};
  sourceStems.forEach((stem, index) => {
    if (stem && rawGods[index]) godByStem[stem] = rawGods[index];
  });
  if (!stems.length) return `<span class="manse-muted">-</span>`;
  return stems
    .map((stem, index) => {
      const key = elementKeyOf(stem);
      const className = key ? `manse-hidden-chip is-${key}` : "manse-hidden-chip";
      const god = tenGodDisplay(godByStem[stem] || (sourceStems[index] === stem ? rawGods[index] : ""));
      const godHtml = god && god !== "-" ? `<em>${escapeHtml(god)}</em>` : "";
      return `<span class="${escapeHtml(className)}"><b>${escapeHtml(stem)}</b>${godHtml}</span>`;
    })
    .join("");
}

function branchTenGodDisplay(row) {
  return tenGodDisplay(row && (row.branchTenGod || row.branchTenGodLabel || asArray(row.hiddenTenGods)[0]));
}

function renderIntegratedPaljaBasis(chart = {}) {
  const rows = Array.isArray(chart.pillarRows) ? chart.pillarRows : [];
  if (!rows.length) return "";
  const columnCount = Math.max(1, rows.length);
  return `
    <section class="paper-card contextual-palja-basis manse-basis-card" data-scroll-anchor="contextual-palja">
      <div class="manse-basis-head">
        <h2>사주 명식</h2>
        <p>사주의 네 기둥을 천간, 지지, 십신, 지장간 순서로 정리한 명식표입니다.</p>
      </div>
      <div class="manse-pillars" style="--manse-cols:${columnCount};" role="table" aria-label="사주 명식">
        <div class="manse-row manse-row-head" role="row">
          <span class="manse-row-label" role="columnheader">구분</span>
          ${rows
            .map((row) => `
              <span class="manse-pillar-head" role="columnheader">
                <b>${escapeHtml(pillarBasisLabel(row))}</b>
                <em>${escapeHtml(row.pillar || `${row.stem || ""}${row.branch || ""}`)}</em>
              </span>
            `)
            .join("")}
        </div>
        <div class="manse-row manse-row-token" role="row">
          <span class="manse-row-label" role="rowheader">천간</span>
          ${rows
            .map((row) => `
              <span class="manse-cell" role="cell">
                ${renderManseToken(row.stem)}
                ${elementBadge(row.stem)}
              </span>
            `)
            .join("")}
        </div>
        <div class="manse-row manse-row-god" role="row">
          <span class="manse-row-label" role="rowheader">십신</span>
          ${rows.map((row) => `<span class="manse-cell manse-god" role="cell">${escapeHtml(tenGodDisplay(row.tenGod))}</span>`).join("")}
        </div>
        <div class="manse-row manse-row-token" role="row">
          <span class="manse-row-label" role="rowheader">지지</span>
          ${rows
            .map((row) => `
              <span class="manse-cell" role="cell">
                ${renderManseToken(row.branch)}
                ${elementBadge(row.branch)}
              </span>
            `)
            .join("")}
        </div>
        <div class="manse-row manse-row-god" role="row">
          <span class="manse-row-label" role="rowheader">십신</span>
          ${rows.map((row) => `<span class="manse-cell manse-god" role="cell">${escapeHtml(branchTenGodDisplay(row))}</span>`).join("")}
        </div>
        <div class="manse-row manse-row-hidden" role="row">
          <span class="manse-row-label" role="rowheader">지장간</span>
          ${rows.map((row) => `<span class="manse-cell manse-hidden-list" role="cell">${renderManseHidden(row)}</span>`).join("")}
        </div>
      </div>
    </section>
  `;
}

function sourceContextualEvidenceCard(profile) {
  if (!profile || profile.source_verified !== true) return null;
  const title = String(profile.display_title || profile.title || profile.source_section || "").trim();
  if (!title) return null;
  return {
    sourceType: "source",
    kind: "source_exact",
    evidenceSection: String(profile.evidence_section || "foundation"),
    title,
    bodyParts: asArray(profile.description_parts),
    groups: asArray(profile.groups),
    meta: String(profile.meta || "").trim(),
    score: Number(profile.priority) || 0,
  };
}

function renderContextualDetail(contract, detailUnit, chart = {}, factors = [], basisUnit = null) {
  if (!contract) {
    return `<section class="paper-card"><h2>종합 근거</h2><p>격국, 월령, 오행, 조후를 결합한 산출값이 없습니다.</p></section>`;
  }
  const evidenceCards = asArray(contract.source_evidence_profiles)
    .map(sourceContextualEvidenceCard)
    .filter(Boolean);
  return `
    ${renderIntegratedPaljaBasis(chart)}
    ${renderContextualEvidenceSection(evidenceCards)}
    <div class="contextual-copy-actions">
      <button
        class="contextual-copy-button"
        type="button"
        data-action="copy-full-analysis"
        aria-label="분석 결과 모두 복사하기"
      ></button>
    </div>
  `;
}

function renderDomainContract(domainKey, domainContracts) {
  const contract = domainContracts && domainContracts[domainKey];
  const items = asArray(contract && contract.items).slice(0, 6);
  if (!items.length) {
    return "";
  }
  return `
    <section class="paper-card">
      <h2>세부 지표</h2>
      <div class="topic-grid">
        ${items
          .map((item) => {
            const score = metricScore(item);
            const level = metricLevelForItem(item, score, item.value || "");
            return `
              <article class="topic-card metric-card ${metricToneClassForItem(item, score)}${metricPolarity(item) === "risk" ? " metric-risk-axis" : ""}">
                <header>
                  <strong>${escapeHtml(item.label || "세부 항목")}</strong>
                  ${renderMetricLevelBadgeForItem(item, score, level)}
                </header>
                ${renderMetricBarForItem(item, score)}
                ${renderMetricBodyParagraphs(item, "영역별 해석에 반영된 세부 값입니다.")}
                ${textList(item.layer_coverage || [], 4).length ? `<div class="tag-row">${textList(item.layer_coverage || [], 4).map((label) => `<span>${escapeHtml(label)}</span>`).join("")}</div>` : ""}
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function displayWatchCaption(caption, score) {
  const number = Number(score);
  const judgmentState = Number.isFinite(number)
    ? semanticStateForGrade(judgmentGradeForScore(number, ""))
    : "normal";
  const fallback = judgmentState === "bad" ? "주의 지표" : "살필 지표";
  const value = String(caption || "").trim();
  if (!value || value === "보완 항목" || value === "먼저 살필 항목") return fallback;
  if (judgmentState !== "bad" && /주의/.test(value)) return "살필 지표";
  return productText(value);
}

function displayWatchTitle(label) {
  const text = productText(label || "").trim();
  if (!text) return "";
  const direct = {
    "공동자금 운영력": "공동재정",
    "공동재정": "공동재정",
    "자금 운용 안정성": "재정 관리",
    "재정 관리": "재정 관리",
    "재정 안정성": "재정 안정",
    "재정 방어력": "손실 방어",
    "손실 방어": "손실 방어",
    "계약·명의 안정성": "계약·명의 안정",
    "계약·명의 안정": "계약·명의 안정",
    "계약 문서 안정성": "문서 안정",
    "문서 안정": "문서 안정",
    "사업 확장성": "사업 확장",
    "사업 확장": "사업 확장",
    "조직 안에서 자리 잡는 힘": "조직 적응",
    "조직 적응력": "조직 적응",
    "조직 적응": "조직 적응",
    "결정권 없는 책임": "책임 범위 주의",
    "성취 축적력": "경력 축적",
    "경력 축적": "경력 축적",
    "독립 가능성": "독립 가능성",
    "독립 전환운": "독립 가능성",
    "관계 진전력": "관계 진전",
    "관계 진전": "관계 진전",
    "관계 속도 조절력": "관계 속도",
    "애정 표현성": "애정 표현",
    "애정 표현": "애정 표현",
    "재회 가능성": "재회 가능성",
    "재회운": "재회 가능성",
    "부부 재정": "부부 재정",
    "부부 갈등 조정력": "부부 갈등",
    "부부 갈등": "부부 갈등",
    "가정 운영력": "가정 운영",
    "생활 안정": "생활 안정",
    "실행 속도": "실행 속도",
    "행동 속도": "실행 속도",
    "움직이는 속도": "실행 속도",
    "대인 조율감": "관계 조율",
    "관계 조율": "관계 조율",
    "타고난 재물의 그릇": "재물 규모",
    "재물 형성력": "재물 형성력",
    "재물 기반": "재물 형성력",
    "재물 규모 확장력": "재물 규모 확장",
    "재물 규모 확장": "재물 규모 확장",
    "후반 축재력": "후반 자산운",
    "후반 자산운": "후반 자산운",
    "압박 대응력": "문제 해결력",
    "압박 대응": "문제 해결력",
    "부담이 커질 때": "문제 해결력",
    "부담이 커졌을 때": "문제 해결력",
    "문제 해결력": "문제 해결력",
    "판단 기준": "자기 신뢰",
    "판단 방식": "자기 신뢰",
    "자기 신뢰": "자기 신뢰",
    "감정 반응": "감정 조절",
    "감정 반응성": "감정 조절",
    "감정 조절": "감정 조절",
    "관심 몰입도": "몰입력",
    "몰입력": "몰입력",
    "대인 거리감": "관계 거리 조절력",
    "관계 거리감": "관계 거리 조절력",
    "관계 거리 조절력": "관계 거리 조절력",
  };
  if (direct[text]) return direct[text];
  return text;
}

function renderSectionVerdictSummary(section) {
  const verdict = section && section.section_verdict ? section.section_verdict : {};
  const score = Number(verdict.score);
  const aggregateGrade = sectionAggregateGrade(section, "");
  const strongScore = Number(verdict.strong_score);
  const watchScore = Number(verdict.watch_score);
  const rows = [
    {
      label: "종합",
      title: "종합 등급",
      toneScore: score,
      grade: aggregateGrade,
    },
    {
      label: verdict.strong_caption || "강점",
      title: verdict.strong_label || "",
      toneScore: strongScore,
    },
    {
      label: displayWatchCaption(verdict.watch_caption, watchScore),
      title: displayWatchTitle(verdict.watch_label || ""),
      toneScore: watchScore,
    },
  ].filter((item) => item.title || item.grade || Number.isFinite(item.toneScore));
  if (!rows.length && !verdict.interpretation && !verdict.action && !verdict.basis) return "";
  return `
    <div class="section-verdict-summary">
      ${rows.length ? `
        <div class="section-verdict-row">
          ${rows.map((item) => `
            <article class="${item.grade ? metricToneClassFromGrade(item.grade) : metricToneClass(item.toneScore)}">
              <span>${escapeHtml(productText(item.label))}</span>
              <strong>${escapeHtml(productText(item.title))}</strong>
              ${(item.grade || Number.isFinite(item.toneScore))
                ? `<em class="metric-grade-value ${item.grade ? metricGradeClassFromLabel(item.grade) : metricGradeClass(item.toneScore)}">${escapeHtml(item.grade || metricGrade(item.toneScore))}</em>`
                : ""}
            </article>
          `).join("")}
        </div>
      ` : ""}
      ${(verdict.interpretation || verdict.action || verdict.basis) ? `
        <div class="section-verdict-copy">
          ${verdict.interpretation ? `<p><b>${escapeHtml(productText(verdict.interpretation_title || "결론"))}</b> ${escapeHtml(productText(verdict.interpretation))}</p>` : ""}
          ${verdict.action ? `<p><b>${escapeHtml(productText(verdict.action_title || "대응"))}</b> ${escapeHtml(productText(verdict.action))}</p>` : ""}
          ${verdict.basis ? `<p class="section-verdict-basis"><b>${escapeHtml(productText(verdict.basis_title || "판단 근거"))}</b> ${escapeHtml(productText(verdict.basis))}</p>` : ""}
        </div>
      ` : ""}
    </div>
  `;
}

function renderDomainLanding(sections) {
  const visible = asArray(sections)
    .map((section, index) => ({ section, index }))
    .filter(({ section }) => section && !["timing", "life", "year_2026", "year_2027"].includes(section.domain))
    .slice(0, 7);
  if (!visible.length) {
    return `<section class="paper-card"><h2>분야별 총운</h2><p>표시할 운세 영역이 없습니다.</p></section>`;
  }
  const ranked = visible
    .map((item) => {
      const rawGrade = rawSectionAggregateGrade(item.section, "");
      return {
        ...item,
        rawGrade,
        rawGradeRank: metricGradeRank(rawGrade),
      };
    })
    .filter((item) => item.rawGradeRank >= 0)
    .sort((a, b) => b.rawGradeRank - a.rawGradeRank);
  const strongestItem = ranked[0] || null;
  const cautionItem = ranked[ranked.length - 1] || null;
  const strongest = strongestItem && sectionDisplayTitle(strongestItem.section);
  const caution = cautionItem && sectionDisplayTitle(cautionItem.section);
  const strongestRank = strongestItem ? strongestItem.rawGradeRank : -1;
  const cautionRank = cautionItem ? cautionItem.rawGradeRank : -1;
  const strongestIsGood = strongestRank >= metricGradeRank("A-");
  const cautionNeedsAttention = cautionRank >= 0 && cautionRank < metricGradeRank("B-");
  const strongestCaption = strongestIsGood ? "두드러진 분야" : "비교적 나은 분야";
  const cautionCaption = cautionNeedsAttention ? "주의가 필요한 분야" : "상대적으로 낮은 분야";
  return `
    <section class="paper-card domain-landing">
      <div class="domain-landing-head">
        <span>분야별 총운</span>
        <h2>먼저 볼 운세를 선택하세요</h2>
        <p>재물, 직업, 인연처럼 필요한 항목부터 이어 볼 수 있습니다.</p>
      </div>
      ${(strongest || caution || visible.length) ? `
        <div class="domain-landing-summary">
          ${strongest ? `<button class="${strongestIsGood ? "is-good" : "is-neutral"}" type="button" data-detail-key="domains:${strongestItem.index}"><b>${escapeHtml(strongestCaption)}</b><strong>${escapeHtml(strongest)}</strong>${domainLandingSummaryNote(strongestItem.section, "strong")}</button>` : ""}
          ${caution && caution !== strongest ? `<button class="${cautionNeedsAttention ? "is-caution" : "is-neutral"}" type="button" data-detail-key="domains:${cautionItem.index}"><b>${escapeHtml(cautionCaption)}</b><strong>${escapeHtml(caution)}</strong>${domainLandingSummaryNote(cautionItem.section, "watch")}</button>` : ""}
        </div>
      ` : ""}
      <div class="domain-landing-grid">
        ${visible.map(({ section, index }) => {
          const domain = section.domain || "default";
          const meta = domainLandingMeta(section);
          const grade = meta.grade;
          return `
            <button class="domain-landing-card ${metricToneClassFromGrade(grade)}" type="button" data-detail-key="domains:${index}">
              <span class="section-symbol">${escapeHtml(sectionSymbols[domain] || sectionSymbols.default)}</span>
              <span class="domain-landing-copy">
                <strong>${escapeHtml(sectionDisplayTitle(section))}</strong>
                <small>${escapeHtml(meta.primaryLabel || (domainPickerHints[domain] || domainPickerHints.default))}</small>
              </span>
              <span class="domain-landing-side">
                ${grade
                  ? `<b class="metric-grade-value ${metricGradeClassFromLabel(grade)}">${escapeHtml(grade)}</b>`
                  : "<em>상세</em>"}
              </span>
            </button>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

function findSectionByDomain(sections, domain) {
  return asArray(sections).find((section) => section && section.domain === domain) || null;
}

function annualSectionTitle(domainKey) {
  if (domainKey === "year_2026") return { title: "올해운", year: "2026", ganji: "병오년", icon: "26" };
  if (domainKey === "year_2027") return { title: "내년운", year: "2027", ganji: "정미년", icon: "27" };
  return { title: "연간 운세", year: "", ganji: "", icon: "年" };
}

function renderAnnualGroupMetricOverview(group) {
  const title = productText((group && group.title) || "연간 지표");
  const visible = asArray(group && group.items).filter(
    (item) => item && typeof item === "object" && metricLabel(item, "")
  );
  if (!visible.length) return "";
  return `
    <section class="annual-group-overview" aria-label="${escapeHtml(title)} 한눈에 보는 지표">
      <div class="annual-group-overview-head">
        <strong>한눈에 보는 지표</strong>
        <span>${visible.length}개 지표</span>
      </div>
      <div class="domain-metric-overview-list annual-group-overview-list">
        ${visible.map((item) => renderDomainMetricOverviewRow(item)).join("")}
      </div>
    </section>
  `;
}

function renderAnnualMetricGroup(group, domainKey = "", groupIndex = 0) {
  const items = asArray(group && group.items).filter((item) => item && typeof item === "object");
  if (!items.length) return "";
  const groupGrade = annualOverviewGroupGrade(group);
  const groupTone = groupGrade
    ? metricToneClassFromGrade(groupGrade).replace("metric-", "annual-tone-")
    : "";
  return `
    <details class="annual-metric-group">
      <summary class="annual-group-head">
        <strong>${escapeHtml(productText((group && group.title) || "연간 지표"))}</strong>
        <span>
          ${groupGrade
            ? `<b class="annual-score-status ${groupTone} metric-grade-value ${metricGradeClassFromLabel(groupGrade)}">${escapeHtml(groupGrade)}</b>`
            : ""}
          <em>${items.length}개 지표</em>
        </span>
      </summary>
      <div class="annual-group-body">
        ${renderAnnualGroupMetricOverview(group)}
        <div class="metric-grid metric-grid-detail annual-metric-grid">
          ${items.map((item) => renderMetricCard(item, { annualDomainKey: domainKey })).join("")}
        </div>
      </div>
    </details>
  `;
}

function annualOverviewGroupLabel(group) {
  const title = productText((group && group.title) || "");
  const labels = {
    "종합 흐름 지표": "종합 흐름",
    "직업·업무 지표": "직업",
    "재물 지표": "재물",
    "대인관계 지표": "대인관계",
    "연애 지표": "연애",
    "결혼·가정 지표": "가정",
    "명예·평판 지표": "명예·평판",
    "생활·컨디션 지표": "건강·컨디션",
  };
  return labels[title] || title.replace(/\s*지표$/, "");
}

function annualOverviewGroupGrade(group) {
  const grade = annualGroupAggregateGrade(group, "");
  if (grade) return grade;
  const backendScore = Number(group && (group.total_score ?? group.score));
  return Number.isFinite(backendScore) ? metricGrade(backendScore, "") : "";
}

function annualOverviewGroupScore(group) {
  return metricGradeVisualPosition(annualOverviewGroupGrade(group));
}

function annualOverviewMetrics(groups, limit = 8) {
  return asArray(groups)
    .map((group, index) => {
      const label = annualOverviewGroupLabel(group);
      const aggregateGrade = annualOverviewGroupGrade(group);
      const score = metricGradeVisualPosition(aggregateGrade);
      if (!label || !aggregateGrade || !Number.isFinite(score)) return null;
      return {
        key: `annual_overview_${index}_${label}`,
        label,
        title: label,
        score,
        display_score: score,
        positive_score: score,
        polarity: "positive",
        score_direction: "higher_is_better",
        aggregate_grade: aggregateGrade,
        level: aggregateGrade,
        source: "annual_group_grade_average",
      };
    })
    .filter(Boolean)
    .slice(0, limit);
}

function primaryContextualActionConcepts(concepts, limit = 1) {
  return asArray(concepts)
    .filter((concept) => concept && concept.name && concept.body)
    .filter((concept) => contextualConceptEvidenceSection(concept.name, concept.kind) === "action")
    .slice(0, limit);
}

function renderAnnualMetricOverview(section, groups, meta) {
  const visible = annualOverviewMetrics(groups, 8);
  if (!visible.length) return "";
  const title = section && section.title ? section.title : meta.title;
  return `
    <section class="domain-metric-overview annual-metric-overview" aria-label="${escapeHtml(title)} 한눈에 보는 지표">
      <div class="domain-metric-overview-head">
        <strong>한눈에 보는 지표</strong>
        <span>${escapeHtml(title)}의 주요 영역 등급입니다.</span>
      </div>
      <div class="domain-metric-overview-list">
        ${visible.map((item) => renderDomainMetricOverviewRow(item)).join("")}
      </div>
    </section>
  `;
}

function renderAnnualDetail(section, domainKey) {
  const meta = annualSectionTitle(domainKey);
  if (!section) {
    return `
      <section class="paper-card annual-detail">
        <div class="domain-landing-head">
          <span>${escapeHtml(meta.year ? `${meta.year} ${meta.ganji}` : "연간 운세")}</span>
          <h2>${escapeHtml(meta.title)}</h2>
          <p>표시할 연간 운세 지표가 없습니다.</p>
        </div>
      </section>
    `;
  }
  const grade = sectionAggregateGrade(section, "");
  const groups = asArray(section.metric_groups).filter((group) => group && group.items);
  return `
    <section class="paper-card annual-detail ${metricToneClassFromGrade(grade)}">
      <div class="annual-detail-head">
        <span class="annual-year-seal" aria-hidden="true">${escapeHtml(section.icon || meta.icon)}</span>
        <div>
          <span>${escapeHtml(`${section.year || meta.year} ${section.ganji || meta.ganji}`.trim())}</span>
          <h2>${escapeHtml(section.title || meta.title)}</h2>
          <p>${escapeHtml(productText(section.lead || `${meta.year} ${meta.ganji} 기준 운세입니다.`))}</p>
        </div>
        ${metricGradeRank(grade) >= 0 ? `
          <div class="domain-score annual-score">
            <strong class="metric-grade-value ${metricGradeClassFromLabel(grade)}">${escapeHtml(grade)}</strong>
            <span>종합 등급</span>
          </div>
        ` : ""}
      </div>
      ${renderAggregateGradeBar(grade)}
      ${renderAnnualMetricOverview(section, groups, meta)}
      <div class="annual-group-list">
        ${groups.map((group, index) => renderAnnualMetricGroup(group, domainKey, index)).join("")}
      </div>
    </section>
  `;
}

function domainScreenItemContract(section) {
  return section && section.screen_item_contract && typeof section.screen_item_contract === "object"
    ? section.screen_item_contract
    : {};
}

function domainLandingMeta(section) {
  const score = sectionMetricScore(section);
  const grade = sectionAggregateGrade(section, "");
  const verdict = section && section.section_verdict ? section.section_verdict : {};
  const representativeMetrics = metricItemsFrom(section, "representative_metrics", 6);
  const featureAxes = metricItemsFrom(section, "feature_axes", 16);
  const { strongest, weakest } = domainMetricExtremes(representativeMetrics, featureAxes);
  const primary = domainRouteMetric(section);
  const contract = domainScreenItemContract(section);
  const summarySlot = asArray(contract.summary_slots).find((item) => item && item.slot !== "domain_verdict" && item.label);
  return {
    score,
    grade,
    gradeRank: metricGradeRank(grade),
    level: metricLevel(score, ""),
    primaryLabel: productText((summarySlot && summarySlot.label) || (primary ? primary.label : "")),
    strongLabel: productText(verdict.strong_label || (strongest && strongest.label) || ""),
    watchLabel: displayWatchTitle(verdict.watch_label || (weakest && weakest.label) || ""),
    strongScore: Number.isFinite(Number(verdict.strong_score)) ? Number(verdict.strong_score) : (strongest && strongest.toneScore),
    watchScore: Number.isFinite(Number(verdict.watch_score)) ? Number(verdict.watch_score) : (weakest && weakest.toneScore),
  };
}

function domainLandingSummaryNote(section, mode = "strong") {
  if (!section) return "";
  const meta = domainLandingMeta(section);
  const focus = mode === "watch"
    ? (meta.watchLabel || meta.primaryLabel || meta.strongLabel)
    : (meta.strongLabel || meta.primaryLabel || meta.watchLabel);
  const pieces = [
    meta.grade || "",
    focus || "",
  ].filter(Boolean);
  return pieces.length ? `<em>${escapeHtml(pieces.join(" · "))}</em>` : "";
}

function domainMetricExtremes(representativeMetrics, featureAxes) {
  const metrics = [...asArray(representativeMetrics), ...asArray(featureAxes)]
    .map((item) => {
      const score = metricScore(item);
      if (!Number.isFinite(score)) return null;
      return {
        item,
        label: metricLabel(item),
        score,
        toneScore: metricToneScore(item, score),
        level: metricLevelForItem(item, score, item.level || item.value || ""),
      };
    })
    .filter(Boolean);
  if (!metrics.length) {
    return { strongest: null, weakest: null };
  }
  const positiveMetrics = metrics.filter(({ item }) => metricPolarity(item) !== "risk");
  const strongest = [...(positiveMetrics.length ? positiveMetrics : metrics)]
    .sort((a, b) => b.toneScore - a.toneScore)[0];
  const weakest = [...metrics].sort((a, b) => a.toneScore - b.toneScore)[0];
  return { strongest, weakest };
}

function domainQuickBriefCopy(domainKey, domainTitle) {
  const copies = {
    personality: {
      total: "성격과 기질의 전체 결론입니다.",
      core: "성격에서 가장 분명하게 드러나는 장점입니다.",
      watch: "성격의 장점이 부담으로 바뀌기 쉬운 조건입니다.",
      coreLead: "성격이 실제 행동으로 드러나는 기준입니다.",
    },
    money: {
      total: "재물운의 전체 결론입니다.",
      core: "재물운에서 가장 분명하게 살아나는 부분입니다.",
      watch: "돈이 남는 과정에서 먼저 살필 부분입니다.",
      coreLead: "재물운은 수입보다 보유와 관리에서 더 크게 갈립니다.",
    },
    career: {
      total: "직업운의 전체 결론입니다.",
      core: "직업운에서 성과로 이어지기 쉬운 부분입니다.",
      watch: "실력과 평가가 어긋나지 않도록 먼저 살필 부분입니다.",
      coreLead: "직업운은 실력, 평가, 보상 기준이 맞을 때 선명해집니다.",
    },
    love: {
      total: "연애운의 전체 결론입니다.",
      core: "인연과 호감에서 가장 강하게 드러나는 부분입니다.",
      watch: "호감이 관계로 이어지기 전에 먼저 확인할 조건입니다.",
      coreLead: "연애운은 끌림, 표현, 지속성에서 차이가 납니다.",
    },
    marriage: {
      total: "결혼운의 전체 결론입니다.",
      core: "결혼 생활에서 안정으로 이어지기 쉬운 부분입니다.",
      watch: "결혼의 안정성을 흔들 수 있어 먼저 확인할 조건입니다.",
      coreLead: "결혼운은 배우자, 생활 기준, 책임 분담에서 갈립니다.",
    },
    life: {
      total: "인생 구간의 전체 결론입니다.",
      core: "인생 구간에서 가장 든든하게 받쳐주는 부분입니다.",
      watch: "인생 구간별 체감 차이를 크게 만드는 조건입니다.",
      coreLead: "초년, 중년, 말년의 체감 차이를 나누어 봅니다.",
    },
    honor: {
      total: "명예운의 전체 결론입니다.",
      core: "평판과 공식 인정에서 가장 유리한 부분입니다.",
      watch: "평판과 공적 인정이 늦어질 수 있어 먼저 확인할 조건입니다.",
      coreLead: "명예운은 평판, 직함, 공식 인정에서 드러납니다.",
    },
    social: {
      total: "대인관계운의 전체 결론입니다.",
      core: "관계에서 가장 안정적으로 드러나는 부분입니다.",
      watch: "관계가 오래 이어지는 데 부담이 되는 조건입니다.",
      coreLead: "대인관계운은 신뢰, 영향력, 거리감에서 갈립니다.",
    },
    timing: {
      total: "시기운의 전체 결론입니다.",
      core: "좋은 시기에 가장 먼저 드러나는 부분입니다.",
      watch: "중요한 해의 성과를 늦출 수 있어 먼저 살필 부분입니다.",
      coreLead: "좋은 해와 주의할 해는 사건의 성격이 다르게 나타납니다.",
    },
  };
    return copies[domainKey] || {
      total: `${domainTitle}의 전체 결론입니다.`,
      core: `${domainTitle}에서 가장 분명하게 드러나는 부분입니다.`,
      watch: `${domainTitle}에서 먼저 살필 부분입니다.`,
      coreLead: `${domainTitle}의 강약을 가르는 기준입니다.`,
    };
}

function renderDomainQuickBrief(section, summaryScore, summaryLevel, representativeMetrics, featureAxes) {
  const verdict = section && section.section_verdict ? section.section_verdict : {};
  const { strongest, weakest } = domainMetricExtremes(representativeMetrics, featureAxes);
  const strongScore = Number(verdict.strong_score);
  const watchScore = Number(verdict.watch_score);
  const domainTitle = sectionDisplayTitle(section);
  const domainKey = section && section.domain ? section.domain : "default";
  const copy = domainQuickBriefCopy(domainKey, domainTitle);
  const rows = [
    {
      label: (Number.isFinite(strongScore) ? strongScore : strongest && strongest.toneScore) >= 70 ? "강한 지표" : "주요 지표",
      title: verdict.strong_label || (strongest && strongest.label) || "",
      body: copy.core,
      toneScore: Number.isFinite(strongScore) ? strongScore : strongest && strongest.toneScore,
      target: "domain-metrics",
    },
    {
      label: "주의 지표",
      title: displayWatchTitle(verdict.watch_label || (weakest && weakest.label) || ""),
      body: copy.watch,
      toneScore: Number.isFinite(watchScore) ? watchScore : weakest && weakest.toneScore,
      target: featureAxes.length || representativeMetrics.length ? "domain-metrics" : "domain-verdict",
    },
  ].filter((row) => row.title || Number.isFinite(row.toneScore));
  if (!rows.length) return "";
  return `
    <div class="domain-quick-brief" aria-label="${escapeHtml(domainTitle)} 요약">
      ${rows.map((row) => `
        <button class="domain-quick-row ${metricToneClass(row.toneScore)}" type="button" data-scroll-target="${escapeHtml(row.target)}">
          <span>${escapeHtml(row.label)}</span>
          <strong>${escapeHtml(row.title || "주요 지표")}</strong>
          ${Number.isFinite(row.toneScore)
            ? `<em class="metric-grade-value ${metricGradeClass(row.toneScore)}">${escapeHtml(metricGrade(row.toneScore))}</em>`
            : ""}
          <p>${escapeHtml(row.body)}</p>
        </button>
      `).join("")}
    </div>
  `;
}

function domainLeadForScore(section, summaryScore, judgmentGrade = "") {
  const summaryOpening = firstSentence(productText(section.summary || ""), "");
  const raw = summaryOpening || productText(section.lead || section.headline || "영역별 세부 분석입니다.");
  const summaryState = semanticStateForGrade(
    judgmentGrade || (Number.isFinite(summaryScore) ? judgmentGradeForScore(summaryScore, "") : ""),
  );
  let opening = firstSentence(raw, "영역별 세부 분석입니다.");
  if (summaryState !== "good") {
    opening = opening
      .replace(/에서 강합니다\.$/, "에서 비교적 안정적으로 작용합니다.")
      .replace(/이 강합니다\.$/, "이 비교적 뚜렷하게 작용합니다.")
      .replace(/가 강합니다\.$/, "가 비교적 뚜렷하게 작용합니다.")
      .replace(/얻는 사주입니다\.$/, "얻는 방식으로 작용합니다.")
      .replace(/지녔습니다\.$/, "나타납니다.");
  }
  const representativeMetrics = metricItemsFrom(section, "representative_metrics", 12);
  const featureAxes = metricItemsFrom(section, "feature_axes", 24);
  const { weakest } = domainMetricExtremes(representativeMetrics, featureAxes);
  const watchScore = Number(weakest && weakest.score);
  const watchLabel = displayWatchTitle(productText(weakest && weakest.label || ""));
  const watchGrade = weakest && Number.isFinite(watchScore)
    ? rawMetricGradeForItem(weakest.item, watchScore)
    : "";
  const watchState = semanticStateForGrade(watchGrade);
  if (watchLabel && watchState === "bad") {
    const normalizedOpening = normalizeMetricDescriptionKey(opening);
    const normalizedWatchLabel = normalizeMetricDescriptionKey(watchLabel);
    if (normalizedWatchLabel && normalizedOpening.includes(normalizedWatchLabel)) {
      const domainKey = section && section.domain ? section.domain : "default";
      opening = domainQuickBriefCopy(domainKey, sectionDisplayTitle(section)).coreLead;
    }
  }
  if (!watchLabel || watchState !== "bad") return opening;
  const domainTitle = sectionDisplayTitle(section);
  return `${opening} 다만 ${watchLabel}${subjectParticle(watchLabel)} ${domainTitle}의 전체 수준을 낮추는 지점입니다.`;
}

function renderDomainDetail(section, sections, domainContracts, selectedIndex = 0, detailUnit = null) {
  if (!section) {
    return `<section class="paper-card"><h2>분야별 총운</h2><p>표시할 운세 영역이 없습니다.</p></section>`;
  }
  const topics = Array.isArray(section.topic_items) ? section.topic_items : [];
  const details = Array.isArray(section.detail_blocks) ? section.detail_blocks : [];
  const representativeMetrics = metricItemsFrom(section, "representative_metrics", 6);
  const featureAxes = metricItemsFrom(section, "feature_axes", 16);
  const domainKey = section.domain || "default";
  const isTimingDomain = domainKey === "timing";
  const summaryScore = sectionMetricScore(section);
  const currentTitle = sectionDisplayTitle(section);
  const keyMetrics = selectDomainKeyMetrics(section, representativeMetrics, featureAxes);
  const unifiedMetrics = mergeMetricItems(keyMetrics, representativeMetrics, featureAxes);
  const rawSummaryGrade = rawAggregateGradeFromMetricItems(
    unifiedMetrics,
    rawSectionAggregateGrade(section, ""),
  );
  const displaySummaryGrade = aggregateGradeFromMetricItems(
    unifiedMetrics,
    sectionAggregateGrade(section, ""),
  );
  return `
    <section class="paper-card domain-detail-head ${metricToneClassFromGrade(displaySummaryGrade)}">
      <div class="domain-title-row">
        <div>
          <h2>${escapeHtml(currentTitle)}</h2>
          <p>${escapeHtml(domainLeadForScore(section, summaryScore, rawSummaryGrade))}</p>
        </div>
        ${
          metricGradeRank(displaySummaryGrade) >= 0
            ? `<div class="domain-score">
                <strong class="metric-grade-value ${metricGradeClassFromLabel(displaySummaryGrade)}">${escapeHtml(displaySummaryGrade)}</strong>
                <span>종합 등급</span>
              </div>`
            : ""
      }
      </div>
      ${renderAggregateGradeBar(displaySummaryGrade)}
      <div data-scroll-anchor="domain-overview"></div>
      ${renderDomainScoreSummary(section, summaryScore, displaySummaryGrade)}
      ${renderDomainMetricOverview(section, unifiedMetrics)}
      ${isTimingDomain ? renderTimingDomainSignals(section) : renderDomainUnifiedMetrics(section, unifiedMetrics)}
    </section>
  `;
}

function metricIdentity(item) {
  return normalizeDetailAction(productText(metricLabel(item, ""))).toLowerCase();
}

function appendUniqueMetric(target, item) {
  if (!item || !metricLabel(item, "")) return;
  const identity = metricIdentity(item);
  if (!identity || target.some((existing) => metricIdentity(existing) === identity)) return;
  target.push(item);
}

function mergeMetricItems(...groups) {
  const merged = [];
  groups.forEach((group) => {
    asArray(group).forEach((item) => appendUniqueMetric(merged, item));
  });
  return merged;
}

function findMetricByLabel(items, label) {
  const target = normalizeDetailAction(productText(label || "")).toLowerCase();
  if (!target) return null;
  const pool = asArray(items);
  return (
    pool.find((item) => metricIdentity(item) === target) ||
    pool.find((item) => {
      const identity = metricIdentity(item);
      return identity && (identity.includes(target) || target.includes(identity));
    }) ||
    null
  );
}

function selectDomainKeyMetrics(section, representativeMetrics, featureAxes) {
  const verdict = section && section.section_verdict ? section.section_verdict : {};
  const pool = [...asArray(representativeMetrics), ...asArray(featureAxes)]
    .filter((item) => item && Number.isFinite(metricScore(item)));
  const positivePool = pool.filter((item) => metricPolarity(item) !== "risk");
  const selected = [];
  appendUniqueMetric(selected, findMetricByLabel(pool, verdict.strong_label));
  appendUniqueMetric(
    selected,
    [...(positivePool.length ? positivePool : pool)].sort((a, b) => metricToneScore(b) - metricToneScore(a))[0],
  );
  appendUniqueMetric(selected, findMetricByLabel(pool, verdict.watch_label));
  appendUniqueMetric(selected, [...pool].sort((a, b) => metricToneScore(a) - metricToneScore(b))[0]);
  for (const item of asArray(representativeMetrics)) {
    appendUniqueMetric(selected, item);
    if (selected.length >= 3) break;
  }
  return selected.slice(0, 3);
}

function renderDomainScoreSummary(section, summaryScore, summaryLevel) {
  const verdict = section && section.section_verdict ? section.section_verdict : {};
  const strongScore = Number(verdict.strong_score);
  const watchScore = Number(verdict.watch_score);
  const metricPool = [
    ...metricItemsFrom(section, "representative_metrics", 12),
    ...metricItemsFrom(section, "feature_axes", 24),
  ];
  const strongMetric = findMetricByLabel(metricPool, verdict.strong_label);
  const watchMetric = findMetricByLabel(metricPool, verdict.watch_label);
  const watchToneScore = watchMetric ? metricToneScore(watchMetric, watchScore) : watchScore;
  const rows = [
    {
      label: verdict.strong_caption || "강점",
      title: verdict.strong_label || "",
      toneScore: strongMetric ? metricToneScore(strongMetric, strongScore) : strongScore,
    },
    {
      label: displayWatchCaption(verdict.watch_caption, watchToneScore),
      title: displayWatchTitle(verdict.watch_label || ""),
      toneScore: watchToneScore,
    },
  ].filter((item) => item.title || Number.isFinite(item.toneScore));
  if (!rows.length) return "";
  return `
    <div class="domain-score-summary" data-scroll-anchor="domain-verdict">
      ${rows.map((item) => `
        <article class="${metricToneClass(item.toneScore)}">
          <span>${escapeHtml(productText(item.label))}</span>
          <strong>${escapeHtml(productText(item.title))}</strong>
          ${Number.isFinite(item.toneScore) ? renderMetricLevelBadge("확인", item.toneScore) : ""}
        </article>
      `).join("")}
    </div>
  `;
}

function renderDomainMetricOverview(section, metrics) {
  const visible = asArray(metrics)
    .filter((item) => item && metricLabel(item, "") && Number.isFinite(metricScore(item)))
    .slice(0, 24);
  if (!visible.length) return "";
  return `
    <section class="domain-metric-overview" aria-label="${escapeHtml(domainMetricSectionTitle(section))} 한눈에 보는 지표">
      <div class="domain-metric-overview-head">
        <strong>한눈에 보는 지표</strong>
        <span>${escapeHtml(domainMetricSectionTitle(section))}의 세부 등급입니다.</span>
      </div>
      <div class="domain-metric-overview-list">
        ${visible.map((item) => renderDomainMetricOverviewRow(item)).join("")}
      </div>
    </section>
  `;
}

function renderDomainMetricOverviewRow(item) {
  const score = metricScore(item);
  const label = metricLabel(item);
  const level = metricLevelForItem(item, score, item.level || item.value || "");
  const compactLabelLength = Array.from(label.replace(/\s/g, "")).length;
  const longLabelClass = compactLabelLength >= 7 ? " is-long-label" : "";
  return `
    <div class="domain-metric-overview-row ${metricToneClassForItem(item, score)}${metricPolarity(item) === "risk" ? " metric-risk-axis" : ""}${longLabelClass}">
      <span>${escapeHtml(label)}</span>
      <div class="domain-metric-overview-bar">
        ${renderMetricBarForItem(item, score)}
      </div>
      ${renderMetricLevelBadgeForItem(item, score, level)}
    </div>
  `;
}

function domainMetricSectionTitle(section) {
  const domain = section && section.domain ? section.domain : "default";
  const titles = {
    personality: "성격 지표",
    money: "재물 지표",
    career: "직업 지표",
    love: "연애 지표",
    marriage: "결혼 지표",
    timing: "시기운 지표",
    life: "인생 구간 지표",
    honor: "명예 지표",
    social: "대인관계 지표",
  };
  return titles[domain] || `${sectionDisplayTitle(section)} 지표`;
}

function renderDomainUnifiedMetrics(section, metrics) {
  const visible = asArray(metrics);
  if (!visible.length) return "";
  const domainCopy = domainQuickBriefCopy(section && section.domain ? section.domain : "default", sectionDisplayTitle(section));
  return `
    <details class="metric-detail-disclosure" data-scroll-anchor="domain-metrics">
      <summary>
        <span>
          <strong>지표 설명 보기</strong>
          <small>${escapeHtml(domainCopy.coreLead || "각 점수가 실제 생활에서 뜻하는 바를 확인합니다.")}</small>
        </span>
        <em>${visible.length}개</em>
      </summary>
      <div class="metric-grid metric-grid-detail metric-grid-unified">
        ${visible.map((item) => renderMetricCard(item, { isKeyMetric: true })).join("")}
      </div>
    </details>
  `;
}

function renderTimingDomainSignals(section) {
  const timingMap = section && section.timing_map ? section.timing_map : {};
  const goodEvents = asArray(timingMap.goodHighlights).slice(0, 3);
  const cautionEvents = asArray(timingMap.cautionHighlights).slice(0, 3);
  const hasSignals = goodEvents.length || cautionEvents.length;
  if (!hasSignals) return "";
  return `
    <div class="domain-subhead">
      <strong>시기별 운세</strong>
      <span>좋은 시기와 조심할 시기를 연도로 정리합니다.</span>
    </div>
    ${(goodEvents.length || cautionEvents.length) ? `
      <div class="timing-inline-columns">
        ${renderTimingInlineColumn("좋은 시기", goodEvents, "good")}
        ${renderTimingInlineColumn("조심할 시기", cautionEvents, "caution")}
      </div>
    ` : ""}
  `;
}

function renderTimingInlineColumn(title, events, tone = "good") {
  const visible = timingYearOnlyItems(events, 8);
  if (!visible.length) return "";
  return `
    <div class="timing-inline-column ${tone === "caution" ? "is-caution" : "is-good"}">
      <strong>${escapeHtml(title)}</strong>
      <div class="timing-year-pills">${visible.map((year) => `<b>${escapeHtml(year)}</b>`).join("")}</div>
    </div>
  `;
}

function renderMetricCard(item, options = {}) {
  const score = metricScore(item);
  const level = metricLevelForItem(item, score, item.level || item.value || "");
  const label = metricLabel(item);
  const bodyHtml = options.annualDomainKey
    ? renderAnnualMetricBodyParagraphs(item, options.annualDomainKey)
    : renderMetricBodyParagraphs(item);
  const compactLabelLength = label.replace(/[\s·/()-]/g, "").length;
  const compactLevelLength = String(level || "").replace(/\s/g, "").length;
  const needsBreathingRoom =
    compactLabelLength >= 5 ||
    (compactLabelLength >= 4 && compactLevelLength >= 4) ||
    /[·/]/.test(label);
  const wideClass = needsBreathingRoom ? " is-wide" : "";
  return `
    <article class="metric-card ${metricToneClassForItem(item, score)}${metricPolarity(item) === "risk" ? " metric-risk-axis" : ""}${wideClass}">
      <header>
        <strong>${escapeHtml(label)}</strong>
        ${renderMetricLevelBadgeForItem(item, score, level)}
      </header>
      ${renderMetricBarForItem(item, score)}
      ${bodyHtml}
    </article>
  `;
}

function renderTopicCard(topic) {
  const score = metricScore(topic);
  const level = metricLevelForItem(topic, score, topic.value || "");
  return `
    <article class="topic-card metric-card ${metricToneClassForItem(topic, score)}${metricPolarity(topic) === "risk" ? " metric-risk-axis" : ""}">
      <header>
        <strong>${escapeHtml(metricLabel(topic))}</strong>
        ${renderMetricLevelBadgeForItem(topic, score, level)}
      </header>
      ${renderMetricBarForItem(topic, score)}
      ${renderMetricBodyParagraphs(topic, "세부 해석입니다.")}
    </article>
  `;
}

function normalizeDetailAction(text) {
  return String(text || "")
    .replace(/[\s·ㆍ,./|:;_\-–—()[\]{}]+/g, "")
    .trim();
}

function renderDetailBlocks(blocks, limit = 6) {
  const seenActions = new Set();
  return asArray(blocks)
    .slice(0, limit)
    .map((block) => renderDetailBlock(block, seenActions))
    .join("");
}

function renderDetailParagraph(className, label, text) {
  const body = productText(String(text || "").trim());
  if (!body) return "";
  return `<p class="${escapeHtml(className)}"><span class="detail-part-label">${escapeHtml(label)}</span>${escapeHtml(body)}</p>`;
}

function detailBasisKeywords(text) {
  const body = productText(String(text || "").trim());
  const match = body.match(/핵심어\s*[:：]\s*(.+)$/);
  if (!match) return [];
  return unique(
    match[1]
      .split(/[,·ㆍ/|]+/)
      .map((item) => item.trim())
      .filter(Boolean),
    8,
  );
}

function renderDetailBlock(block, seenActions = null) {
  const bullets = Array.isArray(block.bullets) ? block.bullets : [];
  const action = productText(String(block.action || block.response || "").trim());
  const actionKey = normalizeDetailAction(action);
  const repeatedAction = Boolean(actionKey && seenActions && seenActions.has(actionKey));
  if (actionKey && seenActions && !repeatedAction) seenActions.add(actionKey);
  const basis = productText(String(block.basis_summary || block.evidence || block.basis || "").trim());
  const score = metricScore(block);
  const toneScore = Number.isFinite(score) ? metricToneScore(block, score) : null;
  const grade = Number.isFinite(toneScore) ? metricGrade(toneScore) : "";
  const metricLabel = productText(String(block.metric_label || "").trim());
  const body = productText(String(block.body || "").trim());
  const basisKeywords = detailBasisKeywords(basis);
  const basisIsKeywordOnly = Boolean(basisKeywords.length && /^핵심어\s*[:：]/.test(basis));
  return `
    <article class="detail-block ${block.tone ? `detail-${escapeHtml(block.tone)}` : ""}">
      <header>
        <strong>${escapeHtml(productText(block.title || "상세 해석"))}</strong>
        ${grade ? `<em class="detail-level metric-grade-value ${metricGradeClass(toneScore)}">${escapeHtml(grade)}</em>` : ""}
      </header>
      ${metricLabel && metricLabel !== block.title ? `<span class="detail-metric-label">${escapeHtml(metricLabel)}</span>` : ""}
      ${Number.isFinite(score) ? renderMetricBarForItem(block, score) : ""}
      ${renderDetailParagraph("detail-interpretation", "풀이", body)}
      ${basisIsKeywordOnly ? "" : renderDetailParagraph("detail-basis", "근거", basis)}
      ${bullets.length ? `<div class="tag-row">${bullets.slice(0, 3).map((item) => `<span>${escapeHtml(productText(item))}</span>`).join("")}</div>` : ""}
      ${basisKeywords.length ? `<div class="tag-row detail-keyword-row">${basisKeywords.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div>` : ""}
      ${action && !repeatedAction ? renderDetailParagraph("detail-action", "대응", action) : ""}
    </article>
  `;
}

function renderTimingContract(timingContract) {
  if (!timingContract) {
    return "";
  }
  const goodYears = unique(asArray(timingContract.good_years).map(timingYearLabel), 10);
  const cautionYears = unique(asArray(timingContract.caution_years).map(timingYearLabel), 10);
  return renderContractSummary(
    "시기운",
    "좋은 시기와 조심할 시기를 연도로 정리합니다.",
    [
      { label: "좋은 시기", value: goodYears.join(", ") },
      { label: "조심할 시기", value: cautionYears.join(", ") },
    ],
    [
      ...goodYears.slice(0, 4),
      ...cautionYears.slice(0, 4),
    ],
  );
}

function timingEventYearAge(event) {
  if (!event) return "";
  const yearText = String(event.year || "").trim();
  const year = yearText ? (yearText.includes("년") ? yearText : `${yearText}년`) : "";
  return year;
}

function timingDecadeEventArray(value) {
  if (Array.isArray(value)) return value.filter(Boolean);
  return value && typeof value === "object" ? [value] : [];
}

function normalizedTimingDecadeGroups(timingMap, goodEvents = [], cautionEvents = []) {
  const rawGroups = asArray(timingMap.decadeHighlights || timingMap.decade_highlights);
  if (rawGroups.length) {
    return rawGroups.map((group) => ({
      label: String(group.label || group.ageLabel || group.age_label || "").trim(),
      good: timingDecadeEventArray(group.good || group.goodHighlights || group.good_highlights).slice(0, 2),
      caution: timingDecadeEventArray(group.caution || group.cautionHighlights || group.caution_highlights).slice(0, 2),
    })).filter((group) => group.label);
  }
  return [
    {
      label: "주요 시기",
      good: asArray(goodEvents).slice(0, 2),
      caution: asArray(cautionEvents).slice(0, 2),
    },
  ];
}

function renderTimingDecadeCell(title, events, tone = "good") {
  const years = timingYearOnlyItems(events, 2);
  const toneClass = tone === "caution" ? "is-caution" : "is-good";
  return `
    <div class="timing-decade-cell ${toneClass}">
      <b>${escapeHtml(title)}</b>
      ${years.length
        ? `<div class="timing-year-pills">${years.map((year) => `<span>${escapeHtml(year)}</span>`).join("")}</div>`
        : `<em>뚜렷한 연도 없음</em>`}
    </div>
  `;
}

function renderTimingDecadeRow(group) {
  return `
    <article class="timing-decade-row">
      <strong>${escapeHtml(group.label)}</strong>
      <div class="timing-decade-columns">
        ${renderTimingDecadeCell("좋은 시기", group.good, "good")}
        ${renderTimingDecadeCell("조심할 시기", group.caution, "caution")}
      </div>
    </article>
  `;
}

function timingEventKeywords(event, limit = 4) {
  if (!event) return [];
  const raw = event.keywordItems || event.keyword_items || event.keywords || event.structureKeywords || [];
  const parts = Array.isArray(raw)
    ? raw
    : String(raw || "")
        .split(/[·,\/|]+/)
        .map((item) => item.trim());
  return unique(parts.map(displayToken).filter(Boolean), limit);
}

function normalizeTimingToken(value) {
  return String(value || "")
    .replace(/[\s·ㆍ,./|:;_\-–—()[\]{}]+/g, "")
    .trim();
}

function sameTimingToken(a, b) {
  const left = normalizeTimingToken(a);
  const right = normalizeTimingToken(b);
  return Boolean(left && right && left === right);
}

function filterTimingKeywordsForTitle(keywords, title, limit = 3) {
  const tokens = unique(asArray(keywords).map(displayToken).filter(Boolean), limit + 2);
  if (sameTimingToken(tokens.join(""), title)) return [];
  return tokens
    .filter((keyword) => !sameTimingToken(keyword, title))
    .slice(0, limit);
}

function stripTimingTitlePrefix(text, title) {
  const raw = String(text || "").trim();
  const normalizedTitle = normalizeTimingToken(title);
  if (!raw || !normalizedTitle) return raw;
  let normalizedHead = "";
  let endIndex = 0;
  for (let index = 0; index < raw.length; index += 1) {
    const normalizedChar = normalizeTimingToken(raw[index]);
    if (!normalizedChar) {
      if (normalizedHead) endIndex = index + 1;
      continue;
    }
    normalizedHead += normalizedChar;
    endIndex = index + 1;
    if (normalizedHead.length >= normalizedTitle.length) break;
  }
  if (normalizedHead === normalizedTitle) {
    return raw.slice(endIndex).replace(/^[\s·ㆍ,./|:;_\-–—()[\]{}]+/g, "").trim();
  }
  return raw;
}

function renderTimingSummaryBoard(map, timingContract) {
  const publicCards = asArray(map && map.publicSummaryCards).slice(0, 3);
  const summaryCards = publicCards.length ? publicCards : asArray(map && map.summaryCards).slice(0, 3);
  const fallbackCards = !summaryCards.length && timingContract
    ? [
        { label: "좋은 시기", title: "좋은 시기", value: unique(asArray(timingContract.good_years).map(timingYearLabel), 5).join(" / "), tone: "good" },
        { label: "조심할 시기", title: "조심할 시기", value: unique(asArray(timingContract.caution_years).map(timingYearLabel), 5).join(" / "), tone: "risk" },
      ]
    : [];
  const cards = summaryCards.length ? summaryCards : fallbackCards;
  if (!cards.length) return "";
  return `
    <section class="paper-card timing-summary-board">
      <h2>시기 요약</h2>
      <div class="timing-summary-grid">
        ${cards.map((card) => {
          const title = productText(card.title || "");
          const keywords = filterTimingKeywordsForTitle(card.keywords, title, 3);
          return `
          <article class="${card.tone === "risk" ? "is-caution" : card.tone === "good" ? "is-good" : ""}">
            <span>${escapeHtml(productText(card.label || ""))}</span>
            <strong>${escapeHtml(title)}</strong>
            ${card.yearAge ? `<em>${escapeHtml(card.yearAge)}</em>` : ""}
            <p>${escapeHtml(compactText(productText(stripTimingTitlePrefix(card.body || card.value || "", title)), 104))}</p>
            ${keywords.length ? `<div class="tag-row">${keywords.map((keyword) => `<span>${escapeHtml(keyword)}</span>`).join("")}</div>` : ""}
          </article>
        `;
        }).join("")}
      </div>
    </section>
  `;
}

function renderTimingEventCard(event, tone = "good") {
  if (!event) return "";
  const title = event.title || event.focus || "주요 연도";
  const keywords = filterTimingKeywordsForTitle(timingEventKeywords(event, 5), title, 4);
  const line = stripTimingTitlePrefix(event.decisionLine || event.productLine || event.focusLine || event.summary || "", title);
  const pillars = [event.daeunPillar ? `${event.daeunPillar} 대운` : "", event.yearPillar ? `${event.yearPillar} 세운` : ""]
    .filter(Boolean)
    .join(" · ");
  return `
    <article class="timing-event-card ${tone === "caution" ? "is-caution" : "is-good"}">
      <header>
        <span>${escapeHtml(timingEventYearAge(event))}</span>
        <em>${tone === "caution" ? "주의" : "상승"}</em>
      </header>
      <strong>${escapeHtml(title)}</strong>
      ${line ? `<p>${escapeHtml(compactText(line, 96))}</p>` : ""}
      ${keywords.length ? `<div class="tag-row">${keywords.map((keyword) => `<span>${escapeHtml(keyword)}</span>`).join("")}</div>` : ""}
      ${pillars ? `<small>${escapeHtml(pillars)}</small>` : ""}
    </article>
  `;
}

function renderTimingEventColumn(title, events, tone = "good") {
  const visible = asArray(events).filter(Boolean).slice(0, 4);
  if (!visible.length) return "";
  return `
    <section class="paper-card timing-event-column ${tone === "caution" ? "is-caution" : "is-good"}">
      <h2>${escapeHtml(title)}</h2>
      <div class="timing-event-grid">
        ${visible.map((event) => renderTimingEventCard(event, tone)).join("")}
      </div>
    </section>
  `;
}

function timingEventNumericYear(event) {
  if (!event) return 9999;
  const yearText = String(event.year || "").trim();
  const match = yearText.match(/\d{4}/);
  if (!match) return 9999;
  const year = Number(match[0]);
  return Number.isFinite(year) ? year : 9999;
}

function buildTimingTimelineItems(goodEvents, cautionEvents, goodYears, cautionYears, timing = {}) {
  const fallbackGood = asArray(goodYears).map((year) => ({
    year,
    title: year,
    decisionLine: timing.good || "",
  }));
  const fallbackCaution = asArray(cautionYears).map((year) => ({
    year,
    title: year,
    decisionLine: timing.caution || "",
  }));
  const source = [
    ...(asArray(goodEvents).length ? asArray(goodEvents) : fallbackGood).map((event) => ({ ...event, timelineTone: "good" })),
    ...(asArray(cautionEvents).length ? asArray(cautionEvents) : fallbackCaution).map((event) => ({ ...event, timelineTone: "caution" })),
  ];
  const seen = new Set();
  return source
    .filter(Boolean)
    .sort((a, b) => timingEventNumericYear(a) - timingEventNumericYear(b))
    .filter((event) => {
      const key = `${timingEventNumericYear(event)}-${event.timelineTone}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, 8);
}

function renderTimingFlowTimeline(events, rangeLabel = "주요 연도") {
  const visible = asArray(events).filter(Boolean).slice(0, 8);
  if (!visible.length) return "";
  return `
    <section class="paper-card timing-flow-timeline">
      <header>
        <span>${escapeHtml(rangeLabel)}</span>
        <h2>시기별 운세</h2>
        <p>좋은 시기와 조심할 시기를 연도별로 정리했습니다.</p>
      </header>
      <div class="timing-flow-list">
        ${visible.map((event) => {
          const tone = event.timelineTone === "caution" ? "caution" : "good";
          const title = productText(event.title || (tone === "caution" ? "조심할 시기" : "좋은 시기"));
          const line = productText(stripTimingTitlePrefix(event.decisionLine || event.productLine || event.focusLine || event.summary || "", title));
          const keywords = filterTimingKeywordsForTitle(timingEventKeywords(event, 4), title, 3);
          return `
            <article class="${tone === "caution" ? "is-caution" : "is-good"}">
              <i aria-hidden="true"></i>
              <div>
                <header>
                  <strong>${escapeHtml(timingEventYearAge(event) || event.year || "주요 시기")}</strong>
                  <em>${tone === "caution" ? "조심" : "좋음"}</em>
                </header>
                <b>${escapeHtml(title)}</b>
                ${line ? `<p>${escapeHtml(compactText(line, 88))}</p>` : ""}
                ${keywords.length ? `<div class="tag-row">${keywords.map((keyword) => `<span>${escapeHtml(keyword)}</span>`).join("")}</div>` : ""}
              </div>
            </article>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

function renderTimingDomainYearCell(event, tone = "good") {
  if (!event) {
    return `<div class="timing-domain-cell ${tone === "caution" ? "is-caution" : "is-good"}"><span>확인 중</span></div>`;
  }
  const keywords = timingEventKeywords(event, 2).join(" · ");
  return `
    <div class="timing-domain-cell ${tone === "caution" ? "is-caution" : "is-good"}">
      <span>${tone === "caution" ? "주의" : "상승"}</span>
      <strong>${escapeHtml(timingEventYearAge(event))}</strong>
      <p>${escapeHtml(event.title || keywords || "주요 연도")}</p>
    </div>
  `;
}

function renderTimingDomainYearHighlights(items) {
  const visible = asArray(items).filter(Boolean).slice(0, 6);
  if (!visible.length) return "";
  return `
    <section class="paper-card timing-domain-years">
      <h2>영역별 대표 연도</h2>
      <p>재물, 직업, 인연, 결혼에서 특히 두드러지는 연도를 따로 정리했습니다.</p>
      <div class="timing-domain-list">
        ${visible.map((item) => `
          <article class="timing-domain-row">
            <h3>${escapeHtml(item.domainLabel || item.domain_label || item.domain || "분야별 총운")}</h3>
            <div>
              ${renderTimingDomainYearCell(item.good, "good")}
              ${renderTimingDomainYearCell(item.caution, "caution")}
            </div>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function renderTimingDetail(profile, sections, chart, timingContract, detailUnit = null) {
  const timing = profile.timing || {};
  const timingSection = sections.find((section) => section.domain === "timing") || {};
  const timingMap = timingSection.timing_map || {};
  const goodEvents = asArray(timingMap.goodHighlights);
  const cautionEvents = asArray(timingMap.cautionHighlights);
  const decadeGroups = normalizedTimingDecadeGroups(timingMap, goodEvents, cautionEvents);
  return `
    <section class="paper-card timing-year-board timing-decade-board">
      <h2>시기운</h2>
      <p>좋은 시기와 조심할 시기를 10세 단위로 정리했습니다.</p>
      <div class="timing-decade-list">
        ${decadeGroups.map(renderTimingDecadeRow).join("")}
      </div>
    </section>
  `;
}

function renderBasis(chart, factors, detailUnit) {
  return `
    ${renderIntegratedPaljaBasis(chart)}
    ${renderAnalysisDetailUnit(detailUnit, "명식 기준", "월령, 지지, 지장간을 기준으로 정리한 명식 요소입니다.", factors, [""])}
  `;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("is-visible"), 2200);
}

function normalizeAnalysisCopyText(value) {
  const lines = String(value || "")
    .replace(/\u00a0/g, " ")
    .split(/\r?\n+/)
    .map((line) => line.replace(/[ \t]+/g, " ").trim())
    .filter(Boolean);
  return lines.filter((line, index) => line !== lines[index - 1]).join("\n");
}

function customerTextFromRenderedAnalysis(html) {
  const staging = document.createElement("div");
  staging.className = "analysis-copy-staging";
  staging.innerHTML = String(html || "");
  staging
    .querySelectorAll("script, style, .detail-tabs, .contextual-copy-actions, [aria-hidden='true']")
    .forEach((element) => element.remove());
  staging
    .querySelectorAll([
      ".metric-detail-disclosure > summary > span > strong",
      ".metric-detail-disclosure > summary > em",
      ".contextual-evidence-group > summary small",
      ".contextual-evidence-subgroup > summary small",
    ].join(", "))
    .forEach((element) => element.remove());
  staging.querySelectorAll("details").forEach((element) => {
    element.open = true;
  });
  Object.assign(staging.style, {
    position: "fixed",
    left: "-100000px",
    top: "0",
    width: "680px",
    opacity: "0",
    pointerEvents: "none",
    zIndex: "-1",
  });
  document.body.appendChild(staging);
  const text = normalizeAnalysisCopyText(staging.innerText || staging.textContent || "");
  staging.remove();
  return text;
}

function buildFullAnalysisCopyText() {
  if (!state.detailPayload) return "";
  const {
    chart,
    profile,
    sections,
    factors,
    detailUnits,
    engineContract,
    screenContract,
  } = state.detailPayload;
  const chunks = [];
  const typeTitle = productText(profile && profile.profile_type || "사주 분석 결과");
  const summaryContract = screenContract && screenContract.summary || {};
  const typeSummary = firstSentence(
    summaryContract.headline || profile && (profile.headline || profile.summary),
    "",
  );
  const name = currentUserDisplayName();
  chunks.push([
    "사주 이현 분석 결과",
    name ? `${name}님의 사주` : "",
    typeTitle ? `타고난 기질 유형: ${typeTitle}` : "",
    typeSummary,
  ].filter(Boolean).join("\n"));

  const visibleDomains = new Set(["personality", "money", "career", "love", "marriage", "honor", "social"]);
  asArray(sections).forEach((section, index) => {
    if (!section || !visibleDomains.has(String(section.domain || ""))) return;
    const html = withMetricDisplayContext("domains", () => renderDomainDetail(
      section,
      sections,
      engineContract && engineContract.domains,
      index,
      detailUnits && detailUnits.domains,
    ));
    const text = customerTextFromRenderedAnalysis(html);
    if (text) chunks.push(text);
  });

  const timingText = customerTextFromRenderedAnalysis(renderTimingDetail(
    profile,
    sections,
    chart,
    engineContract && engineContract.timing,
    detailUnits && detailUnits.timing,
  ));
  if (timingText) chunks.push(timingText);

  ["year_2026", "year_2027"].forEach((domainKey) => {
    const annualSection = findSectionByDomain(sections, domainKey);
    if (!annualSection) return;
    const html = withMetricDisplayContext(domainKey, () => renderAnnualDetail(annualSection, domainKey));
    const text = customerTextFromRenderedAnalysis(html);
    if (text) chunks.push(text);
  });

  const contextualText = customerTextFromRenderedAnalysis(renderContextualDetail(
    engineContract && engineContract.gyeokguk_contextual,
    detailUnits && detailUnits.contextual,
    chart,
    factors,
    detailUnits && detailUnits.basis,
  ));
  if (contextualText) chunks.push(contextualText);
  return chunks.filter(Boolean).join("\n\n").trim();
}

async function writeClipboardText(text) {
  if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
    await navigator.clipboard.writeText(text);
    return;
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.left = "-100000px";
  document.body.appendChild(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  textarea.remove();
  if (!copied) throw new Error("clipboard_unavailable");
}

async function copyFullAnalysisResult(button) {
  if (!state.detailLoaded || !state.detailPayload) {
    showToast("전체 분석을 불러온 뒤 다시 시도해 주세요.");
    return;
  }
  const originalLabel = button && button.textContent;
  if (button) {
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
  }
  try {
    const text = buildFullAnalysisCopyText();
    if (!text) throw new Error("analysis_text_empty");
    await writeClipboardText(text);
    showToast("분석 결과 전체를 복사했습니다.");
  } catch (_error) {
    showToast("분석 결과를 복사하지 못했습니다.");
  } finally {
    if (button) {
      button.disabled = false;
      button.removeAttribute("aria-busy");
      button.textContent = originalLabel || "";
    }
  }
}

async function sharePage() {
  const title = "사주 이현";
  const text = "생년월일과 태어난 시간을 바탕으로 사주 유형과 분야별 흐름을 분석합니다.";
  const url = "https://aisajuleehyeon.com/";
  try {
    if (navigator.share) {
      await navigator.share({ title, text, url });
      return;
    }
  } catch (error) {
    if (error && error.name === "AbortError") {
      return;
    }
  }
  try {
    await navigator.clipboard.writeText(`${text}\n${url}`);
    showToast("공유 문구를 복사했습니다.");
  } catch (_error) {
    showToast("공유 기능을 사용할 수 없습니다.");
  }
}
