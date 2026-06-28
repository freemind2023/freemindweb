# Website Source Files

This folder should contain (or link to) your website's source files.

## Setup

Option 1 — **Symlink** (recommended, avoids duplication):

```bash
# Windows
mklink /D website\src "D:\Free Mind Website\freemind-website"

# Linux/Mac
ln -s /path/to/your/website website/src
```

Option 2 — **Copy** the website source here:

```bash
cp -r /path/to/your/website/* website/
```

## How the Agent Uses This

- The agent reads files here to analyze content, structure, and technical SEO
- Optimized files are written to `output/` — never directly modified here
- Before any modification, the original file is backed up to `backups/`
- You review all changes in `output/` and manually apply them to your live site

## Important

- Never commit your full website source to this repo
- Add the appropriate paths to `.gitignore` if you copy files here
- The symlink approach keeps a single source of truth
