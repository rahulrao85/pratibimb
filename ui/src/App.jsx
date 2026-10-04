import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar.jsx';
import HowMeeraDecides from './components/HowMeeraDecides.jsx';
import MandateLimits from './components/MandateLimits.jsx';
import RequestInbox from './components/RequestInbox.jsx';
import PackInbox from './components/PackInbox.jsx';
import DecisionRecord from './components/DecisionRecord.jsx';
import BacktestDashboard from './components/BacktestDashboard.jsx';
import PitchModal from './components/PitchModal.jsx';

const PACK_KEY = 'pratibimb_pack';
const readPack = () => { try { return localStorage.getItem(PACK_KEY) || 'vendor'; } catch (e) { return 'vendor'; } };

export default function App() {
  const [activeTab, setActiveTab] = useState('inbox');
  // Govu theme: index.html sets <html data-theme> before first paint (stored choice, else the OS preference)
  const [theme, setTheme] = useState(() => document.documentElement.dataset.theme || 'light');
  const [isPitchOpen, setIsPitchOpen] = useState(false);

  // Which senior's Pratibimb is open: vendor (Meera) | leads (Vikram) | spend (Kavya)
  const [packs, setPacks] = useState([]);
  const [packId, setPackId] = useState(readPack);
  const pack = packs.find(p => p.id === packId) || { id: packId };
  const packRef = useRef(packId);
  const api = (path) => `${path}${path.includes('?') ? '&' : '?'}pack=${packRef.current}`;

  // Core Data States
  const [senior, setSenior] = useState(null);
  const [mandate, setMandate] = useState(null);
  const [decisions, setDecisions] = useState([]);
  const [requests, setRequests] = useState([]);
  const [selectedRequestId, setSelectedRequestId] = useState(null);

  // Decision & Analysis States
  const [currentVerdict, setCurrentVerdict] = useState(null);
  const [activeRequest, setActiveRequest] = useState(null); // the request actually evaluated (demo or custom)
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [overrideSuccess, setOverrideSuccess] = useState(null);

  // Backtest State (saved results; the page never re-runs it)
  const [backtestData, setBacktestData] = useState(null);

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('theme', next); } catch (e) { /* private mode: theme just isn't remembered */ }
    setTheme(next);
  };

  const switchPack = (id) => {
    if (id === packRef.current) return;
    try { localStorage.setItem(PACK_KEY, id); } catch (e) { /* not remembered */ }
    setPackId(id);
  };

  useEffect(() => {
    fetch('/api/packs').then(r => r.json()).then(d => setPacks(d.packs || [])).catch(e => console.log('Packs API error:', e));
  }, []);

  // Load the open senior's memory, mandate, requests and back-test (again whenever the pack changes)
  useEffect(() => {
    packRef.current = packId;
    setCurrentVerdict(null); setActiveRequest(null); setOverrideSuccess(null); setBacktestData(null);
    fetch(api('/api/senior')).then(r => r.json()).then(setSenior).catch(e => console.log('Senior API error:', e));
    fetch(api('/api/mandate')).then(r => r.json()).then(setMandate).catch(e => console.log('Mandate API error:', e));
    fetch(api('/api/decisions')).then(r => r.json()).then(d => setDecisions(d.decisions || [])).catch(e => console.log('Decisions API error:', e));
    fetch(api('/api/requests'))
      .then(r => r.json())
      .then(data => {
        const reqList = data.requests || [];
        setRequests(reqList);
        // Open on each senior's hardest demo case (the second request), served from cache
        const defReq = reqList[1] || reqList[0];
        if (defReq) {
          setSelectedRequestId(defReq.id);
          runDecisionAnalysis(defReq, false);
        }
      })
      .catch(e => console.log('Requests API error:', e));
    fetch(api('/api/backtest')).then(r => r.ok ? r.json() : null).then(setBacktestData).catch(e => console.log('Backtest API error:', e));
  }, [packId]);

  // Run Decision Analysis via Decider API
  const runDecisionAnalysis = async (reqToEvaluate, navigateToRecord = true, clearOverride = true) => {
    const forPack = packRef.current;
    setIsAnalyzing(true);
    setActiveRequest(reqToEvaluate);
    if (clearOverride) setOverrideSuccess(null);
    try {
      const res = await fetch(api('/api/decide'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reqToEvaluate)
      });
      if (res.ok && forPack === packRef.current) {
        setCurrentVerdict(await res.json());
        if (navigateToRecord) setActiveTab('record');
      }
    } catch (err) {
      console.error('Decision run failed:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Handle Senior Override
  const handleRecordOverride = async (payload) => {
    try {
      const res = await fetch(api('/api/learner/override'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setOverrideSuccess(data.lesson);
        const d = await fetch(api('/api/decisions')).then(r => r.json());
        setDecisions(d.decisions || []);
      }
    } catch (err) {
      console.error('Override recording failed:', err);
    }
  };

  // Forget what this visitor taught this senior, and re-run the open request
  const handleResetDemo = async () => {
    try {
      await fetch(api('/api/demo/reset'), { method: 'POST' });
      setOverrideSuccess(null);
      const d = await fetch(api('/api/decisions')).then(r => r.json());
      setDecisions(d.decisions || []);
      if (activeRequest) runDecisionAnalysis(activeRequest, false, false);
    } catch (err) {
      console.error('Demo reset failed:', err);
    }
  };

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        theme={theme}
        toggleTheme={toggleTheme}
        onOpenPitch={() => setIsPitchOpen(true)}
        packs={packs}
        packId={packId}
        onSwitchPack={switchPack}
        senior={senior}
      />

      <main style={{ flex: 1, paddingBottom: 'var(--space-8)' }}>
        {activeTab === 'memory' && (
          <HowMeeraDecides senior={senior} decisions={decisions} pack={pack} />
        )}

        {activeTab === 'mandate' && (
          <MandateLimits mandate={mandate} senior={senior} />
        )}

        {activeTab === 'inbox' && (packId === 'vendor' ? (
          <RequestInbox
            requests={requests}
            onSelectRequest={(id) => setSelectedRequestId(id)}
            selectedRequestId={selectedRequestId}
            onRunDecision={(req) => runDecisionAnalysis(req, true)}
            isAnalyzing={isAnalyzing}
          />
        ) : (
          <PackInbox
            pack={pack}
            senior={senior}
            requests={requests}
            onSelectRequest={(id) => setSelectedRequestId(id)}
            selectedRequestId={selectedRequestId}
            onRunDecision={(req) => runDecisionAnalysis(req, true)}
            isAnalyzing={isAnalyzing}
          />
        ))}

        {activeTab === 'record' && (
          <DecisionRecord
            verdict={currentVerdict}
            request={activeRequest}
            pack={pack}
            senior={senior}
            onRecordOverride={handleRecordOverride}
            overrideSuccess={overrideSuccess}
            onRerun={(req) => runDecisionAnalysis(req, false, false)}
            onResetDemo={handleResetDemo}
            isAnalyzing={isAnalyzing}
          />
        )}

        {activeTab === 'backtest' && (
          <BacktestDashboard backtestData={backtestData} pack={pack} senior={senior} />
        )}
      </main>

      <PitchModal
        isOpen={isPitchOpen}
        onClose={() => setIsPitchOpen(false)}
      />

      <footer style={{ borderTop: '1px solid var(--border-color)', paddingTop: 'var(--space-5)', marginTop: 'var(--space-7)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-4)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
        <div>
          <strong>Pratibimb</strong> · Google Cloud AI Builder Cup 2026 (JAPAC) · Team: Rahul Rao & Dipti CA
        </div>
        <div>
          Meridian Global Services is fictional · All data is synthetic · Gemini 3.8 Flash on Vertex AI
        </div>
      </footer>
    </div>
  );
}
