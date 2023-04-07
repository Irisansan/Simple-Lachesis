from input_to_dag import convert_input_to_DAG
import glob
import networkx as nx
from graph_results import graph_results
import os
from collections import deque


class Event:
    def __init__(self, id, seq, creator, parents):
        self.id = id
        self.seq = seq
        self.creator = creator
        self.parents = parents
        self.lowest_events_vector = {}
        self.highest_events_observed_by_event = {}


class Lachesis:
    def __init__(self, validator=None):
        self.frame = 1
        self.frame_border_times = [0]
        self.block = 1
        self.root_set_validators = {}
        self.root_set_nodes = {}
        self.election_votes = {}
        self.frame_to_decide = 1
        self.cheater_list = set()
        self.validators = set()
        self.validator_weights = {}
        self.time = 0
        self.local_dag = nx.DiGraph()
        self.timestep_nodes = []
        self.forkless_cause_set = set()
        self.decided_roots = {}
        self.atropos_roots = {}

    def quorum(self, frame_number):
        return (
            2
            * sum(
                [
                    self.validator_weights[x]
                    for x in self.root_set_validators[frame_number]
                ]
            )
            // 3
            + 1
        )

    def highest_events_observed_by_event(self, node):
        direct_parent = None
        for parent_id in node.parents:
            parent = self.local_dag.nodes[parent_id]["event"]
            if parent.creator == node.creator:
                direct_parent = parent
                break

        node.highest_events_observed_by_event = (
            direct_parent.highest_events_observed_by_event.copy()
            if direct_parent
            else {}
        )

        for target_id in node.parents:
            target = self.local_dag.nodes[target_id]["event"]

            if (
                (target.creator, target.seq)
                not in node.highest_events_observed_by_event
                or target.seq > node.highest_events_observed_by_event[target.creator]
            ):
                node.highest_events_observed_by_event[target.creator] = target.seq

    def detect_forks(self, event):
        for parent_id in event.parents:
            parent = self.local_dag.nodes[parent_id]["event"]
            if parent.creator == event.creator and parent.seq == event.seq:
                self.cheater_list.add(event.creator)
                self.validator_weights[event.creator] = 0
                break

    def forkless_cause(self, event_a, event_b):
        if event_a.id[0] in self.cheater_list or event_b.id[0] in self.cheater_list:
            return False

        a = event_a.highest_events_observed_by_event
        b = event_b.lowest_events_vector

        yes = 0
        for validator, seq in a.items():
            if validator in b and b[validator]["seq"] <= seq:
                yes += self.validator_weights[validator]

        return yes > self.quorum(self.frame)

    def set_lowest_events_vector(self, event):
        self.lowest_events_vector = {}
        parents = deque(event.parents)

        while parents:
            parent_id = parents.popleft()
            parent = self.local_dag.nodes[parent_id]["event"]
            parent_vector = parent.lowest_events_vector

            if event.creator not in parent_vector:
                parent_vector[event.creator] = {"event_id": event.id, "seq": event.seq}

                if parent.creator != event.creator:
                    parents.extend(parent.parents)

    def check_for_roots(self, event):
        if event.seq == 1:
            return True, 1
        else:
            frame_to_add = None
            if (self.frame == 1 and self.time >= 3) or (
                self.frame > 1
                and len(self.root_set_validators[self.frame])
                >= len(self.root_set_validators[self.frame - 1])
                and event.creator in self.root_set_validators[self.frame]
            ):
                forkless_cause_current_frame = self.forkless_cause_quorum(
                    event, self.quorum(self.frame), self.frame
                )
                if forkless_cause_current_frame:
                    frame_to_add = self.frame + 1
            elif (
                self.frame > 1
                and event.creator not in self.root_set_validators[self.frame]
            ):
                forkless_cause_previous_frame = self.forkless_cause_quorum(
                    event, self.quorum(self.frame - 1), self.frame - 1
                )
                if forkless_cause_previous_frame:
                    frame_to_add = self.frame

            if frame_to_add is not None:
                return True, frame_to_add
            return False, None

    def process_event(self, event, node):
        self.highest_events_observed_by_event(event)
        self.set_lowest_events_vector(event)
        self.detect_forks(event)

        is_root, target_frame = self.check_for_roots(event)
        if is_root:
            if target_frame not in self.root_set_validators:
                self.root_set_validators[target_frame] = set()
            if target_frame not in self.root_set_nodes:
                self.root_set_nodes[target_frame] = set()

            self.frame = target_frame

            # Add new root set validators and nodes for the incremented frame
            if self.frame not in self.root_set_validators:
                self.root_set_validators[self.frame] = set()
            if self.frame not in self.root_set_nodes:
                self.root_set_nodes[self.frame] = set()

            self.root_set_validators[target_frame].add(event.creator)
            self.root_set_nodes[target_frame].add(event.id)

            self.atropos_voting(event.id)

    def forkless_cause_quorum(self, event, quorum, frame_number):
        forkless_cause_count = 0
        current_frame_roots = self.root_set_nodes[frame_number]

        for root in current_frame_roots:
            root_event = self.local_dag.nodes[root]["event"]
            # print(root_event.id, event.id)
            # print(event.lowest_events_vector)
            # print(event.highest_events_observed_by_event)
            if self.forkless_cause(event, root_event):
                forkless_cause_count += self.validator_weights[root_event.creator]

        return forkless_cause_count >= quorum

    def atropos_voting(self, new_root):
        candidates = self.root_set_nodes[self.frame_to_decide]
        for candidate in candidates:
            if self.frame_to_decide not in self.election_votes:
                self.election_votes[self.frame_to_decide] = {}
            if (new_root, candidate) not in self.election_votes[self.frame_to_decide]:
                vote = None  # Initialize the vote variable
                if self.frame == self.frame_to_decide + 1:
                    # Round 1 of voting
                    vote = {
                        "decided": False,
                        "yes": self.forkless_cause(
                            self.local_dag.nodes[new_root]["event"],
                            self.local_dag.nodes[candidate]["event"],
                        ),
                    }
                elif self.frame >= self.frame_to_decide + 2:
                    # Round 2+ of voting
                    yes_votes = 0
                    no_votes = 0
                    for prev_root in self.root_set_nodes[self.frame - 1]:
                        prev_vote = self.election_votes[self.frame_to_decide].get(
                            (prev_root, candidate), {"yes": False}
                        )
                        if prev_vote["yes"]:
                            yes_votes += self.validator_weights[prev_root[0]]
                        else:
                            no_votes += self.validator_weights[prev_root[0]]

                    vote = {
                        "decided": yes_votes >= self.quorum(self.frame)
                        or no_votes >= self.quorum(self.frame),
                        "yes": yes_votes >= no_votes,
                    }

                # Update self.election_votes for both decided and undecided cases
                if vote is not None:
                    self.election_votes[self.frame_to_decide][
                        (new_root, candidate)
                    ] = vote
                    if vote["decided"]:
                        self.decided_roots[candidate] = vote
                        if vote["yes"]:
                            self.atropos_roots[self.frame_to_decide] = candidate
                            self.frame_to_decide += 1
                            self.block += 1

    def process_graph_by_timesteps(self, graph):
        nodes = sorted(graph.nodes(data=True), key=lambda node: node[1]["timestamp"])
        max_timestamp = max([node[1]["timestamp"] for node in nodes])

        for current_time in range(max_timestamp + 1):
            nodes_to_process = [
                node for node in nodes if node[1]["timestamp"] == current_time
            ]

            for node in nodes_to_process:
                validator = node[0][0]
                timestamp = node[0][1]
                seq = node[1]["predecessors"]

                if validator not in self.validators:
                    self.validators.add(validator)
                    self.validator_weights[validator] = node[1]["weight"]

                event = Event(
                    id=(validator, seq),
                    seq=seq,
                    creator=validator,
                    parents=[
                        (parent[0], graph.nodes[parent]["predecessors"])
                        for parent in graph.successors((validator, timestamp))
                    ],
                )

                self.local_dag.add_node(
                    (validator, seq),
                    event=event,
                    timestamp=timestamp,
                )

                self.process_event(event, node)

                successors = graph.successors((validator, timestamp))
                for successor in successors:
                    successor_seq = graph.nodes.get(successor)["predecessors"]
                    self.local_dag.add_edge(
                        (validator, seq), (successor[0], successor_seq)
                    )

            self.time += 1

        print("atropos roots:", self.atropos_roots)
        print("frame:", self.frame)
        print("block:", self.block)
        print("frame_to_decide:", self.frame_to_decide)
        print("root_set_nodes:", self.root_set_nodes)
        print("root_set_validators:", self.root_set_validators)
        print("election_votes:", self.election_votes)

        return self

    def process_graph(graph):
        lachesis_state = Lachesis()
        lachesis_state.process_graph_by_timesteps(graph)
        return lachesis_state


if __name__ == "__main__":
    G = convert_input_to_DAG("../inputs/graphs/graph_1.txt")
    lachesis_state = Lachesis()
    lachesis_state.process_graph_by_timesteps(G)
