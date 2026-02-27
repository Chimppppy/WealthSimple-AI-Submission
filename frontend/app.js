const EVALUATE_URL = '/api/evaluate';
const EXPLAIN_URL  = '/api/explain';
const STORAGE_KEY  = 'pulse_profile';

// ── DOM refs ──────────────────────────────────────────
const onboardingEl  = document.getElementById('onboarding');
const dashboardEl   = document.getElementById('dashboard');
const loadingEl     = document.getElementById('loading');
const resultsEl     = document.getElementById('results');
const briefEl       = document.getElementById('brief-section');
const controlsEl    = document.getElementById('controls-section');
const goalRingCard  = document.getElementById('goal-ring-card');
const allocDonutCard= document.getElementById('alloc-donut-card');
const savingsCard   = document.getElementById('savings-card');
const liquidityCard = document.getElementById('liquidity-card');
const scenarioGrid  = document.getElementById('scenario-grid');
const actionChart   = document.getElementById('action-chart');
const detailContent = document.getElementById('detail-content');
const detailBtn     = document.getElementById('detail-btn');
const guardrailsEl  = document.getElementById('guardrails-section');
const toastEl       = document.getElementById('toast');
const marketEl      = document.getElementById('market-section');
const holdingsCard  = document.getElementById('holdings-card');
const chartSection  = document.getElementById('chart-section');
const chartCard     = document.getElementById('chart-card');
const summaryEl     = document.getElementById('profile-summary');
const editBtn       = document.getElementById('edit-btn');
const rerunBtn      = document.getElementById('rerun-btn');

let lastEval = null;
let currentProfile = null;

// ── localStorage ──────────────────────────────────────
function saveProfile(profile) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
}
function loadProfile() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
    const legacy = localStorage.getItem('wfos_profile');
    return legacy ? JSON.parse(legacy) : null;
  } catch { return null; }
}
function clearProfile() {
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem('wfos_profile');
}

// ══════════════════════════════════════════════════════
//  ONBOARDING WIZARD
// ══════════════════════════════════════════════════════
const TOTAL_STEPS = 6;
let wizStep = 0;
let wizData = {};

const wizSteps = document.querySelectorAll('.wiz-step');
const wizNext  = document.getElementById('wiz-next');
const wizBack  = document.getElementById('wiz-back');
const wizFill  = document.getElementById('wiz-progress-fill');

const GOAL_PURPOSE_LABELS = {
  home: 'Home', retirement: 'Retirement', education: 'Education',
  travel: 'Travel', emergency: 'Emergency Fund', general_wealth: 'General Wealth'
};
const LIFE_STAGE_LABELS = {
  student: 'Student', early_career: 'Early Career', mid_career: 'Mid Career',
  pre_retirement: 'Pre-Retirement', retired: 'Retired'
};
const CONCERN_LABELS = {
  none: 'None', market_volatility: 'Market volatility',
  not_saving_enough: 'Not saving enough', debt: 'Debt',
  inflation: 'Inflation', retirement_readiness: 'Retirement readiness'
};

function initCardSelectors() {
  document.querySelectorAll('.card-selector').forEach(container => {
    container.querySelectorAll('.sel-card').forEach(card => {
      card.addEventListener('click', () => {
        container.querySelectorAll('.sel-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
      });
    });
  });
}

function showWizStep(idx) {
  wizStep = idx;
  wizSteps.forEach((s, i) => s.classList.toggle('hidden', i !== idx));
  wizBack.style.visibility = idx === 0 ? 'hidden' : 'visible';
  wizNext.textContent = idx === TOTAL_STEPS - 1 ? 'Start Analysis' : 'Continue';
  wizFill.style.width = `${((idx + 1) / TOTAL_STEPS) * 100}%`;
  if (idx === TOTAL_STEPS - 1) buildReview();
}

function collectWizData() {
  const val = (id) => document.getElementById(id)?.value?.trim() || '';
  const num = (id) => parseFloat(document.getElementById(id)?.value) || 0;

  wizData.first_name = val('w_first_name');
  wizData.age = parseInt(val('w_age')) || null;

  const lsCard = document.querySelector('#life-stage-cards .sel-card.selected');
  wizData.life_stage = lsCard ? lsCard.dataset.value : null;

  wizData.annual_income = num('w_annual_income');
  wizData.monthly_expenses = num('w_monthly_expenses');
  wizData.cash_balance = num('w_cash_balance');
  wizData.portfolio_value = num('w_portfolio_value');
  wizData.portfolio_equity_pct = num('w_portfolio_equity_pct') / 100;
  wizData.portfolio_bond_pct = num('w_portfolio_bond_pct') / 100;
  wizData.monthly_contribution = num('w_monthly_contribution');
  wizData.risk_profile = val('w_risk_profile');

  const gpCard = document.querySelector('#goal-purpose-cards .sel-card.selected');
  wizData.goal_purpose = gpCard ? gpCard.dataset.value : null;
  wizData.goal_target_amount = num('w_goal_target_amount');
  wizData.goal_years = Math.round(num('w_goal_years'));
  wizData.financial_concern = val('w_financial_concern') || 'none';
  wizData.personal_note = val('w_personal_note') || null;
}

function validateStep(idx) {
  collectWizData();
  switch (idx) {
    case 0:
      if (!wizData.first_name) { toast('Please enter your first name.'); return false; }
      return true;
    case 1:
      if (!wizData.life_stage) { toast('Please select a life stage.'); return false; }
      return true;
    case 2:
      if (wizData.annual_income <= 0) { toast('Please enter a valid income.'); return false; }
      if (wizData.monthly_expenses <= 0) { toast('Please enter valid expenses.'); return false; }
      return true;
    case 3:
      return true;
    case 4:
      if (wizData.goal_target_amount <= 0) { toast('Please enter a goal amount.'); return false; }
      if (wizData.goal_years <= 0) { toast('Please enter a goal timeline.'); return false; }
      return true;
    default:
      return true;
  }
}

function buildReview() {
  collectWizData();
  const d = wizData;
  const grid = document.getElementById('review-grid');
  const row = (label, value) => `<div class="review-item"><div class="review-label">${label}</div><div class="review-value">${value}</div></div>`;

  grid.innerHTML =
    row('Name', d.first_name || '\u2014') +
    row('Age', d.age || '\u2014') +
    row('Life Stage', LIFE_STAGE_LABELS[d.life_stage] || '\u2014') +
    row('Annual Income', '$' + fmt(d.annual_income)) +
    row('Monthly Expenses', '$' + fmt(d.monthly_expenses)) +
    row('Cash Balance', '$' + fmt(d.cash_balance)) +
    row('Portfolio Value', '$' + fmt(d.portfolio_value)) +
    row('Equity / Bond', pct(d.portfolio_equity_pct) + ' / ' + pct(d.portfolio_bond_pct)) +
    row('Monthly Contribution', '$' + fmt(d.monthly_contribution)) +
    row('Risk Tolerance', d.risk_profile) +
    row('Goal', (GOAL_PURPOSE_LABELS[d.goal_purpose] || '\u2014') + ' \u2014 $' + fmt(d.goal_target_amount) + ' in ' + d.goal_years + 'yr') +
    row('Top Concern', CONCERN_LABELS[d.financial_concern] || '\u2014') +
    (d.personal_note ? row('Note', d.personal_note) : '');
}

function populateWizFromProfile(p) {
  const set = (id, v) => { const el = document.getElementById(id); if (el && v != null) el.value = v; };
  set('w_first_name', p.first_name);
  set('w_age', p.age);
  set('w_annual_income', p.annual_income);
  set('w_monthly_expenses', p.monthly_expenses);
  set('w_cash_balance', p.cash_balance);
  set('w_portfolio_value', p.portfolio_value);
  set('w_portfolio_equity_pct', p.portfolio_equity_pct != null ? Math.round(p.portfolio_equity_pct * 100) : 60);
  set('w_portfolio_bond_pct', p.portfolio_bond_pct != null ? Math.round(p.portfolio_bond_pct * 100) : 30);
  set('w_monthly_contribution', p.monthly_contribution);
  set('w_risk_profile', p.risk_profile);
  set('w_goal_target_amount', p.goal_target_amount);
  set('w_goal_years', p.goal_years);
  set('w_financial_concern', p.financial_concern || 'none');
  set('w_personal_note', p.personal_note);

  if (p.life_stage) {
    document.querySelectorAll('#life-stage-cards .sel-card').forEach(c => {
      c.classList.toggle('selected', c.dataset.value === p.life_stage);
    });
  }
  if (p.goal_purpose) {
    document.querySelectorAll('#goal-purpose-cards .sel-card').forEach(c => {
      c.classList.toggle('selected', c.dataset.value === p.goal_purpose);
    });
  }
}

function showOnboarding(prefill) {
  dashboardEl.classList.add('hidden');
  onboardingEl.classList.remove('hidden');
  if (prefill) populateWizFromProfile(prefill);
  showWizStep(0);
}

function finishOnboarding() {
  collectWizData();
  currentProfile = { ...wizData };
  saveProfile(currentProfile);
  onboardingEl.classList.add('hidden');
  showDashboard();
  run();
}

wizNext.addEventListener('click', () => {
  if (!validateStep(wizStep)) return;
  if (wizStep === TOTAL_STEPS - 1) {
    finishOnboarding();
  } else {
    showWizStep(wizStep + 1);
  }
});

wizBack.addEventListener('click', () => {
  if (wizStep > 0) showWizStep(wizStep - 1);
});

// ══════════════════════════════════════════════════════
//  DASHBOARD
// ══════════════════════════════════════════════════════
function showDashboard() {
  onboardingEl.classList.add('hidden');
  dashboardEl.classList.remove('hidden');
  renderProfileSummary();
}

function renderProfileSummary() {
  if (!currentProfile) return;
  const p = currentProfile;
  const name = p.first_name || '';
  const ageStr = p.age ? `, ${p.age}` : '';
  const goalLabel = GOAL_PURPOSE_LABELS[p.goal_purpose] || '';
  const goalStr = goalLabel
    ? `$${fmtK(p.goal_target_amount)} ${goalLabel.toLowerCase()} goal in ${p.goal_years}yr`
    : `$${fmtK(p.goal_target_amount)} goal in ${p.goal_years}yr`;

  summaryEl.textContent = `${name}${ageStr} \u00b7 $${fmtK(p.annual_income)} income \u00b7 ${goalStr} \u00b7 ${p.risk_profile} risk`;
  rerunBtn.style.display = lastEval ? 'inline' : 'none';
}

editBtn.addEventListener('click', () => {
  resultsEl.classList.add('hidden');
  showOnboarding(currentProfile);
});

rerunBtn.addEventListener('click', async () => { await run(); });

// Analysis detail toggle
detailBtn.addEventListener('click', () => {
  const isCollapsed = detailContent.classList.contains('collapsed');
  detailContent.classList.toggle('collapsed', !isCollapsed);
  detailContent.classList.toggle('expanded', isCollapsed);
  detailBtn.textContent = isCollapsed ? 'Hide analysis' : 'Show analysis';
});

// ══════════════════════════════════════════════════════
//  MAIN EVALUATION FLOW
// ══════════════════════════════════════════════════════
function buildPayload() {
  if (!currentProfile) return {};
  const p = currentProfile;
  return {
    annual_income: p.annual_income,
    monthly_expenses: p.monthly_expenses,
    cash_balance: p.cash_balance,
    portfolio_value: p.portfolio_value,
    portfolio_equity_pct: p.portfolio_equity_pct,
    portfolio_bond_pct: p.portfolio_bond_pct,
    monthly_contribution: p.monthly_contribution,
    goal_target_amount: p.goal_target_amount,
    goal_years: p.goal_years,
    risk_profile: p.risk_profile,
    first_name: p.first_name,
    age: p.age,
    life_stage: p.life_stage,
    goal_purpose: p.goal_purpose,
    financial_concern: p.financial_concern,
    personal_note: p.personal_note,
  };
}

async function run() {
  const payload = buildPayload();
  resultsEl.classList.add('hidden');
  showLoading();

  try {
    const evalPromise = callAPI(EVALUATE_URL, payload);

    await sleep(300);  setStep(0, 'done');  setStep(1, 'active');
    await sleep(300);  setStep(1, 'done');  setStep(2, 'active');
    await sleep(250);  setStep(2, 'done');  setStep(3, 'active');

    const evalData = await evalPromise;
    lastEval = { ...evalData, risk_profile: payload.risk_profile };

    setStep(3, 'done');
    setStep(4, 'active');

    let aiData = null;
    try {
      aiData = await callAPI(EXPLAIN_URL, {
        risk_profile: payload.risk_profile,
        first_name: payload.first_name,
        age: payload.age,
        life_stage: payload.life_stage,
        goal_purpose: payload.goal_purpose,
        financial_concern: payload.financial_concern,
        personal_note: payload.personal_note,
        financial_snapshot: evalData.financial_snapshot,
        ranked_actions: evalData.ranked_actions,
        top_recommendation: evalData.top_recommendation,
      });
      setStep(4, 'done');
    } catch {
      setStep(4, 'skip');
    }

    await sleep(400);
    hideLoading();
    renderAll(evalData, aiData);
    rerunBtn.style.display = 'inline';
  } catch (err) {
    hideLoading();
    toast('Evaluation failed: ' + err.message);
  }
}

async function callAPI(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const e = await res.json().catch(() => ({}));
    throw new Error(e.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

// ── Loading ────────────────────────────────────────────
function showLoading() {
  loadingEl.classList.remove('hidden');
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active', 'done', 'skip'));
  setStep(0, 'active');
}
function hideLoading() { loadingEl.classList.add('hidden'); }
function setStep(i, state) {
  const steps = document.querySelectorAll('.step');
  if (!steps[i]) return;
  steps[i].classList.remove('active', 'done', 'skip');
  steps[i].classList.add(state);
}

// ══════════════════════════════════════════════════════
//  RENDER ALL
// ══════════════════════════════════════════════════════
function renderAll(evalData, aiData) {
  const brief = aiData ? aiData.explanation : buildFallback(evalData);
  const isAI  = !!aiData;
  const model = aiData ? aiData.model_used : null;
  const guardrails = aiData ? aiData.guardrails : [];

  renderBrief(brief, isAI, evalData.top_recommendation, model);
  renderControls(evalData.top_recommendation.action);
  renderGoalRing(evalData.financial_snapshot.estimated_goal_probability);
  renderAllocationDonut(currentProfile);
  renderSavingsMetric(evalData.financial_snapshot);
  renderLiquidityMetric(evalData.financial_snapshot);
  renderMarketContext(evalData.market_context);
  renderScenarioCards(evalData.financial_snapshot.scenarios);
  renderActionChart(evalData.ranked_actions);
  renderAnalysisDetail(brief, evalData.top_recommendation);
  renderGuardrails(guardrails, evalData.meta);

  // Reset detail to collapsed
  detailContent.classList.add('collapsed');
  detailContent.classList.remove('expanded');
  detailBtn.textContent = 'Show analysis';

  resultsEl.classList.remove('hidden');
  staggerReveal();
}

// ══════════════════════════════════════════════════════
//  AI BRIEF (compact)
// ══════════════════════════════════════════════════════
function renderBrief(ex, isAI, topRec, model) {
  const confPct = Math.round(ex.confidence_score * 100);
  const source  = isAI ? `AI interpretation \u00b7 ${model}` : 'Deterministic analysis';

  briefEl.innerHTML = `
    <div class="brief-eyebrow">This month\u2019s highest-leverage action</div>
    <h1 class="brief-action">${topRec.action}</h1>
    <p class="brief-narrative">${ex.narrative}</p>
    <p class="brief-reasoning">${ex.reasoning}</p>
    <div class="brief-badges">
      ${topRec.impact_summary ? `<span class="badge badge-green">${topRec.impact_summary.replace('Projected impact: ', '')}</span>` : ''}
      <span class="badge badge-blue">Confidence ${confPct}%</span>
      ${ex.risk_warnings && ex.risk_warnings.length ? `<span class="badge badge-gold">${ex.risk_warnings.length} risk warning${ex.risk_warnings.length > 1 ? 's' : ''}</span>` : ''}
    </div>
    <div class="conf-bar-track">
      <div class="conf-bar-fill" style="width:${confPct}%"></div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:8px">
      <span style="font-size:.75rem;color:var(--text-light)">${source}</span>
      <span style="font-size:.75rem;font-weight:600;color:var(--text-muted)">${confPct}% confidence</span>
    </div>
  `;
}

function buildFallback(evalData) {
  const s   = evalData.financial_snapshot;
  const top = evalData.ranked_actions[0];
  const rec = evalData.top_recommendation;
  const name = currentProfile?.first_name || '';
  const goalLabel = GOAL_PURPOSE_LABELS[currentProfile?.goal_purpose] || 'goal';

  const greeting = name ? `${name}, ` : '';
  const narrative =
    `${greeting}${rec.impact_summary} ` +
    `Your savings rate of ${pct(s.savings_rate)} and ${s.liquidity_ratio.toFixed(1)} months ` +
    `of emergency reserves position you well toward your ${goalLabel.toLowerCase()}. ` +
    `Under base conditions your ${goalLabel.toLowerCase()} probability is ${pct(s.estimated_goal_probability)}.`;

  const reasoning = top.rationale ||
    'This action produced the strongest composite score across goal progress, risk adjustment, and liquidity impact.';

  const alts = evalData.ranked_actions.slice(1, 3)
    .map(a => `${a.name} (score ${a.total_score.toFixed(2)}): ${a.rationale}`)
    .join(' ');

  const warnings = s.insights.filter(i => {
    const l = i.toLowerCase();
    return l.includes('drop') || l.includes('below') || l.includes('exceeds') || l.includes('only');
  });

  const gap = evalData.ranked_actions[0].total_score -
    (evalData.ranked_actions[1]?.total_score || 0);
  const confidence = gap > 0.3 ? 0.90 : gap > 0.1 ? 0.72 : 0.50;

  return {
    narrative,
    reasoning,
    alternatives_analysis: alts || 'Alternative actions were evaluated but scored lower overall.',
    risk_warnings: warnings.length ? warnings : ['Review your allocation periodically as market conditions change.'],
    confidence_score: confidence,
    disclaimer: '',
  };
}

// ══════════════════════════════════════════════════════
//  CONTROLS
// ══════════════════════════════════════════════════════
function renderControls(actionName) {
  controlsEl.innerHTML = `
    <button class="btn-primary" onclick="onApprove()">Approve Action</button>
    <button class="btn-outline" onclick="onSimulate()">Explore Alternatives</button>
    <button class="btn-ghost" onclick="onDefer()">Defer Decision</button>
  `;
}

function onApprove() { toast('Action approved. In production this would initiate a workflow.'); }
function onSimulate() {
  document.getElementById('action-chart').scrollIntoView({ behavior: 'smooth', block: 'start' });
  toast('Explore alternatives in the action comparison chart below.');
}
function onDefer() { toast('Decision deferred. We\u2019ll re-evaluate next month.'); }

// ══════════════════════════════════════════════════════
//  GOAL PROGRESS RING
// ══════════════════════════════════════════════════════
function renderGoalRing(goalProb) {
  const pctVal = Math.round(goalProb * 1000) / 10;
  const R = 54, CX = 64, CY = 64, SW = 10;
  const C = 2 * Math.PI * R;
  const offset = C * (1 - goalProb);
  const color = goalProb >= 0.7 ? 'var(--green)' : goalProb >= 0.4 ? 'var(--gold)' : 'var(--red)';

  goalRingCard.innerHTML = `
    <svg class="ring-svg" width="128" height="128" viewBox="0 0 128 128">
      <circle cx="${CX}" cy="${CY}" r="${R}" fill="none" stroke="var(--gray-track)" stroke-width="${SW}"/>
      <circle cx="${CX}" cy="${CY}" r="${R}" fill="none" stroke="${color}" stroke-width="${SW}"
        stroke-dasharray="${C}" stroke-dashoffset="${offset}"
        stroke-linecap="round" transform="rotate(-90 ${CX} ${CY})"
        style="transition: stroke-dashoffset 1s ease"/>
      <text x="${CX}" y="${CY - 2}" text-anchor="middle" dominant-baseline="central"
        class="ring-center-text" font-size="22">${pctVal}%</text>
      <text x="${CX}" y="${CY + 16}" text-anchor="middle" class="ring-label-text" font-size="9">probability</text>
    </svg>
    <div class="glance-label">Goal Progress</div>
  `;
}

// ══════════════════════════════════════════════════════
//  ALLOCATION DONUT
// ══════════════════════════════════════════════════════
function renderAllocationDonut(profile) {
  if (!profile) return;
  const equity = profile.portfolio_equity_pct || 0;
  const bonds  = profile.portfolio_bond_pct || 0;
  const cash   = Math.max(0, 1 - equity - bonds);

  const R = 54, CX = 64, CY = 64, SW = 10;
  const C = 2 * Math.PI * R;

  const segments = [
    { pct: equity, color: 'var(--green)', label: 'Equity' },
    { pct: bonds,  color: 'var(--blue)',  label: 'Bonds' },
    { pct: cash,   color: 'var(--text-light)', label: 'Cash' },
  ].filter(s => s.pct > 0);

  let arcs = '';
  let cumulative = 0;
  segments.forEach(seg => {
    const dashLen = C * seg.pct;
    const dashGap = C - dashLen;
    const rot = -90 + (cumulative * 360);
    arcs += `<circle cx="${CX}" cy="${CY}" r="${R}" fill="none"
      stroke="${seg.color}" stroke-width="${SW}"
      stroke-dasharray="${dashLen} ${dashGap}"
      transform="rotate(${rot} ${CX} ${CY})"/>`;
    cumulative += seg.pct;
  });

  const legend = segments.map(s =>
    `<div class="donut-legend-item"><span class="legend-dot" style="background:${s.color}"></span>${s.label} ${Math.round(s.pct * 100)}%</div>`
  ).join('');

  allocDonutCard.innerHTML = `
    <svg class="donut-svg" width="128" height="128" viewBox="0 0 128 128">
      <circle cx="${CX}" cy="${CY}" r="${R}" fill="none" stroke="var(--gray-track)" stroke-width="${SW}"/>
      ${arcs}
    </svg>
    <div class="donut-legend">${legend}</div>
    <div class="glance-label">Portfolio Allocation</div>
  `;
}

// ══════════════════════════════════════════════════════
//  METRIC MINI-BARS (Savings & Liquidity)
// ══════════════════════════════════════════════════════
function renderSavingsMetric(snap) {
  const rate = snap.savings_rate;
  const fillPct = Math.min(rate * 100, 100);
  savingsCard.innerHTML = `
    <div class="glance-value">${pct(rate)}</div>
    <div class="glance-label">Savings Rate</div>
    <div class="metric-bar-track"><div class="metric-bar-fill green" style="width:${fillPct}%"></div></div>
    <div style="font-size:.75rem;color:var(--text-muted);margin-top:6px">$${fmt(snap.monthly_surplus)}/mo surplus</div>
  `;
}

function renderLiquidityMetric(snap) {
  const months = snap.liquidity_ratio;
  const fillPct = Math.min((months / 12) * 100, 100);
  const color = months >= 6 ? 'green' : months >= 3 ? 'gold' : 'red';
  liquidityCard.innerHTML = `
    <div class="glance-value">${months.toFixed(1)} mo</div>
    <div class="glance-label">Liquidity Ratio</div>
    <div class="metric-bar-track"><div class="metric-bar-fill ${color}" style="width:${fillPct}%"></div></div>
    <div style="font-size:.75rem;color:var(--text-muted);margin-top:6px">Months of expenses covered</div>
  `;
}

// ══════════════════════════════════════════════════════
//  SCENARIO CARDS
// ══════════════════════════════════════════════════════
function renderScenarioCards(scenarios) {
  const icons = { base: '\u2694\uFE0F', recession: '\u{1F4C9}', bull: '\u{1F4C8}' };
  const labels = { base: 'Base Case', recession: 'Recession', bull: 'Bull Market' };
  const classes = { base: 'base', recession: 'recession', bull: 'bull' };

  scenarioGrid.innerHTML = scenarios.map(s => `
    <div class="scenario-card ${classes[s.name] || 'base'}">
      <div class="scenario-icon">${icons[s.name] || '\u{1F4CA}'}</div>
      <div class="scenario-name">${labels[s.name] || s.label}</div>
      <div class="scenario-prob">${pct(s.goal_probability)}</div>
      <div class="scenario-sub">
        $${fmt(s.projected_value)} projected<br>
        ${pct(s.annual_return)} annual return
      </div>
    </div>
  `).join('');
}

// ══════════════════════════════════════════════════════
//  ACTION COMPARISON CHART
// ══════════════════════════════════════════════════════
function renderActionChart(actions) {
  if (!actions || !actions.length) return;

  const maxScore = Math.max(...actions.map(a => a.total_score), 0.01);

  const rows = actions.map((a, i) => {
    const goalW = Math.max(0, a.goal_delta) / maxScore * 100;
    const liqW  = Math.max(0, a.liquidity_delta) / maxScore * 100;
    const riskW = Math.max(0, a.risk_delta) / maxScore * 100;
    const totalW = (a.total_score / maxScore) * 100;

    return `
      <div class="action-row ${i === 0 ? 'top-action' : ''}">
        <div class="action-name">${i === 0 ? '\u2B50 ' : ''}${a.name}</div>
        <div class="action-bar-track">
          <div class="action-seg goal" style="width:${totalW}%" title="Score: ${a.total_score.toFixed(2)}"></div>
        </div>
        <div class="action-score">${a.total_score.toFixed(2)}</div>
      </div>
    `;
  }).join('');

  actionChart.innerHTML = `
    ${rows}
    <div class="action-legend">
      <div class="action-legend-item"><span class="action-legend-dot" style="background:var(--green)"></span>Composite Score</div>
    </div>
  `;
}

// ══════════════════════════════════════════════════════
//  ANALYSIS DETAIL (collapsible)
// ══════════════════════════════════════════════════════
function renderAnalysisDetail(ex, topRec) {
  const tradeoff = topRec.tradeoff || 'No significant tradeoffs identified for this action.';
  const alts = ex.alternatives_analysis || 'No alternatives analysis available.';
  const warnings = (ex.risk_warnings && ex.risk_warnings.length)
    ? ex.risk_warnings.map(w => `<li style="margin-bottom:6px">\u26A0\uFE0F ${w}</li>`).join('')
    : '<li>No risk warnings at this time.</li>';

  detailContent.innerHTML = `
    <div class="detail-grid">
      <div class="detail-block">
        <div class="detail-block-title">Tradeoffs</div>
        <div class="detail-block-content">${tradeoff}</div>
      </div>
      <div class="detail-block">
        <div class="detail-block-title">What Wasn\u2019t Recommended</div>
        <div class="detail-block-content">${alts}</div>
      </div>
      <div class="detail-block">
        <div class="detail-block-title">Risk Warnings</div>
        <div class="detail-block-content"><ul style="padding-left:18px;margin:0">${warnings}</ul></div>
      </div>
    </div>
  `;
}

// ══════════════════════════════════════════════════════
//  MARKET CONTEXT (Holdings + Chart)
// ══════════════════════════════════════════════════════
function renderMarketContext(mkt) {
  if (!mkt || !mkt.holdings || !mkt.holdings.length) {
    marketEl.style.display = 'none';
    chartSection.style.display = 'none';
    return;
  }
  const hasPrice = mkt.holdings.some(h => h.price != null);
  if (!hasPrice) {
    marketEl.style.display = 'none';
    chartSection.style.display = 'none';
    return;
  }

  marketEl.style.display = '';
  holdingsCard.innerHTML = `
    <table class="holdings-table">
      <thead><tr><th>Ticker</th><th>Name</th><th>Type</th><th>Price</th><th>1Y</th><th>3Y</th><th>5Y</th></tr></thead>
      <tbody>
        ${mkt.holdings.map(h => `
          <tr>
            <td style="font-weight:600">${h.ticker}</td>
            <td>${h.name}</td>
            <td><span class="bucket-label ${h.bucket}">${h.bucket}</span></td>
            <td>${h.price != null ? '$' + h.price.toFixed(2) : '\u2014'}</td>
            <td style="color:${retColor(h.return_1y)}">${retFmt(h.return_1y)}</td>
            <td style="color:${retColor(h.return_3y)}">${retFmt(h.return_3y)}</td>
            <td style="color:${retColor(h.return_5y)}">${retFmt(h.return_5y)}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  if (mkt.portfolio_history && mkt.portfolio_history.length > 2) {
    chartSection.style.display = '';
    renderChart(mkt.portfolio_history, mkt.data_as_of);
  } else {
    chartSection.style.display = 'none';
  }
}

function retFmt(v) {
  if (v == null) return '\u2014';
  return (v >= 0 ? '+' : '') + (v * 100).toFixed(1) + '%';
}
function retColor(v) {
  if (v == null) return 'var(--text-muted)';
  return v >= 0 ? 'var(--green)' : 'var(--red)';
}

function renderChart(history, asOf) {
  const W = 740, H = 220, PAD_L = 50, PAD_R = 16, PAD_T = 12, PAD_B = 32;
  const plotW = W - PAD_L - PAD_R;
  const plotH = H - PAD_T - PAD_B;

  const values = history.map(p => p.value);
  const dates  = history.map(p => p.date);
  const minV = Math.min(...values) * 0.995;
  const maxV = Math.max(...values) * 1.005;
  const rangeV = maxV - minV || 1;

  const points = values.map((v, i) => {
    const x = PAD_L + (i / (values.length - 1)) * plotW;
    const y = PAD_T + plotH - ((v - minV) / rangeV) * plotH;
    return { x, y };
  });

  const line = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
  const area = line + ` L${points[points.length - 1].x.toFixed(1)},${PAD_T + plotH} L${PAD_L},${PAD_T + plotH} Z`;

  const gridLines = 4;
  let gridSvg = '';
  let labelSvg = '';
  for (let i = 0; i <= gridLines; i++) {
    const y = PAD_T + (i / gridLines) * plotH;
    const val = maxV - (i / gridLines) * rangeV;
    gridSvg += `<line x1="${PAD_L}" x2="${W - PAD_R}" y1="${y}" y2="${y}" stroke="var(--border)" stroke-width="1"/>`;
    labelSvg += `<text x="${PAD_L - 8}" y="${y + 4}" text-anchor="end" fill="var(--text-light)" font-size="10">$${(val / 1000).toFixed(1)}k</text>`;
  }

  const monthLabels = [];
  const step = Math.max(Math.floor(dates.length / 6), 1);
  for (let i = 0; i < dates.length; i += step) {
    const x = PAD_L + (i / (dates.length - 1)) * plotW;
    const d = new Date(dates[i]);
    const label = d.toLocaleDateString('en', { month: 'short', year: '2-digit' });
    monthLabels.push(`<text x="${x}" y="${H - 4}" text-anchor="middle" fill="var(--text-light)" font-size="10">${label}</text>`);
  }

  const lastVal = values[values.length - 1];
  const firstVal = values[0];
  const totalReturn = ((lastVal / firstVal) - 1) * 100;
  const clr = totalReturn >= 0 ? 'var(--green)' : 'var(--red)';

  chartCard.innerHTML = `
    <svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="font-family:var(--font);width:100%;height:auto">
      <defs>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="var(--green)" stop-opacity="0.15"/>
          <stop offset="100%" stop-color="var(--green)" stop-opacity="0.01"/>
        </linearGradient>
      </defs>
      ${gridSvg}
      ${labelSvg}
      ${monthLabels.join('')}
      <path d="${area}" fill="url(#areaGrad)"/>
      <path d="${line}" fill="none" stroke="var(--green)" stroke-width="2" stroke-linejoin="round"/>
    </svg>
    <div style="display:flex;justify-content:space-between;padding:12px 4px 0;font-size:.8rem;color:var(--text-muted)">
      <span>$${firstVal.toLocaleString()} \u2192 $${lastVal.toLocaleString()} (<span style="color:${clr};font-weight:600">${totalReturn >= 0 ? '+' : ''}${totalReturn.toFixed(1)}%</span>)</span>
      <span>Data as of ${asOf || 'N/A'}</span>
    </div>
  `;
}

// ══════════════════════════════════════════════════════
//  GUARDRAILS
// ══════════════════════════════════════════════════════
function renderGuardrails(tags, meta) {
  const defaultTags = [
    'Deterministic projections',
    'AI interprets only',
    'No auto-execution',
    'Human approval required',
  ];
  const list = (tags && tags.length) ? tags : defaultTags;
  const src = meta && meta.data_source ? meta.data_source : 'Hardcoded estimates';

  guardrailsEl.innerHTML = `
    <p>This system does not execute trades or alter your accounts.
       All projections are deterministic estimates. Market data sourced from ${src}.
       AI interprets structured results only.</p>
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:10px">
      ${list.map(t => `<span class="badge badge-blue" style="font-size:.7rem">${t}</span>`).join('')}
    </div>
  `;
}

// ── Stagger reveal ─────────────────────────────────────
function staggerReveal() {
  const els = resultsEl.querySelectorAll('.reveal');
  els.forEach((el, i) => {
    el.style.animationDelay = `${i * 100}ms`;
  });
  resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── Toast ──────────────────────────────────────────────
function toast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.remove('hidden');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => toastEl.classList.add('hidden'), 3000);
}

// ── Helpers ────────────────────────────────────────────
function pct(v) { return (v * 100).toFixed(1) + '%'; }
function fmt(v) { return Math.round(v).toLocaleString(); }
function fmtK(v) { return v >= 1000 ? Math.round(v / 1000) + 'K' : v; }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ══════════════════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════════════════
(function init() {
  initCardSelectors();
  const saved = loadProfile();
  if (saved) {
    currentProfile = saved;
    showDashboard();
  } else {
    showOnboarding(null);
  }
})();
