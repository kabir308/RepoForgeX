"""AI-powered features for repository management."""
import logging
import re
from typing import Any

logger = logging.getLogger("repoforgex.ai_features")


class RepositoryNameSuggester:
    """Suggests repository names based on description and best practices."""

    # Common tech keywords and their abbreviations
    TECH_KEYWORDS = {
        "application": "app",
        "service": "svc",
        "library": "lib",
        "framework": "fw",
        "interface": "if",
        "database": "db",
        "microservice": "ms",
        "api": "api",
        "backend": "be",
        "frontend": "fe",
        "platform": "platform",
        "engine": "engine",
        "tool": "tool",
        "utility": "util",
    }

    LANGUAGE_PREFIXES = {
        "python": "py",
        "javascript": "js",
        "typescript": "ts",
        "java": "java",
        "golang": "go",
        "rust": "rs",
        "ruby": "rb",
    }

    @classmethod
    def suggest_names(cls, description: str, current_name: str = "", count: int = 3) -> list[str]:
        """
        Suggest repository names based on description.

        Args:
            description: Repository description
            current_name: Current repository name (if any)
            count: Number of suggestions to return

        Returns:
            List of suggested names
        """
        if not description:
            return []

        suggestions = []

        # Clean and tokenize description
        description_lower = description.lower()
        words = re.findall(r"\b\w+\b", description_lower)

        # Extract key technical terms
        tech_terms = []
        for word in words:
            if word in cls.TECH_KEYWORDS:
                tech_terms.append(cls.TECH_KEYWORDS[word])
            elif word in cls.LANGUAGE_PREFIXES:
                tech_terms.append(cls.LANGUAGE_PREFIXES[word])

        # Find important nouns (simple heuristic: words not in common list)
        common_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "for",
            "to",
            "of",
            "in",
            "and",
            "or",
            "this",
            "that",
        }
        important_words = [w for w in words if w not in common_words and len(w) > 3][:3]

        # Generate suggestions
        # 1. Kebab-case from important words
        if important_words:
            suggestions.append("-".join(important_words[:2]))

        # 2. With tech prefix/suffix
        if tech_terms and important_words:
            suggestions.append(f"{important_words[0]}-{tech_terms[0]}")
            if len(important_words) > 1:
                suggestions.append(f"{tech_terms[0]}-{'-'.join(important_words[:2])}")

        # 3. Camel case variant
        if important_words:
            suggestions.append("".join(w.capitalize() for w in important_words[:2]))

        # 4. Snake case variant
        if len(important_words) >= 2:
            suggestions.append("_".join(important_words[:2]))

        # Remove duplicates and current name
        suggestions = list(dict.fromkeys(suggestions))  # Preserve order
        suggestions = [s for s in suggestions if s and s != current_name]

        return suggestions[:count]


class RepositoryHealthScorer:
    """Scores repository health based on various metrics."""

    HEALTH_WEIGHTS = {
        "has_readme": 20,
        "has_license": 15,
        "has_gitignore": 10,
        "has_contributing": 10,
        "has_code_of_conduct": 10,
        "has_security": 10,
        "has_ci": 15,
        "has_tests": 10,
    }

    @classmethod
    def calculate_score(cls, repo_files: list[str]) -> dict[str, Any]:
        """
        Calculate health score for a repository.

        Args:
            repo_files: List of files in the repository

        Returns:
            Dictionary with score and details
        """
        files_lower = [f.lower() for f in repo_files]

        checks = {
            "has_readme": any("readme" in f for f in files_lower),
            "has_license": any("license" in f or "licence" in f for f in files_lower),
            "has_gitignore": ".gitignore" in files_lower,
            "has_contributing": any("contributing" in f for f in files_lower),
            "has_code_of_conduct": any(
                "code_of_conduct" in f or "code-of-conduct" in f for f in files_lower
            ),
            "has_security": any("security" in f for f in files_lower),
            "has_ci": any(
                ".github/workflows" in f or ".gitlab-ci" in f or "jenkinsfile" in f
                for f in files_lower
            ),
            "has_tests": any("test" in f for f in files_lower),
        }

        score = sum(cls.HEALTH_WEIGHTS[key] * (1 if value else 0) for key, value in checks.items())
        max_score = sum(cls.HEALTH_WEIGHTS.values())

        percentage = (score / max_score) * 100 if max_score > 0 else 0

        # Determine rating
        if percentage >= 90:
            rating = "Excellent"
        elif percentage >= 75:
            rating = "Good"
        elif percentage >= 50:
            rating = "Fair"
        else:
            rating = "Needs Improvement"

        return {
            "score": score,
            "max_score": max_score,
            "percentage": round(percentage, 1),
            "rating": rating,
            "checks": checks,
            "recommendations": cls._get_recommendations(checks),
        }

    @classmethod
    def _get_recommendations(cls, checks: dict[str, bool]) -> list[str]:
        """Generate recommendations based on missing items."""
        recommendations = []

        if not checks["has_readme"]:
            recommendations.append(
                "Add a README.md with project description and usage instructions"
            )
        if not checks["has_license"]:
            recommendations.append("Add a LICENSE file to clarify usage rights")
        if not checks["has_gitignore"]:
            recommendations.append("Add a .gitignore file to exclude unnecessary files")
        if not checks["has_contributing"]:
            recommendations.append("Add CONTRIBUTING.md to guide contributors")
        if not checks["has_security"]:
            recommendations.append("Add SECURITY.md to document security policies")
        if not checks["has_ci"]:
            recommendations.append("Set up CI/CD pipeline for automated testing")
        if not checks["has_tests"]:
            recommendations.append("Add tests to ensure code quality")

        return recommendations


class AutoTemplateGenerator:
    """Generates common repository templates automatically."""

    @staticmethod
    def generate_issue_template(repo_type: str = "general") -> str:
        """Generate issue template based on repository type."""
        templates = {
            "general": """---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: 'bug'
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. Ubuntu 20.04]
 - Version [e.g. 1.0.0]

**Additional context**
Add any other context about the problem here.
""",
            "api": """---
name: API Issue
about: Report an API-related issue
title: '[API] '
labels: 'api, bug'
assignees: ''

---

**Endpoint**
Which API endpoint is affected?

**Request**
```
Provide request details (method, headers, body)
```

**Expected Response**
What did you expect?

**Actual Response**
What actually happened?

**Environment:**
 - API Version:
 - Client:
""",
        }
        return templates.get(repo_type, templates["general"])

    @staticmethod
    def generate_pr_template() -> str:
        """Generate pull request template."""
        return """## Description
Please include a summary of the changes and the related issue.

Fixes # (issue)

## Type of change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix/feature causing existing functionality to break)
- [ ] Documentation update

## How Has This Been Tested?
Please describe the tests that you ran to verify your changes.

- [ ] Test A
- [ ] Test B

## Checklist:
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
"""

    @staticmethod
    def generate_security_policy() -> str:
        """Generate security policy template."""
        return """# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please:

1. **Do NOT** open a public issue
2. Email security@example.com with details
3. Include steps to reproduce if possible
4. Allow up to 48 hours for initial response

## Security Best Practices

When using this project:
- Keep dependencies up to date
- Use environment variables for secrets
- Enable two-factor authentication
- Follow the principle of least privilege

## Disclosure Policy

- Security issues will be patched within 30 days
- Public disclosure will occur after a patch is available
- Credit will be given to security researchers
"""

    @staticmethod
    def generate_code_of_conduct() -> str:
        """Generate code of conduct template."""
        return """# Code of Conduct

## Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

## Our Standards

Examples of behavior that contributes to creating a positive environment:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

Examples of unacceptable behavior:
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

## Enforcement

Instances of abusive behavior may be reported by contacting the project team.

## Attribution

This Code of Conduct is adapted from the Contributor Covenant, version 2.0.
"""
