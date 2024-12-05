import os
import subprocess
import json
import logging
from datetime import datetime

# Constants
PLUGIN_NAME = 'softaculous'
SOFTACULOUS_API = 'https://api.softaculous.com/v1'
PYTHON_VERSION = '3.11'
LOG_FILE = 'build_plugin.log'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=LOG_FILE,
    filemode='w'
)
logger = logging.getLogger(__name__)

def run_command(command):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logger.info(f"Command: {command}\nOutput: {result.stdout}\nError: {result.stderr}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Command: {command}\nError: {e.stderr}")
        raise

def validate_project_structure():
    """Validate the project structure and create necessary files if they don't exist."""
    if not os.path.exists('VERSION'):
        with open('VERSION', 'w') as f:
            f.write('1.0.0')
        logger.info("Created VERSION file with initial version 1.0.0")

    if not os.path.exists('requirements.txt'):
        with open('requirements.txt', 'w') as f:
            f.write('requests==2.31.0\nPyYAML==6.0.1\npython-dotenv==1.0.0\n')
        logger.info("Created requirements.txt file with initial dependencies")

def generate_version():
    """Generate the version from the VERSION file."""
    try:
        with open('VERSION', 'r') as f:
            version = f.read().strip()
        logger.info(f"Current version: {version}")
        return version
    except FileNotFoundError:
        logger.error("VERSION file not found")
        raise

def create_plugin_structure(version):
    """Create the comprehensive plugin structure."""
    PLUGIN_DIR = 'softaculous'
    os.makedirs(PLUGIN_DIR, exist_ok=True)

    # Create softaculous_main.py
    with open(f'{PLUGIN_DIR}/softaculous_main.py', 'w') as f:
        f.write('''\
#!/usr/bin/python3
# coding: utf-8
import os
import sys
import json
import requests
import logging
from typing import Dict, List, Any

class SoftaculousPlugin:
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename='/var/log/softaculous_plugin.log'
        )
        self.logger = logging.getLogger(__name__)
        self.config = {
            'api_endpoint': 'https://api.softaculous.com/v1',
            'cache_dir': '/tmp/softaculous_cache'
        }
        os.makedirs(self.config['cache_dir'], exist_ok=True)

    def fetch_application_list(self) -> List[Dict[str, Any]]:
        try:
            response = requests.get(f"{self.config['api_endpoint']}/applications", timeout=10)
            response.raise_for_status()
            applications = response.json().get('applications', [])
            self.logger.info(f"Fetched {len(applications)} applications")
            return applications
        except requests.RequestException as e:
            self.logger.error(f"Error fetching applications: {e}")
            return []

    def install_application(self, app_name: str, domain: str, path: str = '/') -> Dict[str, Any]:
        try:
            payload = {'application': app_name, 'domain': domain, 'path': path}
            response = requests.post(f"{self.config['api_endpoint']}/install", json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            self.logger.info(f"Installation of {app_name} initiated")
            return {'status': 'success', 'message': f"{app_name} installation started", 'details': result}
        except requests.RequestException as e:
            error_msg = f"Installation failed: {e}"
            self.logger.error(error_msg)
            return {'status': 'error', 'message': error_msg}

    def get_application_details(self, app_name: str) -> Dict[str, Any]:
        try:
            response = requests.get(f"{self.config['api_endpoint']}/applications/{app_name}", timeout=10)
            response.raise_for_status()
            details = response.json()
            self.logger.info(f"Details for {app_name} retrieved")
            return details
        except requests.RequestException as e:
            error_msg = f"Failed to retrieve {app_name} details: {e}"
            self.logger.error(error_msg)
            return {'error': error_msg}

def get_list(args):
    plugin = SoftaculousPlugin()
    return plugin.fetch_application_list()

def install(args):
    plugin = SoftaculousPlugin()
    return plugin.install_application(args.get('application', ''), args.get('domain', ''))

def get_application_info(args):
    plugin = SoftaculousPlugin()
    return plugin.get_application_details(args.get('application', ''))
''')
    os.chmod(f'{PLUGIN_DIR}/softaculous_main.py', 0o755)
    logger.info("Created and set permissions for softaculous_main.py")

    # Create info.json
    with open(f'{PLUGIN_DIR}/info.json', 'w') as f:
        json.dump({
            "title": "Softaculous Application Installer",
            "name": "softaculous",
            "ps": "One-click installation for 400+ web applications",
            "versions": version,
            "checks": "/www/server/panel/plugin/softaculous",
            "author": "Softaculous Team",
            "home": "https://softaculous.com"
        }, f, indent=2)
    logger.info("Created info.json")

    # Create index.html
    with open(f'{PLUGIN_DIR}/index.html', 'w') as f:
        f.write('''\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Softaculous Application Installer</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        select, input { margin: 10px 0; padding: 5px; width: 100%; }
        #result { background-color: #f4f4f4; padding: 10px; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>Softaculous Web Application Installer</h1>
    <form id="installForm">
        <label for="application">Select Application:</label>
        <select id="application" required>
            <option value="">Choose an Application</option>
            <option value="wordpress">WordPress</option>
            <option value="joomla">Joomla</option>
            <option value="drupal">Drupal</option>
        </select>

        <label for="domain">Domain:</label>
        <input type="text" id="domain" placeholder="example.com" required>

        <label for="path">Installation Path (Optional):</label>
        <input type="text" id="path" placeholder="/" value="/">

        <button type="submit">Install Application</button>
    </form>

    <div id="result"></div>

    <script>
        document.getElementById('installForm').addEventListener('submit', function(e) {
            e.preventDefault();
            var application = document.getElementById('application').value;
            var domain = document.getElementById('domain').value;
            var path = document.getElementById('path').value;

            fetch('/plugin/softaculous/install', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ application: application, domain: domain, path: path })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('result').innerHTML = `
                    <h3>Installation Result</h3>
                    <pre>${JSON.stringify(data, null, 2)}</pre>
                `;
            })
            .catch(error => {
                document.getElementById('result').innerHTML = `
                    <h3>Error</h3>
                    <pre>${error}</pre>
                `;
            });
        });
    </script>
</body>
</html>
''')
    logger.info("Created index.html")

    # Create install.sh
    with open(f'{PLUGIN_DIR}/install.sh', 'w') as f:
        f.write('''\
#!/bin/bash
set -e

PLUGIN_DIR="/www/server/panel/plugin/softaculous"

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

check_dependencies() {
    local dependencies=("python3" "pip" "curl")
    for dep in "${dependencies[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            echo "Error: $dep is not installed"
            exit 1
        fi
    done
}

install_python_deps() {
    pip install requests PyYAML python-dotenv
}

main() {
    echo "Starting Softaculous Plugin Installation..."
    check_dependencies
    install_python_deps
    echo "Softaculous Plugin installed successfully."
}

main
''')
    os.chmod(f'{PLUGIN_DIR}/install.sh', 0o755)
    logger.info("Created and set permissions for install.sh")

def build_docker_image(version):
    """Build and push the Docker image."""
    try:
        run_command(f'docker build -t softaculous-plugin:{version} .')
        run_command(f'docker push softaculous-plugin:{version}')
        logger.info(f"Built and pushed Docker image softaculous-plugin:{version}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to build or push Docker image: {e}")
        raise

def commit_and_push_changes(version):
    """Commit and push changes to the repository."""
    try:
        run_command('git add .')
        run_command(f'git commit -m "Build and release version {version}"')
        run_command('git push')
        logger.info(f"Committed and pushed changes for version {version}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to commit and push changes: {e}")
        raise

def create_release(version):
    """Create a release on GitHub."""
    try:
        run_command(f'gh release create v{version} --title "Release v{version}" --notes "Release version {version}"')
        logger.info(f"Created release v{version}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create release: {e}")
        raise

def main():
    """Main function to orchestrate the build process."""
    try:
        validate_project_structure()
        version = generate_version()
        create_plugin_structure(version)
        build_docker_image(version)
        commit_and_push_changes(version)
        create_release(version)
        logger.info("Build and release process completed successfully")
    except Exception as e:
        logger.error(f"Build and release process failed: {e}")
        raise

if __name__ == '__main__':
    main()
