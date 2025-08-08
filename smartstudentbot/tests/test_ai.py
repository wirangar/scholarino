import pytest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from smartstudentbot.ai import question_answering

@pytest.mark.asyncio
async def test_get_simple_answer_exact_match():
    """
    Tests that get_simple_answer finds a question with an exact match.
    """
    question = "What is a scholarship?"
    answer = await question_answering.get_simple_answer(question)
    assert answer is not None
    assert "financial aid" in answer

@pytest.mark.asyncio
async def test_get_simple_answer_no_match():
    """
    Tests that get_simple_answer returns None for a question with no exact match.
    """
    question = "Where is the cafeteria?"
    answer = await question_answering.get_simple_answer(question)
    assert answer is None

@pytest.mark.asyncio
async def test_get_semantic_answer_similar_match():
    """
    Tests that get_semantic_answer finds a semantically similar question.
    """
    # This question is similar to "How can I get a scholarship?"
    question = "How do I apply for financial aid?"
    answer = await question_answering.get_semantic_answer(question)
    assert answer is not None
    assert "DSU office" in answer

@pytest.mark.asyncio
async def test_get_semantic_answer_dissimilar_match():
    """
    Tests that get_semantic_answer returns None for a dissimilar question.
    """
    question = "What is the weather like today?"
    answer = await question_answering.get_semantic_answer(question)
    assert answer is None

@pytest.mark.asyncio
async def test_get_answer_orchestrator():
    """
    Tests the main get_answer function to ensure it prioritizes simple search.
    """
    # 1. Test exact match (should be handled by get_simple_answer)
    question_exact = "What is a scholarship?"
    answer_exact = await question_answering.get_answer(question_exact)
    assert "financial aid" in answer_exact

    # 2. Test semantic match (should be handled by get_semantic_answer)
    question_semantic = "How do I get money for school?"
    answer_semantic = await question_answering.get_answer(question_semantic)
    assert "DSU office" in answer_semantic

    # 3. Test no match
    question_none = "What's the best pizza place in town?"
    answer_none = await question_answering.get_answer(question_none)
    assert answer_none is None
