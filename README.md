# Example_Flask_API
A simple Flask API example demonstrating basic REST operations (GET, POST, DELETE) and URL path parameters. This project implements basic user management with SQLite database storage.

## Features

- User management (create, read, delete)
- Password hashing
- User authentication
- SQLite database storage
- Logging functionality
- Docker support

## API Endpoints

### REST Endpoints
- `GET /api/user/` - Get all users
- `POST /api/user/` - Create new user (requires username & password)  
- `DELETE /api/user/` - Delete user (requires username & password)
- `GET/POST /api/user_check/` - Verify user credentials

### Raw URL Endpoints
- `/api/add_user/<username>/<password>` - Create new user
- `/api/user_check/<username>/<password>` - Verify user credentials
- `/api/get_users` - Get all users
- `/api/get_logs` - Get application logs


## Run with Docker
### Build the API as container
docker build --tag api_example .

### Run the container
docker run --name api_example -p 5005:5005 -v ./files:/app/files -d api_example.\
After run it you can access to the API via http://localhost:5005 (get on this url will show API options)\
To use POST or DELETE you can use http://localhost:5005/api/user?username=admin&password=admin

### To explore the container and check the logs you can use
docker exec -it api_example bash -l

### Stop and remove the container
docker stop api_example && docker rm api_example


### test for user chack
In the code created 3 users one of tham admin with password admin\
after you will start the container you get from "http://localhost:5005/api/user_check/admin/admin" the result will be: "{"SUCCESS": "user admin and password matching."}"
