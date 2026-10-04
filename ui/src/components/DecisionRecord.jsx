import React, { useEffect, useState } from 'react';
import AgentTimeline from './AgentTimeline.jsx';
import { verdictLabel, firstName, isRuleId } from '../labels.js';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ShieldAlert,
  BookOpen,
  Scale,
  FileText,
  RotateCcw,
  Sparkles,
  ArrowRight,
  UserCheck
} from 'lucide-react';

const VERDICTS = ['approve', 'approve_with_conditions', 'ask', 'escalate', 'refuse'];

// A ready-made override for each senior's clean demo case, so the learning loop can be shown in one click
const OVERRIDE_DEFAULTS = {
  vendor: {
    note: "The vendor's key account manager just left. I would have held renewal until a senior replacement was named and contractually locked.",
    rule: "For service vendors with named key personnel, verify named persons are active and contractually bound before renewal.",
  },
  leads: {
    note: "We have only three Hindi-certified agents today. Before we promise Hindi chat from 1 November, delivery must confirm we can staff it.",
    rule: "Before qualifying an upsell that needs a new language or skill, delivery confirms capacity and a ramp-up date.",
  },
  spend: {
    note: "Courier is already included in Printex's rate contract, and this is the third month they've added it. Ask them to remove it before we pay.",
    rule: "Recurring add-on charges that the rate contract already covers are held until the supplier removes them.",
  },
};

export default function DecisionRecord({ verdict, request, pack, senior, onRecordOverride, overrideSuccess, onRerun, onResetDemo, isAnalyzing }) {
  const packId = pack?.id || 'vendor';
  const first = senior?.name ? firstName(senior.name) : 'Meera';
  const fullName = senior?.name || 'Meera Nair';
  const he = senior?.pronoun === 'he';
  const subj = he ? 'he' : 'she';
  const pos = he ? 'his' : 'her';
  const vl = (v) => verdictLabel(pack, v);
  const [showOverrideForm, setShowOverrideForm] = useState(false);
  const [seniorDecision, setSeniorDecision] = useState('ask');
  const [verdictBefore, setVerdictBefore] = useState(null);
  const [confirmed, setConfirmed] = useState(false);
  const [overrideNote, setOverrideNote] = useState(OVERRIDE_DEFAULTS[packId]?.note || '');
  const [proposedRule, setProposedRule] = useState(OVERRIDE_DEFAULTS[packId]?.rule || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  // Every citation opens its source: rule, lesson, past decision or document clause
  const [sources, setSources] = useState({});
  const [openCite, setOpenCite] = useState(null);
  useEffect(() => {
    fetch(`/api/sources?pack=${packId}`).then(r => r.json()).then(d => setSources(d.sources || {})).catch(() => {});
    setOpenCite(null);
  }, [packId, verdict?.request_id, overrideSuccess?.id]);
  useEffect(() => {
    setOverrideNote(OVERRIDE_DEFAULTS[packId]?.note || '');
    setProposedRule(OVERRIDE_DEFAULTS[packId]?.rule || '');
    setShowOverrideForm(false); setConfirmed(false); setVerdictBefore(null);
  }, [packId]);

  if (!verdict) {
    return (
      <div className="glass-card" style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
        <HelpCircle size={48} style={{ color: 'var(--text-muted)', margin: '0 auto var(--space-4)' }} />
        <h3 style={{ fontSize: 'var(--text-xl)', marginBottom: 'var(--space-2)' }}>No Active Decision File</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)', maxWidth: '420px', margin: '0 auto var(--space-6)' }}>
          Please select a vendor request from the <strong>Request Inbox</strong> and click "Run Pratibimb Scrutiny" to generate a one-page audit-ready decision file.
        </p>
      </div>
    );
  }

  const getVerdictTheme = (v) => {
    switch (v) {
      case 'approve':
        return { bg: 'var(--success-light)', border: 'var(--success)', color: 'var(--success)', icon: <CheckCircle2 size={24} /> };
      case 'approve_with_conditions':
        return { bg: 'var(--warning-light)', border: 'var(--warning)', color: 'var(--warning)', icon: <AlertTriangle size={24} /> };
      case 'escalate':
        return { bg: 'var(--info-light)', border: 'var(--info)', color: 'var(--info)', icon: <AlertCircle size={24} /> };
      case 'ask':
        return { bg: 'var(--warning-light)', border: 'var(--accent-color)', color: 'var(--accent-color)', icon: <HelpCircle size={24} /> };
      case 'refuse':
      default:
        return { bg: 'var(--danger-light)', border: 'var(--danger)', color: 'var(--danger)', icon: <XCircle size={24} /> };
    }
  };

  const theme = getVerdictTheme(verdict.verdict);

  const handleOverrideSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setVerdictBefore(verdict.verdict);
    await onRecordOverride({
      request_id: verdict.request_id,
      engine_verdict: verdict.verdict,
      senior_decision: seniorDecision,
      senior_override_note: overrideNote,
      proposed_rule: proposedRule,
      senior_name: fullName,
      request
    });
    setIsSubmitting(false);
    setShowOverrideForm(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Decision File Master Card */}
      <div className="glass-card" style={{ padding: 'var(--space-7)', borderTop: `4px solid ${theme.border}` }}>
        {/* Document Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-4)', borderBottom: '1px solid var(--border-color)', paddingBottom: 'var(--space-5)', marginBottom: 'var(--space-6)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-1)' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 'var(--text-sm)', color: 'var(--primary-color)' }}>
                DECISION FILE: PRATIBIMB-{verdict.request_id}
              </span>
              <span className="tag tag-info" style={{ fontSize: 'var(--text-xs)' }}>
                Confidence: {verdict.confidence?.toUpperCase()}
              </span>
            </div>
            <h2 style={{ fontSize: 'var(--text-xl)', color: 'var(--text-primary)', marginTop: 'var(--space-1)' }}>
              {request?.vendor_name || request?.entity_name || 'Decision File'}
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)' }}>
              Subject: {request?.description || 'Vendor Evaluation'} · Requester: {request?.requested_by || 'Operations Team'}
            </p>
          </div>

          {/* Big Verdict Pill */}
          <div style={{
            background: theme.bg,
            border: `1px solid ${theme.border}`,
            color: theme.color,
            padding: 'var(--space-3) var(--space-6)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)'
          }}>
            {theme.icon}
            <div>
              <div style={{ fontSize: 'var(--text-xs)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                Synthesized Verdict
              </div>
              <strong style={{ fontSize: 'var(--text-lg)', letterSpacing: '0.02em' }}>
                {vl(verdict.verdict).toUpperCase()}
              </strong>
            </div>
          </div>
        </div>

        {/* Executive Headline */}
        <div style={{
          background: 'var(--bg-inset)',
          padding: 'var(--space-4) var(--space-5)',
          borderRadius: 'var(--radius-sm)',
          fontSize: 'var(--text-base)',
          fontWeight: 600,
          color: 'var(--text-primary)',
          borderLeft: `4px solid ${theme.border}`,
          marginBottom: 'var(--space-6)'
        }}>
          {verdict.headline}
        </div>

        {/* Why: the reasoning in Meera's voice, and what produced it */}
        {verdict.reasoning && (
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 'var(--space-3)' }}>
            {verdict.reasoning}
          </p>
        )}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', alignItems: 'center', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-6)' }}>
          <span className="tag tag-info" style={{ fontSize: 'var(--text-xs)' }}>{verdict.engine === 'rules' ? 'Rules only' : `Gemini agents · ${verdict.engine}`}</span>
          {verdict.lessons_applied?.length > 0 && (
            <span>Lessons applied: <strong style={{ fontFamily: 'var(--font-mono)' }}>{verdict.lessons_applied.join(', ')}</strong></span>
          )}
          {verdict.elapsed_ms > 0 && <span>· {verdict.elapsed_ms < 1000 ? `${verdict.elapsed_ms} ms` : `${(verdict.elapsed_ms / 1000).toFixed(1)} s`}</span>}
          <span>· {verdict.cost_inr > 0 ? `₹${verdict.cost_inr.toFixed(2)} in Gemini calls` : 'no new Gemini cost (cached or rules)'}</span>
        </div>

        <AgentTimeline verdict={verdict} pack={pack} />

        {/* Two-Column Grid: Mandate Check & Precedents */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 320px), 1fr))', gap: 'var(--space-6)', marginBottom: 'var(--space-6)' }}>
          {/* Mandate Check */}
          <div style={{ background: 'var(--bg-inset)', padding: 'var(--space-5)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
            <h3 style={{ fontSize: 'var(--text-base)', marginBottom: 'var(--space-3)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--primary-color)' }}>
              <Scale size={18} />
              <span>Mandate Limits Evaluation</span>
            </h3>
            <div style={{ marginBottom: 'var(--space-3)' }}>
              <span className={`tag ${verdict.mandate_check?.within_limits ? 'tag-success' : 'tag-danger'}`}>
                {verdict.mandate_check?.within_limits ? '✓ Within Delegated Authority' : '⚠️ Limits Exceeded / Escalation Required'}
              </span>
            </div>
            {verdict.mandate_check?.breaches?.length > 0 ? (
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', fontSize: 'var(--text-xs)' }}>
                {verdict.mandate_check.breaches.map((b, idx) => (
                  <li key={idx} style={{ color: 'var(--danger)', display: 'flex', gap: 'var(--space-2)' }}>
                    <span>•</span>
                    <span>{b}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                Inside {first}'s delegated authority under {(verdict.citations || []).filter(isRuleId).join(', ') || `${pos} mandate`}. {first} still confirms the verdict.
              </p>
            )}
          </div>

          {/* Precedents Cited */}
          <div style={{ background: 'var(--bg-inset)', padding: 'var(--space-5)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
            <h3 style={{ fontSize: 'var(--text-base)', marginBottom: 'var(--space-3)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--primary-color)' }}>
              <BookOpen size={18} />
              <span>Episodic Precedents Grounding</span>
            </h3>
            {verdict.precedents?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {verdict.precedents.map((p, idx) => (
                  <div key={idx} style={{ fontSize: 'var(--text-xs)', paddingBottom: 'var(--space-2)', borderBottom: idx < verdict.precedents.length - 1 ? '1px solid var(--border-color)' : 'none' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-1)' }}>
                      <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary-color)' }}>{p.decision_id}</strong>
                      <span className={`tag ${p.outcome_status === 'bad' ? 'tag-danger' : 'tag-success'}`} style={{ fontSize: 'var(--text-xs)' }}>
                        {p.outcome_status.toUpperCase()}
                      </span>
                    </div>
                    <div style={{ color: 'var(--text-secondary)' }}>{p.takeaway}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                No prior direct precedent on file. Case evaluated as novel counterparty.
              </p>
            )}
          </div>
        </div>

        {/* Contract Challenges (Adversarial Findings) */}
        {verdict.challenges?.length > 0 && (
          <div style={{ marginBottom: 'var(--space-6)', background: 'var(--danger-light)', padding: 'var(--space-5)', borderRadius: 'var(--radius-sm)', border: '1px solid color-mix(in srgb, var(--danger) 25%, transparent)' }}>
            <h3 style={{ fontSize: 'var(--text-base)', marginBottom: 'var(--space-3)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--danger)' }}>
              <ShieldAlert size={18} />
              <span>Challenger Agent Contractual Scrutiny ({verdict.challenges.length} Findings)</span>
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              {verdict.challenges.map((c, idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-2) var(--space-4)', fontSize: 'var(--text-sm)' }}>
                  <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                    <span style={{ color: 'var(--danger)', fontWeight: 700 }}>{idx + 1}.</span>
                    <span>{c.finding}</span>
                  </div>
                  {sources[c.source] ? (
                    <button type="button" className="tag tag-danger" onClick={() => setOpenCite(c.source)}
                      title="Open the clause" style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', whiteSpace: 'nowrap', cursor: 'pointer' }}>
                      {c.source}
                    </button>
                  ) : (
                    <span className="tag tag-danger" style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', whiteSpace: 'nowrap' }}>
                      {c.source}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Probing Questions for Requester */}
        {verdict.questions_for_requester?.length > 0 && (
          <div style={{ marginBottom: 'var(--space-6)', background: 'var(--accent-light)', padding: 'var(--space-5)', borderRadius: 'var(--radius-sm)', border: '1px solid color-mix(in srgb, var(--accent-color) 30%, transparent)' }}>
            <h3 style={{ fontSize: 'var(--text-base)', marginBottom: 'var(--space-3)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--accent-color)' }}>
              <HelpCircle size={18} />
              <span>Interviewer Agent: {first}'s Instinct Inquiries</span>
            </h3>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', fontSize: 'var(--text-sm)' }}>
              {verdict.questions_for_requester.map((q, idx) => (
                <li key={idx} style={{ display: 'flex', gap: 'var(--space-2)', fontStyle: 'italic', color: 'var(--text-primary)' }}>
                  <span>❓</span>
                  <span>"{q}"</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommended Safeguards & Conditions */}
        {verdict.recommended_conditions?.length > 0 && (
          <div style={{ marginBottom: 'var(--space-6)', background: 'var(--bg-inset)', padding: 'var(--space-5)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
            <h3 style={{ fontSize: 'var(--text-base)', marginBottom: 'var(--space-3)', color: 'var(--text-primary)' }}>
              🛡️ Recommended Contractual Safeguards
            </h3>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', fontSize: 'var(--text-sm)' }}>
              {verdict.recommended_conditions.map((cond, idx) => (
                <li key={idx} style={{ display: 'flex', gap: 'var(--space-2)', color: 'var(--text-primary)' }}>
                  <span style={{ color: 'var(--primary-color)' }}>✓</span>
                  <span>{cond}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Mandatory Citations Bar */}
        <div style={{ paddingTop: 'var(--space-5)', borderTop: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
          <span style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Mandatory Citations ({verdict.citations?.length || 0}):
          </span>
          {(verdict.citations || []).map((cite, idx) => (
            <button key={idx} type="button" className="tag tag-info" onClick={() => setOpenCite(openCite === cite ? null : cite)}
              aria-expanded={openCite === cite} title="Open the source"
              style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', cursor: 'pointer',
                outline: openCite === cite ? '2px solid var(--primary-color)' : 'none' }}>
              {cite}
            </button>
          ))}
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>Click any citation to read its source.</span>
        </div>
        {openCite && (
          <div role="region" aria-label={`Source ${openCite}`} style={{ marginTop: 'var(--space-3)', padding: 'var(--space-4)',
            background: 'var(--bg-inset)', border: '1px solid var(--primary-color)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 'var(--space-3)', alignItems: 'flex-start' }}>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 'var(--text-xs)', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                  {sources[openCite]?.kind || 'Source'}
                </div>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: 'var(--space-1)' }}>
                  {sources[openCite]?.title || openCite}
                </div>
              </div>
              <button type="button" className="btn btn-secondary" style={{ padding: 'var(--space-1) var(--space-3)', fontSize: 'var(--text-xs)' }}
                onClick={() => setOpenCite(null)}>Close</button>
            </div>
            <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {sources[openCite]?.text || 'Not found in the record.'}
            </p>
          </div>
        )}
      </div>

      {/* THE LEARNING MOMENT: Senior Review & Override Loop */}
      <div className="glass-card" style={{ padding: 'var(--space-6)', background: 'var(--bg-inset)', border: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-4)', marginBottom: 'var(--space-4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <UserCheck size={22} style={{ color: 'var(--primary-color)' }} />
            <div>
              <h3 style={{ fontSize: 'var(--text-lg)', color: 'var(--text-primary)' }}>
                Senior Authority Review ({fullName})
              </h3>
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                {first} always makes the final call. When {subj} overrides, Pratibimb writes a lesson and files {pos} decision as a precedent; the next verdict uses both.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
            <button
              className="btn btn-primary"
              style={{ fontSize: 'var(--text-xs)' }}
              onClick={() => setConfirmed(true)}
              disabled={confirmed}
            >
              {confirmed ? `Confirmed by ${first}` : 'Confirm Verdict'}
            </button>
            <button
              className="btn btn-secondary"
              style={{ fontSize: 'var(--text-xs)', borderColor: 'var(--warning)', color: 'var(--warning)' }}
              onClick={() => setShowOverrideForm(!showOverrideForm)}
            >
              <RotateCcw size={14} />
              <span>Override Verdict & Teach Pratibimb</span>
            </button>
          </div>
        </div>

        {/* Override Form */}
        {showOverrideForm && (
          <form onSubmit={handleOverrideSubmit} style={{ marginTop: 'var(--space-5)', padding: 'var(--space-5)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
            <h4 style={{ fontSize: 'var(--text-base)', marginBottom: 'var(--space-3)', color: 'var(--warning)' }}>
              Record Senior Override & Crystallize Governance Lesson
            </h4>

            <div style={{ marginBottom: 'var(--space-4)' }}>
              <label htmlFor="senior-decision" style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, marginBottom: 'var(--space-1)' }}>
                {first}'s decision
              </label>
              <select
                id="senior-decision"
                value={seniorDecision}
                onChange={(e) => setSeniorDecision(e.target.value)}
                style={{ width: '100%', padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: 'var(--text-sm)' }}
              >
                {VERDICTS.filter((v) => v !== verdict.verdict).map((v) => (
                  <option key={v} value={v}>{vl(v)}</option>
                ))}
              </select>
            </div>

            <div style={{ marginBottom: 'var(--space-4)' }}>
              <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, marginBottom: 'var(--space-1)' }}>
                {first}'s Decision Note / Reason for Disagreement
              </label>
              <textarea
                rows={2}
                value={overrideNote}
                onChange={(e) => setOverrideNote(e.target.value)}
                style={{ width: '100%', padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: 'var(--text-sm)' }}
              />
            </div>

            <div style={{ marginBottom: 'var(--space-4)' }}>
              <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, marginBottom: 'var(--space-1)' }}>
                Codified Governance Rule (Lesson to Add to Memory)
              </label>
              <input
                type="text"
                value={proposedRule}
                onChange={(e) => setProposedRule(e.target.value)}
                style={{ width: '100%', padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: 'var(--text-sm)' }}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ background: 'var(--warning)', borderColor: 'var(--warning)', fontSize: 'var(--text-sm)' }}
              disabled={isSubmitting}
            >
              <Sparkles size={16} />
              <span>{isSubmitting ? 'Crystallizing Lesson...' : 'Save Override & Teach Pratibimb Engine'}</span>
            </button>
          </form>
        )}

        {/* Override Success Notification */}
        {overrideSuccess && (
          <div style={{
            marginTop: 'var(--space-4)',
            padding: 'var(--space-4)',
            background: 'var(--success-light)',
            border: '1px solid var(--success)',
            borderRadius: 'var(--radius-sm)',
            fontSize: 'var(--text-sm)',
            color: 'var(--success)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)'
          }}>
            <CheckCircle2 size={20} />
            <div style={{ flex: 1 }}>
              <strong>Lesson {overrideSuccess.id} saved: {overrideSuccess.title}.</strong> "{overrideSuccess.rule}"
              <div style={{ marginTop: 'var(--space-1)', color: 'var(--text-secondary)' }}>
                {verdictBefore && verdictBefore !== verdict.verdict
                  ? <>Re-run verdict: <strong>{vl(verdictBefore)}</strong> → <strong>{vl(verdict.verdict)}</strong>{verdict.lessons_applied?.includes(overrideSuccess.id) ? `, citing ${overrideSuccess.id}` : ''}.</>
                  : 'Re-run the request to see the lesson change the verdict.'}
              </div>
              <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-2)', flexWrap: 'wrap' }}>
                <button type="button" className="btn btn-primary" style={{ fontSize: 'var(--text-xs)' }} onClick={() => onRerun && onRerun(request)} disabled={isAnalyzing}>
                  <RotateCcw size={14} /><span>{isAnalyzing ? 'Re-running…' : 'Re-run this request'}</span>
                </button>
                <button type="button" className="btn btn-secondary" style={{ fontSize: 'var(--text-xs)' }} onClick={() => { setVerdictBefore(null); onResetDemo && onResetDemo(); }}>
                  Reset demo memory
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function AlertCircle(props) {
  return <AlertTriangle {...props} />;
}
