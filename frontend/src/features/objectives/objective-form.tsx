"use client";

import { useId, useState, type FormEvent } from "react";
import { objectives } from "./store";
import { MODES, MODE_LABEL, objectiveInputSchema, type Objective } from "./types";

const DEFAULT_MINUTES = 30;
const TIME_OPTIONS = [
  { minutes: 30, label: "30 mins" },
  { minutes: 60, label: "1 hr" },
  { minutes: 120, label: "2 hrs" },
];

type Errors = Partial<Record<"title" | "description" | "minutes", string>>;

const isPreset = (minutes: number) => TIME_OPTIONS.some((o) => o.minutes === minutes);

// Creates a new objective, or edits `objective` in place when one is passed
export function ObjectiveForm({
  objective,
  onSaved,
}: {
  objective?: Objective;
  onSaved?: () => void;
}) {
  // Prefixed ids: the inline form, the phone sheet and an edit dialog can be mounted together
  const uid = useId();
  const [errors, setErrors] = useState<Errors>({});
  const [saved, setSaved] = useState("");
  // A typed custom time wins over the preset; picking a preset clears it
  const [preset, setPreset] = useState(
    objective && isPreset(objective.minutes) ? objective.minutes : DEFAULT_MINUTES,
  );
  const [custom, setCustom] = useState(
    objective && !isPreset(objective.minutes) ? String(objective.minutes) : "",
  );

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const result = objectiveInputSchema.safeParse({
      title: data.get("title") ?? "",
      description: data.get("description") ?? "",
      minutes: custom.trim() ? Number(custom) : preset,
      mode: data.get("mode"),
    });

    if (!result.success) {
      const next: Errors = {};
      for (const issue of result.error.issues) {
        const field = issue.path[0] as keyof Errors;
        next[field] ??= issue.message;
      }
      setErrors(next);
      setSaved("");
      const first = (["title", "description", "minutes"] as const).find((f) => next[f]);
      (
        form.elements.namedItem(
          first === "minutes" ? "custom" : (first ?? "title"),
        ) as HTMLElement | null
      )?.focus();
      return;
    }

    if (objective) {
      objectives.update(objective.id, result.data);
      onSaved?.();
      return;
    }

    objectives.add(result.data);
    setErrors({});
    setSaved(`Saved “${result.data.title}”.`);
    form.reset();
    setPreset(DEFAULT_MINUTES);
    setCustom("");
    (form.elements.namedItem("title") as HTMLElement | null)?.focus();
    onSaved?.();
  }

  return (
    <section className="form-panel" aria-labelledby={`${uid}-heading`}>
      <div className="panel-head">
        <h2 id={`${uid}-heading`}>{objective ? "Edit objective" : "New objective"}</h2>
      </div>
      <form onSubmit={onSubmit} noValidate>
        <div className="field">
          <label htmlFor={`${uid}-title`}>Title</label>
          <input
            id={`${uid}-title`}
            className="input"
            name="title"
            type="text"
            defaultValue={objective?.title}
            maxLength={120}
            autoComplete="off"
            placeholder="Read for 20 pages…"
            aria-invalid={errors.title ? true : undefined}
            aria-describedby={errors.title ? `${uid}-title-error` : undefined}
          />
          {errors.title && (
            <p className="error" id={`${uid}-title-error`}>
              {errors.title}
            </p>
          )}
        </div>

        <div className="field">
          <label htmlFor={`${uid}-description`}>Description</label>
          <textarea
            id={`${uid}-description`}
            className="input"
            name="description"
            rows={3}
            defaultValue={objective?.description}
            maxLength={500}
            autoComplete="off"
            placeholder="Why it matters, or what done looks like…"
            aria-invalid={errors.description ? true : undefined}
            aria-describedby={errors.description ? `${uid}-description-error` : undefined}
          />
          {errors.description && (
            <p className="error" id={`${uid}-description-error`}>
              {errors.description}
            </p>
          )}
        </div>

        <fieldset className="field field-set">
          <legend>Time to spend</legend>
          <div className="segmented">
            {TIME_OPTIONS.map(({ minutes, label }) => (
              <label key={minutes}>
                <input
                  type="radio"
                  name="preset"
                  value={minutes}
                  checked={!custom.trim() && preset === minutes}
                  onChange={() => {
                    setPreset(minutes);
                    setCustom("");
                  }}
                />
                {label}
              </label>
            ))}
          </div>
          <div className="field-custom">
            <label htmlFor={`${uid}-custom`}>Or custom (minutes)</label>
            <input
              id={`${uid}-custom`}
              className="input"
              name="custom"
              type="number"
              inputMode="numeric"
              min={5}
              max={1440}
              step={5}
              autoComplete="off"
              placeholder="45"
              value={custom}
              onChange={(event) => setCustom(event.target.value)}
              aria-invalid={errors.minutes ? true : undefined}
              aria-describedby={errors.minutes ? `${uid}-minutes-error` : undefined}
            />
            {errors.minutes && (
              <p className="error" id={`${uid}-minutes-error`}>
                {errors.minutes}
              </p>
            )}
          </div>
        </fieldset>

        <fieldset className="field field-set">
          <legend>Objective mode</legend>
          <div className="segmented">
            {MODES.map((mode) => (
              <label key={mode}>
                <input
                  type="radio"
                  name="mode"
                  value={mode}
                  defaultChecked={mode === (objective?.mode ?? "daily")}
                />
                {MODE_LABEL[mode]}
              </label>
            ))}
          </div>
        </fieldset>

        <p className="meta form-status" role="status" aria-live="polite">
          {saved}
        </p>
        <button type="submit" className="btn-bar">
          {objective ? "Save changes" : "Save objective"}
          <span className="key-hint" aria-hidden="true">
            ↵
          </span>
        </button>
      </form>
    </section>
  );
}
