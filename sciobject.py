from abc import ABC
import os
import time
from datetime import timedelta
import inspect
import logging

import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError

PATH_OUTPUT_LOGGING = "data/logging/"
PATH_OUTPUT_AUTOSAVE = "data/autosave/"
PATH_OUTPUT_LOGBOOK = "data/logbook/"

def _get_arg_values_method(*args, **kwargs) -> list:
    values = list(args)
    values.extend(kwargs.values())
    return values

def _get_arg_names_method(my_method, **kwargs) -> list:
    names = list(inspect.getfullargspec(my_method).args[1:])
    names.extend([k for k in kwargs.keys() if k not in names])
    return names


class ClassLogbook:

    """
    For every class that is derived from ScientificObject, 1 Logbook will be started. A logbook is initiated once and
    keeps recording all instances of this object and its given input parameters.
    """

    def __init__(self, class_name: str, class_parameter_names: list = None):
        self.class_name = class_name
        self.class_parameter_names = class_parameter_names
        self.class_logbook_path = f"{PATH_OUTPUT_LOGBOOK}{self.class_name}.csv"
        self.current_logbook = self._load_current_logbook()

    def _load_current_logbook(self) -> pd.DataFrame:
        try:
            read_csv = pd.read_csv(self.class_logbook_path, index_col=0)
            self.class_parameter_names = read_csv.columns
            return read_csv
        except (FileNotFoundError, EmptyDataError):
            open(self.class_logbook_path, mode="w").close()
            return pd.DataFrame(columns=self.class_parameter_names)

    def get_current_logbook(self):
        return self._load_current_logbook()


    def get_class_index(self, use_saved: bool, parameter_names: list, parameter_values: list):
        assert len(parameter_names)==len(parameter_values)
        parameter_names_values = {n:v for n, v in zip(parameter_names, parameter_values)}
        new_entry = self._get_new_entry(parameter_names_values)
        print("NEW ENTRY", new_entry)
        if use_saved is True:
            # try finding an existing set of data
            existing_index = None
            for index, data in self.current_logbook.iterrows():
                for i, r in new_entry.iterrows():
                    if r.equals(data):
                        existing_index = index
            if existing_index is not None:
                return existing_index
        # if not use_saved or doesn't exist yet, create new entry
        self._record_new_entry(new_entry)
        return len(self.current_logbook) - 1  # minus 1 because we just added this new one

    def _get_new_entry(self, parameter_names_values: dict):
        current_len = len(self.current_logbook)
        empty_df = pd.DataFrame(columns=self.class_parameter_names)
        for existing_title in self.class_parameter_names:
            empty_df.loc[current_len, existing_title] = np.NaN
        for title, data in parameter_names_values.items():
            empty_df.loc[current_len, title] = data
        return empty_df

    def _record_new_entry(self, new_entry: pd.DataFrame):
        self.current_logbook = pd.concat([self.current_logbook, new_entry])
        # update the file immediately
        self.current_logbook.to_csv(self.class_logbook_path)
        self.current_logbook = self._load_current_logbook()


class ScientificObject(ABC):

    def __init__(self, *args, use_saved: bool = True, use_logger: bool = True, **kwargs):
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

        self.class_name = self.__class__.__name__

        # enter the object in the logbook. Two things can happen:
        # a) a new class_index will be given if self.use_saved=False or if there is no entry in the logbook with the
        # same parameters
        # b) an existing class_index will be given if self.use_saved=True AND there is an entry in the logbook with the
        # same parameters
        my_parameter_names = _get_arg_names_method(self.__init__, **kwargs)
        my_parameter_values = _get_arg_values_method(*args, **kwargs)
        self.class_logbook = ClassLogbook(self.class_name, my_parameter_names)
        self.class_index = self.class_logbook.get_class_index(self.use_saved, my_parameter_names, my_parameter_values)

        self.name = f"{self.class_name}_{self.class_index:05d}"

        if self.use_logger:
            self.logger = logging.getLogger(self.name)
            self.logger.setLevel(logging.INFO)
            # create file handler which logs even debug messages
            fh = logging.FileHandler(f"{PATH_OUTPUT_LOGGING}{self.name}.log")
            fh.setLevel(logging.INFO)
            self.logger.addHandler(fh)

            #logging.basicConfig(filename=f"{PATH_OUTPUT_LOGGING}{self.name}.log",
            #                    level="INFO", format='%(levelname)s:%(message)s')
            print(f"my name is {self.name}")
            self.logger.info(f"SET UP OF: {self.name}")
            for n, v in zip(my_parameter_names, my_parameter_values):
                self.logger.info(f"{n}={v}")

    def get_name(self):
        return self.name

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

    def __init__(self, some_arg, some_kwarg=15, **kwargs):
        super().__init__(some_arg, some_kwarg=some_kwarg, **kwargs)

    def example_method(self, one_arg, one_kwarg = 7):
        pass


if __name__ == "__main__":
    my_logbook = ClassLogbook("SomeClass", ["param1", "param2"])

    eo1 = ExampleObject(22, random_kwarg="randomness", use_saved=False)
    eo2 = ExampleObject(99, random_kwarg="randomness", yet_another=17, use_saved = False)
    print(eo1.class_index, eo2.class_index)
    print(eo1.get_name(), eo2.get_name())
    #eo1.example_method(15)
    #eo1.example_method(17, 3)
