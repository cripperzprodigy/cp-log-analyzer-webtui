import os
import re
from src.vfs import vfs

class LogSearcher:
    def __init__(self, chunk_size=1048576):
        self.chunk_size = chunk_size
        self.vfs = vfs

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
            # We use vfs to read lines in chunks. 
            # In a real heavy-duty app, VFS should expose an async generator like aiofiles.
            # For simplicity here, we read in blocks.
            block_size = 5000
            current_start = 1
            total_matches = 0
            
            while True:
                lines = await self.vfs.read_lines(filepath, start_line=current_start, max_lines=block_size)
                if not lines:
                    break
                    
                for idx, line in enumerate(lines):
                    line_num = current_start + idx
                    match = False
                    
                    if pattern:
                        if pattern.search(line):
                            match = True
                    elif keyword:
                        if keyword in line:
                            match = True
                    else:
                        match = True

                    if match:
                        results.append({
                            "line_num": line_num,
                            "content": line.strip()
                        })
                        total_matches += 1
                        
                    if total_matches >= 1000:
                        results.append({"info": "Results truncated at 1000 lines. Please refine your search."})
                        return results
                        
                current_start += block_size
                
        except Exception as e:
            return [{"error": f"Error reading file {filepath}: {str(e)}"}]
            
        return results

    async def list_files_in_dir(self, directory):
        """List all files in a given directory. Now uses VFS to support remote paths."""
        try:
            nodes = await self.vfs.list_dir(directory)
            return [n.path for n in nodes if not n.is_dir]
        except Exception as e:
            return [f"Error reading directory {directory}: {str(e)}"]

    async def read_file_chunk(self, filepath, start_line=1, max_lines=100):
        """Reads a specific chunk of a file via VFS to avoid loading huge files into memory."""
        try:
            return await self.vfs.read_lines(filepath, start_line=start_line, max_lines=max_lines)
        except Exception as e:
            return [f"Error reading file {filepath}: {str(e)}"]
