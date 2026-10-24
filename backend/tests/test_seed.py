import os

def test_manage_py_exists():
    assert os.path.exists("manage.py"), "manage.py must exist in backend root"

def test_seed_script_runnable():
    """Verify that manage.py can run and exposes commands without crashing"""
    result = os.system("python manage.py --help > /dev/null 2>&1")
    assert result == 0, "manage.py --help should execute successfully"
