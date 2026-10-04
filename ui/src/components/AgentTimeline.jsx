import React from 'react';
import { Workflow, ShieldCheck, Ban } from 'lucide-react';
import { verdictLabel } from '../labels.js';

const LABEL = {
  mandate: 'Mandate check (code)',
  precedent: 'Precedent agent',
  challenger: 'Challenger agent',
  interviewer: 'Interviewer agent',
  decider: 'Decider agent',
};
const STRICT = ['approve', 'approve_with_conditions', 'ask', 'escalate', 'refuse'];
const COLOR = {
  mandate: 'var(--text-muted)',
  precedent: 'var(--primary-color)',
  challenger: 'var(--primary-color)',
  interviewer: 'var(--primary-color)',
  decider: 'var(--accent-color)',
};

/** How this verdict was reached: the ADK workflow timeline, and the two guardrails at work. */
export default function AgentTimeline({ verdict, pack }) {
  const word = (v = '') => verdictLabel(pack, v);
  const trace = verdict.agent_trace || [];
  if (!trace.length) return null;
  const total = Math.max(1, ...trace.map(t => t.start_ms + t.ms));
  const tightened = verdict.llm_verdict && verdict.llm_verdict !== verdict.verdict;
  const dropped = verdict.dropped_citations || [];

  return (
    <div style={{ background: 'var(--bg-inset)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: 'var(--space-5)', marginBottom: 'var(--space-6)' }}>
      <h3 style={{ fontSize: 'var(--text-sm)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--primary-color)', marginBottom: 'var(--space-3)' }}>
        <Workflow size={16} aria-hidden="true" />
        <span>How this verdict was reached · {verdict.orchestrator || 'agent workflow'}</span>
      </h3>

      <div role="list" style={{ display: 'grid', gap: 'var(--space-2)' }}>
        {trace.map(t => (
          <div role="listitem" key={t.node} style={{ display: 'grid', gridTemplateColumns: 'minmax(110px, 160px) 1fr auto', gap: 'var(--space-3)', alignItems: 'center', fontSize: 'var(--text-xs)' }}>
            <span style={{ color: 'var(--text-secondary)' }}>{LABEL[t.node] || t.node}</span>
            <div style={{ position: 'relative', height: '10px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
              <div style={{
                position: 'absolute', top: 0, bottom: 0,
                left: `${(t.start_ms / total) * 100}%`,
                width: `max(${(t.ms / total) * 100}%, 4px)`,
                background: COLOR[t.node] || 'var(--primary-color)', borderRadius: 'var(--radius-full)'
              }} />
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', minWidth: '56px', textAlign: 'right' }}>
              {t.ms < 1000 ? `${t.ms} ms` : `${(t.ms / 1000).toFixed(1)} s`}
            </span>
          </div>
        ))}
      </div>
      <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: 'var(--space-2)' }}>
        The three agents run in parallel; the Decider waits for all of them.
      </p>

      <div style={{ display: 'grid', gap: 'var(--space-2)', marginTop: 'var(--space-3)', fontSize: 'var(--text-xs)' }}>
        <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'flex-start' }}>
          <ShieldCheck size={14} style={{ color: tightened ? 'var(--warning)' : 'var(--success)', flexShrink: 0, marginTop: 2 }} aria-hidden="true" />
          <span>
            {verdict.engine === 'rules' || !verdict.llm_verdict
              ? `Decided by the mandate rules (floor: ${word(verdict.mandate_floor) || 'n/a'}).`
              : tightened
                ? <>Gemini proposed <strong>{word(verdict.llm_verdict)}</strong>; the mandate does not allow that, so the verdict was kept at <strong>{word(verdict.verdict)}</strong>.</>
                : STRICT.indexOf(verdict.verdict) > STRICT.indexOf(verdict.mandate_floor)
                  ? <>The rules alone allowed <strong>{word(verdict.mandate_floor)}</strong>. Pratibimb made it stricter, <strong>{word(verdict.verdict)}</strong>, from what it read in the request, documents and past decisions. (Stricter is allowed; looser never is.)</>
                  : <>Mandate floor: <strong>{word(verdict.mandate_floor)}</strong>. Gemini's verdict stayed within it.</>}
          </span>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'flex-start' }}>
          <Ban size={14} style={{ color: dropped.length ? 'var(--warning)' : 'var(--success)', flexShrink: 0, marginTop: 2 }} aria-hidden="true" />
          <span>
            {dropped.length
              ? <>{dropped.length} citation{dropped.length > 1 ? 's' : ''} matched no real record and {dropped.length > 1 ? 'were' : 'was'} removed: <span style={{ fontFamily: 'var(--font-mono)' }}>{dropped.join(', ')}</span></>
              : 'Every citation was checked against real rules, clauses, decisions and lessons (none removed).'}
          </span>
        </div>
      </div>
    </div>
  );
}
