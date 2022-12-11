import hashlib
import sqlite3
from flask import Response, Flask, request
import logging
import os
import json


# Init the logger
log_level = os.getenv('LOG_LEVEL')
if log_level != logging.ERROR and log_level != logging.INFO and log_level != logging.DEBUG:
    log_level = logging.DEBUG
    #log_level = logging.INFO
log_file = 'example_API_log.log'
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(funcName)s - %(message)s', level=log_level, filename=log_file)

# current_DB : the last 24 hours in time interval of 1 min
DB_PATH = os.getenv('DB_PATH')
if DB_PATH is None or DB_PATH == "":
    DB_PATH = "example_db.db"


###
# Create DB if not exists and create users table
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Create users if not exist
    cur.execute("CREATE TABLE IF NOT EXISTS users (ID INTEGER PRIMARY KEY, user_name TEXT, password TEXT)")
    conn.commit()
    conn.close()


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
    # Hash the password to save
    password = hash_password(password)
    # Get connection to db
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("INSERT OR REPLACE INTO users (user_name, password) VALUES (?, ?)", (username, password,))
        conn.commit()
    except sqlite3.OperationalError as e:
        logging.error("Can't execute the query:\n{0}".format(e))
        return "{\"ERROR\": \"Can't execute the query.\"}"
    conn.close()
    return "SUCCESS"


def delete_user(username:str, password:str) -> str:
    """
        Delete user (with the same user and password)
    Args:
        username (str): Username.
        password (str): Plain text password.
    Returns:
        str: SUCCESS if not get error, json with ERROR if failed to delete the user
    """
    # Hash the password to save
    password = hash_password(password)
    # Get connection to db
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM users WHERE user_name=? and password=?", (username, password,))
        conn.commit()
    except sqlite3.OperationalError as e:
        logging.error("Can't execute the query:\n{0}".format(e))
        return "{\"ERROR\": \"Can't execute the query.\"}"
    conn.close()
    return "SUCCESS"


def get_user_password(username:str) -> str:
    """
        Get user password
    Args:
        username (str): username to get password of.
    Returns:
        str: user hashed password if found, json with ERROR in not.
    """
    # Get connection to db
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("SELECT password FROM users WHERE user_name=?", (username,))
        result = cur.fetchall()
        conn.close()
        return result[0][0]
    except sqlite3.OperationalError as e:
        #logging.error("Can't execute the query:\n{0}".format(e))
        return "{\"ERROR\": \"Can't execute the query.\"}"
    except Exception as e:
        return "{\"ERROR\": \"Get user failed.\"}"


def user_exist(username:str) -> bool:
    """
        Check if username exist in the DB
    Args:
        username (str): Username to check.
    Returns:
        bool: true if exist.
    """
    password = get_user_password(username)
    if "ERROR" not in password:
        return True
    return False

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
    #get_user_password can return string with ERROR if user not exist or wuery failed
    if "ERROR" in user_pass:
        return False
    return user_pass == hash_password(password)

###
# Init the DB
init_db()
# Add admin user
add_user("admin", "admin")
# Add tests users
add_user("test1", "test1")
add_user("user_name", "Password")

# Flask init
app = Flask(__name__)
# API / rout
@app.route("/")
def welcome():
    index_string = """
    <h1>Welcome to example api V0.1</h1>
    <h2>API's:</h2>
    <h3>POST/GET/DELETE</h3>
    <p>username and password is required</p>
    <p>/api/user</p>
    <p>check user: /api/user_check (POST/GET)</p>
    <h3>RAW</h3>
    <p>add user: /api/add_user/username/password</p>
    <p>check user: /api/user_check/username/password</p>
    <p>/api/get_users</p>
    <p>/api/get_logs</p>
    """
    return index_string


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return welcome()


# Get all users with GET method
@app.route("/api/user/", methods=['GET'])
def route_get_users():
    # Get all users
    users = get_users()
    # API return
    return json.dumps(users, indent=4)


# Add user with POST method
@app.route("/api/user/", methods=['POST'])
def route_add_user():
    # Get username and password from the request
    username = request.args.get('username', default=None, type=str)
    password = request.args.get('password', default=None, type=str)
    # Check if get all the info you need
    if username is None or password is None:
        logging.debug("username or password is None.")
        return "{ \"ERROR\" : \"username and password is required.\" }"
    result = add_user(username, password)
    if "ERROR" in result:
        return "{ \"ERROR\" : \"Failed to add the user.\" }"
    # API return
    return "{{\"SUCCESS\": \"user {0} created.\"}}".format(username)


# Delete user with DELETE method
@app.route("/api/user/", methods=['DELETE'])
def route_delete_user():
    # Get username and password from the request
    username = request.args.get('username', default=None, type=str)
    password = request.args.get('password', default=None, type=str)
    # Check if get all the info you need
    if username is None or password is None:
        logging.debug("username or password is None.")
        return "{ \"ERROR\" : \"username and password is required.\" }"
    result = delete_user(username, password)
    if "ERROR" in result:
        return "{ \"ERROR\" : \"Failed to delete the user.\" }"
    # API return
    return "{{\"SUCCESS\": \"user {0} deleted.\"}}".format(username)


# Add user with raw url
@app.route("/api/add_user/<username>/<password>")
def route_raw_add_user(username=None, password=None):
    # Check if get all the info you need
    if username is None or password is None:
        logging.debug("username or password is None.")
        return "{ \"ERROR\" : \"username and password is required.\" }"
    result = add_user(username, password)
    if "ERROR" in result:
        return "{ \"ERROR\" : \"Failed to add the user.\" }"
    # API return
    return "{{\"SUCCESS\": \"user {0} created.\"}}".format(username)


# Check if user exist
@app.route("/api/user_check/<username>/<password>")
def route_raw_user_check(username=None, password=None):
    # Check if get all the info you need
    if username is None or password is None:
        logging.debug("username or password is None.")
        return "{ \"ERROR\" : \"username and password is required.\" }"
    result = get_user_password(username)
    if "ERROR" in result:
        return "{ \"ERROR\" : \"Failed to get the user.\" }"
    try:
        # In case if user not found it will fail to get value from result[0][0]
        if str(result) == hash_password(password):
            return "{{\"SUCCESS\": \"user {0} and password matching.\"}}".format(username)
    except Exception as e:
        logging.error("Can't get user or password, error:\n{0}".format(e))
    # API return
    return "{{\"FAILED\": \"user {0} or password is wrong.\"}}".format(username)


# Check if user exist with GET method
@app.route("/api/user_check/", methods=['POST', 'GET'])
def route_user_check():
    # Get username and password from the request
    username = request.args.get('username', default=None, type=str)
    password = request.args.get('password', default=None, type=str)
    logging.debug("user_check: username {0}\n password {1}".format(username, password))
    return route_raw_user_check(username, password)


# Get all users with raw url
@app.route("/api/get_users")
def route_raw_get_user():
    # Get all users
    users = get_users()
    # API return
    return json.dumps(users, indent=4)


# Get all logs with raw url
@app.route("/api/get_logs")
def route_raw_get_logs():
    # Get all logs
    try:
        with open(log_file) as f:
            contents = f.read()
            return json.dumps(contents, indent=4)
    except Exception as e:
        logging.error("Can't execute the query:\n{0}".format(e))
        # API return
        return "{ \"ERROR\" : \"Failed get the logs.\" }"
