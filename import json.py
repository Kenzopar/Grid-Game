import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Function to read high scores from the JSON file with error handling
def read_high_scores():
    try:
        with open('high_scores.json', 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading high scores: {e}")
        return {"mini": [], "easy": [], "medium": [], "hard": []}  # Return default structure if error occurs

# Function to write high scores to the JSON file with error handling
def write_high_scores(scores):
    try:
        with open('high_scores.json', 'w') as file:
            json.dump(scores, file)
    except IOError as e:
        print(f"Error writing high scores: {e}")

@app.route('/highscores', methods=['GET'])
def get_high_scores():
    scores = read_high_scores()
    return render_template('high_scores.html', scores=scores)

@app.route('/submit_score', methods=['POST'])
def submit_score():
    new_score = request.form['score']
    difficulty = request.form['difficulty']

    # Input validation
    if not new_score.isdigit():
        return jsonify(success=False, message="Invalid input. Please provide a valid score.")

    new_score = int(new_score)  # Convert score to integer

    # Read existing scores
    scores = read_high_scores()

    # Add new score to the list for the specified difficulty
    scores[difficulty].append(new_score)

    # Keep only the top 10 scores
    scores[difficulty] = sorted(scores[difficulty], reverse=True)[:10]

    # Write updated scores back to the file
    write_high_scores(scores)

    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True)