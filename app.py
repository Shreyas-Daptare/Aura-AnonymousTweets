# app.py

from flask import Flask, render_template, request, jsonify

# Initialize the Flask application
app = Flask(__name__)

# Home route
@app.route('/')
def home():
    return render_template('index.html')





















# Example of a route that returns JSON data
@app.route('/api/data', methods=['GET'])
def get_data():
    data = {
        'message': 'This is a sample JSON response',
        'status': 'success'
    }
    return jsonify(data)

# Example of handling form data via POST
@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        name = request.form.get('name')
        return f"Hello, {name}! Your form was submitted successfully."

# Route for rendering an HTML template
@app.route('/template')
def template():
    return render_template('index.html')

# Run the application
if __name__ == '__main__':
    # Debug mode should be turned off in production
    app.run(debug=True)