import os
import re
from src.vfs import vfs

class LogSearcher:
    def __init__(self, chunk_size=1048576):
        self.chunk_size = chunk_size
        self.vfs = vfs

    async def search_file(self, filepath, query=None, search_type="smart", time_range=None, context_lines=2):
        """
        Searches a file based on a query and search_type ('smart', 'keyword', 'regex').
        Returns the matching line along with surrounding context lines.
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
                    escaped_query = re.escape(query).replace(r'\*', '.*')
                    pattern = re.compile(escaped_query, re.IGNORECASE)
                except re.error as e:
                    return [{"error": f"Error building smart pattern: {e}"}]

        try:
            block_size = 5000
            current_start = 1
            total_matches = 0
            
            # Maintain a rolling buffer for "context before"
            rolling_buffer = []
            
            # If we find a match, we need to grab the next N lines for "context after"
            lines_to_grab_after = 0
            active_match = None
            
            while True:
                lines = await self.vfs.read_lines(filepath, start_line=current_start, max_lines=block_size)
                if not lines:
                    break
                    
                for idx, line in enumerate(lines):
                    line_num = current_start + idx
                    line_clean = line.strip()
                    
                    # If we are currently collecting 'after' context for a previous match
                    if active_match and lines_to_grab_after > 0:
                        active_match["context_after"].append(f"{line_num}: {line_clean}")
                        lines_to_grab_after -= 1
                        if lines_to_grab_after == 0:
                            # Finished collecting context for this match
                            # Format it nicely for the UI/AI
                            formatted_content = "\n".join(active_match["context_before"] + [f"> {active_match['line_num']}: {active_match['content']}"] + active_match["context_after"])
                            results.append({
                                "line_num": active_match["line_num"],
                                "content": formatted_content
                            })
                            active_match = None
                            total_matches += 1
                            if total_matches >= 50:
                                results.append({"info": "Results truncated at 50 to protect AI context windows. Please refine your search."})
                                return results

                    # Check for a new match
                    match = False
                    if pattern:
                        if pattern.search(line): match = True
                    elif query and search_type == "keyword":
                        if query in line: match = True
                    elif not query:
                        match = True

                    if match and not active_match:
                        active_match = {
                            "line_num": line_num,
                            "content": line_clean,
                            "context_before": [f"{num}: {txt}" for num, txt in rolling_buffer],
                            "context_after": []
                        }
                        lines_to_grab_after = context_lines
                        
                        # Edge case: If context_lines is 0, append immediately
                        if context_lines == 0:
                            results.append({
                                "line_num": line_num,
                                "content": f"> {line_num}: {line_clean}"
                            })
                            active_match = None
                            total_matches += 1
                            if total_matches >= 50:
                                results.append({"info": "Results truncated at 50 to protect AI context windows. Please refine your search."})
                                return results

                    # Update rolling buffer
                    rolling_buffer.append((line_num, line_clean))
                    if len(rolling_buffer) > context_lines:
                        rolling_buffer.pop(0)
                        
                current_start += block_size
                
            # If we hit EOF while collecting 'after' context
            if active_match:
                formatted_content = "\n".join(active_match["context_before"] + [f"> {active_match['line_num']}: {active_match['content']}"] + active_match["context_after"])
                results.append({
                    "line_num": active_match["line_num"],
                    "content": formatted_content
                })
                
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
