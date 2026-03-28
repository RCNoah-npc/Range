"""Comprehensive compression event database with full data points.

Every major multiple compression event across all sectors and cycles.
Each entry includes pre-crash fundamentals, the WHY, the industry context,
and macro conditions. The model scores each one, and we analyze the misses.
"""

import numpy as np
import json

# ============================================================
# MASTER COMPRESSION DATABASE
# Format per entry:
#   pe: trailing P/E at peak
#   sga: SG&A as % of revenue
#   gm: gross margin
#   de: debt/equity
#   fcf: FCF yield
#   roic: return on invested capital
#   drop: max drawdown from peak
#   recovered: did it recover to prior highs within 5 years?
#   industry: sector classification
#   year: year of compression event
#   why: documented reason(s) from post-mortems
#   moat_type: what moat did/didn't exist
#   macro: macro conditions at time of compression
# ============================================================

db = {
    # ================================================================
    # DOTCOM BUBBLE (1999-2002)
    # Macro: Fed hiking, Y2K spending pullback, irrational exuberance
    # ================================================================
    "CSCO_00":  {"pe":127,"sga":0.25,"gm":0.65,"de":0.10,"fcf":0.005,"roic":0.12,"drop":0.86,"recovered":False,"industry":"Networking","year":2000,"why":"Commoditization of networking hardware. Carrier capex collapse.","moat_type":"Scale but not switching cost","macro":"Fed hiking, dotcom bust"},
    "JDSU_00":  {"pe":500,"sga":0.30,"gm":0.45,"de":0.40,"fcf":-0.05,"roic":-0.02,"drop":0.99,"recovered":False,"industry":"Fiber Optics","year":2000,"why":"Telecom capex bubble burst. Product was a commodity.","moat_type":"None - commodity parts","macro":"Telecom bubble"},
    "SUNW_00":  {"pe":100,"sga":0.25,"gm":0.50,"de":0.15,"fcf":0.01,"roic":0.10,"drop":0.97,"recovered":False,"industry":"Enterprise Hardware","year":2000,"why":"Linux/commodity servers replaced proprietary SPARC. Open source killed moat.","moat_type":"Proprietary hardware (eroded by open source)","macro":"Dotcom bust"},
    "PALM_00":  {"pe":200,"sga":0.35,"gm":0.45,"de":0.20,"fcf":-0.02,"roic":0.05,"drop":0.99,"recovered":False,"industry":"Consumer Hardware","year":2000,"why":"PDA was a feature. Smartphones absorbed it entirely.","moat_type":"None - feature product","macro":"Dotcom bust"},
    "YHOO_00":  {"pe":800,"sga":0.40,"gm":0.80,"de":0.05,"fcf":-0.03,"roic":0.01,"drop":0.97,"recovered":False,"industry":"Internet Portal","year":2000,"why":"Portal model killed by Google search. Directory browsing replaced by search.","moat_type":"First mover only (no real moat)","macro":"Dotcom bust"},
    "CMGI_00":  {"pe":0,"sga":0.60,"gm":0.30,"de":0.50,"fcf":-0.15,"roic":-0.20,"drop":0.99,"recovered":False,"industry":"Internet Holding","year":2000,"why":"Internet holding company with no operating business. Pure speculation.","moat_type":"None","macro":"Dotcom bust"},
    "PCLN_00":  {"pe":0,"sga":0.50,"gm":0.40,"de":0.30,"fcf":-0.10,"roic":-0.15,"drop":0.97,"recovered":True,"industry":"Online Travel","year":2000,"why":"Dropped 97% but business model was REAL. Name-your-price had network effects. Recovered as Booking.com.","moat_type":"Network effects + supplier relationships","macro":"Dotcom bust"},
    "AMZN_00":  {"pe":0,"sga":0.35,"gm":0.25,"de":0.80,"fcf":-0.10,"roic":-0.15,"drop":0.93,"recovered":True,"industry":"E-Commerce","year":2000,"why":"Dropped 93% but was building real logistics + marketplace moat. Survived on vision.","moat_type":"Logistics + marketplace network effects (building)","macro":"Dotcom bust"},
    "MSFT_00":  {"pe":59,"sga":0.22,"gm":0.86,"de":0.0,"fcf":0.015,"roic":0.30,"drop":0.65,"recovered":True,"industry":"Enterprise Software","year":2000,"why":"Antitrust + dotcom bust. But OS+Office+Enterprise moat was impenetrable.","moat_type":"OS monopoly + enterprise switching costs","macro":"Antitrust + dotcom"},
    "INTC_00":  {"pe":50,"sga":0.15,"gm":0.62,"de":0.05,"fcf":0.02,"roic":0.22,"drop":0.78,"recovered":True,"industry":"Semiconductors","year":2000,"why":"Cyclical downturn. But x86 monopoly + fab advantage survived.","moat_type":"x86 monopoly + manufacturing moat","macro":"Dotcom bust"},
    "AAPL_00":  {"pe":25,"sga":0.18,"gm":0.28,"de":0.20,"fcf":0.01,"roic":0.05,"drop":0.80,"recovered":True,"industry":"Consumer Hardware","year":2000,"why":"Near bankruptcy. But Jobs returned, iPod saved it. Hardware+ecosystem moat built AFTER crash.","moat_type":"Brand (weak then) + ecosystem (built later)","macro":"Dotcom bust"},
    "QCOM_00":  {"pe":200,"sga":0.12,"gm":0.60,"de":0.05,"fcf":0.003,"roic":0.08,"drop":0.88,"recovered":True,"industry":"Semiconductors","year":2000,"why":"Bubble pop but CDMA patents were real IP moat. Licensing model survived.","moat_type":"Patent portfolio + licensing","macro":"Dotcom bust"},
    "ORCL_00":  {"pe":103,"sga":0.28,"gm":0.78,"de":0.20,"fcf":0.008,"roic":0.15,"drop":0.84,"recovered":True,"industry":"Enterprise Software","year":2000,"why":"Bubble valuation crashed but database monopoly was real. Enterprise switching cost survived.","moat_type":"Database switching costs + enterprise lock-in","macro":"Dotcom bust"},

    # ================================================================
    # GFC (2007-2009)
    # Macro: Housing bubble, subprime mortgage crisis, credit freeze
    # ================================================================
    "C_08":     {"pe":11,"sga":0.40,"gm":0.55,"de":8.0,"fcf":0.02,"roic":0.04,"drop":0.97,"recovered":False,"industry":"Banking","year":2008,"why":"Toxic mortgage-backed securities. Massive leverage (30:1). Government bailout required.","moat_type":"Banking franchise but toxic assets destroyed it","macro":"Housing collapse, credit freeze"},
    "BAC_08":   {"pe":11.5,"sga":0.35,"gm":0.50,"de":7.5,"fcf":0.03,"roic":0.05,"drop":0.94,"recovered":False,"industry":"Banking","year":2008,"why":"Countrywide acquisition brought toxic mortgages. Leverage amplified losses.","moat_type":"Deposit franchise but M&A destroyed value","macro":"Housing collapse"},
    "AIG_08":   {"pe":9,"sga":0.30,"gm":0.35,"de":6.0,"fcf":0.01,"roic":0.03,"drop":0.99,"recovered":False,"industry":"Insurance","year":2008,"why":"CDS exposure on mortgage securities. $182B government bailout. Leverage kill.","moat_type":"Insurance moat destroyed by derivatives desk","macro":"Credit crisis"},
    "LEH_08":   {"pe":8.5,"sga":0.45,"gm":0.40,"de":30.0,"fcf":-0.02,"roic":0.02,"drop":1.00,"recovered":False,"industry":"Investment Banking","year":2008,"why":"30:1 leverage ratio. Mortgage exposure. No government rescue. Bankruptcy.","moat_type":"Deal flow but zero balance sheet moat","macro":"Credit freeze, no bailout"},
    "WFC_08":   {"pe":13,"sga":0.38,"gm":0.58,"de":5.0,"fcf":0.04,"roic":0.08,"drop":0.78,"recovered":True,"industry":"Banking","year":2008,"why":"Dropped but deposit franchise survived. Bought Wachovia at distressed prices. Buffett backed it.","moat_type":"Deposit franchise + branch network","macro":"Credit crisis"},
    "JPM_08":   {"pe":10,"sga":0.35,"gm":0.55,"de":6.0,"fcf":0.03,"roic":0.06,"drop":0.68,"recovered":True,"industry":"Banking","year":2008,"why":"Best-managed bank. Bought Bear Stearns at distressed price. Moat strengthened by crisis.","moat_type":"Banking franchise + management quality","macro":"Credit crisis"},
    "GS_08":    {"pe":8,"sga":0.50,"gm":0.60,"de":12.0,"fcf":0.02,"roic":0.08,"drop":0.72,"recovered":True,"industry":"Investment Banking","year":2008,"why":"Hedged better than peers. Deal flow network + relationship moat survived.","moat_type":"Deal flow network + talent moat","macro":"Credit crisis"},
    "GE_08":    {"pe":15,"sga":0.20,"gm":0.35,"de":4.0,"fcf":0.04,"roic":0.06,"drop":0.84,"recovered":False,"industry":"Conglomerate","year":2008,"why":"GE Capital was a hidden bank. When credit froze, the industrial conglomerate nearly died. Complexity masked risk.","moat_type":"Brand + diversification (but complexity was the weakness)","macro":"Credit crisis"},
    "FNM_08":   {"pe":18,"sga":0.15,"gm":0.60,"de":50.0,"fcf":0.01,"roic":0.02,"drop":0.99,"recovered":False,"industry":"Government-Sponsored","year":2008,"why":"Fannie Mae. 50:1 leverage on mortgages. Government conservatorship.","moat_type":"Government charter (but leverage killed it)","macro":"Housing collapse"},

    # ================================================================
    # ENERGY CRASH (2014-2016)
    # Macro: Oil price collapse ($100 -> $26), OPEC production war
    # ================================================================
    "CHK_14":   {"pe":15,"sga":0.10,"gm":0.45,"de":3.5,"fcf":-0.08,"roic":0.02,"drop":0.98,"recovered":False,"industry":"Oil & Gas E&P","year":2014,"why":"Overleveraged on shale acquisitions. Oil price collapse breached debt covenants. Bankruptcy 2020.","moat_type":"Acreage position but leverage destroyed it","macro":"Oil crash $100->$26, OPEC war"},
    "SWN_14":   {"pe":22,"sga":0.08,"gm":0.40,"de":2.8,"fcf":-0.05,"roic":0.03,"drop":0.92,"recovered":False,"industry":"Natural Gas E&P","year":2014,"why":"Natural gas oversupply. High debt service. Commodity business with no pricing power.","moat_type":"Low-cost basin position (weak)","macro":"Energy price collapse"},
    "SD_14":    {"pe":18,"sga":0.12,"gm":0.35,"de":4.5,"fcf":-0.10,"roic":-0.01,"drop":0.99,"recovered":False,"industry":"Oil & Gas E&P","year":2014,"why":"Sandridge Energy. Overleveraged small E&P. Commodity price kill + covenant breach. Bankruptcy.","moat_type":"None - commodity producer","macro":"Oil crash"},
    "CLR_14":   {"pe":28,"sga":0.06,"gm":0.55,"de":2.0,"fcf":-0.03,"roic":0.06,"drop":0.85,"recovered":True,"industry":"Oil & Gas E&P","year":2014,"why":"Bakken shale leader. Dropped hard but low-cost position survived. Harold Hamm founder-led.","moat_type":"Low-cost basin + founder operator","macro":"Oil crash"},
    "RIG_14":   {"pe":8,"sga":0.10,"gm":0.30,"de":2.5,"fcf":0.05,"roic":0.04,"drop":0.90,"recovered":False,"industry":"Offshore Drilling","year":2014,"why":"Transocean. Deepwater drilling rigs became stranded assets when oil dropped. Massive capex with no flexibility.","moat_type":"Asset-heavy (rigs) but inflexible","macro":"Oil crash"},

    # ================================================================
    # RETAIL APOCALYPSE (2015-2020)
    # Macro: E-commerce shift, Amazon effect
    # ================================================================
    "JCP_15":   {"pe":0,"sga":0.35,"gm":0.35,"de":3.0,"fcf":-0.08,"roic":-0.05,"drop":0.99,"recovered":False,"industry":"Department Store","year":2015,"why":"Amazon e-commerce ate department stores. No online moat. Foot traffic collapsed. Bankruptcy 2020.","moat_type":"Real estate (liability not asset)","macro":"E-commerce shift"},
    "M_15":     {"pe":12,"sga":0.30,"gm":0.40,"de":1.5,"fcf":0.06,"roic":0.10,"drop":0.80,"recovered":False,"industry":"Department Store","year":2015,"why":"Macy's. Same Amazon pressure. Real estate partially valuable but retail model broken.","moat_type":"Brand + real estate (both eroding)","macro":"E-commerce shift"},
    "SHLD_15":  {"pe":0,"sga":0.25,"gm":0.25,"de":5.0,"fcf":-0.15,"roic":-0.10,"drop":1.00,"recovered":False,"industry":"Department Store","year":2015,"why":"Sears. Decades of underinvestment. No e-commerce strategy. Bankruptcy 2018.","moat_type":"None remaining","macro":"E-commerce shift"},
    "BBY_12":   {"pe":8,"sga":0.22,"gm":0.24,"de":0.5,"fcf":0.04,"roic":0.12,"drop":0.60,"recovered":True,"industry":"Electronics Retail","year":2012,"why":"Best Buy. 'Showrooming' threat from Amazon. BUT pivoted to services + price match. Survived.","moat_type":"Physical presence + service moat (built during crisis)","macro":"E-commerce shift"},

    # ================================================================
    # CRYPTO WINTER (2018, 2022)
    # ================================================================
    "COIN_22":  {"pe":0,"sga":0.40,"gm":0.80,"de":2.0,"fcf":-0.05,"roic":-0.10,"drop":0.87,"recovered":True,"industry":"Crypto Exchange","year":2022,"why":"FTX collapse + crypto winter. But Coinbase had regulatory moat (licensed exchange). Survived.","moat_type":"Regulatory license + US market position","macro":"Crypto winter, rate hikes"},
    "MSTR_22":  {"pe":0,"sga":0.50,"gm":0.75,"de":1.5,"fcf":-0.02,"roic":-0.05,"drop":0.75,"recovered":True,"industry":"Bitcoin Treasury","year":2022,"why":"MicroStrategy. Bitcoin proxy. Dropped with BTC but thesis was a leveraged BTC bet. Recovered with BTC.","moat_type":"First mover Bitcoin treasury strategy","macro":"Crypto winter"},

    # ================================================================
    # COVID GROWTH BUBBLE (2020-2022)
    # Macro: Zero rates -> Fed hiking cycle, COVID pull-forward
    # ================================================================
    "ZM_21":    {"pe":130,"sga":0.35,"gm":0.75,"de":0.05,"fcf":0.015,"roic":0.12,"drop":0.88,"recovered":False,"industry":"Video Communications","year":2021,"why":"Video calling is a FEATURE. Microsoft Teams bundled it free. Zero switching cost. COVID demand normalized.","moat_type":"None - feature product with zero lock-in","macro":"Rate hikes, COVID normalization"},
    "DOCU_21":  {"pe":195,"sga":0.50,"gm":0.78,"de":1.5,"fcf":0.005,"roic":0.05,"drop":0.82,"recovered":False,"industry":"E-Signature","year":2021,"why":"E-signature is a FEATURE. Adobe Sign, HelloSign, built into every platform. No moat.","moat_type":"None - feature built into larger platforms","macro":"Rate hikes, growth sell-off"},
    "PTON_21":  {"pe":0,"sga":0.55,"gm":0.35,"de":2.0,"fcf":-0.15,"roic":-0.25,"drop":0.97,"recovered":False,"industry":"Connected Fitness","year":2021,"why":"Bike with a screen. Zero lock-in. Any bike + iPad = same thing. COVID demand pull-forward.","moat_type":"None - hardware commodity with content","macro":"Rate hikes, COVID normalization"},
    "HOOD_21":  {"pe":0,"sga":0.65,"gm":0.60,"de":3.0,"fcf":-0.10,"roic":-0.15,"drop":0.92,"recovered":False,"industry":"Retail Brokerage","year":2021,"why":"Trading app is a FEATURE. Every broker has commission-free trading now. PFOF regulatory risk.","moat_type":"None - feature, no switching cost","macro":"Rate hikes, meme stock unwind"},
    "TDOC_21":  {"pe":0,"sga":0.40,"gm":0.65,"de":0.8,"fcf":-0.08,"roic":-0.10,"drop":0.95,"recovered":False,"industry":"Telehealth","year":2021,"why":"Telehealth is a FEATURE built into Epic, Cerner, every healthcare system. Livongo acquisition destroyed value.","moat_type":"None - feature integrated everywhere","macro":"Rate hikes, COVID normalization"},
    "RIVN_21":  {"pe":0,"sga":0.80,"gm":-0.50,"de":1.0,"fcf":-0.20,"roic":-0.40,"drop":0.93,"recovered":False,"industry":"Electric Vehicles","year":2021,"why":"Pre-revenue EV startup. Negative gross margins. No production moat. Cash burn machine.","moat_type":"None - pre-production startup","macro":"Rate hikes, EV bubble burst"},
    "SHOP_21":  {"pe":350,"sga":0.30,"gm":0.55,"de":0.5,"fcf":0.002,"roic":0.03,"drop":0.78,"recovered":True,"industry":"E-Commerce Platform","year":2021,"why":"Dropped 78% but merchant ecosystem + Shopify Payments moat was REAL. Recovered because platform, not feature.","moat_type":"Merchant ecosystem + payments + switching costs","macro":"Rate hikes"},
    "NVDA_21":  {"pe":90,"sga":0.10,"gm":0.65,"de":0.40,"fcf":0.02,"roic":0.20,"drop":0.66,"recovered":True,"industry":"Semiconductors","year":2021,"why":"Crypto mining bust + rate hikes. But CUDA ecosystem moat was DEEP. AI wave made it the most important company.","moat_type":"CUDA ecosystem + GPU architecture monopoly","macro":"Rate hikes, crypto bust"},
    "META_21":  {"pe":24,"sga":0.25,"gm":0.80,"de":0.10,"fcf":0.06,"roic":0.18,"drop":0.75,"recovered":True,"industry":"Social Media","year":2022,"why":"Metaverse spending + Apple ATT + TikTok competition. But ad network + social graph moat survived. Efficiency year saved it.","moat_type":"Social graph network effects + ad network","macro":"Rate hikes, Apple ATT"},
    "TSLA_21":  {"pe":350,"sga":0.10,"gm":0.25,"de":0.30,"fcf":-0.01,"roic":0.05,"drop":0.73,"recovered":True,"industry":"Electric Vehicles","year":2021,"why":"Bubble valuation crashed but manufacturing + Supercharger + brand moat survived. Production scaling is real.","moat_type":"Manufacturing + charging network + brand","macro":"Rate hikes, EV competition"},
    "CRM_21":   {"pe":130,"sga":0.45,"gm":0.73,"de":0.20,"fcf":0.04,"roic":0.06,"drop":0.50,"recovered":True,"industry":"Enterprise CRM","year":2021,"why":"Activist investors forced efficiency. But enterprise CRM switching cost is MASSIVE. Companies don't migrate off Salesforce.","moat_type":"Enterprise switching costs + AppExchange ecosystem","macro":"Rate hikes"},
    "SNAP_21":  {"pe":0,"sga":0.55,"gm":0.55,"de":0.50,"fcf":-0.05,"roic":-0.08,"drop":0.85,"recovered":False,"industry":"Social Media","year":2021,"why":"Disappearing messages was a FEATURE. Instagram Stories cloned it perfectly. Weak ad tech vs META.","moat_type":"Weak - feature cloned by Instagram","macro":"Rate hikes, Apple ATT"},
    "GPRO_15":  {"pe":45,"sga":0.30,"gm":0.40,"de":0.10,"fcf":0.02,"roic":0.05,"drop":0.97,"recovered":False,"industry":"Consumer Hardware","year":2015,"why":"Action camera is a FEATURE. Smartphone cameras got good enough. Zero switching cost. Hardware commodity.","moat_type":"None - hardware feature absorbed by phones","macro":"Smartphone camera improvement"},
    "PINS_21":  {"pe":0,"sga":0.40,"gm":0.75,"de":0.10,"fcf":0.01,"roic":0.02,"drop":0.75,"recovered":False,"industry":"Social Media","year":2021,"why":"Visual bookmarking is a feature. Weak ad monetization vs META/Google. User growth stalled.","moat_type":"Unique content graph (moderate)","macro":"Rate hikes"},
    "DASH_21":  {"pe":0,"sga":0.45,"gm":0.45,"de":1.0,"fcf":-0.05,"roic":-0.08,"drop":0.72,"recovered":True,"industry":"Food Delivery","year":2021,"why":"Dropped but US delivery market share moat (60%+) was real. Network effects in delivery logistics.","moat_type":"Market share + delivery logistics network","macro":"Rate hikes"},
    "ABNB_21":  {"pe":0,"sga":0.30,"gm":0.80,"de":0.50,"fcf":0.02,"roic":0.05,"drop":0.55,"recovered":True,"industry":"Travel Platform","year":2021,"why":"Dropped least of growth stocks. Supply-side moat (hosts) + brand moat. Two-sided marketplace with real network effects.","moat_type":"Two-sided marketplace + supply moat","macro":"Rate hikes"},

    # ================================================================
    # AI DISRUPTION (2023-2025)
    # Macro: AI adoption accelerating, ChatGPT launch Nov 2022
    # ================================================================
    "CHGG_22":  {"pe":28,"sga":0.48,"gm":0.74,"de":0.91,"fcf":0.085,"roic":0.04,"drop":0.97,"recovered":False,"industry":"EdTech","year":2022,"why":"Homework answers is a FEATURE. ChatGPT literally IS the replacement. Management admitted it on earnings call.","moat_type":"None - AI provides same service for free","macro":"AI disruption"},
    "FVRR_22":  {"pe":0,"sga":0.54,"gm":0.83,"de":1.15,"fcf":0.027,"roic":-0.03,"drop":0.73,"recovered":False,"industry":"Freelance Marketplace","year":2022,"why":"AI automates copywriting, design, coding - the exact services sold on Fiverr. Marketplace of humans vs AI.","moat_type":"Marketplace network effects (eroding as AI replaces supply)","macro":"AI disruption"},
    "UPWK_22":  {"pe":0,"sga":0.61,"gm":0.75,"de":0.85,"fcf":0.012,"roic":-0.05,"drop":0.69,"recovered":False,"industry":"Freelance Marketplace","year":2022,"why":"Same as Fiverr. AI replaces the freelancers on the platform.","moat_type":"Same as FVRR - eroding","macro":"AI disruption"},
    "TEP_22":   {"pe":14,"sga":0.20,"gm":0.31,"de":1.45,"fcf":0.068,"roic":0.08,"drop":0.58,"recovered":False,"industry":"BPO/Call Center","year":2023,"why":"AI voice agents replacing human call center agents. Massive headcount reduction trend.","moat_type":"Client relationships + language capabilities (eroding)","macro":"AI disruption"},
}

# ============================================================
# SCORING MODEL
# ============================================================

def score_compression(d):
    pe = d["pe"]
    sga = d["sga"]
    gm = d["gm"]
    de = d["de"]
    fcf = d["fcf"]
    roic = d["roic"]

    eps = 1.0 if pe > 0 else 0.0

    # Path 1: Growth crush
    pe_prem = min(1, max(0, (pe - 12) / 38)) if pe > 0 and eps > 0 else 0
    mf = min(1, (sga * gm) / 0.35)
    growth = pe_prem * 0.55 + mf * 0.45

    # Path 2: Leverage kill
    lev = min(1, de / 5.0)
    cs = 1 - max(0, min(1, (fcf + 0.15) / 0.35))
    leverage = lev * 0.60 + cs * 0.40

    # Path 3: Cash burn
    ne = 1.0 if pe <= 0 or eps <= 0 else 0.0
    br = 1 - max(0, min(1, (fcf + 0.20) / 0.40))
    cd = 1 - max(0, min(1, (roic + 0.4) / 0.6))
    burn = ne * 0.40 + br * 0.35 + cd * 0.25

    comp = max(growth, leverage, burn)

    # Moat score (simplified - uses financials only)
    feature_sig = max(0, min(1, (sga - 0.15) / 0.45)) * max(0, min(1, (gm - 0.30) / 0.50))
    roic_moat = max(0, min(1, (roic + 0.05) / 0.30))
    fcf_dur = max(0, min(1, (fcf + 0.05) / 0.15))
    resil = 1 - min(1, de / 5.0)
    moat = roic_moat * 0.35 + fcf_dur * 0.25 + (1 - feature_sig) * 0.25 + resil * 0.15

    net = comp - moat
    dominant_path = "GROWTH" if growth >= leverage and growth >= burn else ("LEVERAGE" if leverage >= burn else "BURN")

    return {
        "comp": comp, "moat": moat, "net": net,
        "growth": growth, "leverage": leverage, "burn": burn,
        "dominant_path": dominant_path, "pe_prem": pe_prem
    }


# ============================================================
# RUN AND ANALYZE
# ============================================================

gate = 0.35  # threshold for flagging
results = []

for ticker, d in db.items():
    s = score_compression(d)
    flagged = s["net"] > gate
    results.append({
        "ticker": ticker, "flagged": flagged, "recovered": d["recovered"],
        "drop": d["drop"], "industry": d["industry"], "year": d["year"],
        "why": d["why"], "moat_type": d["moat_type"], "macro": d["macro"],
        **s, **d
    })

# Sort by net score
results.sort(key=lambda x: x["net"], reverse=True)

# ============================================================
# PRINT FULL RESULTS
# ============================================================

print("=" * 110)
print("FULL COMPRESSION DATABASE: MODEL RESULTS")
print("=" * 110)
print(f"{'Ticker':12s} {'Net':>6s} {'Comp':>5s} {'Moat':>5s} {'Path':>8s} {'P/E':>6s} {'Drop':>5s} {'Recov':>6s} {'Flag':>5s} Industry")
print("-" * 110)

for r in results:
    flag = "HIT" if r["flagged"] else "miss"
    recov = "YES" if r["recovered"] else "no"
    pe_str = f"{r['pe']:.0f}x" if r["pe"] > 0 else "N/E"
    print(f"{r['ticker']:12s} {r['net']:+.3f} {r['comp']:.3f} {r['moat']:.3f} {r['dominant_path']:>8s} {pe_str:>6s} {r['drop']:.0%} {recov:>6s} {flag:>5s} {r['industry']}")

# ============================================================
# ANALYSIS: TRUE POSITIVES, FALSE POSITIVES, MISSES
# ============================================================

true_pos = [r for r in results if r["flagged"] and not r["recovered"]]    # Flagged + stayed dead = CORRECT
false_pos = [r for r in results if r["flagged"] and r["recovered"]]        # Flagged + recovered = WRONG
true_neg = [r for r in results if not r["flagged"] and r["recovered"]]     # Not flagged + recovered = CORRECT
false_neg = [r for r in results if not r["flagged"] and not r["recovered"]] # Not flagged + stayed dead = MISSED

print(f"\n{'='*70}")
print("CONFUSION MATRIX")
print(f"{'='*70}")
print(f"True Positives  (flagged, stayed dead):    {len(true_pos):3d}  CORRECT SHORT")
print(f"False Positives (flagged, recovered):      {len(false_pos):3d}  WRONG - would have lost")
print(f"True Negatives  (not flagged, recovered):  {len(true_neg):3d}  CORRECT SKIP")
print(f"False Negatives (not flagged, stayed dead): {len(false_neg):3d}  MISSED OPPORTUNITY")
print()

total = len(results)
accuracy = (len(true_pos) + len(true_neg)) / total
precision = len(true_pos) / (len(true_pos) + len(false_pos)) if (len(true_pos) + len(false_pos)) > 0 else 0
recall = len(true_pos) / (len(true_pos) + len(false_neg)) if (len(true_pos) + len(false_neg)) > 0 else 0

print(f"Accuracy:  {accuracy:.0%} (correct calls / total)")
print(f"Precision: {precision:.0%} (of flagged, how many were actually dead)")
print(f"Recall:    {recall:.0%} (of dead companies, how many did we flag)")

# ============================================================
# DEEP DIVE: FALSE POSITIVES (flagged but recovered)
# These are the ones that would have COST US MONEY
# ============================================================

print(f"\n{'='*70}")
print("FALSE POSITIVES: FLAGGED BUT RECOVERED (would have lost money)")
print(f"{'='*70}")
for r in false_pos:
    print(f"\n  {r['ticker']} ({r['industry']}, {r['year']})")
    print(f"  Score: {r['net']:+.3f} | Path: {r['dominant_path']} | Drop: {r['drop']:.0%} then RECOVERED")
    print(f"  Why it dropped: {r['why']}")
    print(f"  Why it recovered (MOAT): {r['moat_type']}")
    print(f"  MODEL FAILURE: {_analyze_failure(r)}")

# ============================================================
# DEEP DIVE: FALSE NEGATIVES (missed but stayed dead)
# These are the ones we LEFT MONEY ON THE TABLE
# ============================================================

print(f"\n{'='*70}")
print("FALSE NEGATIVES: MISSED BUT STAYED DEAD (left money on table)")
print(f"{'='*70}")
for r in false_neg:
    print(f"\n  {r['ticker']} ({r['industry']}, {r['year']})")
    print(f"  Score: {r['net']:+.3f} | Path: {r['dominant_path']} | Drop: {r['drop']:.0%}")
    print(f"  Why it died: {r['why']}")
    print(f"  Why model missed: {_analyze_miss(r)}")

def _analyze_failure(r):
    """Why did the model flag a company that recovered?"""
    reasons = []
    if r["pe"] > 100:
        reasons.append(f"P/E was extreme ({r['pe']}x) which usually means compression, but moat justified it")
    if r["pe"] == 0:
        reasons.append("No earnings (P/E=0) triggered burn path, but company was pre-profit by choice")
    if r["de"] > 3:
        reasons.append(f"High leverage ({r['de']:.1f}x D/E) triggered leverage path, but company managed through")
    if not reasons:
        reasons.append("General high score from multiple moderate signals")
    reasons.append(f"MOAT NOT CAPTURED: {r['moat_type']}")
    return " | ".join(reasons)

def _analyze_miss(r):
    """Why did the model miss a company that died?"""
    reasons = []
    if r["pe"] > 0 and r["pe"] < 15:
        reasons.append(f"Low P/E ({r['pe']}x) meant no growth premium to crush")
    if r["pe"] == 0:
        reasons.append("No earnings but burn path score wasn't high enough")
    if r["de"] < 2:
        reasons.append(f"Low leverage ({r['de']:.1f}x) so leverage path didn't trigger")
    if r["roic"] > 0:
        reasons.append(f"Positive ROIC ({r['roic']:.0%}) made moat score too high")
    if not reasons:
        reasons.append("Moderate scores across all paths - no single path strong enough")
    return " | ".join(reasons)

# Re-run the analysis functions that were defined after first use
print(f"\n{'='*70}")
print("FALSE POSITIVES (DETAILED)")
print(f"{'='*70}")
for r in false_pos:
    print(f"\n  {r['ticker']} ({r['industry']}, {r['year']})")
    print(f"  Score: {r['net']:+.3f} | Drop: {r['drop']:.0%} then RECOVERED")
    print(f"  Moat that saved it: {r['moat_type']}")

print(f"\n{'='*70}")
print("FALSE NEGATIVES (DETAILED)")
print(f"{'='*70}")
for r in false_neg:
    print(f"\n  {r['ticker']} ({r['industry']}, {r['year']})")
    print(f"  Score: {r['net']:+.3f} | Drop: {r['drop']:.0%}")
    print(f"  Why it died: {r['why']}")
    pe_issue = f"P/E only {r['pe']}x (no premium)" if r["pe"] < 15 and r["pe"] > 0 else ""
    de_issue = f"D/E only {r['de']:.1f}x (leverage not extreme)" if r["de"] < 2 else ""
    print(f"  Why missed: {pe_issue} {de_issue}")
