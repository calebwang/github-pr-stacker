from github import Github
import subprocess
import os
import re

GITHUB_API_KEY=os.environ["GITHUB_API_KEY"]
PR_STACKER_DATA=os.environ["PR_STACKER_DATA"]

class GitHubStackedPRManager:
    def __init__(self, github_token, repo_name):
        self.github = Github(github_token)
        self.repo = self.github.get_repo(repo_name)
        self.branch_prefix = self.get_branch_prefix()
        self.branches = self.list_branches()

    def get_current_user_username(self):
        return self.github.get_user().login

    def get_current_branch(self):
        """Get the name of the current Git branch."""
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
        return result.stdout.strip()

    def get_branch_prefix(self):
        """Determine the prefix for the branch series based on the current branch."""
        current_branch = self.get_current_branch()
        match = re.match(r"(.*)(-[0-9]+)", current_branch)
        return match.group(1) if match else current_branch
    
    def get_pr(self, branch_name, state="open"):
        return self.repo.get_pulls(state=state, head=f"{self.get_current_user_username()}:{branch_name}")

    def list_branches(self):
        """Retrieve and sort all branches that match the naming convention."""
        branches = [branch.name for branch in self.repo.get_branches() if branch.name.startswith(self.branch_prefix)]
        return sorted(branches, key=lambda x: int(x.split('-')[-1]) if '-' in x else 0)

    def create_pr(self, base, head, title, body=""):
        """Create a pull request for a given head into a base branch."""
        print(f"Creating PR {title} | {head}->{base}")
        self.repo.create_pull(title=title, body=body, base=base, head=head)

    def setup_initial_prs(self):
        """Create the initial PRs for a stacked branch set."""
        for i in range(len(self.branches) - 1):
            base = self.branches[i]
            head = self.branches[i + 1]
            self.create_pr(base, head, title=f"Merge {head} into {base}")

    def rebase_branch(self, branch, onto_branch):
        """Rebase a branch onto another and force push changes."""
        subprocess.run(["git", "fetch", "origin"])
        subprocess.run(["git", "checkout", branch])
        subprocess.run(["git", "rebase", onto_branch])
        subprocess.run(["git", "push", "--force", "origin", branch])

    def rebase_stack(self):
        """Rebase each branch in the stack based on the previous branch."""
        for i in range(1, len(self.branches)):
            self.rebase_branch(self.branches[i], self.branches[i-1])

    def handle_merge_to_master(self):
        """Detect merges to master and propagate them back upstream."""
        master = self.repo.get_branch("master")
        
        # If the current master commit is not in the latest branch, propagate the merge
        if master.commit not in [self.repo.get_branch(branch).commit for branch in self.branches]:
            for i in range(len(self.branches) - 1, 0, -1):
                self.create_pr(base=self.branches[i - 1], head="master", title=f"Propagate master changes to {self.branches[i - 1]}")
                break

current_dir = os.getcwd().split('/')[-1]
head_org = "calebwang"
repo_name = f"{head_org}/{current_dir}"

pr_manager = GitHubStackedPRManager(GITHUB_API_KEY, repo_name)

# Initial PR setup
pr_manager.setup_initial_prs()

# Rebase the stack after changes
pr_manager.rebase_stack()

# Handle merge back to upstream
pr_manager.handle_merge_to_master()
