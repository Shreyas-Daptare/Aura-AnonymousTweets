from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import text, create_engine
import os
# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'supersecretkey'
engine = create_engine("sqlite:///aura.db", echo=True) 

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

    def get_id(self):
        return str(self.id)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aura.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy (but we won’t use models)
db = SQLAlchemy(app)
    
def query_proccesor(query):
    result = db.session.execute(query)
    return result

# Home route
@app.route('/')
@login_required
def index():
    return render_template('index.html')
    #return f"Hello {current_user.username}, you are logged in!"


#Login
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def handle_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        login_query = text("""
        SELECT password, id
        FROM users
        WHERE username=:username
        """)
        with engine.connect() as connection:
            user = connection.execute(login_query, {'username': username}).fetchone()

            if user and check_password_hash(user[0], password):
                # Initialize the User object and log the user in
                user = User(user[1], username)
                login_user(user)

                # After login, Flask-Login will manage the user automatically
                return redirect(url_for("index"))
            else:
                return render_template("IncorrectPassword.html"), 404
    return render_template('login.html')


@login_manager.user_loader
def load_user(user_id):
    # Query the user only once when they log in and Flask-Login will take care of the rest
    login_query = text("""
    SELECT username
    FROM users
    WHERE id=:user_id
    """)
    with engine.connect() as connection:
        user = connection.execute(login_query, {'user_id': user_id}).fetchone()
    
    # If the user exists, return the User object
    if user:
        return User(user_id, user[0])
    return None


#Sign Up
@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/signup", methods=["POST"])
def handle_signup():
    name= request.form["name"]
    username=request.form["username"]
    password=request.form["password"]
    picture = ""
    #picture = request.files['picture']
    #filename = secure_filename(picture.filename)
    #picture.save(os.path.join('static/uploads', filename))

    hashed_password = generate_password_hash(password)
    print(f"username: {username}, password:{password}, Hashed password: {hashed_password}")
    insert_query = text("""
        INSERT INTO users(name, username, password, picture)
        VALUES (:name, :username, :password, :picture)
    """)
    # Execute the query using the parameters
    with engine.connect() as connection:
        connection.execute(insert_query, {
            'name': name,
            'username': username,
            'password': hashed_password,
            'picture': picture
        })
        connection.commit()
    return redirect(url_for("login"))

@app.route("/forgotpassword")
def forgot_password():
    return render_template('ForgotPassword.html')
    
# Run the application
if __name__ == '__main__':
    # Debug mode should be turned off in production
    app.run(debug=True)