"""Tests for AI-powered features."""

from repoforgex.ai_features import (
    AutoTemplateGenerator,
    RepositoryHealthScorer,
    RepositoryNameSuggester,
)


class TestRepositoryNameSuggester:
    """Test AI-powered name suggestions."""

    def test_suggest_names_with_description(self):
        """Test name suggestions from description."""
        desc = "A Python application for machine learning"
        suggestions = RepositoryNameSuggester.suggest_names(desc)

        assert len(suggestions) > 0
        assert all(isinstance(s, str) for s in suggestions)
        # Should not have spaces
        assert all(" " not in s for s in suggestions)

    def test_suggest_names_with_tech_keywords(self):
        """Test suggestions with technical keywords."""
        desc = "A microservice API for backend processing"
        suggestions = RepositoryNameSuggester.suggest_names(desc)

        assert len(suggestions) > 0
        # Should include some tech-related terms
        combined = " ".join(suggestions)
        assert any(keyword in combined for keyword in ["api", "ms", "svc", "backend", "be"])

    def test_suggest_names_empty_description(self):
        """Test with empty description."""
        suggestions = RepositoryNameSuggester.suggest_names("")
        assert suggestions == []

    def test_suggest_names_excludes_current(self):
        """Test that current name is excluded from suggestions."""
        desc = "Python application tool"
        current = "python-application"
        suggestions = RepositoryNameSuggester.suggest_names(desc, current_name=current)

        assert current not in suggestions

    def test_suggest_names_custom_count(self):
        """Test custom number of suggestions."""
        desc = "Data processing library framework utility"
        suggestions = RepositoryNameSuggester.suggest_names(desc, count=2)

        assert len(suggestions) <= 2


class TestRepositoryHealthScorer:
    """Test repository health scoring."""

    def test_calculate_score_all_files(self):
        """Test score with all recommended files."""
        files = [
            "README.md",
            "LICENSE",
            ".gitignore",
            "CONTRIBUTING.md",
            "CODE_OF_CONDUCT.md",
            "SECURITY.md",
            ".github/workflows/ci.yml",
            "tests/test_main.py",
        ]

        result = RepositoryHealthScorer.calculate_score(files)

        assert result["score"] == result["max_score"]
        assert result["percentage"] == 100.0
        assert result["rating"] == "Excellent"
        assert all(result["checks"].values())

    def test_calculate_score_minimal_files(self):
        """Test score with minimal files."""
        files = ["README.md", ".gitignore"]

        result = RepositoryHealthScorer.calculate_score(files)

        assert result["score"] < result["max_score"]
        assert result["percentage"] < 100.0
        assert len(result["recommendations"]) > 0

    def test_calculate_score_no_files(self):
        """Test score with no files."""
        result = RepositoryHealthScorer.calculate_score([])

        assert result["score"] == 0
        assert result["percentage"] == 0.0
        assert result["rating"] == "Needs Improvement"
        assert len(result["recommendations"]) > 0

    def test_recommendations_missing_readme(self):
        """Test recommendations include missing README."""
        files = [".gitignore"]
        result = RepositoryHealthScorer.calculate_score(files)

        assert any("README" in rec for rec in result["recommendations"])

    def test_case_insensitive_matching(self):
        """Test that file matching is case-insensitive."""
        files = ["readme.md", "LICENSE.txt", ".GITIGNORE"]
        result = RepositoryHealthScorer.calculate_score(files)

        assert result["checks"]["has_readme"]
        assert result["checks"]["has_license"]
        assert result["checks"]["has_gitignore"]


class TestAutoTemplateGenerator:
    """Test automatic template generation."""

    def test_generate_issue_template_general(self):
        """Test general issue template generation."""
        template = AutoTemplateGenerator.generate_issue_template("general")

        assert len(template) > 0
        assert "Bug report" in template or "bug" in template.lower()
        assert "Describe the bug" in template
        assert "To Reproduce" in template

    def test_generate_issue_template_api(self):
        """Test API issue template generation."""
        template = AutoTemplateGenerator.generate_issue_template("api")

        assert len(template) > 0
        assert "API" in template
        assert "Endpoint" in template

    def test_generate_pr_template(self):
        """Test PR template generation."""
        template = AutoTemplateGenerator.generate_pr_template()

        assert len(template) > 0
        assert "Description" in template
        assert "Checklist" in template or "checklist" in template.lower()
        assert "- [ ]" in template  # Has checkboxes

    def test_generate_security_policy(self):
        """Test security policy generation."""
        policy = AutoTemplateGenerator.generate_security_policy()

        assert len(policy) > 0
        assert "Security Policy" in policy or "SECURITY" in policy
        assert "Reporting a Vulnerability" in policy
        assert "Supported Versions" in policy

    def test_generate_code_of_conduct(self):
        """Test code of conduct generation."""
        coc = AutoTemplateGenerator.generate_code_of_conduct()

        assert len(coc) > 0
        assert "Code of Conduct" in coc
        assert "Pledge" in coc or "pledge" in coc.lower()
        assert "Standards" in coc or "standards" in coc.lower()

    def test_templates_are_markdown(self):
        """Test that templates use markdown format."""
        templates = [
            AutoTemplateGenerator.generate_issue_template(),
            AutoTemplateGenerator.generate_pr_template(),
            AutoTemplateGenerator.generate_security_policy(),
            AutoTemplateGenerator.generate_code_of_conduct(),
        ]

        for template in templates:
            # Should have markdown headers or bold text
            assert "#" in template or "**" in template
