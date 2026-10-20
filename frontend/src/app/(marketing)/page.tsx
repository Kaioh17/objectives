import Link from "next/link";
import { siteConfig } from "@/config/site";

const MODES = [
  {
    mode: "daily",
    label: "Daily",
    text: "Small wins you can finish today. Pick a time and it lands on your calendar.",
  },
  {
    mode: "weekly",
    label: "Weekly",
    text: "The few things that make the week count, kept apart from the daily noise.",
  },
  {
    mode: "monthly",
    label: "Monthly",
    text: "Bigger goals with room to breathe, scheduled before the month gets away.",
  },
] as const;

export default function LandingPage() {
  return (
    <>
      <section className="hero" aria-labelledby="hero-title">
        <p className="mono eyebrow">Daily · Weekly · Monthly</p>
        <h1 id="hero-title">Decide what matters. Put it on your calendar.</h1>
        <p className="lede">
          Objectives keeps your goals in one quiet place, then schedules each one on Google Calendar
          with a click.
        </p>
        <div className="hero-actions">
          <Link className="btn" href={`${siteConfig.appUrl}/signup`}>
            Get Started
          </Link>
          <Link className="btn btn-quiet" href={`${siteConfig.appUrl}/login`}>
            Log In
          </Link>
        </div>
      </section>

      <section className="band" aria-labelledby="modes-heading">
        <div className="panel-head">
          <h2 id="modes-heading">One Place, Three Rhythms</h2>
        </div>
        <ul className="mode-list">
          {MODES.map((m) => (
            <li key={m.mode} className="mode-cell">
              <p className="mode mono" data-mode={m.mode}>
                {m.label}
              </p>
              <p className="mode-text">{m.text}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="band cta-band" aria-labelledby="cta-title">
        <h2 id="cta-title">Ready When You Are</h2>
        <p className="lede">Create a free account and write down your first objective.</p>
        <Link className="btn" href={`${siteConfig.appUrl}/signup`}>
          Create Account
        </Link>
      </section>
    </>
  );
}
