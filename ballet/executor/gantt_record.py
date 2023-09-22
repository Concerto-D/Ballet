from ballet.executor.gnuplot.gnuplot_gantt import gnuplot_file_from_list


class GanttRecord:
    START = 0
    STOP = 1
    CHANGE_BEHAVIOR = 2

    def __init__(self):
        self.log = []

    def start_transition(self, component, behavior, transition, time):
        self.log.append((self.START, component, behavior, transition, time))

    def stop_transition(self, component, behavior, transition, time):
        self.log.append((self.STOP, component, behavior, transition, time))

    def push_b(self, component, behavior, time):
        self.log.append((self.CHANGE_BEHAVIOR, component, behavior, None, time))

    def dump(self, file_name):
        import csv
        file = open(file_name, "w")

        fieldnames = ['action', 'component', 'behavior', 'transition', 'time']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for (action, component, behavior, transition, time) in self.log:
            row_dict = {
                'action': action,
                'component': component,
                'behavior': behavior,
                'transition': transition,
                'time': time
            }
            writer.writerow(row_dict)

        file.close()

    def _get_ordered_tuples(self):
        transitions = []
        push_bs = []

        max_time = 0.0

        if len(self.log) is 0:
            print("Not exporting Gnuplot: empty log.")
            return

        temp_dict = {}
        (_, _, _, _, min_time) = self.log[0]
        for (action, component, behavior, transition, time) in self.log:
            if action is self.START:
                if (component, behavior, transition) in temp_dict:
                    raise Exception("GanttChart: error during export to gnuplot: action already started")
                start_time = time - min_time
                temp_dict[(component, behavior, transition)] = start_time
                if start_time > max_time:
                    max_time = start_time
            elif action is self.STOP:
                if (component, behavior, transition) not in temp_dict:
                    raise Exception("GanttChart: error during export to gnuplot: action finished before being started")
                start_time = temp_dict[(component, behavior, transition)]
                end_time = time - min_time
                transitions.append((component, behavior, start_time, end_time, transition))
                if end_time > max_time:
                    max_time = end_time
                del temp_dict[(component, behavior, transition)]
            else:
                start_time = time - min_time
                push_bs.append((component, start_time, behavior))
                if start_time > max_time:
                    max_time = start_time

        next_cb_dict = {}
        new_push_bs = []
        for (component, start_time, behavior) in reversed(push_bs):
            if component in next_cb_dict:
                end_time = next_cb_dict[component]
            else:
                end_time = max_time
            if behavior is not None:
                new_push_bs.insert(0, (component, start_time, end_time, behavior))
            next_cb_dict[component] = start_time

        transitions.sort()
        new_push_bs.sort()

        return transitions, new_push_bs

    def get_formatted(self):
        (transitions, push_bs) = self._get_ordered_tuples()

        to_return = {
            "transitions": [],
            "behaviors": []
        }

        if len(transitions) > 0:
            (old_component, old_behavior, _, _, _) = transitions[0]
            component_set = []
            behavior_set = []
            for (component, behavior, start_time, end_time, transition) in transitions:
                if (component is not old_component) or (behavior is not old_behavior):
                    component_set.append({"behavior": old_behavior, "transitions": behavior_set})
                    behavior_set = []
                if component is not old_component:
                    to_return["transitions"].append({"component": old_component, "behaviors": component_set})
                    component_set = []
                behavior_set.append({"transition": transition, "start": start_time, "end": end_time})
                old_behavior = behavior
                old_component = component
            component_set.append({"behavior": old_behavior, "transitions": behavior_set})
            to_return["transitions"].append({"component": old_component, "behaviors": component_set})

        if len(push_bs) > 0:
            (old_component, _, _, _) = push_bs[0]
            component_set = []
            for (component, start_time, end_time, behavior) in push_bs:
                if component is not old_component:
                    to_return["behaviors"].append({"component": old_component, "behaviors": component_set})
                component_set.append({"behavior": behavior, "start": start_time, "end": end_time})
                old_component = old_component
            to_return["behaviors"].append({"component": old_component, "behaviors": component_set})

        return to_return

    def export_json(self, file_name):
        from json import dump
        with open(file_name, "w") as f:
            dump(self.get_formatted(), f, indent='\t')

    def get_gantt_chart(self):
        from concerto.exporters.gantt_chart import GanttChart as ExpGanttChart
        egc = ExpGanttChart([(c, b, tn, st, et) for (c, b, st, et, tn) in self._get_ordered_tuples()[0]])
        return egc

    @staticmethod
    def export_gnuplot_from_tuples(transitions, push_bs, file_name, title):
        tuple_list = []
        push_bs_dict = {}

        for (component, start_time, end_time, behavior) in push_bs:
            if component not in push_bs_dict:
                push_bs_dict[component] = []
            push_bs_dict[component].append((start_time, end_time, behavior))

        for (component, behavior, start_time, end_time, transition) in transitions:
            if component in push_bs_dict:
                cn = component.replace("_", "\\\\\\_")
                for (s, e, b) in push_bs_dict[component]:
                    tuple_list.append((cn, s, e))
                del push_bs_dict[component]
            name = "%s.%s.%s" % (component, behavior, transition)
            name = name.replace("_", "\\\\\\_")
            tuple_list.append((name, start_time, end_time))

        for c in push_bs_dict:
            cn = c.replace("_", "\\\\\\_")
            for (s, e, b) in push_bs_dict[c]:
                tuple_list.append((cn, s, e))

        gnuplot_file_from_list(tuple_list, file_name, title)

    def export_gnuplot(self, file_name, title=''):
        (transitions, push_bs) = self._get_ordered_tuples()
        self.export_gnuplot_from_tuples(transitions, push_bs, file_name, title)

    @staticmethod
    def formatted_to_ordered_tuples(formatted, min_time=0., max_time=float('inf'), components_to_remove=()):
        transitions = []
        push_bs = []
        for c_block in formatted["transitions"]:
            component = c_block["component"]
            for b_block in c_block["behaviors"]:
                behavior = b_block["behavior"]
                for t_block in b_block["transitions"]:
                    transition = t_block["transition"]
                    start = t_block["start"]
                    end = t_block["end"]
                    if start >= min_time and end <= max_time and component not in components_to_remove:
                        transitions.append((component, behavior, start - min_time, end - min_time, transition))
        for c_block in formatted["behaviors"]:
            component = c_block["component"]
            for b_block in c_block["behaviors"]:
                behavior = b_block["behavior"]
                start = b_block["start"]
                end = b_block["end"]
                if start >= min_time and end <= max_time and component not in components_to_remove:
                    push_bs.append((component, start - min_time, end - min_time, behavior))

        transitions.sort()
        push_bs.sort()

        return transitions, push_bs

    @staticmethod
    def json_to_gnuplot(json_file_name, gnuplot_file_name, title='', min_time=0., max_time=float('inf'),
                        components_to_remove=()):
        from json import load
        with open(json_file_name) as f:
            formatted = load(f)
        transitions, push_bs = GanttRecord.formatted_to_ordered_tuples(formatted, min_time=min_time, max_time=max_time,
                                                                       components_to_remove=components_to_remove)
        GanttRecord.export_gnuplot_from_tuples(transitions, push_bs, gnuplot_file_name, title)
