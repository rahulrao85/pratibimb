import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar.jsx';
import HowMeeraDecides from './components/HowMeeraDecides.jsx';
import MandateLimits from './components/MandateLimits.jsx';
import RequestInbox from './components/RequestInbox.jsx';
import DecisionRecord from './components/DecisionRecord.jsx';
import BacktestDashboard from './components/BacktestDashboard.jsx';
import PitchModal from './components/PitchModal.jsx';

export default function App() {
  const [activeTab, setActiveTab] = useState('inbox');
  const [darkMode, setDarkMode] = useState(false);
  const [isPitchOpen, setIsPitchOpen] = useState(false);

  // Core Data States
  const [senior, setSenior] = useState(null);
  const [mandate, setMandate] = useState(null);
  const [decisions, setDecisions] = useState([]);
  const [requests, setRequests] = useState([]);
  const [selectedRequestId, setSelectedRequestId] = useState('REQ-002'); // Default to Kestrel (the hard case)
  
  // Decision & Analysis States
  const [currentVerdict, setCurrentVerdict] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [overrideSuccess, setOverrideSuccess] = useState(null);

  // Backtest State
  const [backtestData, setBacktestData] = useState(null);
  const [isRunningBacktest, setIsRunningBacktest] = useState(false);

  // Toggle Dark Mode
  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    if (!darkMode) {
      document.body.classList.add('dark-theme');
    } else {
      document.body.classList.remove('dark-theme');
    }
  };

  // Initial Data Fetching from FastAPI
  useEffect(() => {
    fetch('/api/senior')
      .then(r => r.json())
      .then(data => setSenior(data))
      .catch(e => console.log('Senior API error:', e));

    fetch('/api/mandate')
      .then(r => r.json())
      .then(data => setMandate(data))
      .catch(e => console.log('Mandate API error:', e));

    fetch('/api/decisions?include_holdouts=true')
      .then(r => r.json())
      .then(data => setDecisions(data.decisions || []))
      .catch(e => console.log('Decisions API error:', e));

    fetch('/api/requests')
      .then(r => r.json())
      .then(data => {
        const reqList = data.requests || [];
        setRequests(reqList);
        if (reqList.length > 0) {
          // Trigger evaluation on default request (REQ-002: Kestrel)
          const defReq = reqList.find(r => r.id === 'REQ-002') || reqList[0];
          runDecisionAnalysis(defReq, false);
        }
      })
      .catch(e => console.log('Requests API error:', e));

    fetch('/api/backtest')
      .then(r => r.json())
      .then(data => setBacktestData(data))
      .catch(e => console.log('Backtest API error:', e));
  }, []);

  // Run Decision Analysis via Decider API
  const runDecisionAnalysis = async (reqToEvaluate, navigateToRecord = true) => {
    setIsAnalyzing(true);
    setOverrideSuccess(null);
    try {
      const res = await fetch('/api/decide', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reqToEvaluate)
      });
      if (res.ok) {
        const verdictData = await res.json();
        setCurrentVerdict(verdictData);
        if (navigateToRecord) {
          setActiveTab('record');
        }
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
      const res = await fetch('/api/learner/override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setOverrideSuccess(data.lesson);
      }
    } catch (err) {
      console.error('Override recording failed:', err);
    }
  };

  // Re-run Live Back-Test
  const handleRerunBacktest = async () => {
    setIsRunningBacktest(true);
    try {
      const res = await fetch('/api/backtest');
      if (res.ok) {
        const data = await res.json();
        setBacktestData(data);
      }
    } catch (err) {
      console.error('Backtest rerun error:', err);
    } finally {
      setIsRunningBacktest(false);
    }
  };

  const activeRequestObj = requests.find(r => r.id === selectedRequestId);

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        darkMode={darkMode}
        toggleDarkMode={toggleDarkMode}
        onOpenPitch={() => setIsPitchOpen(true)}
      />

      <main style={{ flex: 1, paddingBottom: '3rem' }}>
        {activeTab === 'memory' && (
          <HowMeeraDecides senior={senior} decisions={decisions} />
        )}

        {activeTab === 'mandate' && (
          <MandateLimits mandate={mandate} />
        )}

        {activeTab === 'inbox' && (
          <RequestInbox
            requests={requests}
            onSelectRequest={(id) => setSelectedRequestId(id)}
            selectedRequestId={selectedRequestId}
            onRunDecision={(req) => runDecisionAnalysis(req, true)}
            isAnalyzing={isAnalyzing}
          />
        )}

        {activeTab === 'record' && (
          <DecisionRecord
            verdict={currentVerdict}
            request={activeRequestObj}
            onRecordOverride={handleRecordOverride}
            overrideSuccess={overrideSuccess}
          />
        )}

        {activeTab === 'backtest' && (
          <BacktestDashboard
            backtestData={backtestData}
            onRerunBacktest={handleRerunBacktest}
            isRunning={isRunningBacktest}
          />
        )}
      </main>

      <PitchModal
        isOpen={isPitchOpen}
        onClose={() => setIsPitchOpen(false)}
      />

      <footer style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1.25rem', marginTop: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        <div>
          <strong>Pratibimb</strong> · Google Cloud AI Builder Cup 2026 (JAPAC) · Team: Rahul Rao & Dipti CA
        </div>
        <div>
          Canonical Theme: Voltage / Aurora Glassmorphism · Product Model: Gemini 3.8 Flash
        </div>
      </footer>
    </div>
  );
}
