import configparser
class App:
    __conf = None

    @staticmethod
    def config():
        if App.__conf is None:
            App.__conf = configparser.ConfigParser(interpolation=None)
            App.__conf.read('properties.ini')
        return App.__conf