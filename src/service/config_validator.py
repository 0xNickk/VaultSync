#!/usr/bin/env python3
"""
Configuration validation for VaultSync.
Validates config.yaml and .env files for required settings.
"""

import yaml
from pathlib import Path
from typing import List


class ConfigValidator:

    def __init__( self, base_dir: Path ):

        self.base_dir    = base_dir
        self.config_file = self.base_dir / "config.yaml"
        self.env_file    = self.base_dir / ".env"

    def validate_configuration( self ) -> bool:

        if not self.config_file.exists():
            print("[x] Configuration file not found: config.yaml")
            return False

        if not self.env_file.exists():
            print("[x] Environment file not found: .env")
            return False

        try:

            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            env_vars = self._load_env_vars()
            missing_fields = self._check_required_fields(config, env_vars)

            if missing_fields:

                print("\n[x] Configuration is incomplete")
                print("[+] Missing required fields:")
                for field in missing_fields:
                    print(f"    - {field}")
                print("")

                return False

            vault_path = Path(config['vault']['path'])
            if not vault_path.exists():
                print(f"[x] Vault path does not exist: {vault_path}")
                print("[+] Please set a valid vault path using --vault-path\n")
                return False

            return True

        except Exception as e:
            print(f"[x] Error validating configuration: {e}")
            return False

    def _load_env_vars( self ) -> dict:

        env_vars = {}
        with open(self.env_file, 'r', encoding='utf-8') as f:

            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        return env_vars

    def _check_required_fields(self, config: dict, env_vars: dict) -> List[str]:

        missing_fields = []

        if not config.get('vault', {}).get('path'):
            missing_fields.append('vault.path')

        if not config.get('git', {}).get('user_name'):
            missing_fields.append('git.user_name')

        if not config.get('git', {}).get('user_email'):
            missing_fields.append('git.user_email')

        if not env_vars.get('GITHUB_TOKEN'):
            missing_fields.append('GITHUB_TOKEN (in .env)')

        if not env_vars.get('GITHUB_USERNAME'):
            missing_fields.append('GITHUB_USERNAME (in .env)')

        if not env_vars.get('GITHUB_REPOSITORY'):
            missing_fields.append('GITHUB_REPOSITORY (in .env)')

        return missing_fields

    def check_requirements(self) -> bool:

        print("\n[+] Checking VaultSync requirements...")
        print("-" * 50)

        required_files = [
            (self.env_file, "Environment file"),
            (self.config_file, "Configuration file"),
            (self.base_dir / "src" / "sync.py", "Sync engine"),
        ]

        missing_items = []

        for file_path, description in required_files:
            if file_path.exists():
                print(f"[+] {description}: {file_path}")
            else:
                print(f"[-] {description}: {file_path}")
                missing_items.append(description)

        print("-" * 50)

        dependencies = [
            ('psutil', 'Process monitoring'),
            ('schedule', 'Task scheduling'),
            ('plyer', 'Notifications'),
            ('anytree', 'Tree display (optional)'),
        ]

        for module, description in dependencies:
            try:
                __import__(module.replace('-', '_'))
                print(f"[+] {description}: {module}")

            except ImportError:

                if module == 'anytree':
                    print(f"[*] {description}: {module} (using fallback)")
                else:
                    print(f"[-] {description}: {module}")
                    missing_items.append(module)

        if missing_items:

            print(f"\n[x] Missing requirements: {', '.join(missing_items)}")
            print("[+] Install missing packages:")
            print("[+]  pip install -r requirements.txt")
            return False

        else:
            print("[+] All requirements satisfied!\n")
            return True
