import pytest
from unittest.mock import patch, AsyncMock
from src.scripts.run_with_dependencies import ensure_neo4j_container, main

class TestRunWithDependencies:

    @patch("src.scripts.run_with_dependencies.subprocess.run")
    def test_ensure_neo4j_container_success(self, mock_subprocess_run):
        mock_subprocess_run.return_value.returncode = 0
        try:
            ensure_neo4j_container()
        except Exception as e:
            pytest.fail(f"ensure_neo4j_container raised an unexpected exception: {e}")
        
        assert mock_subprocess_run.called

    @pytest.mark.asyncio
    @patch("src.scripts.run_with_dependencies.ensure_neo4j_container")
    @patch("src.scripts.run_with_dependencies.main", new_callable=AsyncMock)
    async def test_main_execution(self, mock_main_coro, mock_ensure_container):
        # If main calls other async functions, we test the script's entrypoint wrapper
        await main()
        mock_ensure_container.assert_called_once()
