"""Tests for repository analytics."""
import pytest
from datetime import datetime, timedelta
from repoforgex.analytics import RepositoryAnalytics


class TestRepositoryAnalytics:
    """Test repository analytics."""
    
    def test_add_repository(self):
        """Test adding repository to analytics."""
        analytics = RepositoryAnalytics()
        analytics.add_repository("test-repo", "test-owner", private=True, template="python-basic")
        
        assert len(analytics.repos) == 1
        assert analytics.repos[0]['name'] == "test-repo"
        assert analytics.repos[0]['owner'] == "test-owner"
    
    def test_get_summary_empty(self):
        """Test summary with no repositories."""
        analytics = RepositoryAnalytics()
        summary = analytics.get_summary()
        
        assert summary['total_repos'] == 0
        assert 'message' in summary
    
    def test_get_summary_with_repos(self):
        """Test summary with repositories."""
        analytics = RepositoryAnalytics()
        analytics.add_repository("repo1", "owner1", private=True, template="python-basic")
        analytics.add_repository("repo2", "owner1", private=False, template="node-basic")
        analytics.add_repository("repo3", "owner2", private=True, template=None)
        
        summary = analytics.get_summary()
        
        assert summary['total_repos'] == 3
        assert summary['private_repos'] == 2
        assert summary['public_repos'] == 1
        assert summary['private_percentage'] == pytest.approx(66.7, rel=0.1)
        assert summary['by_owner']['owner1'] == 2
        assert summary['by_owner']['owner2'] == 1
        assert summary['by_template']['python-basic'] == 1
        assert summary['by_template']['node-basic'] == 1
        assert summary['by_template']['none'] == 1
    
    def test_most_active_owner(self):
        """Test identifying most active owner."""
        analytics = RepositoryAnalytics()
        analytics.add_repository("repo1", "owner1", private=True)
        analytics.add_repository("repo2", "owner1", private=True)
        analytics.add_repository("repo3", "owner2", private=True)
        
        summary = analytics.get_summary()
        assert summary['most_active_owner'] == 'owner1'
    
    def test_most_used_template(self):
        """Test identifying most used template."""
        analytics = RepositoryAnalytics()
        analytics.add_repository("repo1", "owner1", private=True, template="python-basic")
        analytics.add_repository("repo2", "owner1", private=True, template="python-basic")
        analytics.add_repository("repo3", "owner1", private=True, template="node-basic")
        
        summary = analytics.get_summary()
        assert summary['most_used_template'] == 'python-basic'
    
    def test_name_pattern_analysis(self):
        """Test analyzing naming patterns."""
        analytics = RepositoryAnalytics()
        analytics.add_repository("python-app", "owner1", private=True)
        analytics.add_repository("node-service", "owner1", private=True)
        analytics.add_repository("data_processor", "owner1", private=True)
        analytics.add_repository("myRepoName", "owner1", private=True)
        
        summary = analytics.get_summary()
        patterns = summary['name_patterns']
        
        assert patterns['kebab_case_count'] == 2
        assert patterns['snake_case_count'] == 1
        assert patterns['camel_case_count'] == 1
    
    def test_common_prefixes(self):
        """Test identifying common prefixes."""
        analytics = RepositoryAnalytics()
        analytics.add_repository("python-app1", "owner1", private=True)
        analytics.add_repository("python-app2", "owner1", private=True)
        analytics.add_repository("node-service", "owner1", private=True)
        
        summary = analytics.get_summary()
        prefixes = summary['name_patterns']['common_prefixes']
        
        assert 'python' in prefixes
        assert prefixes['python'] == 2
    
    def test_get_recommendations_all_public(self):
        """Test recommendations for all public repos."""
        analytics = RepositoryAnalytics()
        analytics.add_repository("repo1", "owner1", private=False)
        analytics.add_repository("repo2", "owner1", private=False)
        
        recommendations = analytics.get_recommendations()
        
        assert any('public' in rec.lower() for rec in recommendations)
    
    def test_get_recommendations_all_private(self):
        """Test recommendations for all private repos."""
        analytics = RepositoryAnalytics()
        analytics.add_repository("repo1", "owner1", private=True)
        analytics.add_repository("repo2", "owner1", private=True)
        
        recommendations = analytics.get_recommendations()
        
        assert any('private' in rec.lower() for rec in recommendations)
    
    def test_get_recommendations_no_templates(self):
        """Test recommendations for repos without templates."""
        analytics = RepositoryAnalytics()
        analytics.add_repository("repo1", "owner1", private=True, template=None)
        analytics.add_repository("repo2", "owner1", private=True, template=None)
        analytics.add_repository("repo3", "owner1", private=True, template=None)
        analytics.add_repository("repo4", "owner1", private=True, template=None)
        
        recommendations = analytics.get_recommendations()
        
        assert any('template' in rec.lower() for rec in recommendations)
    
    def test_get_recommendations_mixed_naming(self):
        """Test recommendations for mixed naming conventions."""
        analytics = RepositoryAnalytics()
        analytics.add_repository("kebab-case", "owner1", private=True)
        analytics.add_repository("snake_case", "owner1", private=True)
        
        recommendations = analytics.get_recommendations()
        
        assert any('naming' in rec.lower() or 'convention' in rec.lower() for rec in recommendations)
    
    def test_export_report_text(self):
        """Test exporting report as text."""
        analytics = RepositoryAnalytics()
        analytics.add_repository("repo1", "owner1", private=True, template="python-basic")
        
        report = analytics.export_report(format='text')
        
        assert isinstance(report, str)
        assert len(report) > 0
        assert 'REPOSITORY ANALYTICS REPORT' in report
        assert 'SUMMARY' in report
        assert 'repo1' not in report  # Should not include individual repo names in summary
    
    def test_export_report_markdown(self):
        """Test exporting report as markdown."""
        analytics = RepositoryAnalytics()
        analytics.add_repository("repo1", "owner1", private=True, template="python-basic")
        
        report = analytics.export_report(format='markdown')
        
        assert isinstance(report, str)
        assert len(report) > 0
        assert '# Repository Analytics Report' in report
        assert '## Summary' in report
        assert '**Total Repositories:**' in report
    
    def test_trend_analysis_no_repos(self):
        """Test trend analysis with no repositories."""
        analytics = RepositoryAnalytics()
        trends = analytics.get_trend_analysis(time_window_hours=24)
        
        assert trends['repos_created'] == 0
        assert 'message' in trends
    
    def test_average_name_length(self):
        """Test calculating average name length."""
        analytics = RepositoryAnalytics()
        analytics.add_repository("short", "owner1", private=True)
        analytics.add_repository("verylongname", "owner1", private=True)
        
        summary = analytics.get_summary()
        avg_length = summary['name_patterns']['average_name_length']
        
        # "short" = 5 chars, "verylongname" = 12 chars, average = 8.5
        assert avg_length == pytest.approx(8.5, rel=0.1)
    
    def test_shortest_and_longest_names(self):
        """Test identifying shortest and longest repository names."""
        analytics = RepositoryAnalytics()
        analytics.add_repository("a", "owner1", private=True)
        analytics.add_repository("medium-name", "owner1", private=True)
        analytics.add_repository("verylongrepositoryname", "owner1", private=True)
        
        summary = analytics.get_summary()
        patterns = summary['name_patterns']
        
        assert patterns['shortest_name'] == 'a'
        assert patterns['longest_name'] == 'verylongrepositoryname'
