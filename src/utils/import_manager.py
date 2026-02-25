"""
Import Manager - Handles both local and GitHub imports
Provides unified interface for accessing skills, agents, and utilities from:
1. Local project (relative imports)
2. claude-global-library (GitHub raw URLs)
"""

import sys
import urllib.request
import json
from pathlib import Path
from typing import Any, Optional, Dict

# GitHub base URLs
GITHUB_BASE = "https://raw.githubusercontent.com/piyushmakhija28"
GLOBAL_LIB_URL = f"{GITHUB_BASE}/claude-global-library/main"
INSIGHT_URL = f"{GITHUB_BASE}/claude-insight/main"

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent


class ImportManager:
    """Unified import manager for local and GitHub resources."""
    
    @staticmethod
    def get_skill(skill_name: str) -> Optional[Dict]:
        """
        Load skill from claude-global-library.
        
        Usage:
            skill = ImportManager.get_skill('docker')
            # Returns: skill definition from GitHub
        """
        url = f"{GLOBAL_LIB_URL}/skills/{skill_name}/skill.md"
        try:
            with urllib.request.urlopen(url) as response:
                return {
                    'name': skill_name,
                    'content': response.read().decode('utf-8'),
                    'source': 'github',
                    'url': url
                }
        except urllib.error.HTTPError:
            return None
    
    @staticmethod
    def get_agent(agent_name: str) -> Optional[Dict]:
        """
        Load agent from claude-global-library.
        
        Usage:
            agent = ImportManager.get_agent('orchestrator-agent')
            # Returns: agent definition from GitHub
        """
        url = f"{GLOBAL_LIB_URL}/agents/{agent_name}/agent.md"
        try:
            with urllib.request.urlopen(url) as response:
                return {
                    'name': agent_name,
                    'content': response.read().decode('utf-8'),
                    'source': 'github',
                    'url': url
                }
        except urllib.error.HTTPError:
            return None
    
    @staticmethod
    def get_policy(policy_path: str) -> Optional[str]:
        """
        Load policy from claude-insight.
        
        Usage:
            policy = ImportManager.get_policy('01-sync-system/context-management/README.md')
            # Returns: policy content from GitHub
        """
        url = f"{INSIGHT_URL}/scripts/architecture/{policy_path}"
        try:
            with urllib.request.urlopen(url) as response:
                return response.read().decode('utf-8')
        except urllib.error.HTTPError:
            return None
    
    @staticmethod
    def get_local_module(module_path: str) -> Any:
        """
        Load local module (within this project).
        
        Usage:
            services = ImportManager.get_local_module('services.monitoring.metrics_collector')
            # Returns: imported module
        """
        parts = module_path.split('.')
        module = __import__(module_path)
        for part in parts[1:]:
            module = getattr(module, part)
        return module
    
    @staticmethod
    def list_skills() -> Optional[list]:
        """List all available skills from claude-global-library."""
        url = f"{GLOBAL_LIB_URL}/skills/INDEX.md"
        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8')
                # Parse INDEX.md to extract skill list
                return content.split('\n')
        except urllib.error.HTTPError:
            return None
    
    @staticmethod
    def list_agents() -> Optional[list]:
        """List all available agents from claude-global-library."""
        url = f"{GLOBAL_LIB_URL}/agents/README.md"
        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8')
                # Parse README.md to extract agent list
                return content.split('\n')
        except urllib.error.HTTPError:
            return None


# Quick reference URLs
SKILL_URLS = {
    'docker': f"{GLOBAL_LIB_URL}/skills/docker/skill.md",
    'kubernetes': f"{GLOBAL_LIB_URL}/skills/kubernetes/skill.md",
    'python-system-scripting': f"{GLOBAL_LIB_URL}/skills/system/python-system-scripting/SKILL.md",
    'java-spring-boot': f"{GLOBAL_LIB_URL}/skills/backend/java-spring-boot-microservices/SKILL.md",
}

AGENT_URLS = {
    'orchestrator': f"{GLOBAL_LIB_URL}/agents/orchestrator-agent/agent.md",
    'devops': f"{GLOBAL_LIB_URL}/agents/devops-engineer/agent.md",
    'qa-testing': f"{GLOBAL_LIB_URL}/agents/qa-testing-agent/agent.md",
    'spring-boot-microservices': f"{GLOBAL_LIB_URL}/agents/spring-boot-microservices/agent.md",
}

POLICY_URLS = {
    'sync-system': f"{INSIGHT_URL}/scripts/architecture/01-sync-system/README.md",
    'standards-system': f"{INSIGHT_URL}/scripts/architecture/02-standards-system/README.md",
    'execution-system': f"{INSIGHT_URL}/scripts/architecture/03-execution-system/README.md",
}


if __name__ == '__main__':
    # Test
    print("Testing ImportManager...")

    # Test skill
    docker_skill = ImportManager.get_skill('docker')
    if docker_skill:
        print("[OK] Loaded skill: {} ({} bytes)".format(docker_skill['name'], len(docker_skill['content'])))
    else:
        print("[FAIL] Could not load docker skill")

    # Test agent
    orchestrator = ImportManager.get_agent('orchestrator-agent')
    if orchestrator:
        print("[OK] Loaded agent: {} ({} bytes)".format(orchestrator['name'], len(orchestrator['content'])))
    else:
        print("[FAIL] Could not load orchestrator agent")

    print("\nAvailable URLs:")
    print("Skills: {}".format(list(SKILL_URLS.keys())))
    print("Agents: {}".format(list(AGENT_URLS.keys())))
    print("Policies: {}".format(list(POLICY_URLS.keys())))
