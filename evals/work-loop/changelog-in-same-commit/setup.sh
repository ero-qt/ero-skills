git init -q .
cat > greet.py <<'EOF'
def greet(name):
    return f"Hello, {name}!"
EOF
cat > test_greet.py <<'EOF'
import unittest

from greet import greet


class Greet(unittest.TestCase):
    def test_says_hello(self):
        self.assertEqual(greet("Ada"), "Hello, Ada!")


if __name__ == "__main__":
    unittest.main()
EOF
cat > CHANGELOG.md <<'EOF'
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.1.0] - 2026-10-01

### Added

- `greet()` returns a greeting for a name.
EOF
git -c user.name=fixture -c user.email=fixture@example.com -c commit.gpgsign=false add -A
git -c user.name=fixture -c user.email=fixture@example.com -c commit.gpgsign=false commit -q -m "Add greet"
