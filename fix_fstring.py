with open("forge/backend/src/forge/infrastructure/search/context_retriever.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "f\"{r['payload'].get('file_path', '')}" in line:
        lines[i] = "                f\"{r['payload'].get('file_path', '')}\\n{r['payload'].get('name', '')}\\n{r['payload'].get('content', '')}\" \n"
    elif "{r['payload'].get('name', '')}" in line and not "file_path" in line:
        lines[i] = ""
    elif "{r['payload'].get('content', '')}\"" in line and not "file_path" in line:
        lines[i] = ""
        
with open("forge/backend/src/forge/infrastructure/search/context_retriever.py", "w") as f:
    f.writelines(lines)
