class Alacrity(object):
    components = []

    def __init__(self):
        #TODO: send init info?
        print 'in init'
        for cls in type(self).__subclasses__():
            print 'initing {}'.format(cls)
            self.components.append(cls())


    def on_tick(self):
        for obj in components:
            obj.on_tick()

