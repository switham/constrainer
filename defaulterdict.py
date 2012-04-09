from collections import defaultdict


class defaulterdict(defaultdict):
    """
    This is experimental and nonstandard.  The way to do defaultdicts of
    defaultdicts with the standard Python library is with lambda, e.g.,
         foo = defaultdict(lambda: defaultdict(int))

    To do a recursive defaultdict:
    def rdd():
        return defaultdict(rdd)

    However this class prints prettier.
    
    A defaultdict whose default value is always another defaulterdict.
    """
    def __init__(self):
            super(defaulterdict, self).__init__(defaulterdict)
            
    def __repr__(self):
            parts = ((repr(k) + ": " + repr(v)) for k, v in self.iteritems())
            return "defaulterdict({" + ", ".join(parts) + "})"


def DD(default_type=None):
    """
    This is experimental and nonstandard.  The way to do defaultdicts of
    defaultdicts with the standard Python library is, e.g.,
         foo = defaultdict(lambda: defaultdict(int))
    
    Given a class or type or callable to initialize undefined instances,
    return a *class* for defaultdicts of that class or type.
    This class, in turn, can be used as an argument to defaultdict,
    or to DD(), so, e.g.
    foo = defaultdict(DD(int))       or defaultdict(DD(int), {1: {2: 3}})
       or defaultdict(DD(DD(list)))
       or (this is sad): defaultdict(DD(dict))
    Or you can use the returned class to initialize, as in:
    foo = DD(int) ()
    foo = DD(DD(int)) ()
    foo = DD(DD(dict)) ()
    """

    class the_class(defaultdict):
        def __init__(self, initializer={}):
            super(the_class, self).__init__(the_class.default_type, initializer)

        def __repr__(self):
            parts = ((repr(k) + ": " + repr(self[k])) for k in self)
            return type(self).__name__ + "({" + ", ".join(parts) + "})"

    if default_type == None:
        the_class.default_type = the_class
        the_class.__name__ = "DD()"
    else:
        the_class.default_type = default_type
        the_class.__name__ = "DD(" + default_type.__name__ + ")"
    return the_class


class Template(object):
    def __init__(self, template_name, Layer):
        self.template_name = template_name
        self.Layer = Layer
        
    def __call__(self):
        """
        When used like a class, a Template acts like a class that acts like
        what Layer acts like with no arguments.
        """
        the_class = self.Layer()
        the_class.__name__ = self.template_name
        return the_class()
    
    def __getitem__(self, default_type):
        """
        return a class T such that
            T   <==> Layer(default_type)
            T() <==> Layer(default_type) ()
        and so
            template[default_type]() <==> Layer(default_type)()
        """
        assert(default_type != None)
        the_class = self.Layer(default_type)
        the_class.__name__ = self.template_name + \
                             "[" + default_type.__name__ + "]"
        return the_class


Dict = Template("Dict", DD)
Dict.__doc__ = """
    Use Dict like this:
        foo = Dict()            <==> foo = DD() ()
        foo = Dict[int]()       <==> foo = DD(int) ()
        foo = Dict[Dict[int]]() <==> foo = DD(DD(int)) ()
    """

