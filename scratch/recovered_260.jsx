import React, { useState, useEffect, useRef } from 'react';

// Color palette mapping based on reference image
const COLORS = {
  'D': '#000000',  // Black outline / Eye
  'B': '#6fa9e9',  // Light blue body
  'T': '#5fa0b0',  // Darker teal back
  'W': '#ffffff',  // White belly highlight
  'S': '#a5f3fc',  // Splash light blue
  'P': '#e0f2fe',  // Splash white/light blue
};

// 24x24 pixel art grids for all animation frames
const FRAMES = [
  // Frame 0: Puddle Idle A (Rippling)
  [
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........SS...SS.........",
    "......SSPPSSPPSS........",
    ".....SPPPPPPPPPPS.......",
    "......SSSSSSSSSS........",
    "........................"
  ],
  // Frame 1: Puddle Idle B (Alternative ripple to feel alive)
  [
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........S.....S.........",
    "......SSPPPPPPPPSS......",
    ".....SPPSSPPSPPSSP......",
    "......SSSSSSSSSS........",
    "........................"
  ],
  // Frame 2: Puddle Bulge / Dolphin snout emerges (Right side)
  [
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "................DD......",
    "...............DTD......",
    "-------------DDTTD......",
    "------------DTTBD.......",
    "-----------DTWBD........",
    "........SS.DDBD.SS......",
    "......SSPPSSDDSSPPSS....",
    ".....SPPPPPPPPPPPPPP....",
    "......SSSSSSSSSSSS......",
    "........................"
  ],
  // Frame 3: Leaping Up (Body emerged, tilted 45 deg)
  [
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "..............DD........",
    ".............DTD........",
    "..........DDDTTD........",
    ".........DTTTBD.........",
    "........DTWBBBD.........",
    ".......DDTWBBBD.........",
    "......DTTBBBBD..........",
    ".....DDTDDWBD...........",
    "....DDBD.DBD............",
    "....DBD..D..............",
    "....D...................",
    "........................",
    "........................",
    "........SS...SS.........",
    "......SSPPSSPPSS..S.....",
    ".....SPPPPPPPPPPS.PS....",
    "......SSSSSSSSSSSS......",
    "........................"
  ],
  // Frame 4: Apex of the Leap (User's reference dolphin!)
  [
    ".........DD.............",
    "........DTD.............",
    ".....DDDTTDD............",
    "....DTTTTBBTD...........",
    "...DTWWBBBBBTD..........",
    "..DDTDWBBBBBBTD.........",
    ".DTTBBBBTWWBBBD.........",
    "..DDDDDDTTDWBBTD........",
    ".......DDTDDWBBD........",
    ".......DBDD.DBBD........",
    "........D...DBD.........",
    "...........DDBD.........",
    "..........DBBD..........",
    "...........DBD..........",
    "............D...........",
    "........................",
    "........................",
    "........................",
    "........................",
    "........SS...SS.........",
    "......SSPPSSPPSS........",
    ".....SPPPPPPPPPPS.......",
    "......SSSSSSSSSS........",
    "........................"
  ],
  // Frame 5: Diving Down (Mirror/Tilted down-left)
  [
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........DD..............",
    "........DTD.............",
    "........DTTDDD..........",
    ".........DBTTTD........",
    ".........DBBBWTD........",
    ".........DBBBWTDD.......",
    "..........DBBBBDTD......",
    "...........DBWDDDD......",
    "............DBD.DBDD....",
    "..............D..DBD....",
    "...................D....",
    "........................",
    "........................",
    "........SS...SS.........",
    ".....S..SSPPSSPPSS......",
    "....SP.SPPPPPPPPPPS.....",
    "......SSSSSSSSSSSS......",
    "........................"
  ],
  // Frame 6: Splashdown (Impact on the left)
  [
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    ".....S........S.........",
    "....SPS......SPS........",
    "....SPS......SPS........",
    "....SPS......SPS........",
    "...SPPPS....SPPPS.......",
    "..SPPPPPS..SPPPPPS......",
    ".SPPPPPPPSSPPPPPPPS.....",
    "SSSPPPPPPPPPPPPPPPSSS...",
    "....SSSSSSSSSSSS........",
    "........SS...SS.........",
    "......SSPPSSPPSS........",
    ".....SPPPPPPPPPPS.......",
    "......SSSSSSSSSS........",
    "........................"
  ],
  // Frame 7: Splash Settling
  [
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "......S........S........",
    ".....SPS......SPS.......",
    "....SPPPS....SPPPS......",
    "...SSSSSSSSSSSSSSSS.....",
    "......SSSSSSSSSS........",
    "........SS...SS.........",
    "......SSPPSSPPSS........",
    ".....SPPPPPPPPPPS.......",
    "......SSSSSSSSSS........",
    "........................",
    "........................"
  ]
];

/**
 * Reusable animated pixel-art dolphin loading component.
 * Features an idle rippling puddle state and a playful leaping animation loop.
 * Triggers on hover, click, tap, or periodically on idle.
 *
 * @param {Object} props
 * @param {number} props.size - Display width/height in pixels (default 64)
 * @param {number} props.idleInterval - Idle timeout before auto-jumping in ms (default 6000)
 * @param {string} props.className - Optional additional CSS class name
 * @param {Object} props.style - Inline styles merged into the container
 */
export default function DolphinLoader({ 
  size = 64, 
  idleInterval = 6000, 
  className = '', 
  style = {} 
}) {
  const [frameIndex, setFrameIndex] = useState(0);
  const [isJumping, setIsJumping] = useState(false);
  const jumpTimerRef = useRef(null);
  const idleTimerRef = useRef(null);

  // 1. Idle ripple effect
  useEffect(() => {
    let rippleInterval;
    if (!isJumping) {
      rippleInterval = setInterval(() => {
        setFrameIndex(prev => (prev === 0 ? 1 : 0));
      }, 500);
    }
    return () => clearInterval(rippleInterval);
  }, [isJumping]);

  // 2. Idle auto-jump loop
  useEffect(() => {
    const resetIdleTimer = () => {
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
      if (!isJumping) {
        idleTimerRef.current = setTimeout(() => {
          triggerJump();
        }, idleInterval);
      }
    };

    resetIdleTimer();
    return () => {
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
    };
  }, [isJumping, idleInterval]);

  // 3. Trigger jump animation sequence
  const triggerJump = () => {
    if (isJumping) return; // Ignore if already leaping
    
    setIsJumping(true);
    let currentFrame = 2; // Jump start frame
    setFrameIndex(currentFrame);

    if (jumpTimerRef.current) clearInterval(jumpTimerRef.current);
    
    jumpTimerRef.current = setInterval(() => {
      currentFrame++;
      if (currentFrame < FRAMES.length) {
        setFrameIndex(currentFrame);
      } else {
        clearInterval(jumpTimerRef.current);
        setIsJumping(false);
        setFrameIndex(0); // Return to puddle idle A
      }
    }, 90); // 90ms per frame for a crisp, snappy jump
  };

  // Clean up timers on unmount
  useEffect(() => {
    return () => {
      if (jumpTimerRef.current) clearInterval(jumpTimerRef.current);
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
    };
  }, []);

  // Pre-generate rects mapping for the active frame to maximize render speed
  const activeFrame = FRAMES[frameIndex] || FRAMES[0];
  const rects = [];
  
  activeFrame.forEach((row, y) => {
    for (let x = 0; x < row.length; x++) {
      const char = row[x];
      const color = COLORS[char];
      if (color) {
        rects.push(
          <rect
            key={`${y}-${x}`}
            x={x}
            y={y}
            width={1}
            height={1}
            fill={color}
          />
        );
      }
    }
  });

  return (
    <div 
      className={`dolphin-loader-wrapper ${className}`}
      onMouseEnter={triggerJump}
      onClick={triggerJump}
      onTouchStart={triggerJump}
      style={{
        width: size,
        height: size,
        overflow: 'hidden',
        display: 'inline-flex',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'transparent',
        cursor: isJumping ? 'default' : 'pointer',
        userSelect: 'none',
        ...style,
      }}
    >
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
        style={{
          imageRendering: 'pixelated',
          transform: 'translate3d(0,0,0)', // Hardware acceleration
        }}
      >
        <g>
          {rects}
        </g>
      </svg>
    </div>
  );
}
