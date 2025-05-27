"""SightEngine API integration for image quality assessment."""

import logging

import requests

logger = logging.getLogger(__name__)

SIGHTENGINE_API_URL = "https://api.sightengine.com/1.0/check.json"


def check_image_quality(image_path: str, api_user: str, api_secret: str) -> dict | None:
    """Check image quality using SightEngine API.

    Args:
        image_path: Path to the image file
        api_user: SightEngine API user
        api_secret: SightEngine API secret

    Returns:
        API response dict or None if error
    """
    try:
        # Prepare the request
        params = {
            "models": "quality",  # Only check quality (not AI detection)
            "api_user": api_user,
            "api_secret": api_secret,
        }

        # Send the image
        with open(image_path, "rb") as image_file:
            files = {"media": image_file}
            response = requests.post(SIGHTENGINE_API_URL, files=files, data=params, timeout=30)

        # Check response
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                return result
            else:
                logger.error(f"SightEngine API error: {result.get('error', 'Unknown error')}")
                return None
        else:
            logger.error(f"SightEngine HTTP error: {response.status_code}")
            if response.text:
                logger.error(f"Response: {response.text}")
            return None

    except Exception as e:
        logger.error(f"SightEngine request failed: {e}")
        return None
