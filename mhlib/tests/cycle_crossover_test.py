import unittest

from mhlib.permutation_solution import PermutationSolution, cycle_crossover


class TestSolution(PermutationSolution):
    """Solution to a QAP instance.

    Attributes
        - inst: associated QAPInstance
        - x: integer vector representing a permutation
    """

    def copy(self):
        sol = TestSolution(len(self.x), init=False)
        sol.copy_from(self)
        return sol

    def copy_from(self, other: 'TestSolution'):
        super().copy_from(other)

    def calc_objective(self):
        return 0

    def change(self, values):
        self.x = values

    def construct(self, par, result):
        """Scheduler method that constructs a new solution.

        Here we just call initialize.
        """
        del result
        self.initialize(par)


class CycleCrossoverTestCase(unittest.TestCase):

    def no_change(self):
        a = TestSolution(7)
        b = TestSolution(7)

        a.change([1, 4, 6, 2, 0, 3, 5])
        b.change([6, 1, 4, 2, 5, 0, 3])

        cycle_crossover(a, b)

        anew = [1, 4, 6, 2, 0, 3, 5]
        bnew = [6, 1, 4, 2, 5, 0, 3]

        for i in range(0, 7):
            self.assertEqual(a.x[i], anew[i])
            self.assertEqual(b.x[i], bnew[i])

    def change(self):
        a = TestSolution(7)
        b = TestSolution(7)

        a.change([1, 4, 6, 2, 0, 3, 5])
        b.change([6, 1, 4, 0, 2, 5, 3])

        cycle_crossover(a, b)

        anew = [1, 4, 6, 0, 2, 3, 5]
        bnew = [6, 1, 4, 2, 0, 5, 3]

        for i in range(0, 7):
            self.assertEqual(a.x[i], anew[i])
            self.assertEqual(b.x[i], bnew[i])


if __name__ == '__main__':
    unittest.main()
