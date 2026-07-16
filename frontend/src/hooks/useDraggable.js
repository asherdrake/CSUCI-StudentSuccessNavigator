import { useState, useRef, useEffect } from 'react';

/**
 * Drag physics for the floating chat bubble (mouse + touch), with
 * click-vs-drag detection and window-resize clamping.
 *
 * @param {() => void} onClick  Called when the interaction was a click
 *                              (moved < 6px and released within 300ms).
 * @returns {{ pos: {x: number, y: number}, handlers: object }}
 */
export function useDraggable(onClick) {
  const [pos, setPos] = useState({
    x: window.innerWidth - 90,
    y: window.innerHeight - 90
  });
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const bubbleStart = useRef({ x: 0, y: 0 });
  const clickStart = useRef(0); // Timestamp to distinguish click vs drag

  // Adjust coordinates if window is resized
  useEffect(() => {
    const handleResize = () => {
      setPos((prev) => ({
        x: Math.min(prev.x, window.innerWidth - 80),
        y: Math.min(prev.y, window.innerHeight - 80)
      }));
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const begin = (clientX, clientY) => {
    setIsDragging(true);
    clickStart.current = Date.now();
    dragStart.current = { x: clientX, y: clientY };
    bubbleStart.current = { x: pos.x, y: pos.y };
  };

  const move = (clientX, clientY) => {
    if (!isDragging) return;
    const deltaX = clientX - dragStart.current.x;
    const deltaY = clientY - dragStart.current.y;

    const newX = Math.max(10, Math.min(bubbleStart.current.x + deltaX, window.innerWidth - 74));
    const newY = Math.max(80, Math.min(bubbleStart.current.y + deltaY, window.innerHeight - 74));

    setPos({ x: newX, y: newY });
  };

  const end = (clientX, clientY) => {
    setIsDragging(false);
    const duration = Date.now() - clickStart.current;
    const distance = Math.hypot(clientX - dragStart.current.x, clientY - dragStart.current.y);

    if (distance < 6 && duration < 300) {
      onClick();
    }
  };

  const handlers = {
    onMouseDown: (e) => {
      if (e.button !== 0) return;
      begin(e.clientX, e.clientY);
    },
    onMouseMove: (e) => move(e.clientX, e.clientY),
    onMouseUp: (e) => end(e.clientX, e.clientY),
    onTouchStart: (e) => {
      const touch = e.touches[0];
      begin(touch.clientX, touch.clientY);
    },
    onTouchMove: (e) => {
      const touch = e.touches[0];
      move(touch.clientX, touch.clientY);
    },
    onTouchEnd: (e) => {
      const touch = e.changedTouches[0];
      end(touch.clientX, touch.clientY);
    }
  };

  return { pos, handlers };
}
