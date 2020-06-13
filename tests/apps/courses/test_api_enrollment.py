"""
Tests for Enrollment API endpoints in the courses app.
"""
from unittest import mock

import arrow
from cms.test_utils.testcases import CMSTestCase

from richie.apps.core.factories import UserFactory
from richie.apps.courses.factories import CourseRunFactory


@mock.patch("richie.apps.courses.api.LMSHandler")
class EnrollmentApiTestCase(CMSTestCase):
    """Test requests on courses app API endpoints."""

    def test_enrollment_create_anonymous_user(self, LMSHandlerMock):
        """
        Anonymous users cannot enroll in any course and should receive a Forbidden response.
        """
        course_run = CourseRunFactory(
            start=arrow.utcnow().shift(days=-5).datetime,
            end=arrow.utcnow().shift(days=+90).datetime,
            enrollment_start=arrow.utcnow().shift(days=-35).datetime,
            enrollment_end=arrow.utcnow().shift(days=+10).datetime,
        )
        response = self.client.post(
            "/api/v1.0/enrollments/", data={"course_run_id": course_run.id}
        )
        self.assertEqual(response.status_code, 403)
        LMSHandlerMock.set_enrollment.assert_not_called()

    def test_enrollment_create_closed(self, LMSHandlerMock):
        """
        Attempting to enroll in a course that is not open for enrollment anymore results
        in an error.
        """
        user = UserFactory()
        course_run = CourseRunFactory(
            start=arrow.utcnow().shift(days=-35).datetime,
            end=arrow.utcnow().shift(days=+60).datetime,
            enrollment_start=arrow.utcnow().shift(days=-65).datetime,
            enrollment_end=arrow.utcnow().shift(days=-20).datetime,
        )

        self.client.force_login(user)
        response = self.client.post(
            "/api/v1.0/enrollments/", data={"course_run_id": course_run.id}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {"errors": ["Course run is not open for enrollments."]}
        )
        LMSHandlerMock.set_enrollment.assert_not_called()

    def test_enrollment_create(self, LMSHandlerMock):
        """
        Course is open for enrollment and user can join it. Enrollment is successful.
        """
        user = UserFactory()
        course_run = CourseRunFactory(
            start=arrow.utcnow().shift(days=-5).datetime,
            end=arrow.utcnow().shift(days=+90).datetime,
            enrollment_start=arrow.utcnow().shift(days=-35).datetime,
            enrollment_end=arrow.utcnow().shift(days=+10).datetime,
        )

        self.client.force_login(user)
        LMSHandlerMock.set_enrollment.return_value = True
        response = self.client.post(
            "/api/v1.0/enrollments/", data={"course_run_id": course_run.id}
        )

        self.assertEqual(response.status_code, 201)
        LMSHandlerMock.set_enrollment.assert_called_once_with(
            user, course_run.resource_link
        )

    def test_enrollment_create_failure(self, LMSHandlerMock):
        """
        What we do when the enrollment fails.
        """
        user = UserFactory()
        course_run = CourseRunFactory(
            start=arrow.utcnow().shift(days=-5).datetime,
            end=arrow.utcnow().shift(days=+90).datetime,
            enrollment_start=arrow.utcnow().shift(days=-35).datetime,
            enrollment_end=arrow.utcnow().shift(days=+10).datetime,
        )

        self.client.force_login(user)
        LMSHandlerMock.set_enrollment.return_value = False
        response = self.client.post(
            "/api/v1.0/enrollments/", data={"course_run_id": course_run.id}
        )

        self.assertEqual(response.status_code, 400)
        LMSHandlerMock.set_enrollment.assert_called_once_with(
            user, course_run.resource_link
        )

    def test_enrollment_list_anonymous_user(self, LMSHandlerMock):
        """
        Anonymous users cannot make requests to the LIST enrollments endpoint.
        """
        response = self.client.get("/api/v1.0/enrollments/")
        self.assertEqual(response.status_code, 403)
        LMSHandlerMock.get_enrollment.assert_not_called()

    def test_enrollment_list_enrollments(self, LMSHandlerMock):
        """
        A logged-in user can only see their own enrollment when they call the LIST
        enrollments endpoint for a course run.
        """
        course_run = CourseRunFactory()
        user = UserFactory()

        self.client.force_login(user)
        LMSHandlerMock.get_enrollment.return_value = {"some key": "some value"}
        response = self.client.get(
            f"/api/v1.0/enrollments/?course_run_id={course_run.id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"some key": "some value"}])
        LMSHandlerMock.get_enrollment.assert_called_once_with(
            user, course_run.resource_link
        )

    def test_enrollment_list_enrollments_course_run_does_not_exist(
        self, LMSHandlerMock
    ):
        """
        If the course run passed in parameters does not exist, we just return an empty list for
        enrollments.
        """
        user = UserFactory()

        self.client.force_login(user)
        response = self.client.get("/api/v1.0/enrollments/?course_run_id=42")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        LMSHandlerMock.get_enrollment.assert_not_called()

    def test_enrollment_list_enrollments_missing_course_run_param(self, LMSHandlerMock):
        """
        The `course_run_id` param is mandatory. When it is missing, return an error code with an
        appropriate message.
        """
        user = UserFactory()

        self.client.force_login(user)
        response = self.client.get("/api/v1.0/enrollments/")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {"errors": ['The "course_run_id" parameter is mandatory.']}
        )
        LMSHandlerMock.get_enrollment.assert_not_called()
