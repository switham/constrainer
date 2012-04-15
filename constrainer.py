#!/usr/bin/env python
"""
constrainer.py -- boolean variables and constraints on them.
"""

from maybies import *


class State(object):
    """ The overall state for a constraints problem-solving process. """

    def __init__(self, verbose=False):
        if verbose:
            print "Hi, I am a new State."
        self.verbose = verbose
        self.vars = set()
        self.maybe_vars = set()
        self.constraints = set()
        self.conflicted_constraints = set()
        self.eager_constraints = set()
        self.log_stack = [[]]  # a list of lists of (var, prev_value) pairs.

    def depth(self):
        return len(self.log_stack)

    def push(self):
        self.log_stack.append([])
        if self.verbose:
            print "depth", self.depth()

    def pop(self):
        """
        Pop and undo one level of stack and return True,
        or return False if we hit bottom.
        """
        if len(self.log_stack) > 1:
            for var, value_to_restore in reversed(self.log_stack.pop()):
                var.raw_set(value_to_restore)
            return True
        
        else:
            # The bottom level is just for recording the initial setup;
            # it can't be popped.
            return False

    def check_all(self):
        self.maybe_vars = set(var for var in self.vars if var.value == Maybe)
        for constraint in self.constraints:
            constraint.check()

    def consistent(self):
        return not self.conflicted_constraints

    def is_solved(self):
        return not self.conflicted_constraints and not self.maybe_vars

    def propagate(self):
        if not self.consistent():
            return False
        
        while self.eager_constraints:
            for constraint in list(self.eager_constraints):
                if not constraint.propagate():
                    return False

                # constraint should have become uneager if no contradiction.
        # We should have caught any contradictions by now.            
        return True

    def guess(self):
        """
        Return a guess: (var, value), where value is True or False.
        var.value must be Maybe at the time you guess.
        This is the default guesser; it just guesses that an arbitrary
        Maybe is False.  You may want to subclass this class and override
        this guesser.  If so, a good strategy to improve your chances of
        getting a solution sooner, is the Principle of Least Committment,
        which is to make the safest, most likely guess you can find.
        """
        var = self.maybe_vars.pop()
        self.maybe_vars.add(var)
        return var, False

    def generate_leaves(self,verbose=False):
        """
        Search for solutions.  Yield False when I'm at a dead end,
        and True when I'm at a solution.
        """
        self.check_all()
        self.push()
        while True:
            if not self.propagate():
                if verbose: print "Conflict:", self.conflicted_constraints
                yield False
                # ...then fall down to the pop below.

            elif self.is_solved():
                yield True
                # ...then fall down to the pop below.

            else:
                var, value = self.guess()
                if self.verbose:
                    print "guess", var.die, var.letter, value
                assert var.value == Maybe, "You can only guess about Maybies."
                assert value != Maybe, "Must guess True or False, not Maybe."
                # This set() pushes the Maybe and sets the alternative.
                # Pop through here untakes both alternatives and their context.
                var.set(not value)
                self.push()  # -------- the stack frame boundary --------
                # This set() pushes the alternative and sets the guess.
                # Pop through here tries the alternative.
                var.set(value)
                continue

            if not self.pop():
                break
        
    
class BoolVar(object):
    """
    A True/False/Maybe variable or slot, constrained by constraints.
    """
    def __init__(self, state, **kwargs):
        self.state = state
        for kw in kwargs:
            self.__dict__[kw] = kwargs[kw]
        self.value = Maybe
        state.vars.add(self)
        state.maybe_vars.add(self)
        self.constraints = set()

    def be_constrained_by(self, constraint):
        """ Not meant to be called by the user. """
        assert constraint not in self.constraints, \
               "Adding a constraint to a var twice."
        
        self.constraints.add(constraint)

    def set(self, value):
        """ Push, then set.  Return False if a contradiction results. """
        self.state.log_stack[-1].append( (self, self.value) )
        return self.raw_set(value)

    def raw_set(self, value):
        """
        Set without push.  Do accounting.  Used after both push and pop.
        Return False if a contradiction results.
        """
        prev_value = self.value
        self.value = value
        if value == Maybe:
            self.state.maybe_vars.add(self)
        else:
            self.state.maybe_vars.discard(self)
        # Vars have to do notice()'s -- set()s must always be accounted for.
        # So we must complete the loop here.  Constraints don't have to do
        # all the set()'s they could, as long as the accounting stays right.
        for constraint in self.constraints:
            constraint.notice_change(self, prev_value, value)
        return self.state.consistent()


class BoolConstraint(object):
    """ An object that manages a constraint over some vars. """
    def __init__(self, state, **kwargs ):
        self.min_True = 0
        self.max_True = None
        self.label = {}
        for kw in kwargs:
            self.__dict__[kw] = kwargs[kw]
            if kw not in ("min_True", "max_True"):
                self.label[kw] = kwargs[kw]

        self.state = state
        state.constraints.add(self)
        self.vars = set()
        self.var_categories = {True: set(), Maybe: set(), False: set()}

    def __getitem__(self, value):
        """
        self[value], where value is in {True, Maybe, False},
        is the set of my vars that are currently set to value.
        self[value].add() and self[value].discard() modify the sets.
        """
        return self.var_categories[value]

    def __repr__(self):
        return "Constraint(" + str(self.label) + ")"

    def constrain(self, var):
        assert var not in self.vars, "Adding a var to a constraint twice."
        
        self.vars.add(var)
        self[var.value].add(var)
        var.be_constrained_by(self)

    def notice_change(self, var, prev_value, new_value):
        self[prev_value].discard(var)
        self[new_value].add(var)
        return self.check()

    def check(self):
        """
        Become "eager" if there are Maybes whose values can be inferred.
        Check whether my var populations are consistent with my min_True and
        max_True.  Update both of these situations in the state.
        Return False if there's a contradiction noticed in *any* constraint.
        """
        if self.Maybes_must_be_True() or self.Maybes_must_be_False():
            self.state.eager_constraints.add(self)
        else:
            self.state.eager_constraints.discard(self)
        conflicted = len(self[True]) > self.max_True \
                or len(self[True]) + len(self[Maybe]) < self.min_True
        if conflicted != (self in self.state.conflicted_constraints):
            if conflicted:
                if self.state.verbose: print self, "is conflicted:"
                self.state.conflicted_constraints.add(self)
            else:
                if self.state.verbose: print self, "is not conflicted:"
                self.state.conflicted_constraints.discard(self)
            if self.state.verbose:
                print "    min:", self.min_True, "vars:", len(self.vars),
                print "Trues:", len(self[True]),
                print "Maybies:", len(self[Maybe]), "max:", self.max_True
        return self.state.consistent()

    def propagate(self):
        """
        This is usually called when this constraint is eager, but there is a
        case where the constraint is still in the state's to-propagate list
        after it has become uneager.  When a constraint does propagate
        (completely) it always resets itself to uneager.
         o  Propagate does the right thing if there's nothing to do.
         o  A constraint needn't propagate completely or at all if there's a
            contradiction; partially-done propagations leave a still-eager
            situation, and propagate() will get called again if appropriate.
         o  Reporting a contradiction is more important than propagating.
        Return False if a contradiction is found in self or elsewhere.
        """
        if not self.check():
            return False

        # Vars have to do notice()'s -- set()s must always be accounted for.
        # Constraints don't have to do all possible sets as long as the
        # accounting stays correct.
        # So I can return in the middle of a loop here.
        if self.Maybes_must_be_True():
            for var in list(self[Maybe]):
                if self.state.verbose:
                    print "infer", var.letter, var.die, True
                if not var.set(True):
                    return False
                
        elif self.Maybes_must_be_False():
            for var in list(self[Maybe]):
                if self.state.verbose:
                    print "infer", var.letter, var.die, False
                if not var.set(False):
                    return False

        return self.check()

    def Maybes_must_be_True(self):
        return self[Maybe] \
           and len(self[True]) + len(self[Maybe]) == self.min_True

    def Maybes_must_be_False(self):
        return self[Maybe] \
           and len(self[True]) == self.max_True

    
        

    
        
        
        
