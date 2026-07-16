import React from 'react';

// Color palette mapping
const COLORS = {
  'D': '#002D62',  // Navy outline / Eye
  'B': '#005A9C',  // Dolphin Body Blue
  'L': '#00B5E2',  // Dolphin Highlights (Teal)
  'W': '#FFFFFF',  // White belly / highlights
  'S': '#A1E3F9',  // Splash Light Blue
  'P': '#E8F9FF',  // Splash White
};

// 24x24 pixel art grids for 5 frames
const FRAMES = [
  // Frame 0: Horizontal Swimming (Prep)
  [
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "..........DDD...........",
    ".........DBBBD..........",
    "......DD.DBBBD..........",
    ".....DBBDBBBBD..........",
    "....DBBBBBBBBDD.........",
    "...DBBBBBBBBBBBD........",
    "..DBBBBBBBBBBBBBD.......",
    ".DBBBBBBDDBBBBBBBD......",
    "DBBBBBBWWWWWWBBBBD......",
    ".DBBBBBWWWWWWBBBD.......",
    "..DDDBBWWWWWWD..........",
    "....DDBWWWWWD...........",
    "......DDWWWDD...........",
    "........DDD.............",
    "........................",
    "........................",
    "....SSSSSSSSSSSSSS......",
    "...SSSSSSSSSSSSSSSS.....",
    "........................"
  ],
  // Frame 1: Leaping Up (Breaking water)
  [
    "........................",
    "........................",
    "........................",
    "..............DD........",
    ".............DBBD.......",
    "............DBBBD.......",
    "...........DBBBBD.......",
    "..........DBBBBD........",
    ".........DBBBBD.........",
    "........DBBBBD..........",
    "......DDBBBBD...........",
    ".....DBBBBBBD...........",
    "....DBBBDDBBD...........",
    "...DBBBWWWBBD...........",
    "..DBBBWWWWWD............",
    "..DBBBWWWWD.............",
    "...DBBWWWD..............",
    "....DBWWD...............",
    ".....DDD................",
    "........................",
    "......SS..SS............",
    "....SSSPSSPSSS..........",
    "...SSSSSSSSSSSS.........",
    "........................"
  ],
  // Frame 2: Apex of the Leap (Highest point)
  [
    "........................",
    "........................",
    "..........DDD...........",
    "........DDBBBDD.........",
    ".......DBBBBBBBD........",
    "......DBBBBBBBBBD.......",
    ".....DBBDDBBBBBBBD......",
    "....DBBBWWWWWWBBBD......",
    "...DBBBWWWWWWWWBD.......",
    "..DBBBWWWWWWWWWD........",
    ".DBBBWWWWWWWWWD.........",
    "DBBBWWWWWWWWDD..........",
    "DDBBWWWWWDDD............",
    ".DDWWWWDDD..............",
    "..DDDDD.................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "....SS........SS........",
    "...SSS........SSS......."
  ],
  // Frame 3: Diving Down (Entering water)
  [
    "........................",
    ".....DDD................",
    "....DBWWD...............",
    "...DBBWWWD..............",
    "..DBBBWWWWD.............",
    "..DBBBWWWWWD............",
    "...DBBBWWWBBD...........",
    "....DBBBDDBBD...........",
    ".....DBBBBBBD...........",
    "......DDBBBBD...........",
    "........DBBBBD..........",
    ".........DBBBBD.........",
    "..........DBBBBD........",
    "...........DBBBBD.......",
    "............DBBBD.......",
    ".............DBBD.......",
    "..............DD........",
    "........................",
    "........................",
    "........................",
    "........................",
    "......SS..SS............",
    "....SSSPSSPSSS..........",
    "...SSSSSSSSSSSS........."
  ],
  // Frame 4: Splashdown (Impact)
  [
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "..........DDD...........",
    ".........DBBBD..........",
    "......DD.DBBBD..........",
    ".....DBBDBBBBD..........",
    "....DBBBBBBBBDD.........",
    "...DBBBBBBBBBBBD........",
    "..DBBBBBBBBBBBBBD.......",
    ".DBBBBBBDDBBBBBBBD......",
    "DBBBBBBWWWWWWBBBBD......",
    ".DBBBBBWWWWWWBBBD.......",
    "..DDDBBWWWWWWD..........",
    "....DDBWWWWWD...P..P....",
    "......DDWWWDD..SPSPS....",
    "..P..P..DDD...SSSSSS....",
    ".SPSPS.......SSSSSSSS...",
    "SSSSSS......SSSSSSSSSS..",
    "SSSSSSS....SSSSSSSSSSSS.",
    "SSSSSSSSSSSSSSSSSSSSSSSS",
    "SSSSSSSSSSSSSSSSSSSSSSSS"
  ]
];

/**
 * Reusable animated pixel-art dolphin loading component.
 * Uses a horizontal SVG sprite sheet translation with steps() timing for smooth looping.
 *
 * @param {Object} props
 * @param {number} props.size - Display width/height in pixels (default 64)
 * @param {number} props.duration - Loop cycle speed in seconds (default 0.75)
 * @param {string} props.className - Optional additional CSS class name
 */
export default function DolphinLoader({ size = 64, duration = 0.75, className = '' }) {
  // Pre-generate rects mapping to avoid runtime overhead
  const rects = [];
  
  FRAMES.forEach((frame, fIdx) => {
    const offsetX = fIdx * 24;
    frame.forEach((row, y) => {
      for (let x = 0; x < row.length; x++) {
        const char = row[x];
        const color = COLORS[char];
        if (color) {
          rects.push(
            <rect
              key={`${fIdx}-${y}-${x}`}
              x={offsetX + x}
              y={y}
              width={1}
              height={1}
              fill={color}
            />
          );
        }
      }
    });
  });

  return (
    <div 
      className={`dolphin-loader-wrapper ${className}`}
      style={{
        width: size,
        height: size,
        overflow: 'hidden',
        display: 'inline-flex',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'transparent',
      }}
    >
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
        style={{
          imageRendering: 'pixelated',
          transform: 'translate3d(0,0,0)', // GPU acceleration hint
        }}
      >
        <style>{`
          @keyframes play-dolphin-sprite {
            from { transform: translateX(0px); }
            to { transform: translateX(-120px); }
          }
          .dolphin-sprite-sheet {
            animation: play-dolphin-sprite ${duration}s steps(5) infinite;
          }
        `}</style>
        <g className="dolphin-sprite-sheet">
          {rects}
        </g>
      </svg>
    </div>
  );
}
