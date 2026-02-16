#!/usr/bin/env python
"""
Update README.md and CHANGELOG.md with new version
"""

import sys
import re
from pathlib import Path
from datetime import datetime


def update_readme_version(version):
    """Update version in README.md title"""
    readme = Path(__file__).parent.parent / "README.md"

    if not readme.exists():
        print("[WARNING] README.md not found")
        return False

    content = readme.read_text(encoding='utf-8')

    # Update title version (line 1)
    updated = re.sub(
        r'^# 🤖 Claude Insight v[\d.]+',
        f'# 🤖 Claude Insight v{version}',
        content,
        flags=re.MULTILINE
    )

    if updated != content:
        readme.write_text(updated, encoding='utf-8')
        print(f"[OK] README.md version updated to v{version}")
        return True
    else:
        print("[INFO] README.md version already up to date")
        return False


def update_changelog(version, bump_type):
    """Add new entry to CHANGELOG.md"""
    changelog = Path(__file__).parent.parent / "CHANGELOG.md"

    if not changelog.exists():
        print("[WARNING] CHANGELOG.md not found")
        return False

    content = changelog.read_text(encoding='utf-8')

    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')

    # Determine what was changed based on bump type
    if bump_type == "major":
        change_desc = "Major release with breaking changes"
    elif bump_type == "minor":
        change_desc = "New features and enhancements"
    else:  # patch
        change_desc = "Bug fixes and minor improvements"

    # Create new changelog entry
    new_entry = f"""## [{version}] - {today}

### {change_desc.split()[0]}
- {change_desc}

---

"""

    # Insert after "## [Unreleased]" section
    updated = re.sub(
        r'(## \[Unreleased\].*?---\n\n)',
        r'\1' + new_entry,
        content,
        flags=re.DOTALL
    )

    if updated != content:
        changelog.write_text(updated, encoding='utf-8')
        print(f"[OK] CHANGELOG.md entry added for v{version}")
        return True
    else:
        print("[INFO] CHANGELOG.md already contains v{version}")
        return False


def main():
    """Main entry point"""
    if len(sys.argv) != 3:
        print("Usage: python update-docs.py <version> <bump_type>")
        print("Example: python update-docs.py 2.5.2 patch")
        sys.exit(1)

    version = sys.argv[1]
    bump_type = sys.argv[2]

    print(f"Updating documentation for v{version}...")
    print()

    readme_updated = update_readme_version(version)
    changelog_updated = update_changelog(version, bump_type)

    print()
    if readme_updated or changelog_updated:
        print("[OK] Documentation updated successfully!")
    else:
        print("[INFO] No documentation changes needed")


if __name__ == "__main__":
    main()
