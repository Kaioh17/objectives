import { useSyncExternalStore } from "react";
import { z } from "zod";
import { objectiveSchema, type Objective, type ObjectiveInput } from "./types";

// ponytail: localStorage stands in for the backend. Replace the bodies of `objectives` and
// `useObjectives` with apiFetch calls; components only depend on those two exports.
const KEY = "objectives:v1";
const listeners = new Set<() => void>();
let state: Objective[] | null = null;

// Stored data is untrusted: anything that fails the schema is dropped, never rendered
export function parseObjectives(raw: string | null): Objective[] {
  if (!raw) return [];
  try {
    const result = z.array(objectiveSchema).safeParse(JSON.parse(raw));
    return result.success ? result.data : [];
  } catch {
    return [];
  }
}

function load(): Objective[] {
  try {
    return parseObjectives(localStorage.getItem(KEY));
  } catch {
    return [];
  }
}

const current = () => (state ??= load());

function commit(next: Objective[]) {
  state = next;
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    // Storage blocked or full: the session still works from memory
  }
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  const onStorage = (event: StorageEvent) => {
    if (event.key !== KEY) return;
    state = load();
    listener();
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", onStorage);
  };
}

// null on the server and during hydration, so the first client render matches the server
export const useObjectives = (): Objective[] | null =>
  useSyncExternalStore(subscribe, current, () => null);

export const objectives = {
  add(input: ObjectiveInput) {
    // Not crypto.randomUUID: it is missing on plain-http LAN origins (testing from a phone)
    const id = `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;
    commit([
      { ...input, id, archived: false, createdAt: new Date().toISOString(), event: null },
      ...current(),
    ]);
  },
  update(id: string, patch: Partial<Omit<Objective, "id" | "createdAt">>) {
    commit(current().map((o) => (o.id === id ? { ...o, ...patch } : o)));
  },
  remove(id: string) {
    commit(current().filter((o) => o.id !== id));
  },
};
