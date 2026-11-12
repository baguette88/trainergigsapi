"""tools/sample_rows.py: the sample shows fresh rows only, leaves some platforms out, and says where to write."""
import datetime
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))
import sample_rows  # noqa: E402

TABLE = """| Pay | Role | Platform | Field | Posted |
|---|---|---|---|---|
| \\$350/hr | [Cardiologist](https://trainergigs.com/job-a?src=api) | Mercor | Medicine | 2026-11-10 |
| \\$300/hr | [Research Advisor](https://trainergigs.com/job-b?src=api) | Scale AI | Science & Research | 2026-05-13 |
| \\$160 to \\$180/hr | [Hematologist](https://trainergigs.com/job-c?src=api) | micro1 | Medicine | 2026-11-10 |
| \\$120/hr | [No date](https://trainergigs.com/job-d?src=api) | Turing | Law |  |

Counted on 2026-11-12. Data: [TrainerGigs](https://trainergigs.com/?src=api)
"""


class Trim(unittest.TestCase):
    def setUp(self):
        self.text, self.kept, self.dropped = sample_rows.trim(TABLE, datetime.date(2026, 11, 12))

    def test_only_fresh_rows_of_platforms_we_name_stay(self):
        self.assertEqual((self.kept, self.dropped), (1, 3))
        self.assertIn("Hematologist", self.text)
        for gone in ("Cardiologist", "Research Advisor", "No date", "Mercor"):
            self.assertNotIn(gone, self.text)

    def test_the_head_the_credit_and_the_contact_are_there(self):
        self.assertTrue(self.text.startswith("| Pay | Role | Platform | Field | Posted |\n|---|---|---|---|---|\n"))
        self.assertIn("Counted on 2026-11-12. Data: [TrainerGigs]", self.text)
        self.assertTrue(self.text.rstrip().endswith("hello@trainergigs.com"))

    def test_run_twice_is_the_same(self):
        again, kept, dropped = sample_rows.trim(self.text, datetime.date(2026, 11, 12))
        self.assertEqual((again, kept, dropped), (self.text, 1, 0))


if __name__ == "__main__":
    unittest.main()
