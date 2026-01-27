import pytest

from backend.services.translate_llm import translate_blocks_async

@pytest.mark.asyncio
async def test_translate_blocks_async_basic():
    """Test basic async translation with mock mode."""
    # Use unique strings and disable TM to avoid interference
    blocks = [
        {"source_text": "RandomAsyncBlock1", "slide_index": 1},
        {"source_text": "RandomAsyncBlock2", "slide_index": 2},
    ]

    result = await translate_blocks_async(
        blocks, target_language="zh-TW", provider="mock", use_tm=False
    )

    assert "blocks" in result
    assert len(result["blocks"]) == 2
    assert result["blocks"][0]["translated_text"] == "RandomAsyncBlock1"


@pytest.mark.asyncio
async def test_translate_blocks_async_progress():
    """Test that on_progress callback is called."""
    blocks = [
        {"source_text": "ProgTest1", "slide_index": 1},
        {"source_text": "ProgTest2", "slide_index": 1},
        {"source_text": "ProgTest3", "slide_index": 2},
    ]

    progress_calls = []

    async def on_progress(data):
        progress_calls.append(data)

    param_overrides = {"chunk_size": 1, "single_request": False}

    await translate_blocks_async(
        blocks,
        target_language="zh-TW",
        provider="mock",
        on_progress=on_progress,
        param_overrides=param_overrides,
        use_tm=False,
    )

    # Expected exactly 3 calls for 3 blocks with chunk_size=1
    assert len(progress_calls) == 3
    for call in progress_calls:
        assert "completed_indices" in call
        assert "total_pending" in call


@pytest.mark.asyncio
async def test_translate_blocks_async_parallel():
    """Test that parallel translation works."""
    blocks = [{"source_text": f"ParallelTest{i}", "slide_index": i} for i in range(5)]

    result = await translate_blocks_async(
        blocks,
        target_language="zh-TW",
        provider="mock",
        param_overrides={"chunk_size": 1, "single_request": False},
        use_tm=False,
    )

    assert len(result["blocks"]) == 5
    for i, block in enumerate(result["blocks"]):
        assert block["translated_text"] == f"ParallelTest{i}"
