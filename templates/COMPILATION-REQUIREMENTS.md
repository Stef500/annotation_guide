# Cross-Platform Compilation Requirements
## Task 4.7: XeLaTeX Template Compilation Guide

### System Requirements

#### Required Software
1. **TeX Live 2024** (recommended) or **MiKTeX 2024**
2. **XeLaTeX engine** (included in TeX distributions)
3. **Biber** for bibliography processing
4. **Python 3.8+** (for validation tools)

#### Required LaTeX Packages
The template requires the following packages (auto-installed by modern TeX distributions):

##### Core XeLaTeX Packages
- `fontspec` - Font handling for XeLaTeX
- `xunicode` - Unicode support
- `xltxtra` - XeLaTeX extras
- `polyglossia` - Multilingual typesetting

##### Typography and Layout
- `geometry` - Page layout
- `fancyhdr` - Headers and footers
- `titlesec` - Section formatting
- `microtype` - Typography enhancement
- `enumitem` - Enhanced lists

##### Mathematical Notation
- `amsmath`, `amsfonts`, `amssymb` - AMS math packages
- `mathtools` - Extended math tools
- `breqn` - Better equation breaking

##### Tables and Graphics
- `booktabs` - Professional tables
- `longtable` - Multi-page tables
- `array`, `tabularx` - Extended table support
- `xcolor` - Color support
- `graphicx` - Graphics inclusion
- `float` - Float placement

##### Advanced Features
- `tcolorbox` - Colored boxes
- `listings` - Code highlighting
- `hyperref` - Hyperlinks and bookmarks
- `biblatex` - Bibliography management

### Platform-Specific Instructions

#### Windows 10/11

##### Option 1: TeX Live (Recommended)
```powershell
# Download and install TeX Live 2024
# https://www.tug.org/texlive/
# Run install-tl-windows.exe as Administrator

# Verify installation
xelatex --version
biber --version
```

##### Option 2: MiKTeX
```powershell
# Download and install MiKTeX
# https://miktex.org/download
# Use MiKTeX Console to update packages

# Enable automatic package installation
# MiKTeX Console > Settings > General > Install missing packages: Ask me first
```

#### macOS (10.15+)

##### Option 1: MacTeX (Recommended)
```bash
# Download and install MacTeX 2024
# https://www.tug.org/mactex/
# This includes TeX Live 2024 + Mac-specific tools

# Verify installation
xelatex --version
biber --version
```

##### Option 2: Homebrew
```bash
# Install via Homebrew
brew install --cask mactex

# Or minimal installation
brew install basictex
sudo tlmgr update --self
sudo tlmgr install collection-xetex collection-fontsrecommended
```

#### Linux (Ubuntu/Debian)

##### Full Installation
```bash
# Install complete TeX Live
sudo apt update
sudo apt install texlive-full

# Or minimal XeLaTeX setup
sudo apt install texlive-xetex texlive-fonts-recommended texlive-fonts-extra
sudo apt install biber texlive-bibtex-extra texlive-science
```

##### Fedora/CentOS/RHEL
```bash
# Full installation
sudo dnf install texlive-scheme-full

# Or minimal XeLaTeX setup
sudo dnf install texlive-xetex texlive-fontspec texlive-polyglossia
sudo dnf install texlive-biblatex biber
```

##### Arch Linux
```bash
# Full installation
sudo pacman -S texlive-most texlive-lang

# Or minimal setup
sudo pacman -S texlive-bin texlive-core texlive-fontutils
sudo pacman -S biber texlive-bibtexextra
```

### Font Requirements

#### System Fonts
The template requires these fonts to be installed:

1. **Times New Roman** (Windows: built-in, macOS: built-in, Linux: install manually)
2. **Arial** (Windows: built-in, macOS: built-in, Linux: install manually)  
3. **Courier New** (Windows: built-in, macOS: built-in, Linux: install manually)

#### Linux Font Installation
```bash
# Ubuntu/Debian
sudo apt install ttf-mscorefonts-installer
sudo fc-cache -f

# Or download fonts manually to ~/.local/share/fonts/
mkdir -p ~/.local/share/fonts
# Copy font files and run:
fc-cache -f
```

### Compilation Commands

#### Standard Compilation
```bash
# Navigate to templates directory
cd templates

# Draft mode (faster)
make draft

# Final version (complete processing)
make final

# Clean build artifacts
make clean
```

#### Manual Compilation
```bash
# Full compilation sequence
xelatex main.tex
biber main
xelatex main.tex
xelatex main.tex
```

#### CI/CD Environment
```bash
# GitHub Actions / Docker
apt-get update
apt-get install -y texlive-xetex texlive-fonts-recommended texlive-fonts-extra
apt-get install -y texlive-bibtex-extra biber texlive-science

# Compilation
xelatex -interaction=nonstopmode main.tex
```

### Validation and Testing

#### Template Validation
```bash
# Run validation suite
python validation/template-validator.py

# Color consistency check  
python validation/color-consistency-test.py

# Test individual components
xelatex validation/math-notation-test.tex
xelatex validation/table-formatting-test.tex
xelatex validation/bibliography-test.tex
```

#### Performance Testing
```bash
# Benchmark compilation time
make benchmark

# Watch mode for development
make watch  # Requires inotify-tools on Linux
```

### Troubleshooting

#### Common Issues

1. **Font not found errors**
   - Install required system fonts
   - Clear font cache: `fc-cache -f`
   - Check font names: `fc-list | grep "Times"`

2. **Package not found errors**
   - Update package database: `tlmgr update --self`
   - Install missing packages: `tlmgr install <package>`

3. **Bibliography not appearing**
   - Ensure biber is installed and in PATH
   - Check .bib file encoding (UTF-8)
   - Run compilation sequence completely

4. **Compilation hangs**
   - Check for infinite loops in includes
   - Use `-interaction=nonstopmode` flag
   - Enable draft mode for faster testing

#### Platform-Specific Issues

**Windows:**
- Run Command Prompt as Administrator for font installation
- Use Windows Subsystem for Linux (WSL) for better compatibility
- Check PATH variables include TeX binaries

**macOS:**
- Ensure Xcode Command Line Tools installed
- Update macOS for latest font rendering
- Use Terminal.app or iTerm2 for compilation

**Linux:**
- Install font rendering libraries: `libfontconfig1-dev`
- Set proper locale: `export LANG=en_US.UTF-8`
- Check SELinux policies if using RHEL/CentOS

### Performance Optimization

#### Compilation Speed
- Use draft mode during development
- Enable font caching in performance.tex
- Use `\includeonly{}` for partial compilation
- Cache mathematical formulas with breqn

#### Memory Usage
- Enable etex memory management
- Use streaming for large documents
- Optimize image formats (PDF preferred)

### Continuous Integration

#### GitHub Actions Example
```yaml
name: LaTeX Build
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Install TeX Live
      run: |
        sudo apt-get update
        sudo apt-get install -y texlive-xetex texlive-fonts-recommended
        sudo apt-get install -y texlive-fonts-extra biber
    - name: Build PDF
      run: |
        cd templates
        make final
```

#### Docker Support
```dockerfile
FROM texlive/texlive:TL2024-historic
RUN apt-get update && apt-get install -y python3
COPY templates/ /workspace/
WORKDIR /workspace
RUN make final
```