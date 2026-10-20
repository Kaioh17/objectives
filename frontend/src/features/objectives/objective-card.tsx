"use client";

import { useState, type CSSProperties } from "react";
import { formatMinutes, formatWhen } from "./format";
import { ObjectiveForm } from "./objective-form";
import { PanelDialog } from "./panel-dialog";
import { ScheduleDialog } from "./schedule-dialog";
import { objectives } from "./store";
import { MODE_LABEL, type Objective } from "./types";

export function ObjectiveCard({ objective, index }: { objective: Objective; index: number }) {
  const [scheduling, setScheduling] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [editing, setEditing] = useState(false);
  const { id, title, description, minutes, mode, archived, event } = objective;

  return (
    <li className="objective reveal" style={{ "--index": Math.min(index, 8) } as CSSProperties}>
      <div className="objective-body">
        <h3 className="objective-title">{title}</h3>
        {description && <p className="objective-desc">{description}</p>}
        {event && (
          <p className="objective-when mono">
            Scheduled <time dateTime={event.start}>{formatWhen(event.start)}</time>
          </p>
        )}
      </div>

      <div className="objective-foot">
        {confirming ? (
          <>
            <span className="foot-cell">Delete forever?</span>
            <button
              type="button"
              className="foot-cell foot-end"
              autoFocus
              onClick={() => setConfirming(false)}
            >
              Cancel
            </button>
            <button
              type="button"
              className="foot-cell foot-danger"
              aria-label={`Confirm delete ${title}`}
              onClick={() => objectives.remove(id)}
            >
              Delete
            </button>
          </>
        ) : (
          <>
            <span className="foot-cell mode mono" data-mode={mode}>
              {MODE_LABEL[mode]}
            </span>
            <span className="foot-cell mono">{formatMinutes(minutes)}</span>
            {archived ? (
              <>
                <button
                  type="button"
                  className="foot-cell foot-end"
                  aria-label={`Restore ${title}`}
                  onClick={() => objectives.update(id, { archived: false })}
                >
                  Restore
                </button>
                <button
                  type="button"
                  className="foot-cell foot-danger"
                  aria-label={`Delete ${title}`}
                  onClick={() => setConfirming(true)}
                >
                  Delete
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  className="foot-cell foot-stretch"
                  aria-haspopup="dialog"
                  aria-label={`${event ? "Reschedule" : "Schedule"} ${title}`}
                  onClick={() => setScheduling(true)}
                >
                  {event ? "Reschedule" : "Schedule"}
                </button>
                <button
                  type="button"
                  className="foot-cell foot-end"
                  aria-haspopup="dialog"
                  aria-label={`Edit ${title}`}
                  onClick={() => setEditing(true)}
                >
                  Edit
                </button>
                <button
                  type="button"
                  className="foot-cell"
                  aria-label={`Archive ${title}`}
                  onClick={() => objectives.update(id, { archived: true })}
                >
                  Archive
                </button>
              </>
            )}
          </>
        )}
      </div>

      {editing && (
        <PanelDialog label={`Edit ${title}`} onClose={() => setEditing(false)}>
          <ObjectiveForm objective={objective} onSaved={() => setEditing(false)} />
        </PanelDialog>
      )}
      {scheduling && <ScheduleDialog objective={objective} onClose={() => setScheduling(false)} />}
    </li>
  );
}

export function ObjectiveList({ items }: { items: Objective[] }) {
  return (
    <ul className="objective-list">
      {items.map((objective, index) => (
        <ObjectiveCard key={objective.id} objective={objective} index={index} />
      ))}
    </ul>
  );
}
