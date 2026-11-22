import { Link, Route, Routes, useLocation } from "react-router-dom";
import CustomerPage from "./pages/CustomerPage";
import TeamPage from "./pages/TeamPage";

export default function App() {
  const { pathname } = useLocation();
  return (
    <div className="shell">
      <div className="bg-orb orb-a" />
      <div className="bg-orb orb-b" />
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="brand-mark">◆</span> Smart<span className="grad">Desk</span>
        </Link>
        <nav>
          <Link className={pathname === "/" ? "active" : ""} to="/">Contact us</Link>
          <Link className={pathname.startsWith("/team") ? "active" : ""} to="/team">Team</Link>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<CustomerPage />} />
        <Route path="/team" element={<TeamPage />} />
        <Route path="*" element={<main className="center-note">Page not found.</main>} />
      </Routes>
    </div>
  );
}
