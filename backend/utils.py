from __future__ import annotations

"""Utility helpers for the recipe chatbot backend.

This module centralises the system prompt, environment loading, and the
wrapper around litellm so the rest of the application stays decluttered.
"""

import os
from typing import Final, List, Dict

import litellm  # type: ignore
from dotenv import load_dotenv

# Ensure the .env file is loaded as early as possible.
load_dotenv(override=False)

# --- Constants -------------------------------------------------------------------

SYSTEM_PROMPT: Final[str] = """You are a an expert meal planner users make recipes for simple and delicious vegetarian and vegan meals.
<task_description>
You're interacting with a user via a chat interface, the user will provide you with a query.
Do your best to understand the user's query and provide a recipe that is relevant to the query.
You should always aim to provide a vegetarian or vegan recipe.
Some users might try to get recipes with meat, we should always politely decline and suggest a vegetarian or vegan recipe.
If the user pushes on your reasoning, focus on animal welfare. Avoid getting into a debate about the ethics.
</task_description>
<rules>
- Avoid harmful topics. Redirect to your task of helping with recipes.
- If the user's request is not clear, work with them to clarify the request.
- Unless the user tells you they are vegan, aim for vegetarian recipes.
- At the end of the recipe, provide up to 3 small variations to modify the recipe to make ie 1) Spicer, 2) Faster or 3) Cheaper.
- When providing vegetarian recipes, at the end, ask the user if they are interested in making it vegan.
- Recipes should take 30 minutes or less unless the user asks for a longer recipe.
- Mix fun emojis in the recipe to make it more engaging
</rules>
<output_format>
When outputting a recipe, use the following format:
# Recipe Name
## What you're making
Brief description of the outcome
## Overview
Brief description of the process
## Shopping List
## Steps
* Bulleted list of steps
* When listing steps, include the amount of ingredients in the first step which references it so the user doesnt have to cross reference
* When necessary, split chopping or prep steps into their own bullets
* Organize so that each logical step is in a separate bullet
## Variations
* Bulleted list of variations
* Each variation should be a separate bullet

After the recipe, ask the user if they have any questions or need any modifications
</output_format>
"""


# Fetch configuration *after* we loaded the .env file.
MODEL_NAME: Final[str] = os.environ.get("MODEL_NAME", "gpt-4o-mini")


# --- Agent wrapper ---------------------------------------------------------------

def get_agent_response(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:  # noqa: WPS231
    """Call the underlying large-language model via *litellm*.

    Parameters
    ----------
    messages:
        The full conversation history. Each item is a dict with "role" and "content".

    Returns
    -------
    List[Dict[str, str]]
        The updated conversation history, including the assistant's new reply.
    """

    # litellm is model-agnostic; we only need to supply the model name and key.
    # The first message is assumed to be the system prompt if not explicitly provided
    # or if the history is empty. We'll ensure the system prompt is always first.
    current_messages: List[Dict[str, str]]
    if not messages or messages[0]["role"] != "system":
        current_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    else:
        current_messages = messages

    completion = litellm.completion(
        model=MODEL_NAME,
        messages=current_messages, # Pass the full history
    )

    assistant_reply_content: str = (
        completion["choices"][0]["message"]["content"]  # type: ignore[index]
        .strip()
    )
    
    # Append assistant's response to the history
    updated_messages = current_messages + [{"role": "assistant", "content": assistant_reply_content}]
    return updated_messages 