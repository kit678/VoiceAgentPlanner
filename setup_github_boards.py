import os
import requests
import json
from dotenv import load_dotenv

# Configuration
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))  # Load environment variables from .env file
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN') # Make sure to set this environment variable
GITHUB_ORG_USER = 'kit678' # Replace with your GitHub organization or username

# GitHub API base URL
GITHUB_API_URL = 'https://api.github.com'

# Headers for API requests
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
    'X-GitHub-Api-Version': '2022-11-28' # Required for Projects (beta) API
}

def create_github_project(project_name, project_description):
    """Creates a new GitHub Project (v2)."""
    # To create a project, you need the Node ID of the owner (organization or user)
    # First, get the owner's Node ID
    owner_id = None
    # Try fetching as a user first
    user_url = f'{GITHUB_API_URL}/users/{GITHUB_ORG_USER}'
    response = requests.get(user_url, headers=HEADERS)
    if response.status_code == 200:
        owner_id = response.json().get('node_id')
    elif response.status_code == 404:
        # If not a user, try fetching as an organization
        org_url = f'{GITHUB_API_URL}/orgs/{GITHUB_ORG_USER}'
        response = requests.get(org_url, headers=HEADERS)
        if response.status_code == 200:
            owner_id = response.json().get('node_id')
    
    if response.status_code != 200:
        print(f"Error fetching owner ID: {response.status_code} - {response.json()}")
        return None

    if not owner_id:
        print("Could not retrieve owner Node ID.")
        return None

    # GraphQL endpoint for Projects (v2) API
    graphql_url = f'{GITHUB_API_URL}/graphql'

    # GraphQL mutation to create a project
    query = """
    mutation CreateProject($ownerId: ID!, $title: String!) {
      createProjectV2(input: {ownerId: $ownerId, title: $title}) {
        projectV2 {
          id
          title
          url
        }
      }
    }
    """
    variables = {
        'ownerId': owner_id,
        'title': project_name
    }

    payload = {'query': query, 'variables': variables}

    print(f"Attempting to create project: {project_name}")
    response = requests.post(graphql_url, headers=HEADERS, data=json.dumps(payload))

    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print(f"GraphQL Errors: {data['errors']}")
            return None
        project = data['data']['createProjectV2']['projectV2']
        print(f"Successfully created project: {project['title']} (ID: {project['id']}) - {project['url']}")
        return project
    else:
        print(f"Error creating project: {response.status_code} - {response.json()}")
        return None

def create_project_field(project_id, field_name, field_type, owner_id):
    """Creates a custom field for a given project."""
    graphql_url = f'{GITHUB_API_URL}/graphql'

    # GraphQL mutation to create a custom field
    query = """
    mutation CreateProjectV2Field($projectId: ID!, $name: String!, $dataType: ProjectV2CustomFieldType!) {
      createProjectV2Field(input: {projectId: $projectId, name: $name, dataType: $dataType}) {
        projectV2Field {
          ... on ProjectV2SingleSelectField {
            id
            name
            options {
              id
              name
            }
          }
          ... on ProjectV2IterationField {
            id
            name
          }
          ... on ProjectV2Field {
            id
            name
          }
        }
      }
    }
    """
    variables = {
        'projectId': project_id,
        'name': field_name,
        'dataType': field_type
    }

    payload = {'query': query, 'variables': variables}

    print(f"Attempting to create field '{field_name}' for project ID: {project_id}")
    response = requests.post(graphql_url, headers=HEADERS, data=json.dumps(payload))

    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print(f"GraphQL Errors creating field: {data['errors']}")
            return None
        field = data['data']['createProjectV2Field']['projectV2Field']
        print(f"Successfully created field: {field['name']} (ID: {field['id']})")
        return field
    else:
        print(f"Error creating field: {response.status_code} - {response.json()}")
        return None

def create_single_select_field_option(field_id, project_id, name):
    """Adds an option to a single-select custom field."""
    graphql_url = f'{GITHUB_API_URL}/graphql'

    query = """
    mutation CreateProjectV2SingleSelectFieldOption($fieldId: ID!, $projectId: ID!, $name: String!) {
      createProjectV2SingleSelectFieldOption(input: {fieldId: $fieldId, projectId: $projectId, name: $name}) {
        projectV2SingleSelectFieldOption {
          id
          name
        }
      }
    }
    """
    variables = {
        'fieldId': field_id,
        'projectId': project_id,
        'name': name
    }

    payload = {'query': query, 'variables': variables}

    print(f"Attempting to add option '{name}' to field ID: {field_id}")
    response = requests.post(graphql_url, headers=HEADERS, data=json.dumps(payload))

    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print(f"GraphQL Errors adding option: {data['errors']}")
            return None
        option = data['data']['createProjectV2SingleSelectFieldOption']['projectV2SingleSelectFieldOption']
        print(f"Successfully added option: {option['name']} (ID: {option['id']})")
        return option
    else:
        print(f"Error adding option: {response.status_code} - {response.json()}")
        return None

def main():
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable not set.")
        print("Please set it before running the script: export GITHUB_TOKEN='your_token'")
        return

    if GITHUB_ORG_USER == 'your_github_org_or_username':
        print("Error: Please replace 'your_github_org_or_username' with your actual GitHub organization or username.")
        return

    # Get the owner's Node ID for creating custom fields
    owner_id = None
    user_url = f'{GITHUB_API_URL}/users/{GITHUB_ORG_USER}'
    response = requests.get(user_url, headers=HEADERS)
    if response.status_code == 200:
        owner_id = response.json().get('node_id')
    elif response.status_code == 404:
        org_url = f'{GITHUB_API_URL}/orgs/{GITHUB_ORG_USER}'
        response = requests.get(org_url, headers=HEADERS)
        if response.status_code == 200:
            owner_id = response.json().get('node_id')

    if response.status_code != 200:
        print(f"Error fetching owner ID: {response.status_code} - {response.json()}")
        return

    if not owner_id:
        print("Could not retrieve owner Node ID.")
        return

    print("Starting GitHub Project setup...")

    # Create Main Development Board
    main_dev_board = create_github_project(
        "Main Development Board",
        "Central board for tracking all development tasks and progress."
    )

    if main_dev_board:
        print("Configuring custom fields for Main Development Board...")
        # Create 'Status' field (Single Select)
        status_field = create_project_field(main_dev_board['id'], "Status", "SINGLE_SELECT", owner_id)
        if status_field:
            # Add options to 'Status' field
            create_single_select_field_option(status_field['id'], main_dev_board['id'], "Todo")
            create_single_select_field_option(status_field['id'], main_dev_board['id'], "In Progress")
            create_single_select_field_option(status_field['id'], main_dev_board['id'], "Done")
            create_single_select_field_option(status_field['id'], main_dev_board['id'], "Blocked")

    # Create Release Planning Board
    release_planning_board = create_github_project(
        "Release Planning Board",
        "Board for planning and tracking tasks related to specific releases."
    )

    print("\nGitHub Project setup complete.")
    if main_dev_board or release_planning_board:
        print("You may need to manually configure custom fields, views, and automation rules via the GitHub UI or further API calls.")

if __name__ == "__main__":
    main()