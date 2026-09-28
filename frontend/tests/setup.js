// vitest setup — jsdom gaps only
if (!window.matchMedia) {
  window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
}
if (!window.scrollTo) window.scrollTo = () => {};
if (!Element.prototype.scrollIntoView) Element.prototype.scrollIntoView = () => {};

// React.lazy route modules are registered eagerly so a chunk never resolves
// mid-test (that produced spurious act() warnings on the first navigation).
await Promise.all(Object.values(import.meta.glob('/src/pages/*.jsx')).map((m) => m()));
