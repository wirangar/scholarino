from smartstudentbot.utils.db_utils import add_points_to_user
from smartstudentbot.utils.logger import logger

# Define points for various actions
ACTION_POINTS = {
    "complete_registration": 25,
    "ask_question": 1,
    "receive_answer": 2,
    "submit_feedback": 10,
}

async def award_points_for_action(user_id: int, action: str):
    """
    Awards points to a user for a specific action.

    Args:
        user_id: The ID of the user.
        action: The name of the action performed (e.g., 'complete_registration').
    """
    points = ACTION_POINTS.get(action)
    if points:
        logger.info(f"Awarding {points} points to user {user_id} for action: {action}")
        await add_points_to_user(user_id, points)
    else:
        logger.warning(f"Unknown gamification action: {action}")

# Badge logic can be added here in the future
# For example:
# async def award_badge(user_id: int, badge_name: str): ...
