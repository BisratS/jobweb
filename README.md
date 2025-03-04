# Job Web

## Introduction
This project is dockerized to ensure a consistent and reproducible environment for development and deployment.

## Prerequisites
- Docker installed on your machine. You can download it from [here](https://www.docker.com/get-started).

## Building the Docker Image
 Replace "job-web" with your favorite  build name
- ``` docker build -t  job-web .  ```

## Running Build image
 Run Build docker image by using below command 
 You can change the port as you want plus make sure the name you used in the Build phase matches Running phase
- ```docker run -p 5000:5000 job-web```

## Making Changes to the Code
If you make changes to the code, you need to rebuild the Docker image to include those changes. Follow these steps:

1. Stop the running container (if any):
   - List running containers to find the container ID or name:
     ```sh
     docker ps
     ```
   - Stop the container using its ID or name:
     ```sh
     docker stop <container_id_or_name>
     ```

2. Rebuild the Docker image:
   - ```docker build -t job-web .```

3. Run the updated Docker image:
   - ```docker run -p 5000:5000 job-web```

By following these steps, you ensure that your changes are reflected in the running Docker container.