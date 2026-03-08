import os
import re
import concurrent.futures

TOOL_TIMEOUT = 60  # seconds — max time any file tool is allowed to run


def list_files(directory, recursive=False):
    """Lists all files in a given directory."""
    def _run():
        if not os.path.isdir(directory):
            return f"Error: Directory '{directory}' not found."
        file_list = []
        for entry in os.scandir(directory):
            if entry.is_file():
                file_list.append(entry.path)
            elif entry.is_dir() and recursive:
                result = list_files(entry.path, recursive=True)
                if isinstance(result, list):
                    file_list.extend(result)
        return file_list

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run)
        try:
            return future.result(timeout=TOOL_TIMEOUT)
        except concurrent.futures.TimeoutError:
            return f"Error: list_files timed out after {TOOL_TIMEOUT} seconds."
        except Exception as e:
            return f"Error listing files in '{directory}': {e}"


def read_file(filepath):
    """Reads the content of a file."""
    def _run():
        if not os.path.exists(filepath):
            return f"Error: File '{filepath}' not found."
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run)
        try:
            return future.result(timeout=TOOL_TIMEOUT)
        except concurrent.futures.TimeoutError:
            return f"Error: read_file timed out after {TOOL_TIMEOUT} seconds."
        except Exception as e:
            return f"Error reading file '{filepath}': {e}"


def write_file(filepath, content):
    """Writes content to a file. Overwrites if it exists."""
    def _run():
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{filepath}' written successfully."

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run)
        try:
            return future.result(timeout=TOOL_TIMEOUT)
        except concurrent.futures.TimeoutError:
            return f"Error: write_file timed out after {TOOL_TIMEOUT} seconds."
        except Exception as e:
            return f"Error writing to file '{filepath}': {e}"


def delete_file(filepath):
    """Deletes a file or directory at the specified path."""
    def _run():
        if os.path.isdir(filepath):
            import shutil
            shutil.rmtree(filepath)
            return f"Directory '{filepath}' deleted successfully."
        elif os.path.exists(filepath):
            os.remove(filepath)
            return f"File '{filepath}' deleted successfully."
        else:
            return f"Error: Path '{filepath}' not found."

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run)
        try:
            return future.result(timeout=TOOL_TIMEOUT)
        except concurrent.futures.TimeoutError:
            return f"Error: delete_file timed out after {TOOL_TIMEOUT} seconds."
        except Exception as e:
            return f"Error deleting path '{filepath}': {e}"


def list_files_by_pattern(directory, pattern, recursive=False):
    """Lists files in a given directory that match a regex pattern."""
    def _run():
        if not os.path.isdir(directory):
            return f"Error: Directory '{directory}' not found."
        file_list = []
        for entry in os.scandir(directory):
            if entry.is_file() and re.search(pattern, entry.name):
                file_list.append(entry.path)
            elif entry.is_dir() and recursive:
                result = list_files_by_pattern(entry.path, pattern, recursive=True)
                if isinstance(result, list):
                    file_list.extend(result)
        return file_list

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run)
        try:
            return future.result(timeout=TOOL_TIMEOUT)
        except concurrent.futures.TimeoutError:
            return f"Error: list_files_by_pattern timed out after {TOOL_TIMEOUT} seconds."
        except Exception as e:
            return f"Error listing files by pattern in '{directory}': {e}"


def search_file_contents(directory, pattern, use_regex=False, recursive=False):
    """Searches within file contents for a pattern."""
    def _run():
        if not os.path.isdir(directory):
            return f"Error: Directory '{directory}' not found."
        results = []
        files_to_search = list_files(directory, recursive=recursive)
        if isinstance(files_to_search, str) and files_to_search.startswith("Error"):
            return files_to_search
        for filepath in files_to_search:
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    if use_regex:
                        if re.search(pattern, content):
                            results.append(filepath)
                    else:
                        if pattern in content:
                            results.append(filepath)
            except Exception:
                pass
        return results

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run)
        try:
            return future.result(timeout=TOOL_TIMEOUT)
        except concurrent.futures.TimeoutError:
            return f"Error: search_file_contents timed out after {TOOL_TIMEOUT} seconds."
        except Exception as e:
            return f"Error searching contents in '{directory}': {e}"
