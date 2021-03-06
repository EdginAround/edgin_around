import unittest
import numpy

from math import pi, atan, sqrt, radians

from typing import Any, Dict

from . import common

from src import geometry

class GeometryTest(common.SerdeTest):
    def assert_tuples_almost_equal(self, t1, t2) -> None:
        self.assertEqual(len(t1), len(t1))
        for e1, e2 in zip(t1, t2):
            self.assertAlmostEqual(e1, e2)

    def assert_arrays_almost_equal(self, t1, t2) -> None:
        self.assertEqual(len(t1), len(t1))
        for e1, e2 in zip(t1, t2):
            self.assert_tuples_almost_equal(e1, e2)

    def test_cartesian_to_spherical(self) -> None:
        for cartesian, expected in (
            ((1.0, 0.0, 0.0), (     1.0,      0.50 * pi, 0.50 * pi)),
            ((0.0, 1.0, 0.0), (     1.0,      0.00 * pi, 0.50 * pi)),
            ((0.0, 0.0, 1.0), (     1.0,      0.50 * pi, 0.00 * pi)),
            ((0.0, 1.0, 1.0), (sqrt(2.0),     0.25 * pi, 0.00 * pi)),
            ((1.0, 0.0, 1.0), (sqrt(2.0),     0.50 * pi, 0.25 * pi)),
            ((1.0, 1.0, 0.0), (sqrt(2.0),     0.25 * pi, 0.50 * pi)),
            ((1.0, 1.0, 1.0), (sqrt(3.0), atan(sqrt(2)), 0.25 * pi)),
        ):
            computed = geometry.Coordinates.cartesian_to_spherical(*cartesian)
            self.assertEqual(expected, computed)

    def test_spherical_to_cartesian(self) -> None:
        for spherical, expected in (
            ((1.0, 0.0 * pi, 0.0 * pi), (0.0,  1.0,  0.0)),
            ((1.0, 1.0 * pi, 0.0 * pi), (0.0, -1.0,  0.0)),
            ((1.0, 0.0 * pi, 1.0 * pi), (0.0,  1.0,  0.0)),
            ((1.0, 0.5 * pi, 0.0 * pi), (0.0,  0.0,  1.0)),
            ((1.0, 0.5 * pi, 1.0 * pi), (0.0,  0.0, -1.0)),
            ((1.0, 0.5 * pi, 0.5 * pi), (1.0,  0.0,  0.0)),
        ):
            computed = geometry.Coordinates.spherical_to_cartesian(*spherical)
            self.assert_tuples_almost_equal(expected, computed)

    def test_spherical_to_geographical_degrees(self) -> None:
        for spherical, geographical in (
            ((1.0, 0.00 * pi, 0.0 * pi), (1.0,  90.0,    0.0)),
            ((1.0, 0.25 * pi, 0.5 * pi), (1.0,  45.0,   90.0)),
            ((1.0, 0.50 * pi, 1.0 * pi), (1.0,   0.0,  180.0)),
            ((1.0, 0.75 * pi, 1.5 * pi), (1.0, -45.0,  -90.0)),
            ((1.0, 1.00 * pi, 2.0 * pi), (1.0, -90.0,    0.0)),
        ):
            computed = geometry.Coordinates.spherical_to_geographical_degrees(*spherical)
            self.assert_tuples_almost_equal(geographical, computed)

    def test_geographical_degrees_spherical(self) -> None:
        for geographical, spherical in (
            ((1.0,  90.0,    0.0), (1.0, 0.00 * pi, 0.0 * pi)),
            ((1.0,  45.0,   90.0), (1.0, 0.25 * pi, 0.5 * pi)),
            ((1.0,   0.0,  180.0), (1.0, 0.50 * pi, 1.0 * pi)),
            ((1.0, -45.0,  -90.0), (1.0, 0.75 * pi, 1.5 * pi)),
            ((1.0, -90.0,    0.0), (1.0, 1.00 * pi, 0.0 * pi)),
        ):
            computed = geometry.Coordinates.geographical_degrees_to_spherical(*geographical)
            self.assert_tuples_almost_equal(spherical, computed)

    def test_bearing(self) -> None:
        for t1, t2, expected1, expected2 in (
            ((0.5 * pi, 0.0 * pi), (0.00 * pi,  0.0 * pi),  0.00 * pi,  1.00 * pi),
            ((0.5 * pi, 0.0 * pi), (0.25 * pi,  0.5 * pi),  0.25 * pi, -0.50 * pi),
            ((0.5 * pi, 0.0 * pi), (0.50 * pi,  0.5 * pi),  0.50 * pi, -0.50 * pi),
            ((0.5 * pi, 0.0 * pi), (0.75 * pi,  0.5 * pi),  0.75 * pi, -0.50 * pi),
            ((0.5 * pi, 0.0 * pi), (1.00 * pi,  0.0 * pi),  1.00 * pi,  0.00 * pi),
            ((0.5 * pi, 0.0 * pi), (0.75 * pi, -0.5 * pi), -0.75 * pi,  0.50 * pi),
            ((0.5 * pi, 0.0 * pi), (0.50 * pi, -0.5 * pi), -0.50 * pi,  0.50 * pi),
            ((0.5 * pi, 0.0 * pi), (0.25 * pi, -0.5 * pi), -0.25 * pi,  0.50 * pi),
        ):
            p1 = geometry.Point(*t1)
            p2 = geometry.Point(*t2)
            computed1 = p1.bearing_to(p2)
            computed2 = p2.bearing_to(p1)
            self.assertAlmostEqual(expected1, computed1)
            self.assertAlmostEqual(expected2, computed2)

    def test_personal_to_global(self) -> None:
        left     = numpy.array((-1.0,  0.0,  0.0, 1.0)).reshape(4, 1)
        right    = numpy.array(( 1.0,  0.0,  0.0, 1.0)).reshape(4, 1)
        up       = numpy.array(( 0.0,  1.0,  0.0, 1.0)).reshape(4, 1)
        down     = numpy.array(( 0.0, -1.0,  0.0, 1.0)).reshape(4, 1)
        forward  = numpy.array(( 0.0,  0.0, -1.0, 1.0)).reshape(4, 1)
        backward = numpy.array(( 0.0,  0.0,  1.0, 1.0)).reshape(4, 1)

        transformation = geometry.Matrices3D.personal_to_global(0.0, 0.0, 0.0)
        self.assert_arrays_almost_equal(transformation @ left, left)
        self.assert_arrays_almost_equal(transformation @ right, right)
        self.assert_arrays_almost_equal(transformation @ up, up)
        self.assert_arrays_almost_equal(transformation @ down, down)
        self.assert_arrays_almost_equal(transformation @ forward, forward)
        self.assert_arrays_almost_equal(transformation @ backward, backward)

        transformation = geometry.Matrices3D.personal_to_global(0.5 * pi, 0.0, 0.0)
        self.assert_arrays_almost_equal(transformation @ left, left)
        self.assert_arrays_almost_equal(transformation @ right, right)
        self.assert_arrays_almost_equal(transformation @ up, backward)
        self.assert_arrays_almost_equal(transformation @ down, forward)
        self.assert_arrays_almost_equal(transformation @ forward, up)
        self.assert_arrays_almost_equal(transformation @ backward, down)

        transformation = geometry.Matrices3D.personal_to_global(pi, 0.0, 0.0)
        self.assert_arrays_almost_equal(transformation @ left, left)
        self.assert_arrays_almost_equal(transformation @ right, right)
        self.assert_arrays_almost_equal(transformation @ up, down)
        self.assert_arrays_almost_equal(transformation @ down, up)
        self.assert_arrays_almost_equal(transformation @ forward, backward)
        self.assert_arrays_almost_equal(transformation @ backward, forward)

        transformation = geometry.Matrices3D.personal_to_global(0.5 * pi, 0.5 * pi, 0.0)
        self.assert_arrays_almost_equal(transformation @ left, backward)
        self.assert_arrays_almost_equal(transformation @ right, forward)
        self.assert_arrays_almost_equal(transformation @ up, right)
        self.assert_arrays_almost_equal(transformation @ down, left)
        self.assert_arrays_almost_equal(transformation @ forward, up)
        self.assert_arrays_almost_equal(transformation @ backward, down)

        transformation = geometry.Matrices3D.personal_to_global(0.5 * pi, -0.5 * pi, 0.0)
        self.assert_arrays_almost_equal(transformation @ left, forward)
        self.assert_arrays_almost_equal(transformation @ right, backward)
        self.assert_arrays_almost_equal(transformation @ up, left)
        self.assert_arrays_almost_equal(transformation @ down, right)
        self.assert_arrays_almost_equal(transformation @ forward, up)
        self.assert_arrays_almost_equal(transformation @ backward, down)

        transformation = geometry.Matrices3D.personal_to_global(0.0, 0.0, 0.5 * pi)
        self.assert_arrays_almost_equal(transformation @ left, forward)
        self.assert_arrays_almost_equal(transformation @ right, backward)
        self.assert_arrays_almost_equal(transformation @ up, up)
        self.assert_arrays_almost_equal(transformation @ down, down)
        self.assert_arrays_almost_equal(transformation @ forward, right)
        self.assert_arrays_almost_equal(transformation @ backward, left)

        transformation = geometry.Matrices3D.personal_to_global(0.5 * pi, 1.0 * pi, pi)
        self.assert_arrays_almost_equal(transformation @ left, left)
        self.assert_arrays_almost_equal(transformation @ right, right)
        self.assert_arrays_almost_equal(transformation @ up, forward)
        self.assert_arrays_almost_equal(transformation @ down, backward)
        self.assert_arrays_almost_equal(transformation @ forward, down)
        self.assert_arrays_almost_equal(transformation @ backward, up)

        transformation = geometry.Matrices3D.personal_to_global(0.5 * pi, 0.5 * pi, 0.5 * pi)
        self.assert_arrays_almost_equal(transformation @ left, up)
        self.assert_arrays_almost_equal(transformation @ right, down)
        self.assert_arrays_almost_equal(transformation @ up, right)
        self.assert_arrays_almost_equal(transformation @ down, left)
        self.assert_arrays_almost_equal(transformation @ forward, forward)
        self.assert_arrays_almost_equal(transformation @ backward, backward)

    def test_elevation_function_serialization(self) -> None:
        """Checks if the elevation function is serialized and deserialized properly."""

        original: Dict[str, Any] = {
            'radius': 999,
            'terrain': [{
                'type': 'hills',
                'origin': { 'theta': 0.0, 'phi': 0.0 },
            }, {
                'type': 'hills',
                'origin': { 'theta': 1.0, 'phi': 1.0 },
            }, {
                'type': 'ranges',
                'origin': { 'theta': 5.0, 'phi': 2.0 },
            }, {
                'type': 'continents',
                'origin': { 'theta': 8.0, 'phi': 9.0 },
            }]
        }

        self.assert_serde(original, geometry.ElevationFunction.Schema(), geometry.ElevationFunction)

