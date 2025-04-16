from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import text, create_engine
import os
import uuid 
from datetime import datetime
import pytz
# Initialize the Flask application
utc = pytz.utc
ist = pytz.timezone("Asia/Kolkata")

app = Flask(__name__)
app.secret_key = 'supersecretkey'
engine = create_engine("sqlite:///aura.db", echo=True) 
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aura.db'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy (but we won’t use models)
#db = SQLAlchemy(app)
    


# Home route
@app.route('/')
@login_required
def index():
    get_details_query = text("""
        SELECT id, name, username, picture
        FROM users
        WHERE username=:username
    """)
    with engine.connect() as connection:
        user = connection.execute(get_details_query, {'username': current_user.username}).fetchone()
        print(f"User details: {user}")
        user = list(user)
        fixed_path = user[3].replace("static/", "")
        #fixed_path = "/static/" + fixed_path
        user[3] = fixed_path
        print(f"Fixed path: {user[3]}")
        #print(f"Current user: {current_user.username}, ID: {current_user.id}")
        
        
    get_tweets_query = text("""
    SELECT u.id, u.picture, u.username, u.name, t.tweet, t.contains_image, t.image_path, t.created_at
    FROM tweets t
    LEFT JOIN users u ON t.user_id = u.id
    ORDER BY created_at DESC
    """)
    
    with engine.connect() as connection:
        tweets = connection.execute(get_tweets_query).fetchall()
        #print(f"Tweets: {tweets}")
        list_of_lists = []
        for tup in tweets:
            lst = list(tup)

            if len(lst) > 1 and isinstance(lst[1], str) and lst[1].startswith('static/'):
                lst[1] = lst[1].replace('static/', '')
            if len(lst) > 6 and isinstance(lst[6], str) and lst[6].startswith('static/'):
                lst[6] = lst[6].replace('static/', '')

            # Convert timestamp (index 7) to IST
            if len(lst) > 7 and isinstance(lst[7], str):
                try:
                    naive_dt = datetime.strptime(lst[7], "%Y-%m-%d %H:%M:%S")
                    aware_utc = utc.localize(naive_dt)
                    ist_time = aware_utc.astimezone(ist)
                    lst[7] = ist_time.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    print("Error converting time:", e)

            list_of_lists.append(lst)
        print(f"List of lists: {list_of_lists}")
        
    
        
    return render_template('index.html', user=user, tweets=list_of_lists)
    #return f"Hello {current_user.username}, you are logged in!"

@app.route('/', methods=['POST'])
def index_tweeted():
    get_details_query = text("""
        SELECT id, name, username, picture
        FROM users
        WHERE username=:username
    """)
    with engine.connect() as connection:
        user = connection.execute(get_details_query, {'username': current_user.username}).fetchone()
        print(f"User details: {user}")
        user = list(user)
        fixed_path = user[3].replace("static/", "")
        #fixed_path = "/static/" + fixed_path
        user[3] = fixed_path
        print(f"Fixed path: {user[3]}")
        #print(f"Current user: {current_user.username}, ID: {current_user.id}")
    get_tweets_query = text("""
    SELECT u.id, u.picture, u.username, u.name, t.tweet, t.contains_image, t.image_path, t.created_at
    FROM tweets t
    LEFT JOIN users u ON t.user_id = u.id
    ORDER BY created_at DESC
    """)
    
    contains_image = 0
    tweet = request.form['tweet']
    picture = request.files.get('image')
    filepath = ""
    if picture and allowed_file(picture.filename):
        original_filename = secure_filename(picture.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        picture.save(filepath)
        contains_image = 1
    action = request.form.get('action')
    print("[DEBUG] Action:", action)
    #Normal
    if action == 'Post':
        insert_query = text("""
        INSERT INTO tweets(tweet, user_id, contains_image, image_path)
        VALUES (:tweet, :user_id, :contains_image, :image_path)
        """)
        print(insert_query)
        with engine.connect() as connection:
            connection.execute(insert_query, {
                'tweet': tweet,
                'user_id': current_user.id,
                'contains_image': contains_image,
                'image_path': filepath
            })
            connection.commit()
    elif action == 'Anonymous':
        insert_query = text("""
        INSERT INTO tweets(tweet, contains_image, image_path)
        VALUES (:tweet, :contains_image, :image_path)
        """)
        print(insert_query)
        with engine.connect() as connection:
            connection.execute(insert_query, {
                'tweet': tweet,
                #'user_id': current_user.id,
                'contains_image': contains_image,
                'image_path': filepath
            })
            connection.commit()
    with engine.connect() as connection:
        tweets = connection.execute(get_tweets_query).fetchall()
        #print(f"Tweets: {tweets}")
        list_of_lists = []
        for tup in tweets:
            lst = list(tup)

            if len(lst) > 1 and isinstance(lst[1], str) and lst[1].startswith('static/'):
                lst[1] = lst[1].replace('static/', '')
            if len(lst) > 6 and isinstance(lst[6], str) and lst[6].startswith('static/'):
                lst[6] = lst[6].replace('static/', '')

            # Convert timestamp (index 7) to IST
            if len(lst) > 7 and isinstance(lst[7], str):
                try:
                    naive_dt = datetime.strptime(lst[7], "%Y-%m-%d %H:%M:%S")
                    aware_utc = utc.localize(naive_dt)
                    ist_time = aware_utc.astimezone(ist)
                    lst[7] = ist_time.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    print("Error converting time:", e)

            list_of_lists.append(lst)
        print(f"List of lists: {list_of_lists}")
    return render_template('index.html', user=user, tweets=list_of_lists)
    #return f"Hello {current_user.username}, you are logged in!"

@app.route('/logout')
@login_required
def logouts_user():
    logout_user()
    return redirect(url_for('login')) 
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
    #picture = ""
    picture = request.files['image']
    #filename = secure_filename(picture.filename)
    #picture.save(os.path.join('static/uploads', filename))

    if picture and allowed_file(picture.filename):
        original_filename = secure_filename(picture.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        picture.save(filepath)
    else:
        return render_template("InvalidImage.html"), 404
    
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
            'picture': filepath
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