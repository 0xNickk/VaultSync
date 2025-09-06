# VaultSync - Obsidian Vault Synchronization Tool
<img src = "https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue"> <img src = "https://img.shields.io/badge/GIT-E44C30?style=for-the-badge&logo=git&logoColor=white"> <img src = "https://img.shields.io/badge/Obsidian-483699?style=for-the-badge&logo=Obsidian&logoColor=white">


## 📖 Overview

VaultSync is a powerful command-line tool designed to automatically synchronize your Obsidian Vault with GitHub repositories. It monitors Obsidian's process state and performs Git operations seamlessly in the background, ensuring your notes are always backed up and synchronized across devices.

## ✨ Features

- **🔄 Automatic Synchronization** - Syncs when Obsidian starts/stops or at regular intervals
- **💾 Smart Backup System** - Creates local backups before sync operations
- **🔔 Desktop Notifications** - Real-time sync status updates
- **🚀 Background Operation** - Runs silently without interrupting your workflow
- **🖥️ Windows Auto-start** - Optional boot-time startup
- **📝 Comprehensive Logging** - Detailed operation logs for troubleshooting
- **⚙️ Flexible Configuration** - Command-line argument-based setup

## 🛠️ Installation

### Prerequisites

- **Python 3.8+**
- **Git** installed and accessible from command line
- **GitHub Personal Access Token**
- **Windows OS** (for auto-start features)

### Setup Steps

1. **Clone or download VaultSync**
   ```bash
   git clone https://github.com/0xNickk/VaultSync.git
   cd VaultSync
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure VaultSync** (see Configuration section)

## ⚙️ Configuration

VaultSync uses command-line arguments for configuration. No interactive setup required.

### Required Configuration

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

### Optional Configuration

```bash
# Sync mode (default: on_close)
python VaultSync.py --sync-mode "interval"  # or "on_close"

# Interval timing (for interval mode only)
python VaultSync.py --interval-time 5  # minutes

# Backup settings
python VaultSync.py --backup "enable"  # or "disable"
python VaultSync.py --backup-dir "C:/Backups/Vault"
python VaultSync.py --max-backups 5

# Notifications
python VaultSync.py --notification "enable"  # or "disable"
```

## 🚀 Usage

### Control Commands

```bash
# Run VaultSync normally (with console output)
python VaultSync.py --run

# Run VaultSync in background (no console)
python VaultSync.py --background

# Stop background process
python VaultSync.py --stop

# Check status
python VaultSync.py --status

# Show configuration
python VaultSync.py --config

# Check requirements
python VaultSync.py --check
```

### Auto-start Commands

```bash
# Enable auto-start on Windows boot
python VaultSync.py --enable-autorun

# Disable auto-start
python VaultSync.py --disable-autorun
```

## 📋 Sync Modes

### On-Close Mode (Default)
- **Pull** when Obsidian starts
- **Push** when Obsidian closes
- **Minimal resource usage**
- **Perfect for single-device usage**

### Interval Mode
- **Pull** when Obsidian starts
- **Push** at regular intervals while Obsidian is running
- **Great for multi-device synchronization**
- **Configurable interval timing**

## 🔧 Configuration Files

VaultSync uses two configuration files:

### `config.yaml`
```yaml
vault:
  path: "C:/Path/To/Your/Vault"
  branch: "main"

sync:
  mode: "on_close"  # or "interval"
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

### `.env`
```bash
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_USERNAME=YourGitHubUsername
GITHUB_REPOSITORY=YourRepositoryName
```

## ⚠️ Troubleshooting

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

## 🔒 Security Notes

- **Never share your `.env` file** - contains sensitive tokens
- **Use Personal Access Tokens** - more secure than passwords
- **Limit token permissions** - only grant necessary repository access

## 📧 Support

For issues, questions, or feature requests:
- **GitHub Issues:** [Create an issue](https://github.com/0xNickk/VaultSync/issues)

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Made by 0xNickk**
