import React, { useState } from 'react';
import { Award, CheckCircle2, XCircle, MinusCircle, ShieldAlert, ChevronDown, ChevronUp } from 'lucide-react';

const tagFor = (v = '') =>
  v === 'approve' ? 'tag-success' : v === 'approve_with_conditions' ? 'tag-warning' : v === 'refuse' ? 'tag-danger' : 'tag-info';
const label = (v = '') => v.replace(/_/g, ' ');
const HOLD = ['ask', 'escalate'];

function Mark({ got, expected }) {
  if (got === expected) return <CheckCircle2 size={14} style={{ color: 'var(--success)' }} aria-label="agrees" />;
  if (HOLD.includes(got) && HOLD.includes(expected)) return <MinusCircle size={14} style={{ color: 'var(--warning)' }} aria-label="same call: both hold" />;
  return <XCircle size={14} style={{ color: 'var(--danger)' }} aria-label="disagrees" />;
}

function ScoreCard({ title, subtitle, s, accent }) {
  if (!s) return null;
  return (
    <div style={{ flex: '1 1 240px', border: `2px solid ${accent}`, borderRadius: 'var(--radius-md)', padding: 'var(--space-4) var(--space-5)', background: 'var(--bg-inset)' }}>
      <div style={{ fontSize: 'var(--text-xs)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700, color: accent }}>{title}</div>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-2)' }}>{subtitle}</div>
      <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 800, lineHeight: 1.1, color: 'var(--text-primary)' }}>
        {s.all.lenient} / {s.all.cases}
      </div>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginTop: 'var(--space-1)', display: 'grid', gap: '0.15rem' }}>
        <span>{s.all.exact} / {s.all.cases} exact verdict</span>
        <span>Original 10: {s.original_10.lenient} · Hard 5: <strong>{s.hard_5.lenient}</strong></span>
        <span style={{ color: s.unsafe_approvals.length ? 'var(--danger)' : 'var(--success)', fontWeight: 600 }}>
          Unsafe approvals: {s.unsafe_approvals.length}
        </span>
        <span>Over-cautious: {s.over_cautious.length} · Citation recall {Math.round(s.citation_recall * 100)}%</span>
      </div>
    </div>
  );
}

export default function BacktestDashboard({ backtestData, pack, senior }) {
  const first = (senior?.name || 'Meera Nair').split(' ')[0];
  const [open, setOpen] = useState(null);

  if (!backtestData || !backtestData.cases) {
    return (
      <div className="glass-card" style={{ padding: 'var(--space-7)' }}>
        <h2 style={{ fontSize: 'var(--text-xl)' }}>Back-test</h2>
        <p style={{ color: 'var(--text-secondary)' }}>No saved results yet. Run <code>python -m agents.backtest</code>.</p>
      </div>
    );
  }

  const { scores, cases, cost, model, run_at } = backtestData;
  const g = scores.gemini;
  const r = scores.rules;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      <div className="glass-card" style={{ padding: 'var(--space-6)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-1)' }}>
          <Award size={22} style={{ color: 'var(--primary-color)' }} />
          <h2 style={{ fontSize: 'var(--text-xl)', color: 'var(--text-primary)' }}>Blind back-test: {cases.length} decisions {first} already made</h2>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)', maxWidth: '760px', marginBottom: 'var(--space-5)' }}>
          These decisions were never in Pratibimb's memory. Each one is replayed as a fresh request (what the requester
          wrote, nothing of {first}'s answer) and the verdict is compared with hers. The same pipeline runs twice: once on the
          delegation-of-authority rules alone, once with the Gemini agents reading her past decisions and lessons.
          The last 5 are deliberately hard: the rules see a clean case, but something in the request text matters.
        </p>

        <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
          <ScoreCard title="Rules alone" subtitle="mandate only, no memory" s={r} accent="var(--text-muted)" />
          <ScoreCard title="Pratibimb" subtitle={`Gemini agents · ${model}`} s={g} accent="var(--primary-color)" />
        </div>

        <div style={{ marginTop: 'var(--space-4)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          Score counts ask and escalate as the same call (both hold the request back). Run {run_at?.replace('T', ' ')} · {cost?.live_calls} Gemini calls · ₹{cost?.inr} (USD {cost?.usd})
        </div>
      </div>

      <div className="glass-card" style={{ padding: 'var(--space-6)' }}>
        <h3 style={{ fontSize: 'var(--text-lg)', marginBottom: 'var(--space-4)', color: 'var(--text-primary)' }}>Case by case</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          {cases.map((c) => {
            const isOpen = open === c.decision_id;
            return (
              <div key={c.decision_id} style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}>
                <button
                  onClick={() => setOpen(isOpen ? null : c.decision_id)}
                  aria-expanded={isOpen}
                  style={{ width: '100%', background: 'transparent', border: 0, cursor: 'pointer', padding: 'var(--space-3) var(--space-4)', display: 'grid',
                    gridTemplateColumns: 'minmax(0, 1.4fr) repeat(3, minmax(0, 1fr)) auto', gap: 'var(--space-2)', alignItems: 'center', textAlign: 'left', color: 'inherit', font: 'inherit' }}
                  className="bt-row"
                >
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--primary-color)', fontWeight: 700 }}>
                      {c.decision_id}{c.set === 'hard' && <span className="tag tag-danger" style={{ marginLeft: 'var(--space-2)' }}>hard</span>}
                    </div>
                    <div style={{ fontWeight: 600, fontSize: 'var(--text-sm)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.vendor_name}</div>
                  </div>
                  <div><div className="bt-k">{first}</div><span className={`tag ${tagFor(c.expected)}`}>{label(c.expected)}</span></div>
                  <div><div className="bt-k">Rules alone</div>
                    <span style={{ display: 'inline-flex', gap: 'var(--space-1)', alignItems: 'center' }}><Mark got={c.rules?.verdict} expected={c.expected} /><span className={`tag ${tagFor(c.rules?.verdict)}`}>{label(c.rules?.verdict)}</span></span>
                  </div>
                  <div><div className="bt-k">Pratibimb</div>
                    <span style={{ display: 'inline-flex', gap: 'var(--space-1)', alignItems: 'center' }}><Mark got={c.gemini?.verdict} expected={c.expected} /><span className={`tag ${tagFor(c.gemini?.verdict)}`}>{label(c.gemini?.verdict)}</span></span>
                  </div>
                  {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>

                {isOpen && (
                  <div style={{ padding: '0 var(--space-4) var(--space-4)', fontSize: 'var(--text-xs)', display: 'grid', gap: 'var(--space-2)', color: 'var(--text-secondary)' }}>
                    <div><strong>Request:</strong> {c.request?.description}</div>
                    <div><strong>{first} decided:</strong> {c.meera_note}</div>
                    {c.gemini && (
                      <div style={{ background: 'var(--bg-inset)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Pratibimb: {c.gemini.headline}</div>
                        <div style={{ marginTop: 'var(--space-1)' }}>{c.gemini.reasoning}</div>
                        <div style={{ marginTop: 'var(--space-2)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)' }}>
                          Cites: {(c.gemini.citations || []).join(', ')}
                        </div>
                      </div>
                    )}
                    {c.rules?.verdict !== c.expected && c.set === 'hard' && (
                      <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'flex-start' }}>
                        <ShieldAlert size={14} style={{ color: 'var(--danger)', flexShrink: 0, marginTop: 2 }} />
                        <span>Why rules alone miss it: {c.why}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
