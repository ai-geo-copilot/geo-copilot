"use client";

import { useState } from "react";
import { faq } from "../../mocks/landing-data";

export function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section className="section" id="faq">
      <div className="container">
        <div className="section-header">
          <p className="section-label">FAQ</p>
          <h2 className="section-title">常见问题</h2>
        </div>
        <dl className="faq">
          {faq.map((item, i) => {
            const isOpen = openIndex === i;
            return (
              <div className={`faq-item${isOpen ? " faq-item--open" : ""}`} key={i}>
                <dt
                  className="faq-item__question"
                  onClick={() => setOpenIndex(isOpen ? null : i)}
                  aria-expanded={isOpen}
                >
                  <span>{item.q}</span>
                  <svg className="faq-item__chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="m6 9 6 6 6-6" />
                  </svg>
                </dt>
                <dd className={`faq-item__answer${isOpen ? " faq-item__answer--open" : ""}`}>
                  <div className="faq-item__answer-inner">{item.a}</div>
                </dd>
              </div>
            );
          })}
        </dl>
      </div>
    </section>
  );
}
