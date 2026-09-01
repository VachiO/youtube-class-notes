import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from video_identity import title_class_date, validate_title_identity


class VideoIdentityTest(unittest.TestCase):
    def test_matching_title(self):
        validate_title_identity("POL 2129 วันที่ 18/8/69", "POL2129", "2026-08-18")
        self.assertEqual(title_class_date("POL2100 13/08/2569"), "2026-08-13")

    def test_wrong_subject_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "subject is POL4115"):
            validate_title_identity("pol 4115 18/8/69", "POL2129", "2026-08-18")

    def test_wrong_date_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "expected 2026-08-18"):
            validate_title_identity("POL2129 11/8/69", "POL2129", "2026-08-18")


if __name__ == "__main__":
    unittest.main()
