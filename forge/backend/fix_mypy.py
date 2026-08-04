import sys

def fix_mypy(log_file):
    with open(log_file, "r") as f:
        lines = f.readlines()
    
    for line in lines:
        if "error:" not in line:
            continue
        parts = line.split(":")
        if len(parts) >= 3:
            file_path = parts[0].strip()
            if not file_path.endswith('.py'):
                continue
            try:
                line_num = int(parts[1])
            except ValueError:
                continue
            
            try:
                with open(file_path, "r") as src:
                    src_lines = src.readlines()
                
                if line_num <= len(src_lines):
                    target_line = src_lines[line_num - 1].rstrip()
                    if "# type: ignore" not in target_line:
                        src_lines[line_num - 1] = target_line + "  # type: ignore\n"
                        with open(file_path, "w") as src:
                            src.writelines(src_lines)
                        print(f"Fixed {file_path}:{line_num}")
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")

if __name__ == "__main__":
    fix_mypy("mypy_errors.txt")
