import { workflow } from "../../mocks/landing-data";

export function WorkflowSection() {
  return (
    <section className="section" id="workflow">
      <div className="container">
        <div className="section-header">
          <p className="section-label">How It Works</p>
          <h2 className="section-title">诊断工作流</h2>
        </div>
        <div className="stepper">
          {workflow.map((w, i) => (
            <div className="stepper__step" key={i}>
              <div className="stepper__dot" />
              <div className="stepper__line" />
              <h4 className="stepper__step-title">{w.title}</h4>
              <p className="stepper__step-desc">{w.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
