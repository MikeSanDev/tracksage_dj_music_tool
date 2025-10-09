
"""
AI Rename Suggester
-------------------
This module acts as a *helper* for the rename tool.

When a track has missing or unreliable tags, this script asks an AI model
to infer the most likely "Artist - Title.mp3" name based on the filename
and any tag fragments that exist.

Example use:
    from tools.ai_suggester import suggest_name_with_ai
    new_name = suggest_name_with_ai("Daft_Punk-Face2Face.mp3")
"""

import os
from typing import Optional
from openai import OpenAI  # ← we'll use OpenAI GPT-4o-mini