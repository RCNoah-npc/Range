/**
 * Noah's Compression Risk Widget
 * Displays the Multiple Compression Signal Detector results.
 *
 * Reads from: agent_drops/output/compression_dashboard.json
 * Run the Python scorer first: python -m src.rangers.noah.run
 */
import { Widget } from '../../shared/widget-base.js';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_PATH = join(__dirname, '..', '..', '..', 'agent_drops', 'output', 'compression_dashboard.json');

function loadData() {
  try {
    const raw = readFileSync(DATA_PATH, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function riskColor(label) {
  const colors = {
    Critical: '#ef4444',
    High: '#f97316',
    Elevated: '#eab308',
    Moderate: '#22c55e',
    Low: '#3b82f6',
  };
  return colors[label] || '#6b7280';
}

function riskBar(score, maxWidth = 200) {
  const width = Math.round((score / 100) * maxWidth);
  const color = score >= 75 ? '#ef4444' : score >= 60 ? '#f97316' : score >= 40 ? '#eab308' : '#22c55e';
  return `<div style="background:#1f2937;border-radius:4px;width:${maxWidth}px;height:12px;display:inline-block;vertical-align:middle">
    <div style="background:${color};border-radius:4px;width:${width}px;height:12px"></div>
  </div>`;
}

export class CompressionWidget extends Widget {
  constructor() {
    super({
      id: 'noah:compression',
      name: 'Multiple Compression Detector',
      author: 'noah',
      description: 'Scores stocks on compression risk using macro, valuation, momentum, and AI disruption signals',
    });
  }

  render() {
    const data = loadData();

    if (!data) {
      return `
        <div class="widget" style="padding:20px;font-family:monospace;color:#9ca3af">
          <h3 style="color:#f59e0b">⚠️ No Data</h3>
          <p>Run the scorer first:</p>
          <code style="background:#1f2937;padding:8px;border-radius:4px;display:block;margin:8px 0">
            pip install pandas numpy<br>
            python agent_drops/collect_all_market_data.py<br>
            python -m src.rangers.noah.run
          </code>
        </div>`;
    }

    const { market_score, stock_rankings, summary } = data;
    const top10 = stock_rankings.slice(0, 10);
    const bottom5 = stock_rankings.slice(-5).reverse();

    return `
      <div class="widget" style="padding:20px;font-family:system-ui,-apple-system,sans-serif;color:#e5e7eb;max-width:900px">
        
        <!-- Market Score Header -->
        <div style="background:linear-gradient(135deg,#1e1b4b,#312e81);border-radius:12px;padding:24px;margin-bottom:20px">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <h2 style="margin:0;color:#c7d2fe;font-size:14px;text-transform:uppercase;letter-spacing:1px">
                Market Compression Risk
              </h2>
              <div style="font-size:48px;font-weight:800;color:${riskColor(market_score.label)};margin:8px 0">
                ${market_score.compression_risk}
                <span style="font-size:18px;color:#9ca3af">/100</span>
              </div>
              <span style="background:${riskColor(market_score.label)}22;color:${riskColor(market_score.label)};padding:4px 12px;border-radius:20px;font-size:13px;font-weight:600">
                ${market_score.label}
              </span>
            </div>
            <div style="text-align:right;font-size:13px;color:#9ca3af">
              <div>Macro: ${market_score.macro_score}</div>
              <div>Valuation: ${market_score.median_valuation_score}</div>
              <div style="margin-top:8px;font-size:11px">
                ${new Date(data.generated_at).toLocaleString()}
              </div>
            </div>
          </div>
          <div style="margin-top:12px;font-size:13px;color:#a5b4fc">
            ${market_score.top_drivers.map(d => `• ${d}`).join('<br>')}
          </div>
        </div>

        <!-- Distribution Summary -->
        <div style="display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap">
          ${[
            ['Critical', summary.critical, '#ef4444'],
            ['High', summary.high, '#f97316'],
            ['Elevated', summary.elevated, '#eab308'],
            ['Moderate', summary.moderate, '#22c55e'],
            ['Low', summary.low, '#3b82f6'],
          ].map(([label, count, color]) => `
            <div style="background:${color}15;border:1px solid ${color}40;border-radius:8px;padding:8px 16px;text-align:center;flex:1;min-width:80px">
              <div style="font-size:20px;font-weight:700;color:${color}">${count}</div>
              <div style="font-size:11px;color:#9ca3af">${label}</div>
            </div>
          `).join('')}
        </div>

        <!-- Top 10 Most Vulnerable -->
        <h3 style="color:#fbbf24;font-size:14px;margin:16px 0 8px">🔥 Top 10 Compression Candidates</h3>
        <table style="width:100%;border-collapse:collapse;font-size:13px">
          <tr style="color:#6b7280;font-size:11px;text-transform:uppercase">
            <th style="text-align:left;padding:6px">Ticker</th>
            <th style="text-align:right;padding:6px">Score</th>
            <th style="padding:6px">Risk</th>
            <th style="text-align:right;padding:6px">P/E</th>
            <th style="text-align:right;padding:6px">EV/EBITDA</th>
            <th style="text-align:left;padding:6px">Top Factor</th>
          </tr>
          ${top10.map((r, i) => `
            <tr style="border-top:1px solid #374151;${i === 0 ? 'background:#7f1d1d22' : ''}">
              <td style="padding:6px;font-weight:600;color:#f3f4f6">${r.ticker}</td>
              <td style="text-align:right;padding:6px;color:${riskColor(r.label)};font-weight:700">${r.compression_risk_score}</td>
              <td style="padding:6px">
                <span style="background:${riskColor(r.label)}22;color:${riskColor(r.label)};padding:2px 8px;border-radius:10px;font-size:11px">${r.label}</span>
              </td>
              <td style="text-align:right;padding:6px">${r.current_pe ? r.current_pe.toFixed(1) : '—'}</td>
              <td style="text-align:right;padding:6px">${r.ev_ebitda ? r.ev_ebitda.toFixed(1) : '—'}</td>
              <td style="padding:6px;font-size:11px;color:#9ca3af">${(r.risk_factors || [])[0] || ''}</td>
            </tr>
          `).join('')}
        </table>

        <!-- Bottom 5 Safest -->
        <h3 style="color:#34d399;font-size:14px;margin:20px 0 8px">🛡️ Lowest Compression Risk</h3>
        <table style="width:100%;border-collapse:collapse;font-size:13px">
          ${bottom5.map(r => `
            <tr style="border-top:1px solid #374151">
              <td style="padding:6px;font-weight:600;color:#f3f4f6;width:80px">${r.ticker}</td>
              <td style="text-align:right;padding:6px;color:${riskColor(r.label)};font-weight:700;width:60px">${r.compression_risk_score}</td>
              <td style="padding:6px">
                <span style="background:${riskColor(r.label)}22;color:${riskColor(r.label)};padding:2px 8px;border-radius:10px;font-size:11px">${r.label}</span>
              </td>
              <td style="padding:6px;font-size:11px;color:#9ca3af">${r.current_pe ? `P/E: ${r.current_pe.toFixed(1)}` : ''}</td>
            </tr>
          `).join('')}
        </table>

        <div style="margin-top:16px;font-size:11px;color:#4b5563;text-align:right">
          Scored ${summary.total_scored} stocks • Based on GGM, Perez framework, HALO methodology
        </div>
      </div>`;
  }

  async refresh() {
    // Re-read the JSON on refresh
    this.setState({ lastRefresh: Date.now() });
  }
}
