from bs4 import BeautifulSoup as bs
from datetime import datetime
import pandas as pd
import requests
import time


class GithubActivityCrawler:

    def __init__(self, user, token=None, start_time=None, end_time=None):
        self.user = user
        # default headers + token if provided
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Mozilla/5.0",
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
        self.base_url = "https://api.github.com"
        self.start_time = pd.to_datetime(start_time) if start_time else None
        self.end_time = pd.to_datetime(end_time) if end_time else None

    def get_user_repos(self):
        """Get all repositories for the user"""
        repos = []
        page = 1
        while True:
            url = f"{self.base_url}/users/{self.user}/repos?page={page}&per_page=100"
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                print(f"Error fetching repositories: {response.status_code}")
                break
            data = response.json()
            if not data:
                break
            repos.extend(data)
            page += 1
            time.sleep(1)
        return repos

    def is_within_timeframe(self, timestamp):
        """Check if timestamp is within specified timeframe"""
        dt = pd.to_datetime(timestamp)
        if self.start_time and dt < self.start_time:
            return False
        if self.end_time and dt > self.end_time:
            return False
        return True

    def get_repo_commits(self, repo_full_name):
        """Get all commits for a repository by the specific user"""
        commits = []
        page = 1
        while True:
            url = f"{self.base_url}/repos/{repo_full_name}/commits?author={self.user}&page={page}&per_page=100"
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                break
            data = response.json()
            if not data:
                break

            for commit in data:
                # check what key in commit , maybe not 'commit'
                # print(commit)
                print(commit)
                commit_time = commit["commit"]["author"]["date"]

                if not self.is_within_timeframe(commit_time):
                    continue

                commits.append(
                    {
                        "time": commit_time,
                        "repo": repo_full_name,
                        "message": commit["commit"]["message"].replace("\n", " "),
                        "hash": commit["sha"],
                        "type": "commit",
                    }
                )

            page += 1
            time.sleep(1)
        return commits

    def get_user_prs(self):
        """Get all pull requests created by the user across all repositories"""
        pulls = []
        page = 1
        while True:
            # Search for PRs created by the user
            url = f"{self.base_url}/search/issues?q=author:{self.user}+is:pr&page={page}&per_page=100"
            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                print(f"Error fetching PRs: {response.status_code}")
                break

            data = response.json()
            if not data.get("items"):
                break

            for pr in data["items"]:
                pr_time = pr["created_at"]

                if not self.is_within_timeframe(pr_time):
                    continue

                # Extract repo name from PR URL
                repo_full_name = "/".join(pr["repository_url"].split("/")[-2:])

                pulls.append(
                    {
                        "time": pr_time,
                        "repo": repo_full_name,
                        "message": pr["title"].replace("\n", " "),
                        "hash": str(pr["number"]),  # PR number as hash
                        "type": "pull_request",
                    }
                )

            # Check if we've reached the last page
            if page >= (data["total_count"] + 99) // 100:
                break

            page += 1
            time.sleep(1)
        return pulls

    def get_all_activity(self):
        """Get all commits and pull requests"""
        all_activity = []

        # Get all PRs first (using search API)
        print("Fetching pull requests...")
        pulls = self.get_user_prs()
        all_activity.extend(pulls)

        # Then get commits from repositories
        repos = self.get_user_repos()
        for repo in repos:
            print(f"Processing repository: {repo['full_name']}")
            commits = self.get_repo_commits(repo["full_name"])
            all_activity.extend(commits)

        return all_activity


def main(
    github_username,
    output_file="github_activity.csv",
    github_token=None,
    start_time=None,
    end_time=None,
):
    """
    Main function to crawl GitHub activity and save to CSV

    Args:
        github_username (str): GitHub username to crawl
        output_file (str): Output CSV filename
        github_token (str): GitHub API token for authentication (optional)
        start_time (str): Start time in any format pandas can parse (optional)
        end_time (str): End time in any format pandas can parse (optional)
    """
    try:
        # Initialize crawler
        crawler = GithubActivityCrawler(
            github_username, github_token, start_time, end_time
        )

        print(f"Starting to crawl GitHub activity for user: {github_username}")
        if start_time:
            print(f"Start time: {start_time}")
        if end_time:
            print(f"End time: {end_time}")

        # Get all activity
        activity = crawler.get_all_activity()

        if not activity:
            print("No activity found for the specified criteria")
            return

        # Convert to DataFrame
        df = pd.DataFrame(activity)

        # Sort by time
        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values("time", ascending=False)

        # Save to CSV
        df.to_csv(output_file, index=False)

        print(f"\nSummary:")
        print(f"Total activities found: {len(df)}")
        print(f"Total commits: {len(df[df['type'] == 'commit'])}")
        print(f"Total pull requests: {len(df[df['type'] == 'pull_request'])}")
        print(f"Date range: from {df['time'].min()} to {df['time'].max()}")
        print(f"Output saved to: {output_file}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    # Example usage
    github_username = "frinkleko"
    output_file = "github_activity.csv"
    main(
        github_username=github_username,
        output_file=output_file,
        start_time=None,
        end_time=None,
        github_token=None,
    )
