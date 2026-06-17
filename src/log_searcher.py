import re
from typing import Any, Dict, List, Optional

from src.core.config import config as app_config
from src.core.logger import logger
from src.core.security import PIIMasker
from src.vfs import VirtualFileSystem


class LogSearcher:
    """
    Core engine for searching log files via the Virtual File System.
    Uses chunked block reading to handle massive files efficiently.
    """

    def __init__(self, vfs_instance: VirtualFileSystem):
        # Dependency Injection of VFS
        self.vfs = vfs_instance
        self.chunk_size = app_config.search.chunk_size_bytes

    async def search_file(
        self,
        filepath: str,
        query: Optional[str] = None,
        search_type: str = "smart",
        time_range=None,
        context_lines: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Searches a file based on a query and search_type ('smart', 'keyword', 'regex').
        Returns the matching line along with surrounding context lines.

        Args:
            filepath (str): The VFS or local path to search.
            query (Optional[str]): The search string.
            search_type (str): 'smart', 'keyword', or 'regex'.
            time_range: Deprecated/unused.
            context_lines (int): Lines before and after match to return.

        Returns:
            List[Dict]: Array of matches with line_num and content.
        """
        logger.debug("search_file_started", filepath=filepath, search_type=search_type)
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
                    escaped_query = re.escape(query).replace(r"\*", ".*")
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
                lines = await self.vfs.read_lines(
                    filepath, start_line=current_start, max_lines=block_size
                )
                if not lines:
                    break

                for idx, line in enumerate(lines):
                    line_num = current_start + idx
                    line_clean = line.strip()

                    # If we are currently collecting 'after' context for a previous match
                    if active_match and lines_to_grab_after > 0:
                        active_match["context_after"].append(
                            f"{line_num}: {line_clean}"
                        )
                        lines_to_grab_after -= 1
                        if lines_to_grab_after == 0:
                            # Finished collecting context for this match
                            # Format it nicely for the UI/AI
                            formatted_content = "\n".join(
                                active_match["context_before"]
                                + [
                                    f"> {active_match['line_num']}: {active_match['content']}"
                                ]
                                + active_match["context_after"]
                            )
                            # Mask PII in results before returning to UI/AI
                            formatted_content = PIIMasker.mask_pii(formatted_content)
                            results.append(
                                {
                                    "line_num": active_match["line_num"],
                                    "content": formatted_content,
                                }
                            )
                            active_match = None
                            total_matches += 1
                            if total_matches >= 50:
                                results.append(
                                    {
                                        "info": "Results truncated at 50 to protect AI context windows. Please refine your search."
                                    }
                                )
                                return results

                    # Check for a new match
                    match = False
                    if pattern:
                        if pattern.search(line):
                            match = True
                    elif query and search_type == "keyword":
                        if query in line:
                            match = True
                    elif not query:
                        match = True

                    if match and not active_match:
                        active_match = {
                            "line_num": line_num,
                            "content": line_clean,
                            "context_before": [
                                f"{num}: {txt}" for num, txt in rolling_buffer
                            ],
                            "context_after": [],
                        }
                        lines_to_grab_after = context_lines

                        # Edge case: If context_lines is 0, append immediately
                        if context_lines == 0:
                            results.append(
                                {
                                    "line_num": line_num,
                                    "content": f"> {line_num}: {line_clean}",
                                }
                            )
                            active_match = None
                            total_matches += 1
                            if total_matches >= 50:
                                results.append(
                                    {
                                        "info": "Results truncated at 50 to protect AI context windows. Please refine your search."
                                    }
                                )
                                return results

                    # Update rolling buffer
                    rolling_buffer.append((line_num, line_clean))
                    if len(rolling_buffer) > context_lines:
                        rolling_buffer.pop(0)

                current_start += block_size

            # If we hit EOF while collecting 'after' context
            if active_match:
                formatted_content = "\n".join(
                    active_match["context_before"]
                    + [f"> {active_match['line_num']}: {active_match['content']}"]
                    + active_match["context_after"]
                )
                # Mask PII in results before returning to UI/AI
                formatted_content = PIIMasker.mask_pii(formatted_content)
                results.append(
                    {"line_num": active_match["line_num"], "content": formatted_content}
                )

        except Exception as e:
            logger.error("search_file_failed", filepath=filepath, error=str(e))
            return [{"error": f"Error reading file {filepath}: {str(e)}"}]

        return results

    async def list_files_in_dir(self, directory: str) -> List[str]:
        """List all files in a given directory. Now uses VFS to support remote paths."""
        try:
            nodes = await self.vfs.list_dir(directory)
            return [n.path for n in nodes if not n.is_dir]
        except Exception as e:
            logger.error("list_dir_failed", directory=directory, error=str(e))
            return [f"Error reading directory {directory}: {str(e)}"]

    async def read_file_chunk(
        self, filepath: str, start_line: int = 1, max_lines: int = 100
    ) -> List[str]:
        """Reads a specific chunk of a file via VFS to avoid loading huge files into memory."""
        try:
            return await self.vfs.read_lines(
                filepath, start_line=start_line, max_lines=max_lines
            )
        except Exception as e:
            logger.error("read_file_failed", filepath=filepath, error=str(e))
            return [f"Error reading file {filepath}: {str(e)}"]
