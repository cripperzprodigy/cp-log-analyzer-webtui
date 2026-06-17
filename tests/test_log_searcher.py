from unittest.mock import AsyncMock, patch

import pytest

from src.log_searcher import LogSearcher
from src.vfs import VFSNode, VirtualFileSystem


@pytest.fixture
def mock_vfs():
    vfs = VirtualFileSystem()

    # We need to simulate the chunking loop stopping.
    # Return lines on first call, empty list on second call to break the loop.
    vfs.read_lines = AsyncMock(
        side_effect=[["line 1", "error connecting to db", "line 3", "line 4"], []]
    )
    vfs.list_dir = AsyncMock(
        return_value=[VFSNode(name="app.log", path="vfs://test/app.log", is_dir=False)]
    )
    return vfs


@pytest.mark.asyncio
async def test_search_file_smart(mock_vfs):
    searcher = LogSearcher(vfs_instance=mock_vfs)
    results = await searcher.search_file(
        "vfs://test/app.log", query="error*db", search_type="smart", context_lines=0
    )

    assert len(results) == 1
    assert "error connecting to db" in results[0]["content"]


@pytest.mark.asyncio
async def test_list_files(mock_vfs):
    searcher = LogSearcher(vfs_instance=mock_vfs)
    files = await searcher.list_files_in_dir("vfs://test/")

    assert len(files) == 1
    assert files[0] == "vfs://test/app.log"
