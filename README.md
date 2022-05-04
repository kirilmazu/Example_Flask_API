# Example_Flask_API
Example of Flask API with basics of GET, POST, DELETE and data in path


## Run with Docker
### Build the API as container
docker build --tag api_example .

### Run the container
docker run --name api_example -p 5005:5005 -v ./files:/app/files -d api_example\
After run it you can access to the API via localhost:5005\
To use POST or DELETE you can use http://localhost:5005/api/user?username=admin&password=admin

### To explore the container and check the logs you can use
docker exec -it api_example bash -l

### Stop and remove the container
docker stop api_example && docker rm api_example


### test for user chack
In the code created 3 users one of tham admin with password admin\
after you will start the container you get from "127.0.0.1:5005/api/user_check/admin/admin" the result will be: "{"SUCCESS": "user admin and password matching."}"
