#!/usr/bin/env python3
"""
Configuration display for VaultSync.
Pretty-prints configuration using tree structure.
"""

import yaml
from pathlib import Path
from anytree import Node, RenderTree


class ConfigDisplay:


    def __init__( self, base_dir: Path ):

        self.base_dir    = base_dir
        self.config_file = self.base_dir / "config.yaml"
        self.env_file    = self.base_dir / ".env"

    def show_config( self ) -> None:

        try:
            self._show_config_with_anytree()
        except Exception as e:
            print(f"[x] Config display error: {e}")

    def _show_config_with_anytree( self ) -> None:

        root = Node("\n📁 VaultSync Configuration")

        self._add_file_info(root)

        if self.config_file.exists():
            self._add_config_yaml_tree(root)
        else:
            Node("[x] config.yaml not found", parent=root)

        if self.env_file.exists():
            self._add_env_tree(root)
        else:
            Node("[x] .env not found", parent=root)

        for pre, fill, node in RenderTree(root):
            print(f"{pre}{node.name}")

        print()

    def _add_file_info( self, root: Node ) -> None:

        files_node = Node("📂 Files", parent=root)
        Node(f"📄 Config: {self.config_file.name}", parent=files_node)
        Node(f"🔑 Environment: {self.env_file.name}", parent=files_node)
        Node(f"📁 Directory: {self.base_dir}", parent=files_node)

    def _add_config_yaml_tree(self, root: Node) -> None:

        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        config_node = Node("📋 config.yaml", parent=root)

        # Vault section
        self._add_vault_section(config, config_node)

        # Sync section
        self._add_sync_section(config, config_node)

        # Backup section
        self._add_backup_section(config, config_node)

        # Logging section
        self._add_logging_section(config, config_node)

        # Notification section
        self._add_notification_section(config, config_node)

        # Git section
        self._add_git_section(config, config_node)

    def _add_vault_section( self, config: dict, parent: Node ) -> None:

        vault_node = Node("📁 Vault", parent=parent)
        Node(f"path: {config.get('vault', {}).get('path', 'NOT SET')}", parent=vault_node)
        Node(f"branch: {config.get('vault', {}).get('branch', 'main')}", parent=vault_node)

    def _add_sync_section( self, config: dict, parent: Node ) -> None:

        sync_node = Node("⚙️  Sync", parent=parent)
        Node(f"mode: {config.get('sync', {}).get('mode', 'on_close')}", parent=sync_node)
        Node(f"interval_minutes: {config.get('sync', {}).get('interval_minutes', 2)}", parent=sync_node)
        Node(f"process_name: {config.get('sync', {}).get('process_name', 'Obsidian.exe')}", parent=sync_node)

    def _add_backup_section( self, config: dict, parent: Node ) -> None:

        backup_enabled = config.get('backup', {}).get('enabled', True)
        backup_node = Node("💾 Backup", parent=parent)
        Node(f"enabled: {backup_enabled}", parent=backup_node)

        if backup_enabled:
            Node(f"directory: {config.get('backup', {}).get('directory', 'NOT SET')}", parent=backup_node)
            Node(f"max_backups: {config.get('backup', {}).get('max_backups', 2)}", parent=backup_node)

    def _add_logging_section( self, config: dict, parent: Node ) -> None:

        logging_node = Node("📝 Logging", parent=parent)
        Node(f"file: {config.get('logging', {}).get('file', 'VaultSync.log')}", parent=logging_node)
        Node(f"level: {config.get('logging', {}).get('level', 'INFO')}", parent=logging_node)

    def _add_notification_section( self, config: dict, parent: Node ) -> None:

        notification_enabled = config.get('notification', {}).get('enabled', True)
        notification_node = Node("🔔 Notification", parent=parent)
        Node(f"enabled: {notification_enabled}", parent=notification_node)

        if notification_enabled:
            Node(f"timeout: {config.get('notification', {}).get('timeout', 3)} seconds", parent=notification_node)
            icon_path = config.get('notification', {}).get('icon_path')
            Node(f"icon_path: {icon_path if icon_path else 'Default'}", parent=notification_node)

    def _add_git_section( self, config: dict, parent: Node ) -> None:

        git_node = Node("🔗 Git", parent=parent)
        Node(f"timeout: {config.get('git', {}).get('timeout', 120)} seconds", parent=git_node)
        Node(f"user_name: {config.get('git', {}).get('user_name', 'NOT SET')}", parent=git_node)
        Node(f"user_email: {config.get('git', {}).get('user_email', 'NOT SET')}", parent=git_node)

        gitignore = config.get('git', {}).get('gitignore', {})
        gitignore_node = Node("📝 gitignore", parent=git_node)

        for section, patterns in gitignore.items():
            if patterns:
                Node(f"{section}: {len(patterns)} pattern(s)", parent=gitignore_node)
            else:
                Node(f"{section}: No patterns", parent=gitignore_node)

    def _add_env_tree( self, root: Node ) -> None:

        env_node = Node("🔐 .env", parent=root)

        with open(self.env_file, 'r', encoding='utf-8') as f:

            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    if key == 'GITHUB_TOKEN':
                        if value:
                            obfuscated = self._obfuscate_token(value)
                            Node(f"{key}: {obfuscated}", parent=env_node)
                        else:
                            Node(f"{key}: NOT SET", parent=env_node)
                    else:
                        Node(f"{key}: {value if value else 'NOT SET'}", parent=env_node)

    def _obfuscate_token( self, token: str ) -> str:

        if len(token) > 8:
            return f"{token[:4]}{'*' * (len(token) - 8)}{token[-4:]}"
        else:
            return "***"


