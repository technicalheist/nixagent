import os
import re

def list_files(directory, recursive=False):
    """
    Lists all files in a given directory.
    """
    if not os.path.isdir(directory):
        return f"Error: Directory '{directory}' not found."

    try:
        file_list = []
        for entry in os.scandir(directory):
            if entry.is_file():
                file_list.append(entry.path)
            elif entry.is_dir() and recursive:
                file_list.extend(list_files(entry.path, recursive=True))
        return file_list
    except Exception as e:
        return f"Error listing files in '{directory}': {e}"

def read_file(filepath):
    """
    Reads the content of a file.
    """
    if not os.path.exists(filepath):
        return f"Error: File '{filepath}' not found."
    try:
        with open(filepath, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file '{filepath}': {e}"

def write_file(filepath, content):
    """
    Writes content to a file.
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(content)
        return f"File '{filepath}' written successfully."
    except Exception as e:
        return f"Error writing to file '{filepath}': {e}"

def delete_file(filepath):
    """
    Deletes a file or directory at the specified path.
    """
    try:
        if os.path.isdir(filepath):
            import shutil
            shutil.rmtree(filepath)
            return f"Directory '{filepath}' deleted successfully."
        elif os.path.exists(filepath):
            os.remove(filepath)
            return f"File '{filepath}' deleted successfully."
        else:
            return f"Error: Path '{filepath}' not found."
    except Exception as e:
        return f"Error deleting path '{filepath}': {e}"

def list_files_by_pattern(directory, pattern, recursive=False):
    """
    Lists files in a given directory that match a regex pattern.
    """
    if not os.path.isdir(directory):
        return f"Error: Directory '{directory}' not found."

    try:
        file_list = []
        for entry in os.scandir(directory):
            if entry.is_file() and re.search(pattern, entry.name):
                file_list.append(entry.path)
            elif entry.is_dir() and recursive:
                file_list.extend(
                    list_files_by_pattern(entry.path, pattern, recursive=True)
                )
        return file_list
    except Exception as e:
        return f"Error listing files by pattern in '{directory}': {e}"

def search_file_contents(directory, pattern, use_regex=False, recursive=False):
    """
    Searches within file contents iteratively.
    """
    if not os.path.isdir(directory):
        return f"Error: Directory '{directory}' not found."

    results = []
    try:
        files_to_search = list_files(directory, recursive=recursive)
        if isinstance(files_to_search, str) and files_to_search.startswith("Error"):
            return files_to_search
            
        for filepath in files_to_search:
            try:
                with open(filepath, "r", encoding='utf-8') as f:
                    content = f.read()
                    if use_regex:
                        if re.search(pattern, content):
                            results.append(filepath)
                    else:
                        if pattern in content:
                            results.append(filepath)
            except UnicodeDecodeError:
                pass # Skip binary files
            except Exception:
                pass
        return results
    except Exception as e:
        return f"Error searching contents in '{directory}': {e}"
