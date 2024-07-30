import os


ignore_list = [
    ".idea",
    ".git",
    ".svn",
    ".code",
    "__pycache__"
]


def generate_file_structure(root_dir: str) -> str:
    file_structure = []
    for root, dirs, files in os.walk(root_dir):
        if os.path.basename(root) in ignore_list:
            continue
        level = root.replace(root_dir, '').count(os.sep)
        indent = ' ' * 4 * level
        file_structure.append(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            file_structure.append(f"{subindent}{f}")
    return '\n'.join(file_structure)


if __name__ == "__main__":
    root_directory = r'C:\Users\loren\Projects\Epic7_Automation_Python'  # Replace with the path to your project directory
    structure = generate_file_structure(root_directory)
    print(structure)
