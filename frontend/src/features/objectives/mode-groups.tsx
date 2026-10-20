import type { CSSProperties } from "react";
import daily from "@/assets/group-daily.jpg";
import weekly from "@/assets/group-weekly.jpg";
import { ObjectiveList } from "./objective-card";
import { MODES, MODE_LABEL, type Mode, type Objective } from "./types";

// Header art per mode; monthly stays plain
const ART: Partial<Record<Mode, string>> = { daily: daily.src, weekly: weekly.src };

// Native <details>: collapsible with no JS, keyboard and screen-reader support built in
export function ModeGroups({ items }: { items: Objective[] }) {
  return MODES.map((mode) => {
    const group = items.filter((o) => o.mode === mode);
    if (!group.length) return null;
    return (
      <details key={mode} className="group" open>
        <summary
          className={ART[mode] ? "has-art" : undefined}
          style={ART[mode] ? ({ "--art": `url(${ART[mode]})` } as CSSProperties) : undefined}
        >
          <h2>
            <span className="mode" data-mode={mode}>
              {MODE_LABEL[mode]}
            </span>
            <span className="count">{group.length}</span>
          </h2>
        </summary>
        <ObjectiveList items={group} />
      </details>
    );
  });
}
