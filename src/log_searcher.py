import os
import re
from src.vfs import vfs

class LogSearcher:
    def __init__(self, chunk_size=1048576):
        self.chunk_size = chunk_size
        self.vfs = vfs

    async def search_file(self, filepath, query=None, search_type="smart", time_range=None):
        """
        Searches a file based on a query and search_type ('smart', 'keyword', 'regex').
        Handles large files by chunked reading via VFS.
        """
        results = []
        pattern = None
        
        if query:
            if search_type == "regex":
                try:
                    pattern = re.compile(query)
                except re.error as e:
                    return [{"error": f"Invalid regex pattern: {e}"}]
            elif search_type == "smart":
                try:
                    # Smart search: Case-insensitive, escapes special characters except *, allows * as wildcard
                    escaped_query = re.escape(query).replace(r'\*', '.*')
                    # Wrap in word boundaries if it looks like a word, but keep it flexible
                    pattern = re.compile(escaped_query, re.IGNORECASE)
                except re.error as e:
                    return [{"error": f"Error building smart pattern: {e}"}]

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
                    
                    if pattern: # Handles 'regex' and 'smart'
                        if pattern.search(line):
                            match = True
                    elif query and search_type == "keyword": # Handles exact 'keyword'
                        if query in line:
                            match = True
                    elif not query:
                        match = True # Return all if no query (useful for small chunks)

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
