# portal/tests/test_compute_insights_and_fixtures.py
from django.apps import apps
from django.test import TestCase

from portal.services_insights import compute_insights

Company = apps.get_model("core", "Company")


class FixturesAndInsightsTest(TestCase):
    def setUp(self):
        from django.core.management import call_command

        call_command("create_sample_data")

    def test_compute_insights_runs(self):
        company = Company.objects.first()
        insights = compute_insights(company)
        self.assertIsInstance(insights, list)
