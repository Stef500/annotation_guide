# File and Folder Naming Standards

This document establishes naming conventions for the BRAT Annotation Guide project to ensure consistency and collaboration.

## Directory Structure Standards

### Core Directories
- `src/` - Source files and content
- `templates/` - LaTeX template components
- `docs/` - Documentation files
- `output/` - Generated PDF files
- `examples/` - Sample annotation files
- `scripts/` - Build and utility scripts
- `config/` - Configuration files

### Template Directory Structure
```
templates/
├── main.tex                 # Main document entry point
├── styles/                  # Styling and package imports
│   ├── packages.tex         # Package imports
│   └── formatting.tex       # Formatting definitions
├── layouts/                 # Page layout configurations
│   └── page-setup.tex       # Page geometry and headers
├── sections/                # Document sections
│   ├── title-page.tex       # Title page
│   ├── introduction.tex     # Introduction section
│   ├── annotation-guidelines.tex  # Guidelines section
│   └── examples.tex         # Examples section
└── components/              # Reusable components (future use)
```

## File Naming Conventions

### LaTeX Files
- Use lowercase with hyphens: `title-page.tex`
- Section files should be descriptive: `annotation-guidelines.tex`
- Component files should indicate purpose: `page-setup.tex`

### Documentation Files
- Use kebab-case for markdown files: `naming-standards.md`
- README files in each directory: `README.md`
- User guides: descriptive names like `getting-started.md`

### Script Files
- Use lowercase with extensions: `build.sh`
- Make scripts executable with appropriate permissions
- Include descriptive comments and error handling

### Configuration Files
- Use standard extensions: `.yml`, `.json`, `.toml`
- Descriptive names: `project.yml`, `build-config.json`

## Version Control Standards

### Branch Naming
- Feature branches: `feature/description`
- Bug fixes: `bugfix/issue-description`
- Documentation: `docs/update-description`

### Commit Messages
- Use imperative mood: "Add template structure"
- Keep first line under 50 characters
- Include detailed description if needed

## Collaboration Guidelines

### File Organization
- Keep related files in appropriate directories
- Use consistent indentation (2 spaces for YAML, 4 for others)
- Include comments in configuration files
- Document any special requirements or dependencies

### Documentation Requirements
- Every directory should have a README.md if it contains multiple files
- Update documentation when adding new components
- Include examples in documentation where appropriate
- Maintain this naming standards document