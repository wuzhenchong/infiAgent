
import pytest
import os
import shutil
from pathlib import Path
from tool_server_lite.tools.file_tools import (
    FileReadTool,
    FileWriteTool,
    DirListTool,
    DirCreateTool,
    FileMoveTool,
    FileDeleteTool,
)

pytestmark = pytest.mark.unit

@pytest.fixture
def workspace(tmp_path):
    """Fixture to provide a temporary workspace path."""
    return str(tmp_path)

class TestFileReadTool:
    def test_read_single_file_success(self, workspace):
        file_path = Path(workspace) / "test.txt"
        file_path.write_text("Hello World", encoding="utf-8")
        
        tool = FileReadTool()
        result = tool.execute(workspace, {"path": "test.txt"})
        
        assert result["status"] == "success"
        assert "Hello World" in result["output"]

    def test_read_single_file_not_found(self, workspace):
        tool = FileReadTool()
        result = tool.execute(workspace, {"path": "nonexistent.txt"})
        
        assert result["status"] == "error"
        assert "File not found" in result["error"]

    def test_read_multiple_files_success(self, workspace):
        (Path(workspace) / "f1.txt").write_text("C1", encoding="utf-8")
        (Path(workspace) / "f2.txt").write_text("C2", encoding="utf-8")
        
        tool = FileReadTool()
        result = tool.execute(workspace, {"path": ["f1.txt", "f2.txt"]})
        
        assert result["status"] == "success"
        assert "\"success_count\": 2" in result["output"]

class TestFileWriteTool:
    def test_write_file_success(self, workspace):
        tool = FileWriteTool()
        result = tool.execute(workspace, {"path": "new.txt", "content": "New Content"})
        
        assert result["status"] == "success"
        assert (Path(workspace) / "new.txt").read_text(encoding="utf-8") == "New Content"

    def test_append_file_success(self, workspace):
        p = Path(workspace) / "log.txt"
        p.write_text("Line1\n", encoding="utf-8")
        
        tool = FileWriteTool()
        result = tool.execute(workspace, {"path": "log.txt", "content": "Line2", "mode": "append"})
        
        assert result["status"] == "success"
        assert p.read_text(encoding="utf-8") == "Line1\nLine2"

    def test_replace_lines_success(self, workspace):
        p = Path(workspace) / "code.py"
        p.write_text("lines = [\n    'one',\n    'two',\n    'three'\n]\n", encoding="utf-8")
        
        tool = FileWriteTool()
        # Replace lines 2-4 (0-indexed 1-3)
        # Original:
        # 1: lines = [
        # 2:     'one',
        # 3:     'two',
        # 4:     'three'
        # 5: ]
        
        result = tool.execute(workspace, {
            "path": "code.py", 
            "start_line": 2, 
            "end_line": 4, 
            "content": "    'updated'"
        })
        
        assert result["status"] == "success"
        expected = "lines = [\n    'updated'\n]\n"
        assert p.read_text(encoding="utf-8") == expected

class TestDirListTool:
    def test_list_dir_success(self, workspace):
        (Path(workspace) / "a.txt").touch()
        (Path(workspace) / "b_dir").mkdir()
        
        tool = DirListTool()
        result = tool.execute(workspace, {"path": "."})
        
        assert result["status"] == "success"
        assert "[file] a.txt" in result["output"]
        assert "[dir] b_dir" in result["output"]

    def test_list_recursive_success(self, workspace):
        (Path(workspace) / "parent").mkdir()
        (Path(workspace) / "parent/child.txt").touch()
        
        tool = DirListTool()
        result = tool.execute(workspace, {"path": ".", "recursive": True})
        
        assert result["status"] == "success"
        assert "[dir] parent" in result["output"]
        assert "  [file] child.txt" in result["output"]

class TestDirCreateTool:
    def test_create_dir_success(self, workspace):
        tool = DirCreateTool()
        result = tool.execute(workspace, {"path": "new_folder/sub_folder"})
        
        assert result["status"] == "success"
        assert (Path(workspace) / "new_folder/sub_folder").is_dir()

class TestFileMoveTool:
    def test_move_file_success(self, workspace):
        src = Path(workspace) / "src.txt"
        src.touch()
        (Path(workspace) / "dest").mkdir()
        
        tool = FileMoveTool()
        result = tool.execute(workspace, {"source": ["src.txt"], "destination": "dest/"})
        
        assert result["status"] == "success"
        assert not src.exists()
        assert (Path(workspace) / "dest/src.txt").exists()

    def test_copy_file_success(self, workspace):
        src = Path(workspace) / "src.txt"
        src.touch()
        (Path(workspace) / "dest").mkdir()
        
        tool = FileMoveTool()
        result = tool.execute(workspace, {"source": ["src.txt"], "destination": "dest/", "copy": True})
        
        assert result["status"] == "success"
        assert src.exists()
        assert (Path(workspace) / "dest/src.txt").exists()

class TestFileDeleteTool:
    def test_delete_file_success(self, workspace):
        f = Path(workspace) / "todel.txt"
        f.touch()
        
        tool = FileDeleteTool()
        result = tool.execute(workspace, {"path": "todel.txt"})
        
        assert result["status"] == "success"
        assert not f.exists()

    def test_delete_dir_success(self, workspace):
        d = Path(workspace) / "deldir"
        d.mkdir()
        (d / "f.txt").touch()
        
        tool = FileDeleteTool()
        result = tool.execute(workspace, {"path": "deldir"})
        
        assert result["status"] == "success"
        assert not d.exists()
