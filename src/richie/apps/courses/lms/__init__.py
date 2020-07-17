"""LMS handler to select and return the right LMS backend for each url."""
import re

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


class LMSHandler:
    """Class to handle LMS backends.

    Actions on a particular course are automatically routed to the LMS handling this course
    via the `SELECTOR_REGEX` configured for each LMS.
    """

    @staticmethod
    def select_lms(url):
        """
        Select and return the first LMS backend matching the url passed in argument.

        Default to None if no LMS is found to enable use-cases where we need to detect whether
        a course run has a matching LMS or not. Callers can determine if not finding an LMS
        backend is an exception or not.
        """

        for lms_configuration in settings.LMS_BACKENDS:
            if re.match(lms_configuration.get("SELECTOR_REGEX", r".*"), url):
                return import_string(lms_configuration["BACKEND"])(lms_configuration)

        return None

    @classmethod
    def get_enrollment(cls, user, url):
        """
        Get enrollment statuc for a user on a course run given its url. This method is a wrapper
        that routes the request to the LMS linked to this LMS.
        """
        lms = cls.select_lms(url)

        try:
            return lms.get_enrollment(user, url)
        except AttributeError:
            raise ImproperlyConfigured()

    @classmethod
    def set_enrollment(cls, user, url):
        """
        Set enrollment for a user with a course run given its url. This method is a wrapper
        that routes the request to the LMS linked to this LMS.
        """
        lms = cls.select_lms(url)

        try:
            return lms.set_enrollment(user, url)
        except AttributeError:
            raise ImproperlyConfigured()
