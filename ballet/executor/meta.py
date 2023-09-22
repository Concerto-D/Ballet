from ballet.assembly.concertod.dependency import DepType
from ballet.executor.reconfiguration import Reconfiguration
from ballet.executor.internal_instruction import InternalInstruction
from ballet.assembly.concertod.component import Component


def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


class WeightedGraph:
    def __init__(self, vertices=(), arcs=(), cluster=None):
        self._graph = dict()
        self._clusters = dict()
        self._shapes = dict()
        self.add_vertices(vertices, cluster=cluster)
        for (v1, v2, w) in arcs:
            self._graph[v1].append((v2, w))

    def __iadd__(self, other):
        for v in other._graph:
            self.add_vertex(v, ignore_already_existing=True)
        for v, trs in other._graph.items():
            self.add_arcs([(v, dest, w, n) for (dest, w, n) in trs])
        for cl, verts in other._clusters.items():
            if cl in self._clusters:
                self._clusters[cl] |= verts
            else:
                self._clusters[cl] = verts
        for v, shape in other._shapes.items():
            self._shapes[v] = shape
        return self

    def add_vertex(self, vertex, cluster=None, ignore_already_existing=False, shape=None):
        if vertex in self._graph:
            if ignore_already_existing:
                return
            else:
                raise Exception("Trying to add vertex %s which is already in the graph!" % str(vertex))
        self._graph[vertex] = []
        if cluster:
            if cluster not in self._clusters:
                self._clusters[cluster] = set()
            self._clusters[cluster].add(vertex)
        if shape:
            self._shapes[vertex] = shape

    def add_vertices(self, vertices, *args, **kwargs):
        for v in vertices:
            self.add_vertex(v, *args, **kwargs)

    def add_arc(self, source, destination, weight, name=""):
        if source not in self._graph or destination not in self._graph:
            raise Exception("Error: one of the two vertices of the arc was not added to the graph!")
        self._graph[source].append((destination, weight, name))

    def add_arcs(self, arcs):
        for a in arcs:
            self.add_arc(*a)

    def get_arcs_from_vertex(self, v):
        """ Returns a list of arcs under the form (destination, weight, name)"""
        from copy import deepcopy
        return deepcopy(list(self._graph[v]))

    def get_vertices(self):
        """ Returns a list of vertices """
        from copy import deepcopy
        return deepcopy(list(self._graph.keys()))

    def get_dot(self,
                f_get_vertex_label=lambda x: str(x),
                f_get_arc_label=lambda n, w: n + ("\n" if n != "" and w != 0 else "") + (str(w) if w != 0 else "")
                ):
        from copy import deepcopy

        working_graph = deepcopy(self._graph)

        identifiers = dict()
        vertices = set(working_graph.keys())
        for source, arcs in working_graph.items():
            for dest, _, _ in arcs:
                vertices.add(dest)
        i = 0
        for v in vertices:
            identifiers[v] = "v%d" % i
            i += 1

        treated_vertices = set()

        gstr = "digraph G {\n"
        gstr += "\trankdir=BT;\n"
        i = 0
        for (cl_name, cl_contents) in self._clusters.items():
            i += 1
            gstr += "\tsubgraph cluster_%d {\n" % i
            gstr += "\t\tcolor = black;\n"
            gstr += "\t\tlabel = \"%s\";\n" % cl_name
            for v in cl_contents:
                if v not in vertices:  # was removed
                    continue
                gstr += "\t\t%s [label=\"%s\"] [shape=%s];\n" % (
                    identifiers[v], f_get_vertex_label(v), self._shapes.get(v, "oval"))
                treated_vertices.add(v)
            for (v1, transitions) in working_graph.items():
                filtered_transitions = []
                for (v2, w, n) in transitions:
                    if v1 in cl_contents and v2 in cl_contents:
                        gstr += "\t\t%s -> %s [label=\"%s\"];\n" % (
                            identifiers[v1], identifiers[v2], f_get_arc_label(n, w))
                    else:
                        filtered_transitions.append((v2, w, n))
                working_graph[v1] = filtered_transitions

            gstr += "\t}\n"

        for v in working_graph:
            if v not in treated_vertices:
                gstr += "\t%s [label=\"%s\"] [shape=%s];\n" % (
                    identifiers[v], f_get_vertex_label(v), self._shapes.get(v, "oval"))

        for (v1, transitions) in working_graph.items():
            for (v2, w, n) in transitions:
                gstr += "\t%s -> %s [label=\"%s\"];\n" % (identifiers[v1], identifiers[v2], f_get_arc_label(n, w))
        gstr += "}\n"
        return gstr

    def save_as_dot(self, filename, *args, **kwargs):
        gstr = self.get_dot(*args, **kwargs)
        with open(filename, "w") as f:
            f.write(gstr)

    def remove_unreachable_from(self, source):
        reached = set()
        lifo = [source]
        while lifo:
            current = lifo.pop()
            reached.add(current)
            for (d, _, _) in self._graph[current]:
                if d not in reached:
                    lifo.append(d)
        not_reached = set(self._graph.keys()) - reached
        for v in not_reached:
            del self._graph[v]
        for v in self._graph:
            self._graph[v] = list(filter(lambda t: t[0] not in not_reached, self._graph[v]))
        return not_reached

    def detect_cycle(self, source_vertex):
        def _dfs(vertex, visited):
            if vertex in visited:
                i = visited.index(vertex)
                cycle = visited[i:] + [vertex]
                return cycle

            for (child, _, _) in self._graph[vertex]:
                r = _dfs(child, visited + [vertex])
                if r:
                    return r
            return None

        return _dfs(source_vertex, [])

    def get_max_distances(self, source_vertex, transitions_lengths):
        def _topological_order():
            unmarked = set(self._graph.keys())
            temporary_marks = set()
            permanent_marks = set()
            vert_list = []

            def __visit(vertex):
                if vertex in permanent_marks:
                    return
                if vertex in temporary_marks:
                    raise Exception("Not a DAG!")
                temporary_marks.add(vertex)
                for (d, _, _) in self._graph[vertex]:
                    __visit(d)
                temporary_marks.remove(vertex)
                permanent_marks.add(vertex)
                vert_list.insert(0, vertex)
                unmarked.discard(vertex)

            while unmarked:
                v = unmarked.pop()
                __visit(v)
            return vert_list

        ordered_verts = _topological_order()
        dist = dict([(v, float("-inf")) for v in self._graph])
        dist[source_vertex] = 0
        for u in ordered_verts:
            for (v, weight, _) in self._graph[u]:
                if not is_number(weight):
                    (c, t) = weight
                    if weight not in transitions_lengths:
                        raise Exception("Error: weight not given for transition %s.%s (key: %s)" % (c, t, weight))
                    weight = transitions_lengths[weight]
                if dist[v] < dist[u] + weight:
                    dist[v] = dist[u] + weight
        return dist

    def get_longest_path_length(self, source_vertex, destination_vertex, transitions_lengths):
        return self.get_max_distances(source_vertex, transitions_lengths)[destination_vertex]

    class MaxFormula:
        def __init__(self, *args):
            self._sum_lists = []
            for sum_list in args:
                self._sum_lists.append(list(sum_list))
            self.simplify()

        def simplify(self):
            new_sum_lists = []
            for sum_list in self._sum_lists:
                for elem in sum_list:
                    if isinstance(elem, WeightedGraph.MaxFormula) and elem.is_singleton():
                        sum_list += elem._sum_lists[0]
                        elem._sum_lists = []
                f_sum_list = list(filter(
                    lambda x: (not x.is_null()) if isinstance(x, WeightedGraph.MaxFormula) else (
                            not is_number(x) or x != 0),
                    sum_list
                ))
                if f_sum_list:
                    new_sum_lists.append(f_sum_list)
            self._sum_lists = new_sum_lists

        def is_singleton(self):
            self.simplify()
            return len(self._sum_lists) == 1

        def is_null(self):
            self.simplify()
            return not bool(self._sum_lists)

        def to_string(self, f_variable_str=lambda x: str(x)):
            def _str_sum_list(sl):
                def __str_elem(e):
                    if is_number(e):
                        return str(e)
                    elif isinstance(e, WeightedGraph.MaxFormula):
                        return e.to_string(f_variable_str)
                    else:
                        return f_variable_str(e)

                return '+'.join([__str_elem(e) for e in sl])

            l = len(self._sum_lists)
            if l == 0:
                return str(0)
            elif l == 1:
                return _str_sum_list(self._sum_lists[0])
            else:
                return "max(" + ",".join([_str_sum_list(sl) for sl in self._sum_lists]) + ")"

        def __str__(self):
            return self.to_string()

        def evaluate(self, values_dict=None):
            if values_dict is None:
                values_dict = dict()

            def _eval_sum_list(sl):
                def __eval_elem(e):
                    if is_number(e):
                        return e
                    elif isinstance(e, WeightedGraph.MaxFormula):
                        return e.evaluate(values_dict)
                    else:
                        if e not in values_dict:
                            raise Exception("Error: no value provided for %s" % str(e))
                        return values_dict[e]

                return sum([__eval_elem(e) for e in sl])

            if len(self._sum_lists) == 0:
                return 0
            else:
                return max([_eval_sum_list(sl) for sl in self._sum_lists])

    def get_longest_path_formula(self, source_vertex, destination_vertex):
        reversed_graph = dict()
        for s, transitions in self._graph.items():
            for d, w, _ in transitions:
                if d not in reversed_graph:
                    reversed_graph[d] = []
                reversed_graph[d].append((s, w))

        def _build_formula_rec(vertex):
            if vertex == source_vertex:
                return 0
            sum_lists = [[w, _build_formula_rec(s)] for (s, w) in reversed_graph[vertex]]
            return WeightedGraph.MaxFormula(*sum_lists)

        mf = _build_formula_rec(destination_vertex)
        if mf == 0:
            mf = WeightedGraph.MaxFormula([])
        return mf


def flatten(list_of_lists):
    from itertools import chain
    return chain(*list_of_lists)


class ComponentPerfAnalyzer:
    def __init__(self, component: Component, name):
        self.component = component
        self.name = name

        self.transitions = dict([(name, (source, destination, behavior)) for (name, source, destination, behavior) in
                                 self.component.get_transitions()])
        self.ports = dict(self.component.get_ports())  # (name, type)
        self.groups_contents = self.component.get_groups()
        self.groups = dict([(group_name, (self.group_entry(group_name), self.group_exit(group_name))) for group_name in
                            self.groups_contents])
        self.bindings = self.component.get_bindings()  # dict(element, [port])

        self.treated_elements = set()
        self.treated_during_behavior = dict()
        self.active_places = set()
        self.old_places = set()

        self.graph = WeightedGraph()

    def v(self, element, vertex_type):
        return self.name, element, vertex_type

    def group_entry(self, group_name):
        group_contents = self.groups_contents[group_name]
        entry_elements = set()
        for (name, (source, destination, _)) in self.transitions.items():
            if destination in group_contents and source not in group_contents:
                if name in group_contents:
                    entry_elements.add(name)
                else:
                    entry_elements.add(destination)
        return entry_elements

    def group_exit(self, group_name):
        group_content = self.groups_contents[group_name]
        exit_elements = set()
        for (name, (source, destination, _)) in self.transitions.items():
            if source in group_content and destination not in group_content:
                if name in group_content:
                    exit_elements.add(name)
                else:
                    exit_elements.add(source)
        return exit_elements

    def get_port_vertices(self, elem_name, f_type_filter, f_port_vertex):
        bindings = self.bindings.get(elem_name, [])
        for (group_name, (group_entry, group_exit)) in self.groups.items():
            if elem_name in group_entry | group_exit:
                bindings += self.bindings[group_name]
        port_vertices = []
        for port in bindings:
            p_type = self.ports[port]
            if f_type_filter(p_type):
                port_vertex = f_port_vertex(port)
                self.graph.add_vertex(port_vertex, ignore_already_existing=True, shape="diamond")
                port_vertices.append(port_vertex)
        return port_vertices

    def get_provide_port_stop_vertices(self, elem_name):
        return self.get_port_vertices(
            elem_name,
            f_type_filter=lambda t: t == DepType.PROVIDE,
            f_port_vertex=self.port_stop_vertex
        )

    def get_use_port_stop_vertices(self, elem_name):
        return self.get_port_vertices(
            elem_name,
            f_type_filter=lambda t: t == DepType.USE,
            f_port_vertex=self.port_stop_vertex
        )

    def get_provide_port_start_vertices(self, elem_name):
        return self.get_port_vertices(
            elem_name,
            f_type_filter=lambda t: t == DepType.PROVIDE or t == DepType.DATA_PROVIDE,
            f_port_vertex=self.port_start_vertex
        )

    def get_use_port_start_vertices(self, elem_name):
        return self.get_port_vertices(
            elem_name,
            f_type_filter=lambda t: t == DepType.USE or t == DepType.DATA_USE,
            f_port_vertex=self.port_start_vertex
        )

    def get_elem_identifier(self, elem_name):
        if elem_name in self.treated_during_behavior:
            return self.treated_during_behavior[elem_name]

        i = 1
        while (elem_name, i) in self.treated_elements:
            i += 1
        eid = (elem_name, i)
        self.treated_during_behavior[elem_name] = eid
        self.treated_elements.add(eid)
        return eid

    def treat_place(self, place_name, entry=False):
        new = place_name not in self.treated_during_behavior
        pid = self.get_elem_identifier(place_name)
        place_vertex = self.place_place_vertex(pid)
        leaving_vertex = self.place_leaving_vertex(pid)
        if new:
            self.graph.add_vertex(place_vertex, cluster=self.name, shape="box")
            self.graph.add_vertex(leaving_vertex, cluster=self.name, shape="triangle")
            self.graph.add_arc(place_vertex, leaving_vertex, 0)

            if entry:
                provide_port_start_vertices = self.get_provide_port_start_vertices(place_name)
                self.graph.add_arcs([(place_vertex, ppsv, 0) for ppsv in provide_port_start_vertices])

                use_port_start_vertices = self.get_use_port_start_vertices(place_name)
                self.graph.add_arcs([(upsv, place_vertex, 0) for upsv in use_port_start_vertices])

            provide_port_stop_vertices = self.get_provide_port_stop_vertices(place_name)
            self.graph.add_arcs([(ppsv, leaving_vertex, 0) for ppsv in provide_port_stop_vertices])

            use_port_stop_vertices = self.get_use_port_stop_vertices(place_name)
            self.graph.add_arcs([(leaving_vertex, upsv, 0) for upsv in use_port_stop_vertices])

        return place_vertex, leaving_vertex

    def treat_active_places(self, entry=False):
        active_place_vertices = dict()
        active_leaving_vertices = dict()
        for p in self.active_places:
            place_vertex, leaving_vertex = self.treat_place(p, entry)
            active_place_vertices[p] = place_vertex
            active_leaving_vertices[p] = leaving_vertex

        self.active_place_vertices = active_place_vertices
        self.active_leaving_vertices = active_leaving_vertices

    def treat_transition(self, transition_name):
        tid = self.get_elem_identifier(transition_name)
        beginning_vertex = self.transition_beginning_vertex(tid)
        end_vertex = self.transition_end_vertex(tid)

        (source, dest, _) = self.transitions[transition_name]
        source_leaving_vertex = self.old_active_leaving_vertices[source]
        dest_place_vertex = self.active_place_vertices[dest]

        self.graph.add_vertices([beginning_vertex, end_vertex], cluster=self.name, shape="point")
        self.graph.add_arc(beginning_vertex, end_vertex, (self.name, transition_name))
        self.graph.add_arc(source_leaving_vertex, beginning_vertex, 0)
        self.graph.add_arc(end_vertex, dest_place_vertex, 0)

        provide_port_start_vertices = self.get_provide_port_start_vertices(transition_name)
        self.graph.add_arcs([(beginning_vertex, ppsv, 0) for ppsv in provide_port_start_vertices])

        use_port_start_vertices = self.get_use_port_start_vertices(transition_name)
        self.graph.add_arcs([(upsv, beginning_vertex, 0) for upsv in use_port_start_vertices])

        provide_port_stop_vertices = self.get_provide_port_stop_vertices(transition_name)
        self.graph.add_arcs([(ppsv, end_vertex, 0) for ppsv in provide_port_stop_vertices])

        use_port_stop_vertices = self.get_use_port_stop_vertices(transition_name)
        self.graph.add_arcs([(end_vertex, upsv, 0) for upsv in use_port_stop_vertices])

    def initialize(self, initial_places=()):
        self.active_places = set(initial_places)
        self.treated_during_behavior = dict()
        if not self.active_places:
            self.active_places = set(self.component.get_initial_places())
        self.treat_active_places()
        return self.active_place_vertices.values()

    def get_next(self, behavior):
        next_places = set(self.active_places)
        places_left = set()
        places_arrived = set()
        next_transitions = set()
        for p in self.active_places:
            for (name, (src, dst, bhv)) in self.transitions.items():
                if bhv == behavior and src == p:
                    places_left.add(src)
                    places_arrived.add(dst)
                    if name not in self.treated_during_behavior:
                        next_transitions.add(name)
        next_places -= places_left
        next_places |= places_arrived
        return next_places, next_transitions

    def push_b(self, behavior):
        self.treated_during_behavior = dict()
        initial_active_place_vertices = self.active_place_vertices
        trs = ["something"]  # just so that bool(trs) evaluates to True the first time
        while trs:
            self.old_places = self.active_places
            self.old_active_leaving_vertices = self.active_leaving_vertices
            aps, trs = self.get_next(behavior)
            self.active_places = aps
            self.treat_active_places(entry=True)
            for tr in trs:
                self.treat_transition(tr)
        return initial_active_place_vertices.values()

    def wait(self):
        return self.active_place_vertices.values()

    def place_place_vertex(self, place_name):
        return self.v(place_name, "place")

    def place_leaving_vertex(self, place_name):
        return self.v(place_name, "leaving")

    def transition_beginning_vertex(self, transition_name):
        return self.v(transition_name, "beginning")

    def transition_end_vertex(self, transition_name):
        return self.v(transition_name, "end")

    def port_start_vertex(self, port_name):
        return self.v(port_name, "start")

    def port_stop_vertex(self, port_name):
        return self.v(port_name, "stop")

    def source_vertex(self):
        return self.v(None, "source")

    def sink_vertex(self):
        return self.v(None, "sink")

    def get_graph(self):
        return self.graph


class ReconfigurationPerfAnalyzer:
    def __init__(self, reconfiguration: Reconfiguration, existing_components=(), debug=False):
        self.reconfiguration = reconfiguration
        self.source_vertex = "source"
        self._graph = WeightedGraph([self.source_vertex])
        self._component_analyzers = dict()

        self._latest_synchro = self.source_vertex
        self._latest_wait_id = 0

        for (name, component, active_places) in existing_components:
            ca = ComponentPerfAnalyzer(component, name)
            ca.initialize(active_places)
            self._component_analyzers[name] = ca

        self._handle_instructions()
        self._generate_total_graph(debug=debug)

    def _handle_instructions(self):
        for ri in self.reconfiguration._get_instructions():
            itype = ri.get_type()
            iargs = ri.get_args()
            if itype == InternalInstruction.Type.ADD:
                name = iargs["name"]
                component = iargs["comp"]
                ca = ComponentPerfAnalyzer(component, name)
                ca.initialize()
                self._component_analyzers[name] = ca
            elif itype == InternalInstruction.Type.CONNECT:
                comp1_name = iargs['comp1_name']
                dep1_name = iargs['dep1_name']
                comp2_name = iargs['comp2_name']
                dep2_name = iargs['dep2_name']
                dep1_type = self._component_analyzers[comp1_name].ports[dep1_name]
                if dep1_type == DepType.PROVIDE or dep1_type == DepType.DATA_PROVIDE:
                    provider = comp1_name
                    provide_port = dep1_name
                    user = comp2_name
                    use_port = dep2_name
                else:
                    provider = comp2_name
                    provide_port = dep2_name
                    user = comp1_name
                    use_port = dep1_name
                if dep1_type == DepType.DATA_USE or dep1_type == DepType.DATA_PROVIDE:
                    stopping = False
                else:
                    stopping = True

                provide_start = self._component_analyzers[provider].port_start_vertex(provide_port)
                use_start = self._component_analyzers[user].port_start_vertex(use_port)
                self._graph.add_vertices([provide_start, use_start], ignore_already_existing=True)
                self._graph.add_arc(provide_start, use_start, 0)
                if self._latest_synchro != self.source_vertex:
                    self._graph.add_arc(self._latest_synchro, provide_start, 0)
                if stopping:
                    provide_stop = self._component_analyzers[provider].port_stop_vertex(provide_port)
                    use_stop = self._component_analyzers[user].port_stop_vertex(use_port)
                    self._graph.add_vertices([provide_stop, use_stop], ignore_already_existing=True)
                    self._graph.add_arc(use_stop, provide_stop, 0)

            elif itype == InternalInstruction.Type.PUSH_B:
                component_name = iargs['component_name']
                behavior = iargs['behavior']
                start_vertices = self._component_analyzers[component_name].push_b(behavior)
                self._graph.add_vertices(start_vertices, ignore_already_existing=True)
                for v in start_vertices:
                    self._graph.add_arc(self._latest_synchro, v, 0)

            elif itype == InternalInstruction.Type.WAIT:
                self._latest_wait_id += 1
                wait_s = "wait_%d" % self._latest_wait_id
                self._graph.add_vertex(wait_s)
                self._graph.add_arc(self._latest_synchro, wait_s, 0)
                self._latest_synchro = wait_s
                component_name = iargs['component_name']
                idle_vertices = self._component_analyzers[component_name].wait()
                self._graph.add_vertices(idle_vertices, ignore_already_existing=True)
                for v in idle_vertices:
                    self._graph.add_arc(v, wait_s, 0)

            elif itype == InternalInstruction.Type.WAIT_ALL:
                self._latest_wait_id += 1
                wait_s = "wait_all_%d" % self._latest_wait_id
                self._graph.add_vertex(wait_s)
                self._graph.add_arc(self._latest_synchro, wait_s, 0)
                self._latest_synchro = wait_s
                for component_analyzer in self._component_analyzers.values():
                    idle_vertices = component_analyzer.wait()
                    self._graph.add_vertices(idle_vertices, ignore_already_existing=True)
                    for v in idle_vertices:
                        self._graph.add_arc(v, wait_s, 0)

    def _generate_total_graph(self, debug=False):
        for component_analyzer in self._component_analyzers.values():
            self._graph += component_analyzer.get_graph()
        removed = self._graph.remove_unreachable_from(self.source_vertex)
        if debug and removed:
            print("Debug: unreachable vertices were removed from the graph: %s" % removed)

    def get_graph(self):
        return self._graph

    def get_exec_time_formula(self):
        return self._graph.get_longest_path_formula(self.source_vertex, self._latest_synchro)

    def get_exec_time(self, transitions_durations):
        return self._graph.get_longest_path_length(self.source_vertex, self._latest_synchro, transitions_durations)

    def get_gantt_chart(self, transitions_durations):
        from concerto.exporters.gantt_chart import GanttChart
        gc = GanttChart(default_show_behaviors=False)
        vertices_distances = self._graph.get_max_distances(self.source_vertex, transitions_durations)
        for source in vertices_distances:
            try:
                component_name, transition_info, arc_type = source
                if arc_type == "beginning":
                    transition_name, nb = transition_info
                    for _, weight, name in self._graph.get_arcs_from_vertex(source):
                        if not is_number(weight):
                            (c, t) = weight
                            if weight not in transitions_durations:
                                raise Exception("Error: weight not given for transition %s.%s (key: %s)" % (c, t,
                                                                                                            weight))
                            weight = transitions_durations[weight]
                        gc.add_transition(component_name,
                                          "?",
                                          transition_name,
                                          vertices_distances[source],
                                          vertices_distances[source]+weight)
            except ValueError:
                pass

        return gc
