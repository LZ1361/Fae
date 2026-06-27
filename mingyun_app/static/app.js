const $ = (selector) => document.querySelector(selector);

const form = $("#readingForm");
const modelConfigForm = $("#modelConfigForm");
const modelSelect = $("#modelSelect");
const testModelBtn = $("#testModelBtn");
const modelStatus = $("#modelStatus");
const readingOutput = $("#readingOutput");
const evidenceList = $("#evidenceList");
const limitsList = $("#limitsList");
const usageText = $("#usageText");
const canvas = $("#elementCanvas");
const applyProviderPresetBtn = $("#applyProviderPresetBtn");
const saveLocalModelBtn = $("#saveLocalModelBtn");
const resetLocalModelsBtn = $("#resetLocalModelsBtn");
const modelList = $("#modelList");
const toastStack = $("#toastStack");

const STORAGE_MODELS = "mingyun.customModels";
const STORAGE_KEYS = "mingyun.apiKeys";
const STORAGE_DISABLED = "mingyun.disabledModels";
const STORAGE_SELECTED = "mingyun.selectedModel";
const STORAGE_READING_DRAFT = "mingyun.readingDraft";

let registryModels = [];
let allModels = [];

const providerDefaults = {
  mock: {
    provider: "mock",
    api_format: "local",
    base_url: "",
    model_id: "mock-local",
    display_name: "本地模拟模型",
    temperature: 0.2,
    max_tokens: 1200,
    param_overrides: {},
  },
  deepseek: {
    provider: "deepseek",
    api_format: "openai_compatible",
    base_url: "https://api.deepseek.com",
    model_id: "deepseek-v4-pro",
    display_name: "DeepSeek V4 Pro",
    temperature: 0.35,
    max_tokens: 6000,
    param_overrides: { thinking_type: "disabled" },
  },
  openai: {
    provider: "openai",
    api_format: "openai_responses",
    base_url: "https://api.openai.com/v1",
    model_id: "gpt-5.5",
    display_name: "OpenAI GPT-5.5",
    temperature: "",
    max_tokens: 6000,
    param_overrides: {},
  },
  anthropic: {
    provider: "anthropic",
    api_format: "anthropic_messages",
    base_url: "https://api.anthropic.com",
    model_id: "claude-opus-4-8",
    display_name: "Claude Opus 4.8",
    temperature: "",
    max_tokens: 6000,
    param_overrides: {},
  },
  openai_compatible: {
    provider: "openai_compatible",
    api_format: "openai_compatible",
    base_url: "http://localhost:11434/v1",
    model_id: "qwen3:8b",
    display_name: "OpenAI 兼容模型",
    temperature: 0.35,
    max_tokens: 6000,
    param_overrides: {},
  },
  custom: {
    provider: "custom",
    api_format: "openai_compatible",
    base_url: "",
    model_id: "",
    display_name: "自定义模型",
    temperature: 0.35,
    max_tokens: 6000,
    param_overrides: {},
  },
};

async function loadModels() {
  const res = await fetch("/api/models");
  const data = await res.json();
  registryModels = (data.models || []).map((model) => ({ ...model, local: false }));
  refreshModelState();
  selectModel(localStorage.getItem(STORAGE_SELECTED) || preferredModelId());
}

function refreshModelState() {
  const merged = new Map(registryModels.map((model) => [model.id, model]));
  readLocalModels().forEach((model) => merged.set(model.id, { ...model, local: true }));
  allModels = [...merged.values()];
  renderModelSelect();
  renderModelList();
}

function preferredModelId() {
  return allModels.find((model) => model.id === "deepseek-v4-pro")?.id || allModels[0]?.id || "";
}

function renderModelSelect() {
  if (!modelSelect) return;
  const enabledModels = allModels.filter(isModelEnabled);
  modelSelect.innerHTML = enabledModels
    .map((model) => {
      const origin = model.local ? "本地" : "内置";
      return `<option value="${escapeAttr(model.id)}">${escapeHtml(model.display_name)} · ${escapeHtml(model.provider)} · ${origin}</option>`;
    })
    .join("");
}

function selectModel(id) {
  const enabledModels = allModels.filter(isModelEnabled);
  const model = enabledModels.find((item) => item.id === id) || enabledModels[0] || allModels[0];
  if (!model) return;
  if (modelSelect) modelSelect.value = model.id;
  localStorage.setItem(STORAGE_SELECTED, model.id);
  if (modelConfigForm) populateModelForm(model);
  renderModelList();
}

function populateModelForm(model) {
  const keys = readApiKeys();
  setField("display_name", model.display_name || "");
  setField("provider", model.provider || "openai_compatible");
  setField("api_format", model.api_format || "openai_compatible");
  setField("base_url", model.base_url || "");
  setField("real_model_id", model.model_id || model.id || "");
  setField("api_key", keys[model.id] || "");
  setField("temperature", model.default_params?.temperature ?? "");
  setField("max_tokens", model.default_params?.max_tokens ?? 6000);
  setField("param_overrides", stringifyParams(model.param_overrides || model.extra_body || {}));
}

function collectPayload() {
  const data = new FormData(form);
  const runtime = getSelectedModelConfig();
  return {
    birth_date: data.get("birth_date"),
    birth_time: data.get("birth_time"),
    birth_time_accuracy: data.get("birth_time_accuracy"),
    birth_city: data.get("birth_city"),
    gender: data.get("gender") || "unspecified",
    calendar_type: data.get("calendar_type") || "solar",
    lunar_is_leap: data.get("lunar_is_leap") === "on",
    style: data.get("style"),
    mysticism_level: Number(data.get("mysticism_level")),
    model_id: runtime.id,
    model_config: runtime,
    api_key: getApiKeyForModel(runtime.id),
    focus_theories: ["MBTI", "天干地支", "星座", "五行"],
    psychology_answers: {
      energy_social: Number(data.get("energy_social")),
      planning: Number(data.get("planning")),
      emotion_focus: Number(data.get("emotion_focus")),
      novelty: Number(data.get("novelty")),
    },
  };
}

function getSelectedModelConfig() {
  const selectedId = modelSelect?.value || localStorage.getItem(STORAGE_SELECTED);
  return allModels.find((item) => item.id === selectedId) || allModels.find(isModelEnabled) || allModels[0];
}

function getApiKeyForModel(modelId) {
  if (modelConfigForm) {
    return $("#modelApiKey")?.value.trim() || "";
  }
  return readApiKeys()[modelId] || "";
}

function readModelForm(options = {}) {
  if (!modelConfigForm) throw new Error("当前页面没有模型配置表单");
  const { preserveLocalId = true, preserveSelectedId = false } = options;
  const selected = allModels.find((item) => item.id === modelSelect?.value);
  const formData = new FormData(modelConfigForm);
  const provider = String(formData.get("provider") || "openai_compatible");
  const modelId = String(formData.get("real_model_id") || "").trim();
  const displayName = String(formData.get("display_name") || modelId || "自定义模型").trim();
  const id = preserveSelectedId && selected
    ? selected.id
    : preserveLocalId && selected?.local
    ? selected.id
    : `${provider}-${slug(modelId || displayName)}`;
  const defaultParams = {
    max_tokens: clampMaxTokens(Number(formData.get("max_tokens") || 6000)),
  };
  const temperature = String(formData.get("temperature") || "").trim();
  if (temperature !== "") defaultParams.temperature = Number(temperature);

  return {
    id,
    display_name: displayName,
    provider,
    api_format: String(formData.get("api_format") || "openai_compatible"),
    base_url: normalizeBaseUrl(String(formData.get("base_url") || "").trim()),
    model_id: modelId,
    enabled: selected ? isModelEnabled(selected) : true,
    capabilities: {
      text: true,
      json_output: provider !== "mock",
      tool_calls: provider !== "mock",
      streaming: provider !== "mock",
      reasoning_mode: provider !== "mock",
    },
    pricing: selected?.pricing || { input_per_million: 0, output_per_million: 0 },
    default_params: defaultParams,
    param_overrides: parseParamOverrides(),
  };
}

function parseParamOverrides() {
  const raw = String(modelConfigForm?.elements.param_overrides?.value || "").trim();
  if (!raw) return {};
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (error) {
    throw new Error(`高级请求参数不是合法 JSON：${error.message}`);
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("高级请求参数必须是 JSON 对象");
  }
  return parsed;
}

modelSelect?.addEventListener("change", () => {
  selectModel(modelSelect.value);
});

$("#modelProvider")?.addEventListener("change", () => {
  applyProviderPreset(false);
});

applyProviderPresetBtn?.addEventListener("click", () => {
  applyProviderPreset(true);
});

function applyProviderPreset(includeName) {
  const provider = $("#modelProvider")?.value || "openai_compatible";
  const preset = providerDefaults[provider] || providerDefaults.openai_compatible;
  setField("api_format", preset.api_format);
  setField("base_url", preset.base_url);
  setField("real_model_id", preset.model_id);
  setField("temperature", preset.temperature);
  setField("max_tokens", preset.max_tokens);
  setField("param_overrides", stringifyParams(preset.param_overrides));
  if (includeName) setField("display_name", preset.display_name);
}

$("#modelBaseUrl")?.addEventListener("input", () => {
  const value = $("#modelBaseUrl").value.trim();
  if (value && !value.startsWith("https://") && !value.startsWith("http://")) {
    setStatus("接口 URL 需要以 http:// 或 https:// 开头");
  }
});

saveLocalModelBtn?.addEventListener("click", () => {
  saveCurrentModelConfig();
});

function saveCurrentModelConfig() {
  try {
    const config = { ...readModelForm({ preserveSelectedId: true }), local: true, enabled: true };
    const apiKey = $("#modelApiKey")?.value.trim() || "";
    persistModelConfig(config, apiKey);
    setStatus("配置/API 已保存");
  } catch (error) {
    setStatus("保存失败");
    setUsage(error.message);
  }
}

function persistModelConfig(config, apiKey = "") {
  const localModels = readLocalModels().filter((model) => model.id !== config.id);
  localModels.push({ ...config, local: true, enabled: true });
  localStorage.setItem(STORAGE_MODELS, JSON.stringify(localModels));

  if (apiKey) {
    const keys = readApiKeys();
    keys[config.id] = apiKey;
    localStorage.setItem(STORAGE_KEYS, JSON.stringify(keys));
  }

  refreshModelState();
  selectModel(config.id);
}

function autoSaveOnTestSuccess(config, apiKey) {
  persistModelConfig({ ...config, local: true, enabled: true }, apiKey);
  setStatus("连接可用，配置/API 已自动保存");
}

resetLocalModelsBtn?.addEventListener("click", () => {
  localStorage.removeItem(STORAGE_MODELS);
  localStorage.removeItem(STORAGE_KEYS);
  localStorage.removeItem(STORAGE_DISABLED);
  refreshModelState();
  selectModel("deepseek-v4-pro");
  setStatus("本地模型已清空");
});

testModelBtn?.addEventListener("click", async () => {
  await testModelConfig();
});

async function testModelConfig(modelId, button) {
  setBusy(button, true);
  setStatus("测试中");
  setUsage("正在测试模型连接");
  try {
    const config = modelId
      ? allModels.find((item) => item.id === modelId)
      : modelConfigForm
        ? readModelForm()
        : getSelectedModelConfig();
    if (!config) throw new Error("模型不存在");
    const apiKey = modelConfigForm && !modelId ? getApiKeyForModel(config.id) : readApiKeys()[config.id] || "";

    const res = await fetch("/api/models/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model_id: config.id,
        model_config: config,
        api_key: apiKey,
      }),
    });
    const data = await res.json();
    setStatus(data.ok ? "连接可用" : "连接失败");
    setUsage(data.message || "");
    if (data.ok && modelConfigForm && !modelId) {
      autoSaveOnTestSuccess(config, apiKey);
    }
    return data;
  } catch (error) {
    setStatus("连接失败");
    setUsage(error.message);
    return { ok: false, message: error.message };
  } finally {
    setBusy(button, false);
  }
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitButton = form.querySelector("button[type='submit']");
  submitButton.disabled = true;
  setUsage("生成中");
  readingOutput.innerHTML = `<div class="empty-state">正在计算依据并生成报告...</div>`;
  try {
    const payload = collectPayload();
    if (!payload.model_config) throw new Error("请先选择模型");
    const res = await fetch("/api/readings/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "生成失败");
    renderResult(data);
  } catch (error) {
    readingOutput.innerHTML = `<div class="truth-note">${escapeHtml(error.message)}</div>`;
  } finally {
    submitButton.disabled = false;
  }
});

function renderResult(data) {
  const reading = data.reading || {};
  const usage = data.usage || {};
  const profile = data.evidence_profile || {};
  setUsage(`${data.provider} / ${data.model} / $${usage.estimated_cost_usd ?? 0}`);
  readingOutput.innerHTML = `
    <section class="report-head">
      <div>
        <h2 class="report-title">${escapeHtml(reading.title || "命运测试报告")}</h2>
        <p>${escapeHtml(reading.summary || "系统已完成本地证据推导，等待模型解释这些证据。")}</p>
      </div>
      <div class="truth-note">${escapeHtml(reading.truthfulness_note || "结论必须来自可复核依据。")}</div>
    </section>
    ${renderPlainTakeaways(reading, profile)}
    ${renderChartOverview(reading, profile)}
    ${renderDerivedFacts(reading, profile)}
    ${(reading.dimensions || []).length ? `<section class="report-section">${(reading.dimensions || []).map((dimension, index) => renderDimension(dimension, index)).join("")}</section>` : ""}
    ${renderRelationshipProfile(reading, profile)}
    ${renderMatchmaking(reading, profile)}
    ${renderLifeTopics(reading, profile)}
    ${renderQuestions(reading)}
  `;
  renderEvidence(profile);
  renderElements(profile.elements || {});
}

const readingSymbols = ["✦", "◎", "◇", "◈", "✧", "▣", "△", "◆"];

function readingSymbol(index) {
  return readingSymbols[index % readingSymbols.length];
}

function renderPlainTakeaways(reading, profile) {
  const takeaways = normalizePlainTakeaways(reading.plain_takeaways, reading, profile);
  return `
    <section class="plain-takeaways">
      <h3>先看这几句话</h3>
      <p>${escapeHtml(takeaways.direct_answer)}</p>
      <div class="plain-card-grid">
        <article class="plain-card">
          <h4>重点</h4>
          <ul>${takeaways.key_points.slice(0, 3).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </article>
        <article class="plain-card">
          <h4>可以怎么做</h4>
          <ul>${takeaways.suggested_actions.slice(0, 3).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </article>
        <article class="plain-card">
          <h4>不要误读</h4>
          <ul>${takeaways.do_not_overread.slice(0, 3).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </article>
      </div>
    </section>
  `;
}

function normalizePlainTakeaways(takeaways, reading, profile) {
  if (takeaways && typeof takeaways === "object") {
    return {
      direct_answer: takeaways.direct_answer || reading.summary || "这份报告只说明倾向，不替你决定人生。",
      key_points: Array.isArray(takeaways.key_points) && takeaways.key_points.length
        ? takeaways.key_points
        : fallbackKeyPoints(reading, profile),
      suggested_actions: Array.isArray(takeaways.suggested_actions) && takeaways.suggested_actions.length
        ? takeaways.suggested_actions
        : fallbackActions(reading),
      do_not_overread: Array.isArray(takeaways.do_not_overread) && takeaways.do_not_overread.length
        ? takeaways.do_not_overread
        : fallbackBoundaries(),
    };
  }
  return {
    direct_answer: reading.summary || "这份报告只说明倾向，不替你决定人生。",
    key_points: fallbackKeyPoints(reading, profile),
    suggested_actions: fallbackActions(reading),
    do_not_overread: fallbackBoundaries(),
  };
}

function fallbackKeyPoints(reading, profile) {
  const topics = reading.life_topics || Object.values(profile.life_topics || {});
  const firstTopic = topics[0]?.insight || topics[0]?.signal;
  return [
    firstTopic || "先把命盘结果当作观察自己的线索。",
    "看重复出现的倾向，不要只看单个标签。",
    "真正重要的是现实中的选择和反馈。",
  ];
}

function fallbackActions(reading) {
  const firstTopic = (reading.life_topics || []).find((item) => (item.actionable_suggestions || []).length);
  return firstTopic?.actionable_suggestions || [
    "挑一条最像自己的结论，记录一周看看准不准。",
    "把建议改成一个今天能做的小动作。",
    "遇到重大决定时，优先参考现实信息。",
  ];
}

function fallbackBoundaries() {
  return [
    "这不是绝对预测。",
    "不能替代医疗、投资、法律建议。",
    "出生时间不准时，部分结论会变弱。",
  ];
}

function renderBasisList(basis = [], confidence) {
  const items = [
    `<span class="basis-item">置信度 ${confidencePercent(confidence)}%</span>`,
    ...basis.slice(0, 3).map((item) => `<span class="basis-item">依据 ${escapeHtml(item)}</span>`),
  ];
  return `<div class="basis-list">${items.join("")}</div>`;
}

function renderSuggestionList(suggestions = []) {
  if (!suggestions.length) return "";
  return `
    <ul class="suggestion-list">
      ${suggestions.slice(0, 3).map((tip) => `<li>${escapeHtml(tip)}</li>`).join("")}
    </ul>
  `;
}

function renderDimension(item, index = 0) {
  return `
    <article class="dimension">
      <div class="dimension-heading">
        <span class="dimension-symbol">${readingSymbol(index)}</span>
        <h3>${escapeHtml(item.title || item.id || "维度")}</h3>
      </div>
      <div class="claim">${escapeHtml(item.claim || "")}</div>
      ${renderBasisList(item.basis || [], item.confidence)}
      ${renderSuggestionList(item.suggestions || [])}
    </article>
  `;
}

function renderChartOverview(reading, profile) {
  const overview = reading.chart_overview || chartOverviewFromProfile(profile);
  const pillars = Array.isArray(overview.pillars) ? overview.pillars : [];
  const pillarText = pillars.length ? pillars.join(" / ") : "未计算";
  return `
    <section class="chart-overview">
      <article class="chart-summary">
        <span>四柱</span>
        <strong>${escapeHtml(pillarText)}</strong>
      </article>
      <article class="chart-summary">
        <span>日主</span>
        <strong>${escapeHtml(overview.day_master || "未计算")}</strong>
      </article>
      <article class="chart-summary">
        <span>生肖</span>
        <strong>${escapeHtml(overview.zodiac || "未计算")}</strong>
      </article>
      <article class="chart-summary">
        <span>节气</span>
        <strong>${escapeHtml(overview.solar_term || "未计算")}</strong>
      </article>
      <p class="chart-headline">${escapeHtml(overview.headline || "命盘摘要用于定位证据，不作为绝对预测。")}</p>
    </section>
  `;
}

function chartOverviewFromProfile(profile) {
  const bazi = profile.bazi || {};
  const pillars = bazi.pillars || {};
  const dayMaster = bazi.day_master || {};
  const zodiac = bazi.zodiac || {};
  const solarTerm = bazi.solar_term || {};
  return {
    pillars: ["year", "month", "day", "hour"]
      .map((key) => pillars[key]?.pillar)
      .filter(Boolean),
    day_master: dayMaster.stem ? `${dayMaster.stem}日主 / ${dayMaster.element_label || ""}` : "",
    zodiac: zodiac.animal || "",
    solar_term: solarTerm.current?.name || "",
    headline: "先看命盘结构，再看生活议题，所有判断都回到证据。",
  };
}

function renderDerivedFacts(reading, profile) {
  const facts = normalizeDerivedFacts(reading.derived_facts, profile);
  if (!facts.length) return "";
  return `
    <section class="report-section">
      <div class="mini-section-title">推导事实</div>
      <div class="derived-fact-grid">
        ${facts.map((fact, index) => renderDerivedFact(fact, index)).join("")}
      </div>
    </section>
  `;
}

function normalizeDerivedFacts(derivedFacts, profile) {
  if (Array.isArray(derivedFacts) && derivedFacts.length) return derivedFacts;
  const bazi = profile.bazi || {};
  const elements = profile.elements || {};
  const tenGods = profile.ten_gods || {};
  const strongest = Object.values(elements)
    .sort((a, b) => Number(b.score || 0) - Number(a.score || 0))
    .slice(0, 3);
  const hidden = Object.entries(bazi.hidden_stems || {})
    .map(([branch, stems]) => `${branch}: ${(stems || []).join("/")}`)
    .join("；");
  const visible = (tenGods.visible || [])
    .slice(0, 4)
    .map((item) => `${item.stem}=${item.ten_god}`)
    .join("、");
  return [
    {
      title: "五行分布",
      value: strongest.map((item) => `${item.label} ${item.score}`).join("、"),
      basis: ["四柱天干", "地支", "藏干加权"],
      confidence: 0.72,
    },
    { title: "藏干", value: hidden, basis: ["地支藏干表"], confidence: 0.78 },
    { title: "可见十神", value: visible, basis: ["以日干为日主"], confidence: 0.78 },
  ].filter((item) => item.value);
}

function renderDerivedFact(item, index = 0) {
  return `
    <article class="derived-fact">
      <div class="dimension-heading">
        <span class="dimension-symbol">${readingSymbol(index + 2)}</span>
        <h3>${escapeHtml(item.title || "推导")}</h3>
      </div>
      <strong>${escapeHtml(formatValue(item.value))}</strong>
      ${renderBasisList(item.basis || [], item.confidence)}
    </article>
  `;
}

function renderLifeTopics(reading, profile) {
  const topics = normalizeLifeTopics(reading.life_topics, profile.life_topics);
  if (!topics.length) return "";
  return `
    <section class="report-section">
      <div class="mini-section-title">生活议题</div>
      <div class="life-topic-grid">
        ${topics.map((topic, index) => renderLifeTopic(topic, index)).join("")}
      </div>
    </section>
  `;
}

function normalizeLifeTopics(readingTopics, profileTopics = {}) {
  if (Array.isArray(readingTopics) && readingTopics.length) return readingTopics;
  const order = [
    "personality",
    "relationship",
    "career",
    "wealth",
    "health_energy",
    "study_growth",
    "social_family",
    "timing",
  ];
  return order
    .map((id) => {
      const item = profileTopics[id];
      if (!item) return null;
      return {
        id,
        title: item.title,
        insight: item.signal,
        basis: item.basis,
        confidence: item.confidence,
        actionable_suggestions: suggestionsForTopic(id),
        limits: item.limits,
      };
    })
    .filter(Boolean);
}

function renderLifeTopic(item, index = 0) {
  const suggestions = item.actionable_suggestions || item.suggestions || [];
  return `
    <article class="life-topic-card">
      <div class="life-topic-top">
        <div class="topic-title">
          <span class="topic-symbol">${readingSymbol(index + 4)}</span>
          <h3>${escapeHtml(item.title || topicLabel(item.id))}</h3>
        </div>
        <span>${confidencePercent(item.confidence)}%</span>
      </div>
      <p>${escapeHtml(item.insight || item.claim || "")}</p>
      ${renderBasisList(item.basis || [], item.confidence)}
      ${renderSuggestionList(suggestions)}
    </article>
  `;
}

function renderRelationshipProfile(reading, profile) {
  const item = reading.relationship_profile || profile.relationship_profile;
  if (!item) return "";
  const pairing = item.day_branch_pairing || {};
  return `
    <section class="relationship-panel">
      <div class="mini-section-title">${escapeHtml(item.title || "姻缘分析")}</div>
      <div class="relationship-grid">
        <article>
          <span>伴侣星口径</span>
          <strong>${escapeHtml(item.partner_star || "未指定")}</strong>
        </article>
        <article>
          <span>日支关系宫</span>
          <strong>${escapeHtml(pairing.self_day_branch || "未计算")} → ${escapeHtml(pairing.six_harmony_branch || "无六合参考")}</strong>
        </article>
        <article>
          <span>需要补足</span>
          <strong>${escapeHtml((item.needs_to_balance || []).join("、") || "按现实互动校准")}</strong>
        </article>
      </div>
      <p>${escapeHtml(item.relationship_tone || "")}</p>
      ${(item.risk_notes || []).length ? `<ul>${item.risk_notes.slice(0, 2).map((note) => `<li>${escapeHtml(note)}</li>`).join("")}</ul>` : ""}
    </section>
  `;
}

function renderMatchmaking(reading, profile) {
  const item = reading.matchmaking || profile.matchmaking;
  if (!item) return "";
  const elements = item.recommended_elements || [];
  const branches = item.favorable_branches || [];
  return `
    <section class="matchmaking-panel">
      <div class="mini-section-title">${escapeHtml(item.title || "更匹配的异性八字画像")}</div>
      <div class="matchmaking-grid">
        ${elements.map((element) => `
          <article class="match-card">
            <span>${escapeHtml(element.label || element.element || "五行")}</span>
            <strong>${escapeHtml((element.candidate_day_stems || []).join(" / ") || "日主不限")}</strong>
            <p>${escapeHtml(element.reason || "")}</p>
          </article>
        `).join("")}
        <article class="match-card">
          <span>地支加分</span>
          <strong>${escapeHtml(branches.map((branch) => branch.branch).join(" / ") || "无固定")}</strong>
          <p>${escapeHtml(branches.map((branch) => branch.reason).join("；") || "需要结合完整命盘和现实互动。")}</p>
        </article>
      </div>
      <div class="matchmaking-note">
        <strong>${escapeHtml(item.partner_ten_god_focus || "")}</strong>
        ${(item.screening_questions || []).length ? `<ol>${item.screening_questions.slice(0, 3).map((question) => `<li>${escapeHtml(question)}</li>`).join("")}</ol>` : ""}
      </div>
    </section>
  `;
}

function renderQuestions(reading) {
  const questions = reading.questions_to_reflect || [];
  if (!questions.length) return "";
  return `
    <section class="reflection-panel">
      <div class="mini-section-title">反思问题</div>
      <ol>${questions.slice(0, 5).map((question) => `<li>${escapeHtml(question)}</li>`).join("")}</ol>
    </section>
  `;
}

function renderEvidence(profile) {
  if (!evidenceList || !limitsList) return;
  evidenceList.innerHTML = (profile.evidence || [])
    .map(
      (item) => `
      <div class="evidence-item">
        <strong>${escapeHtml(item.label)}</strong>：${escapeHtml(formatValue(item.value))}
        <br><span>${escapeHtml(item.basis)} · 置信度 ${Math.round((item.confidence || 0) * 100)}%</span>
      </div>
    `
    )
    .join("");
  limitsList.innerHTML = (profile.limits || [])
    .map((item) => `<div class="limit-item">${escapeHtml(item)}</div>`)
    .join("");
}

function renderElements(elements) {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const entries = Object.entries(elements);
  const colors = ["#63d7bc", "#ff8b7e", "#e2bd65", "#8db1ff", "#b4a8d7"];
  ctx.font = "14px Microsoft YaHei";
  entries.forEach(([key, value], index) => {
    const y = 28 + index * 34;
    const width = Math.max(8, (Number(value.score || 0) / 100) * 260);
    ctx.fillStyle = colors[index % colors.length];
    ctx.fillRect(96, y - 16, width, 18);
    ctx.fillStyle = "#eef4ff";
    ctx.fillText(`${value.label || key} ${value.score || 0}`, 18, y);
  });
  ctx.strokeStyle = "rgba(226, 189, 101, 0.32)";
  ctx.strokeRect(96, 12, 260, 174);
}

function topicLabel(id) {
  return {
    personality: "性格底色",
    relationship: "婚恋关系",
    career: "事业职业",
    wealth: "财运资源",
    health_energy: "身心节律",
    study_growth: "学习成长",
    social_family: "人际家庭",
    timing: "阶段建议",
  }[id] || "生活议题";
}

function suggestionsForTopic(id) {
  return {
    personality: ["用一周记录验证报告中的行为倾向。"],
    relationship: ["把建议改写成可沟通的边界和需求。"],
    career: ["把职业判断拆成技能、环境、压力源三个观察点。"],
    wealth: ["只当作资源管理提醒，不作投资判断。"],
    health_energy: ["观察作息与压力节律，不作医疗判断。"],
    study_growth: ["选择一个可输出的小项目验证学习方式。"],
    social_family: ["区分支持关系和消耗关系。"],
    timing: ["先看阶段主题，再结合现实计划调整。"],
  }[id] || ["保留观察，不做绝对结论。"];
}

function confidencePercent(value) {
  return Math.round((Number(value) || 0) * 100);
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "未计算";
  if (Array.isArray(value)) return value.map(formatValue).join("、");
  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, item]) => `${key}: ${formatValue(item)}`)
      .join(" / ");
  }
  return String(value);
}

function renderModelList() {
  if (!modelList) return;
  const selectedId = modelSelect?.value;
  modelList.innerHTML = allModels.map((model) => renderModelCard(model, selectedId)).join("");
  modelList.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => {
      handleModelAction(button.dataset.action, button.dataset.id, button);
    });
  });
}

function renderModelCard(model, selectedId) {
  const enabled = isModelEnabled(model);
  const origin = model.local ? "本地" : "内置";
  const activeClass = model.id === selectedId ? " active" : "";
  const enabledLabel = enabled ? "启用中" : "已禁用";
  return `
    <article class="model-card${activeClass}">
      <div class="model-card-main">
        <div>
          <strong>${escapeHtml(model.display_name || model.id)}</strong>
          <div class="model-meta">${escapeHtml(model.provider)} · ${escapeHtml(model.api_format || "")} · ${escapeHtml(model.model_id || model.id)}</div>
          <div class="model-url">${escapeHtml(model.base_url || "local")}</div>
        </div>
        <div class="model-tags">
          <span class="model-chip">${origin}</span>
          <span class="model-chip ${enabled ? "good" : "muted-chip"}">${enabledLabel}</span>
        </div>
      </div>
      <div class="model-card-actions">
        <button type="button" class="secondary compact" data-action="select" data-id="${escapeAttr(model.id)}">选择</button>
        <button type="button" class="secondary compact" data-action="test" data-id="${escapeAttr(model.id)}">测试连接</button>
        <button type="button" class="secondary compact" data-action="edit" data-id="${escapeAttr(model.id)}">编辑</button>
        <button type="button" class="secondary compact" data-action="clone" data-id="${escapeAttr(model.id)}">克隆</button>
        <button type="button" class="secondary compact" data-action="toggle" data-id="${escapeAttr(model.id)}">${enabled ? "禁用" : "启用"}</button>
        ${model.local ? `<button type="button" class="secondary compact danger" data-action="delete" data-id="${escapeAttr(model.id)}">删除</button>` : ""}
      </div>
    </article>
  `;
}

function handleModelAction(action, id, button) {
  if (!id) return;
  if (action === "select") selectModel(id);
  if (action === "test") testModelConfig(id, button);
  if (action === "edit") selectModel(id);
  if (action === "clone") cloneModel(id);
  if (action === "toggle") toggleModelEnabled(id);
  if (action === "delete") deleteLocalModel(id);
}

function cloneModel(id) {
  const model = allModels.find((item) => item.id === id);
  if (!model) return;
  const cloneId = `${model.provider}-${slug(model.model_id || model.display_name)}-${Date.now().toString(36)}`;
  const clone = {
    ...JSON.parse(JSON.stringify(model)),
    id: cloneId,
    display_name: `${model.display_name || model.id} 副本`,
    local: true,
    enabled: true,
  };
  const localModels = readLocalModels();
  localModels.push(clone);
  localStorage.setItem(STORAGE_MODELS, JSON.stringify(localModels));

  const keys = readApiKeys();
  if (keys[id]) {
    keys[cloneId] = keys[id];
    localStorage.setItem(STORAGE_KEYS, JSON.stringify(keys));
  }

  refreshModelState();
  selectModel(cloneId);
  setStatus("模型副本已创建");
}

function toggleModelEnabled(id) {
  const model = allModels.find((item) => item.id === id);
  if (!model) return;
  if (model.local) {
    const localModels = readLocalModels().map((item) =>
      item.id === id ? { ...item, enabled: !isModelEnabled(item) } : item
    );
    localStorage.setItem(STORAGE_MODELS, JSON.stringify(localModels));
  } else {
    const disabled = readDisabledModels();
    if (disabled.has(id)) disabled.delete(id);
    else disabled.add(id);
    writeDisabledModels(disabled);
  }
  refreshModelState();
  if (!isModelEnabled(allModels.find((item) => item.id === modelSelect?.value))) {
    selectModel(allModels.find(isModelEnabled)?.id);
  } else {
    renderModelList();
  }
}

function deleteLocalModel(id) {
  const localModels = readLocalModels().filter((model) => model.id !== id);
  localStorage.setItem(STORAGE_MODELS, JSON.stringify(localModels));
  const keys = readApiKeys();
  delete keys[id];
  localStorage.setItem(STORAGE_KEYS, JSON.stringify(keys));
  refreshModelState();
  selectModel(allModels.find(isModelEnabled)?.id || preferredModelId());
  setStatus("本地模型已删除");
}

function isModelEnabled(model) {
  if (!model) return false;
  if (model.local) return model.enabled !== false;
  return !readDisabledModels().has(model.id);
}

function readLocalModels() {
  try {
    const models = JSON.parse(localStorage.getItem(STORAGE_MODELS) || "[]");
    return Array.isArray(models) ? models.map((model) => ({ ...model, local: true })) : [];
  } catch {
    return [];
  }
}

function readApiKeys() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEYS) || "{}");
  } catch {
    return {};
  }
}

function readDisabledModels() {
  try {
    const ids = JSON.parse(localStorage.getItem(STORAGE_DISABLED) || "[]");
    return new Set(Array.isArray(ids) ? ids : []);
  } catch {
    return new Set();
  }
}

function writeDisabledModels(disabled) {
  localStorage.setItem(STORAGE_DISABLED, JSON.stringify([...disabled]));
}

function setupReadingDraftPersistence() {
  if (!form) return;
  restoreReadingDraft();
  updateSliderGuides();
  form.addEventListener("input", () => {
    saveReadingDraft();
    updateSliderGuides();
  });
  form.addEventListener("change", () => {
    saveReadingDraft();
    updateSliderGuides();
  });
}

function saveReadingDraft() {
  if (!form) return;
  const values = {};
  form.querySelectorAll("input[name], select[name]").forEach((field) => {
    values[field.name] = field.type === "checkbox" ? field.checked : field.value;
  });
  localStorage.setItem(STORAGE_READING_DRAFT, JSON.stringify(values));
}

function restoreReadingDraft() {
  if (!form) return;
  let values = {};
  try {
    values = JSON.parse(localStorage.getItem(STORAGE_READING_DRAFT) || "{}");
  } catch {
    values = {};
  }
  Object.entries(values).forEach(([name, value]) => {
    const field = form.elements[name];
    if (!field) return;
    if (field.type === "checkbox") field.checked = Boolean(value);
    else field.value = value;
  });
}

function updateSliderGuides() {
  document.querySelectorAll("[data-range-output]").forEach((output) => {
    const field = form?.elements[output.dataset.rangeOutput];
    if (!field) return;
    output.textContent = sliderText(output.dataset.rangeOutput, Number(field.value));
  });
}

function sliderText(name, value) {
  if (name === "mysticism_level") {
    if (value <= 25) return `${value} 理性解释`;
    if (value <= 65) return `${value} 平衡表达`;
    return `${value} 神秘叙事`;
  }
  const labels = {
    energy_social: ["独处恢复", "均衡", "外向充电"],
    planning: ["即兴", "适中", "强计划"],
    emotion_focus: ["低情绪敏感", "适中", "高共情"],
    novelty: ["稳定偏好", "适中", "探索偏好"],
  }[name] || ["低", "中", "高"];
  if (value <= 2) return `${value} ${labels[0]}`;
  if (value >= 4) return `${value} ${labels[2]}`;
  return `${value} ${labels[1]}`;
}

function setField(name, value) {
  if (!modelConfigForm) return;
  const field = modelConfigForm.elements[name];
  if (field) field.value = value ?? "";
}

function stringifyParams(value) {
  if (!value || Object.keys(value).length === 0) return "";
  return JSON.stringify(value, null, 2);
}

function clampMaxTokens(value) {
  if (!Number.isFinite(value)) return 6000;
  return Math.min(16000, Math.max(6000, value));
}

function setBusy(button, busy) {
  if (!button) return;
  button.disabled = busy;
}

function setStatus(text) {
  if (modelStatus) modelStatus.textContent = text;
  if (text && !["测试中", "生成中", "未测试连接"].includes(text)) {
    showToast(text);
  }
}

function setUsage(text) {
  if (usageText) usageText.textContent = text;
}

function showToast(message, tone = "default") {
  if (!toastStack || !message) return;
  const toast = document.createElement("div");
  toast.className = `toast ${tone}`;
  toast.innerHTML = `
    <span class="toast-symbol">✦</span>
    <span>${escapeHtml(message)}</span>
  `;
  toastStack.appendChild(toast);
  window.setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(-8px)";
  }, 2600);
  window.setTimeout(() => toast.remove(), 3100);
}

function installClickSymbols() {
  const symbols = ["✦", "✧", "✶", "⋆", "✷"];
  document.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    const disabledTarget = event.target.closest("button:disabled, input:disabled, select:disabled, textarea:disabled");
    if (disabledTarget) return;
    const burst = document.createElement("span");
    burst.className = "click-symbol";
    burst.style.left = `${event.clientX}px`;
    burst.style.top = `${event.clientY}px`;
    const starCount = 7;
    for (let index = 0; index < starCount; index += 1) {
      const star = document.createElement("span");
      star.className = "click-star";
      star.textContent = symbols[index % symbols.length];
      const angle = (Math.PI * 2 * index) / starCount - Math.PI / 2;
      const distance = 22 + Math.random() * 26;
      star.style.setProperty("--dx", `${Math.cos(angle) * distance}px`);
      star.style.setProperty("--dy", `${Math.sin(angle) * distance}px`);
      star.style.setProperty("--rot", `${Math.round(-45 + Math.random() * 90)}deg`);
      star.style.setProperty("--star-size", `${11 + Math.round(Math.random() * 7)}px`);
      burst.appendChild(star);
    }
    document.body.appendChild(burst);
    window.setTimeout(() => burst.remove(), 1700);
  });
}

function slug(value) {
  return String(value || "model")
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 50);
}

function normalizeBaseUrl(value) {
  return value.replace(/\/+$/g, "");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

installClickSymbols();
setupReadingDraftPersistence();
loadModels();
