const NBSP = " ";

export function formatMinutes(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (!hours) return `${rest}${NBSP}min`;
  return rest ? `${hours}${NBSP}h ${rest}${NBSP}min` : `${hours}${NBSP}h`;
}

const when = new Intl.DateTimeFormat(undefined, {
  weekday: "short",
  day: "numeric",
  month: "short",
  hour: "numeric",
  minute: "2-digit",
});

export const formatWhen = (iso: string): string => when.format(new Date(iso));

const time = new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" });

export const formatTime = (iso: string): string => time.format(new Date(iso));
