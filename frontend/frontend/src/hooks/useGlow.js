// src/hooks/useGlow.js — a cursor-lit highlight for one surface (the hero).
// The element gets --mx/--my percentages that CSS turns into a radial light.
// Deliberately narrow: pointer-fine devices only, rAF-throttled to one write per
// frame, and it never runs at all under prefers-reduced-motion.
import { useRef } from 'react';

export function useGlow() {
  const s = useRef({ node: null, raf: 0, x: 0, y: 0 });

  if (!s.current.move) {
    s.current.move = () => {
      const st = s.current;
      if (!st.node || st.raf) return;
      st.raf = requestAnimationFrame(() => {
        st.raf = 0;
        const r = st.node.getBoundingClientRect();
        if (!r.width || !r.height) return;
        st.node.style.setProperty('--mx', `${(((st.x - r.left) / r.width) * 100).toFixed(1)}%`);
        st.node.style.setProperty('--my', `${(((st.y - r.top) / r.height) * 100).toFixed(1)}%`);
      });
    };
  }

  const allowed = () => {
    if (typeof window === 'undefined' || !window.matchMedia) return false;
    return window.matchMedia('(hover: hover) and (pointer: fine)').matches
      && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  };

  // used as a callback ref, so it also fires when the hero mounts after loading
  return (node) => {
    const st = s.current;
    if (st.node && st.node !== node) {
      st.node.removeEventListener('pointermove', st.move);
      st.node.removeEventListener('pointerleave', st.move);
      st.node.style.removeProperty('--mx');
      st.node.style.removeProperty('--my');
      st.node = null;
    }
    if (node && allowed()) {
      st.node = node;
      node.addEventListener('pointermove', st.move);
      node.addEventListener('pointerleave', st.move);
    }
  };
}

export default useGlow;
