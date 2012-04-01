#!/usr/bin/env python
"""
constrainer.py -- boolean "constrainers" ("cers") and "constrainees" ("cees").
"""

from maybies import *


class State(object):
    """ The overall state for a constraints problem-solving process. """

    def __init__(self):
        self.cees = set()
        self.maybe_cees = set()
        self.cers = set()
        self.conflicted_cers = set()
        self.eager_cers = set()
        self.log_stack = [[]]  # a list of lists of (cee, prev_value) pairs.

    def push(self):
        self.stack.append([])

    def pop(self):
        # Return True if we didn't hit bottom and something was popped.
        if len(self.log_stack) > 1:
            for cee, value_to_restore in reversed(self.log_stack.pop()):
                cee.reset(value_to_restore)
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
        if not self.consistent()
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
        This is the default guesser; it just guesses an arbitrary
        Maybe is True.  You may want to subclass this class and override
        this guesser.  If so, a good strategy to improve your chances of
        getting a solution sooner, is the Principle of Least Committment,
        which is to make the safest, most likely guess you can find.
        """
        cee = self.maybe_cees.pop()
        self.maybe_cees.add(cee)
        return cee, True

    def generate_leaves(self):
        """
        Search for solutions.  Yield False when I'm at a dead end,
        and True when I'm at a solution.
        """
        self.check_all()
        self.push()
        while True:
            if not self.propagate():
                yield False
                # ...then fall down to the pop below.

            elif self.is_solved():
                yield True
                # ...then fall down to the pop below.

            else:
                cee, value = self.guess()
                assert cee.value == Maybe, "You can only guess about Maybies."
                # When we pop back here, take the opposite guess.
                self.log_stack[-1].append( (cee, not value) )
                self.push()
                continue

            if not self.pop():
                break
        
    
class BoolCee(object):
    """ A cee is a True/False/Maybe variable or slot, constrained by cers. """

    def __init__(self, state):
        self.state = state
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
        """ Set and push.  Return False if a contradiction results. """
        prev_value = self.value
        self.state[-1].append(self, prev_value)
        self.value = value
        if value == Maybe:
            self.state.maybe_cees.add(self)
        else:
            self.state.maybe_cees.discard(self)
        # Cees have to do notice()'s -- set()s must always be accounted for.
        # So we must complete the loop here.
        # Cers don't have to do set()'s as long as the accounting stays right.
        good = True
        for cer in self.cers:
            good = cer.notice_change(self, prev_value, value) and good
        return good

    def reset(self, value_to_restore):  # called by the pop
        value_to_discard = self.value
        self.value = value_to_restore
        # As with set() above, we must complete the loop here.
        for cer in self.cers:
            cer.notice_change(self, value_to_discard, value_to_restore)
            # for now at least


class BoolCer(object):
    """ A 'constrainer' manages a constraint over some cees. """
    def __init__(self, state, minTrue=0, maxTrue=None):
        self.state = state
        state.cers.add(self)
        self.minTrue = minTrue
        self.maxTrue = maxTrue
        self.cees = set()
        self.cee_categories = {True: set(), Maybe: set(), False: set()}

    def __getitem__(self, value):
        """ cer[cee.value] <==> cer.cee_categories[cee.value] """
        return self.cee_categories[value]

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
        Check whether my cee populations are consistent with my minTrue and
        maxTrue.  Update both of these situations in the state.
        Return False if there's a contradiction noticed *anywhere*.
        """
        if self.Maybes_must_be_True() or self.Maybes_must_be_False():
            self.state.eager_cers.add(self)
        else:
            self.state.eager_cers.discard(self)
        if len(self[True]) > self.maxTrue \
                or len(self[True]) + len(self[Maybe]) < self.minTrue:
            self.state.conflicted_cers.add(self)
        else:
            self.state.conflicted_cers.discard(self)
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
                if not cee.set(True):
                    return False
                
        elif self.Maybes_must_be_False():
            for cee in list(self[Maybe]):
                if not cee.set(False):
                    return False

        return self.check()

    def Maybes_must_be_True(self):
        return self[Maybe] \
           and len(self[True]) + len(self[Maybe]) == self.minTrue

    def Maybes_must_be_False(self):
        return self[Maybe] \
           and len(self[True]) == self.maxTrue

    
        

    
        
        
        
