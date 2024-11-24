import hashlib
import sqlite3
from flask import Flask, request, jsonify
import logging
import os


# Init the logger
log_level = os.getenv('LOG_LEVEL', logging.DEBUG)
log_file = 'example_API_log.log'
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(funcName)s - %(message)s', level=log_level, filename=log_file)

# Database configuration
DB_PATH = os.getenv('DB_PATH', "example_db.db")

def init_db():
    """Create DB if not exists and create users table"""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users (ID INTEGER PRIMARY KEY, user_name TEXT UNIQUE, password TEXT)")
        conn.commit()


# Get all users
def get_users() -> list:
    """
    Get list of all users.
    Returns:
        list: [[index(int),username(str),password(str)],[...]] 
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Get available VM name
    try:
        cur.execute("SELECT * FROM users")
    except sqlite3.OperationalError as e:
        logging.error("Can't execute the query:\n{0}".format(e))
        return "{\"ERROR\": \"Can't execute the query.\"}"
    result = cur.fetchall()
    conn.close()
    return result


def add_user(username:str, password:str) -> str:
    """
    Add user with hashed password to DB.
    Args:
        username (str): Username to save.
        password (str): Plain text password.
    Returns:
        str: SUCCESS if not get error, json with ERROR if failed to add the user
    """
    hashed_password = hash_password(password)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (user_name, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            return "SUCCESS"
        except sqlite3.IntegrityError:
            return "ERROR: User already exists"
        except sqlite3.OperationalError as e:
            logging.error(f"Can't execute the query: {e}")
            return "ERROR: Can't execute the query"


def delete_user(username:str, password:str) -> str:
    """
    Delete user (with the same user and password)
    Args:
        username (str): Username.
        password (str): Plain text password.
    Returns:
        str: SUCCESS if not get error, json with ERROR if failed to delete the user
    """
    hashed_password = hash_password(password)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM users WHERE user_name=? AND password=?", (username, hashed_password))
            if cur.rowcount == 0:
                return "ERROR: User not found or incorrect password"
            conn.commit()
            return "SUCCESS"
        except sqlite3.OperationalError as e:
            logging.error(f"Can't execute the query: {e}")
            return "ERROR: Can't execute the query"


def get_user_password(username:str) -> str:
    """
    Get user password
    Args:
        username (str): username to get password of.
    Returns:
        str: user hashed password if found, json with ERROR in not.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT password FROM users WHERE user_name=?", (username,))
            result = cur.fetchone()
            return result[0] if result else None
        except sqlite3.OperationalError as e:
            logging.error(f"Can't execute the query: {e}")
            return None


def user_exist(username:str) -> bool:
    """
    Check if username exist in the DB
    Args:
        username (str): Username to check.
    Returns:
        bool: true if exist.
    """
    return get_user_password(username) is not None

def hash_password(password:str) -> str:
    """
    Hash string with sha256
    Args:
        password (str): password string to hash.
    Returns:
        str: hashed string from password string
    """
    return hashlib.sha256(password.encode()).hexdigest()

def check_user_password(username:str, password:str) -> bool:
    """
    Check if the input password hashed and compered with saved password.
    Args:
        username (str): User name of the user to check.
        password (str): plain text password to compere with saved password.
    Returns:
        bool: True if password equals to user password (comper hashed), False if not equals or failed to get user password. 
    """
    user_pass = get_user_password(username)
    return user_pass == hash_password(password) if user_pass else False

# Init the DB
init_db()
# Add admin user
add_user("admin", "admin")
# Add tests users
add_user("test1", "test1")
add_user("user_name", "Password")

# Flask init
app = Flask(__name__)

@app.route("/")
def welcome():
    return """
    <h1>Welcome to example api V0.2</h1>
    <h2>API's:</h2>
    <h3>POST/GET/DELETE</h3>
    <p>username and password are required</p>
    <p>/api/user</p>
    <p>check user: /api/user_check (POST/GET)</p>
    <h3>RAW</h3>
    <p>add user: /api/add_user/username/password</p>
    <p>check user: /api/user_check/username/password</p>
    <p>/api/get_users</p>
    <p>/api/get_logs</p>
    """

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return welcome()


# Get all users with GET method
@app.route("/api/user/", methods=['GET'])
def route_get_users():
    return jsonify(get_users())


# Add user with POST method
@app.route("/api/user/", methods=['POST'])
def route_add_user():
    # Get username and password from the request
    username = request.args.get('username', default=None, type=str)
    password = request.args.get('password', default=None, type=str)
    # Check if get all the info you need
    if not username or not password:
        logging.debug("username or password is None.")
        return jsonify({"ERROR": "username and password are required"}), 400
    result = add_user(username, password)
    if result == "SUCCESS":
        return jsonify({"SUCCESS": f"user {username} created"}), 201
    return jsonify({"ERROR": "Failed to add the user"}), 400


# Delete user with DELETE method
@app.route("/api/user/", methods=['DELETE'])
def route_delete_user():
    # Get username and password from the request
    username = request.args.get('username', default=None, type=str)
    password = request.args.get('password', default=None, type=str)
    # Check if get all the info you need
    if not username or not password:
        logging.debug("username or password is None.")
        return jsonify({"ERROR": "username and password are required"}), 400
    result = delete_user(username, password)
    if result == "SUCCESS":
        return jsonify({"SUCCESS": f"user {username} deleted"}), 200
    return jsonify({"ERROR": "Failed to delete the user"}), 400

# Add user with raw url
@app.route("/api/add_user/<username>/<password>")
def route_raw_add_user(username=None, password=None):
    # Check if get all the info you need
    if username is None or password is None:
        logging.debug("username or password is None.")
        return jsonify({"ERROR": "username and password is required."}), 400

    result = add_user(username, password)
    if result == "SUCCESS":
        return jsonify({"SUCCESS": f"user {username} created"}), 201
    return jsonify({"ERROR": "Failed to add the user"}), 400

# Check if user exist
@app.route("/api/user_check/<username>/<password>")
def route_raw_user_check(username, password):
    if check_user_password(username, password):
        return jsonify({"SUCCESS": f"user {username} and password matching"}), 200
    return jsonify({"FAILED": f"user {username} or password is wrong"}), 401

# Check if user exist with GET method
@app.route("/api/user_check/", methods=['POST', 'GET'])
def route_user_check():
    # Get username and password from the request
    username = request.args.get('username', default=None, type=str)
    password = request.args.get('password', default=None, type=str)
    logging.debug(f"user_check: username {username}, password {password}")
    return route_raw_user_check(username, password)


# Get all users with raw url
@app.route("/api/get_users")
def route_raw_get_user():
    return jsonify(get_users())

# Get all logs with raw url
@app.route("/api/get_logs")
def route_raw_get_logs():
    # Get all logs
    try:
        with open(log_file, 'r') as f:
            contents = f.read()
        return jsonify(contents), 200
    except Exception as e:
        logging.error(f"Can't read the log file: {e}")
        return jsonify({"ERROR": "Failed to get the logs"}), 500
