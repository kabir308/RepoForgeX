"""Repository analytics and insights module."""
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger("repoforgex.analytics")


class RepositoryAnalytics:
    """Provides analytics and insights for repositories."""

    def __init__(self):
        self.repos: list[dict[str, Any]] = []

    def add_repository(
        self,
        name: str,
        owner: str,
        private: bool,
        template: Optional[str] = None,
        **metadata,
    ):
        """
        Track a repository for analytics.

        Args:
            name: Repository name
            owner: Repository owner
            private: Whether repository is private
            template: Template used (if any)
            **metadata: Additional metadata
        """
        repo_data = {
            "name": name,
            "owner": owner,
            "private": private,
            "template": template,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata,
        }
        self.repos.append(repo_data)
        logger.debug(f"Tracked repository: {owner}/{name}")

    def get_summary(self) -> dict[str, Any]:
        """
        Get summary statistics for all tracked repositories.

        Returns:
            Dictionary with summary statistics
        """
        if not self.repos:
            return {"total_repos": 0, "message": "No repositories tracked"}

        total = len(self.repos)
        private_count = sum(1 for r in self.repos if r["private"])
        public_count = total - private_count

        # Count by owner
        by_owner = defaultdict(int)
        for repo in self.repos:
            by_owner[repo["owner"]] += 1

        # Count by template
        by_template = defaultdict(int)
        for repo in self.repos:
            template = repo.get("template") or "none"
            by_template[template] += 1

        # Name pattern analysis
        name_patterns = self._analyze_name_patterns()

        return {
            "total_repos": total,
            "private_repos": private_count,
            "public_repos": public_count,
            "private_percentage": round((private_count / total) * 100, 1),
            "by_owner": dict(by_owner),
            "by_template": dict(by_template),
            "name_patterns": name_patterns,
            "most_active_owner": max(by_owner.items(), key=lambda x: x[1])[0] if by_owner else None,
            "most_used_template": max(by_template.items(), key=lambda x: x[1])[0]
            if by_template
            else None,
        }

    def _analyze_name_patterns(self) -> dict[str, Any]:
        """Analyze naming patterns in repositories."""
        if not self.repos:
            return {}

        names = [r["name"] for r in self.repos]

        # Count naming conventions
        kebab_case = sum(1 for n in names if "-" in n and "_" not in n)
        snake_case = sum(1 for n in names if "_" in n)
        camel_case = sum(1 for n in names if re.match(r"^[a-z][a-zA-Z0-9]*[A-Z]", n))

        # Common prefixes
        prefixes = defaultdict(int)
        for name in names:
            if "-" in name:
                prefix = name.split("-")[0]
                if len(prefix) <= 10:  # Reasonable prefix length
                    prefixes[prefix] += 1

        # Average name length
        avg_length = sum(len(n) for n in names) / len(names) if names else 0

        return {
            "kebab_case_count": kebab_case,
            "snake_case_count": snake_case,
            "camel_case_count": camel_case,
            "common_prefixes": dict(
                list(sorted(prefixes.items(), key=lambda x: x[1], reverse=True))[:5]
            ),
            "average_name_length": round(avg_length, 1),
            "shortest_name": min(names, key=len) if names else None,
            "longest_name": max(names, key=len) if names else None,
        }

    def get_recommendations(self) -> list[str]:
        """
        Get recommendations based on repository analytics.

        Returns:
            List of recommendation strings
        """
        recommendations = []
        summary = self.get_summary()

        if summary["total_repos"] == 0:
            return ["Create some repositories to get recommendations"]

        # Privacy recommendations
        if summary["private_percentage"] == 0:
            recommendations.append(
                "⚠️  All repositories are public. Consider making sensitive repositories private."
            )
        elif summary["private_percentage"] == 100:
            recommendations.append(
                "ℹ️  All repositories are private. Consider open-sourcing some if appropriate."
            )

        # Template recommendations
        template_stats = summary["by_template"]
        if template_stats.get("none", 0) > summary["total_repos"] * 0.3:
            recommendations.append(
                "💡 Many repositories without templates. "
                "Consider using templates for consistency."
            )

        # Naming consistency
        patterns = summary["name_patterns"]
        if patterns:
            kebab = patterns.get("kebab_case_count", 0)
            snake = patterns.get("snake_case_count", 0)

            if kebab > 0 and snake > 0:
                recommendations.append(
                    "📝 Mixed naming conventions detected (kebab-case and snake_case). "
                    "Consider standardizing on one convention."
                )

        # Organization recommendations
        owner_count = len(summary["by_owner"])
        if owner_count > 3:
            recommendations.append(
                f"🏢 Repositories spread across {owner_count} owners. "
                "Consider consolidating under fewer organizations for easier management."
            )

        return recommendations

    def get_trend_analysis(self, time_window_hours: int = 24) -> dict[str, Any]:
        """
        Analyze repository creation trends within a time window.

        Args:
            time_window_hours: Time window in hours

        Returns:
            Trend analysis data
        """
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)

        recent_repos = []
        for repo in self.repos:
            created_at = datetime.fromisoformat(repo["created_at"])
            if created_at >= cutoff_time:
                recent_repos.append(repo)

        if not recent_repos:
            return {
                "time_window_hours": time_window_hours,
                "repos_created": 0,
                "message": f"No repositories created in last {time_window_hours} hours",
            }

        # Calculate velocity (repos per hour)
        actual_timespan = (
            datetime.now() - datetime.fromisoformat(min(r["created_at"] for r in recent_repos))
        ).total_seconds() / 3600

        velocity = len(recent_repos) / actual_timespan if actual_timespan > 0 else 0

        return {
            "time_window_hours": time_window_hours,
            "repos_created": len(recent_repos),
            "creation_velocity_per_hour": round(velocity, 2),
            "projected_daily_rate": round(velocity * 24, 1),
            "recent_repos": [
                {
                    "name": r["name"],
                    "owner": r["owner"],
                    "created_at": r["created_at"],
                }
                for r in sorted(recent_repos, key=lambda x: x["created_at"], reverse=True)
            ],
        }

    def export_report(self, format: str = "text") -> str:
        """
        Export analytics report in specified format.

        Args:
            format: Output format ('text' or 'markdown')

        Returns:
            Formatted report string
        """
        summary = self.get_summary()
        recommendations = self.get_recommendations()

        if format == "markdown":
            return self._export_markdown(summary, recommendations)
        else:
            return self._export_text(summary, recommendations)

    def _export_text(self, summary: dict[str, Any], recommendations: list[str]) -> str:
        """Export report as plain text."""
        lines = [
            "=" * 60,
            "REPOSITORY ANALYTICS REPORT",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 60,
            f"Total Repositories: {summary['total_repos']}",
            f"Private: {summary['private_repos']} ({summary.get('private_percentage', 0)}%)",
            f"Public: {summary['public_repos']}",
            "",
        ]

        if summary.get("by_owner"):
            lines.append("BY OWNER")
            lines.append("-" * 60)
            for owner, count in summary["by_owner"].items():
                lines.append(f"  {owner}: {count}")
            lines.append("")

        if summary.get("by_template"):
            lines.append("BY TEMPLATE")
            lines.append("-" * 60)
            for template, count in summary["by_template"].items():
                lines.append(f"  {template}: {count}")
            lines.append("")

        if recommendations:
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 60)
            for rec in recommendations:
                lines.append(f"  • {rec}")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def _export_markdown(self, summary: dict[str, Any], recommendations: list[str]) -> str:
        """Export report as markdown."""
        lines = [
            "# Repository Analytics Report",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Summary",
            f"- **Total Repositories:** {summary['total_repos']}",
            f"- **Private:** {summary['private_repos']} ({summary.get('private_percentage', 0)}%)",
            f"- **Public:** {summary['public_repos']}",
            "",
        ]

        if summary.get("by_owner"):
            lines.append("## By Owner")
            for owner, count in summary["by_owner"].items():
                lines.append(f"- **{owner}:** {count}")
            lines.append("")

        if summary.get("by_template"):
            lines.append("## By Template")
            for template, count in summary["by_template"].items():
                lines.append(f"- **{template}:** {count}")
            lines.append("")

        if recommendations:
            lines.append("## Recommendations")
            for rec in recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)
