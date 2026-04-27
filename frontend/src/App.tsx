import { NavLink, Route, Routes } from 'react-router-dom';
import ForecastPage from '@/pages/ForecastPage';
import DiagnosticPage from '@/pages/DiagnosticPage';
import ValidationPage from '@/pages/ValidationPage';

export default function App() {
  return (
    <div className="min-h-screen">
      <nav className="border-b border-white/5">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="font-serif text-xl text-chalk">
            <span className="text-accent">∿</span> bess.forecast
          </div>
          <div className="flex gap-8 text-sm font-mono">
            <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>forecast</NavLink>
            <NavLink to="/validation" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>validation</NavLink>
            <NavLink to="/diagnostic" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>diagnostic</NavLink>
          </div>
        </div>
      </nav>
      <Routes>
        <Route path="/" element={<ForecastPage />} />
        <Route path="/validation" element={<ValidationPage />} />
        <Route path="/diagnostic" element={<DiagnosticPage />} />
      </Routes>
    </div>
  );
}
