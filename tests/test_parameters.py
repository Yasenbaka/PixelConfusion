"""Tests for the sidebar parameter normalization."""

import unittest

from pixelconfusion.parameters import TransformRequest, build_transform_request


class ParameterTests(unittest.TestCase):
    def test_gilbert_defaults_to_automatic_offset(self):
        request = build_transform_request(
            "gilbert", "scramble", "3", "  ", "9", "9", width=40, height=20,
        )
        self.assertEqual(request, TransformRequest("gilbert", "scramble", 3, None))

    def test_gilbert_ignores_arnold_fields(self):
        request = build_transform_request(
            "gilbert", "restore", "1", "-11", "not-an-int", "also-bad",
            width=40, height=20,
        )
        self.assertEqual(request, TransformRequest("gilbert", "restore", 1, -11))

    def test_arnold_reads_a_and_b(self):
        request = build_transform_request(
            "arnold", "scramble", "17", "", "2", "3", width=32, height=32,
        )
        self.assertEqual(request, TransformRequest("arnold", "scramble", 17, None, 2, 3))

    def test_out_of_range_iterations_are_rejected(self):
        for text in ("0", "1000001"):
            with self.subTest(iterations=text):
                with self.assertRaises(ValueError):
                    build_transform_request(
                        "gilbert", "scramble", text, "", "1", "1", width=8, height=8,
                    )

    def test_non_square_arnold_is_rejected(self):
        with self.assertRaises(ValueError):
            build_transform_request(
                "arnold", "scramble", "1", "", "1", "1", width=8, height=9,
            )

    def test_invalid_numbers_are_rejected(self):
        with self.assertRaises(ValueError):
            build_transform_request(
                "gilbert", "scramble", "abc", "", "1", "1", width=8, height=8,
            )


if __name__ == "__main__":
    unittest.main()
