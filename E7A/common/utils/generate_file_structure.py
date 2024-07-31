import os


def should_ignore(path, ignore_dirs):
    """
    Check if the path or any of its parent directories should be ignored.
    """
    for ignore in ignore_dirs:
        if ignore in path:
            return True
    return False


def generate_file_structure(
        root_dir: str,
        ignore_dirs:
        list[str] = None) -> str:
    """
    Generate the file structure of the directory ignoring specified directories.
    """
    ignore_dirs = ignore_dirs or []
    file_structure = []
    for root, dirs, files in os.walk(root_dir):
        # If any parent directory is in the ignore list, skip this directory
        if should_ignore(root, ignore_dirs):
            continue
        level = root.replace(root_dir, '').count(os.sep)
        indent = ' ' * 4 * level
        file_structure.append(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            file_structure.append(f"{subindent}{f}")
    return '\n'.join(file_structure)


if __name__ == "__main__":
    ignore_list = [
        ".idea",
        ".git",
        ".svn",
        ".code",
        "__pycache__",
        "temp",
        "log",
        "E7A\\E7A.egg-info"
    ]

    # Replace with the path to your project directory
    root_directory = r'C:\Users\loren\Projects\Epic7_Automation_Python'
    structure = generate_file_structure(root_directory, ignore_list)
    print(structure)
