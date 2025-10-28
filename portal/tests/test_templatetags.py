# portal/tests/test_templatetags.py
from django.template import Context, Template
from django.test import SimpleTestCase


class MoneyFilterTest(SimpleTestCase):
    def test_money_filter(self):
        tpl = Template("{% load portal_extras %}{{ 12345.67|money }}")
        rendered = tpl.render(Context({}))
        self.assertIn("12 345,67", rendered)
