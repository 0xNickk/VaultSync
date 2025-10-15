<p align="center">
  <img width="250" height="250" src="https://github.com/user-attachments/assets/b2ea31c7-2b3b-4782-8b71-3031132e74e3" />
</p>



# VaultSync


![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Git](https://img.shields.io/badge/Git-F05032?logo=git&logoColor=white)
![Obsidian](https://img.shields.io/badge/Obsidian-7C3AED?logo=obsidian&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Purpose

While the official [@Vinzent03/obsidian-git](https://github.com/Vinzent03/obsidian-git) plugin exists in the Obsidian community store, VaultSync was developed as a personal solution to address stability issues I encountered. After experiencing frequent crashes with the existing plugin that significantly impacted my productivity, I researched online and discovered that other users were facing similar problems. This led me to develop VaultSync as a more stable and highly customizable alternative that could be tailored to specific user needs and preferences.

## ✨ Features

- **Stable Operation** - Designed to prevent crashes and improve overall reliability
- **Automatic Synchronization** - Syncs when Obsidian starts/stops or at configurable intervals
- **Smart Backup System** - Creates local backups before sync operations
- **Desktop Notifications** - Real-time sync status updates
- **Background Operation** - Runs silently without interrupting workflow
- **Windows Auto-start** - Optional boot-time startup
- **Comprehensive Logging** - Detailed operation logs for troubleshooting
- **Flexible Configuration** - Highly customizable through command-line arguments

## Installation

### Prerequisites

- Python 3.8 or higher
- Git installed and accessible from command line
- [GitHub Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- Windows OS (for auto-start features)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/0xNickk/VaultSync.git
   cd VaultSync
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   
## ⚙️ Configuration

### Required Settings

```bash
# Set vault path
python VaultSync.py --vault-path "C:/Path/To/Your/Vault"

# Set Git credentials
python VaultSync.py --git-username "YourGitUsername"
python VaultSync.py --git-email "your.email@example.com"

# Set GitHub credentials
python VaultSync.py --github-username "YourGitHubUsername"
python VaultSync.py --github-repository "YourRepositoryName"
python VaultSync.py --github-token "ghp_your_personal_access_token"
```

### Optional Settings

```bash
# Sync mode (default: on_close)
python VaultSync.py --sync-mode "interval"

# Interval timing (for interval mode)
python VaultSync.py --interval-time 5  # minutes

# Backup configuration
python VaultSync.py --backup "enable"
python VaultSync.py --backup-dir "C:/Backups/Vault"
python VaultSync.py --max-backups 5

# Notifications
python VaultSync.py --notification "enable"
```

##  👀 Preview

<img width="1800" height="712" alt="image" src="https://github.com/user-attachments/assets/89233e5a-2f5a-4520-85e5-fd61db33a438" />


## 🔄 Sync Modes

### On-Close Mode (Default)
- Pulls when Obsidian starts
- Pushes when Obsidian closes
- Minimal resource usage
- Ideal for single-device usage

### Interval Mode
- Pulls when Obsidian starts
- Pushes at regular intervals while Obsidian is running
- Suitable for multi-device synchronization
- Configurable interval timing

##  📁 Configuration Files

### config.yaml
```yaml
vault:
  path: "C:/Path/To/Your/Vault"
  branch: "main"

sync:
  mode: "on_close"
  interval_minutes: 2
  process_name: "Obsidian.exe"

backup:
  enabled: true
  directory: "C:/Backups"
  max_backups: 2

git:
  user_name: "YourUsername"
  user_email: "your.email@example.com"
```

### .env
```bash
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_USERNAME=YourGitHubUsername
GITHUB_REPOSITORY=YourRepositoryName
```

##  🔧 Troubleshooting

### Common Issues

**Configuration Incomplete:**
```bash
python VaultSync.py --config  # Check missing fields
```

**VaultSync Won't Start:**
```bash
python VaultSync.py --check   # Verify requirements
```

**Process Already Running:**
```bash
python VaultSync.py --stop    # Stop background process
python VaultSync.py --status  # Check current status
```

**Git Authentication Issues:**
- Verify GitHub token has repository access
- Check token permissions (read/write)
- Ensure repository exists

## 🔒 Security

- Never share your `.env` file - contains sensitive tokens
- Limit token permissions to necessary repository access only


## ✨ Programmed Features

- Multi-Platform Support - Linux and macOS compatibility
- SSH Authentication - Secure SSH key-based authentication as alternative to tokens
- Advanced Scheduling - Date/time specific synchronization with cron-like syntax
- Multi-Repository Support - Manage multiple Obsidian vaults with different repositories

##  💬 Support

For issues, questions, or feature requests, please create an issue on the [GitHub repository](https://github.com/0xNickk/VaultSync/issues).

##  📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Developed by 0xNickk**
