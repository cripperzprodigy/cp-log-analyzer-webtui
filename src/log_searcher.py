import os
import re
import aiofiles

class LogSearcher:
    def __init__(self, chunk_size=1048576):
        self.chunk_size = chunk_size

    async def search_file(self, filepath, keyword=None, regex=None, time_range=None):
        """
        Searches a file for a keyword or regex pattern, returning matching lines.
        Handles large files by reading asynchronously line-by-line using aiofiles.
        """
        results = []
        pattern = None
        
        if regex:
            try:
                pattern = re.compile(regex)
            except re.error as e:
                return [{"error": f"Invalid regex pattern: {e}"}]

        try:
            async with aiofiles.open(filepath, mode='r', encoding='utf-8', errors='replace') as f:
                line_num = 0
                async for line in f:
                    line_num += 1
                    match = False
                    
                    if pattern:
                        if pattern.search(line):
                            match = True
                    elif keyword:
                        if keyword in line:
                            match = True
                    else:
                        match = True # If no search criteria, return all (maybe not ideal for huge files, but useful for small chunks)

                    if match:
                        results.append({
                            "line_num": line_num,
                            "content": line.strip()
                        })
                        
                    # Stop after 1000 matches to prevent memory explosion if not careful
                    if len(results) >= 1000:
                        results.append({"info": "Results truncated at 1000 lines. Please refine your search."})
                        break
                        
        except Exception as e:
            return [{"error": f"Error reading file {filepath}: {str(e)}"}]
            
        return results

    async def list_files_in_dir(self, directory):
        """List all files in a given directory and its subdirectories."""
        file_list = []
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    file_list.append(os.path.join(root, file))
        except Exception as e:
            return [f"Error reading directory {directory}: {str(e)}"]
        return file_list

    async def read_file_chunk(self, filepath, start_line=1, max_lines=100):
        """Reads a specific chunk of a file to avoid loading huge files into memory."""
        lines = []
        try:
            async with aiofiles.open(filepath, mode='r', encoding='utf-8', errors='replace') as f:
                current_line = 0
                async for line in f:
                    current_line += 1
                    if current_line >= start_line:
                        lines.append(line.strip())
                    if len(lines) >= max_lines:
                        break
        except Exception as e:
            return [f"Error reading file {filepath}: {str(e)}"]
        return lines
