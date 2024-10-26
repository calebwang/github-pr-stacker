from github import Github
import subprocess
import os
import re

GITHUB_API_KEY=os.environ["GITHUB_API_KEY"]

class GitHubStackedPRManager:
    def __init__(self, github_token, repo_name):
        self.github = Github(github_token)
        self.repo = self.github.get_repo(repo_name)
        self.starting_branch = self.get_current_branch()
        self.branch_prefix = self.get_branch_prefix()
        self.branches = self.list_branches()

        self.fetch()

        self.pulls = self.fetch_prs(self.branches)

    def fetch(self):
        subprocess.run(["git", "fetch"])
    
    def push(self, branch):
        subprocess.run(["git", "checkout", branch], text=True)
        subprocess.run(["git", "push", "-u", "origin", branch], text=True)

    def push_all(self, branches):
        for branch in branches:
            self.push(branch)
    
    def show_ref(self, branch):
<<<<<<< HEAD
        result = subprocess.run(["git", "show-ref", branch], capture_output=True, text=True)
        return result.stdout.split()[0]
=======
        result = subprocess.run(["git", "show-ref", "branch"], capture_output=True, text=True)
        return result.split()[0]
>>>>>>> 1d8c12b (Code to rebase stack)

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
        results = list(self.repo.get_pulls(state="all", head=f"{self.get_current_user_username()}:{branch_name}"))
        result = results[0] if results else None
        if result:
            print(f"Identified PR {result.number} for {branch_name}")
        return result
    
    def fetch_prs(self, branches):
        return {
            branch: self.get_pr(branch)
            for branch in branches
        }

    def list_branches(self):
        """Retrieve and sort all branches that match the naming convention."""
        result = subprocess.run(["git", "branch"], capture_output=True, text=True)
        branches = result.stdout.splitlines()
        # Remove any leading "* " from the currently checked-out branch
        branches = [branch.strip("* ").strip() for branch in branches]
        branches = [branch for branch in branches if branch.startswith(self.branch_prefix)]
        def sort_key(branch_name):
            if branch_name == self.get_branch_prefix():
                return 0
            return int(branch_name.split("-")[-1])
        return sorted(branches, key=sort_key)

    def create_pr(self, base, head, title, body=""):
        """Create a pull request for a given head into a base branch."""
        print(f"Creating PR {title} | {head}->{base}")
        self.repo.create_pull(title=title, body=body, base=base, head=head)

    def ensure_prs(self):
        """Create the initial PRs for a stacked branch set."""
        branches = ["master"] + self.branches
        for i in range(len(branches) - 1):
            base = branches[i]
            head = branches[i + 1]
            if not self.pulls[head]:
                self.pulls[head] = self.create_pr(base, head, title=f"Merge {head} into {base}")

    def rebase_branch(self, branch, onto_branch):
        """Rebase a branch onto another and force push changes."""
        subprocess.run(["git", "fetch", "origin"])
        subprocess.run(["git", "checkout", branch])
        subprocess.run(["git", "rebase", onto_branch])
        subprocess.run(["git", "push", "--force", "origin", branch])

    def update_stack(self):
        """Rebase each branch in the stack based on the previous branch."""
        self.fetch()
        for branch in self.branches:
            if self.show_ref(branch) != self.show_ref(f"origin/{branch}"):
                changed_branch = branch
                break

<<<<<<< HEAD
        print("xcxc", changed_branch)
=======
>>>>>>> 1d8c12b (Code to rebase stack)
        self.push(changed_branch)
        idx = self.branches.index(changed_branch)
        for i in range(idx + 1, len(self.branches)):
            self.rebase_branch(self.branches[i], changed_branch)

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

