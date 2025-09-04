# BRAT Annotation Guide Template - Usage Examples

This directory contains comprehensive examples demonstrating all features of the BRAT Annotation Guide Template system.

## Example Documents

### 1. Complete Annotation Guide (`complete-annotation-guide.tex`)
A full-featured example demonstrating:
- ✅ Document header and navigation
- ✅ Entity and relation tables  
- ✅ Mathematical notation for metrics
- ✅ Information boxes and guidelines
- ✅ Multilingual support
- ✅ Advanced table layouts
- ✅ Bibliography integration
- ✅ Quality assurance elements

### 2. Test Documents (in `../validation/`)
- `math-notation-test.tex` - Mathematical notation testing
- `table-formatting-test.tex` - Table structure validation  
- `bibliography-test.tex` - Citation and bibliography testing

## Compilation Instructions

### Quick Start
```bash
# Navigate to templates directory
cd templates

# Compile complete example
xelatex examples/complete-annotation-guide.tex
biber complete-annotation-guide
xelatex examples/complete-annotation-guide.tex
```

### Using Makefile
```bash
# From templates directory
make final  # Compiles main.tex
```

### Individual Examples
```bash
# Compile specific example
cd examples
xelatex complete-annotation-guide.tex

# Or using relative paths
cd templates
xelatex examples/complete-annotation-guide.tex
```

## Template Features Demonstrated

### Typography and Layout
- Custom document headers with version information
- Section introduction formatting
- Professional typography with XeLaTeX optimization
- Consistent spacing and font handling

### BRAT-Specific Elements
- Entity type definitions with color coding
- Relation type specifications
- Medical terminology formatting
- Annotation guideline structures

### Advanced Components
- Information boxes (important, note, example, warning)
- Statistical tables with alternating row colors
- Mathematical notation for annotation metrics
- Long tables for extensive guidelines
- Navigation aids and cross-references

### Quality Assurance
- Validation frameworks
- Consistency checking
- Color scheme verification
- Syntax validation tools

## Customization Guide

### Modifying Colors
Edit `styles/formatting.tex`:
```latex
\definecolor{primarycolor}{RGB}{52, 73, 94}      % Main theme color
\definecolor{secondarycolor}{RGB}{149, 165, 166} % Accent color
```

### Adding New Entity Types
Edit `styles/typography.tex`:
```latex
\newcommand{\newentitytype}[1]{\texttt{\textcolor{primarycolor}{\textbf{#1}}}}
```

### Custom Table Environments
Edit `styles/tables.tex` to add new table types:
```latex
\newenvironment{customtable}[1][Custom Table]
{%
    \begin{table}[H]
    \centering
    \caption{#1}
    % ... table definition
}{%
    \end{table}
}
```

### Bibliography Styles
Modify `styles/packages.tex` for different citation formats:
```latex
\ExecuteBibliographyOptions{
    style=numeric,        % numeric, authoryear, etc.
    sorting=none,         % none, nyt, ynt, etc.
    maxbibnames=5
}
```

## Performance Considerations

### Draft Mode
For faster compilation during development:
- Use `make draft` command
- Enable draft mode in `styles/performance.tex`
- Disable microtype and complex graphics

### Memory Optimization
The template includes optimizations for:
- Font caching and preloading
- Mathematical formula caching
- Table rendering performance
- Large document processing

### Cross-Platform Testing
Tested on:
- ✅ Windows 10/11 with TeX Live 2024
- ✅ macOS 12+ with MacTeX 2024
- ✅ Ubuntu 20.04+ with TeX Live
- ✅ GitHub Actions CI/CD environment

## Integration with BRAT Tools

### Configuration Files
The template generates BRAT-compatible configuration:
- Entity type definitions
- Relation specifications
- Color schemes matching BRAT interface
- Export format compatibility

### Workflow Integration
1. **Annotation**: Use BRAT web interface
2. **Documentation**: Generate guides with this template
3. **Training**: Create materials using example documents
4. **Quality Control**: Use validation tools provided

## Known Limitations and Solutions

### Font Requirements
- Requires Times New Roman, Arial, Courier New
- Linux users: install `ttf-mscorefonts-installer`
- Alternative: Configure different fonts in `styles/formatting.tex`

### Large Documents
- Use `\includeonly{}` for partial compilation
- Enable performance optimizations
- Consider splitting into multiple documents

### Complex Tables
- Long tables may require manual page breaks
- Use `longtable` environment for multi-page tables
- Adjust column widths for content fitting

## Support and Troubleshooting

### Common Issues
1. **Compilation errors**: Check COMPILATION-REQUIREMENTS.md
2. **Missing fonts**: Install required system fonts
3. **Package errors**: Update TeX distribution
4. **Bibliography issues**: Ensure biber is installed and in PATH

### Validation Tools
```bash
# Run comprehensive validation
python validation/template-validator.py

# Check color consistency  
python validation/color-consistency-test.py

# Syntax validation
python validation/syntax-checker.py
```

### Getting Help
- Check COMPILATION-REQUIREMENTS.md for platform-specific instructions
- Review validation output for specific error messages
- Ensure all required packages are installed
- Verify font availability with `fc-list | grep Times`

## Contributing

To contribute additional examples or improvements:
1. Follow existing naming conventions
2. Include comprehensive documentation
3. Test on multiple platforms
4. Validate with provided tools
5. Update this README with new examples