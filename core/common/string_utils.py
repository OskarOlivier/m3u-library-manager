# core/common/string_utils.py

import os
import re
import logging
from typing import Optional

from Levenshtein import distance as levenshtein_distance
import numpy as np

def clean_for_matching(s: str) -> str:
    """
    Remove all special characters for pure string matching.
    Maintains only alphanumeric characters and spaces.
    """
    # Convert to lowercase and remove all non-alphanumeric chars except spaces
    cleaned = re.sub(r'[^a-z0-9\s]', '', s.lower())
    # Normalize whitespace
    return ' '.join(cleaned.split())

def clean_for_probability(s: str) -> str:
    """
    Remove only invalid Windows filename characters.
    Keeps: letters, numbers, spaces, hyphens, underscores, periods, parentheses
    """
    # Windows invalid: < > : " / \ | ? *
    cleaned = re.sub(r'[<>:"/\\|?*]', '', s.lower())
    # Normalize whitespace
    return ' '.join(cleaned.split())

def estimate_string_similarity(search: str, target: str) -> float:           
    """
    Estimate similarity between search string and target string.
    Gives less weight to differences involving special characters.
    
    Args:
        search: Search string (from window title)
        target: Target string (from filename)
        
    Returns:
        float: Similarity score between 0 and 1
    """
    search = search.lower()
    target = target.lower()

    # Define weights: Numbers = 1, Alphabetic = 0.5, Special characters = 0.05
    def char_weight(c: str) -> float:
        if c.isdigit():
            return 1.0  # Numbers
        elif c.isalpha():
            return 0.9  # Alphabetic
        else:
            return 0.05  # Special characters
            
    # Initialize a matrix for Levenshtein distance with weighted costs
    len_search = len(search)
    len_target = len(target)
    dp = np.zeros((len_search + 1, len_target + 1))

    # Fill the matrix
    for i in range(len_search + 1):
        for j in range(len_target + 1):
            if i == 0:
                dp[i][j] = sum(char_weight(target[k]) for k in range(j))
            elif j == 0:
                dp[i][j] = sum(char_weight(search[k]) for k in range(i))
            else:
                cost = 0 if search[i - 1] == target[j - 1] else max(char_weight(search[i - 1]), char_weight(target[j - 1]))
                dp[i][j] = min(
                    dp[i - 1][j] + char_weight(search[i - 1]),  # Deletion
                    dp[i][j - 1] + char_weight(target[j - 1]),  # Insertion
                    dp[i - 1][j - 1] + cost  # Substitution
                )

    # Distance is the last cell in the matrix
    dist = dp[len_search][len_target]
    max_len = max(len_search, len_target)
    if max_len == 0:  # Handle edge case of empty strings
        return 1.0

    # Convert distance to similarity score
    score = 1.0 - (dist / max_len)
    return max(0.0, min(1.0, score))