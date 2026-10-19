"""Guard against publishing incomplete or fabricated activity data."""
from datetime import date, timedelta
import sys
from pathlib import Path
import unittest
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from update_profile import CalendarParser, THEMES, activity, intro


def fixture():
    parts = ['<h2 id="js-contribution-activity-description">1,200 contributions in the last year</h2>']
    for i in range(366):
        day = date(2025, 10, 19)+timedelta(days=i)
        count, level = ("1,200", 4) if i == 365 else ("No", 0)
        cell_id = f"contribution-day-{i}"
        parts += [f'<td id="{cell_id}" data-date="{day}" data-level="{level}"></td>',
                  f'<tool-tip for="{cell_id}">{count} contributions on October 19th.</tool-tip>']
    return "".join(parts)


def parse(html):
    p = CalendarParser()
    p.feed(html)
    return p.calendar()


class CalendarTests(unittest.TestCase):
    def test_real_counts_and_full_year(self):
        data = parse(fixture())
        self.assertEqual(data["total"], 1200)
        self.assertEqual(data["daily_total"], 1200)
        self.assertEqual(len(data["days"]), 366)
        self.assertEqual(data["days"][-1]["count"], 1200)

    def test_rejects_partial_or_error_page(self):
        for html in ["<h1>Rate limited</h1>", fixture().split('<td id="contribution-day-50"')[0]]:
            with self.assertRaises(ValueError):
                parse(html)

    def test_rejects_missing_count_instead_of_assuming_zero(self):
        with self.assertRaisesRegex(ValueError, "count"):
            parse(fixture().replace("No contributions on October 19th.", "Unknown", 1))

    def test_rejects_calendar_gaps(self):
        with self.assertRaisesRegex(ValueError, "duplicated or incomplete"):
            parse(fixture().replace('data-date="2025-10-20"', 'data-date="2025-10-19"'))

    def test_rejects_inconsistent_intensity(self):
        with self.assertRaisesRegex(ValueError, "intensity"):
            parse(fixture().replace('data-level="4"', 'data-level="0"'))

    def test_all_render_variants_have_valid_xml_and_no_external_resources(self):
        for palette in THEMES.values():
            for mobile in [False, True]:
                for svg in [intro(palette, mobile), activity(parse(fixture()), palette, mobile)]:
                    ElementTree.fromstring(svg)
                    self.assertNotIn("<script", svg)
                    self.assertNotIn("href=", svg)
                    self.assertIn("prefers-reduced-motion", svg)
                    self.assertIn("infinite", svg)
                    self.assertNotIn(".reveal{", svg)
                    self.assertIn('class="cursor"', svg)


if __name__ == "__main__":
    unittest.main()
