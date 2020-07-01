"""Test suite for the EdX LMS backend."""
import json
import random

from django.test import TestCase
from django.test.utils import override_settings

import responses
from edx_django_utils.cache import TieredCache

from richie.apps.core.factories import UserFactory
from richie.apps.courses.lms import LMSHandler


@override_settings(
    LMS_BACKENDS=[
        {
            "BACKEND": "richie.apps.courses.lms.edx.EdXLMSBackend",
            "COURSE_REGEX": r"^.*/courses/(?P<course_id>.*)/course/?$",
            "BASE_URL": "http://edx:8073",
            "OAUTH2_KEY": "edx-id",
            "OAUTH2_SECRET": "fakesecret",
        }
    ]
)
class EdXLMSBackendTestCase(TestCase):
    """Test suite for the EdX LMS backend."""

    @staticmethod
    def _add_access_token_response():
        """Not a test. Shared utility method to add a mock for the access token request."""
        # Delete access token cache for independance between tests
        TieredCache.delete_all_tiers(
            "edx_rest_api_client.access_token.jwt.client_credentials."
            "edx-id.http://edx:8073/oauth2/access_token"
        )

        # Configure requests mocks using https://github.com/getsentry/responses
        responses.add(
            responses.POST,
            "http://edx:8073/oauth2/access_token",
            status=200,
            json={
                "access_token": "FakeToken",
                "token_type": "JWT",
                "expires_in": 36000,
                "scope": "read write profile email",
            },
        )

    @responses.activate
    def test_lms_edx_set_enrollment_active(self):
        """Setting an enrollment with success."""
        self._add_access_token_response()
        user = UserFactory(username="teacher")

        responses.add(
            responses.POST,
            "http://edx:8073/api/enrollment/v1/enrollment",
            status=200,
            json={"is_active": True},
        )

        is_enrolled = LMSHandler.set_enrollment(
            user, "http://edx:8073/courses/course-v1:edX+DemoX+Demo_Course/course/"
        )

        self.assertEqual(len(responses.calls), 2)

        # First call to get access token
        self.assertEqual(
            responses.calls[0].request.url, "http://edx:8073/oauth2/access_token"
        )
        self.assertEqual(
            responses.calls[0].request.body,
            (
                "grant_type=client_credentials&client_id=edx-id&"
                "client_secret=fakesecret&token_type=jwt"
            ),
        )

        # Second call to set enrollment
        self.assertEqual(
            responses.calls[1].request.url,
            "http://edx:8073/api/enrollment/v1/enrollment",
        )
        self.assertEqual(
            responses.calls[1].request.headers["Authorization"], "JWT FakeToken"
        )
        self.assertEqual(
            json.loads(responses.calls[1].request.body),
            {
                "username": user.username,
                "course_details": {"course_id": "course-v1:edX+DemoX+Demo_Course"},
            },
        )

        self.assertTrue(is_enrolled)

    @responses.activate
    def test_lms_edx_set_enrollment_inactive(self):
        """The enrollment attempt should return False if the server returns an inactive status."""
        self._add_access_token_response()
        user = UserFactory(username="teacher")

        responses.add(
            responses.POST,
            "http://edx:8073/api/enrollment/v1/enrollment",
            status=200,
            json={"is_active": False},
        )
        is_enrolled = LMSHandler.set_enrollment(
            user, "http://edx:8073/courses/course-v1:edX+DemoX+Demo_Course/course/"
        )

        self.assertEqual(len(responses.calls), 2)
        self.assertFalse(is_enrolled)

    @responses.activate
    def test_lms_edx_set_enrollment_error(self):
        """The enrollment attempt should return False if the server returns an error."""
        self._add_access_token_response()
        user = UserFactory(username="teacher")

        responses.add(
            responses.POST, "http://edx:8073/api/enrollment/v1/enrollment", status=404
        )
        is_enrolled = LMSHandler.set_enrollment(
            user, "http://edx:8073/courses/course-v1:edX+DemoX+Demo_Course/course/"
        )

        self.assertEqual(len(responses.calls), 2)
        self.assertFalse(is_enrolled)

    @responses.activate
    def test_lms_edx_get_enrollment_success(self):
        """Getting an enrollment with success."""
        self._add_access_token_response()

        expected_object = {"is_active": random.choice([True, False])}

        responses.add(
            responses.GET,
            (
                "http://edx:8073/api/enrollment/v1/enrollment/"
                "teacher,course-v1:edX+DemoX+Demo_Course"
            ),
            status=200,
            json=expected_object,
        )

        user = UserFactory(username="teacher")
        enrollment = LMSHandler.get_enrollment(
            user, "http://edx:8073/courses/course-v1:edX+DemoX+Demo_Course/course/"
        )

        self.assertEqual(len(responses.calls), 2)

        # First call to get access token
        self.assertEqual(
            responses.calls[0].request.url, "http://edx:8073/oauth2/access_token"
        )
        self.assertEqual(
            responses.calls[0].request.body,
            (
                "grant_type=client_credentials&client_id=edx-id&"
                "client_secret=fakesecret&token_type=jwt"
            ),
        )

        # Second call to get enrollment
        self.assertEqual(
            responses.calls[1].request.url,
            (
                "http://edx:8073/api/enrollment/v1/enrollment/"
                "teacher,course-v1:edX+DemoX+Demo_Course"
            ),
        )
        self.assertEqual(
            responses.calls[1].request.headers["Authorization"], "JWT FakeToken"
        )
        self.assertEqual(responses.calls[1].request.body, None)

        self.assertEqual(enrollment, expected_object)

    @responses.activate
    def test_lms_edx_get_enrollment_error(self):
        """Getting an enrollment should return None if the server returns an error."""
        self._add_access_token_response()

        responses.add(
            responses.GET,
            (
                "http://edx:8073/api/enrollment/v1/enrollment/"
                "teacher,course-v1:edX+DemoX+Demo_Course"
            ),
            status=404,
        )

        user = UserFactory(username="teacher")
        enrollment = LMSHandler.get_enrollment(
            user, "http://edx:8073/courses/course-v1:edX+DemoX+Demo_Course/course/"
        )

        self.assertEqual(len(responses.calls), 2)
        self.assertIsNone(enrollment)
