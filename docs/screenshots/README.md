# Screenshots — Manual Capture Instructions

The following screenshots must be captured manually from the running application.

## Required Files

| File | Section to capture |
|---|---|
| `hero.png` | Hero section — campus image and tagline visible |
| `digital-twin.png` | Digital Twin Campus section — all zones visible |
| `war-room.png` | Agent War Room — agents active, node network visible |
| `waste-agent.png` | Waste-to-Wealth Analyzer — result shown for e-waste 50kg |
| `report.png` | Report section — executive brief visible |

## Steps

1. Start the backend: `cd backend && uvicorn main:app --reload --port 8000`
2. Start the frontend: `cd frontend && npm run dev`
3. Open `http://localhost:5173` in Chrome or Edge
4. Set browser zoom to 100% (Ctrl+0)
5. Maximize the browser window
6. For each section:
   - Navigate to the section
   - For War Room: click Run Agents, wait for all agents to complete
   - For Waste Agent: enter `e-waste` and `50`, click Analyze
   - Take screenshot using the OS tool or browser (F12 → Screenshots in Chrome DevTools)
   - Save to this folder with the exact filename listed above

## Recommended Dimensions

- Width: 1920px (or full window width)
- Height: Capture enough to show the section clearly — crop vertically as needed
- Format: PNG

## After Capturing

Update `README.md` screenshot table — links already point to these file paths and will render automatically once the images exist.
