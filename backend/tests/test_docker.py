import os
import pytest

def test_docker_compose_exists():
    assert os.path.exists("../docker-compose.yml"), "docker-compose.yml must exist in project root"

def test_dockerfile_exists():
    assert os.path.exists("Dockerfile"), "Dockerfile must exist in backend"
