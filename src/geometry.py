import abc, enum
from dataclasses import dataclass
from math import asin, atan2, cos, degrees, pi, radians, sin, sqrt, tan

import marshmallow, numpy
from marshmallow import fields as mf
from marshmallow_oneofschema import OneOfSchema

from typing import Callable, Iterable, Iterator, List, Optional, Set, Tuple, cast

####################################################################################################

class Coordinates:
    @staticmethod
    def cartesian_to_spherical(x, y, z):
        r = sqrt(x * x + y * y + z * z)
        theta = atan2(sqrt(x * x + z * z), y) if y != 0.0 else 0.5 * pi
        phi = atan2(x, z) if z != 0.0 else 0.5 * pi
        return r, theta, phi

    @staticmethod
    def cartesian_to_geographical_radians(x, y, z):
        coords = Coordinates.cartesian_to_spherical(x, y, z)
        return Coordinates.spherical_to_geographical_radians(*coords)

    @staticmethod
    def cartesian_to_geographical_degrees(x, y, z):
        coords = Coordinates.cartesian_to_spherical(x, y, z)
        return Coordinates.spherical_to_geographical_degrees(*coords)

    @staticmethod
    def spherical_to_cartesian(r, theta, phi):
        z = r * sin(theta) * cos(phi)
        x = r * sin(theta) * sin(phi)
        y = r * cos(theta)
        return x, y, z

    @staticmethod
    def spherical_to_geographical_radians(r, theta, phi):
        lat = 0.5 * pi - theta
        lon = phi if phi <= pi else phi - 2.0 * pi
        return r, lat, lon

    @staticmethod
    def spherical_to_geographical_degrees(r, theta, phi):
        r, lat, lon = Coordinates.spherical_to_geographical_radians(r, theta, phi)
        return r, degrees(lat), degrees(lon)

    @staticmethod
    def geographical_radians_to_spherical(r, lat, lon):
        theta = 0.5 * pi - lat
        phi = lon if lon >= 0 else lon + 2.0 * pi
        return r, theta, phi

    @staticmethod
    def geographical_degrees_to_spherical(r, lat, lon):
        return Coordinates.geographical_radians_to_spherical(r, radians(lat), radians(lon))

####################################################################################################

class Coordinate:
    """Position expressed in geographical coordinates with radians."""

    def __init__(self, lat, lon) -> None:
        self.lat = lat
        self.lon = lon

    def bearing_to(self, other: 'Coordinate') -> float:
        """Calculates bearing between two coordinates."""

        x = sin(other.lon - self.lon) * cos(other.lat)
        y = cos(self.lat) * sin(other.lat) - \
            sin(self.lat) * cos(other.lat) * cos(other.lon - self.lon)

        return atan2(x, y)

    def great_circle_distance_to(self, other: 'Coordinate', radius: float) -> float:
        sin1 = sin(0.5 * abs(self.lat - other.lat))
        sin2 = sin(0.5 * abs(self.lon - other.lon))
        return 2 * radius * asin(sqrt(sin1 * sin1 + cos(self.lat) * cos(other.lat) * sin2 * sin2))

    def moved_by(self, distance, bearing, radius) -> 'Coordinate':
        angular_distance = distance / radius
        cad = cos(angular_distance)
        sad = sin(angular_distance)

        cb = cos(bearing)
        sb = sin(bearing)

        slat1 = sin(self.lat)
        clat1 = cos(self.lat)

        lat2 = asin(slat1 * cad + clat1 * sad * cb)
        slat2 = sin(lat2)
        lon2 = self.lon + atan2(sb * sad * clat1, cad - slat1 * slat2)

        return Coordinate(lat2, lon2)

    def to_point(self) -> 'Point':
        r, theta, phi = Coordinates.geographical_radians_to_spherical(1.0, self.lat, self.lon)
        return Point(theta, phi)

####################################################################################################

class Point:
    """Position expressed in spherical coordinates."""

    class Schema(marshmallow.Schema):
        theta = mf.Float()
        phi = mf.Float()

        @marshmallow.post_load
        def make(self, data, **kwargs):
            return Point(**data)

    def __init__(self, theta: float, phi: float) -> None:
        self.theta = theta
        self.phi = phi

    def bearing_to(self, other: 'Point') -> float:
        """Calculates bearing between two points expressed in spherical coordinates."""

        coord1 = self.to_coordinate()
        coord2 = other.to_coordinate()
        return coord1.bearing_to(coord2)

    def great_circle_distance_to(self, other: 'Point', radius: float) -> float:
        coord1 = self.to_coordinate()
        coord2 = other.to_coordinate()
        return coord1.great_circle_distance_to(coord2, radius)

    def moved_by(self, distance, bearing, radius) -> 'Point':
        return self.to_coordinate().moved_by(distance, bearing, radius).to_point()

    def to_coordinate(self) -> Coordinate:
        r, lat, lon = Coordinates.spherical_to_geographical_radians(1.0, self.theta, self.phi)
        return Coordinate(lat, lon)

    def __str__(self) -> str:
        return f'Point(theta={self.theta}, phi={self.phi})'

####################################################################################################

Point3D = Tuple[float, float, float]
Indices3D = Tuple[int, int, int]

class Polyhedron:
    """"Polyhedron data container."""

    def __init__(self, vertices: Iterable[Point3D], triangles: Iterable[Indices3D]) -> None:
        # An ordered list of points.
        self.vertices: List[Point3D] = list(vertices)

        # A set of triangles defined as tuples of indices.
        self.triangles: Set[Indices3D] = \
            set(cast(Indices3D, tuple(sorted(indices))) for indices in triangles)

    def get_vertices(self) -> Iterator[Tuple[float, float, float]]:
        for vertex in self.vertices:
            yield vertex

    def get_triangles(self) -> Iterator[Tuple[float, float, float]]:
        for triangle in self.triangles:
            yield triangle

    def rescale(self, stretch: Callable[[Point], float]) -> None:
        for i, vertex in enumerate(self.vertices):
            r, theta, phi = Coordinates.cartesian_to_spherical(*vertex)
            multiplier = stretch(Point(theta, phi)) / r
            self.vertices[i] = cast(Point3D, tuple(cast(float, v * multiplier) for v in vertex))

####################################################################################################

class Structures:
    """Structures generator class."""

    @staticmethod
    def icosahedron() -> Polyhedron:
        """Icosahedron generation function"""

        f = (sqrt(5.0) + 1.0) / 2.0
        b = sqrt(2.0 / (5.0 + sqrt(5.0)))
        a = b * f

        return Polyhedron(
            (( 0, b, a), ( 0, b,-a), ( 0,-b, a), ( 0,-b,-a),
             ( a, 0, b), ( a, 0,-b), (-a, 0, b), (-a, 0,-b),
             ( b, a, 0), ( b,-a, 0), (-b, a, 0), (-b,-a, 0)),
            {(0,  2, 4), (0,  2, 6), (1,  3,  5), (1,  3,  7),
             (4,  5, 8), (4,  5, 9), (6,  7, 10), (6,  7, 11),
             (8, 10, 0), (8, 10, 1), (9, 11,  2), (9, 11,  3),
             (4,  8, 0), (5,  8, 1), (4,  9,  2), (5,  9,  3),
             (6, 10, 0), (7, 10, 1), (6, 11,  2), (7, 11,  3)}
        )

    @staticmethod
    def sphere(n, radius=1.0) -> Polyhedron:
        """Sphere generation function"""

        def scaled(vector):
            length_inv = 1.0 / sqrt(sum(v*v for v in vector))
            return tuple([radius * v * length_inv for v in vector])

        def nm(v1, v2):
            return scaled([0.5 * (v1[i] + v2[i]) for i in range(0, len(v1))])

        def index(v):
            if v not in indices:
                indices[v] = len(vertices)
                vertices.append(v)

            return indices[v]

        icosahedron = Structures.icosahedron()
        vertices = [scaled(v) for v in icosahedron.vertices]
        old_triangles = icosahedron.triangles
        indices = {v: i for i, v in enumerate(vertices)}

        for i in range(0, n):
            new_triangles = set()

            for t in old_triangles:
                v0 = nm(vertices[t[1]], vertices[t[2]])
                v1 = nm(vertices[t[0]], vertices[t[2]])
                v2 = nm(vertices[t[0]], vertices[t[1]])

                p0 = index(v0)
                p1 = index(v1)
                p2 = index(v2)

                new_triangles.update([(t[0], p1, p2)])
                new_triangles.update([(t[1], p0, p2)])
                new_triangles.update([(t[2], p0, p1)])
                new_triangles.update([(p0, p1, p2)])

            old_triangles = new_triangles

        return Polyhedron(vertices, new_triangles)

####################################################################################################

class Matrices3D:
    """Generator for 3D transformations."""

    @staticmethod
    def identity() -> numpy.array:
        return numpy.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ], dtype=numpy.float32)

    @staticmethod
    def perspective(
            fovy: float,
            width: float,
            height: float,
            near: float,
            far: float,
        ) -> numpy.array:
        s = 1.0 / tan(0.5 * fovy)
        sx, sy = s * height / width, s
        zz = (far + near) / (near - far)
        zw = 2 * far * near / (near - far)
        return numpy.array([
            [sx,  0,  0,  0],
            [ 0, sy,  0,  0],
            [ 0,  0, zz, zw],
            [ 0,  0, -1,  0],
        ], dtype=numpy.float32)

    @staticmethod
    def orthographic(
            left: float,
            right: float,
            bottom: float,
            top: float,
            near: float,
            far: float,
        ) -> numpy.array:
        wr = 1.0 / (right - left)
        hr = 1.0 / (top - bottom)
        dr = 1.0 / (far - near)
        return numpy.array([
            [2.0 * wr,        0,         0, -(right + left) * wr],
            [       0, 2.0 * hr,         0, -(top + bottom) * hr],
            [       0,        0, -2.0 * dr,   -(far + near) * dr],
            [       0,        0,         0,                    1],
        ], dtype=numpy.float32)

    @staticmethod
    def translation(vector: Tuple[float, float, float]) -> numpy.array:
        x, y, z = vector
        return numpy.array([
            [1, 0, 0, x],
            [0, 1, 0, y],
            [0, 0, 1, z],
            [0, 0, 0, 1],
        ], dtype=numpy.float32)

    @staticmethod
    def rotation_x(a: float) -> numpy.array:
        c, s = cos(a), sin(a)
        return numpy.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0,   c,  -s, 0.0],
            [0.0,   s,   c, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ], dtype=numpy.float32)

    @staticmethod
    def rotation_y(a: float) -> numpy.array:
        c, s = cos(a), sin(a)
        return numpy.array([
            [  c, 0.0,   s, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [ -s, 0.0,   c, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ], dtype=numpy.float32)

    @staticmethod
    def rotation_z(a: float) -> numpy.array:
        c, s = cos(a), sin(a)
        return numpy.array([
            [  c,  -s, 0.0, 0.0],
            [  s,   c, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ], dtype=numpy.float32)

    @staticmethod
    def personal_to_global(theta, phi, bearing) -> numpy.array:
        return Matrices3D.rotation_y(phi) \
             @ Matrices3D.rotation_x(theta) \
             @ Matrices3D.rotation_y(-bearing)

class Matrices2D:
    """Generator for 2D transformations."""

    @staticmethod
    def identity() -> numpy.array:
        return numpy.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
        ], dtype=numpy.float32)

    @staticmethod
    def translation(vector: Tuple[float, float]) -> numpy.array:
        x, y = vector
        return numpy.array([
            [1, 0, x],
            [0, 1, y],
            [0, 0, 1],
        ], dtype=numpy.float32)

    @staticmethod
    def rotation(a: float) -> numpy.array:
        c, s = cos(a), sin(a)
        return numpy.array([
            [  c,  -s, 0.0],
            [  s,   c, 0.0],
            [0.0, 0.0, 1.0],
        ], dtype=numpy.float32)

    @staticmethod
    def scale(scale: Tuple[float, float]) -> numpy.array:
        x, y = scale
        return numpy.array([
            [  x, 0.0, 0.0],
            [0.0,   y, 0.0],
            [0.0, 0.0, 1.0],
        ], dtype=numpy.float32)

####################################################################################################

class Boundary2D:
    def __init__(self, left: float, bottom: float, right: float, top: float) -> None:
        self.left = left
        self.bottom = bottom
        self.right = right
        self.top = top

    def contains(self, x: float, y: float) -> bool:
        return self.left < x and x < self.right and self.bottom < y and y < self.top


class Tile:
    def __init__(
        self,
        id: Tuple[str, ...],
        position: Tuple[float, float],
        size: Tuple[float, float],
    ) -> None:
        self.id = id
        self.points = [
            numpy.array([position[0],           position[1]          , 1.0], dtype=numpy.float32),
            numpy.array([position[0],           position[1] + size[1], 1.0], dtype=numpy.float32),
            numpy.array([position[0] + size[0], position[1] + size[1], 1.0], dtype=numpy.float32),
            numpy.array([position[0] + size[0], position[1]          , 1.0], dtype=numpy.float32),
        ]

    def rotate(self, angle: float) -> None:
        self.transform(Matrices2D.rotation(angle))

    def translate(self, vector: Tuple[float, float]) -> None:
        self.transform(Matrices2D.translation(vector))

    def scale(self, vector: Tuple[float, float]) -> None:
        self.transform(Matrices2D.scale(vector))

    def transform(self, matrix: numpy.array) -> None:
        for i, point in enumerate(self.points):
            self.points[i] = matrix @ point.reshape(3, 1)

    def rotated(self, angle: float) -> 'Tile':
        self.rotate(angle)
        return self

    def translated(self, vector: Tuple[float, float]) -> 'Tile':
        self.translate(vector)
        return self

    def scaled(self, vector: Tuple[float, float]) -> 'Tile':
        self.scale(vector)
        return self

    def transformed(self, matrix: numpy.array) -> 'Tile':
        self.transform(matrix)
        return self

    def __repr__(self) -> str:
        return f'Tile(id={self.id}, points={self.points})'

####################################################################################################

class _Terrains(enum.Enum):
    HILLS = 'hills'
    RANGES = 'ranges'
    CONTINENTS = 'continents'


class _TerrainInfo(abc.ABC):
    def evaluate(self, pos: Point, radius: float) -> float:
        pass


@dataclass
class Hills(_TerrainInfo):
    origin: Point

    class Schema(marshmallow.Schema):
        origin = mf.Nested(Point.Schema)

        @marshmallow.post_load
        def make(self, data, **kwargs):
            return Hills(**data)

    def evaluate(self, pos: Point, radius: float) -> float:
        return 0.006 * radius \
            * (pos.theta / pi - 1) * sin(50 * pos.phi) \
            * (pos.theta / pi - 2) * sin(50 * pos.theta)


@dataclass
class Ranges(_TerrainInfo):
    origin: Point

    class Schema(marshmallow.Schema):
        origin = mf.Nested(Point.Schema)

        @marshmallow.post_load
        def make(self, data, **kwargs):
            return Ranges(**data)

    def evaluate(self, pos: Point, radius: float) -> float:
        return 0.012 * radius * cos(10 * pos.theta + pi) * cos(10 * pos.phi)


@dataclass
class Continents(_TerrainInfo):
    origin: Point

    class Schema(marshmallow.Schema):
        origin = mf.Nested(Point.Schema)

        @marshmallow.post_load
        def make(self, data, **kwargs):
            return Continents(**data)

    def evaluate(self, pos: Point, radius: float) -> float:
        return 0.018 * radius * sin(pos.theta) * sin(pos.phi)


class _TerrainSchema(OneOfSchema):
    type_schemas = {
        _Terrains.HILLS.value: Hills.Schema,
        _Terrains.RANGES.value: Ranges.Schema,
        _Terrains.CONTINENTS.value: Continents.Schema,
    }

    type_names = {
        Hills: _Terrains.HILLS.value,
        Ranges: _Terrains.RANGES.value,
        Continents: _Terrains.CONTINENTS.value,
    }

    def get_obj_type(self, obj):
        name = self.type_names.get(type(obj), None)
        if name is not None:
            return name
        else:
            raise Exception("Unknown object type: {}".format(obj.__class__.__name__))


class ElevationFunction:
    class Schema(marshmallow.Schema):
        radius = mf.Float()
        terrain = mf.List(mf.Nested(_TerrainSchema))

        @marshmallow.post_load
        def make(self, data, **kwargs):
            schema = _TerrainSchema()
            ef = ElevationFunction(data['radius'])
            ef.terrain = data['terrain']
            return ef

    def __init__(self, radius: float) -> None:
        self.radius = radius
        self.terrain: List[_TerrainInfo] = list()

    def add(self, terrain: _TerrainInfo) -> None:
        self.terrain.append(terrain)

    def get_radius(self) -> float:
        return self.radius

    def evaluate_without_radius(self, position: Point) -> float:
        return sum(terrain.evaluate(position, self.radius) for terrain in self.terrain)

    def evaluate_with_radius(self, position: Point) -> float:
        return self.radius + self.evaluate_without_radius(position)

