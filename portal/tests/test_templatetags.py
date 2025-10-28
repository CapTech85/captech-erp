# portal/tests/test_templatetags.py
from django.test import SimpleTestCase
from django.template import Context, Template

class MoneyFilterTest(SimpleTestCase):
    def test_money_filter(self):
        tpl = Template("{% load portal_extras %}{{ 12345.67|money }}")
        rendered = tpl.render(Context({}))
        self.assertIn("12 345,67", rendered)
