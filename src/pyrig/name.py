import copy
import six
import re
import json
import logging
import os

from maya import cmds

LOG = logging.getLogger(__name__)

NODE_TYPE_REMAP = {}
FILE_PATH = os.path.dirname(os.path.realpath(__file__))
NODE_TYPE_REMAP_FILE = os.path.join(
    FILE_PATH, "resources", "node_type_remap.json"
)
with open(NODE_TYPE_REMAP_FILE, "r") as stream:
    NODE_TYPE_REMAP = json.load(stream)


def validate_name(name, node_type=None):
    """"""
    if isinstance(name, six.string_types):
        name = name.split("|")[-1]
        name = name.split(Name.SEPARATOR)
    if isinstance(name, (list, tuple)):
        name = Name(name)
    if not name:
        name = Name([find_next_available_name(node_type)])
    if not isinstance(name, Name):
        raise TypeError(
            "Use lists or the pyrig.name.Name class to construct names."
        )

    return copy.copy(name)

def find_next_available_name(value, index=None):
    """Recursive."""
    # Strip trailing numbers.
    cache_value = copy.copy(value)
    value.rstrip("1234567890")

    # Append index if specified.
    if index:
        value = "{0}{1}".format(value, index)
    if cmds.objExists(value):
        # Configure index.
        index = index or 0
        index += 1
        return find_next_available_name(cache_value, index)
    return value

def transpose_node_type(node_type):
    """"""
    return NODE_TYPE_REMAP.get(node_type, node_type)

class Name(object):
    """"""

    SEPARATOR = "_"

    def __init__(self, *args):
        """"""
        # Convert args to list.
        self._tokens = []
        self._node = None

        # Parse the inputs correctly.
        for part in list(args):
            if isinstance(part, (list, tuple)):
                self._tokens.extend(part)
            elif isinstance(part, six.string_types) and self.SEPARATOR in part:
                self._tokens.extend(part.split(self.SEPARATOR))
            else:
                self._tokens.append(part)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.to_string())

    def __str__(self):
        return self.to_string()

    def __nonzero__(self):
        return bool(self.to_string())

    def __bool__(self):
        return self.__nonzero__()

    def __add__(self, other):
        return self.to_string() + other

    def __getitem__(self, request):
        """"""
        return self._tokens[request]

    def __setitem__(self, index, value):
        self._tokens[index] = value
        self.update_node()

    def __copy__(self):
        """"""
        return Name(*self._tokens)
    
    def copy(
        self, append=None, suffix=None, insert=None, extend=None, shape=False
    ):
        """Copy the current name and return it."""
        name = copy.copy(self)
        if insert and isinstance(insert, (tuple, list)):
            name.tokens.insert(*insert)
        if extend and len(extend) == 2:
            name.tokens[extend[0]] += extend[1]
        if len(name.tokens) == 1 and suffix:
            name.append(suffix)
        elif suffix:
            name.suffix = suffix
        if append:
            name.append(append)
        if len(name.tokens) == 1 and shape is True:
            name.suffix += "Shape"
        elif shape is True:
            name.suffix += "Shape"
        return name

    @property
    def node(self):
        """"""
        return self._node

    @node.setter
    def node(self, value):
        self._node = value

    @property
    def tokens(self):
        """"""
        return self._tokens

    @property
    def suffix(self):
        """"""
        return self._tokens[-1]

    @suffix.setter
    def suffix(self, value):
        self.__setitem__(-1, value)

    def to_string(self):
        """"""
        return self.SEPARATOR.join([str(part) for part in self.tokens])

    def update_node(self):
        """"""
        if self.node:
            self.node.name = self

    def append_type(self):
        """"""
        type_suffix = transpose_node_type(self._node.node_type)
        if self.suffix != type_suffix:
            self.append(type_suffix)

    def append(self, item):
        """"""
        self._tokens.append(item)
        self.update_node()

class AttributName(object):
    """"""

    SEPARATOR = "."

    def __init__(self, *args):
        """"""
        # Convert args to list.
        self._tokens = []
        self._node = None

        # Parse the inputs correctly.
        for part in list(args):
            if isinstance(part, (list, tuple)):
                self._tokens.extend([str(item) for item in part])
            elif isinstance(part, six.string_types) and self.SEPARATOR in part:
                self._tokens.extend(part.split(self.SEPARATOR))
            else:
                self._tokens.append(str(part))

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.to_string())

    def __str__(self):
        return self.to_string()

    def __nonzero__(self):
        return bool(self.to_string())

    def __bool__(self):
        return self.__nonzero__()

    def __add__(self, other):
        return self.to_string() + other

    def __getitem__(self, request):
        """"""
        return AttributName(self._tokens[request])

    def __setitem__(self, index, value):
        self._tokens[index] = str(value)

    def __copy__(self):
        """"""
        return AttributName(*self._tokens)

    @property
    def node(self):
        """"""
        return self._node

    @node.setter
    def node(self, value):
        self._node = value

    @property
    def tokens(self):
        """"""
        return self._tokens
    
    @property
    def plug(self):
        """"""
        return "{}.{}".format(self.node, self.to_string())
    
    @property
    def index(self):
        """"""
        index = None
        enclose_index = re.findall("\[[0-9]+\]", self._tokens[-1])
        if enclose_index:
            index = int(re.findall("[0-9]+", enclose_index[0])[0])
        return index
    
    @property
    def nice(self):
        """"""
        try:
            return cmds.attributeName(self.plug, nice=True, leaf=True)
        except:
            return self.to_string()

    @property
    def short(self):
        """"""
        try:
            cmds.attributeName(self.plug, short=True, leaf=True)
        except:
            return self.to_string()

    @property
    def long(self):
        """"""
        try:
            cmds.attributeName(self.plug, long=True, leaf=True)
        except:
            return self.to_string()

    def to_string(self):
        """"""
        return self.SEPARATOR.join(self.tokens)
    
    def unindexted(self):
        """"""
        if not self.index:
            return self.to_string()
        unindexted =  self._tokens[-1].replace("[{}]".format(self.index), "")
        return self.SEPARATOR.join(self.tokens[:-1] + unindexted)
