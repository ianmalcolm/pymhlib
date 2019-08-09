"""A generic solution class for solutions that are represented by permutations of integers."""

import numpy as np
from abc import ABC
from typing import List

from mhlib.solution import VectorSolution
import random


class PermutationSolution(VectorSolution, ABC):
    """Solution that is represented by a permutation of 0,...length-1."""

    def __init__(self, length: int, init=True, **kwargs):
        """Initializes the solution with 0,...,length-1 if init is set."""
        super().__init__(length, init=False, **kwargs)
        if init:
            self.x[:] = np.arange(length)

    def copy_from(self, other: 'PermutationSolution'):
        super().copy_from(other)

    def initialize(self, k):
        """Random initialization."""
        np.random.shuffle(self.x)
        self.invalidate()

    def check(self):
        """Check if valid solution.

        :raises ValueError: if problem detected.
        """
        super().check()
        if set(self.x) != set(range(len(self.x))):
            raise ValueError("Solution is no permutation of 0,...,length-1")

    def two_exchange_neighborhood_search(self, best_improvement) -> bool:
        """Perform the systematic search of the 2-exchange neighborhood, in which two elements are exchanged.

        The neighborhood is searched in a randomized ordering.
        Note that frequently, a more problem-specific neighborhood search with delta-evaluation is
        much more efficient!

        :param best_improvement:  if set, the neighborhood is completely searched and a best neighbor is kept;
            otherwise the search terminates in a first-improvement manner, i.e., keeping a first encountered
            better solution.

        :return: True if an improved solution has been found
        """
        n = self.inst.n
        best_obj = orig_obj = self.obj()
        best_p1 = None
        best_p2 = None
        order = np.arange(n)
        np.random.shuffle(order)
        for idx, p1 in enumerate(order[:n - 1]):
            for p2 in order[idx + 1:]:
                self.x[p1], self.x[p2] = self.x[p2], self.x[p1]
                if self.two_exchange_delta_eval(p1, p2):
                    if self.is_better_obj(self.obj(), best_obj):
                        if not best_improvement:
                            return True
                        best_obj = self.obj()
                        best_p1 = p1
                        best_p2 = p2
                    self.x[p1], self.x[p2] = self.x[p2], self.x[p1]
                    self.obj_val = orig_obj
                    assert self.two_exchange_delta_eval(p1, p2, False)
        if best_p1:
            self.x[best_p1], self.x[best_p2] = self.x[best_p2], self.x[best_p1]
            self.obj_val = best_obj
            return True
        self.obj_val = orig_obj
        return False

    def two_exchange_delta_eval(self, p1: int, p2: int, update_obj_val=True, allow_infeasible=False) -> bool:
        """A 2-exchange move was performed, if feasible update other solution data accordingly, else revert.

        It can be assumed that the solution was in a correct state with a valid objective value in obj_val
        *before* the already applied move, obj_val_valid therefore is True.
        The default implementation just calls invalidate() and returns True.

        :param p1: first position
        :param p2: second position
        :param update_obj_val: if set, the objective value should also be updated or invalidate needs to be called
        :param allow_infeasible: if set and the solution is infeasible, the move is nevertheless accepted and
            the update of other data done
        """
        if update_obj_val:
            self.invalidate()
        return True

    def partially_mapped_crossover(self, other: 'PermutationSolution') -> 'PermutationSolution':
        """Partially mapped crossover (PMX).

        Copies the current solution, selects a random subsequence from the other parent and realizes this subsequence
        in the child by corresponding pairwise exchanges.

        :param other: second parent
        :return: new offspring solution
        """

        size = len(self.x)

        # determine random subsequence
        begin = random.randrange(size)
        end = random.randrange(size - 1)
        if begin == end:
            end = end + 1
        if begin > end:
            begin, end = end, begin

        child = self.copy()

        # adopt subsequence from parent b by corresponding pairwise exchanges
        pos = np.empty(size, int)
        for i, elem in enumerate(child.x):
            pos[elem] = i
        for i in range(begin, end):
            elem = other.x[i]
            j = pos[elem]
            if i != j:
                elem_2 = child.x[i]
                child.x[i], child.x[j] = elem, elem_2
                pos[elem], pos[elem_2] = i, j
        child.invalidate()
        return child

    def cycle_crossover(self, other: 'PermutationSolution') -> 'PermutationSolution':
        """ Cycle crossover.

        A randomized crossover method that adopts absolute positions of the elements from the parents.

        :param other: second parent
        :return: new offspring solution
        """
        size = len(self.x)
        pos = np.empty(size, int)
        for i, elem in enumerate(self.x):
            pos[elem] = i

        # detect all cycles
        group = np.full(size, 0)
        group_id = 1
        for i in range(size):
            if group[i]:
                continue
            j = i
            while not group[j]:
                group[j] = group_id
                elem = other.x[j]
                j = pos[elem]
            group_id += 1

        # perform exchange
        child = self.copy()
        for i in range(size):
            if child.x[i] % 2 == 1:
                child.x[pos] = other.x[pos]
        child.invalidate()
        return child

    def edge_recombination(self, other: 'PermutationSolution') -> 'PermutationSolution':
        """ Edge recombination.

        This is a classical recombination operator for the traveling salesman problem, for example.
        It creates an adjacency list, i.e., a list of neighbors in the cyclically viewed parent permutations,
        for each element.
        A start element is randomly chosen.
        From this current element the next is iteratively determined by either choosing a neighbor with the smallest
        adjacency list (ties are broken randomly), or, if the list is of remaining neighbors is empty,
        by choosing some other not yet visited element at random.

        :param other: second parent
        :return new offspring solution
        """
        def append_if_not_contained(nbs, nb):
            if nb not in nbs:
                nbs.append(nb)
        size = len(self.x)
        adj_lists: List[List[int]] = [list() for _ in range(size)]
        for i, elem in enumerate(self.x):
            append_if_not_contained(adj_lists[elem], self.x[(i-1) % size])
            append_if_not_contained(adj_lists[elem], self.x[(i+1) % size])
        for i, elem in enumerate(other.x):
            append_if_not_contained(adj_lists[elem], other.x[(i-1) % size])
            append_if_not_contained(adj_lists[elem], other.x[(i+1) % size])
        unvisited = set(range(size))
        child = self.copy()
        elem = random.randrange(size)
        for i in range(size-1):
            # accept elem and remove it from unvisited and adjacency list
            child.x[i] = elem
            unvisited.remove(elem)
            for j in adj_lists[elem]:
                adj_lists[j].remove(elem)
            # select next elem
            if not adj_lists[elem]:
                sel = random.choice(list(unvisited))
            else:
                candidates = [adj_lists[elem][0]]
                degree = len(adj_lists[candidates[0]])
                for e2 in adj_lists[elem][1:]:
                    degree_e2 = len(adj_lists[e2])
                    if degree_e2 < degree:
                        candidates = [e2]
                    elif degree_e2 == degree:
                        candidates.append(e2)
                sel = random.choice(candidates)
                adj_lists[elem].clear()
            elem = sel
        child.x[-1] = elem
        child.invalidate()
        return child
