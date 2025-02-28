# Grid Game Web App

A simple web-based implementation of a D20 grid game where players roll dice to mark and complete cells on a 20x20 grid.

## Game Rules

- The game is played on a 20x20 grid
- Players start with 50 points
- Each turn, two D20 dice are rolled to determine a random position on the grid
- Each roll costs 1 point
- Cells progress through states:
  - Empty (·) → Marked (1) → Completed (2)
- Completing a cell (reaching value 2) awards 10 points
- Try to complete as many cells as possible before running out of points!

## Features

- Interactive web interface
- Real-time score and turn tracking
- Visual grid display with color-coded cells
- Animated dice roll
- Session-based game state persistence

## Technical Details

- Built with Flask (Python web framework)
- Frontend: HTML, CSS, JavaScript
- Bootstrap for styling
- No database required (uses Flask sessions)

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python app.py
   ```
4. Open your browser and navigate to `http://127.0.0.1:5000/`

## Development

- `app.py` - Main Flask application with game logic
- `templates/index.html` - Frontend interface
- `requirements.txt` - Project dependencies

## Future Improvements

- Multiplayer support
- Leaderboard
- Different grid sizes and difficulty levels
- Special cells with bonus effects
