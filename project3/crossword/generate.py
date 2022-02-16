from re import X
import sys

import functools

from sqlalchemy import over
from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        rm_set = set()
        for i in self.domains:
            for word in self.domains[i]:
                if len(word) != i.length:
                    rm_set.add(word)
            self.domains[i] -= rm_set
            rm_set.clear()

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        if not self.crossword.overlaps[x,y]:
            return False

        i = self.crossword.overlaps[x,y][0]
        j = self.crossword.overlaps[x,y][1]

        remove_set = set()
        for word in self.domains[x]:
            suit = False
            for wordy in self.domains[y]:
                if word[i] == wordy[j]:
                    suit = True
                    break
            if not suit:
                remove_set.add(word)
        
        self.domains[x] -= remove_set

        return len(remove_set)
                

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # init queue
        arcqueue = []
        if arcs:
            arcqueue = arcs
        else:
            for i in self.crossword.overlaps:
                if self.crossword.overlaps[i]:
                    arcqueue.append(i)

        # queue is not empty
        f = 0
        r = len(arcqueue)
        while(r-f):
            # revise first arc
            front = arcqueue[f]
            f += 1
            Delete = self.revise(front[0],front[1])
            # if x no domain return False
            if Delete:
                x = front[0]
                if not self.domains[x]:
                    return False
            # if delete ,then ( ,x) in queue without (y,x)
                Neighbors = self.crossword.neighbors(x) - {front[1]}
                for neighbor in Neighbors:
                    arcqueue.append((neighbor,x))
                    r += 1

        # return true
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for var in self.crossword.variables:
            if var not in assignment:
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # not distinct
        if len(assignment) != len(set(assignment.values())):
            return False
        # length
        for i in assignment:
            if i.length != len(assignment[i]):
                return False
        # neighbor
        for x in assignment:
            for y in assignment:
                if x != y:
                    overlap = self.crossword.overlaps[x,y]
                    if overlap:
                        if assignment[x][overlap[0]]!=assignment[y][overlap[1]]:
                            return False
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # get domain
        domain = list(self.domains[var])

        def count_rule_out(choicee):
    
            notassignmet = self.crossword.variables - set(assignment.keys()) - {var}

            Neighbor = self.crossword.neighbors(var)

            # all neighbor,(neigh,var),how much value is ruled out?
            cnt = 0

            for neighbor in Neighbor:
                if neighbor in notassignmet:
                    neighborwordindex = self.crossword.overlaps[neighbor,var][0]
                    varwordindex = self.crossword.overlaps[neighbor,var][1]
                    for neighword in self.domains[neighbor]:
                        if neighword[neighborwordindex] != choicee[varwordindex]:
                            cnt +=1
            
            return cnt

        # sort by the count_rule_out
        return sorted(domain,key = count_rule_out)

    

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        unassgined = list(self.crossword.variables - set(assignment.keys()))

        def cmp(a,b):
            if len(self.domains[a]) == len(self.domains[b]) and len(self.crossword.neighbors(a)) == len(self.crossword.neighbors(b)):
                return 0
            elif len(self.domains[a]) == len(self.domains[b]):
                return len(self.crossword.neighbors(a)) < len(self.crossword.neighbors(b))
            else:
                return self.domains[a] > self.domains[b]
        
        return sorted(unassgined,key=functools.cmp_to_key(cmp))[0]
            

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # exit
        if self.assignment_complete(assignment):
            return assignment

        # select var
        var = self.select_unassigned_variable(assignment)

        # loop all value in domain
        OrderDomain = self.order_domain_values(var,assignment)
        for value in OrderDomain:
            assignment[var] = value
            if self.consistent(assignment):
                return self.backtrack(assignment)
            assignment.pop(var)

        # failture
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
