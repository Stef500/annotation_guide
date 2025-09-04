#!/usr/bin/env python3
"""
Color Definitions and Consistency Validator
Task 4.6: Validate color rendering and visual consistency
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Set

class ColorConsistencyValidator:
    """Validates color definitions and usage consistency across template files."""
    
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.color_definitions = {}
        self.color_usages = []
        self.issues = []
    
    def validate_color_consistency(self) -> Dict:
        """Run complete color consistency validation."""
        print("🎨 Validating Color Definitions and Consistency")
        print("=" * 50)
        
        # Extract color definitions
        self._extract_color_definitions()
        
        # Find color usages
        self._find_color_usages()
        
        # Validate consistency
        self._validate_consistency()
        
        return self._generate_color_report()
    
    def _extract_color_definitions(self) -> None:
        """Extract all color definitions from template files."""
        print("🔍 Extracting color definitions...")
        
        tex_files = list(self.template_dir.rglob('*.tex'))
        
        for tex_file in tex_files:
            try:
                content = tex_file.read_text(encoding='utf-8')
                
                # Find \definecolor commands
                definecolor_pattern = r'\\definecolor\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}'
                matches = re.findall(definecolor_pattern, content)
                
                for match in matches:
                    color_name, color_model, color_value = match
                    self.color_definitions[color_name] = {
                        'model': color_model,
                        'value': color_value,
                        'file': str(tex_file.relative_to(self.template_dir))
                    }
                
                # Find \colorlet commands
                colorlet_pattern = r'\\colorlet\{([^}]+)\}\{([^}]+)\}'
                matches = re.findall(colorlet_pattern, content)
                
                for match in matches:
                    new_name, source_name = match
                    self.color_definitions[new_name] = {
                        'model': 'alias',
                        'value': source_name,
                        'file': str(tex_file.relative_to(self.template_dir))
                    }
                    
            except Exception as e:
                self.issues.append(f"Error reading {tex_file}: {e}")
        
        print(f"📊 Found {len(self.color_definitions)} color definitions")
    
    def _find_color_usages(self) -> None:
        """Find all color usages in template files."""
        print("🔍 Finding color usages...")
        
        tex_files = list(self.template_dir.rglob('*.tex'))
        
        color_usage_patterns = [
            r'\\textcolor\{([^}]+)\}',
            r'\\color\{([^}]+)\}',
            r'\\rowcolor\{([^}]+)\}',
            r'\\columncolor\{([^}]+)\}',
            r'\\cellcolor\{([^}]+)\}',
            r'colframe=([^,}\]]+)',
            r'colback=([^,}\]]+)',
            r'linkcolor=([^,}\]]+)',
            r'urlcolor=([^,}\]]+)'
        ]
        
        for tex_file in tex_files:
            try:
                content = tex_file.read_text(encoding='utf-8')
                
                for pattern in color_usage_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        self.color_usages.append({
                            'color': match,
                            'file': str(tex_file.relative_to(self.template_dir)),
                            'pattern': pattern
                        })
                        
            except Exception as e:
                self.issues.append(f"Error reading {tex_file}: {e}")
        
        print(f"📊 Found {len(self.color_usages)} color usages")
    
    def _validate_consistency(self) -> None:
        """Validate color consistency and find issues."""
        print("✅ Validating color consistency...")
        
        # Check for undefined colors
        defined_colors = set(self.color_definitions.keys())
        used_colors = set(usage['color'] for usage in self.color_usages)
        
        undefined_colors = used_colors - defined_colors
        
        # Filter out common LaTeX color names
        standard_colors = {
            'black', 'white', 'red', 'green', 'blue', 'yellow', 'cyan', 'magenta',
            'orange', 'purple', 'brown', 'pink', 'gray', 'grey', 'lightgray',
            'darkgray', 'lightblue', 'darkblue', 'lightgreen', 'darkgreen'
        }
        
        undefined_colors = undefined_colors - standard_colors
        
        if undefined_colors:
            for color in undefined_colors:
                files_using = [u['file'] for u in self.color_usages if u['color'] == color]
                self.issues.append(f"Undefined color '{color}' used in: {', '.join(set(files_using))}")
        
        # Check for unused defined colors
        unused_colors = defined_colors - used_colors
        if unused_colors:
            for color in unused_colors:
                definition = self.color_definitions[color]
                self.issues.append(f"Unused color definition '{color}' in {definition['file']}")
        
        # Validate RGB values
        for color_name, definition in self.color_definitions.items():
            if definition['model'] == 'RGB':
                rgb_values = definition['value'].split(',')
                if len(rgb_values) != 3:
                    self.issues.append(f"Invalid RGB definition for '{color_name}': {definition['value']}")
                else:
                    for i, value in enumerate(rgb_values):
                        try:
                            val = int(value.strip())
                            if not 0 <= val <= 255:
                                self.issues.append(f"RGB value out of range for '{color_name}': {value}")
                        except ValueError:
                            self.issues.append(f"Invalid RGB value for '{color_name}': {value}")
    
    def _generate_color_report(self) -> Dict:
        """Generate comprehensive color validation report."""
        print("\n" + "=" * 50)
        print("🎨 COLOR VALIDATION REPORT")
        print("=" * 50)
        
        status = 'PASS' if not self.issues else 'FAIL'
        
        print(f"Overall Status: {'✅ PASS' if status == 'PASS' else '❌ FAIL'}")
        print(f"Issues Found: {len(self.issues)}")
        print()
        
        print("COLOR DEFINITIONS:")
        for name, definition in sorted(self.color_definitions.items()):
            if definition['model'] == 'RGB':
                print(f"  🎨 {name}: RGB({definition['value']}) - {definition['file']}")
            else:
                print(f"  🔗 {name}: alias to {definition['value']} - {definition['file']}")
        print()
        
        if self.issues:
            print("ISSUES:")
            for issue in self.issues:
                print(f"  ❌ {issue}")
            print()
        
        # Color usage summary
        color_counts = {}
        for usage in self.color_usages:
            color = usage['color']
            color_counts[color] = color_counts.get(color, 0) + 1
        
        print("COLOR USAGE FREQUENCY:")
        for color, count in sorted(color_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  📊 {color}: {count} uses")
        
        return {
            'status': status,
            'definitions': self.color_definitions,
            'usages': self.color_usages,
            'issues': self.issues,
            'usage_counts': color_counts
        }


def main():
    """Main color validation entry point."""
    template_dir = Path(__file__).parent.parent  # templates directory
    
    validator = ColorConsistencyValidator(template_dir)
    report = validator.validate_color_consistency()
    
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    exit(main())