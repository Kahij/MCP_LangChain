from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPContextManager:
    def __init__(self):
        self.context = []
        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message_count": 0
        }

    def add_context(self, user_input, model_response):
        """Add a conversation exchange to the context with timestamp."""
        timestamp = datetime.now().isoformat()
        
        entry = {
            "timestamp": timestamp,
            "user": user_input,
            "model": model_response
        }
        
        self.context.append(entry)
        self.metadata["updated_at"] = timestamp
        self.metadata["message_count"] += 1
        
        logger.debug(f"Added context entry. Total entries: {len(self.context)}")

    def clear_context(self):
        """Clear the conversation context but preserve metadata."""
        self.context = []
        self.metadata["updated_at"] = datetime.now().isoformat()
        self.metadata["message_count"] = 0
        logger.info("Context cleared")

    def get_context(self):
        """Return the current context."""
        return self.context

    def get_last_n_exchanges(self, n=5):
        """Get the last n conversation exchanges."""
        return self.context[-n:] if n < len(self.context) else self.context

    def show_context(self):
        """Print the current context to console."""
        if not self.context:
            print("Context is empty.")
            return
            
        print(f"\n=== Context ({len(self.context)} entries) ===")
        for i, entry in enumerate(self.context):
            print(f"\n--- Exchange {i+1} ({entry['timestamp']}) ---")
            print(f"User: {entry['user']}")
            print(f"Model: {entry['model']}")
        print("\n=== End of Context ===")

    def save_to_file(self, filename="context_history.json"):
        """Save the context and metadata to a JSON file."""
        try:
            data = {
                "metadata": self.metadata,
                "context": self.context
            }
            
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Context saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving context to file: {str(e)}")
            return False

    def load_from_file(self, filename="context_history.json"):
        """Load context and metadata from a JSON file."""
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                
            self.metadata = data.get("metadata", self.metadata)
            self.context = data.get("context", [])
            
            # Update timestamp
            self.metadata["updated_at"] = datetime.now().isoformat()
            
            logger.info(f"Context loaded from {filename}: {len(self.context)} entries")
            return True
        except FileNotFoundError:
            logger.warning(f"Context file not found: {filename}")
            return False
        except Exception as e:
            logger.error(f"Error loading context from file: {str(e)}")
            return False

    def summarize_context(self):
        """Return a summary of the context."""
        return {
            "metadata": self.metadata,
            "total_exchanges": len(self.context),
            "first_timestamp": self.context[0]["timestamp"] if self.context else None,
            "last_timestamp": self.context[-1]["timestamp"] if self.context else None
        }