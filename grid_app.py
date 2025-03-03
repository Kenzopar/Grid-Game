from flask import Flask, render_template, request, jsonify, session
import random
import os
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

def roll_d20():
    return random.randint(1, 20)

# Special cell types
EMPTY = 0
IN_PROGRESS = 1
COMPLETED = 2
BONUS_DOUBLE = 3  # Double points
BONUS_EXTRA_TURN = 4  # Free extra turn
BONUS_WILD = 5  # Complete any cell
PENALTY_WILD = 6  # -10 points penalty

# Difficulty settings
DIFFICULTY = {

    'mini': {
        'size': 6,
        'starting_score': 30,
        'bonus_frequency': 0.35,  # 15% of cells
        'completion_points': 10
    },
    'easy': {
        'size': 10,
        'starting_score': 30,
        'bonus_frequency': 0.25,  # 12% of cells
        'completion_points': 10
    },
    'medium': {
        'size': 20,
        'starting_score': 50,
        'bonus_frequency': 0.15,  # 15% of cells
        'completion_points': 10
    },
    'hard': {
        'size': 20,
        'starting_score': 30,
        'bonus_frequency': 0.03,  # 3% of cells
        'completion_points': 6
    }
}

class GridGame:
    def __init__(self, difficulty='medium', size=None):
        self.difficulty = difficulty
        self.settings = DIFFICULTY[difficulty]
        self.size = size if size else self.settings['size']  # Use provided size or default
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.score = self.settings['starting_score']
        self.turn_count = 0
        self.extra_turns = 0
        self.wild_cells = 0
        self.penalty_wild_cells = 0
        
        # Track available rows and columns
        self.available_rows = set(range(self.size))
        self.available_cols = set(range(self.size))
        
        # Add special bonus cells
        self._add_bonus_cells()
    
    def _add_bonus_cells(self):
        # Calculate number of bonus cells based on difficulty
        total_cells = self.size * self.size
        bonus_frequency = self.settings['bonus_frequency']
        num_bonus_cells = int(total_cells * bonus_frequency)
        
        # Add bonus cells randomly
        for _ in range(num_bonus_cells):
            row = random.randint(0, self.size - 1)
            col = random.randint(0, self.size - 1)
            
            # Only replace empty cells
            if self.grid[row][col] == EMPTY:
                # Randomly choose a bonus type (exclude penalty cells initially)
                bonus_type = random.choice([BONUS_DOUBLE, BONUS_EXTRA_TURN, BONUS_WILD])
                self.grid[row][col] = bonus_type
    
    def add_penalty_cells(self):
        """Add penalty cells after player reaches 100 points"""
        # Only add penalty cells if they don't already exist
        if self.penalty_wild_cells > 0:
            return
            
        # Add 3-5 penalty cells randomly
        num_penalty_cells = random.randint(3, 5)
        penalty_cells_added = 0
        
        # Try to add penalty cells (max 20 attempts to avoid infinite loop)
        attempts = 0
        while penalty_cells_added < num_penalty_cells and attempts < 20:
            row = random.randint(0, self.size - 1)
            col = random.randint(0, self.size - 1)
            
            # Only replace empty or in-progress cells
            if self.grid[row][col] in [EMPTY, IN_PROGRESS]:
                self.grid[row][col] = PENALTY_WILD
                penalty_cells_added += 1
            
            attempts += 1
        
        return penalty_cells_added > 0

    def take_turn(self):
        # Create a list of available cells, excluding completed cells
        available_cells = [(row, col) for row in self.available_rows for col in self.available_cols if self.grid[row][col] != COMPLETED]
        
        # Check if there are available cells to roll
        if available_cells:
            # Randomly select from available cells
            row, col = random.choice(available_cells)
        else:
            # Handle the case where no available cells are left
            raise Exception("No available cells to roll.")
        
        return row, col

    def update_grid(self, row, col):
        cell_value = self.grid[row][col]
        bonus_message = ""
        bonus_applied = False
        completion_message = ""  # New message for grid completion patterns
        
        # Handle special bonus cells
        if cell_value in [BONUS_DOUBLE, BONUS_EXTRA_TURN, BONUS_WILD, PENALTY_WILD]:
            if cell_value == BONUS_DOUBLE:
                self.score += self.settings['completion_points']  # Extra points
                bonus_message = f"BONUS: Double points! +{self.settings['completion_points']} extra points"
            elif cell_value == BONUS_EXTRA_TURN:
                self.extra_turns += 1
                bonus_message = "BONUS: Extra turn awarded! You can roll again without losing points"
            elif cell_value == BONUS_WILD:
                self.wild_cells += 1
                bonus_message = "BONUS: Wild cell awarded! You can complete any cell of your choice"
            elif cell_value == PENALTY_WILD:
                self.penalty_wild_cells += 1
                self.score -= 10
                bonus_message = "PENALTY: -10 points penalty"
            
            # Mark as completed (special cells are completed immediately)
            self.grid[row][col] = COMPLETED
            bonus_applied = True
            return True, bonus_message, bonus_applied
        
        # Handle normal cells
        if cell_value == EMPTY:
            self.grid[row][col] = IN_PROGRESS
            return True, "", bonus_applied
        elif cell_value == IN_PROGRESS:
            self.grid[row][col] = COMPLETED
            # Check if the row or column is now fully completed
            if all(cell == COMPLETED for cell in self.grid[row]):
                self.available_rows.discard(row)
                completion_message += f"Row {row} completed! "
            if all(self.grid[i][col] == COMPLETED for i in range(self.size)):
                self.available_cols.discard(col)
                completion_message += f"Column {col} completed! "
            
            # Check if all cells are completed
            if all(cell == COMPLETED for row in self.grid for cell in row):
                bonus_points = self.size * 10  # 10 points per cell for 10x10 grid, etc.
                self.score += bonus_points
                completion_message += f"All cells completed! Bonus: +{bonus_points} points!"
            
            return True, completion_message, bonus_applied
        else:
            # Cell is already completed, need to roll again
            return False, "", bonus_applied

    def play_turn(self):
        print(f"Current score: {self.score}, Available rows: {self.available_rows}, Available cols: {self.available_cols}")  # Debugging line
        completion_message = ""  # Initialize the completion message here
        # Check if score is 100 or more to limit rolls
        if self.score >= 100:
            row, col = self.take_turn()  # This will now only choose from available rows and cols
        else:
            # Roll freely
            row = random.randint(0, self.size - 1)
            col = random.randint(0, self.size - 1)

        # Ensure the selected cell is valid
        while self.grid[row][col] == COMPLETED:
            print(f"Cell at row {row}, col {col} is completed. Re-rolling...")  # Debugging line
            if self.score >= 100:
                row, col = self.take_turn()  # Re-select from available cells
            else:
                row = random.randint(0, self.size - 1)
                col = random.randint(0, self.size - 1)

        result, bonus_message, bonus_applied = self.update_grid(row, col)
        print(f"Rolled to row {row}, col {col}. Result: {result}, Bonus message: {bonus_message}")  # Debugging line
        
        if result:
            # Check if we have an extra turn to use
            if self.extra_turns > 0:
                self.extra_turns -= 1
                turn_cost = 0
                turn_message = " (Free turn used!)"
            else:
                turn_cost = 1
                turn_message = ""
                
            self.score -= turn_cost  # Subtract points for the turn
            
            # Award points for completing a cell
            if self.grid[row][col] == COMPLETED and not bonus_applied:
                self.score += self.settings['completion_points']
                
            self.turn_count += 1
            
            # Add penalty cells if score reaches 100 points
            penalty_cells_added = False
            if self.score >= 100 and self.penalty_wild_cells == 0:
                penalty_cells_added = self.add_penalty_cells()
                if penalty_cells_added:
                    bonus_message += " WARNING: Penalty cells have appeared on the grid!"
        
        # Capture the completion message
        if result and bonus_message:
            message = f"{bonus_message} {completion_message}"
        elif result:
            message = f"Rolled position: row {row}, col {col} - Marked cell"
        else:
            message = f"Rolled position: row {row}, col {col} - Cell already completed"
        
        # Check if all cells are completed
        if all(cell == COMPLETED for row in self.grid for cell in row):
            message += " All cells completed! Click 'Start New Game' to play again."
        
        return row, col, self.score, result, self.turn_count, message, self.extra_turns, self.wild_cells, self.penalty_wild_cells

    def use_wild_cell(self, target_row, target_col):
        # Check if we have wild cells to use
        if self.wild_cells <= 0:
            return False, "No wild cells available"
        
        # Check if the target cell is valid
        if not (0 <= target_row < self.size and 0 <= target_col < self.size):
            return False, "Invalid cell position"
            
        # Check if the target cell is already completed
        if self.grid[target_row][target_col] == COMPLETED:
            return False, "Cell is already completed"
            
        # Use the wild cell
        self.wild_cells -= 1
        
        # Complete the cell (regardless of current state)
        self.grid[target_row][target_col] = COMPLETED
        self.score += self.settings['completion_points']  # Award points for completion
        
        return True, f"Wild cell used to complete position: row {target_row}, col {target_col}"

    def to_json(self):
        return {
            'grid': self.grid,
            'score': self.score,
            'turn_count': self.turn_count,
            'size': self.size,
            'extra_turns': self.extra_turns,
            'wild_cells': self.wild_cells,
            'penalty_wild_cells': self.penalty_wild_cells,
            'difficulty': self.difficulty,
            'available_rows': list(self.available_rows),
            'available_cols': list(self.available_cols)
        }
    
    @classmethod
    def from_json(cls, data):
        game = cls(difficulty=data.get('difficulty', 'medium'))
        game.grid = data['grid']
        game.score = data['score']
        game.turn_count = data['turn_count']
        game.extra_turns = data.get('extra_turns', 0)
        game.wild_cells = data.get('wild_cells', 0)
        game.penalty_wild_cells = data.get('penalty_wild_cells', 0)
        game.available_rows = set(data.get('available_rows', range(game.size)))
        game.available_cols = set(data.get('available_cols', range(game.size)))
        return game

@app.route('/')
def index():
    # Initialize a new game if not already in session
    if 'game' not in session:
        game = GridGame()
        session['game'] = json.dumps(game.to_json())
    return render_template('index.html')

@app.route('/new_game', methods=['POST'])
def new_game():
    # Get difficulty and size from request
    data = request.json
    difficulty = data.get('difficulty', 'medium')
    size = data.get('size', None)  # Get size from request, if provided
    
    # Validate difficulty
    if difficulty not in DIFFICULTY:
        difficulty = 'medium'
    
    # Create a new game with the specified difficulty and size
    game = GridGame(difficulty=difficulty, size=size)
    session['game'] = json.dumps(game.to_json())
    
    return jsonify(game.to_json())

@app.route('/roll', methods=['POST'])
def roll():
    try:
        # Get game state from session
        game_data = json.loads(session.get('game', '{}'))
        print("Game data retrieved from session:", game_data)  # Debugging line
        game = GridGame.from_json(game_data)
        
        # Take a turn
        row, col, score, result, turn_count, message, extra_turns, wild_cells, penalty_wild_cells = game.play_turn()
        
        # Update session
        session['game'] = json.dumps(game.to_json())
        
        # Return the result
        return jsonify({
            'row': row,
            'col': col,
            'score': score,
            'result': result,
            'turn_count': turn_count,
            'grid': game.grid,
            'message': message,
            'extra_turns': extra_turns,
            'wild_cells': wild_cells,
            'penalty_wild_cells': penalty_wild_cells,
            'size': game.size
        })
    except Exception as e:
        print("An error occurred:", e)  # Debugging line
        return jsonify({'error': str(e)}), 500  # Return error message

@app.route('/use_wild', methods=['POST'])
def use_wild():
    # Get the target cell from request
    data = request.json
    target_row = int(data.get('row', 0))
    target_col = int(data.get('col', 0))
    
    # Get game state from session
    game_data = json.loads(session.get('game', '{}'))
    game = GridGame.from_json(game_data)
    
    # Use the wild cell
    success, message = game.use_wild_cell(target_row, target_col)
    
    # Update session
    session['game'] = json.dumps(game.to_json())
    
    # Return the result
    return jsonify({
        'success': success,
        'message': message,
        'score': game.score,
        'grid': game.grid,
        'wild_cells': game.wild_cells,
        'penalty_wild_cells': game.penalty_wild_cells
    })

@app.route('/reset', methods=['POST'])
def reset():
    # Get difficulty from request
    data = request.json
    difficulty = data.get('difficulty', 'medium')
    
    # Validate difficulty
    if difficulty not in DIFFICULTY:
        difficulty = 'medium'
    
    # Create a new game
    game = GridGame(difficulty=difficulty)
    session['game'] = json.dumps(game.to_json())
    return jsonify(game.to_json())

if __name__ == '__main__':
    app.run(debug=True)