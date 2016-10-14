import re
import random
import inspect
import hashlib
import colorsys
import pygraphviz as pgv

path_regex = re.compile(r'site-packages\/(\S+?)\/')


class FrameGraph(object):

    def __init__(self, *args, **kwargs):
        self._graph = pgv.AGraph(*args, **kwargs)
        self._subgraphs = {}
        self._num_edges = 0
        self._color_mapping = {}

    def _get_id_from_frame_record(self, frame_record):
        frame, filename, _, name, _, _ = frame_record
        firstlineno = frame.f_code.co_firstlineno
        raw_str = '{0}:{1}:{2}'.format(filename, firstlineno, name)
        return hashlib.sha1(raw_str).hexdigest()

    def _generate_color(self):
        r, g, b = colorsys.hls_to_rgb(random.random(), 0.5, 0.5)
        hex_r = hex(int(r * 255))[2:].zfill(2)
        hex_g = hex(int(g * 255))[2:].zfill(2)
        hex_b = hex(int(b * 255))[2:].zfill(2)
        color = '#{0}{1}{2}'.format(hex_r, hex_g, hex_b)
        return color

    def _get_color_of_subgraph(self, subgraph):
        match = path_regex.search(subgraph)
        if match:
            token = match.group(1)
            if token not in self._color_mapping:
                self._color_mapping[token] = self._generate_color()
            color = self._color_mapping[token]
        else:
            color = '#000000'
        return color

    def add_edge(self, start, end):
        self._num_edges += 1

        self.add_node(start)
        self.add_node(end)

        _, _, lineno, _, _, _ = start

        start_id = self._get_id_from_frame_record(start)
        end_id = self._get_id_from_frame_record(end)

        self._graph.add_edge(
            start_id,
            end_id,
            label='#{0} at {1}'.format(self._num_edges, lineno)
        )

    def add_node(self, frame_record):
        frame, filename, _, name, _, _ = frame_record
        firstlineno = frame.f_code.co_firstlineno
        self.add_subgraph(filename)

        node_id = self._get_id_from_frame_record(frame_record)
        if node_id not in self._subgraphs[filename][1]:
            color = self._subgraphs[filename][2]
            self._subgraphs[filename][0].add_node(
                node_id,
                label='{0}:{1}'.format(firstlineno, name),
                color=color
            )
            self._subgraphs[filename][1].add(node_id)

    def add_subgraph(self, name):
        if name not in self._subgraphs:
            color = self._get_color_of_subgraph(name)

            subgraph = self._graph.add_subgraph(
                name='cluster' + name,
                label=name,
                color=color
            )
            self._subgraphs[name] = (subgraph, set(), color)

    def draw(self, *args, **kwargs):
        self._graph.draw(*args, **kwargs)

    def close(self):
        self._graph.close()


def figure_frame(out='figure.png'):
    stack = list(reversed(inspect.stack()))
    graph = FrameGraph(strict=False, directed=True)

    try:
        for index, start in enumerate(stack[:-1]):
            end = stack[index + 1]
            graph.add_edge(start, end)

        if out:
            graph.draw(out, prog='dot')
            graph.close()
    finally:
        del stack, graph
