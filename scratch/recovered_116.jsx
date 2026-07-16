<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CSUCI Student Success Navigator - Dolphin Animation Preview</title>
  <style>
    body {
      background-color: #121824;
      color: #f3f4f6;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
      padding: 20px;
    }

    .container {
      background-color: #1e293b;
      border-radius: 16px;
      padding: 32px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
      text-align: center;
      max-width: 500px;
      border: 1px solid #334155;
    }

    h1 {
      font-size: 1.5rem;
      margin-bottom: 8px;
      color: #38bdf8;
    }

    p {
      color: #94a3b8;
      font-size: 0.95rem;
      line-height: 1.5;
      margin-bottom: 24px;
    }

    .preview-box {
      background-color: #0f172a;
      border-radius: 12px;
      padding: 40px;
      margin-bottom: 24px;
      display: flex;
      justify-content: center;
      align-items: center;
      position: relative;
      overflow: hidden;
      border: 1px dashed #475569;
    }

    .preview-box::before {
      content: "";
      position: absolute;
      width: 100%;
      height: 4px;
      bottom: 20px;
      background: linear-gradient(90deg, transparent, #38bdf8, transparent);
      opacity: 0.3;
    }

    /* Pixel art crisp rendering styles */
    .pixelated {
      image-rendering: crisp-edges;
      image-rendering: pixelated;
    }

    .controls {
      display: flex;
      justify-content: center;
      gap: 12px;
      margin-bottom: 16px;
    }

    button {
      background-color: #334155;
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 500;
      transition: background-color 0.2s;
    }

    button:hover {
      background-color: #475569;
    }

    button.active {
      background-color: #0284c7;
    }

    .footer {
      font-size: 0.8rem;
      color: #64748b;
      margin-top: 16px;
    }
  </style>
</head>
<body>

  <div class="container">
    <h1>CSUCI Dolphin Navigate Mascot</h1>
    <p>Leaping Pixel-Art Dolphin animation designed for loading indicators, empty-states, and success feedback.</p>
    
    <div class="preview-box">
      <!-- Animated SVG Sprite Sheet -->
      <svg id="dolphin-svg" width="128" height="128" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" class="pixelated" style="background: transparent;">
        <style>
          @keyframes play-sprite {
            from { transform: translateX(0px); }
            to { transform: translateX(-120px); }
          }
          .sprite-sheet {
            animation: play-sprite 0.75s steps(5) infinite;
          }
        </style>
        <g class="sprite-sheet">
          <!-- Frame 0: Horizontal Swimming (Prep) -->
          <g id="frame-0">
            <rect x="10" y="5" width="1" height="1" fill="#002D62" />
            <rect x="11" y="5" width="1" height="1" fill="#002D62" />
            <rect x="12" y="5" width="1" height="1" fill="#002D62" />
            <rect x="9" y="6" width="1" height="1" fill="#002D62" />
            <rect x="10" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="11" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="12" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="13" y="6" width="1" height="1" fill="#002D62" />
            <rect x="6" y="7" width="1" height="1" fill="#002D62" />
            <rect x="7" y="7" width="1" height="1" fill="#002D62" />
            <rect x="9" y="7" width="1" height="1" fill="#002D62" />
            <rect x="10" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="11" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="12" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="13" y="7" width="1" height="1" fill="#002D62" />
            <rect x="5" y="8" width="1" height="1" fill="#002D62" />
            <rect x="6" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="7" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="8" y="8" width="1" height="1" fill="#002D62" />
            <rect x="9" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="10" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="11" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="12" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="13" y="8" width="1" height="1" fill="#002D62" />
            <rect x="4" y="9" width="1" height="1" fill="#002D62" />
            <rect x="5" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="6" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="7" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="8" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="9" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="10" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="11" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="12" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="13" y="9" width="1" height="1" fill="#002D62" />
            <rect x="14" y="9" width="1" height="1" fill="#002D62" />
            <rect x="3" y="10" width="1" height="1" fill="#002D62" />
            <rect x="4" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="5" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="6" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="7" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="8" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="9" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="10" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="11" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="12" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="13" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="14" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="15" y="10" width="1" height="1" fill="#002D62" />
            <rect x="2" y="11" width="1" height="1" fill="#002D62" />
            <rect x="3" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="4" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="5" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="6" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="7" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="8" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="9" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="10" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="11" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="12" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="13" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="14" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="15" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="16" y="11" width="1" height="1" fill="#002D62" />
            <rect x="1" y="12" width="1" height="1" fill="#002D62" />
            <rect x="2" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="3" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="4" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="5" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="6" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="7" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="8" y="12" width="1" height="1" fill="#002D62" />
            <rect x="9" y="12" width="1" height="1" fill="#002D62" />
            <rect x="10" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="11" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="12" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="13" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="14" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="15" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="16" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="17" y="12" width="1" height="1" fill="#002D62" />
            <rect x="0" y="13" width="1" height="1" fill="#002D62" />
            <rect x="1" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="2" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="3" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="4" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="5" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="6" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="7" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="8" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="9" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="10" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="11" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="12" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="13" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="14" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="15" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="16" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="17" y="13" width="1" height="1" fill="#002D62" />
            <rect x="1" y="14" width="1" height="1" fill="#002D62" />
            <rect x="2" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="3" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="4" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="5" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="6" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="7" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="8" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="9" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="10" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="11" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="12" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="13" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="14" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="15" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="16" y="14" width="1" height="1" fill="#002D62" />
            <rect x="2" y="15" width="1" height="1" fill="#002D62" />
            <rect x="3" y="15" width="1" height="1" fill="#002D62" />
            <rect x="4" y="15" width="1" height="1" fill="#002D62" />
            <rect x="5" y="15" width="1" height="1" fill="#005A9C" />
            <rect x="6" y="15" width="1" height="1" fill="#005A9C" />
            <rect x="7" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="8" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="9" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="10" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="11" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="12" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="13" y="15" width="1" height="1" fill="#002D62" />
            <rect x="4" y="16" width="1" height="1" fill="#002D62" />
            <rect x="5" y="16" width="1" height="1" fill="#002D62" />
            <rect x="6" y="16" width="1" height="1" fill="#005A9C" />
            <rect x="7" y="16" width="1" height="1" fill="#FFFFFF" />
            <rect x="8" y="16" width="1" height="1" fill="#FFFFFF" />
            <rect x="9" y="16" width="1" height="1" fill="#FFFFFF" />
            <rect x="10" y="16" width="1" height="1" fill="#FFFFFF" />
            <rect x="11" y="16" width="1" height="1" fill="#FFFFFF" />
            <rect x="12" y="16" width="1" height="1" fill="#002D62" />
            <rect x="6" y="17" width="1" height="1" fill="#002D62" />
            <rect x="7" y="17" width="1" height="1" fill="#002D62" />
            <rect x="8" y="17" width="1" height="1" fill="#FFFFFF" />
            <rect x="9" y="17" width="1" height="1" fill="#FFFFFF" />
            <rect x="10" y="17" width="1" height="1" fill="#FFFFFF" />
            <rect x="11" y="17" width="1" height="1" fill="#002D62" />
            <rect x="12" y="17" width="1" height="1" fill="#002D62" />
            <rect x="8" y="18" width="1" height="1" fill="#002D62" />
            <rect x="9" y="18" width="1" height="1" fill="#002D62" />
            <rect x="10" y="18" width="1" height="1" fill="#002D62" />
            <rect x="4" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="5" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="6" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="7" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="8" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="9" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="10" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="11" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="12" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="13" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="14" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="15" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="16" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="17" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="3" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="4" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="5" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="6" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="7" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="8" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="9" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="10" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="11" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="12" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="13" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="14" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="15" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="16" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="17" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="18" y="22" width="1" height="1" fill="#A1E3F9" />
          </g>

          <!-- Frame 1: Leaping Up (Breaking water) -->
          <g id="frame-1">
            <rect x="38" y="3" width="1" height="1" fill="#002D62" />
            <rect x="39" y="3" width="1" height="1" fill="#002D62" />
            <rect x="37" y="4" width="1" height="1" fill="#002D62" />
            <rect x="38" y="4" width="1" height="1" fill="#005A9C" />
            <rect x="39" y="4" width="1" height="1" fill="#005A9C" />
            <rect x="40" y="4" width="1" height="1" fill="#002D62" />
            <rect x="36" y="5" width="1" height="1" fill="#002D62" />
            <rect x="37" y="5" width="1" height="1" fill="#005A9C" />
            <rect x="38" y="5" width="1" height="1" fill="#005A9C" />
            <rect x="39" y="5" width="1" height="1" fill="#005A9C" />
            <rect x="40" y="5" width="1" height="1" fill="#002D62" />
            <rect x="35" y="6" width="1" height="1" fill="#002D62" />
            <rect x="36" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="37" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="38" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="39" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="40" y="6" width="1" height="1" fill="#002D62" />
            <rect x="34" y="7" width="1" height="1" fill="#002D62" />
            <rect x="35" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="36" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="37" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="38" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="39" y="7" width="1" height="1" fill="#002D62" />
            <rect x="33" y="8" width="1" height="1" fill="#002D62" />
            <rect x="34" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="35" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="36" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="37" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="38" y="8" width="1" height="1" fill="#002D62" />
            <rect x="32" y="9" width="1" height="1" fill="#002D62" />
            <rect x="33" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="34" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="35" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="36" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="37" y="9" width="1" height="1" fill="#002D62" />
            <rect x="30" y="10" width="1" height="1" fill="#002D62" />
            <rect x="31" y="10" width="1" height="1" fill="#002D62" />
            <rect x="32" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="33" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="34" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="35" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="36" y="10" width="1" height="1" fill="#002D62" />
            <rect x="29" y="11" width="1" height="1" fill="#002D62" />
            <rect x="30" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="31" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="32" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="33" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="34" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="35" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="36" y="11" width="1" height="1" fill="#002D62" />
            <rect x="28" y="12" width="1" height="1" fill="#002D62" />
            <rect x="29" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="30" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="31" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="32" y="12" width="1" height="1" fill="#002D62" />
            <rect x="33" y="12" width="1" height="1" fill="#002D62" />
            <rect x="34" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="35" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="36" y="12" width="1" height="1" fill="#002D62" />
            <rect x="27" y="13" width="1" height="1" fill="#002D62" />
            <rect x="28" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="29" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="30" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="31" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="32" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="33" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="34" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="35" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="36" y="13" width="1" height="1" fill="#002D62" />
            <rect x="26" y="14" width="1" height="1" fill="#002D62" />
            <rect x="27" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="28" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="29" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="30" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="31" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="32" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="33" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="34" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="35" y="14" width="1" height="1" fill="#002D62" />
            <rect x="26" y="15" width="1" height="1" fill="#002D62" />
            <rect x="27" y="15" width="1" height="1" fill="#005A9C" />
            <rect x="28" y="15" width="1" height="1" fill="#005A9C" />
            <rect x="29" y="15" width="1" height="1" fill="#005A9C" />
            <rect x="30" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="31" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="32" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="33" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="34" y="15" width="1" height="1" fill="#002D62" />
            <rect x="27" y="16" width="1" height="1" fill="#002D62" />
            <rect x="28" y="16" width="1" height="1" fill="#005A9C" />
            <rect x="29" y="16" width="1" height="1" fill="#005A9C" />
            <rect x="30" y="16" width="1" height="1" fill="#FFFFFF" />
            <rect x="31" y="16" width="1" height="1" fill="#FFFFFF" />
            <rect x="32" y="16" width="1" height="1" fill="#FFFFFF" />
            <rect x="33" y="16" width="1" height="1" fill="#002D62" />
            <rect x="28" y="17" width="1" height="1" fill="#002D62" />
            <rect x="29" y="17" width="1" height="1" fill="#005A9C" />
            <rect x="30" y="17" width="1" height="1" fill="#FFFFFF" />
            <rect x="31" y="17" width="1" height="1" fill="#FFFFFF" />
            <rect x="32" y="17" width="1" height="1" fill="#002D62" />
            <rect x="29" y="18" width="1" height="1" fill="#002D62" />
            <rect x="30" y="18" width="1" height="1" fill="#002D62" />
            <rect x="31" y="18" width="1" height="1" fill="#002D62" />
            <rect x="30" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="31" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="34" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="35" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="28" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="29" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="30" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="31" y="21" width="1" height="1" fill="#E8F9FF" />
            <rect x="32" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="33" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="34" y="21" width="1" height="1" fill="#E8F9FF" />
            <rect x="35" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="36" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="37" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="27" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="28" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="29" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="30" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="31" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="32" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="33" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="34" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="35" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="36" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="37" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="38" y="22" width="1" height="1" fill="#A1E3F9" />
          </g>

          <!-- Frame 2: Apex of the Leap (Highest point) -->
          <g id="frame-2">
            <rect x="58" y="2" width="1" height="1" fill="#002D62" />
            <rect x="59" y="2" width="1" height="1" fill="#002D62" />
            <rect x="60" y="2" width="1" height="1" fill="#002D62" />
            <rect x="56" y="3" width="1" height="1" fill="#002D62" />
            <rect x="57" y="3" width="1" height="1" fill="#002D62" />
            <rect x="58" y="3" width="1" height="1" fill="#005A9C" />
            <rect x="59" y="3" width="1" height="1" fill="#005A9C" />
            <rect x="60" y="3" width="1" height="1" fill="#005A9C" />
            <rect x="61" y="3" width="1" height="1" fill="#002D62" />
            <rect x="62" y="3" width="1" height="1" fill="#002D62" />
            <rect x="55" y="4" width="1" height="1" fill="#002D62" />
            <rect x="56" y="4" width="1" height="1" fill="#005A9C" />
            <rect x="57" y="4" width="1" height="1" fill="#005A9C" />
            <rect x="58" y="4" width="1" height="1" fill="#005A9C" />
            <rect x="59" y="4" width="1" height="1" fill="#005A9C" />
            <rect x="60" y="4" width="1" height="1" fill="#005A9C" />
            <rect x="61" y="4" width="1" height="1" fill="#005A9C" />
            <rect x="62" y="4" width="1" height="1" fill="#005A9C" />
            <rect x="63" y="4" width="1" height="1" fill="#002D62" />
            <rect x="54" y="5" width="1" height="1" fill="#002D62" />
            <rect x="55" y="5" width="1" height="1" fill="#005A9C" />
            <rect x="56" y="5" width="1" height="1" fill="#005A9C" />
            <rect x="57" y="5" width="1" height="1" fill="#005A9C" />
            <rect x="58" y="5" width="1" height="1" fill="#005A9C" />
            <rect x="59" y="5" width="1" height="1" fill="#005A9C" />
            <rect x="60" y="5" width="1" height="1" fill="#005A9C" />
            <rect x="61" y="5" width="1" height="1" fill="#005A9C" />
            <rect x="62" y="5" width="1" height="1" fill="#005A9C" />
            <rect x="63" y="5" width="1" height="1" fill="#005A9C" />
            <rect x="64" y="5" width="1" height="1" fill="#002D62" />
            <rect x="53" y="6" width="1" height="1" fill="#002D62" />
            <rect x="54" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="55" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="56" y="6" width="1" height="1" fill="#002D62" />
            <rect x="57" y="6" width="1" height="1" fill="#002D62" />
            <rect x="58" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="59" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="60" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="61" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="62" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="63" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="64" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="65" y="6" width="1" height="1" fill="#002D62" />
            <rect x="52" y="7" width="1" height="1" fill="#002D62" />
            <rect x="53" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="54" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="55" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="56" y="7" width="1" height="1" fill="#FFFFFF" />
            <rect x="57" y="7" width="1" height="1" fill="#FFFFFF" />
            <rect x="58" y="7" width="1" height="1" fill="#FFFFFF" />
            <rect x="59" y="7" width="1" height="1" fill="#FFFFFF" />
            <rect x="60" y="7" width="1" height="1" fill="#FFFFFF" />
            <rect x="61" y="7" width="1" height="1" fill="#FFFFFF" />
            <rect x="62" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="63" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="64" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="65" y="7" width="1" height="1" fill="#002D62" />
            <rect x="51" y="8" width="1" height="1" fill="#002D62" />
            <rect x="52" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="53" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="54" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="55" y="8" width="1" height="1" fill="#FFFFFF" />
            <rect x="56" y="8" width="1" height="1" fill="#FFFFFF" />
            <rect x="57" y="8" width="1" height="1" fill="#FFFFFF" />
            <rect x="58" y="8" width="1" height="1" fill="#FFFFFF" />
            <rect x="59" y="8" width="1" height="1" fill="#FFFFFF" />
            <rect x="60" y="8" width="1" height="1" fill="#FFFFFF" />
            <rect x="61" y="8" width="1" height="1" fill="#FFFFFF" />
            <rect x="62" y="8" width="1" height="1" fill="#FFFFFF" />
            <rect x="63" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="64" y="8" width="1" height="1" fill="#002D62" />
            <rect x="50" y="9" width="1" height="1" fill="#002D62" />
            <rect x="51" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="52" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="53" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="54" y="9" width="1" height="1" fill="#FFFFFF" />
            <rect x="55" y="9" width="1" height="1" fill="#FFFFFF" />
            <rect x="56" y="9" width="1" height="1" fill="#FFFFFF" />
            <rect x="57" y="9" width="1" height="1" fill="#FFFFFF" />
            <rect x="58" y="9" width="1" height="1" fill="#FFFFFF" />
            <rect x="59" y="9" width="1" height="1" fill="#FFFFFF" />
            <rect x="60" y="9" width="1" height="1" fill="#FFFFFF" />
            <rect x="61" y="9" width="1" height="1" fill="#FFFFFF" />
            <rect x="62" y="9" width="1" height="1" fill="#FFFFFF" />
            <rect x="63" y="9" width="1" height="1" fill="#002D62" />
            <rect x="49" y="10" width="1" height="1" fill="#002D62" />
            <rect x="50" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="51" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="52" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="53" y="10" width="1" height="1" fill="#FFFFFF" />
            <rect x="54" y="10" width="1" height="1" fill="#FFFFFF" />
            <rect x="55" y="10" width="1" height="1" fill="#FFFFFF" />
            <rect x="56" y="10" width="1" height="1" fill="#FFFFFF" />
            <rect x="57" y="10" width="1" height="1" fill="#FFFFFF" />
            <rect x="58" y="10" width="1" height="1" fill="#FFFFFF" />
            <rect x="59" y="10" width="1" height="1" fill="#FFFFFF" />
            <rect x="60" y="10" width="1" height="1" fill="#FFFFFF" />
            <rect x="61" y="10" width="1" height="1" fill="#FFFFFF" />
            <rect x="62" y="10" width="1" height="1" fill="#002D62" />
            <rect x="48" y="11" width="1" height="1" fill="#002D62" />
            <rect x="49" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="50" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="51" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="52" y="11" width="1" height="1" fill="#FFFFFF" />
            <rect x="53" y="11" width="1" height="1" fill="#FFFFFF" />
            <rect x="54" y="11" width="1" height="1" fill="#FFFFFF" />
            <rect x="55" y="11" width="1" height="1" fill="#FFFFFF" />
            <rect x="56" y="11" width="1" height="1" fill="#FFFFFF" />
            <rect x="57" y="11" width="1" height="1" fill="#FFFFFF" />
            <rect x="58" y="11" width="1" height="1" fill="#FFFFFF" />
            <rect x="59" y="11" width="1" height="1" fill="#FFFFFF" />
            <rect x="60" y="11" width="1" height="1" fill="#002D62" />
            <rect x="61" y="11" width="1" height="1" fill="#002D62" />
            <rect x="48" y="12" width="1" height="1" fill="#002D62" />
            <rect x="49" y="12" width="1" height="1" fill="#002D62" />
            <rect x="50" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="51" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="52" y="12" width="1" height="1" fill="#FFFFFF" />
            <rect x="53" y="12" width="1" height="1" fill="#FFFFFF" />
            <rect x="54" y="12" width="1" height="1" fill="#FFFFFF" />
            <rect x="55" y="12" width="1" height="1" fill="#FFFFFF" />
            <rect x="56" y="12" width="1" height="1" fill="#FFFFFF" />
            <rect x="57" y="12" width="1" height="1" fill="#002D62" />
            <rect x="58" y="12" width="1" height="1" fill="#002D62" />
            <rect x="59" y="12" width="1" height="1" fill="#002D62" />
            <rect x="49" y="13" width="1" height="1" fill="#002D62" />
            <rect x="50" y="13" width="1" height="1" fill="#002D62" />
            <rect x="51" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="52" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="53" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="54" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="55" y="13" width="1" height="1" fill="#002D62" />
            <rect x="56" y="13" width="1" height="1" fill="#002D62" />
            <rect x="57" y="13" width="1" height="1" fill="#002D62" />
            <rect x="50" y="14" width="1" height="1" fill="#002D62" />
            <rect x="51" y="14" width="1" height="1" fill="#002D62" />
            <rect x="52" y="14" width="1" height="1" fill="#002D62" />
            <rect x="53" y="14" width="1" height="1" fill="#002D62" />
            <rect x="54" y="14" width="1" height="1" fill="#002D62" />
            <rect x="52" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="53" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="62" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="63" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="51" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="52" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="53" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="62" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="63" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="64" y="23" width="1" height="1" fill="#A1E3F9" />
          </g>

          <!-- Frame 3: Diving Down (Entering water) -->
          <g id="frame-3">
            <rect x="77" y="1" width="1" height="1" fill="#002D62" />
            <rect x="78" y="1" width="1" height="1" fill="#002D62" />
            <rect x="79" y="1" width="1" height="1" fill="#002D62" />
            <rect x="76" y="2" width="1" height="1" fill="#002D62" />
            <rect x="77" y="2" width="1" height="1" fill="#005A9C" />
            <rect x="78" y="2" width="1" height="1" fill="#FFFFFF" />
            <rect x="79" y="2" width="1" height="1" fill="#FFFFFF" />
            <rect x="80" y="2" width="1" height="1" fill="#002D62" />
            <rect x="75" y="3" width="1" height="1" fill="#002D62" />
            <rect x="76" y="3" width="1" height="1" fill="#005A9C" />
            <rect x="77" y="3" width="1" height="1" fill="#005A9C" />
            <rect x="78" y="3" width="1" height="1" fill="#FFFFFF" />
            <rect x="79" y="3" width="1" height="1" fill="#FFFFFF" />
            <rect x="80" y="3" width="1" height="1" fill="#FFFFFF" />
            <rect x="81" y="3" width="1" height="1" fill="#002D62" />
            <rect x="74" y="4" width="1" height="1" fill="#002D62" />
            <rect x="75" y="4" width="1" height="1" fill="#005A9C" />
            <rect x="76" y="4" width="1" height="1" fill="#005A9C" />
            <rect x="77" y="4" width="1" height="1" fill="#005A9C" />
            <rect x="78" y="4" width="1" height="1" fill="#FFFFFF" />
            <rect x="79" y="4" width="1" height="1" fill="#FFFFFF" />
            <rect x="80" y="4" width="1" height="1" fill="#FFFFFF" />
            <rect x="81" y="4" width="1" height="1" fill="#FFFFFF" />
            <rect x="82" y="4" width="1" height="1" fill="#002D62" />
            <rect x="74" y="5" width="1" height="1" fill="#002D62" />
            <rect x="75" y="5" width="1" height="1" fill="#005A9C" />
            <rect x="76" y="5" width="1" height="1" fill="#005A9C" />
            <rect x="77" y="5" width="1" height="1" fill="#005A9C" />
            <rect x="78" y="5" width="1" height="1" fill="#FFFFFF" />
            <rect x="79" y="5" width="1" height="1" fill="#FFFFFF" />
            <rect x="80" y="5" width="1" height="1" fill="#FFFFFF" />
            <rect x="81" y="5" width="1" height="1" fill="#FFFFFF" />
            <rect x="82" y="5" width="1" height="1" fill="#FFFFFF" />
            <rect x="83" y="5" width="1" height="1" fill="#002D62" />
            <rect x="75" y="6" width="1" height="1" fill="#002D62" />
            <rect x="76" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="77" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="78" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="79" y="6" width="1" height="1" fill="#FFFFFF" />
            <rect x="80" y="6" width="1" height="1" fill="#FFFFFF" />
            <rect x="81" y="6" width="1" height="1" fill="#FFFFFF" />
            <rect x="82" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="83" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="84" y="6" width="1" height="1" fill="#002D62" />
            <rect x="76" y="7" width="1" height="1" fill="#002D62" />
            <rect x="77" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="78" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="79" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="80" y="7" width="1" height="1" fill="#002D62" />
            <rect x="81" y="7" width="1" height="1" fill="#002D62" />
            <rect x="82" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="83" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="84" y="7" width="1" height="1" fill="#002D62" />
            <rect x="77" y="8" width="1" height="1" fill="#002D62" />
            <rect x="78" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="79" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="80" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="81" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="82" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="83" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="84" y="8" width="1" height="1" fill="#002D62" />
            <rect x="78" y="9" width="1" height="1" fill="#002D62" />
            <rect x="79" y="9" width="1" height="1" fill="#002D62" />
            <rect x="80" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="81" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="82" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="83" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="84" y="9" width="1" height="1" fill="#002D62" />
            <rect x="80" y="10" width="1" height="1" fill="#002D62" />
            <rect x="81" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="82" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="83" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="84" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="85" y="10" width="1" height="1" fill="#002D62" />
            <rect x="81" y="11" width="1" height="1" fill="#002D62" />
            <rect x="82" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="83" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="84" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="85" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="86" y="11" width="1" height="1" fill="#002D62" />
            <rect x="82" y="12" width="1" height="1" fill="#002D62" />
            <rect x="83" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="84" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="85" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="86" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="87" y="12" width="1" height="1" fill="#002D62" />
            <rect x="83" y="13" width="1" height="1" fill="#002D62" />
            <rect x="84" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="85" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="86" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="87" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="88" y="13" width="1" height="1" fill="#002D62" />
            <rect x="84" y="14" width="1" height="1" fill="#002D62" />
            <rect x="85" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="86" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="87" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="88" y="14" width="1" height="1" fill="#002D62" />
            <rect x="85" y="15" width="1" height="1" fill="#002D62" />
            <rect x="86" y="15" width="1" height="1" fill="#005A9C" />
            <rect x="87" y="15" width="1" height="1" fill="#005A9C" />
            <rect x="88" y="15" width="1" height="1" fill="#002D62" />
            <rect x="86" y="16" width="1" height="1" fill="#002D62" />
            <rect x="87" y="16" width="1" height="1" fill="#002D62" />
            <rect x="78" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="79" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="82" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="83" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="76" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="77" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="78" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="79" y="22" width="1" height="1" fill="#E8F9FF" />
            <rect x="80" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="81" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="82" y="22" width="1" height="1" fill="#E8F9FF" />
            <rect x="83" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="84" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="85" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="75" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="76" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="77" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="78" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="79" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="80" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="81" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="82" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="83" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="84" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="85" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="86" y="23" width="1" height="1" fill="#A1E3F9" />
          </g>

          <!-- Frame 4: Splashdown (Impact) -->
          <g id="frame-4">
            <rect x="106" y="5" width="1" height="1" fill="#002D62" />
            <rect x="107" y="5" width="1" height="1" fill="#002D62" />
            <rect x="108" y="5" width="1" height="1" fill="#002D62" />
            <rect x="105" y="6" width="1" height="1" fill="#002D62" />
            <rect x="106" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="107" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="108" y="6" width="1" height="1" fill="#005A9C" />
            <rect x="109" y="6" width="1" height="1" fill="#002D62" />
            <rect x="102" y="7" width="1" height="1" fill="#002D62" />
            <rect x="103" y="7" width="1" height="1" fill="#002D62" />
            <rect x="105" y="7" width="1" height="1" fill="#002D62" />
            <rect x="106" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="107" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="108" y="7" width="1" height="1" fill="#005A9C" />
            <rect x="109" y="7" width="1" height="1" fill="#002D62" />
            <rect x="101" y="8" width="1" height="1" fill="#002D62" />
            <rect x="102" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="103" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="104" y="8" width="1" height="1" fill="#002D62" />
            <rect x="105" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="106" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="107" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="108" y="8" width="1" height="1" fill="#005A9C" />
            <rect x="109" y="8" width="1" height="1" fill="#002D62" />
            <rect x="100" y="9" width="1" height="1" fill="#002D62" />
            <rect x="101" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="102" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="103" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="104" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="105" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="106" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="107" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="108" y="9" width="1" height="1" fill="#005A9C" />
            <rect x="109" y="9" width="1" height="1" fill="#002D62" />
            <rect x="110" y="9" width="1" height="1" fill="#002D62" />
            <rect x="99" y="10" width="1" height="1" fill="#002D62" />
            <rect x="100" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="101" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="102" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="103" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="104" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="105" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="106" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="107" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="108" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="109" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="110" y="10" width="1" height="1" fill="#005A9C" />
            <rect x="111" y="10" width="1" height="1" fill="#002D62" />
            <rect x="98" y="11" width="1" height="1" fill="#002D62" />
            <rect x="99" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="100" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="101" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="102" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="103" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="104" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="105" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="106" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="107" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="108" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="109" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="110" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="111" y="11" width="1" height="1" fill="#005A9C" />
            <rect x="112" y="11" width="1" height="1" fill="#002D62" />
            <rect x="97" y="12" width="1" height="1" fill="#002D62" />
            <rect x="98" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="99" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="100" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="101" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="102" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="103" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="104" y="12" width="1" height="1" fill="#002D62" />
            <rect x="105" y="12" width="1" height="1" fill="#002D62" />
            <rect x="106" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="107" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="108" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="109" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="110" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="111" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="112" y="12" width="1" height="1" fill="#005A9C" />
            <rect x="113" y="12" width="1" height="1" fill="#002D62" />
            <rect x="96" y="13" width="1" height="1" fill="#002D62" />
            <rect x="97" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="98" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="99" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="100" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="101" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="102" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="103" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="104" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="105" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="106" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="107" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="108" y="13" width="1" height="1" fill="#FFFFFF" />
            <rect x="109" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="110" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="111" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="112" y="13" width="1" height="1" fill="#005A9C" />
            <rect x="113" y="13" width="1" height="1" fill="#002D62" />
            <rect x="97" y="14" width="1" height="1" fill="#002D62" />
            <rect x="98" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="99" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="100" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="101" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="102" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="103" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="104" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="105" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="106" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="107" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="108" y="14" width="1" height="1" fill="#FFFFFF" />
            <rect x="109" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="110" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="111" y="14" width="1" height="1" fill="#005A9C" />
            <rect x="112" y="14" width="1" height="1" fill="#002D62" />
            <rect x="98" y="15" width="1" height="1" fill="#002D62" />
            <rect x="99" y="15" width="1" height="1" fill="#002D62" />
            <rect x="100" y="15" width="1" height="1" fill="#002D62" />
            <rect x="101" y="15" width="1" height="1" fill="#005A9C" />
            <rect x="102" y="15" width="1" height="1" fill="#005A9C" />
            <rect x="103" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="104" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="105" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="106" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="107" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="108" y="15" width="1" height="1" fill="#FFFFFF" />
            <rect x="109" y="15" width="1" height="1" fill="#002D62" />
            <rect x="100" y="16" width="1" height="1" fill="#002D62" />
            <rect x="101" y="16" width="1" height="1" fill="#002D62" />
            <rect x="102" y="16" width="1" height="1" fill="#005A9C" />
            <rect x="103" y="16" width="1" height="1" fill="#FFFFFF" />
            <rect x="104" y="16" width="1" height="1" fill="#FFFFFF" />
            <rect x="105" y="16" width="1" height="1" fill="#FFFFFF" />
            <rect x="106" y="16" width="1" height="1" fill="#FFFFFF" />
            <rect x="107" y="16" width="1" height="1" fill="#FFFFFF" />
            <rect x="108" y="16" width="1" height="1" fill="#002D62" />
            <rect x="112" y="16" width="1" height="1" fill="#E8F9FF" />
            <rect x="115" y="16" width="1" height="1" fill="#E8F9FF" />
            <rect x="102" y="17" width="1" height="1" fill="#002D62" />
            <rect x="103" y="17" width="1" height="1" fill="#002D62" />
            <rect x="104" y="17" width="1" height="1" fill="#FFFFFF" />
            <rect x="105" y="17" width="1" height="1" fill="#FFFFFF" />
            <rect x="106" y="17" width="1" height="1" fill="#FFFFFF" />
            <rect x="107" y="17" width="1" height="1" fill="#002D62" />
            <rect x="108" y="17" width="1" height="1" fill="#002D62" />
            <rect x="111" y="17" width="1" height="1" fill="#A1E3F9" />
            <rect x="112" y="17" width="1" height="1" fill="#E8F9FF" />
            <rect x="113" y="17" width="1" height="1" fill="#A1E3F9" />
            <rect x="114" y="17" width="1" height="1" fill="#E8F9FF" />
            <rect x="115" y="17" width="1" height="1" fill="#A1E3F9" />
            <rect x="98" y="18" width="1" height="1" fill="#E8F9FF" />
            <rect x="101" y="18" width="1" height="1" fill="#E8F9FF" />
            <rect x="102" y="18" width="1" height="1" fill="#002D62" />
            <rect x="103" y="18" width="1" height="1" fill="#002D62" />
            <rect x="104" y="18" width="1" height="1" fill="#002D62" />
            <rect x="105" y="18" width="1" height="1" fill="#A1E3F9" />
            <rect x="106" y="18" width="1" height="1" fill="#E8F9FF" />
            <rect x="107" y="18" width="1" height="1" fill="#A1E3F9" />
            <rect x="108" y="18" width="1" height="1" fill="#E8F9FF" />
            <rect x="109" y="18" width="1" height="1" fill="#A1E3F9" />
            <rect x="110" y="18" width="1" height="1" fill="#A1E3F9" />
            <rect x="97" y="19" width="1" height="1" fill="#A1E3F9" />
            <rect x="98" y="19" width="1" height="1" fill="#E8F9FF" />
            <rect x="99" y="19" width="1" height="1" fill="#A1E3F9" />
            <rect x="100" y="19" width="1" height="1" fill="#E8F9FF" />
            <rect x="101" y="19" width="1" height="1" fill="#A1E3F9" />
            <rect x="105" y="19" width="1" height="1" fill="#A1E3F9" />
            <rect x="106" y="19" width="1" height="1" fill="#A1E3F9" />
            <rect x="107" y="19" width="1" height="1" fill="#A1E3F9" />
            <rect x="108" y="19" width="1" height="1" fill="#A1E3F9" />
            <rect x="109" y="19" width="1" height="1" fill="#A1E3F9" />
            <rect x="110" y="19" width="1" height="1" fill="#A1E3F9" />
            <rect x="111" y="19" width="1" height="1" fill="#A1E3F9" />
            <rect x="112" y="19" width="1" height="1" fill="#A1E3F9" />
            <rect x="96" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="97" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="98" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="99" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="100" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="101" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="104" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="105" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="106" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="107" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="108" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="109" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="110" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="111" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="112" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="113" y="20" width="1" height="1" fill="#A1E3F9" />
            <rect x="96" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="97" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="98" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="99" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="100" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="101" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="102" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="103" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="104" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="105" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="106" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="107" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="108" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="109" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="110" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="111" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="112" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="113" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="114" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="115" y="21" width="1" height="1" fill="#A1E3F9" />
            <rect x="96" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="97" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="98" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="99" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="100" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="101" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="102" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="103" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="104" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="105" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="106" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="107" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="108" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="109" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="110" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="111" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="112" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="113" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="114" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="115" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="116" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="117" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="118" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="119" y="22" width="1" height="1" fill="#A1E3F9" />
            <rect x="96" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="97" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="98" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="99" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="100" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="101" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="102" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="103" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="104" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="105" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="106" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="107" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="108" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="109" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="110" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="111" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="112" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="113" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="114" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="115" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="116" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="117" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="118" y="23" width="1" height="1" fill="#A1E3F9" />
            <rect x="119" y="23" width="1" height="1" fill="#A1E3F9" />
          </g>
        </g>
      </svg>
    </div>

    <div class="controls">
      <button id="size-sm">Small (64px)</button>
      <button id="size-md" class="active">Medium (128px)</button>
      <button id="size-lg">Large (256px)</button>
    </div>
    
    <div class="footer">
      CSS sprite sheet animation (steps(5)) cycling over a 24x24 pixel grid.
    </div>
  </div>

  <script>
    const svg = document.getElementById('dolphin-svg');
    const sizeSm = document.getElementById('size-sm');
    const sizeMd = document.getElementById('size-md');
    const sizeLg = document.getElementById('size-lg');

    function setSize(size, activeBtn) {
      svg.setAttribute('width', size);
      svg.setAttribute('height', size);
      [sizeSm, sizeMd, sizeLg].forEach(btn => btn.classList.remove('active'));
      activeBtn.classList.add('active');
    }

    sizeSm.addEventListener('click', () => setSize(64, sizeSm));
    sizeMd.addEventListener('click', () => setSize(128, sizeMd));
    sizeLg.addEventListener('click', () => setSize(256, sizeLg));
  </script>
</body>
</html>