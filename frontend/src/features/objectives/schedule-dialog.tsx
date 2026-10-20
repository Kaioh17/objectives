"use client";

import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { googleStartUrl } from "@/features/auth/api";
import { listCalendarEvents, type ScheduleItem } from "@/features/calendar/api";
import { ApiError } from "@/lib/api-client";
import { formatTime } from "./format";
import { objectives } from "./store";
import type { Objective } from "./types";

const pad = (n: number) => String(n).padStart(2, "0");
const toDateValue = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const toTimeValue = (d: Date) => `${pad(d.getHours())}:${pad(d.getMinutes())}`;

function nextHour() {
  const d = new Date();
  d.setHours(d.getHours() + 1, 0, 0, 0);
  return d;
}

// Rendered only after a click, so reading the clock here cannot cause a hydration mismatch
export function ScheduleDialog({
  objective,
  onClose,
}: {
  objective: Objective;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [start] = useState(() => (objective.event ? new Date(objective.event.start) : nextHour()));
  const [date, setDate] = useState(() => toDateValue(start));
  // "connect": the user has not linked Google Calendar yet (the API answers 409)
  const [schedule, setSchedule] = useState<{
    date: string;
    items: ScheduleItem[];
    problem: "connect" | "failed" | null;
  } | null>(null);
  const [minutes] = useState(() =>
    objective.event
      ? Math.round(
          (new Date(objective.event.end).getTime() - new Date(objective.event.start).getTime()) /
            60_000,
        )
      : objective.minutes,
  );

  useEffect(() => {
    const dialog = ref.current;
    if (dialog && !dialog.open) dialog.showModal();
  }, []);

  useEffect(() => {
    let stale = false;
    listCalendarEvents(date)
      .then((items) => !stale && setSchedule({ date, items, problem: null }))
      .catch((err) => {
        const problem = err instanceof ApiError && err.status === 409 ? "connect" : "failed";
        if (!stale) setSchedule({ date, items: [], problem });
      });
    return () => {
      stale = true;
    };
  }, [date]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const startAt = new Date(`${data.get("date")}T${data.get("time")}`);
    const duration = Number(data.get("minutes"));

    if (Number.isNaN(startAt.getTime())) return setError("Pick a date and a start time.");
    if (startAt < new Date()) return setError("Pick a start time in the future.");
    if (!Number.isInteger(duration) || duration < 5 || duration > 1440)
      return setError("Enter a duration between 5 and 1,440 minutes.");

    setError(null);
    setPending(true);
    try {
      await objectives.schedule(objective.id, startAt, duration);
      ref.current?.close();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setSchedule((current) => current && { ...current, problem: "connect" });
        setError(null);
      } else {
        setError("Could not reach Google Calendar. Try again.");
      }
      setPending(false);
    }
  }

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onClose={onClose}
      onClick={(event) => event.target === event.currentTarget && ref.current?.close()}
    >
      <form onSubmit={onSubmit} noValidate>
        <div className="panel-head">
          <h2 id={titleId}>Schedule on Google Calendar</h2>
        </div>
        <div className="dialog-intro">
          <p className="dialog-objective">{objective.title}</p>
          {objective.description && <p className="dialog-description">{objective.description}</p>}
        </div>

        <div className="field-row">
          <div className="field">
            <label htmlFor={`${titleId}-date`}>Date</label>
            <input
              id={`${titleId}-date`}
              className="input"
              type="date"
              name="date"
              required
              min={toDateValue(new Date())}
              value={date}
              onChange={(event) => setDate(event.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor={`${titleId}-time`}>Start time</label>
            <input
              id={`${titleId}-time`}
              className="input"
              type="time"
              name="time"
              required
              defaultValue={toTimeValue(start)}
            />
          </div>
        </div>

        <div className="field">
          <label htmlFor={`${titleId}-minutes`}>Duration (minutes)</label>
          <input
            id={`${titleId}-minutes`}
            className="input"
            type="number"
            name="minutes"
            inputMode="numeric"
            min={5}
            max={1440}
            step={5}
            autoComplete="off"
            defaultValue={minutes}
          />
        </div>

        <section className="dialog-section" aria-labelledby={`${titleId}-schedule`}>
          <h3 id={`${titleId}-schedule`} className="meta">
            Your schedule on {date}
          </h3>
          {schedule?.date !== date ? (
            <p className="meta" role="status">
              Loading…
            </p>
          ) : schedule.problem === "connect" ? (
            <p className="meta">
              Connect Google Calendar to see your schedule and add this objective.{" "}
              <a href={googleStartUrl()}>Connect Google Calendar</a>
            </p>
          ) : schedule.problem === "failed" ? (
            <p className="meta">Could not load your schedule.</p>
          ) : schedule.items.length === 0 ? (
            <p className="meta">Nothing scheduled. You are free all day.</p>
          ) : (
            <ul className="schedule-list">
              {schedule.items.map((item) => (
                <li key={item.id}>
                  <time dateTime={item.start}>{formatTime(item.start)}</time> to{" "}
                  <time dateTime={item.end}>{formatTime(item.end)}</time> {item.title}
                </li>
              ))}
            </ul>
          )}
        </section>

        {error && (
          <p className="error dialog-note" role="alert">
            {error}
          </p>
        )}

        <div className="dialog-actions">
          <button type="button" className="btn-quiet" onClick={() => ref.current?.close()}>
            Cancel
          </button>
          <button type="submit" disabled={pending || schedule?.problem === "connect"}>
            {pending ? "Adding…" : objective.event ? "Reschedule" : "Add to calendar"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
