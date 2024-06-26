"""Contains an abstract `MapReader` base class, which must be implemented for each
map format to decode location references on.

A MapReader is an interface with which the decoder can traverse the map. An implementation may
consist of a database connection or something similar. Its purpose is to let the decoder read
map objects.

In order to implement a reader for a new map, the following interfaces have to be implemented:

* :py:attr:`~MapReader`
* :py:attr:`~Node`
* :py:attr:`~Line`

The map model
-------------
Nodes
=====
A node is an object with an ID and a WGS84 longitude/latitude position.

Lines
=====
A line interconnects exactly two nodes in exactly one direction. As additional attributes,
it has a shape, a functional road class and a form of way.

Note that the map you want to implement may have a different line concept. For example, it is
common that roads are not necessarily directed. Also, roads may connect more than two nodes.

Let's consider an example map format that defines ways like this:

.. image:: _static/Mapformat_1_Way.svg

Roads in the map are modeled as multi-directional ways.

If we write a MapReader adapter for this format, we could consider every
directed link between nodes being a line, yielding multiple lines per way.

As lines and ways are now different things, our line IDs have to include more than
just the way ID. It can be, for example, a tuple of the way ID and both node IDs.

.. image:: _static/Mapformat_2_Lines.svg

Line IDs are required to be hashable. Since tuples of numbers are hashable,
they can be used to implement line IDs.
"""

from abc import ABC, abstractmethod
from typing import Iterable, Hashable, Sequence, Tuple, Optional
from openlr import Coordinates, FOW, FRC
from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry


class GeoTool(ABC):
    """
    Abstract geo-utility class

    Instances of this class contain helper methods invoked by the matcher at various
    points during the matching process. An instance of this class can be specified on the
    `decode` function, or else it defaults to a Python-only instance for WGS84 
    (WGS84GeoTool). The intent is to give the user the opportunity to specialize this 
    class for a specific target map. Doing so allows the user to more easily target 
    non-WGS84 maps, and also to optimize processing (for example by implementing the 
    methods in such a way as to defer processing to C-libraries such as proj or
    geographiclib instead of using the default python-only implementation).   
    """

    @abstractmethod
    def transform_coordinate(self, coord: Coordinates) -> Coordinates:
        """ Transforms a WGS84 coordinate into the local CRS """

    @abstractmethod
    def bearing(self, point_a: Coordinates, point_b: Coordinates) -> float:
        """Returns the angle between self and other relative to true north

        The result of this function is between -pi, pi, including them"""

    @abstractmethod
    def distance(self, point_a: Coordinates, point_b: Coordinates) -> float:
        """Returns the distance of two WGS84 coordinates on our planet, in meters"""

    @abstractmethod
    def line_string_length(self, line_string: LineString) -> float:
        """Returns the length of a line string in meters"""

    @abstractmethod
    def extrapolate(self, point: Coordinates, dist: float, angle: float) -> Coordinates:
        """Creates a new point that is `dist` meters away in direction `angle`"""

    @abstractmethod
    def interpolate(self, path: Sequence[Coordinates], distance_meters: float) -> Coordinates:
        """Go `distance` meters along the `path` and return the resulting point

        When the length of the path is too short, returns its last coordinate"""

    @abstractmethod
    def split_line(self, line: LineString, meters_into: float) -> Tuple[Optional[LineString], Optional[LineString]]:
        """Splits a line at `meters_into` meters and returns the two parts. A part is None if it would be a Point"""

    @abstractmethod
    def join_lines(self, lines: Sequence[LineString]) -> LineString:
        """ Combine a sequence of contiguous LineStrings into a single LineString"""


class GeometricObject(ABC):
    @property
    @abstractmethod
    def geometry(self) -> BaseGeometry:
        """Returns the geometry of this object"""


class Line(GeometricObject):
    """Abstract Line class, modelling a line coming from a map reader"""

    @property
    @abstractmethod
    def line_id(self) -> Hashable:
        """Returns the id of the line.
        
        A type is not specified here, but the ID has to be usable as key of a dictionary."""

    @property
    @abstractmethod
    def start_node(self) -> "Node":
        """Returns the node from which this line starts"""

    @property
    @abstractmethod
    def end_node(self) -> "Node":
        """Returns the node on which this line ends"""

    @property
    @abstractmethod
    def frc(self) -> FRC:
        """Returns the functional road class of this line"""

    @property
    @abstractmethod
    def fow(self) -> FOW:
        """Returns the form of way of this line"""

    @property
    @abstractmethod
    def geometry(self) -> LineString:
        """Returns the geometric shape as a linestring"""

    def coordinates(self) -> Sequence[Coordinates]:
        """Returns the shape of the line as list of Coordinates"""
        return [Coordinates(*point) for point in self.geometry.coords]

    @property
    @abstractmethod
    def length(self) -> float:
        """Return the line length in meters"""

    @abstractmethod
    def distance_to(self, coord: Coordinates) -> int:
        """Compute the point-to-line distance"""


class Node(GeometricObject):
    """Abstract class modelling a node returned by a map reader"""

    @property
    @abstractmethod
    def coordinates(self) -> Coordinates:
        """Returns the lon, lat coordinates of this node"""

    @property
    def geometry(self) -> Point:
        """Returns the position of this node as shapely point"""
        return Point(*self.coordinates)

    @abstractmethod
    def outgoing_lines(self, source: Optional[Line] = None) -> Iterable[Line]:
        """Yields all lines coming directly from this node"""

    @abstractmethod
    def incoming_lines(self, source: Optional[Line] = None) -> Iterable[Line]:
        """Yields all lines coming directly to this node."""

    @abstractmethod
    def connected_lines(self) -> Iterable[Line]:
        """Returns lines which touch this node"""

    @property
    @abstractmethod
    def node_id(self) -> Hashable:
        """Returns the id of this node."""


class MapReader(ABC):
    """Abstract base class for map readers.

    This is an adapter class that fulfills the map requirements of OpenLR."""

    @abstractmethod
    def get_line(self, line_id: Hashable) -> Line:
        """Returns a line by its id"""

    @abstractmethod
    def get_lines(self) -> Iterable[Line]:
        """Yields all lines in the map."""

    @abstractmethod
    def get_linecount(self) -> int:
        """Returns the number of lines in the map."""

    @abstractmethod
    def get_node(self, node_id: Hashable) -> Node:
        """Returns a node by its id."""

    @abstractmethod
    def get_nodes(self) -> Iterable[Node]:
        """Yields all nodes contained in the map."""

    @abstractmethod
    def get_nodecount(self) -> int:
        """Returns the number of nodes in the map."""

    @abstractmethod
    def find_nodes_close_to(self, coord: Coordinates, dist: float) -> Iterable[Node]:
        """Iterates over all nodes within `dist` meters around `coord`.

        No order specified here."""

    @abstractmethod
    def find_lines_close_to(self, coord: Coordinates, dist: float) -> Iterable[Line]:
        """Iterates over all lines within `dist` meters around `coord`.

        No order specified here."""


def path_length(lines: Iterable[Line]) -> float:
    """Length of a path in the map, in meters"""
    return sum([line.length for line in lines])
