import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { NavLink, Route, Routes } from 'react-router-dom';
import ForecastPage from '@/pages/ForecastPage';
import DiagnosticPage from '@/pages/DiagnosticPage';
import ValidationPage from '@/pages/ValidationPage';
export default function App() {
    return (_jsxs("div", { className: "min-h-screen", children: [_jsx("nav", { className: "border-b border-white/5", children: _jsxs("div", { className: "max-w-6xl mx-auto px-6 py-5 flex items-center justify-between", children: [_jsxs("div", { className: "font-serif text-xl text-chalk", children: [_jsx("span", { className: "text-accent", children: "\u223F" }), " bess.forecast"] }), _jsxs("div", { className: "flex gap-8 text-sm font-mono", children: [_jsx(NavLink, { to: "/", end: true, className: ({ isActive }) => `nav-link ${isActive ? 'active' : ''}`, children: "forecast" }), _jsx(NavLink, { to: "/validation", className: ({ isActive }) => `nav-link ${isActive ? 'active' : ''}`, children: "validation" }), _jsx(NavLink, { to: "/diagnostic", className: ({ isActive }) => `nav-link ${isActive ? 'active' : ''}`, children: "diagnostic" })] })] }) }), _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: _jsx(ForecastPage, {}) }), _jsx(Route, { path: "/validation", element: _jsx(ValidationPage, {}) }), _jsx(Route, { path: "/diagnostic", element: _jsx(DiagnosticPage, {}) })] })] }));
}
