"""
Typing test manager for handling monkeytype functionality.
"""

import random
import collections
from datetime import datetime
from typing import Dict, List, Any

class TypingManager:
    def __init__(self):
        # Store user_id: {"words": [], "start_time": datetime, "message_id": int, "channel_id": int}
        self.active_typing_tests: Dict[int, Dict[str, Any]] = {}
        
        # Store challenge_id: {"challenger": user_id, "challenged": user_id, "word_count": int, "words": [], "results": {}}
        self.typing_challenges: Dict[str, Dict[str, Any]] = {}
        
        # Store challenged_user_id: [list of challenge_ids]
        self.pending_challenges: Dict[int, List[str]] = {}
        
        # Common words for typing tests
        self.common_words = [
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "I", "it", "for", "not", "on", "with", "he", "as", 
            "you", "do", "at", "this", "but", "his", "by", "from", "they", "we", "say", "her", "she", "or", "an", "will", 
            "my", "one", "all", "would", "there", "their", "what", "so", "up", "out", "if", "about", "who", "get", "which", 
            "go", "me", "when", "make", "can", "like", "time", "no", "just", "him", "know", "take", "people", "into", "year", 
            "your", "good", "some", "could", "them", "see", "other", "than", "then", "now", "look", "only", "come", "its", 
            "over", "think", "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", "way", "even", 
            "new", "want", "because", "any", "these", "give", "day", "most", "us", "is", "was", "were", "are", "has", "had", 
            "been", "being", "am", "did", "does", "doing", "done", "should", "must", "might", "may", "shall", "can", "could", 
            "would", "should", "ought", "need", "dare", "used", "going", "let", "help", "keep", "try", "start", "stop", 
            "begin", "end", "continue", "finish", "complete", "succeed", "fail", "win", "lose", "find", "search", "seek", 
            "try", "attempt", "avoid", "achieve", "accomplish", "reach", "attain", "obtain", "acquire", "get", "gain", 
            "earn", "receive", "accept", "reject", "refuse", "deny", "admit", "acknowledge", "recognize", "identify", 
            "understand", "comprehend", "grasp", "know", "learn", "study", "teach", "instruct", "educate", "train", 
            "develop", "improve", "enhance", "increase", "decrease", "reduce", "lower", "raise", "lift", "elevate", 
            "climb", "ascend", "descend", "fall", "drop", "sink", "rise", "grow", "expand", "shrink", "contract", 
            "condense", "compress", "squeeze", "stretch", "extend", "spread", "distribute", "gather", "collect", 
            "accumulate", "amass", "assemble", "build", "construct", "create", "design", "develop", "invent", 
            "discover", "explore", "investigate", "research", "analyze", "examine", "inspect", "observe", "watch", 
            "monitor", "track", "follow", "lead", "guide", "direct", "manage", "control", "regulate", "govern", 
            "rule", "dominate", "influence", "affect", "impact", "change", "alter", "modify", "transform"
        ]
        
    def generate_words(self, count: int) -> List[str]:
        """Generate a random list of words for typing test."""
        return random.sample(self.common_words, min(count, len(self.common_words)))
        
    def start_typing_test(self, user_id: int, channel_id: int, word_count: int = 25, challenge_id: str = None) -> List[str]:
        """Start a typing test for a user."""
        words = self.generate_words(word_count)
        
        test_info = {
            "words": words,
            "start_time": datetime.now(),
            "channel_id": channel_id
        }
        
        if challenge_id:
            test_info["challenge_id"] = challenge_id
            
        self.active_typing_tests[user_id] = test_info
        return words
        
    def calculate_results(self, user_id: int, typed_text: str) -> Dict[str, Any]:
        """Calculate typing test results."""
        if user_id not in self.active_typing_tests:
            return None
            
        test_info = self.active_typing_tests[user_id]
        
        # Calculate time elapsed
        end_time = datetime.now()
        elapsed_seconds = (end_time - test_info["start_time"]).total_seconds()
        
        # Get the original words and the typed words
        original_words = test_info["words"]
        typed_words = typed_text.split()
        
        # Calculate accuracy
        correct_chars = 0
        total_chars = sum(len(word) for word in original_words)
        original_text = " ".join(original_words)
        
        # Compare character by character
        for i in range(min(len(original_text), len(typed_text))):
            if original_text[i] == typed_text[i]:
                correct_chars += 1
        
        # Calculate accuracy percentage - ensure it doesn't exceed 100%
        accuracy = min(100, (correct_chars / total_chars) * 100) if total_chars > 0 else 0
        
        # Calculate words per minute (WPM)
        # Standard: 5 characters = 1 word
        standard_word_length = 5
        characters_per_minute = (correct_chars / elapsed_seconds) * 60
        wpm = characters_per_minute / standard_word_length
        
        return {
            "wpm": wpm,
            "accuracy": accuracy,
            "time": elapsed_seconds,
            "correct_chars": correct_chars,
            "total_chars": total_chars,
            "challenge_id": test_info.get("challenge_id")
        }
        
    def finish_typing_test(self, user_id: int) -> None:
        """Remove a user from active typing tests."""
        if user_id in self.active_typing_tests:
            del self.active_typing_tests[user_id]
            
    def is_user_typing(self, user_id: int) -> bool:
        """Check if user has an active typing test."""
        return user_id in self.active_typing_tests
        
    def create_challenge(self, challenger_id: int, challenged_id: int, word_count: int) -> str:
        """Create a typing challenge between two users."""
        import uuid
        challenge_id = str(uuid.uuid4())
        
        words = self.generate_words(word_count)
        
        self.typing_challenges[challenge_id] = {
            "challenger": challenger_id,
            "challenged": challenged_id,
            "word_count": word_count,
            "words": words,
            "results": {}
        }
        
        # Add to pending challenges for the challenged user
        if challenged_id not in self.pending_challenges:
            self.pending_challenges[challenged_id] = []
        self.pending_challenges[challenged_id].append(challenge_id)
        
        return challenge_id
        
    def accept_challenge(self, challenge_id: str, user_id: int) -> bool:
        """Accept a typing challenge."""
        if challenge_id not in self.typing_challenges:
            return False
            
        challenge = self.typing_challenges[challenge_id]
        if challenge["challenged"] != user_id:
            return False
            
        # Remove from pending challenges
        if user_id in self.pending_challenges:
            self.pending_challenges[user_id] = [
                cid for cid in self.pending_challenges[user_id] if cid != challenge_id
            ]
            
        return True
        
    def get_challenge(self, challenge_id: str) -> Dict[str, Any]:
        """Get challenge information."""
        return self.typing_challenges.get(challenge_id)
        
    def add_challenge_result(self, challenge_id: str, user_id: int, result: Dict[str, Any]) -> bool:
        """Add a result to a challenge."""
        if challenge_id not in self.typing_challenges:
            return False
            
        self.typing_challenges[challenge_id]["results"][user_id] = result
        return True
        
    def is_challenge_complete(self, challenge_id: str) -> bool:
        """Check if both users have completed the challenge."""
        if challenge_id not in self.typing_challenges:
            return False
            
        challenge = self.typing_challenges[challenge_id]
        return len(challenge["results"]) == 2
        
    def get_challenge_results(self, challenge_id: str) -> Dict[str, Any]:
        """Get the results comparison for a challenge."""
        if challenge_id not in self.typing_challenges:
            return None
            
        challenge = self.typing_challenges[challenge_id]
        if len(challenge["results"]) != 2:
            return None
            
        challenger_result = challenge["results"][challenge["challenger"]]
        challenged_result = challenge["results"][challenge["challenged"]]
        
        # Determine winner
        if challenger_result["wpm"] > challenged_result["wpm"]:
            winner_id = challenge["challenger"]
            loser_id = challenge["challenged"]
            winner_result = challenger_result
            loser_result = challenged_result
        else:
            winner_id = challenge["challenged"]
            loser_id = challenge["challenger"]
            winner_result = challenged_result
            loser_result = challenger_result
            
        return {
            "winner_id": winner_id,
            "loser_id": loser_id,
            "winner_result": winner_result,
            "loser_result": loser_result,
            "wpm_diff": abs(challenger_result["wpm"] - challenged_result["wpm"]),
            "accuracy_diff": abs(challenger_result["accuracy"] - challenged_result["accuracy"]),
            "word_count": challenge["word_count"]
        }
        
    def remove_challenge(self, challenge_id: str) -> None:
        """Remove a challenge."""
        if challenge_id in self.typing_challenges:
            del self.typing_challenges[challenge_id]