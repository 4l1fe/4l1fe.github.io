import sys
from pathlib import Path
from dataclasses import dataclass, field
from functools import partial, lru_cache
from typing import List, Tuple
from enum import Enum
from statistics import median

import toml
import networkx
import typer
import matplotlib.pyplot as plt
from matplotlib import font_manager
from structlog import get_logger, configure, make_filtering_bound_logger
from structlog.contextvars import merge_contextvars
from structlog.dev import ConsoleRenderer, _use_colors, set_exc_info
from structlog.processors import add_log_level, StackInfoRenderer
from benedict import benedict


FONT_FAMILY = 'Roboto'
SIZE_DEFAULT = 40
SIZE_K = 40
TOML_COLOR = 'tab:purple'
ERROR_COLOR = 'tab:red'
FILE_COLOR = 'tab:cyan'
EDGE_COLOR = 'tab:blue'
font_files = font_manager.findSystemFonts(fontpaths=['/usr/local/share/fonts/r'])
for font_file in font_files:
    font_manager.fontManager.addfont(font_file)

logger = get_logger()
cli = typer.Typer()


def strip_home_dir(path) -> Path:
    return path.expanduser().resolve().relative_to(Path.home())


class ErrorTypes(Enum):
    NOT_EXIST = 'No such file.'
    OUT_OF_SCOPE = 'Refer to an outer scope.'


@dataclass
class NodeAttr:
    color: str = TOML_COLOR
    size: int = SIZE_DEFAULT
    error: ErrorTypes = None


@dataclass
class Node:
    """General container for any file type"""
    graph_id: Path = field(init=False)  # relative, unique
    path: Path = field(repr=False)  # absolute
    attrs: NodeAttr = field(repr=True)

    def __post_init__(self):
        if not self.path.is_absolute():
            raise TypeError("Path isn't absolute.")

        self.graph_id = strip_home_dir(self.path)


@dataclass
class TomlNode(Node):
    """Container of toml file type"""
    data: dict = field(repr=False, init=False)  # parsed toml config

    def __post_init__(self):
        super(TomlNode, self).__post_init__()
        self.data = toml.load(self.path)


@dataclass
class RefNode(Node):
    """Can be not a real file"""
    raw_ref: str


class TomlNodeReferences:
    """Search and accumulate all the references in the .toml files"""

    def __init__(self, node: TomlNode):
        self.node = node
        self._refs = list()
        self._log_error = True
        self._log_checks = True

    def get_all(self):
        self._log_error = False
        self._log_checks = False
        return self._check_modify()
        
    def checks_passed(self) -> bool:
        for ref_node in self._check_modify():
            if ref_node.attrs.error:
                return False

        return True
    
    def _traverse_gather_refs(self, source_node, dict_, key, value):
        source_dir = source_node.path.parent
        color = source_node.attrs.color

        if key == 'reference':
            ref_node = node_fabric(value, reference=True, source_dir=source_dir)
            self._refs.append(ref_node)
            logger.debug('One ref added.', node=source_node, reference_node=ref_node)
        elif key == 'references':
            ref_nodes = [node_fabric(v, color, reference=True, source_dir=source_dir) for v in value]
            self._refs.extend(ref_nodes)
            logger.debug('Many refs added.', node=source_node, reference_nodes=ref_nodes)

    # @lru_cache(maxsize=None)
    def _get_all(self) -> list:
        bd = benedict(self.node.data, keypath_separator=None)
        per_node_callback = partial(self._traverse_gather_refs, self.node)
        bd.traverse(per_node_callback)
        return self._refs

    def _check_modify(self):
        for ref_node in self._get_all():
            # todo check ref abs path error. Has to be only relative to source dir
            # todo check out of scope error

            logger_ = logger.bind(node=self.node.graph_id, reference=ref_node.raw_ref)
            flag = ref_node.path.exists()

            if flag and self._log_checks:
                logger_.info("Reference exists.")
            elif not flag:
                ref_node.attrs.error = ErrorTypes.NOT_EXIST
                ref_node.attrs.color = ERROR_COLOR
                if self._log_error:
                    logger_.error("Reference doesn't exist.")

            yield ref_node


def node_fabric(str_or_path, color=None, reference=False, source_dir: Path = None):
    """Cover all the cases of node creation"""
    path = Path(str_or_path)
    attrs = NodeAttr()
    if color:
        attrs.color = color

    if reference:
        abs_path = source_dir.joinpath(str_or_path).resolve()
        node = RefNode(path=abs_path, raw_ref=str_or_path, attrs=attrs)
    elif path.suffix == '.toml':
        node = TomlNode(path=path, attrs=attrs)
    else:
        attrs.color = FILE_COLOR
        node = Node(path=path, attrs=attrs)

    return node


def nodes_from_files(source_dir: Path):
    """Scan folders and create nodes"""

    # @lru_cache(maxsize=None)
    def _cached(path):
        if not path.is_absolute():  # `Folder/path | ~/Folder/path`
            path = path.expanduser().resolve()

        for file in path.rglob('*'):
            if file.is_dir():
                continue

            node = node_fabric(file)

            yield node

    # logger.debug('Cache stats.', func=_cached, stats=_cached.cache_info())
    yield from _cached(source_dir)


def create_graph(nodes, add_edges=True):
    g = networkx.Graph()

    for node in nodes:
        g.add_node(node.graph_id, attrs=node.attrs)

        if add_edges and isinstance(node, TomlNode):
            ref_nodes = TomlNodeReferences(node).get_all()
            for ref_node in ref_nodes:
                g.add_node(ref_node.graph_id, attrs=ref_node.attrs)
                g.add_edge(node.graph_id, ref_node.graph_id)
            logger.debug('Edges added.', edges=g.edges)

    return g


@cli.command()
def check(path: Path):
    """Ensure all the checks are passed"""

    nodes = nodes_from_files(path)
    refs_exist = [TomlNodeReferences(node).checks_passed() for node in nodes if isinstance(node, TomlNode)]
    is_valid = all(refs_exist)

    if is_valid:
        logger.info('Success.')
    else:
        logger.error('Fail.')

    return is_valid
    

@cli.command()
def create_plot(paths: List[Path], output_file="plot.png", relations: bool = False,
                names: bool = False, emphasize: bool = False,  layout: str = 'random', dpi: int = 200,
                title: bool = False):
    """Display files and their references"""

    def make_emphasizing_coefficients(graph_) -> Tuple[dict, dict]:
        """Make the size coefficients depended on neighbors count"""

        node_nbr_counts = {graph_id: len(nbrs) for (graph_id, nbrs) in graph_.adjacency()}
        nbr_median = median(node_nbr_counts.values())
        nbr_cnt_groups_asc = sorted(filter(lambda nbr_count: nbr_count > nbr_median,
                                           set(node_nbr_counts.values())))
        nbr_cnt_groups_k = {group: group / nbr_cnt_groups_asc[0] * SIZE_K for group in nbr_cnt_groups_asc}
        return node_nbr_counts, nbr_cnt_groups_k

    def subplot(path, _layout=None):
        source_nodes = list(nodes_from_files(path))
        logger.debug('Subplot nodes.', subplot=path.name, nodes=source_nodes)

        graph = create_graph(source_nodes, add_edges=relations)
        layout_ = networkx.random_layout(graph)
        if _layout == 'kamada kawai':
            layout_ = networkx.kamada_kawai_layout(graph)
        elif _layout == 'spring':
            layout_ = networkx.spring_layout(graph, k=1)
        elif _layout == 'circular':
            layout_ = networkx.circular_layout(graph)

        colors, sizes = [], []
        groups, coefficients = make_emphasizing_coefficients(graph)
        for graph_id, node_attr in graph.nodes.data('attrs'):
            colors.append(node_attr.color)
            size = node_attr.size
            if emphasize:
                k = coefficients.get(groups[graph_id], 0)
                size = size + k
            sizes.append(size)

        labels = {}
        for graph_id, node_attr in graph.nodes.data('attrs'):
            if not names:
                break

            if not emphasize:  # all are labeled
                labels[graph_id] = graph_id.name
                continue

            if (emphasize and coefficients.get(groups[graph_id])) \
                    or node_attr.error:
                labels[graph_id] = graph_id.name

        networkx.draw(graph, pos=layout_,
                      with_labels=True, labels=labels, verticalalignment='bottom', horizontalalignment='left',
                      node_shape='o', node_size=list(sizes), node_color=list(colors),
                      font_size=8, width=0.2, font_family=FONT_FAMILY, font_color='black',
                      linewidths=0.4, edgecolors='white',
                      bbox={'edgecolor': 'black', 'facecolor': 'white', 'linewidth': 0.2,
                            'boxstyle': 'round', 'alpha': 0.3},
                      edge_color=EDGE_COLOR)  # edges between nodes

    for path in paths:
        check(path)

    for i, source_dir in enumerate(paths, start=1):
        nrows, ncols, idx = len(paths), 1, i
        ax = plt.subplot(nrows, ncols, idx)
        if title:
            title = strip_home_dir(source_dir).name
            ax.set_title(title, font=FONT_FAMILY)
        subplot(source_dir, _layout=layout)

    plt.savefig(output_file, dpi=dpi)


if __name__ == '__main__':
    import logging
    configure(wrapper_class=make_filtering_bound_logger(logging.INFO),
              processors=[
                        merge_contextvars,
                        add_log_level,
                        StackInfoRenderer(),
                        set_exc_info,
                        ConsoleRenderer(
                            colors=_use_colors
                            and sys.stdout is not None
                            and hasattr(sys.stdout, "isatty")
                            and sys.stdout.isatty()
                        ),
                    ])
    cli()
