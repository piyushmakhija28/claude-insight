#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Auto-Commit with AI Messages (Phase 4)
Automatically generates commit messages and commits changes

PHASE 4 AUTOMATION - FULL AUTO GIT COMMIT
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class GitAutoCommitAI:
    """
    Automatically generates commit messages and commits
    Uses git diff to understand changes
    """

    def __init__(self):
        self.memory_path = Path.home() / '.claude' / 'memory'
        self.logs_path = self.memory_path / 'logs'
        self.commit_log = self.logs_path / 'git-auto-commit.log'

    def check_git_repo(self, path='.'):
        """Check if current directory is a git repo"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def get_git_status(self, path='.'):
        """Get git status"""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except:
            return None

    def get_git_diff(self, path='.', staged=False):
        """Get git diff"""
        try:
            cmd = ['git', 'diff', '--stat']
            if staged:
                cmd.append('--cached')

            result = subprocess.run(
                cmd,
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except:
            return None

    def analyze_changes(self, status, diff):
        """
        Analyze changes to generate commit message
        """
        if not status:
            return None

        changes = {
            'added': [],
            'modified': [],
            'deleted': [],
            'renamed': []
        }

        # Parse status
        for line in status.split('\n'):
            if not line:
                continue

            status_code = line[0:2].strip()
            filename = line[3:].strip()

            if status_code in ['A', '??']:
                changes['added'].append(filename)
            elif status_code == 'M':
                changes['modified'].append(filename)
            elif status_code == 'D':
                changes['deleted'].append(filename)
            elif status_code == 'R':
                changes['renamed'].append(filename)

        return changes

    def generate_commit_message(self, changes, context=None):
        """
        Generate AI commit message based on changes

        Format:
        <type>: <short summary>

        <detailed description>

        Types: feat, fix, refactor, docs, test, chore, style
        """
        if not changes:
            return "chore: update files"

        # Determine commit type
        commit_type = self.determine_commit_type(changes, context)

        # Generate summary
        summary = self.generate_summary(changes, commit_type)

        # Generate detailed description
        details = self.generate_details(changes)

        # Build commit message
        message_parts = [f"{commit_type}: {summary}"]

        if details:
            message_parts.append("")  # Blank line
            message_parts.extend(details)

        # Add co-author
        message_parts.append("")
        message_parts.append("Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>")

        return "\n".join(message_parts)

    def determine_commit_type(self, changes, context):
        """Determine commit type from changes"""
        # Check for new features (new files)
        if changes['added']:
            # Check if they're source files
            source_files = [f for f in changes['added'] if f.endswith(('.java', '.py', '.js', '.ts'))]
            if source_files:
                return 'feat'

        # Check for deletions
        if changes['deleted']:
            return 'refactor'

        # Check for modifications
        if changes['modified']:
            # Check context for clues
            if context:
                context_lower = context.lower()
                if 'fix' in context_lower or 'bug' in context_lower:
                    return 'fix'
                elif 'test' in context_lower:
                    return 'test'
                elif 'doc' in context_lower or 'readme' in context_lower:
                    return 'docs'
                elif 'refactor' in context_lower:
                    return 'refactor'

            # Check file types
            test_files = [f for f in changes['modified'] if 'test' in f.lower()]
            if test_files:
                return 'test'

            doc_files = [f for f in changes['modified'] if f.endswith(('.md', '.txt'))]
            if doc_files:
                return 'docs'

        return 'chore'

    def generate_summary(self, changes, commit_type):
        """Generate commit summary (first line)"""
        if commit_type == 'feat':
            if len(changes['added']) == 1:
                filename = Path(changes['added'][0]).stem
                return f"add {filename}"
            else:
                return f"add {len(changes['added'])} new files"

        elif commit_type == 'fix':
            if len(changes['modified']) == 1:
                filename = Path(changes['modified'][0]).stem
                return f"fix issue in {filename}"
            else:
                return f"fix issues in {len(changes['modified'])} files"

        elif commit_type == 'refactor':
            if changes['deleted']:
                return f"remove {len(changes['deleted'])} files"
            else:
                return f"refactor {len(changes['modified'])} files"

        elif commit_type == 'test':
            return f"update tests"

        elif commit_type == 'docs':
            return f"update documentation"

        else:
            total = len(changes['added']) + len(changes['modified']) + len(changes['deleted'])
            return f"update {total} files"

    def generate_details(self, changes):
        """Generate detailed description"""
        details = []

        if changes['added']:
            details.append(f"Added files ({len(changes['added'])}):")
            for f in changes['added'][:5]:  # Max 5 files
                details.append(f"  - {f}")
            if len(changes['added']) > 5:
                details.append(f"  - ... and {len(changes['added']) - 5} more")

        if changes['modified']:
            details.append(f"\nModified files ({len(changes['modified'])}):")
            for f in changes['modified'][:5]:
                details.append(f"  - {f}")
            if len(changes['modified']) > 5:
                details.append(f"  - ... and {len(changes['modified']) - 5} more")

        if changes['deleted']:
            details.append(f"\nDeleted files ({len(changes['deleted'])}):")
            for f in changes['deleted'][:5]:
                details.append(f"  - {f}")
            if len(changes['deleted']) > 5:
                details.append(f"  - ... and {len(changes['deleted']) - 5} more")

        return details

    def find_git_repos(self, base_path):
        """
        Find all git repositories in base path
        Useful when running from non-git directory like .claude
        """
        git_repos = []

        try:
            base = Path(base_path)
            if not base.exists():
                return []

            # Check immediate subdirectories (1 level deep)
            for item in base.iterdir():
                if item.is_dir():
                    # Check if it has .git
                    if (item / '.git').exists():
                        git_repos.append(str(item))

                    # Check one level deeper (for nested structure)
                    try:
                        for subitem in item.iterdir():
                            if subitem.is_dir() and (subitem / '.git').exists():
                                git_repos.append(str(subitem))
                    except:
                        pass
        except:
            pass

        return git_repos

    def auto_commit(self, path='.', context=None, push=False, dry_run=False, auto_find=True):
        """
        Main entry point - auto commit with AI message

        Args:
            path: Git repo path (or base path to search)
            context: Task context for better messages
            push: Auto-push after commit
            dry_run: Don't actually commit
            auto_find: Auto-find git repos if current dir is not a repo
        """
        # Check if current path is a git repo
        if not self.check_git_repo(path):
            # If auto_find enabled and we're in .claude or similar
            if auto_find and ('.claude' in str(Path(path).resolve()) or path == '.'):
                # Try to find git repos in workspace
                workspace_path = Path.home() / 'Documents' / 'workspace-spring-tool-suite-4-4.27.0-new'

                if workspace_path.exists():
                    git_repos = self.find_git_repos(workspace_path)

                    if git_repos:
                        # Commit to all found repos
                        results = []
                        for repo_path in git_repos:
                            result = self._commit_single_repo(repo_path, context, push, dry_run)
                            results.append(result)

                        return {
                            'success': True,
                            'multi_repo': True,
                            'repos': results,
                            'total_repos': len(git_repos)
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'No git repositories found in {workspace_path}',
                            'path': path,
                            'suggestion': 'Run this script from a project directory with .git'
                        }
                else:
                    return {
                        'success': False,
                        'error': f'Workspace not found: {workspace_path}',
                        'path': path,
                        'suggestion': 'Run this script from a project directory with .git'
                    }

            return {
                'success': False,
                'error': 'Not a git repository',
                'path': path,
                'suggestion': 'Run this script from a project directory with .git, or use --auto-find to search workspace'
            }

        # Single repo commit
        return self._commit_single_repo(path, context, push, dry_run)

    def _commit_single_repo(self, path, context, push, dry_run):
        """Commit to a single repository"""

        # Get status
        status = self.get_git_status(path)
        if not status:
            return {
                'success': True,
                'skipped': True,
                'reason': 'No changes to commit',
                'path': path
            }

        # Get diff
        diff = self.get_git_diff(path, staged=False)

        # Analyze changes
        changes = self.analyze_changes(status, diff)

        # Generate commit message
        commit_message = self.generate_commit_message(changes, context)

        result = {
            'path': path,
            'changes': changes,
            'commit_message': commit_message,
            'dry_run': dry_run,
            'timestamp': datetime.now().isoformat()
        }

        # Commit (if not dry run)
        if not dry_run:
            # Stage all changes
            try:
                subprocess.run(
                    ['git', 'add', '.'],
                    cwd=path,
                    check=True,
                    timeout=10
                )
            except Exception as e:
                result['success'] = False
                result['error'] = f'Failed to stage changes: {e}'
                return result

            # Commit
            try:
                subprocess.run(
                    ['git', 'commit', '-m', commit_message],
                    cwd=path,
                    check=True,
                    timeout=10
                )
                result['success'] = True
                result['committed'] = True
            except Exception as e:
                result['success'] = False
                result['error'] = f'Failed to commit: {e}'
                return result

            # Push (if requested)
            if push:
                try:
                    subprocess.run(
                        ['git', 'push'],
                        cwd=path,
                        check=True,
                        timeout=30
                    )
                    result['pushed'] = True
                except Exception as e:
                    result['push_error'] = str(e)

        else:
            result['success'] = True

        # Log commit
        self.log_commit(result)

        return result

    def log_commit(self, result):
        """Log commit"""
        self.logs_path.mkdir(parents=True, exist_ok=True)

        log_entry = {
            'timestamp': result['timestamp'],
            'path': result['path'],
            'success': result.get('success', False),
            'dry_run': result['dry_run'],
            'file_count': sum(len(v) for v in result.get('changes', {}).values())
        }

        with open(self.commit_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def print_result(self, result):
        """Print formatted result"""
        print(f"\n{'='*70}")
        print(f"📦 Git Auto-Commit with AI (Phase 4)")
        print(f"{'='*70}\n")

        # Handle multi-repo results
        if result.get('multi_repo'):
            print(f"🔍 Found {result['total_repos']} git repositories\n")

            for i, repo_result in enumerate(result['repos'], 1):
                repo_path = Path(repo_result['path']).name
                print(f"[{i}/{result['total_repos']}] Repository: {repo_path}")

                if repo_result.get('skipped'):
                    print(f"   ⏭️  Skipped: {repo_result.get('reason', 'No changes')}")
                elif repo_result.get('success'):
                    changes = repo_result.get('changes', {})
                    total_changes = sum(len(v) for v in changes.values())
                    print(f"   ✅ Committed {total_changes} changes")
                    if repo_result.get('pushed'):
                        print(f"   ✅ Pushed to remote")
                else:
                    print(f"   ❌ Failed: {repo_result.get('error', 'Unknown error')}")

                print()

            print(f"{'='*70}\n")
            return

        # Handle single repo results
        if result.get('skipped'):
            print(f"⏭️  Skipped: {result.get('reason')}")
            print(f"📂 Path: {result.get('path')}")
            print(f"\n{'='*70}\n")
            return

        if not result.get('success', False) and result.get('error'):
            print(f"❌ Error: {result['error']}")
            if result.get('suggestion'):
                print(f"\n💡 Suggestion: {result['suggestion']}")
            print(f"\n{'='*70}\n")
            return

        changes = result.get('changes', {})
        print(f"📊 Changes Summary:")
        print(f"   Added: {len(changes.get('added', []))}")
        print(f"   Modified: {len(changes.get('modified', []))}")
        print(f"   Deleted: {len(changes.get('deleted', []))}")

        print(f"\n📝 Generated Commit Message:")
        print(f"───────────────────────────────────────────────────────────────")
        print(result['commit_message'])
        print(f"───────────────────────────────────────────────────────────────")

        if result['dry_run']:
            print(f"\n⚠️  DRY RUN MODE - No actual commit")
        else:
            if result.get('committed'):
                print(f"\n✅ Changes committed successfully!")

            if result.get('pushed'):
                print(f"✅ Changes pushed to remote!")
            elif result.get('push_error'):
                print(f"⚠️  Push failed: {result['push_error']}")

        print(f"\n{'='*70}\n")


def main():
    """CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Git Auto-Commit with AI (Phase 4)')
    parser.add_argument('--path', default='.', help='Git repository path (or base path to search)')
    parser.add_argument('--context', help='Task context for better messages')
    parser.add_argument('--push', action='store_true', help='Auto-push after commit')
    parser.add_argument('--dry-run', action='store_true', help='Dry run - no actual commit')
    parser.add_argument('--auto-find', action='store_true', default=True, help='Auto-find git repos in workspace (default: True)')
    parser.add_argument('--no-auto-find', dest='auto_find', action='store_false', help='Disable auto-find')

    args = parser.parse_args()

    committer = GitAutoCommitAI()
    result = committer.auto_commit(
        path=args.path,
        context=args.context,
        push=args.push,
        dry_run=args.dry_run,
        auto_find=args.auto_find
    )

    committer.print_result(result)

    sys.exit(0 if result.get('success', False) else 1)


if __name__ == '__main__':
    main()
