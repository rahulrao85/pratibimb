import React, { useState } from 'react';
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

export default function DecisionRecord({ verdict, request, onRecordOverride, overrideSuccess }) {
  const [showOverrideForm, setShowOverrideForm] = useState(false);
  const [overrideNote, setOverrideNote] = useState(
    "The vendor's key account manager just left. I would have held renewal until a senior replacement was named and contractually locked."
  );
  const [proposedRule, setProposedRule] = useState(
    "For service vendors with named key personnel, verify named persons are active and contractually bound before renewal."
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!verdict) {
    return (
      <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
        <HelpCircle size={48} style={{ color: 'var(--text-muted)', margin: '0 auto 1rem' }} />
        <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>No Active Decision File</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '420px', margin: '0 auto 1.5rem' }}>
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
    await onRecordOverride({
      request_id: verdict.request_id,
      engine_verdict: verdict.verdict,
      senior_decision: 'escalate_with_condition',
      senior_override_note: overrideNote,
      proposed_rule: proposedRule,
      senior_name: 'Meera Nair'
    });
    setIsSubmitting(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Decision File Master Card */}
      <div className="glass-card" style={{ padding: '2rem', borderTop: `4px solid ${theme.border}` }}>
        {/* Document Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1.25rem', marginBottom: '1.5rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.25rem' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.9rem', color: 'var(--primary-color)' }}>
                DECISION FILE: PRATIBIMB-{verdict.request_id}
              </span>
              <span className="tag tag-info" style={{ fontSize: '0.65rem' }}>
                Confidence: {verdict.confidence?.toUpperCase()}
              </span>
            </div>
            <h2 style={{ fontSize: '1.4rem', color: 'var(--text-primary)', marginTop: '0.25rem' }}>
              {request?.vendor_name || 'Vendor Decision File'}
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Subject: {request?.description || 'Vendor Evaluation'} · Requester: {request?.requested_by || 'Operations Team'}
            </p>
          </div>

          {/* Big Verdict Pill */}
          <div style={{
            background: theme.bg,
            border: `1px solid ${theme.border}`,
            color: theme.color,
            padding: '0.75rem 1.5rem',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem'
          }}>
            {theme.icon}
            <div>
              <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                Synthesized Verdict
              </div>
              <strong style={{ fontSize: '1.15rem', letterSpacing: '0.02em' }}>
                {verdict.verdict.replace(/_/g, ' ').toUpperCase()}
              </strong>
            </div>
          </div>
        </div>

        {/* Executive Headline */}
        <div style={{
          background: 'var(--bg-inset)',
          padding: '1rem 1.25rem',
          borderRadius: 'var(--radius-sm)',
          fontSize: '1rem',
          fontWeight: 600,
          color: 'var(--text-primary)',
          borderLeft: `4px solid ${theme.border}`,
          marginBottom: '1.5rem'
        }}>
          {verdict.headline}
        </div>

        {/* Two-Column Grid: Mandate Check & Precedents */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
          {/* Mandate Check */}
          <div style={{ background: 'var(--bg-inset)', padding: '1.25rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
            <h3 style={{ fontSize: '0.95rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--primary-color)' }}>
              <Scale size={18} />
              <span>Mandate Limits Evaluation</span>
            </h3>
            <div style={{ marginBottom: '0.65rem' }}>
              <span className={`tag ${verdict.mandate_check?.within_limits ? 'tag-success' : 'tag-danger'}`}>
                {verdict.mandate_check?.within_limits ? '✓ Within Delegated Authority' : '⚠️ Limits Exceeded / Escalation Required'}
              </span>
            </div>
            {verdict.mandate_check?.breaches?.length > 0 ? (
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.825rem' }}>
                {verdict.mandate_check.breaches.map((b, idx) => (
                  <li key={idx} style={{ color: 'var(--danger)', display: 'flex', gap: '0.4rem' }}>
                    <span>•</span>
                    <span>{b}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                Request complies with all delegation thresholds (≤ ₹5,00,000, 0 breaches, standard 12m term).
              </p>
            )}
          </div>

          {/* Precedents Cited */}
          <div style={{ background: 'var(--bg-inset)', padding: '1.25rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
            <h3 style={{ fontSize: '0.95rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--primary-color)' }}>
              <BookOpen size={18} />
              <span>Episodic Precedents Grounding</span>
            </h3>
            {verdict.precedents?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                {verdict.precedents.map((p, idx) => (
                  <div key={idx} style={{ fontSize: '0.8rem', paddingBottom: '0.5rem', borderBottom: idx < verdict.precedents.length - 1 ? '1px solid var(--border-color)' : 'none' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                      <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary-color)' }}>{p.decision_id}</strong>
                      <span className={`tag ${p.outcome_status === 'bad' ? 'tag-danger' : 'tag-success'}`} style={{ fontSize: '0.65rem' }}>
                        {p.outcome_status.toUpperCase()}
                      </span>
                    </div>
                    <div style={{ color: 'var(--text-secondary)' }}>{p.takeaway}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                No prior direct precedent on file. Case evaluated as novel counterparty.
              </p>
            )}
          </div>
        </div>

        {/* Contract Challenges (Adversarial Findings) */}
        {verdict.challenges?.length > 0 && (
          <div style={{ marginBottom: '1.5rem', background: 'rgba(239, 68, 68, 0.05)', padding: '1.25rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
            <h3 style={{ fontSize: '0.95rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--danger)' }}>
              <ShieldAlert size={18} />
              <span>Challenger Agent Contractual Scrutiny ({verdict.challenges.length} Findings)</span>
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {verdict.challenges.map((c, idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', fontSize: '0.85rem' }}>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <span style={{ color: 'var(--danger)', fontWeight: 700 }}>{idx + 1}.</span>
                    <span>{c.finding}</span>
                  </div>
                  <span className="tag tag-danger" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', whiteSpace: 'nowrap' }}>
                    {c.source}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Probing Questions for Requester */}
        {verdict.questions_for_requester?.length > 0 && (
          <div style={{ marginBottom: '1.5rem', background: 'var(--accent-light)', padding: '1.25rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(14, 165, 233, 0.2)' }}>
            <h3 style={{ fontSize: '0.95rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-color)' }}>
              <HelpCircle size={18} />
              <span>Interviewer Agent: Meera's Instinct Inquiries</span>
            </h3>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.85rem' }}>
              {verdict.questions_for_requester.map((q, idx) => (
                <li key={idx} style={{ display: 'flex', gap: '0.5rem', fontStyle: 'italic', color: 'var(--text-primary)' }}>
                  <span>❓</span>
                  <span>"{q}"</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommended Safeguards & Conditions */}
        {verdict.recommended_conditions?.length > 0 && (
          <div style={{ marginBottom: '1.5rem', background: 'var(--bg-inset)', padding: '1.25rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
            <h3 style={{ fontSize: '0.95rem', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
              🛡️ Recommended Contractual Safeguards
            </h3>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.85rem' }}>
              {verdict.recommended_conditions.map((cond, idx) => (
                <li key={idx} style={{ display: 'flex', gap: '0.5rem', color: 'var(--text-primary)' }}>
                  <span style={{ color: 'var(--primary-color)' }}>✓</span>
                  <span>{cond}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Mandatory Citations Bar */}
        <div style={{ paddingTop: '1.25rem', borderTop: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Mandatory Citations ({verdict.citations?.length || 0}):
          </span>
          {(verdict.citations || []).map((cite, idx) => (
            <span key={idx} className="tag tag-info" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.725rem' }}>
              {cite}
            </span>
          ))}
        </div>
      </div>

      {/* THE LEARNING MOMENT: Senior Review & Override Loop */}
      <div className="glass-card" style={{ padding: '1.75rem', background: 'var(--bg-inset)', border: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <UserCheck size={22} style={{ color: 'var(--primary-color)' }} />
            <div>
              <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)' }}>
                Senior Authority Review (Meera Nair)
              </h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                The senior retains final decision authority. Overrides generate lessons that update future verdicts.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button 
              className="btn btn-primary"
              style={{ fontSize: '0.8rem' }}
              onClick={() => alert(`Verdict ${verdict.verdict.toUpperCase()} confirmed by Meera Nair. Audit record archived.`)}
            >
              Confirm Verdict
            </button>
            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', borderColor: 'var(--warning)', color: 'var(--warning)' }}
              onClick={() => setShowOverrideForm(!showOverrideForm)}
            >
              <RotateCcw size={14} />
              <span>Override Verdict & Teach Pratibimb</span>
            </button>
          </div>
        </div>

        {/* Override Form */}
        {showOverrideForm && (
          <form onSubmit={handleOverrideSubmit} style={{ marginTop: '1.25rem', padding: '1.25rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
            <h4 style={{ fontSize: '0.95rem', marginBottom: '0.75rem', color: 'var(--warning)' }}>
              Record Senior Override & Crystallize Governance Lesson
            </h4>
            
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Meera's Decision Note / Reason for Disagreement
              </label>
              <textarea
                rows={2}
                value={overrideNote}
                onChange={(e) => setOverrideNote(e.target.value)}
                style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: '0.85rem' }}
              />
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Codified Governance Rule (Lesson to Add to Memory)
              </label>
              <input
                type="text"
                value={proposedRule}
                onChange={(e) => setProposedRule(e.target.value)}
                style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: '0.85rem' }}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ background: 'var(--warning)', borderColor: 'var(--warning)', fontSize: '0.85rem' }}
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
            marginTop: '1rem',
            padding: '1rem',
            background: 'var(--success-light)',
            border: '1px solid var(--success)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.85rem',
            color: 'var(--success)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.65rem'
          }}>
            <CheckCircle2 size={20} />
            <div>
              <strong>Lesson {overrideSuccess.id} Crystallized!</strong> "{overrideSuccess.rule}" is now registered in Pratibimb's governance ledger. Future vendor renewals will enforce key personnel checks automatically.
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
