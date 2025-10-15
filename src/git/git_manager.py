#!/usr/bin/env python3

import sys
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from config.config_manager import GitConfig
from utils.logger import Logger


class GitCommandResult:

    # Result of git command execution

    def __init__( self, returncode: int, stdout: str, stderr: str, command: str ):
        
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.command = command
        self.success = returncode == 0


class GitManager:
    

    def __init__( self, config: GitConfig, vault_path: Path, remote_url: str, branch: str, logger: Logger ):
        
        self.config = config
        self.vault_path = vault_path
        self.remote_url = remote_url
        self.branch = branch
        self.logger = logger
        
        self.startupinfo = None
        self.creation_flags = 0
        
        if sys.platform == "win32":
            
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.startupinfo.wShowWindow = subprocess.SW_HIDE
            self.creation_flags = subprocess.CREATE_NO_WINDOW
        
        self._command_lock = threading.Lock()
        
        self._git_available = None
        

    def _check_git_availability( self ) -> bool:
        
        
        if self._git_available is not None:
            return self._git_available
            
        try:
            
            result = self._run_command_sync(
                
                ["git", "--version"], 
                description="Git availability check",
                timeout=10
            )
            
            self._git_available = result.success
            
            if self._git_available:
                self.logger.debug(f"[+] Git available: {result.stdout.strip()}")
            else:
                self.logger.error("[x] Git not found in system PATH")
                
            return self._git_available
            
        except Exception as e:
            
            self.logger.error(f"[x] Git availability check failed: {e}")
            self._git_available = False
            return False


    def _run_command_sync( self, cmd: List[str], description: str = "Git command", timeout: Optional[int] = None ) -> GitCommandResult:
        
        # Run a git command synchronously with locking
        
        if timeout is None:
            timeout = self.config.timeout
            
        cmd_str = ' '.join(cmd)
        
        try:
            
            with self._command_lock:
                
                self.logger.debug(f"[>] Executing: {cmd_str}")
                
                result = subprocess.run(
                    
                    cmd,
                    cwd=self.vault_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    startupinfo=self.startupinfo,
                    creationflags=self.creation_flags,
                    encoding='utf-8',
                    errors='replace'
                )
                
                git_result = GitCommandResult(result.returncode, result.stdout, result.stderr, cmd_str)
                
                if git_result.success:
                    
                    if git_result.stdout.strip() and "nothing to commit" not in git_result.stdout.lower():
                        self.logger.debug(f"[+] {description}: {git_result.stdout.strip()}")
                        
                else:
                    
                    self.logger.error(f"[x] {description} failed (exit code {git_result.returncode})")
                    
                    if git_result.stderr.strip():
                        self.logger.error(f"[x] Error: {git_result.stderr.strip()}")
                
                # Handle common warnings (non-critical)
                if git_result.stderr.strip():
                    self._handle_git_warnings(git_result.stderr, description)
                
                return git_result
            
        except subprocess.TimeoutExpired:
            
            self.logger.error(f"[x] {description} timed out after {timeout} seconds")
            return GitCommandResult(124, "", f"Command timed out after {timeout}s", cmd_str)
        
        except Exception as e:
            
            self.logger.error(f"[x] {description} failed: {e}")
            return GitCommandResult(1, "", str(e), cmd_str)
        
        
    def _run_command_async( self, cmd: List[str], description: str = "Git command", timeout: Optional[int] = None ) -> GitCommandResult:
        
        # Run a git command asynchronously using thread pool
                
        with ThreadPoolExecutor(max_workers=1) as executor:
            
            try:
                
                future = executor.submit(self._run_command_sync, cmd, description, timeout)
                return future.result(timeout=timeout or self.config.timeout)
                
            except TimeoutError:
                
                self.logger.error(f"[x] {description} async timeout")
                return GitCommandResult(124, "", "Async timeout", ' '.join(cmd))


    def _handle_git_warnings( self, stderr: str, description: str ) -> None:

        warning_patterns = [
            
            "lf will be replaced by crlf",
            "crlf will be replaced by lf", 
            "warning: adding embedded git repository",
            "branch 'main' set up to track",
            "branch            main       -> fetch_head",
            "[new branch]      main       -> origin/main",
            "to https://github.com",
            "main -> main",
            "fast-forward"
        ]
        
        stderr_lower = stderr.lower()
        
        # Only log as warning if it's not a known non-critical message
        if not any(pattern in stderr_lower for pattern in warning_patterns):
            self.logger.warning(f"[!] {description} stderr: {stderr.strip()}")


    def setup_repository( self ) -> bool:

        # Setup Git repository, remote, and .gitignore
        
        if not self._check_git_availability():
            return False
            
        try:
            
            self.logger.info("[+] Setting up Git repository...")
            
            # Initialize repository if not already a git repo
            if not (self.vault_path / ".git").exists():
                
                self.logger.info("[+] Initializing new Git repository")

                result = self._run_command_sync(["git", "init"], "Git init")
                if not result.success:
                    return False
                
                result = self._run_command_sync(["git", "branch", "-M", self.branch], "Set main branch")
                if not result.success:
                    self.logger.warning(f"[!] Could not set main branch to {self.branch}")

            self._configure_git_user()
            
            if not self._setup_remote():
                return False
            
            self._create_gitignore()
            
            self.logger.info("[+] Git repository setup completed successfully")
            return True
            
        except Exception as e:
            
            self.logger.error(f"[x] Git setup failed: {e}")
            return False
        
        
    def _configure_git_user( self ) -> None:
        
        # Configure Git username and email

        result = self._run_command_sync(
            
            ["git", "config", "user.name", self.config.user_name], 
            "Set user name"
        )
        
        if result.success:
            self.logger.debug(f"[+] Git user name set to: {self.config.user_name}")
        
        result = self._run_command_sync(
            
            ["git", "config", "user.email", self.config.user_email], 
            "Set user email"
        )
        
        if result.success:
            self.logger.debug(f"[+] Git user email set to: {self.config.user_email}")


    def _setup_remote( self ) -> bool:
        
        # Setup Git remote origin with validation

        result = self._run_command_sync(["git", "remote", "get-url", "origin"], "Check remote")
        
        if not result.success:
            
            self.logger.info("[+] Adding remote origin")
            result = self._run_command_sync(
                
                ["git", "remote", "add", "origin", self.remote_url], 
                "Add remote"
            )
            
            return result.success
            
        else:
            
            current_remote = result.stdout.strip()
            
            # Extract repo part for comparison (ignore token differences)
            current_repo = self._extract_repo_from_url(current_remote)
            expected_repo = self._extract_repo_from_url(self.remote_url)
            
            if current_repo != expected_repo:
                
                self.logger.info("[+] Updating remote URL")
                result = self._run_command_sync(
                    
                    ["git", "remote", "set-url", "origin", self.remote_url], 
                    "Update remote"
                )
                
                return result.success
                
            else:
                
                self.logger.debug("[+] Remote URL is already correct")
                return True
    
    
    def _extract_repo_from_url( self, url: str ) -> str:

        try:
            
            if "://" in url:
                url = url.split("://", 1)[1]
                
            if "@" in url:
                url = url.split("@", 1)[1]
                
            return url
            
        except Exception:
            return url
    
    
    def _create_gitignore( self ) -> None:

        gitignore_path = self.vault_path / ".gitignore"
        
        gitignore_sections = []
        
        # Build gitignore content from configuration
        section_configs = [
            ('obsidian', "# Obsidian workspace (user-specific)"),
            ('system', "# System files"),
            ('directories', "# Directories"),
            ('custom', "# Custom patterns")
        ]
        
        for section_key, section_header in section_configs:

            if section_key in self.config.gitignore and self.config.gitignore[section_key]:

                gitignore_sections.append(section_header)
                gitignore_sections.extend(self.config.gitignore[section_key])
                gitignore_sections.append("")
        
        new_content = f"""# .gitignore generated by VaultSync
# Edit patterns in config.yaml under git.gitignore section

{chr(10).join(gitignore_sections).rstrip()}

# End of VaultSync .gitignore
"""
        
        try:
            if gitignore_path.exists():
                existing_content = gitignore_path.read_text(encoding='utf-8')

                if existing_content.strip() == new_content.strip():
                    self.logger.debug("[+] .gitignore is already up to date - no changes needed")
                    return
                else:
                    self.logger.debug("[+] .gitignore content has changed - updating file")
            else:
                self.logger.debug("[+] Creating new .gitignore file")

            # Write the file only if it doesn't exist or content changed
            gitignore_path.write_text(new_content, encoding='utf-8')

            action = "updated" if gitignore_path.exists() else "created"
            self.logger.debug(f"[+] .gitignore file {action} successfully")
            
            configured_sections = [k for k, v in self.config.gitignore.items() if v]
            if configured_sections:
                self.logger.debug(f"[+] Configured sections: {', '.join(configured_sections)}")
            
        except Exception as e:
            self.logger.error(f"[x] Failed to create .gitignore: {e}")
            

    def _has_commits( self ) -> bool:

        # Check if there are any commits in the repository
            
        result = self._run_command_sync(["git", "rev-parse", "HEAD"], "Check commits")
        return result.success


    def _remote_branch_exists( self ) -> bool:

        # Check if the remote branch exists
        
        result = self._run_command_sync(
            
            ["git", "ls-remote", "--heads", "origin", self.branch], 
            "Check remote branch"
        )
        
        return result.success and result.stdout.strip()
        

    def _has_local_changes( self ) -> bool:

        # Check if there are any local uncommitted changes
        
        result = self._run_command_sync(["git", "status", "--porcelain"], "Status check")
        return result.success and result.stdout.strip()

    def _get_local_changes_count( self ) -> Dict[str, int]:

        result = self._run_command_sync(["git", "status", "--porcelain"], "Status check")

        if not result.success:
            return {"modified": 0, "added": 0, "deleted": 0, "untracked": 0}

        changes = {"modified": 0, "added": 0, "deleted": 0, "untracked": 0}

        for line in result.stdout.splitlines():
            if not line.strip():
                continue

            status = line[:2]

            if status.startswith('M') or status.endswith('M'):
                changes["modified"] += 1

            elif status.startswith('A') or status.endswith('A'):
                changes["added"] += 1

            elif status.startswith('D') or status.endswith('D'):
                changes["deleted"] += 1

            elif status.startswith('??'):
                changes["untracked"] += 1

        return changes

    def _check_divergence( self ) -> Dict[str, any]:

        # Check if local branch has diverged from remote

        local_result = self._run_command_sync(
            ["git", "rev-parse", self.branch],
            "Get local commit"
        )

        # Get remote commit
        remote_result = self._run_command_sync(
            ["git", "rev-parse", f"origin/{self.branch}"],
            "Get remote commit"
        )

        if not local_result.success or not remote_result.success:
            return {"diverged": False, "ahead": 0, "behind": 0}

        local_commit = local_result.stdout.strip()
        remote_commit = remote_result.stdout.strip()

        if local_commit == remote_commit:
            return {"diverged": False, "ahead": 0, "behind": 0}

        # Count commits ahead
        ahead_result = self._run_command_sync(
            ["git", "rev-list", "--count", f"origin/{self.branch}..{self.branch}"],
            "Count ahead"
        )

        # Count commits behind
        behind_result = self._run_command_sync(
            ["git", "rev-list", "--count", f"{self.branch}..origin/{self.branch}"],
            "Count behind"
        )

        ahead = int(ahead_result.stdout.strip()) if ahead_result.success else 0
        behind = int(behind_result.stdout.strip()) if behind_result.success else 0

        return {
            "diverged": ahead > 0 and behind > 0,
            "ahead": ahead,
            "behind": behind
        }

    def _verify_repository_integrity( self ) -> bool:

        self.logger.debug("[+] Verifying repository integrity...")

        if not (self.vault_path / ".git").exists():
            self.logger.error("[x] .git directory not found")
            return False

        fsck_result = self._run_command_sync(
            ["git", "fsck", "--no-progress"],
            "Verify repository",
            timeout=60
        )

        if not fsck_result.success:
            self.logger.warning("[!] Repository integrity check found issues")
            return True

        self.logger.debug("[+] Repository integrity verified")
        return True


    def pull( self ) -> bool:

        try:
            self.logger.info("[+] Pulling changes from remote...")
            
            if not self._verify_repository_integrity():
                self.logger.error("[x] Repository integrity check failed")
                return False

            if not self._remote_branch_exists():
                self.logger.info("[*] Remote branch doesn't exist yet - normal for new repositories")
                return True
            
            self.logger.debug("[+] Fetching latest changes from remote...")
            fetch_result = self._run_command_async(
                ["git", "fetch", "origin", self.branch],
                "Fetch remote changes",
                timeout=self.config.timeout // 2
            )
            
            if not fetch_result.success:
                if "couldn't find remote ref" in fetch_result.stderr.lower():
                    self.logger.info("[*] Remote branch doesn't exist yet")
                    return True
                self.logger.error("[x] Failed to fetch from remote")
                return False
            
            divergence = self._check_divergence()

            if divergence["behind"] == 0:
                self.logger.info("[*] Already up to date with remote")
                return True

            self.logger.info(f"[+] Remote has {divergence['behind']} new commit(s)")

            if divergence["ahead"] > 0:
                self.logger.info(f"[+] Local has {divergence['ahead']} unpushed commit(s)")

            # Handle local uncommitted changes
            has_changes = self._has_local_changes()
            stashed = False
            
            if has_changes:

                changes = self._get_local_changes_count()
                self.logger.info(f"[+] Found local changes: {changes['modified']} modified, "
                               f"{changes['added']} added, {changes['deleted']} deleted, "
                               f"{changes['untracked']} untracked")

                if self._has_commits():
                    self.logger.info("[+] Stashing local changes before pull...")
                    stash_result = self._run_command_sync([
                        "git", "stash", "push", "-u", "-m",
                        f"Auto-stash before pull {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    ], "Stash changes")

                    stashed = stash_result.success

                    if not stashed:
                        self.logger.error("[x] Failed to stash changes - aborting pull to prevent data loss")
                        return False

            # Use rebase strategy for cleaner history
            if divergence["ahead"] > 0:
                self.logger.info("[+] Using rebase to integrate changes...")
                pull_result = self._run_command_async(
                    ["git", "pull", "--rebase", "origin", self.branch],
                    "Pull with rebase"
                )
            else:
                # Fast-forward only if no local commits
                self.logger.info("[+] Fast-forwarding to remote...")
                pull_result = self._run_command_async(
                    ["git", "pull", "--ff-only", "origin", self.branch],
                    "Fast-forward pull"
                )

            if pull_result.success:
                self.logger.info("[+] Successfully pulled changes from remote")

                # Restore stashed changes if any
                if stashed:
                    self.logger.info("[+] Restoring stashed changes...")
                    pop_result = self._run_command_sync(["git", "stash", "pop"], "Restore stash")
                    
                    if not pop_result.success:

                        if "conflict" in pop_result.stderr.lower() or "merge" in pop_result.stderr.lower():

                            self.logger.error("[x] Conflict detected while restoring stashed changes")
                            self.logger.error("[!] Conflicts must be resolved manually")
                            self.logger.error("[!] Run 'git status' in vault directory for details")
                            self.logger.error("[!] After resolving: 'git stash drop' to clear the stash")

                            return False
                        else:
                            self.logger.warning("[!] Could not restore stashed changes")
                            self.logger.warning("[!] Changes are still in stash - run 'git stash pop' manually")

                return True
                
            else:
                # Analyze pull failure

                if "conflict" in pull_result.stderr.lower():
                    self.logger.error("[x] Merge conflict detected during pull")
                    self.logger.error("[!] Aborting rebase to prevent data loss...")

                    abort_result = self._run_command_sync(["git", "rebase", "--abort"], "Abort rebase")

                    # Restore stash if we stashed
                    if stashed:
                        self.logger.info("[+] Restoring stashed changes...")
                        self._run_command_sync(["git", "stash", "pop"], "Restore stash")

                    self.logger.error("[!] Manual conflict resolution required")
                    return False

                self.logger.error(f"[x] Pull failed: {pull_result.stderr}")

                # Try to restore previous state
                if stashed:
                    self._run_command_sync(["git", "stash", "pop"], "Restore stash")

                return False
                
        except Exception as e:
            self.logger.error(f"[x] Pull operation failed: {e}")
            return False
        

    def push( self ) -> bool:


        try:
            self.logger.info("[+] Pushing changes to remote...")

            if not self._verify_repository_integrity():
                self.logger.error("[x] Repository integrity check failed")
                return False

            # Check if there are any local changes
            if not self._has_local_changes():
                self.logger.info("[*] No local changes to push")
                return True
            
            changes = self._get_local_changes_count()
            total_changes = sum(changes.values())
            self.logger.info(f"[+] Preparing to push {total_changes} change(s): "
                           f"{changes['modified']} modified, {changes['added']} added, "
                           f"{changes['deleted']} deleted, {changes['untracked']} untracked")

            self.logger.debug("[+] Staging all changes...")
            add_result = self._run_command_sync(
                ["git", "add", "-A"],
                "Stage all changes"
            )

            if not add_result.success:
                self.logger.error("[x] Failed to stage changes")
                return False
            
            # Check if there's actually something to commit after staging
            status_result = self._run_command_sync(
                ["git", "status", "--porcelain"],
                "Check staged status"
            )

            if not status_result.stdout.strip():
                self.logger.info("[*] No changes to commit after staging (possibly only ignored files)")
                return True

            commit_msg = f"VaultSync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.logger.debug(f"[+] Creating commit: {commit_msg}")

            commit_result = self._run_command_sync(
                ["git", "commit", "-m", commit_msg],
                "Create commit"
            )
            
            if not commit_result.success:

                if "nothing to commit" in commit_result.stdout.lower():
                    self.logger.info("[*] Nothing new to commit")
                    return True
                else:
                    self.logger.error("[x] Failed to create commit")
                    return False
            
            is_first_push = not self._remote_branch_exists()
            
            if not is_first_push:

                self.logger.debug("[+] Checking remote state before push...")
                fetch_result = self._run_command_sync(
                    ["git", "fetch", "origin", self.branch],
                    "Pre-push fetch",
                    timeout=self.config.timeout // 3
                )

                if fetch_result.success:

                    divergence = self._check_divergence()

                    if divergence["behind"] > 0:
                        self.logger.warning(f"[!] Remote has {divergence['behind']} newer commit(s)")
                        self.logger.warning("[!] A pull is required before pushing")
                        self.logger.info("[+] Attempting to pull and rebase before push...")

                        pull_result = self._run_command_sync(
                            ["git", "pull", "--rebase", "origin", self.branch],
                            "Pre-push pull with rebase"
                        )

                        if not pull_result.success:
                            self.logger.error("[x] Failed to sync with remote before push")
                            self.logger.error("[!] Please resolve conflicts manually and try again")
                            return False

                        self.logger.info("[+] Successfully synced with remote")

            if is_first_push:

                self.logger.info("[+] First push - creating remote branch...")
                push_result = self._run_command_async(
                    ["git", "push", "-u", "origin", self.branch],
                    "Initial push",
                    timeout=self.config.timeout
                )
            else:

                self.logger.info("[+] Pushing to remote...")
                push_result = self._run_command_async(
                    ["git", "push", "origin", self.branch],
                    "Push changes",
                    timeout=self.config.timeout
                )

            if push_result.success:
                self.logger.info("[+] Successfully pushed changes to remote")
                return True
            else:

                stderr_lower = push_result.stderr.lower()

                if "rejected" in stderr_lower or "non-fast-forward" in stderr_lower:

                    self.logger.error("[x] Push rejected - remote has diverged")
                    self.logger.error("[!] This usually means the remote has commits you don't have locally")
                    self.logger.error("[!] Solution: Pull latest changes first")

                    return False

                elif "authentication" in stderr_lower or "permission denied" in stderr_lower:

                    self.logger.error("[x] Authentication failed")
                    self.logger.error("[!] Check your GitHub token in .env file")
                    self.logger.error("[!] Ensure the token has 'repo' scope permissions")

                    return False

                elif "repository not found" in stderr_lower:

                    self.logger.error("[x] Repository not found")
                    self.logger.error("[!] Check GITHUB_REPOSITORY in .env file")
                    self.logger.error("[!] Format should be: username/repository-name")

                    return False

                elif "timeout" in stderr_lower:

                    self.logger.error("[x] Push timed out")
                    self.logger.error("[!] Check your internet connection")
                    self.logger.error("[!] Large repositories may need more time")

                    return False

                else:
                    self.logger.error(f"[x] Push failed: {push_result.stderr}")
                    return False

        except Exception as e:

            self.logger.error(f"[x] Push operation failed: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return False

    def sync( self ) -> bool:


        try:
            self.logger.info("[+] Starting full synchronization...")

            if not self.pull():
                self.logger.error("[x] Sync failed during pull phase")
                return False

            if not self.push():
                self.logger.error("[x] Sync failed during push phase")
                return False

            self.logger.info("[+] Synchronization completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"[x] Synchronization failed: {e}")
            return False