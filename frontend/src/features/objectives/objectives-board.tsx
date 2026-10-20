"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { useMediaQuery } from "@/hooks/use-media-query";
import { ModeGroups } from "./mode-groups";
import { ObjectiveForm } from "./objective-form";
import { PanelDialog } from "./panel-dialog";
import { objectives, useObjectives } from "./store";

// Below this width the board is one column: the form and archive move into popups behind the dock
const SMALL = "(max-width: 63.99rem)";

function Icon({ children }: { children: ReactNode }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

export function ObjectivesBoard() {
  const all = useObjectives();
  const small = useMediaQuery(SMALL);
  const [panel, setPanel] = useState<"new" | "archive" | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);
  const active = all?.filter((o) => !o.archived);
  const archived = all?.filter((o) => o.archived);

  const load = useCallback(() => {
    objectives.load().catch(() => setLoadFailed(true));
  }, []);
  useEffect(load, [load]);

  const loading = (
    <p className="panel-empty" role="status">
      Loading…
    </p>
  );
  // Loading only means "no data yet"; once a load fails the retry takes its place
  const retry = (
    <div className="panel-empty" role="alert">
      <p>Could not load your objectives.</p>
      <button
        type="button"
        onClick={() => {
          setLoadFailed(false);
          load();
        }}
      >
        Try Again
      </button>
    </div>
  );

  const archiveCard = (
    <section className="archive-panel" aria-labelledby="archive-heading">
      <div className="panel-head">
        <h2 id="archive-heading">Archive</h2>
        <span className="mono meta">{archived?.length ?? ""}</span>
      </div>
      {!archived ? (
        loadFailed ? (
          <p className="panel-empty">Could not load.</p>
        ) : (
          loading
        )
      ) : archived.length === 0 ? (
        <p className="panel-empty">Archived objectives appear here.</p>
      ) : (
        <ModeGroups items={archived} />
      )}
    </section>
  );

  return (
    <div className="board">
      {!small && <ObjectiveForm />}

      <div className="board-list">
        {!active ? (
          loadFailed ? (
            retry
          ) : (
            loading
          )
        ) : active.length === 0 ? (
          <>
            <div className="panel-head">
              <h2>Nothing yet</h2>
            </div>
            <p className="panel-empty">
              Add your first objective with {small ? "the New objective button" : "the form"}.
              Archived ones move to the Archive {small ? "button" : "panel"}.
            </p>
          </>
        ) : (
          <ModeGroups items={active} />
        )}
      </div>

      {!small && archiveCard}

      {small && (
        <>
          <nav aria-label="Quick actions" className="dock">
            <button type="button" onClick={() => setPanel("new")}>
              <Icon>
                <path d="M12 5v14M5 12h14" />
              </Icon>
              New objective
            </button>
            <button type="button" className="btn-quiet" onClick={() => setPanel("archive")}>
              <Icon>
                <rect x="3" y="4" width="18" height="4" rx="1" />
                <path d="M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8M10 12h4" />
              </Icon>
              Archive
            </button>
          </nav>

          {panel && (
            <PanelDialog
              label={panel === "new" ? "New objective" : "Archive"}
              onClose={() => setPanel(null)}
            >
              {panel === "new" ? <ObjectiveForm onSaved={() => setPanel(null)} /> : archiveCard}
            </PanelDialog>
          )}
        </>
      )}
    </div>
  );
}
