"Contains a test case for WGS84 functions"

import unittest
from math import pi

from shapely.geometry import Point, LineString

from openlr import Coordinates

from openlr_dereferencer.maps.wgs84 import WGS84GeoTool

class GeoTests(unittest.TestCase):
    "Unit tests for all the WGS84 functions"

    geo_tool = WGS84GeoTool()

    def test_distance_1(self):
        "Compare a WGS84 distance to an expected value"
        geo1 = Coordinates(4.9091286, 52.3773181)
        geo2 = Coordinates(13.4622487, 52.4952885)
        dist = self.geo_tool.distance(geo1, geo2)
        # Compare that to what google maps says (579.3 km)
        self.assertAlmostEqual(dist, 579_530, delta=3000)

    def test_distance_2(self):
        "Compare a WGS84 distance to an expected value"
        geo1 = Coordinates(13.1759576, 52.4218989)
        geo2 = Coordinates(13.147999, 52.4515114)
        dist = self.geo_tool.distance(geo1, geo2)
        self.assertAlmostEqual(3800, dist, delta=10)

    def test_distance_3(self):
        "Compare a WGS84 distance to an expected value"
        geo1 = Coordinates(19.3644325, 51.796037)
        geo2 = Coordinates(19.3642027, 51.7957296)
        dist = self.geo_tool.distance(geo1, geo2)
        # Compare that to what Spatialite says
        self.assertAlmostEqual(37.7, dist, delta=0.05)

    def test_distance_4(self):
        "Compare a WGS84 distance near prime Meridian to an expected value"
        geo1 = Coordinates(-0.0000886, 51.462934)
        geo2 = Coordinates(0.000097, 51.4629935)
        dist = self.geo_tool.distance(geo1, geo2)
        # Compare that to what Spatialite says
        self.assertAlmostEqual(14.50, dist, delta=0.05)

    def test_bearing_zero(self):
        "Test bearing function where it should be zero"
        geo1 = Coordinates(0.0, 10.0)
        geo2 = Coordinates(0.0, 20.0)
        dist = self.geo_tool.bearing(geo1, geo2)
        self.assertEqual(dist, 0.0)

    def test_bearing_180(self):
        "Test bearing function where it should be 180°"
        geo1 = Coordinates(0.0, -10.0)
        geo2 = Coordinates(0.0, -20.0)
        bear = self.geo_tool.bearing(geo1, geo2)
        self.assertEqual(bear, pi)

    def test_bearing_90_1(self):
        "Test bearing function where it should be 90°"
        geo1 = Coordinates(1.0, 0.0)
        geo2 = Coordinates(2.0, 0.0)
        bear = self.geo_tool.bearing(geo1, geo2)
        self.assertEqual(bear, pi / 2)

    def test_bearing_90_2(self):
        "Test bearing function where it should be 90°"
        geo1 = Coordinates(-1.0, 0.0)
        geo2 = Coordinates(-2.0, 0.0)
        bear = self.geo_tool.bearing(geo1, geo2)
        self.assertEqual(bear, -pi / 2)

    def test_projection_90(self):
        "Test point projection into 90° direction"
        geo1 = Coordinates(0.0, 0.0)
        (lon, lat) = self.geo_tool.extrapolate(geo1, 20037508.0, pi * 90.0 / 180)
        self.assertAlmostEqual(lon, 180.0, delta=0.1)
        self.assertAlmostEqual(lat, 0.0)

    def test_projection_and_angle(self):
        "Test re-projecting existing point"
        geo1 = Coordinates(13.41, 52.525)
        geo2 = Coordinates(13.414, 52.525)
        dist = self.geo_tool.distance(geo1, geo2)
        angle = self.geo_tool.bearing(geo1, geo2)
        geo3 = self.geo_tool.extrapolate(geo1, dist, angle)
        self.assertAlmostEqual(geo2.lon, geo3.lon)
        self.assertAlmostEqual(geo2.lat, geo3.lat)

    def test_point_along_path(self):
        "Test point projection along path"
        path = [
            Coordinates(0.0, 0.0),
            Coordinates(0.0, 1.0),
            Coordinates(0.0, 2.0)
        ]
        part_lengths = [self.geo_tool.distance(path[i], path[i+1]) for i in range(len(path)-1)]
        length = sum(part_lengths)
        projected = self.geo_tool.interpolate(path, 0.75 * length)
        self.assertAlmostEqual(projected.lon, 0.0, places=3)
        self.assertAlmostEqual(projected.lat, 1.5, places=3)

    def test_split_line(self):
        start = Coordinates(13.0, 52.0)
        middle = Coordinates(13.1, 52.0)
        end = Coordinates(13.1, 52.1)
        line = LineString([Point(*start), Point(*middle), Point(*end)])
        length = self.geo_tool.distance(start, middle) + self.geo_tool.distance(middle, end)
        (first, second) = self.geo_tool.split_line(line, 0.0)
        self.assertIsNone(first)
        self.assertEqual(second, line)
        (first, second) = self.geo_tool.split_line(line, 1.0 * length)
        self.assertIsNone(second)
        self.assertEqual(first, line)
        (first, second) = self.geo_tool.split_line(line, 0.5 * length)
        assert(first is not None)
        assert(second is not None)
        self.assertAlmostEqual(first.length + second.length, line.length)

