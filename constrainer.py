#!/usr/bin/env python
"""
constrainer.py -- boolean "constrainers" ("cers") and "constrainees" ("cees").
"""

from maybies import *


class State(object):
    """ The overall state for a constraints problem-solving process. """

    def __init__(self, verbose=False):
        if verbose:
            print "Hi, I am a new State."
        self.verbose = verbose
        self.cees = set()
        self.maybe_cees = set()
        self.cers = set()
        self.conflicted_cers = set()
        self.eager_cers = set()
        self.log_stack = [[]]  # a list of lists of (cee, prev_value) pairs.

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
            for cee, value_to_restore in reversed(self.log_stack.pop()):
                cee.raw_set(value_to_restore)
            return True
        
        else:
            # The bottom level is just for recording the initial setup;
            # it can't be popped.
            return False

    def check_all(self):
        self.maybe_cees = set(cee for cee in self.cees if cee.value == Maybe)
        # (not to mention the slitted sheet)
        for cer in self.cers:
            cer.check()

    def consistent(self):
        return not self.conflicted_cers

    def is_solved(self):
        return not self.conflicted_cers and not self.maybe_cees

    def propagate(self):
        if not self.consistent():
            return False
        
        while self.eager_cers:
            for cer in list(self.eager_cers):
                if not cer.propagate():
                    return False

                # cer should have made itself uneager if no contradiction.
        # We should have caught any contradictions by now.            
        return True

    def guess(self):
        """
        Return a guess: (cee, value), where value is True or False.
        cee.value must be Maybe at the time you guess.
        This is the default guesser; it just guesses that an arbitrary
        Maybe is False.  You may want to subclass this class and override
        this guesser.  If so, a good strategy to improve your chances of
        getting a solution sooner, is the Principle of Least Committment,
        which is to make the safest, most likely guess you can find.
        """
        cee = self.maybe_cees.pop()
        self.maybe_cees.add(cee)
        return cee, False

    def generate_leaves(self,verbose=False):
        """
        Search for solutions.  Yield False when I'm at a dead end,
        and True when I'm at a solution.
        """
        self.check_all()
        self.push()
        while True:
            if not self.propagate():
                if verbose: print "Conflict:", self.conflicted_cers
                yield False
                # ...then fall down to the pop below.

            elif self.is_solved():
                yield True
                # ...then fall down to the pop below.

            else:
                cee, value = self.guess()
                if self.verbose:
                    print "guess", cee.die, cee.letter, value
                assert cee.value == Maybe, "You can only guess about Maybies."
                assert value != Maybe, "Must guess True or False, not Maybe."
                # This set() pushes the Maybe and sets the alternative.
                # Pop through here untakes both alternatives and their context.
                cee.set(not value)
                self.push()  # -------- the stack frame boundary --------
                # This set() pushes the alternative and sets the guess.
                # Pop through here tries the alternative.
                cee.set(value)
                continue

            if not self.pop():
                break
        
    
class BoolCee(object):
    """
    A constrainee is a True/False/Maybe variable or slot, constrained by cers.
    """
    def __init__(self, state, **kwargs):
        self.state = state
        for kw in kwargs:
            self.__dict__[kw] = kwargs[kw]
        self.value = Maybe
        state.cees.add(self)
        state.maybe_cees.add(self)
        self.cers = set()

    def be_constrained_by(self, cer):
        if cer in self.cers:
            return
        
        self.cers.add(cer)
        cer.constrain(self)

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
            self.state.maybe_cees.add(self)
        else:
            self.state.maybe_cees.discard(self)
        # Cees have to do notice()'s -- set()s must always be accounted for.
        # So we must complete the loop here.
        # Cers don't have to do set()'s as long as the accounting stays right.
        for cer in self.cers:
            cer.notice_change(self, prev_value, value)
        return self.state.consistent()


class BoolCer(object):
    """ A 'constrainer' manages a constraint over some cees. """
    def __init__(self, state, **kwargs ):
        self.min_True = 0
        self.max_True = None
        self.label = {}
        for kw in kwargs:
            self.__dict__[kw] = kwargs[kw]
            if kw not in ("min_True", "max_True"):
                self.label[kw] = kwargs[kw]

        self.state = state
        state.cers.add(self)
        self.cees = set()
        self.cee_categories = {True: set(), Maybe: set(), False: set()}

    def __getitem__(self, value):
        """ cer[cee.value] <==> cer.cee_categories[cee.value] """
        return self.cee_categories[value]

    def __repr__(self):
        return "Cer(" + str(self.label) + ")"

    def constrain(self, cee):
        if cee in self.cees:
            return
        
        self.cees.add(cee)
        self[cee.value].add(cee)
        cee.be_constrained_by(self)

    def notice_change(self, cee, prev_value, new_value):
        self[prev_value].discard(cee)
        self[new_value].add(cee)
        return self.check()

    def check(self):
        """
        Become "eager" if there are Maybes whose values can be inferred.
        Check whether my cee populations are consistent with my min_True and
        max_True.  Update both of these situations in the state.
        Return False if there's a contradiction noticed *anywhere*.
        """
        if self.Maybes_must_be_True() or self.Maybes_must_be_False():
            self.state.eager_cers.add(self)
        else:
            self.state.eager_cers.discard(self)
        conflicted = len(self[True]) > self.max_True \
                or len(self[True]) + len(self[Maybe]) < self.min_True
        if conflicted != (self in self.state.conflicted_cers):
            if conflicted:
                if self.state.verbose: print self, "is conflicted:"
                self.state.conflicted_cers.add(self)
            else:
                if self.state.verbose: print self, "is not conflicted:"
                self.state.conflicted_cers.discard(self)
            if self.state.verbose:
                print "    min:", self.min_True, "cees:", len(self.cees),
                print "Trues:", len(self[True]),
                print "Maybies:", len(self[Maybe]), "max:", self.max_True
        return self.state.consistent()

    def propagate(self):
        """
        This is usually called when this cer is eager, but there is a case
        where the cer is still in the state's to-propagate list after it has
        become uneager.  When a cer does propagate (completely) it always
        leaves itself uneager.
         o  Propagate does the right thing if there's nothing to do.
         o  A cer needn't propagate completely or at all if there's a
            contradiction; partially-done propagations leave a still-eager
            situation, and propagate() will get called again if appropriate.
         o  Reporting a contradiction is more important than propagating.
        Return False if a contradiction is found in self or elsewhere.
        """
        if not self.check():
            return False

        # Cees have to do notice()'s -- set()s must always be accounted for.
        # Cers don't have to do sets as long as the accounting stays correct.
        # So I can return in the middle of a loop here.
        if self.Maybes_must_be_True():
            for cee in list(self[Maybe]):
                if self.state.verbose:
                    print "infer", cee.letter, cee.die, True
                if not cee.set(True):
                    return False
                
        elif self.Maybes_must_be_False():
            for cee in list(self[Maybe]):
                if self.state.verbose:
                    print "infer", cee.letter, cee.die, False
                if not cee.set(False):
                    return False

        return self.check()

    def Maybes_must_be_True(self):
        return self[Maybe] \
           and len(self[True]) + len(self[Maybe]) == self.min_True

    def Maybes_must_be_False(self):
        return self[Maybe] \
           and len(self[True]) == self.max_True

    
        

    
        
        
        
