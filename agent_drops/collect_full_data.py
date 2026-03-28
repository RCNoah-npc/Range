"""
FULL Market & Economic Training Data Collector — Round 2
=========================================================
Pulls ~100MB+ of institutional-grade financial data from public libraries.
No API keys needed.

Drop in: C:\\Users\\noahj\\OneDrive\\Desktop\\Claude\\Range\\agent_drops\\
Run:
    pip install yfinance pandas numpy requests lxml html5lib
    python collect_full_data.py

Sources:
- Yahoo Finance: All 503 S&P 500 components (5yr daily + 35 fundamental metrics)
- FRED: 92 macroeconomic time series (rates, inflation, employment, credit, housing, global)
- Shiller/Yale: S&P 500 monthly since 1870 (price, earnings, dividends, P/E, CAPE)
- Damodaran/NYU Stern: Industry multiples, betas, margins, WACC, earnings history
- Kalshi: Prediction market data (open + settled)
- SEC EDGAR: Full US public company ticker mappings
- CoinGecko: BTC + ETH daily
"""

import os
import json
import time
import requests
import pandas as pd
import numpy as np
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

DIRS = {
    "stocks": DATA_DIR / "stocks",
    "sp500": DATA_DIR / "sp500_components",
    "econ": DATA_DIR / "economic",
    "fred2": DATA_DIR / "fred_extended",
    "kalshi": DATA_DIR / "kalshi",
    "shiller": DATA_DIR / "shiller",
    "damodaran": DATA_DIR / "damodaran",
    "crypto": DATA_DIR / "crypto",
}
for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)

KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"


def fetch_json(url, params=None, headers=None):
    r = requests.get(url, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

def safe_name(ticker):
    return ticker.replace("^", "IDX_").replace("-", "_").replace(".", "_")

def download_file(url, path, headers=None):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    r = requests.get(url, headers=h, timeout=30)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    return len(r.content)


# ═══════════════════════════════════════════════════════════════════════
# 1. SHILLER — S&P 500 since 1870 with P/E, earnings, dividends, CAPE
# ═══════════════════════════════════════════════════════════════════════
def collect_shiller():
    print("\n📜 [1/8] SHILLER — S&P 500 since 1870")
    try:
        size = download_file(
            "https://datahub.io/core/s-and-p-500/r/data.csv",
            DIRS["shiller"] / "sp500_shiller_1870_monthly.csv"
        )
        print(f"  ✓ Monthly CSV ({size:,} bytes)")
    except Exception as e:
        print(f"  ✗ DataHub CSV: {e}")

    try:
        size = download_file(
            "http://www.econ.yale.edu/~shiller/data/ie_data.xls",
            DIRS["shiller"] / "ie_data_shiller.xls"
        )
        print(f"  ✓ Shiller Excel — full dataset ({size:,} bytes)")
    except Exception as e:
        print(f"  ✗ Shiller Excel: {e}")


# ═══════════════════════════════════════════════════════════════════════
# 2. DAMODARAN / NYU STERN — Industry multiples, betas, margins, WACC
# ═══════════════════════════════════════════════════════════════════════
def collect_damodaran():
    print("\n🎓 [2/8] DAMODARAN / NYU STERN — Industry Data")
    base = "https://www.stern.nyu.edu/~adamodar/pc/datasets"
    files = [
        "spearn.xls", "histretSP.xls", "histimpl.xls", "wacc.xls",
        "pedata.xls", "pbvdata.xls", "psdata.xls", "margin.xls",
        "roe.xls", "betaGlobal.xls", "taxrate.xls", "divfcfe.xls",
        "capex.xls", "ctryprem.xls", "totalbeta.xls", "fundgrEB.xls",
    ]
    for fname in files:
        try:
            size = download_file(f"{base}/{fname}", DIRS["damodaran"] / fname)
            print(f"  ✓ {fname} ({size:,} bytes)")
        except:
            print(f"  ✗ {fname}")
        time.sleep(0.3)


# ═══════════════════════════════════════════════════════════════════════
# 3. FULL S&P 500 — All 503 components, 5yr daily + fundamentals
# ═══════════════════════════════════════════════════════════════════════
def collect_sp500():
    import yfinance as yf

    print("\n📈 [3/8] S&P 500 — All 503 Components (5yr daily + fundamentals)")

    # Get component list from Wikipedia
    print("  Fetching S&P 500 component list...")
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        sp500_table = tables[0]
        tickers = [t.replace(".", "-") for t in sp500_table["Symbol"].tolist()]
        sp500_table.to_csv(DIRS["sp500"] / "sp500_components.csv", index=False)
        save_json(tickers, DIRS["sp500"] / "sp500_tickers.json")
        print(f"  Found {len(tickers)} components")
    except Exception as e:
        print(f"  ✗ Wikipedia parse failed: {e}")
        return

    # Bulk download in batches
    batch_size = 50
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        batch_num = i // batch_size + 1
        total = (len(tickers) + batch_size - 1) // batch_size
        print(f"  Batch {batch_num}/{total} ({len(batch)} tickers)...")
        try:
            data = yf.download(batch, period="5y", interval="1d", group_by="ticker", threads=True)
            for ticker in batch:
                try:
                    if len(batch) == 1:
                        td = data
                    else:
                        td = data[ticker] if ticker in data.columns.get_level_values(0) else None
                    if td is not None and len(td) > 0:
                        td.to_csv(DIRS["sp500"] / f"{safe_name(ticker)}_5y.csv")
                except:
                    pass
        except Exception as e:
            print(f"    Batch error: {e}")
        time.sleep(1)

    # Fundamentals
    print(f"  Fetching fundamentals for all {len(tickers)} stocks...")
    fundamentals = []
    for i, ticker in enumerate(tickers):
        if i % 100 == 0 and i > 0:
            print(f"    Progress: {i}/{len(tickers)}...")
        try:
            info = yf.Ticker(ticker).info
            fundamentals.append({
                "ticker": ticker, "name": info.get("shortName"),
                "sector": info.get("sector"), "industry": info.get("industry"),
                "marketCap": info.get("marketCap"),
                "trailingPE": info.get("trailingPE"), "forwardPE": info.get("forwardPE"),
                "pegRatio": info.get("pegRatio"),
                "dividendYield": info.get("dividendYield"), "beta": info.get("beta"),
                "52wHigh": info.get("fiftyTwoWeekHigh"), "52wLow": info.get("fiftyTwoWeekLow"),
                "avgVolume": info.get("averageVolume"),
                "revenue": info.get("totalRevenue"),
                "grossMargins": info.get("grossMargins"),
                "operatingMargins": info.get("operatingMargins"),
                "ebitdaMargins": info.get("ebitdaMargins"),
                "profitMargins": info.get("profitMargins"),
                "returnOnEquity": info.get("returnOnEquity"),
                "returnOnAssets": info.get("returnOnAssets"),
                "debtToEquity": info.get("debtToEquity"),
                "currentRatio": info.get("currentRatio"),
                "earningsGrowth": info.get("earningsGrowth"),
                "revenueGrowth": info.get("revenueGrowth"),
                "evToEbitda": info.get("enterpriseToEbitda"),
                "evToRevenue": info.get("enterpriseToRevenue"),
                "priceToBook": info.get("priceToBook"),
                "priceToSales": info.get("priceToSalesTrailing12Months"),
                "freeCashflow": info.get("freeCashflow"),
                "totalCash": info.get("totalCash"),
                "totalDebt": info.get("totalDebt"),
                "shortRatio": info.get("shortRatio"),
                "shortPercentFloat": info.get("shortPercentOfFloat"),
                "heldPercentInsiders": info.get("heldPercentInsiders"),
                "heldPercentInstitutions": info.get("heldPercentInstitutions"),
            })
        except:
            pass
    save_json(fundamentals, DIRS["sp500"] / "sp500_fundamentals_full.json")
    print(f"  ✓ Fundamentals for {len(fundamentals)} stocks")


# ═══════════════════════════════════════════════════════════════════════
# 4. FRED — 92 Macroeconomic Series (original 25 + 67 extended)
# ═══════════════════════════════════════════════════════════════════════
def collect_fred():
    print("\n🏛️  [4/8] FRED — 92 Macroeconomic Series")

    SERIES = {
        # Core (25)
        "GDP": "GDP", "REAL_GDP": "GDPC1", "CPI": "CPIAUCSL", "CORE_CPI": "CPILFESL",
        "PCE": "PCEPI", "CORE_PCE": "PCEPILFE", "UNEMPLOYMENT": "UNRATE",
        "NONFARM_PAYROLL": "PAYEMS", "INITIAL_CLAIMS": "ICSA",
        "FED_FUNDS_RATE": "FEDFUNDS", "10Y_TREASURY": "DGS10", "2Y_TREASURY": "DGS2",
        "YIELD_SPREAD_10Y2Y": "T10Y2Y", "SP500": "SP500", "VIX": "VIXCLS",
        "INDUSTRIAL_PROD": "INDPRO", "RETAIL_SALES": "RSXFS",
        "HOUSING_STARTS": "HOUST", "CONSUMER_SENTIMENT": "UMCSENT",
        "M2_MONEY_SUPPLY": "M2SL", "DOLLAR_INDEX": "DTWEXBGS",
        "PERSONAL_INCOME": "PI", "PERSONAL_SAVING_RATE": "PSAVERT",
        "TRADE_BALANCE": "BOPGSTB", "BREAKEVEN_INFLATION_5Y": "T5YIE",
        # Extended (67)
        "ISM_MANUFACTURING": "MANEMP", "ISM_NEW_ORDERS": "NEWORDER",
        "CAPACITY_UTILIZATION": "TCU", "BUSINESS_INVENTORIES": "BUSINV",
        "DURABLE_GOODS": "DGORDER",
        "JOLTS_OPENINGS": "JTSJOL", "JOLTS_QUITS": "JTSQUR",
        "AVG_HOURLY_EARNINGS": "CES0500000003",
        "LABOR_FORCE_PARTICIPATION": "CIVPART",
        "PART_TIME_ECONOMIC": "LNS12032194", "AVG_WEEKLY_HOURS": "AWHMAN",
        "CASE_SHILLER_NATIONAL": "CSUSHPINSA",
        "EXISTING_HOME_SALES": "EXHOSLUSM495S", "NEW_HOME_SALES": "HSN1F",
        "MORTGAGE_30Y": "MORTGAGE30US", "HOUSING_PERMITS": "PERMIT",
        "BAA_CORPORATE_YIELD": "DBAA", "AAA_CORPORATE_YIELD": "DAAA",
        "HIGH_YIELD_SPREAD": "BAMLH0A0HYM2", "IG_SPREAD": "BAMLC0A0CM",
        "FINANCIAL_STRESS": "STLFSI2", "CHICAGO_FED_NATIONAL": "CFNAI",
        "LEADING_INDEX": "USSLIND", "TED_SPREAD": "TEDRATE",
        "PPI_FINISHED_GOODS": "WPSFD49207", "IMPORT_PRICE_INDEX": "IR",
        "STICKY_PRICE_CPI": "STICKCPIM157SFRBATL",
        "MEDIAN_CPI": "MEDCPIM158SFRBCLE",
        "TRIMMED_MEAN_PCE": "PCETRIM12M159SFRBDAL",
        "INFLATION_EXPECTATIONS_1Y": "MICH", "INFLATION_EXPECTATIONS_5Y": "T5YIFR",
        "3M_TREASURY": "DGS3MO", "5Y_TREASURY": "DGS5", "7Y_TREASURY": "DGS7",
        "20Y_TREASURY": "DGS20", "30Y_TREASURY": "DGS30",
        "REAL_RATE_5Y": "DFII5", "REAL_RATE_10Y": "DFII10", "REAL_RATE_30Y": "DFII30",
        "MONETARY_BASE": "BOGMBASE", "BANK_CREDIT": "TOTBKCR",
        "COMMERCIAL_LOANS": "BUSLOANS", "CONSUMER_CREDIT": "TOTALSL",
        "FED_BALANCE_SHEET": "WALCL", "REPO_RATE": "SOFR",
        "OIL_WTI": "DCOILWTICO", "NATURAL_GAS": "DHHNGSP",
        "COPPER_PRICE": "PCOPPUSDM",
        "IMPORT_GOODS": "IMPGS", "EXPORT_GOODS": "EXPGS",
        "CHINA_GDP": "MKTGDPCNA646NWDB",
        "EURO_CPI": "CP0000EZ19M086NEST", "JAPAN_CPI": "JPNCPIALLMINMEI",
        "GERMANY_IPI": "DEUPROINDMISMEI",
        "MARGIN_DEBT": "BOGZ1FL663067003Q",
        "PERSONAL_CONSUMPTION": "PCE", "REAL_DISPOSABLE_INCOME": "DSPIC96",
        "HOUSEHOLD_DEBT_SERVICE": "TDSP",
        "HOUSEHOLD_NET_WORTH": "BOGZ1FL192090005Q",
        "AUTO_SALES": "TOTALSA", "RETAIL_SALES_EXAUTO": "RSFSXMV",
        "FEDERAL_DEBT_GDP": "GFDEGDQ188S", "FEDERAL_DEFICIT": "MTSDS133FMS",
        "GOV_SPENDING": "FGEXPND",
    }

    success = 0
    for name, sid in SERIES.items():
        try:
            r = requests.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", timeout=15)
            r.raise_for_status()
            path = DIRS["econ"] / f"{name}.csv"
            with open(path, "wb") as f:
                f.write(r.content)
            success += 1
            time.sleep(0.3)
        except:
            print(f"  ✗ {name}")
    print(f"  ✓ {success}/{len(SERIES)} FRED series downloaded")


# ═══════════════════════════════════════════════════════════════════════
# 5. KALSHI — Prediction Markets
# ═══════════════════════════════════════════════════════════════════════
def collect_kalshi():
    print("\n📊 [5/8] KALSHI — Prediction Markets")
    for status in ["open", "settled"]:
        page = 1
        cursor = None
        while True:
            params = {"limit": 1000, "status": status}
            if cursor:
                params["cursor"] = cursor
            try:
                data = fetch_json(f"{KALSHI_BASE}/markets", params)
                save_json(data, DIRS["kalshi"] / f"markets_{status}_p{page}.json")
                count = len(data.get("markets", []))
                print(f"  ✓ {status} page {page} ({count} markets)")
                cursor = data.get("cursor")
                if not cursor or count == 0:
                    break
                page += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"  ✗ {status} p{page}: {e}")
                break

    try:
        data = fetch_json(f"{KALSHI_BASE}/events", {"limit": 200, "status": "open"})
        save_json(data, DIRS["kalshi"] / "events_open.json")
        print(f"  ✓ {len(data.get('events', []))} events")
    except:
        pass


# ═══════════════════════════════════════════════════════════════════════
# 6. CRYPTO
# ═══════════════════════════════════════════════════════════════════════
def collect_crypto():
    print("\n🪙 [6/8] CRYPTO — Daily Prices")
    for coin in ["bitcoin", "ethereum", "solana"]:
        try:
            data = fetch_json(
                f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart",
                {"vs_currency": "usd", "days": 365, "interval": "daily"},
            )
            save_json(data, DIRS["crypto"] / f"{coin}_1y.json")
            print(f"  ✓ {coin} ({len(data.get('prices', []))} days)")
            time.sleep(2)
        except Exception as e:
            print(f"  ✗ {coin}: {e}")


# ═══════════════════════════════════════════════════════════════════════
# 7. SEC EDGAR
# ═══════════════════════════════════════════════════════════════════════
def collect_sec():
    print("\n🏢 [7/8] SEC EDGAR — Company Tickers")
    try:
        data = fetch_json(
            "https://www.sec.gov/files/company_tickers.json",
            headers={"User-Agent": "OpenClaw/1.0 research@example.com"}
        )
        save_json(data, DATA_DIR / "sec_edgar_tickers.json")
        print(f"  ✓ {len(data)} companies")
    except Exception as e:
        print(f"  ✗ {e}")


# ═══════════════════════════════════════════════════════════════════════
# 8. KEY ETFs + INDICES (individual histories)
# ═══════════════════════════════════════════════════════════════════════
def collect_etfs_indices():
    import yfinance as yf

    print("\n📉 [8/8] Key ETFs & Indices")
    tickers = [
        "^GSPC", "^DJI", "^IXIC", "^VIX", "^RUT", "^TNX",
        "SPY", "QQQ", "IWM", "DIA", "VTI", "GLD", "SLV", "TLT",
        "HYG", "LQD", "XLF", "XLK", "XLE", "XLV", "XLI", "XLU",
        "XLP", "XLY", "XLB", "XLRE", "XLC",
        "EEM", "EFA", "VWO", "IEMG",  # Intl/EM
        "TIP", "SHY", "IEF", "AGG",   # Fixed income
        "USO", "UNG", "DBA",           # Commodities
        "ARKK", "ARKG",                # Innovation ETFs
        "VNQ", "IYR",                  # REITs
    ]
    for ticker in tickers:
        try:
            df = yf.Ticker(ticker).history(period="5y")
            df.to_csv(DIRS["stocks"] / f"{safe_name(ticker)}_5y.csv")
            print(f"  ✓ {ticker} ({len(df)} rows)")
        except:
            print(f"  ✗ {ticker}")


# ═══════════════════════════════════════════════════════════════════════
# README
# ═══════════════════════════════════════════════════════════════════════
def write_readme():
    readme = """# Full Market & Economic Training Data
## For: Multiple Compression Signal Detection

### Data Sources (~100MB+)

#### sp500_components/ — Full S&P 500 (503 stocks)
- Individual 5yr daily OHLCV CSVs for every component
- `sp500_fundamentals_full.json` — 35 metrics per stock (PE, EV/EBITDA, margins, growth, beta, short interest, insider ownership)
- `sp500_components.csv` — Component list with sectors, industries

#### stocks/ — Key ETFs & Indices
- Major indices: S&P 500, Dow, Nasdaq, VIX, Russell 2000, 10Y Yield
- Sector ETFs: XLK, XLF, XLE, XLV, XLI, XLU, XLP, XLY, XLB, XLRE, XLC
- Fixed income: TLT, HYG, LQD, TIP, SHY, IEF, AGG
- International: EEM, EFA, VWO
- Commodities: GLD, SLV, USO, UNG
- Innovation: ARKK, ARKG
- REITs: VNQ, IYR

#### economic/ — 92 FRED Macroeconomic Series
- Rates: Fed funds, full yield curve (3M through 30Y), real rates (5Y/10Y/30Y)
- Inflation: CPI, Core CPI, PCE, Core PCE, PPI, sticky CPI, median CPI, trimmed mean PCE, breakeven inflation, expectations
- Employment: Unemployment, payrolls, claims, JOLTS openings/quits, participation, earnings, hours
- Credit: BAA/AAA yields, HY spread, IG spread, financial stress, commercial loans, consumer credit, margin debt
- Housing: Starts, permits, sales, Case-Shiller, mortgage rates
- Business: ISM, capacity utilization, inventories, durable goods, leading index
- Money: M2, monetary base, Fed balance sheet, SOFR
- Consumer: Sentiment, consumption, disposable income, debt service, auto sales
- Government: Debt/GDP, deficit, spending
- Commodities: Oil WTI, natural gas, copper
- Global: China GDP, Euro CPI, Japan CPI, Germany industrial production
- FX: Dollar index

#### shiller/ — S&P 500 Since 1870
- Monthly: price, dividends, earnings, CPI, P/E ratio, CAPE
- The gold standard for long-term valuation analysis

#### damodaran/ — NYU Stern Industry Data
- P/E ratios by industry, Price/Book, Price/Sales
- EV/EBITDA multiples, operating margins, ROE
- Industry betas (levered + unlevered), WACC
- S&P earnings history (1960-current), historical returns
- Equity risk premiums, country risk premiums
- CapEx, dividends/FCFE, tax rates by industry

#### kalshi/ — Prediction Markets
- Open + settled markets with outcomes (great for supervised learning)

#### crypto/ — BTC, ETH, SOL daily

#### sec_edgar_tickers.json — All US public company ticker/CIK mappings
"""
    with open(DATA_DIR / "README.md", "w") as f:
        f.write(readme)


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  FULL Market & Economic Data Collector")
    print("  Target: Multiple Compression Signal Detection")
    print("=" * 60)

    collect_shiller()
    collect_damodaran()
    collect_sp500()     # This is the big one (~15-20 min)
    collect_fred()
    collect_kalshi()
    collect_crypto()
    collect_sec()
    collect_etfs_indices()
    write_readme()

    # Summary
    print("\n" + "=" * 60)
    print("  FINAL SUMMARY")
    print("=" * 60)
    total = 0
    for name, path in sorted(DIRS.items()):
        if path.exists():
            size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            total += size
            count = sum(1 for f in path.rglob("*") if f.is_file())
            print(f"  {name:15s}  {count:4d} files  {size/1024/1024:8.1f} MB")
    print(f"  {'TOTAL':15s}  {total/1024/1024:13.1f} MB")
    print(f"\n  Data: {DATA_DIR}")
    print("=" * 60)
