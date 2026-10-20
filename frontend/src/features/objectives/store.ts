import { useSyncExternalStore } from "react";
import { z } from "zod";
import { apiFetch, SIGNED_OUT_EVENT } from "@/lib/api-client";
import { apiObjectiveSchema, type Objective, type ObjectiveInput } from "./types";

// The backend is the source of truth; this is a client cache of the signed-in user's objectives.
// Every mutation waits for the API and then stores what it returned, so the UI never shows
// something the server rejected. Mutations reject on failure so the caller can say why.
const listeners = new Set<() => void>();
let state: Objective[] | null = null;

function set(next: Objective[] | null) {
  state = next;
  listeners.forEach((listener) => listener());
}

// One user's data must never show for the next: drop the cache whenever the session ends
if (typeof window !== "undefined") window.addEventListener(SIGNED_OUT_EVENT, () => set(null));

const replace = (next: Objective) => set((state ?? []).map((o) => (o.id === next.id ? next : o)));

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

// null until the first load finishes, and on the server, so the first client render matches it
export const useObjectives = (): Objective[] | null =>
  useSyncExternalStore(
    subscribe,
    () => state,
    () => null,
  );

export const objectives = {
  async load() {
    set(z.array(apiObjectiveSchema).parse(await apiFetch("/objectives")));
  },
  async add(input: ObjectiveInput) {
    const created = apiObjectiveSchema.parse(
      await apiFetch("/objectives", { method: "POST", json: input }),
    );
    set([created, ...(state ?? [])]);
  },
  async update(id: string, patch: Partial<ObjectiveInput & { archived: boolean }>) {
    replace(
      apiObjectiveSchema.parse(
        await apiFetch(`/objectives/${id}`, { method: "PATCH", json: patch }),
      ),
    );
  },
  async remove(id: string) {
    await apiFetch(`/objectives/${id}`, { method: "DELETE" });
    set((state ?? []).filter((o) => o.id !== id));
  },
  // Creates the Google Calendar event, or moves it if the objective already has one
  async schedule(id: string, start: Date, minutes: number) {
    replace(
      apiObjectiveSchema.parse(
        await apiFetch(`/objectives/${id}/schedule`, {
          method: "POST",
          json: { start: start.toISOString(), minutes },
        }),
      ),
    );
  },
};
