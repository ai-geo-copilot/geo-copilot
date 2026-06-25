"use client";

import { useEffect, useState } from "react";

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 80);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header className={`nav${scrolled ? " nav--scrolled" : ""}`}>
      <div className="nav__inner">
        <a href="#" className="nav__logo">
          GEO<span>Copilot</span>
        </a>
        <nav className="nav__links">
          <a href="#capabilities">诊断能力</a>
          <a href="#workflow">工作流</a>
          <a href="#faq">常见问题</a>
          <a
            href="#analysis-section"
            className="btn btn--primary"
            style={{ padding: "0.4rem 1rem", fontSize: "0.8rem", color: "#fff" }}
            onClick={(e) => {
              e.preventDefault();
              document.getElementById("analysis-section")?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            查看演示
          </a>
        </nav>
        <button
          className="nav__hamburger"
          aria-label="菜单"
          onClick={() => setMobileOpen((v) => !v)}
        >
          <span />
          <span />
          <span />
        </button>
      </div>
      <div className={`nav__mobile${mobileOpen ? " nav__mobile--open" : ""}`}>
        <a href="#capabilities" onClick={() => setMobileOpen(false)}>诊断能力</a>
        <a href="#workflow" onClick={() => setMobileOpen(false)}>工作流</a>
        <a href="#faq" onClick={() => setMobileOpen(false)}>常见问题</a>
        <a
          href="#analysis-section"
          onClick={(e) => {
            e.preventDefault();
            setMobileOpen(false);
            document.getElementById("analysis-section")?.scrollIntoView({ behavior: "smooth" });
          }}
        >
          查看演示
        </a>
      </div>
    </header>
  );
}
