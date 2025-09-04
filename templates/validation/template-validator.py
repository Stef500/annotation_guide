#!/usr/bin/env python3
"""
BRAT Annotation Guide Template Validator
Task 4: Template Testing and Validation

Comprehensive validation framework for LaTeX template components
when XeLaTeX is not available for direct compilation testing.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set

class LaTeXTemplateValidator:
    """Validates LaTeX template structure, syntax, and compliance."""
    
    def __init__(self, template_dir: str):
        self.template_dir = Path(template_dir)
        self.validation_results = {}
        self.errors = []
        self.warnings = []
        
    def validate_all(self) -> Dict:
        """Run complete validation suite."""
        print("🧪 Starting BRAT Template Validation Suite")
        print("=" * 50)
        
        # Validate template structure
        self.validate_structure()
        
        # Validate syntax
        self.validate_syntax()
        
        # Validate XeLaTeX compatibility  
        self.validate_xelatex_compatibility()
        
        # Validate BRAT-specific components
        self.validate_brat_components()
        
        # Generate validation report
        return self.generate_report()
    
    def validate_structure(self) -> None:
        """Validate template directory structure and file organization."""
        print("📁 Validating template structure...")
        
        required_files = [
            'template-loader.tex',
            'main.tex',
            'styles/packages.tex',
            'styles/formatting.tex',
            'styles/typography.tex',
            'styles/tables.tex',
            'styles/mathematics.tex',
            'styles/multilingual.tex',
            'styles/performance.tex',
            'components/header.tex',
            'components/boxes.tex',
            'components/lists.tex',
            'components/navigation.tex',
            'Makefile'
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.template_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.errors.extend(f"Missing required file: {f}" for f in missing_files)
        else:
            print("✅ All required template files present")
            
        self.validation_results['structure'] = {
            'status': 'PASS' if not missing_files else 'FAIL',
            'missing_files': missing_files
        }
    
    def validate_syntax(self) -> None:
        """Validate LaTeX syntax in all template files."""
        print("📝 Validating LaTeX syntax...")
        
        syntax_errors = []
        tex_files = list(self.template_dir.rglob('*.tex'))
        
        for tex_file in tex_files:
            try:
                content = tex_file.read_text(encoding='utf-8')
                file_errors = self._check_latex_syntax(content, str(tex_file))
                syntax_errors.extend(file_errors)
            except Exception as e:
                syntax_errors.append(f"Error reading {tex_file}: {e}")
        
        if syntax_errors:
            self.errors.extend(syntax_errors)
            print(f"❌ Found {len(syntax_errors)} syntax issues")
        else:
            print("✅ LaTeX syntax validation passed")
            
        self.validation_results['syntax'] = {
            'status': 'PASS' if not syntax_errors else 'FAIL',
            'errors': syntax_errors
        }
    
    def _check_latex_syntax(self, content: str, filename: str) -> List[str]:
        """Check basic LaTeX syntax patterns."""
        errors = []
        
        # Check for unmatched braces
        brace_count = 0
        for i, char in enumerate(content):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count < 0:
                    errors.append(f"{filename}: Unmatched closing brace at position {i}")
                    
        if brace_count != 0:
            errors.append(f"{filename}: Unmatched opening braces ({brace_count})")
        
        # Check for unmatched environments
        begin_envs = re.findall(r'\\begin\{([^}]+)\}', content)
        end_envs = re.findall(r'\\end\{([^}]+)\}', content)
        
        for env in begin_envs:
            if begin_envs.count(env) != end_envs.count(env):
                errors.append(f"{filename}: Unmatched environment {env}")
        
        return errors
    
    def validate_xelatex_compatibility(self) -> None:
        """Validate XeLaTeX-specific features and compatibility."""
        print("🔧 Validating XeLaTeX compatibility...")
        
        compatibility_issues = []
        
        # Check for XeLaTeX-incompatible packages
        packages_file = self.template_dir / 'styles' / 'packages.tex'
        if packages_file.exists():
            content = packages_file.read_text(encoding='utf-8')
            
            # Should NOT contain these with XeLaTeX
            incompatible = ['inputenc', 'fontenc']
            for pkg in incompatible:
                if f'\\usepackage{{{pkg}}}' in content or f'\\usepackage[' in content and pkg in content:
                    compatibility_issues.append(f"Incompatible package {pkg} found (should be removed for XeLaTeX)")
            
            # Should contain these for XeLaTeX
            required = ['fontspec', 'polyglossia']  
            for pkg in required:
                if f'\\usepackage{{{pkg}}}' not in content:
                    compatibility_issues.append(f"Missing required XeLaTeX package: {pkg}")
        
        if compatibility_issues:
            self.warnings.extend(compatibility_issues)
            print(f"⚠️  Found {len(compatibility_issues)} compatibility issues")
        else:
            print("✅ XeLaTeX compatibility validation passed")
            
        self.validation_results['xelatex_compatibility'] = {
            'status': 'PASS' if not compatibility_issues else 'WARN',
            'issues': compatibility_issues
        }
    
    def validate_brat_components(self) -> None:
        """Validate BRAT-specific annotation components."""
        print("🏷️  Validating BRAT annotation components...")
        
        brat_issues = []
        typography_file = self.template_dir / 'styles' / 'typography.tex'
        
        if typography_file.exists():
            content = typography_file.read_text(encoding='utf-8')
            
            # Check for required BRAT commands
            required_commands = [
                'entitytype', 'relationtype', 'attributetype',
                'pathogen', 'symptom', 'medication'
            ]
            
            for cmd in required_commands:
                if f'\\newcommand{{\\{cmd}}}' not in content:
                    brat_issues.append(f"Missing BRAT command: \\{cmd}")
        else:
            brat_issues.append("Typography file missing")
        
        # Check table environments
        tables_file = self.template_dir / 'styles' / 'tables.tex'
        if tables_file.exists():
            content = tables_file.read_text(encoding='utf-8')
            
            required_envs = ['entitytable', 'relationtable', 'statstable']
            for env in required_envs:
                if f'\\newenvironment{{{env}}}' not in content:
                    brat_issues.append(f"Missing BRAT table environment: {env}")
        
        if brat_issues:
            self.errors.extend(brat_issues)
            print(f"❌ Found {len(brat_issues)} BRAT component issues")
        else:
            print("✅ BRAT component validation passed")
            
        self.validation_results['brat_components'] = {
            'status': 'PASS' if not brat_issues else 'FAIL',
            'issues': brat_issues
        }
    
    def generate_report(self) -> Dict:
        """Generate comprehensive validation report."""
        print("\n" + "=" * 50)
        print("📊 VALIDATION REPORT")
        print("=" * 50)
        
        total_errors = len(self.errors)
        total_warnings = len(self.warnings)
        
        overall_status = 'PASS' if total_errors == 0 else 'FAIL'
        
        print(f"Overall Status: {'✅ PASS' if overall_status == 'PASS' else '❌ FAIL'}")
        print(f"Errors: {total_errors}")
        print(f"Warnings: {total_warnings}")
        print()
        
        if self.errors:
            print("ERRORS:")
            for error in self.errors:
                print(f"  ❌ {error}")
            print()
            
        if self.warnings:
            print("WARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
            print()
        
        # Component status summary
        print("COMPONENT STATUS:")
        for component, result in self.validation_results.items():
            status_icon = {'PASS': '✅', 'FAIL': '❌', 'WARN': '⚠️'}[result['status']]
            print(f"  {status_icon} {component.replace('_', ' ').title()}: {result['status']}")
        
        return {
            'overall_status': overall_status,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'errors': self.errors,
            'warnings': self.warnings,
            'components': self.validation_results
        }


def main():
    """Main validation entry point."""
    template_dir = Path(__file__).parent.parent  # templates directory
    
    validator = LaTeXTemplateValidator(template_dir)
    report = validator.validate_all()
    
    # Exit with appropriate code
    sys.exit(0 if report['overall_status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()