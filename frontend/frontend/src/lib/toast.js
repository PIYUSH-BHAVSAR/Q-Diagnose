// src/lib/toast.js — 20-line toast store (no context boilerplate, no library)
const listeners = new Set();
let seq = 0;
const queue = [];

export function toast(title, body, kind = 'info', ms = 4200) {
  const id = ++seq;
  queue.push({ id, title, body, kind });
  listeners.forEach((f) => f([...queue]));
  if (ms) setTimeout(() => dismiss(id), ms);
  return id;
}
export function dismiss(id) {
  const i = queue.findIndex((t) => t.id === id);
  if (i >= 0) queue.splice(i, 1);
  listeners.forEach((f) => f([...queue]));
}
export function subscribe(fn) {
  listeners.add(fn);
  fn([...queue]);
  return () => listeners.delete(fn);
}
