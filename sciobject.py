from abc import ABC
import time
from datetime import timedelta
import inspect
import logging

PATH_OUTPUT_LOGGING = "data/logging/"
PATH_OUTPUT_AUTOSAVE = "data/autosave/"
PATH_OUTPUT_LOGBOOK = "data/logbook/"

def _get_arg_dict_method(my_method, *args, **kwargs):
    names = list(inspect.getfullargspec(my_method).args[1:])
    names.extend(kwargs.keys())
    values = list(args[1:])
    defaults = inspect.getfullargspec(my_method).defaults
    if any(defaults):
        values.extend(defaults)
    values.extend(kwargs.values())
    return {n:v for n, v in zip(names, values)}


class ClassLogbook:

    def _search_class_index(self):


class ScientificObject(ABC):

    def __init__(self, use_saved: bool = True, use_logger: bool = True):
        """
        A ScientificObject knows that scientific calculations sometimes take a long time and depend on a ton of
        parameters. That is why this class offers a logger that records parameters of the class and every performed
        method and a wrapper that dumps the output of selected methods to a file.

        An object is associated with a name <class_name>_<class_index>.
        A method of an object is associated with a name <class_name>_<class_index>_<method_name>_<method_index>

        Args:
            use_saved (bool):
            use_logger (bool):
        """
        self.use_saved = use_saved
        self.use_logger = use_logger

        # enter the object in the logbook. Two things can happen:
        # a) a new class_index will be given if self.use_saved=False or if there is no entry in the logbook with the
        # same parameters
        # b) an existing class_index will be given if self.use_saved=True AND there is an entry in the logbook with the
        # same parameters
        if self.use_saved is True:
            saved_index = _search_class_index(self)
            if saved_index is not None:
                self.class_index =


        if self.use_logger:
            class_name = self.__class__.__name__
            logging.basicConfig(filename=f"{PATH_OUTPUT_LOGGING}{class_name}_{self.class_index}", level="INFO")
            self.logger = logging.getLogger(class_name)
            self.logger.info(f"SET UP OF: {class_name}")

    def init_logger(self):


    def log_ran_method(self, my_method, time, *args, **kwargs):
        """
        Every time a method has been run you want to record the arguments that were used.

        Args:
            my_method ():
            *args ():
            *kwargs ():

        Returns:

        """
        if self.use_logger:
            names = list(inspect.getfullargspec(my_method).args[1:])
            names.extend(kwargs.keys())
            values = list(args[1:])
            defaults = inspect.getfullargspec(my_method).defaults
            if any(defaults):
                values.extend(defaults)
            values.extend(kwargs.values())
            my_text = ""
            for n, v in zip(names, values):
                my_text += f"{n}={v}, "
            self.logger.info(f"RAN THE METHOD {my_method.__name__}")
            self.logger.info(f"Arguments of the method: {my_text}")
            self.logger.info(f"Hash of this method run is {hash(tuple(values))}.")
            self.logger.info(f"Runtime of the method is {timedelta(seconds=time)} hours:minutes:seconds")


class ExampleObject(ScientificObject):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def example_method(self, one_arg, one_kwarg = 7):
        pass


if __name__ == "__main__":
    eo1 = ExampleObject()
    eo1.example_method(15)
    eo1.example_method(17, 3)
