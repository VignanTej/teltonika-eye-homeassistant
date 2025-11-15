# HACS Setup Guide for Teltonika EYE Sensors Integration

This guide will help you get the Teltonika EYE Sensors integration into HACS (Home Assistant Community Store).

## Repository Structure ✅

Your repository is now properly structured for HACS with all required files:

```
Repository Root/
├── .github/
│   └── workflows/
│       ├── validate.yml          # HACS validation workflow
│       └── release.yml            # Automated releases
├── custom_components/
│   └── teltonika_eye/             # Integration code
│       ├── __init__.py
│       ├── manifest.json
│       ├── config_flow.py
│       ├── coordinator.py
│       ├── sensor.py
│       ├── binary_sensor.py
│       ├── const.py
│       ├── README.md
│       └── translations/
│           └── en.json
├── hacs.json                      # HACS configuration
├── README_HACS.md                 # Main repository README
├── LICENSE                        # MIT License
├── CONTRIBUTING.md                # Contribution guidelines
└── Other project files...
```

## Steps to Get Into HACS

### 1. Create GitHub Repository

1. **Create a new GitHub repository** with a descriptive name like:
   - `teltonika-eye-homeassistant` (recommended)
   - `homeassistant-teltonika-eye`
   - `ha-teltonika-eye-sensors`

2. **Upload all files** from this project to your GitHub repository

3. **Rename README_HACS.md to README.md** in your GitHub repository:
   ```bash
   mv README_HACS.md README.md
   ```

4. **Repository URLs are already configured** for username `vignantej`
   - If using a different GitHub username, update URLs in README.md
   - Repository name should be `teltonika-eye-homeassistant`

### 2. Validate Repository Structure

Before submitting to HACS, ensure:

- ✅ `hacs.json` exists in repository root
- ✅ `custom_components/teltonika_eye/` contains all integration files
- ✅ `manifest.json` has correct domain and version
- ✅ `LICENSE` file exists
- ✅ `README.md` has proper HACS badges and installation instructions
- ✅ GitHub workflows are set up for validation

### 3. Create Initial Release

1. **Tag your first release**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Create GitHub Release**:
   - Go to your repository on GitHub
   - Click "Releases" → "Create a new release"
   - Tag: `v1.0.0`
   - Title: `v1.0.0 - Initial Release`
   - Description: Include features and installation instructions

3. **The release workflow will automatically**:
   - Update version in manifest.json
   - Create a zip file for download
   - Attach it to the release

### 4. Submit to HACS

#### Option A: Submit to HACS Default Repository (Recommended)

1. **Fork the HACS repository**: https://github.com/hacs/default
2. **Edit the integration file**: `hacs/default/integration`
3. **Add your repository** in alphabetical order:
   ```
   vignantej/teltonika-eye-homeassistant
   ```
4. **Create a Pull Request** with:
   - Title: `Add Teltonika EYE Sensors integration`
   - Description: Brief description of what the integration does

#### Option B: Add as Custom Repository

Users can add your repository manually:

1. **HACS** → **Integrations** → **⋮** → **Custom repositories**
2. **Repository**: `https://github.com/vignantej/teltonika-eye-homeassistant`
3. **Category**: Integration
4. **Add**

### 5. Repository Requirements Checklist

Ensure your repository meets HACS requirements:

- ✅ **Public GitHub repository**
- ✅ **Proper repository structure** with `custom_components/`
- ✅ **Valid `hacs.json`** configuration file
- ✅ **MIT License** (or compatible)
- ✅ **README.md** with installation instructions
- ✅ **At least one release** with semantic versioning
- ✅ **Working integration** that passes Home Assistant validation
- ✅ **Proper `manifest.json`** with all required fields

### 6. HACS Configuration Details

Your `hacs.json` is configured for:
- **Integration type**: Custom component
- **Home Assistant compatibility**: 2023.1.0+
- **IoT Class**: Local Polling
- **Multi-country support**: Worldwide availability

### 7. Maintenance and Updates

After HACS acceptance:

1. **Version Updates**:
   - Update version in `manifest.json`
   - Create new GitHub release
   - HACS will automatically detect updates

2. **Bug Fixes**:
   - Fix issues in code
   - Create new release
   - Users get update notifications in HACS

3. **Feature Additions**:
   - Add new features
   - Update documentation
   - Create new release with changelog

## Example Repository URLs

Repository URLs are pre-configured for:
```markdown
[commits-shield]: https://img.shields.io/github/commit-activity/y/vignantej/teltonika-eye-homeassistant.svg
[commits]: https://github.com/vignantej/teltonika-eye-homeassistant/commits/main
[releases-shield]: https://img.shields.io/github/release/vignantej/teltonika-eye-homeassistant.svg
[releases]: https://github.com/vignantej/teltonika-eye-homeassistant/releases
```

**Developer**: Vignan Tej
**Company**: Tez Solutions
**GitHub**: @vignantej

## Testing Before Submission

1. **Install manually** in Home Assistant to verify it works
2. **Test with real sensors** if available
3. **Check Home Assistant logs** for any errors
4. **Verify all entities** are created correctly
5. **Test configuration flow** works properly

## HACS Validation

Your repository includes automatic validation:
- **HACS validation**: Checks repository structure
- **Hassfest validation**: Validates Home Assistant integration
- **Runs on**: Push, PR, and daily schedule

## Support After HACS

Once in HACS, users can:
- ✅ **Install via HACS UI** (one-click installation)
- ✅ **Get automatic updates** when you release new versions
- ✅ **Easy uninstallation** through HACS
- ✅ **Browse integration** in HACS store

## Final Checklist

Before submitting to HACS:

- [ ] Repository is public on GitHub
- [ ] All files uploaded and properly structured
- [ ] README.md updated with correct repository URLs
- [ ] First release (v1.0.0) created
- [ ] Integration tested and working
- [ ] GitHub workflows passing
- [ ] License file included
- [ ] Contributing guidelines added

Your integration is now ready for HACS! 🎉

## Need Help?

- **HACS Documentation**: https://hacs.xyz/
- **HACS Discord**: https://discord.gg/apgchf8
- **Home Assistant Community**: https://community.home-assistant.io/