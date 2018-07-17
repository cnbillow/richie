"""
Plugin tests
"""
from django.test import TestCase
from django.test.client import RequestFactory

from cms.api import add_plugin
from cms.models import Placeholder
from cms.plugin_rendering import ContentRenderer

from richie.plugins.simple_text_ckeditor.cms_plugins import CKEditorPlugin
from richie.plugins.simple_text_ckeditor.factories import SimpleTextFactory


class CKEditorPluginTests(TestCase):
    """Plugin tests case"""

    def test_simpletext_context_and_html(self):
        """
        Instanciating this plugin with an instance should populate the context
        and render in the template.
        """
        placeholder = Placeholder.objects.create(slot="test")

        # Create random values for parameters with a factory
        simpletext = SimpleTextFactory()

        model_instance = add_plugin(
            placeholder, CKEditorPlugin, "en", body=simpletext.body
        )
        plugin_instance = model_instance.get_plugin_class_instance()
        context = plugin_instance.render({}, model_instance, None)

        # Check if "instance" is in context
        self.assertIn("instance", context)

        # Check if parameters, generated by the factory, are correctly set in "instance" of context
        self.assertEqual(context["instance"].body, simpletext.body)

        # Get generated html for simpletext body
        renderer = ContentRenderer(request=RequestFactory())
        html = renderer.render_plugin(model_instance, {})

        # Check rendered body is correct after save and sanitize
        self.assertInHTML(simpletext.body, html)