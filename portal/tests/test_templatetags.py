# portal/tests/test_templatetags.py
from django.test import SimpleTestCase
from django.template import Template, Context

class MoneyFilterTest(SimpleTestCase):
    def test_money_filter_basic(self):
        tpl = Template("{% load portal_extras %}{{ 12345.67|money }}")
        rendered = tpl.render(Context({}))
        assert "12 345,67" in rendered

    def test_money_filter_none(self):
        tpl = Template("{% load portal_extras %}{{ none_value|money }}")
        rendered = tpl.render(Context({"none_value": None}))
        assert "0,00" in rendered
