"""Tests for the sidebar parameter normalization."""

import unittest

from pixelconfusion.parameters import (
    MAX_ITERATIONS,
    BatchRequest,
    TransformRequest,
    build_batch_request,
    build_transform_request,
)


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


class BatchParameterTests(unittest.TestCase):
    def test_batch_reads_range_and_shared_parameters(self):
        request = build_batch_request(
            "gilbert", ("restore", "scramble"), 11, "10", "-7", "9", "9",
            width=40, height=20,
        )
        self.assertEqual(
            request,
            BatchRequest("gilbert", ("restore", "scramble"), 11, 10, -7),
        )
        self.assertEqual(request.end, 20)

    def test_batch_out_of_range_counts_are_rejected(self):
        for text in ("0", "51", "abc"):
            with self.subTest(count=text):
                with self.assertRaises(ValueError):
                    build_batch_request(
                        "gilbert", ("restore",), 1, text, "", "1", "1",
                        width=8, height=8,
                    )

    def test_batch_start_must_stay_within_iteration_limit(self):
        for start in (0, MAX_ITERATIONS):
            with self.subTest(start=start):
                with self.assertRaises(ValueError):
                    build_batch_request(
                        "gilbert", ("restore",), start, "2", "", "1", "1",
                        width=8, height=8,
                    )

    def test_batch_rejects_non_square_arnold_and_unknown_actions(self):
        with self.assertRaises(ValueError):
            build_batch_request(
                "arnold", ("restore",), 1, "10", "", "1", "1",
                width=8, height=9,
            )
        with self.assertRaises(ValueError):
            build_batch_request(
                "gilbert", ("sideways",), 1, "10", "", "1", "1",
                width=8, height=8,
            )

    def test_batch_gilbert_ignores_arnold_fields(self):
        request = build_batch_request(
            "gilbert", ("scramble",), 1, "3", " ", "bad", "bad",
            width=20, height=10,
        )
        self.assertEqual(request.offset, None)
        self.assertEqual((request.a, request.b), (1, 1))


if __name__ == "__main__":
    unittest.main()
