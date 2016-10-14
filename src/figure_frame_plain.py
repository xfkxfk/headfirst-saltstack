import inspect
import hashlib
import pygraphviz as pgv


class FrameGraph(object):

    def __init__(self, *args, **kwargs):
        self._graph = pgv.AGraph(*args, **kwargs)
        self._subgraphs = {}
        self._num_edges = 0

    def _get_id_from_frame_record(self, frame_record):
        frame, filename, _, name, _, _ = frame_record
        firstlineno = frame.f_code.co_firstlineno
        raw_str = '{0}:{1}:{2}'.format(filename, firstlineno, name)
        return hashlib.sha1(raw_str).hexdigest()

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
            self._subgraphs[filename][0].add_node(
                node_id,
                label='{0}:{1}'.format(firstlineno, name)
            )
            self._subgraphs[filename][1].add(node_id)

    def add_subgraph(self, name):
        if name not in self._subgraphs:
            subgraph = self._graph.add_subgraph(
                name='cluster' + name,
                label=name
            )
            self._subgraphs[name] = (subgraph, set())

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

