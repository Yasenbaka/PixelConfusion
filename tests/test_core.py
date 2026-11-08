"""Deterministic tests using generated pixels only: python -m unittest -v."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from pixelconfusion.core import (
    Transformer,
    arnold_transform,
    default_offset,
    gilbert_order,
    gilbert_transform,
    load_image,
    save_png,
)


class PermutationTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(20261104)

    def test_known_gilbert_path_and_direction(self):
        np.testing.assert_array_equal(gilbert_order(3, 2), [0, 3, 4, 5, 2, 1])
        np.testing.assert_array_equal(gilbert_order(2, 3), [0, 1, 3, 5, 4, 2])
        pixels = np.arange(6, dtype=np.uint8).reshape(2, 3, 1)
        actual = gilbert_transform(pixels, gilbert_order(3, 2), 2)
        np.testing.assert_array_equal(actual.ravel(), [4, 3, 0, 5, 2, 1])

    def test_curve_is_bijective_including_thin_and_odd_images(self):
        dimensions = [(w, h) for w in range(1, 19) for h in range(1, 19)]
        dimensions.extend([(1, 9001), (9001, 1), (97, 83), (128, 96)])
        for width, height in dimensions:
            with self.subTest(size=(width, height)):
                order = gilbert_order(width, height)
                np.testing.assert_array_equal(np.sort(order), np.arange(width * height))

    def test_gilbert_round_trip_retains_every_rgba_byte(self):
        engine = Transformer()
        for height, width in [(1, 1), (1, 101), (81, 1), (23, 37), (96, 128)]:
            original = self.rng.integers(0, 256, (height, width, 4), dtype=np.uint8)
            image = Image.fromarray(original)
            for iterations, offset in [(1, None), (7, -11), (29, 0), (3, 10**30)]:
                with self.subTest(size=(width, height),
                                  iterations=iterations, offset=offset):
                    encrypted = engine.apply(image, action="scramble",
                                             iterations=iterations, offset=offset)
                    restored = engine.apply(encrypted, action="restore",
                                            iterations=iterations, offset=offset)
                    np.testing.assert_array_equal(np.array(restored), original)
                    np.testing.assert_array_equal(np.array(image), original)

    def test_arnold_matches_independent_forward_coordinate_formula(self):
        pixels = np.arange(5 * 5 * 4, dtype=np.uint8).reshape(5, 5, 4)
        expected = np.empty_like(pixels)
        for y in range(5):
            for x in range(5):
                expected[(x + 2 * y) % 5, (x + y) % 5] = pixels[y, x]
        encrypted = arnold_transform(pixels, -1)
        np.testing.assert_array_equal(encrypted, expected)
        np.testing.assert_array_equal(arnold_transform(encrypted, 1), pixels)

    def test_arnold_round_trip_with_varied_parameters(self):
        engine = Transformer()
        for size in (1, 7, 16, 29):
            original = self.rng.integers(0, 256, (size, size, 4), dtype=np.uint8)
            image = Image.fromarray(original)
            for a, b, iterations in ((1, 1, 1), (2, 3, 17), (-5, 7, 1_000_000)):
                with self.subTest(size=size, a=a, b=b, iterations=iterations):
                    encrypted = engine.apply(image, "arnold", "scramble", iterations, a=a, b=b)
                    restored = engine.apply(encrypted, "arnold", "restore", iterations, a=a, b=b)
                    np.testing.assert_array_equal(np.array(restored), original)

    def test_invalid_parameters_are_rejected(self):
        engine = Transformer()
        image = Image.new("RGBA", (7, 5))
        with self.assertRaises(ValueError):
            engine.apply(image, "arnold")
        with self.assertRaises(ValueError):
            engine.apply(image, iterations=0)
        with self.assertRaises(ValueError):
            engine.apply(image, method="unknown")
        with self.assertRaises(ValueError):
            gilbert_order(0, 10)

    def test_file_round_trip_preserves_pixels_and_dimensions(self):
        original = self.rng.integers(0, 256, (25, 37, 4), dtype=np.uint8)
        image = Image.fromarray(original)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ordinary_test.png"
            save_png(image, path)
            loaded = load_image(path)
            self.assertEqual(loaded.size, (37, 25))
            np.testing.assert_array_equal(np.array(loaded), original)

    def test_default_offset_uses_nearest_integer(self):
        self.assertEqual(default_offset(6), 4)
        self.assertEqual(default_offset(100), 62)


if __name__ == "__main__":
    unittest.main()
