1. Remember to install the required libraries:
   pip install -r requirements.txt
   
2. Add yuur OpenAI API Key as an env variable:
   export env OPENAI_API_KEY="your_openai_key"
  
3. Run the script:
   usage: dockerfile-generator.py [-h] [--env-file ENV_FILE] [--env-vars ENV_VARS] [--ecs] project_dir
   Dockerfile and docker-compose.yml generator using OpenAI

   positional arguments:
   project_dir          Project directory

   options:
    -h, --help           show this help message and exit
    --env-file ENV_FILE  Path to an environment file to add to the container
    --env-vars ENV_VARS  Environment variables to add to the container, format 'KEY=VALUE,KEY2=VALUE2'
    --ecs                Generate an AWS ECS Fargate task definition if specified
