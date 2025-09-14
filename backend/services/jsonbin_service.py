import os
import requests
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class JsonBinService:
    """Service for interacting with JSONBin.io to manage personifications"""

    def __init__(self):
        self.api_key = os.getenv("JSONBIN_API_KEY")
        self.bin_id = os.getenv("JSONBIN_BIN_ID")

        if not self.api_key or not self.bin_id:
            logger.error(
                "JSONBin configuration missing. Please set JSONBIN_API_KEY and JSONBIN_BIN_ID environment variables."
            )
            raise ValueError("JSONBin configuration missing")

    def get_personifications_data(self) -> Dict:
        """Fetch personifications data from JSONBin"""
        try:
            url = f"https://api.jsonbin.io/v3/b/{self.bin_id}"
            headers = {"X-Master-Key": self.api_key, "X-Bin-Meta": "false"}

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Successfully fetched personifications from JSONBin")
                return data
            else:
                logger.error(
                    f"❌ JSONBin API error: {response.status_code} {response.text}"
                )
                return {"choice": None, "personifications": []}

        except Exception as e:
            logger.error(f"❌ Error fetching personifications: {e}")
            return {"choice": None, "personifications": []}

    def get_active_personification(self) -> Optional[Dict]:
        """Get the currently active personification"""
        try:
            data = self.get_personifications_data()
            active_choice = data.get("choice")
            personifications = data.get("personifications", [])

            if not active_choice:
                logger.info("No active personification set")
                return None

            # Find the active personification by ID
            for personification in personifications:
                if personification.get("id") == active_choice:
                    logger.info(
                        f"✅ Found active personification: {personification.get('name', 'Unknown')}"
                    )
                    return personification

            logger.warning(
                f"⚠️ Active personification ID '{active_choice}' not found in personifications list"
            )
            return None

        except Exception as e:
            logger.error(f"❌ Error getting active personification: {e}")
            return None

    def update_active_choice(self, personification_id: Optional[str]) -> bool:
        """Update the active personification choice"""
        try:
            # First get current data
            current_data = self.get_personifications_data()

            # Update the choice
            updated_data = {**current_data, "choice": personification_id}

            # Send update to JSONBin
            url = f"https://api.jsonbin.io/v3/b/{self.bin_id}"
            headers = {"Content-Type": "application/json", "X-Master-Key": self.api_key}

            response = requests.put(url, json=updated_data, headers=headers, timeout=10)

            if response.status_code == 200:
                logger.info(
                    f"✅ Successfully updated active choice to: {personification_id}"
                )
                return True
            else:
                logger.error(
                    f"❌ Failed to update active choice: {response.status_code} {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Error updating active choice: {e}")
            return False


# Global service instance
jsonbin_service = JsonBinService()
