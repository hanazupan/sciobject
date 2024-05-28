from abc import ABC
import os
import time
from datetime import timedelta
import inspect
import logging

import numpy as np
import pandas as pd

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

    """
    For every class that is derived from ScientificObject, 1 Logbook will be started. A logbook is initiated once and
    keeps recording all instances of this object and its given input parameters.
    """

    def __init__(self, class_name: str):
        self.class_name = class_name
        self.class_logbook_path = f"{PATH_OUTPUT_LOGBOOK}{self.class_name}.csv"
        self.current_logbook = self._load_current_logbook()

    def _load_current_logbook(self) -> pd.DataFrame:
        try:
            return pd.read_csv(self.class_logbook_path, index_col=0)
        except FileNotFoundError:
            open(self.class_logbook_path, mode="w").close()
            return pd.DataFrame()


    def get_class_index(self, use_saved: bool, parameter_names_values: dict):
        #new_entry = self._get_new_entry(parameter_names_values)
        new_entry = pd.Series(parameter_names_values)
        print(new_entry)
        for index, data in self.current_logbook.iterrows():
            print(new_entry.equals(data))
        # if use_saved is True:
        #     print("where", self.current_logbook.where("param1"==19).index)
        #     #saved_index = self.class_logbook._search_class_index()
        #     #if saved_index is not None:
        #     #    return saved_index
        # #self._record_new_entry()
        return len(self.current_logbook)

    def _get_new_entry(self, parameter_names_values: dict):
        new_index = len(self.current_logbook)
        new_entry = pd.DataFrame.from_dict({new_index: parameter_names_values.values()},
                                           orient='index', columns=parameter_names_values.keys())
        return new_entry

    def _record_new_entry(self, new_entry: pd.DataFrame):
        self.current_logbook = pd.concat([self.current_logbook, new_entry])
        print(self.current_logbook)
        # update the file immediately
        self.current_logbook.to_csv(self.class_logbook_path)

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

        class_name = self.__class__.__name__

        # enter the object in the logbook. Two things can happen:
        # a) a new class_index will be given if self.use_saved=False or if there is no entry in the logbook with the
        # same parameters
        # b) an existing class_index will be given if self.use_saved=True AND there is an entry in the logbook with the
        # same parameters
        self.class_logbook = ClassLogbook(class_name, self.use_saved)
        self.class_index = self.class_logbook.get_class_index(use_saved, use_logger)



        if self.use_logger:
            logging.basicConfig(filename=f"{PATH_OUTPUT_LOGGING}{class_name}_{self.class_index}", level="INFO")
            self.logger = logging.getLogger(class_name)
            self.logger.info(f"SET UP OF: {class_name}")

    def init_logger(self):
        pass


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
    my_logbook = ClassLogbook("SomeClass")
    my_logbook._record_new_entry({"param1": 17, "param2": tuple([3.0, "ab"])})
    my_logbook._record_new_entry({"param1": 19, "param2": tuple([18, "ab"]),
                                                                "param3": None})
    my_logbook.get_class_index(True, {"param1": 19, "param2": tuple([18, "ab"]),
                                                                "param3": None})
    #eo1 = ExampleObject()
    #eo1.example_method(15)
    #eo1.example_method(17, 3)
