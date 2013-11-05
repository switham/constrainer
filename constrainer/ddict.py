"""
constrainer/ddict.py -- more-easily-specialized defaultdict.

    Copyright (c) 2013 Steve Witham All rights reserved.  
    Constrainer is available under a BSD license, whose full text is at
        https://github.com/switham/constrainer/blob/master/LICENSE
"""

from collections import defaultdict


class Template(object):
    """
    This class is meant as a decorator for a function that returns a class,
    so I'll describe it that way:
    @Template
    def layerer(default_type):
        ...
        return a_class

    new_class = layerer[default_type]
    new_instance = layerer[default_type] ()
    ellipsified_class = layerer[...]
    ellipsified_instance = layerer[...] ()

    The template is meant to be used with a default type in brackets,
    so the __getitem__ method does most of the work.
    """
    
    def __init__(self, layerer):
        self.template_name = layerer.__name__
        self.layerer = layerer
        
    def __getitem__(self, default_type):
        """
        template[default_type] returns a class such that
            template[default_type]() <==> layerer(default_type)()
        except that the class has a name like: "template[default_type]".

        template[...] uses the Ellipsis object as the "default_type"
        (whatever that means to the layerer function)
        and spells the resulting class name like: template[...].
        """
        the_class = self.layerer(default_type)
        if default_type == Ellipsis:
            default_type_name = "..."
        else:
            default_type_name = default_type.__name__
        the_class.__name__ = self.template_name + \
                             "[" + default_type_name + "]"
        return the_class


@Template
def ddict(default_type=None):
    """
    The way to do defaultdicts of defaultdicts with the standard Python
    collections library is, e.g.,
         foo = defaultdict(lambda: defaultdict(int))

    You might want this nesting to recursively go to as many levels as
    necessary, which you can do like this:
        def rdd():
            return defaultdict(rdd)
        bar = rdd()
    This lets you assign to any depth:
        bar[1][2] = "hi"
        print bar
        defaultdict(<function rdd at 0x10042ae60>,
                    {1: defaultdict(<function rdd at 0x10042ae60>, {2: 'hi'})})

    ddict is some syntactic sugar and class plumbing around defaultdict,
    and is used like this:

    Foo = ddict[int]     Returns a CLASS called "ddict[int]" whose instances
                         are like defaultdict(int) except for how they print.
    foo = ddict[int] ()  (Remember the parens!) gives you an instance directly.
                         A brand new one would print as "ddict[int]({})".
    fooo = ddict[ddict[int]] ()  (Parens! Parens!)
                         Gives you a defaultdict whose instances are
                         defaultdicts whose instances are ints.
    Bar = ddict[...]     Here we really mean three dots, the Python Ellipsis.
                         Returns a CLASS called "ddict[...]", that acts like
                         rdd above, except for how instances print.
    bar = ddict[...] ()  (Remember the parens!) gives you an instance directly.
                         A brand new one would print as "ddict[...]({})".
    bar[1][2] = "yo"
    print bar
    ddict[...]({1: ddict[...]({2: 'yo'})})
    
    wow = ddict[ddict[ddict[int]]] ({"a": {"b": {"c": 12}}})
                         (Also possible with nested lambda: defaultdict's.)

    Besides being prettier, the repr() strings of a ddict can be used to
    reconstruct the ddict, whereas an ordinary defaultdict's repr() can't.
    """

    class the_class(defaultdict):
        def __init__(self, initializer={}):
            super(the_class, self).__init__(the_class.default_type, initializer)

        def __repr__(self):
            parts = ((repr(k) + ": " + repr(self[k])) for k in self)
            return type(self).__name__ + "({" + ", ".join(parts) + "})"

    if default_type == Ellipsis:
        the_class.default_type = the_class
    else:
        the_class.default_type = default_type
    return the_class

