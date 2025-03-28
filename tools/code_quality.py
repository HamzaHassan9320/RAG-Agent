# tools/code_quality.py

import subprocess
from llama_index.core.tools import FunctionTool
import os
import json
from typing import Dict, List

class CodeQualityAnalyzer:
    def __init__(self):
        self.metrics = {
            "error": "🔴",
            "warning": "🟡",
            "convention": "🔵",
            "refactor": "🟣"
        }
    
    def run_pylint(self, file_path: str) -> str:
        """Run pylint and get the output"""
        try:
            result = subprocess.run(
                ["pylint", "--output-format=json", file_path],
                capture_output=True,
                text=True
            )
            return result.stdout
        except Exception as e:
            return json.dumps([{"message": f"Error running pylint: {str(e)}"}])
    
    def analyze_complexity(self, file_path: str) -> Dict:
        """Analyze code complexity using radon"""
        try:
            result = subprocess.run(
                ["radon", "cc", "--json", file_path],
                capture_output=True,
                text=True
            )
            return json.loads(result.stdout)
        except Exception as e:
            return {"error": str(e)}
    
    def format_pylint_results(self, results: List[Dict]) -> str:
        """Format pylint results into a readable report"""
        if not results:
            return "No issues found! 🎉"
            
        report = "# Code Quality Report\n\n"
        
        # Group by type
        issues_by_type = {}
        for issue in results:
            issue_type = issue.get("type", "unknown")
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)
        
        # Format each type
        for issue_type, issues in issues_by_type.items():
            emoji = self.metrics.get(issue_type, "❓")
            report += f"## {emoji} {issue_type.title()} ({len(issues)})\n\n"
            
            for issue in issues:
                report += f"- **Line {issue.get('line', '?')}:** {issue.get('message', 'No message')}\n"
                if "path" in issue:
                    report += f"  - In: `{issue['path']}`\n"
            report += "\n"
        
        return report
    
    def format_complexity_results(self, results: Dict) -> str:
        """Format complexity analysis results"""
        if "error" in results:
            return f"Error analyzing complexity: {results['error']}"
            
        report = "## 📊 Code Complexity Analysis\n\n"
        
        for file_path, functions in results.items():
            report += f"### File: `{os.path.basename(file_path)}`\n\n"
            
            if not functions:
                report += "No functions found to analyze.\n\n"
                continue
                
            for func in functions:
                complexity = func.get("complexity", "?")
                rank = "🟢" if complexity <= 5 else "🟡" if complexity <= 10 else "🔴"
                
                report += (f"- {rank} **{func.get('name', 'Unknown')}**\n"
                          f"  - Complexity: {complexity}\n"
                          f"  - Line numbers: {func.get('lineno', '?')}-{func.get('endline', '?')}\n")
            
            report += "\n"
            
        return report

def code_quality_tool_func(file_name: str) -> Dict:
    """Analyze code quality using multiple metrics"""
    path = os.path.join("data", file_name)
    analyzer = CodeQualityAnalyzer()
    
    try:
        # Run pylint analysis
        pylint_output = analyzer.run_pylint(path)
        pylint_results = json.loads(pylint_output) if pylint_output else []
        
        # Run complexity analysis
        complexity_results = analyzer.analyze_complexity(path)
        
        # Format results
        report = analyzer.format_pylint_results(pylint_results)
        report += "\n" + analyzer.format_complexity_results(complexity_results)
        
        return {
            "pylint_report": report,
            "raw_results": {
                "pylint": pylint_results,
                "complexity": complexity_results
            }
        }
    except Exception as e:
        return {"error": f"Error analyzing code: {str(e)}"}

# Wrap as a FunctionTool for the agent
code_quality_tool = FunctionTool.from_defaults(
    fn=code_quality_tool_func,
    name="CodeQualityAnalyzer",
    description=(
        "Analyzes Python code quality using multiple metrics including style, complexity, and best practices. "
        "Provides detailed reports with suggestions for improvement."
    )
)