import argparse
import os
import pathlib
from openai import OpenAI
import json
import xml.etree.ElementTree as ET

# Configure your OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Command-line arguments
parser = argparse.ArgumentParser(description="Dockerfile and docker-compose.yml generator using OpenAI")
parser.add_argument('project_dir', type=str, help="Project directory")
parser.add_argument('--env-file', type=str, default="", help="Path to an environment file to add to the container")
parser.add_argument('--env-vars', type=str, default="", help="Environment variables to add to the container, format 'KEY=VALUE,KEY2=VALUE2'")
parser.add_argument('--ecs', action='store_true', help="Generate an AWS ECS Fargate task definition if specified")

args = parser.parse_args()

def read_file_content(file_path):
    """
    Reads and returns the content of a file, ideal for configuration files.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def analyze_project_dependencies(file_path):
    """
    Analyzes configuration files to identify dependencies for Node.js, Ruby, and Python projects.
    """
    dependencies = []
    if file_path.name == "package.json":
        content = read_file_content(file_path)
        if content:
            try:
                data = json.loads(content)
                dependencies = list(data.get('dependencies', {}).keys())
                return f"Node.js dependencies: {', '.join(dependencies)}."
            except json.JSONDecodeError:
                return "Error analyzing package.json."
    elif file_path.name == "Gemfile":
        content = read_file_content(file_path)
        if content:
            # Simplified parsing logic for demonstration purposes
            for line in content.splitlines():
                if line.startswith('gem'):
                    gem_name = line.split()[1].strip('"').strip("'")
                    dependencies.append(gem_name)
            return f"Ruby dependencies (Gemfile): {', '.join(dependencies)}."
    elif file_path.name in ["requirements.txt", "Pipfile"]:
        content = read_file_content(file_path)
        if content:
            # For requirements.txt, simply list each line as a dependency
            # For Pipfile, more complex parsing would be needed
            dependencies = [line for line in content.splitlines() if line and not line.startswith('#')]
            python_deps_desc = "Python dependencies (Pipfile)" if file_path.name == "Pipfile" else "Python dependencies (requirements.txt)"
            return f"{python_deps_desc}: {', '.join(dependencies)}."
    elif file_path.suffix == ".csproj":
        content = read_file_content(file_path)
        if content:
            try:
                tree = ET.ElementTree(ET.fromstring(content))
                packages = [element.attrib['Include'] for element in tree.findall(".//PackageReference")]
                return f"C# dependencies: {', '.join(packages)}."
            except ET.ParseError:
                return "Error analyzing .csproj."
    return ""

def summarize_project_structure(directory):
    """
    Generates a detailed summary of the project, including dependency configuration files
    and the directory structure hierarchy.
    """
    dependency_summary = []
    directory_structure = set()
    
    for path in pathlib.Path(directory).rglob('*'):
        if path.is_file():
            analysis_result = analyze_project_dependencies(path)
            if analysis_result:
                dependency_summary.append(analysis_result)
        else:
            relative_path = path.relative_to(directory)
            directory_structure.add(str(relative_path.parent))
    
    # Format the directory structure for readability
    structured_dirs = "\n".join(sorted(directory_structure))
    dependencies_info = " ".join(dependency_summary)
    project_summary = f"Detected directories:\n{structured_dirs}\n\nDependencies info: {dependencies_info}"
    
    return project_summary


def generate_dockerfile_with_openai(project_dir, env_file="", env_vars=""):
    project_summary = summarize_project_structure(project_dir)
    prompt_dockerfile = f"Based on a project that {project_summary}, generate an appropriate Dockerfile. Apply best practices including non-root users and multistage if possible."
    
    if env_file or env_vars:
        env_details = f"Include environment variables from {env_file} " if env_file else ""
        env_details += f"and direct environment variables {env_vars}." if env_vars else ""
        prompt_dockerfile += f" {env_details}"
    
    response = client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt=prompt_dockerfile,
    temperature=0,
    max_tokens=2816,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0)
    
    dockerfile = response.choices[0].text.strip()
    print("\nGenerated Dockerfile:\n", dockerfile)


def generate_docker_compose_with_openai(project_dir, env_file="", env_vars=""):
    project_summary = summarize_project_structure(project_dir)
    prompt = f"Based on a project that {project_summary}, generate an appropriate docker-compose.yml. Apply best practices."
    
    response = client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt=prompt,
    temperature=0,
    max_tokens=2816,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0)
    
    docker_compose = response.choices[0].text.strip()
    print("\nGenerated docker-compose.yml:\n", docker_compose)

def generate_ecs_task_definition_with_openai(project_dir):
    project_summary = summarize_project_structure(project_dir)
    prompt_ecs = f"Generate an AWS ECS Fargate task definition for a project that {project_summary}, considering best practices."
    
    response = client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt=prompt_ecs,
    temperature=0,
    max_tokens=2816,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0)
    
    task_definition = response.choices[0].text.strip()
    print("\nGenerated AWS ECS Fargate task definition:\n", task_definition)


if __name__ == "__main__":
    env_details = ""
    if args.env_file or args.env_vars:
        if args.env_file:
            env_details += f"Add the file {args.env_file} to the root of the app container, preserving its name. "
        if args.env_vars:
            vars_list = args.env_vars.split(',')
            env_vars_formatted = ", ".join([f"{var.split('=')[0]} for use within the container" for var in vars_list])
            env_details += f"Include environment variables: {env_vars_formatted}."
        
        print("Including environment configuration:")
        print(env_details)

    generate_dockerfile_with_openai(args.project_dir, env_file=args.env_file, env_vars=args.env_vars)
    print("\n-----------------------------------------\n")
    generate_docker_compose_with_openai(args.project_dir, env_file=args.env_file, env_vars=args.env_vars)
    
    if args.ecs:
        print("\n-----------------------------------------\n")
        generate_ecs_task_definition_with_openai(args.project_dir)

