# Ax-Shell Development Guide

## Project Structure

```
ax-shell/
├── flake.nix              # Nix flake definition
├── nix/
│   ├── modules/
│   │   ├── ax-shell.nix   # NixOS module
│   │   └── lib.nix        # Module helper functions
│   └── packages/
│       ├── ax-shell.nix   # Main package derivation
│       ├── fabric-cli.nix
│       ├── python-fabric.nix
│       └── ...
├── config/
│   ├── platform.py        # Platform detection (Arch vs NixOS)
│   └── ...
├── modules/               # Python modules
├── main.py               # Entry point
└── main.css              # Styles
```

## Development Setup

### NixOS (Recommended)

Enter the development shell:

```bash
cd ax-shell
nix develop
```

This provides all dependencies. Run from source:

```bash
ax-shell
```

### Arch Linux

See the install script for Arch-specific setup.

## How the Nix Flake Works

### Source Handling

The flake uses `self` as the package source, meaning:
- When you run `nix build .#ax-shell`, it builds from your **current working directory**
- When users reference the flake from GitHub, it builds from the **commit in their flake.lock**
- No need to update hashes or rev numbers for normal development

The `fetchFromGitHub` fallback in `ax-shell.nix` is **only** for users who call the package directly without using the flake (rare case).

### Module Pattern

The NixOS module receives `self` (the flake) to access packages:

```nix
# flake.nix
nixosModules.ax-shell = import ./nix/modules/ax-shell.nix self;

# ax-shell.nix module
self:
{ config, lib, pkgs, ... }:
{
  package = lib.mkOption {
    default = self.packages.${pkgs.system}.default;
  };
}
```

This ensures users always get the package from the same flake version they imported.

## Release Process

### For Regular Development

1. Make changes
2. Test locally with `nix develop` then `ax-shell`
3. Commit and push to main
4. Users update with `nix flake update ax-shell`

**That's it.** No version bumps or tags needed for normal flake users.

### For Version Releases (Optional)

Version tags are useful for:
- Human-readable version numbers
- GitHub release pages
- Non-flake users using `fetchFromGitHub`

To create a release:

1. **Update version number** in `nix/packages/ax-shell.nix`:
   ```nix
   version = "0.0.65";  # NO "v" prefix here
   ```

2. **Commit the version bump**:
   ```bash
   git add nix/packages/ax-shell.nix
   git commit -m "version: 0.0.65"
   ```

3. **Create and push tag**:
   ```bash
   git tag v0.0.65  # Tag HAS "v" prefix
   git push origin main --tags
   ```

4. **Create GitHub release** (optional):
   - Go to GitHub releases
   - Create release from tag
   - Add changelog notes

### Version Number Convention

- **In code**: `version = "0.0.65"` (no "v" prefix)
- **Git tags**: `v0.0.65` (with "v" prefix)
- **fetchFromGitHub rev**: `rev = "v${version}"` (adds "v" prefix)

## Testing Changes

### Local Build Test

```bash
# Build package
nix build .#ax-shell

# Check output
ls ./result/lib/ax-shell/

# Run it
./result/bin/ax-shell
```

### Test NixOS Module

In your nixos-config, temporarily point to local source:

```nix
# flake.nix inputs
ax-shell.url = "path:/home/user/ax-shell";
```

Then rebuild:

```bash
sudo nixos-rebuild switch --flake .#hostname
```

Remember to change back to GitHub URL after testing.

## Platform Compatibility

The codebase supports both Arch Linux and NixOS through `config/platform.py`:

```python
from config.platform import is_nixos, get_asset_path, get_user_config_dir

# Detect platform
if is_nixos():
    # NixOS-specific behavior
else:
    # Arch Linux behavior

# Get asset paths (works on both platforms)
icon_path = get_asset_path("assets/icon.png")
```

- On Arch: Returns `~/.config/Ax-Shell/assets/icon.png`
- On NixOS: Returns `/nix/store/.../lib/ax-shell/assets/icon.png`

## Troubleshooting

### "Module not found" errors with fabric-cli

When `fabric-cli exec ax-shell 'code'` fails with import errors, it's because fabric-cli runs in a different Python context without the PYTHONPATH set up.

Solution: Pre-compute values before defining functions that fabric-cli will call:

```python
# Bad - import inside function fails when called via fabric-cli
def set_css():
    from config.platform import get_package_root  # Fails!
    ...

# Good - import at module level, use closure
from config.platform import get_package_root
_css_path = os.path.join(get_package_root(), "main.css")

def set_css():
    # Uses _css_path from closure
    ...
```

### Dirty Git tree warnings

```
warning: Git tree '/path/to/ax-shell' is dirty
```

This is normal during development. The flake builds from your working directory including uncommitted changes.

### Flake not updating

If `nix flake update ax-shell` doesn't pick up new commits:

1. Check the commit is pushed to GitHub
2. Delete the flake.lock entry and re-add:
   ```bash
   nix flake lock --update-input ax-shell
   ```
