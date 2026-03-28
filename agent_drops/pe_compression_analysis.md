# Quantitative Analysis of P/E Multiple Compression and AI-Driven Market Disruption

## Mathematical Foundations of Valuation and Multiple Compression

The valuation of equities in public markets relies fundamentally on the dynamic interplay between corporate earnings growth and the price-to-earnings (P/E) multiple that market participants are willing to assign to those anticipated future cash flows. Multiple compression is a specific financial phenomenon occurring when a security's market price declines or remains stagnant even as the underlying fundamental earnings remain stable or increase. This results in a mathematical contraction of the P/E ratio. Historically, this structural repricing is initiated by macroeconomic tightening, dramatic shifts in the equity risk premium, or the onset of technological paradigm shifts that permanently alter long-term terminal growth assumptions.

### Gordon Growth Model (GGM)

To model multiple compression with rigorous accuracy, quantitative analysts must rely on the Gordon Growth Model (GGM), which establishes the foundational theory for the P/E ratio. The intrinsic present value of a stock (P₀) is defined by its expected dividend or free cash flow to equity (D₁), the cost of equity capital (kₑ), and the perpetual terminal growth rate (g):

```
P₀ = D₁ / (kₑ - g)
```

By dividing both sides by expected EPS (E₁), the theoretical forward P/E ratio:

```
P₀/E₁ = (D₁/E₁) / (kₑ - g) = Payout Ratio / (kₑ - g)
```

### Three Primary Independent Variables

1. **Payout Ratio**: Proportion of earnings returned to shareholders
2. **Cost of Equity (kₑ)**: Driven by risk-free rate and Beta (β) via CAPM. Elevated risk or hawkish rates → kₑ rises → denominator expands → multiple compresses violently
3. **Expected Growth Rate (g)**: Long-term earnings trajectory. Downward revision in terminal g is the primary catalyst for severe, idiosyncratic compression during tech disruption

### Total Return Algorithm

```
Total Return ≈ Earnings Growth + Multiple Change + Dividend Yield
```

The "Multiple Change" variable is the most critical and volatile vector in the current AI landscape. Markets are recalibrating long-term growth (g) and competitive risk (β) for legacy business models — this cognitive repricing leads to compression events BEFORE actual earnings deterioration appears in quarterly filings.

---

## Historical P/E Data and Statistical Volatility Analysis

### Long-Term Baseline
- S&P 500 (Jan 1971 – Jun 2017): Average P/E = **19.4x**, Median = **17.7x**
- For most of this 46-year period, market P/E resided BELOW the 19.4x average

### Key Historical Anomaly: 2008 GFC
- Earnings collapsed ~90% in one year
- Trailing P/E paradoxically spiked above **120x** (denominator collapsed faster than numerator)
- Lesson: Must use forward P/E or cyclically-adjusted earnings for compression modeling

### Post-COVID Compression Cycle
- Late 2021 peak: P/E expanded to **35x** amid fiscal/monetary exuberance
- 2022 rate hiking cycle: Compressed to less than **25x**

### Quarterly S&P 500 P/E Progression (Q3 2021 – Q3 2025)

| Quarter | P/E Ratio | QoQ Change | Context |
|---------|-----------|------------|---------|
| Sep 2021 | 24.56 | — | Peak pandemic-era growth valuations |
| Dec 2021 | 24.09 | -1.91% | Anticipation of Fed hawkishness |
| Mar 2022 | 22.89 | -4.98% | First rate hikes commence |
| Jun 2022 | 19.69 | -13.98% | Aggressive tightening; peak compression |
| Sep 2022 | 19.17 | -2.64% | Bear market nadir |
| Dec 2022 | 22.23 | +15.96% | AI thesis forms post-ChatGPT |
| Mar 2023 | 23.46 | +5.53% | AI infra narrative drives mega-cap expansion |
| Jun 2023 | 24.59 | +4.81% | Gains concentrate in "Magnificent Seven" |
| Sep 2023 | 23.27 | -5.36% | "Higher for longer" rate fears |
| Dec 2023 | 24.79 | +6.53% | Rate cut optimism; multiples recover |
| Mar 2024 | 27.45 | +10.73% | Hyperscaler CapEx triggers semi expansion |
| Jun 2024 | 27.87 | +1.53% | Multiples stabilize amid AI frenzy |
| Sep 2024 | 28.77 | +3.22% | Peak 2024 AI optimism |
| Dec 2024 | 27.99 | -2.71% | Skepticism re: software terminal growth |
| Mar 2025 | 25.90 | -7.46% | Software compression from AI agent capabilities |
| Jun 2025 | 27.88 | +7.64% | Rotation from software to hardware/infra |
| Sep 2025 | 28.58 | +2.48% | Current equilibrium; high dispersion |

Recovery from 19.17x (Sep 2022) to 28.58x (Sep 2025) shows structural willingness to absorb elevated valuations when tethered to tech paradigm shifts — but aggregate numbers mask extreme internal dispersion.

---

## Cross-Sectional Regression Analysis of P/E Determinants

Standard regression: P/E = f(Expected Growth, Risk/β, Payout Ratio)

### Historical Regression Coefficients

| Year | Regression Equation | R² | Analysis |
|------|--------------------|----|----------|
| 1961 | P/E = 4.73 + 3.28(g) + 2.05(Payout) - 0.85(β) | 0.70 | Post-war expansion. Negative β confirms traditional theory |
| 1965 | P/E = 0.96 + 2.74(g) + 5.01(Payout) - 0.35(β) | 0.85 | Rising dividend importance; payout coefficient doubled |
| 1987 | P/E = 7.18 + 6.56(g) + 13.05(Payout) - 0.62(β) | 0.93 | Pre-Black Monday. Near-perfect fundamental explanation |
| 1991 | P/E = 2.77 + 13.86(g) + 22.89(Payout) - 0.13(β) | 0.32 | Recession distorted earnings. Model lost efficacy |
| 2000 | P/E = -17.22 + 155.65(g) + 10.93(Payout) + 16.44(β) | 0.25 | **Dot-com peak. Model broke. β coefficient INVERTED — higher risk = higher P/E** |

### Critical Insight

R² collapsed from 0.93 (1987) to 0.25 (2000) during tech frenzy. In 2000, the Beta coefficient inverted to **+16.44** — the market paradoxically rewarded risk with higher multiples, contradicting GGM.

**This is the historical precedent for the current AI cycle.** Volatile, unproven software integrations and capital-intensive semi firms are being valued on hypothetical TAM, not cash flows. When the paradigm reverts, Beta flipping from positive to negative will trigger unprecedented compression in high-risk tech — independent of earnings stability.

---

## Macroeconomic Variables Impacting Multiple Compression

Beyond firm-specific fundamentals, multiple compression is heavily dictated by macro aggregates. Since the 1960s, the market P/E has essentially acted as a slave to nominal interest rates.

### The Fed Model

The earnings yield (E/P = inverse of P/E) is intrinsically cointegrated with the 10-year Treasury yield. When bond yields rise, equity earnings yield must rise proportionally to maintain the equity risk premium. The only mechanism without instant earnings growth is a sharp price decline → P/E compresses.

Academic consensus: The Fed Model provides a superior description of P/E changes over time vs. mean-reverting models (Campbell & Shiller).

### Sector Sensitivity to Macro Shocks

Ranked via weighted z-score methodology (60% R², 40% Beta coefficient):

| Macro Variable | Positively Correlated (Beneficiaries) | Negatively Correlated (Compression Targets) | Mechanism |
|---|---|---|---|
| **10Y Treasury Yield** | Insurance, Banks, Regional Banks, Energy, Financials | Communication Services, Technology, Real Estate | Banks benefit via NIM expansion. Tech/Comms are "long-duration" — cash flows weighted in distant future, hyper-sensitive to higher discount rates |
| **Yield Curve Slope (10Y-2Y)** | Banks, Regional Banks (bear steepening) | Real Estate, Utilities (bear steepening) | Bear steepening: Banks +1.846% relative returns. Real Estate -2.09%, Utilities -2.2% |
| **10Y Breakeven Rate (Inflation)** | Oil & Gas Equipment, Metals & Mining | Health Care, Consumer Staples | Primary inflation hedge. During shocks (>1σ), Metals & Mining R² spikes from 0.03 → 0.379 |
| **US Dollar Index** | Consumer Staples | Metals & Mining, Materials, Oil & Gas Equipment | Strong USD suppresses multinational earnings translation + commodity pricing. During severe shocks, USD→Mining R² jumps from 0.047 → 0.496 |
| **WTI Crude Oil** | Oil & Gas Equipment, E&P, Energy | Health Care, Consumer Staples, Utilities | Crude spikes punish Utilities/Staples via input costs. Energy R² increases from 0.143 → 0.402 during oil shocks |

**Key insight:** Cannot stress-test for AI disruption without first establishing baseline vulnerability to yield curve steepening or dollar shocks — these remain the primary drivers of market-wide multiple compression.

---

## Historical Technological Paradigm Shifts and Market Cycles

### Carlota Perez Framework

~50-year megacycles, each initiated by a massive technological leap:

1. **Industrial Revolution** (1771) — Arkwright's mill, Cromford
2. **Age of Steam & Railways** (1829) — 'Rocket' steam engine, Liverpool-Manchester
3. **Age of Steel, Electricity & Heavy Engineering** (1875) — Carnegie Bessemer steel plant
4. **Age of Oil, Automobile & Mass Production** (1908) — First Ford Model-T
5. **Age of Information & Telecommunications** (1971) — Intel microprocessor
6. **Age of Artificial Intelligence** (2022–Present) — Scalable LLMs

### Four Phases of Every Revolution

1. **Irruption** — Proof of concept demonstrated
2. **Frenzy** — Financial capital floods the sector. Valuations divorce from fundamentals. Massive infrastructure overbuilding. Multiple expansion
3. **Synergy** — Breaking point → market crash. Speculative excess purged. Surviving best uses identified. Efficient capital deployment
4. **Maturity** — Technology saturates. Profit margins compress to macro mean

**The critical transition: Frenzy → Synergy.** Almost universally marked by a spectacular crash and severe, systemic multiple compression.

### Historical Analogues

**1840s UK Railway Boom:**
- Railway miles nearly quadrupled (1843–1853)
- Revenue per mile flat or negative — capacity outpaced demand
- Painful correction, massive equity capital destruction

**1990s Dot-Com Telecom Boom:**
- 39 million miles of fiber optic cable installed
- $800B+ spent on internet infrastructure
- Earnings failed to support debt + expanded multiples
- Nasdaq lost **78%** by October 2002
- Cisco lost **80%** of market cap — picks-and-shovels compression

---

## 1990s Dot-Com Era vs. Current AI Infrastructure Buildout

### Similarities
- Massive infrastructure CapEx driven by theoretical demand projections
- Multiple expansion on narrative, not immediate cash flows

### Key Differences

| Metric | Dot-Com (2000) | AI Era (Late 2025) |
|---|---|---|
| Forward P/E (tech sector) | **55x** | **29.7x** |
| Historical median | — | 22x |
| Earnings quality | Many companies had zero earnings/FCF | Massive entrenched revenue, ROE >50%, low leverage, aggressive buybacks |

### AI Data Center Capital Intensity

| Generation | Power per Rack | GPUs per Rack | Cooling |
|---|---|---|---|
| Data Center 1.0 (Cloud era) | 5–15 kW | N/A | Standard air |
| Current AI transitional | 130–200 kW | 144 GPUs | Liquid + air |
| Next-gen purpose-built AI | **500+ kW** | 576 GPUs | Advanced liquid |

### CapEx Scale
- Hyperscaler CapEx: ~$200B annually
- Total data center development: trending toward **$1 trillion**
- Morgan Stanley estimate: $1.4T of $2.9T data center CapEx through 2028 from tech companies; remainder from private credit, corporate bonds, securitizations

### The Compression Risk Vector

The risk is NOT an immediate lack of earnings. It's **Return on Invested Capital (ROIC).**

If training-to-inferencing transition is delayed, OR if efficient open-weight models commoditize the software layer (making massive proprietary models unviable) → unprecedented infrastructure investments suffer declining marginal returns → **violent, systemic repricing and multiple compression across hardware, semiconductor, and data center real estate equities.**

---

## AI Disruption: Sentiment vs. Fundamentals and Target Industries

The market has ceased treating technology as a monolithic growth engine — it's aggressively bifurcating into "AI Winners" and "AI Losers," generating unprecedented idiosyncratic volatility within previously correlated sectors.

### Performance Divergence (H2 2025)
- AI Winners portfolio: **+23.0%**
- AI Losers portfolio: **-14.1%**
- UBS "at risk from AI" basket: **-50%** over 12 months

### The Catalyst: Agentic AI and the Software Selloff

**Early thesis (2023–2024):** Generative AI = augmentative tool → integrates into existing SaaS → boosts subscription pricing → software multiples expand.

**Paradigm shift:** Anthropic's Claude agent capabilities demonstrated AI evolving beyond augmentation into autonomous execution — complex coding, legal review, multi-step operational workflows with minimal human intervention.

**Market reaction:** Institutional panic over software economic moats. "Vibe-coding" thesis — end users prompt AI to generate custom apps on the fly → commoditizes application software → strips legacy vendor pricing power.

- **S&P 500 Software industry group: -31% (Oct 28, 2025 → Feb 23, 2026)**

### Textbook Compression Event

This was purely sentiment-driven, divorced from operating reality:
- **No deterioration** in reported revenue, operating margins, or FCF
- Goldman Sachs: 2-year forward earnings estimates for software **climbed 5%** during the same 3-month period investors were dumping stocks
- Driver: Terminal growth (g) revised from 15–20% medium-term revenue growth → slashed to 5–10%
- This single variable adjustment to DCF models justified the price decline, wiping out massive market cap despite intact near-term earnings

### Disruption Target Classification

#### Vulnerable Industries ("AI Losers")

| Category | Vulnerable Industries | Representative Equities | Compression Thesis |
|---|---|---|---|
| **Workflow & Application Software** | CRM, E-signature, Digital Workflow | DocuSign (-83% over 5yr), Salesforce | Clients use internal agentic AI to replace expensive SaaS subscriptions |
| **Professional Services** | Tech Consulting, Legal, Financial Admin, HR | Accenture (severe replication risk) | Agentic AI drastically reduces billable labor hours for integration, legal review, consulting |
| **Digital Education & Content** | Language Learning, Tutoring, Localization | Duolingo (immediate competition risk) | Open-weight models + specialized LLMs offer superior personalized tutoring |
| **Data Processing & Logistics** | Freight brokerage, RE admin, Back-office accounting | Logistics & RE intermediaries | AI removes friction in supply/demand matching, bypassing human brokers |

#### Resilient Industries ("AI Winners")

| Category | Resilient Industries | Representative Equities | Expansion/Stability Thesis |
|---|---|---|---|
| **Cybersecurity** | Zero-trust, Endpoint protection, Cloud security | Cloudflare, CrowdStrike, Palo Alto Networks | Open-weight models exponentially increase threat vectors; adversarial AI manipulation necessitates massive security spend |
| **Energy & Utilities** | Power generation, Grid modernization, Energy storage | Fluence Energy, Xcel Energy | AI can't generate electricity. Liquid-cooled data centers need unprecedented baseload power — utilities are critical bottleneck assets |
| **Semiconductors & Data Centers** | Advanced chip design, Foundry, Physical DCs | NVIDIA, Core Scientific, Firmus | Physical manifestation of AI requires hard assets with immense barriers to entry |
| **Biotech & Healthcare Delivery** | Pharma, Life sciences, Direct patient care | Argenx, Bio-pharma innovators | Physical care delivery, surgery, clinical trials require "human interaction premium" + regulatory compliance |

---

## Quantitative Variables for AI Disruption Modeling

### Labor Substitution PCA Weights

From Yale Budget Lab research — Principal Component Analysis synthesizing occupational exposure metrics into unified vulnerability scores:

| Exposure Variable | PCA Weight | Description |
|---|---|---|
| dv_rating_beta | **0.426** | Variance exposure from empirical task disruption ratings. Highest occupational variance |
| human_rating_beta | **0.425** | Human-evaluated task vulnerability. Qualitative counterbalance to algorithmic scoring |
| genaiexp_estz_total | **0.419** | Total estimated exposure to GenAI text/code processing across workforce |
| AIOE (AI Occupational Exp.) | **0.410** | Standardized measure of tasks subject to automation/labor substitution |
| genai_exp_estz_core | **0.407** | Core essential task exposure to GenAI (non-peripheral job functions) |
| ai_applicability_score | **0.359** | Applicability of existing commercial AI tools to firm's specific workflows |

**Key finding:** A one-unit increase in aggregate PCA score → **0.0617 increase in earnings variance** → justifies upward β adjustment in CAPM → increases kₑ → forces multiple compression.

NBER event studies confirm: labor-based GenAI exposure **negatively and significantly predicts cumulative abnormal returns (CARs)** — labor substitution is a primary, quantifiable driver of firm devaluation.

### Financial Stability Board (FSB) Monitoring Indicators

Systemic risk metrics for AI adoption vulnerability:

1. **Concentration Risk** — Reliance on oligopoly of hyperscalers/third-party LLM providers. High dependency = loss of operational control + margin stability
2. **Substitutability** — Friction/cost of swapping foundational AI models. Proprietary lock-in = higher disruption risk vs. model-agnostic/open-weight architectures
3. **Criticality** — % of core revenue dependent on uninterrupted AI agent functioning. If AI fails/hallucinates, what % of daily revenue halts?
4. **Cyber Vulnerability** — Cisco assessments: open-weight LLMs show multi-turn attack success rates **2x–10x** higher than single-turn. Heavy open-model reliance → higher risk premium

**Composite metric:** Cross-reference labor PCA exposure score × FSB concentration metrics → construct **"AI Disruption Beta"** → dynamically adjust discount rate (kₑ) in DCF models.

---

## Advanced Financial Modeling Methodologies

### Beyond Linear Regression

Standard OLS is structurally insufficient for non-linear AI-driven capital markets. The relationship between AI exposure and equity returns is rarely linear — initial AI integration may boost margins (via cost cuts), but eventually destroys pricing power (via commoditization). Neural networks with hidden layers capture these inflection points.

### Deep Learning Architectures for Equity Prediction

- **CNNs** (Convolutional Neural Networks) — Pattern recognition across massive datasets
- **LSTMs** (Long Short-Term Memory) — Temporal sequence modeling for time-series financial data
- Features: historical transactions, unstructured news text, real-time social sentiment

**Performance:** Technical ML approaches on monthly rebalancing have achieved cumulative returns of approximately **1,977.71%** — demonstrating alpha-generating power of non-linear modeling in volatile environments.

### Reinforcement Learning and Fuzzy Logic

**Reinforcement Learning (RL):**
- Algorithmic "agent" learns optimal trading behavior through trial-and-error in simulated market environments
- Deep Q-learning dynamically adjusts asset allocations to maximize returns against risk tolerance
- **Deep hedging:** RL derives optimal real-time hedging strategies for options/derivatives under real-world frictions (transaction costs, liquidity vacuums)
- Critical for shorting "AI Losers" — these sentiment-driven stocks are prone to violent short-squeezes; static linear hedging = catastrophic capital destruction

**Fuzzy Logic:**
- Current software repricing is driven by sentiment, not hard data → fuzzy systems evaluate variables on a continuous spectrum of truth values
- Mamdani/Sugeno models and hybrid ANFIS process ambiguity, nuance, uncertainty
- **Fuzzy entropy calculations** quantify "degree of market intricateness" → objective metric for the hype cycle
- Identifies exactly when multiple expansion crosses from rational growth into irrational "Frenzy" → compression imminent
- Entropy-based ML approaches: consistent returns totaling approximately **701%** over testing periods

---

## Strategic Portfolio Allocation: The HALO Framework

### HALO = Heavy Assets, Low Obsolescence (Morgan Stanley)

Designed to mitigate AI-specific volatility during the dangerous "Frenzy" phase.

**Heavy Assets:**
- Capital-intensive, physically difficult-to-replicate infrastructure with embedded scarcity value
- Historical precedent: Energy and physical assets dramatically outperformed during 1970s inflation shocks + post-COVID supply chain constraints
- Current application: Overweight **Energy, Utilities, specialized Industrials**
- AI requires immense physical infrastructure + uninterrupted baseload power
- Companies owning the power grid, DC real estate, and semiconductor foundries = ultimate insulated beneficiaries, shielded from software obsolescence risk

**Low Obsolescence:**
- Sector-by-sector assessment of structural resilience
- **Healthcare & Biotech:** Often below 20x P/E, steady dividends, strict regulatory environment, physical biology complexity, human interaction premium → shielded from algorithmic substitution

### Duration Matching in a Deflationary AI Environment

AI introduces deflationary forces — removing friction, accelerating throughput, scaling software at near-zero marginal cost → macro environment may shift toward disinflationary growth.

BlackRock 2026 strategy: Balance income generation with duration risk. Hold high-quality fixed income for yield + equities only where AI-driven margin expansion meets deflationary growth (logistics, defense, mission-critical infrastructure).

### Institutional Fund Strategies

| Fund | Asset Class | Strategic Rationale | Key Metrics |
|---|---|---|---|
| **Strategic Income Opportunities (BSIIX)** | Flexible Bond / Fixed Income | Secures yield (5.59% YTM) while mitigating equity duration risk. Stabilizing ballast against tech volatility | Duration: 3.57yr. 6,866 holdings. Top: US Rate Derivatives (35.8%) |
| **iShares Flexible Income Active ETF (BINC)** | Multisector Active Fixed Income | Nimble active management, maximizes income (6.25% YTM) across Non-Agency Mortgages, EM | Duration: 3.48yr. Yield: 5.16% (30-day SEC). Top: Agency RMBS (17.37%) |
| **Global Allocation Fund (MALOX)** | Multi-Asset (Equity, FI, Commodities) | Unconstrained flexibility. Holds mega-cap AI winners (NVDA, GOOGL) but balanced with 26.6% FI + cash | Eq: 62.38%, FI: 26.60%, Cash: 7.29%. Top: NVIDIA (2.28%) |

---

## Avoiding the Valuation Trap

**Critical warning:** Do NOT buy "cheap" legacy software stocks just because multiples have compressed.

Dot-Com history proves: when a business model faces structural technological obsolescence, a low P/E is a **value trap**, not a buying opportunity.

If agentic AI commoditizes digital workflow platforms → terminal growth (g) trends toward zero or negative. Per the GGM:

```
P₀ = D₁ / (kₑ - g)
```

**Negative g mathematically demands severe, continuous price degradation** — regardless of how "cheap" the trailing multiple appears.

**Action:** Ruthlessly rotate capital out of AI-vulnerable entities (even at a short-term loss) → redeploy exclusively into firms with:
- True productivity-led growth
- Robust free cash flow generation
- Impenetrable physical or proprietary-data moats

---

## Synthesis and Strategic Recommendations

The global equity markets stand at the precipice of a profound structural realignment. The current volatility — violent, sentiment-driven compression of legacy software + simultaneous massive expansion of hardware/infrastructure multiples — is not transient. It is the early manifestation of the **Irruption → Frenzy transition** of the AI technological revolution.

### Key Deductions

1. **Multiple compression is rarely localized.** As the $1T+ AI CapEx cycle escalates, ROIC hurdle rates rise. If 10Y Treasury yields remain elevated (fiscal deficits, sticky inflation) → Fed Model dictates broader equity multiples must compress to maintain equity risk premium.

2. **Firms without moats face structural margin degradation.** Those lacking proprietary un-scrapable datasets, physical manufacturing moats, or high-touch human interaction premiums → relentless compression. Labor PCA scores forecast total collapse in pricing power as open-weight models + agentic AI democratize knowledge work.

3. **Terminal growth must be aggressively discounted** for professional services, administrative intermediaries, and legacy workflow software vendors.

4. **Adopt non-linear predictive architectures** (LSTMs, RL, Fuzzy Logic) capable of dynamically interpreting sentiment and hedging irrational volatility. Linear assumptions are insufficient.

5. **Anchor portfolios in HALO framework** — overweight the physical prerequisites of the digital revolution: energy generation, raw compute hardware, secure networking infrastructure.

**The disruption is no longer hypothetical. It is actively rewriting the mathematical foundations of equity valuation, demanding a ruthless recalculation of growth, risk, and intrinsic value across all asset classes.**

---

## Sources

- NYU Stern — Chapter 18: Earnings Multiples
- StockTitan — Multiple Compression vs Expansion
- Marshall & Stevens — S&P 500 P/E Historical Perspective
- Zacks IM — Evaluating AI Disruption Risk
- Current Market Valuation — S&P 500 CAPE Model
- YCharts — S&P 500 P/E Ratio (Quarterly)
- McKinsey — M&A Annual Report
- Advisor Perspectives — Technological Revolutions and Stock Returns
- PM Research — Compression/Expansion of Market P/E: Fed Model
- SSGA — Macroeconomic Variables and Sector Performance
- WisdomTree — Market Regimes; Bubble Narratives
- IntechOpen — Megacycles of the Economy
- Stratechery — Death and Birth of Technological Revolutions
- J.P. Morgan — Outlook 2026
- Goldman Sachs — Powering the AI Era; AI: In a Bubble?; Software Earnings; AI Winners/Losers
- BlackRock — AI-Driven Investing & Deflationary Growth
- Sparkco — AI Infrastructure Analysis 2025
- CFM — Review of 2025 & Expectations for 2026
- FRBSF — Boom and Bust in IT Investment
- Polar Capital — New AI Era in Technology
- LPL Financial — AI Disruption Survival Kit (March 2026)
- Cisco Blogs — Open Model Vulnerability Analysis
- Yale Budget Lab — Labor Market AI Exposure
- NBER — Generative AI and Firm Performance
- FSB — Monitoring AI Adoption
- PMC/NIH — AI Models for Stock Returns (Entropy-Based)
- Morgan Stanley — The BEAT: Creative Destruction in the Age of AI; AI Disruption Fears
- Vanguard — AI Exuberance: Economic Upside, Stock Market Downside
- SEC filings
- JM Finn — Cutting Through the Noise
