
# === NEXUSQUANT TEST COMMANDS ===
# Full Audit:        python tests/test_runner.py host all
# Unit Tests:        python tests/test_runner.py host unit
# Integration:       python tests/test_runner.py host integration
# Raw Pytest:        docker-compose -f docker-compose.test.yml run --rm test_runner pytest tests/ -v
# ====================================

import re
import ast
import os
import sys
import argparse
import subprocess
from datetime import datetime

# Configuration
REPORTS_DIR = "REPORTS"
os.makedirs(REPORTS_DIR, exist_ok=True)



def extract_test_metadata(test_dir="tests"):
    """
    Scans test files and extracts OBJECTIVE and EXPECTED RESULT from docstrings.
    Returns a dict: { "test_function_name": {"objective": "...", "expected": "..."} }
    """
    metadata = {}
    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r") as f:
                    try:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                docstring = ast.get_docstring(node)
                                if docstring:
                                    obj_match = re.search(r"OBJECTIVE:\s*(.*)", docstring)
                                    exp_match = re.search(r"EXPECTED RESULT:\s*(.*)", docstring)
                                    
                                    metadata[node.name] = {
                                        "objective": obj_match.group(1).strip() if obj_match else "N/A",
                                        "expected": exp_match.group(1).strip() if exp_match else "N/A"
                                    }
                    except Exception as e:
                        print(f"Error parsing {path}: {e}")
    return metadata

def generate_pdf(results, category):
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos
    
    # Strip ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_results = ansi_escape.sub('', results)
    
    # Extract Metadata
    metadata = extract_test_metadata()

    class AlphaReport(FPDF):
        def header(self):
            self.set_fill_color(0, 51, 102) # NexusQuant Deep Blue
            self.rect(0, 0, 210, 30, 'F')
            self.set_font('helvetica', 'B', 18)
            self.set_text_color(255, 255, 255)
            self.cell(0, 15, 'NexusQuant Integrity Report', align='C', 
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_font('helvetica', 'I', 10)
            self.cell(0, 5, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 
                      align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('helvetica', 'I', 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, f'Page {self.page_no()}', align='C')

        def add_section(self, title, color=(0, 0, 150)):
            self.ln(5)
            self.set_font('helvetica', 'B', 12)
            self.set_text_color(*color)
            self.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_draw_color(*color)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(2)

    pdf = AlphaReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # 1. Summary Scorecard
    pdf.add_section("1. SIMULATION SCORECARD", (0, 102, 255))
    pdf.set_font('helvetica', '', 11)
    pdf.set_text_color(0, 0, 0)
    
    passed = clean_results.count("PASSED")
    failed = clean_results.count("FAILED")
    total = passed + failed
    
    pdf.cell(0, 8, f"Audit Category: {category.upper()}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(50, 8, f"Total Tests: {total}")
    pdf.set_text_color(0, 150, 0)
    pdf.cell(50, 8, f"Passed: {passed}")
    if failed > 0:
        pdf.set_text_color(255, 0, 0)
    else:
        pdf.set_text_color(0, 0, 0)
    pdf.cell(50, 8, f"Failed: {failed}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # 2. High-Fidelity Audit Ledger
    pdf.add_section("2. SYSTEM INTEGRITY AUDIT LEDGER", (0, 102, 255))
    
    # Table Header
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(0, 0, 0)
    
    widths = [40, 60, 60, 30]
    headers = ["TEST CASE", "OBJECTIVE", "EXPECTED", "VERDICT"]
    
    for i, h in enumerate(headers):
        pdf.cell(widths[i], 10, h, border=1, fill=True, align='C')
    pdf.ln()

    pdf.set_font('helvetica', '', 7)
    for line in clean_results.splitlines():
        if "::" in line:
            # Parse line: path/file.py::func_name RESULT [PERCENT]
            parts = line.split("::")
            if len(parts) >= 2:
                func_and_res = parts[1].split()
                if len(func_and_res) < 2:
                    continue # Skip malformed or weirdly wrapped lines
                func_name = func_and_res[0]
                res = func_and_res[1]
                
                meta = metadata.get(func_name, {"objective": "N/A", "expected": "N/A"})
                
                # Draw Row
                curr_y = pdf.get_y()
                if curr_y > 260: # Page break safety
                    pdf.add_page()
                    curr_y = pdf.get_y()

                # Multi-cell for wrapping content
                start_x = pdf.get_x()
                
                # Column 1: Function name
                pdf.multi_cell(widths[0], 5, func_name, border=1)
                max_h = pdf.get_y() - curr_y
                
                # Column 2: Objective
                pdf.set_xy(start_x + widths[0], curr_y)
                pdf.multi_cell(widths[1], 5, meta["objective"], border=1)
                max_h = max(max_h, pdf.get_y() - curr_y)
                
                # Column 3: Expected
                pdf.set_xy(start_x + widths[0] + widths[1], curr_y)
                pdf.multi_cell(widths[2], 5, meta["expected"], border=1)
                max_h = max(max_h, pdf.get_y() - curr_y)
                
                # Column 4: Verdict
                pdf.set_xy(start_x + widths[0] + widths[1] + widths[2], curr_y)
                if res == "PASSED":
                    pdf.set_text_color(0, 120, 0)
                else:
                    pdf.set_text_color(200, 0, 0)
                pdf.cell(widths[3], 5, res, border=1, align='C')
                max_h = max(max_h, pdf.get_y() - curr_y)
                
                pdf.set_text_color(0, 0, 0)
                pdf.set_xy(start_x, curr_y + max_h)

    # 3. Raw Execution Trace (Simplified)
    pdf.add_section("3. RAW EXECUTION TRACE", (100, 100, 100))
    pdf.set_font('courier', '', 6)
    pdf.set_text_color(50, 50, 50)
    
    # Only show summary info from raw output
    trace_lines = []
    capture = False
    for line in clean_results.splitlines():
        if "short test summary info" in line:
            capture = True
        if capture or "passed" in line:
            trace_lines.append(line)
            
    pdf.multi_cell(190, 3, "\n".join(trace_lines))
    
    report_path = os.path.join(REPORTS_DIR, f"INTEGRITY_REPORT_{category}.pdf")
    pdf.output(report_path)
    print(f"PDF Report Generated: {report_path}")

def run_internal(category):
    """Runs pytest inside container and generates PDF"""
    paths = {
        "unit": "tests/unit/",
        "integration": "tests/integration/",
        "decision": "tests/unit/test_decisions.py",
        "all": "tests/"
    }
    
    env = os.environ.copy()
    env["PYTHONPATH"] = f".{os.pathsep}{env.get('PYTHONPATH', '')}"
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    print("--- [PYTEST STDOUT] ---")
    print(result.stdout)
    print("--- [PYTEST STDERR] ---")
    print(result.stderr)
    
    generate_pdf(result.stdout, category)
    
    # We don't exit here anymore so the CI can finish the upload artifact step
    # but we should still return failure state if we want the job to fail.
    # Actually, sys.exit(1) is fine as long as we printed everything.
    if result.returncode != 0:
        print(f"ERROR: Pytest failed with exit code {result.returncode}")
        # sys.exit(1) # Keep it if you want the red X in GitHub
        sys.exit(result.returncode)

def run_host(category):
    """Triggers docker-compose from host"""
    print(f"[HOST] Triggering NexusQuant {category} tests in Docker...")
    cmd = ["docker-compose", "-f", "docker-compose.test.yml", "run", "--rm", "test_runner"]
    
    # Note: We don't append pytest here anymore because the container's 
    # command is already set to 'python tests/test_runner.py internal'
    # We pass the category via env or positional if we modify command
    
    # Actually, let's override the command to pass the category
    cmd.extend(["python", "tests/test_runner.py", "internal", category])
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print(f"FAILED: {category} tests.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NexusQuant Unified Test Runner")
    parser.add_argument("mode", choices=["host", "internal"], default="host", nargs="?")
    parser.add_argument("category", default="all", help="all, unit, integration, decision")
    
    args = parser.parse_args()
    
    if args.mode == "internal":
        run_internal(args.category)
    else:
        run_host(args.category)
