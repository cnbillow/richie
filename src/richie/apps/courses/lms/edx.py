"""
Backend to connect Open edX richie with an LMS
"""
import json
import logging

from edx_rest_api_client.client import OAuthAPIClient

from .base import BaseLMSBackend

logger = logging.getLogger(__name__)


class EdXLMSBackend(BaseLMSBackend):
    """LMS backend for Richie tested with Open EdX Hawthorn."""

    @property
    def api_client(self):
        """Instantiate and return an edx REST API client."""
        return OAuthAPIClient(
            self.configuration["BASE_URL"],
            self.configuration["OAUTH2_KEY"],
            self.configuration["OAUTH2_SECRET"],
        )

    def get_enrollment(self, user, url):
        """Get enrollment status for a user on a course run given its url."""

        response = self.api_client.request(
            "GET",
            "{base_url:s}/api/enrollment/v1/enrollment/{username:s},{course_id:s}".format(
                base_url=self.configuration["BASE_URL"],
                username=user.username,
                course_id=self.extract_course_id(url),
            ),
        )

        if response.ok:
            return json.loads(response.content)

        logger.error(response.content)
        return None

    def set_enrollment(self, user, url):
        """Set enrollment for a user with a course run given its url."""
        course_id = self.extract_course_id(url)
        payload = {
            "username": user.username,
            "course_details": {"course_id": course_id},
        }

        response = self.api_client.request(
            "POST",
            "{:s}/api/enrollment/v1/enrollment".format(self.configuration["BASE_URL"]),
            json=payload,
        )

        if response.ok:
            data = json.loads(response.content)
            if data["is_active"]:
                return True

        logger.error(response.content)
        return False
