"""
SciObject is an abstract class that helps all derived classes dump parameters (of initiated class and ran methods)
and output to files, so that no parameters are ever forgotten, no runtime a mystery and no calculation needs to be
repeated.

How to use:
- if you have a class that you want to record, let it inherit from SciObject and include super().__init__(<arguments>)
- for the methods of this class you want to record, use a wrapper @sci_method before them


Example use:

class ExampleObject(ScientificObject):

    def __init__(self, some_arg, some_kwarg=15, **kwargs):
        # forward all of your args to super()
        super().__init__(some_arg, some_kwarg=some_kwarg, **kwargs)

    @sci_method
    def important_method(self, one_arg, another_arg, one_kwarg=7):
        pass

    def unimportant_method(self, *som_args):
        pass

Now you wanna go back to one very specific run? Here's a suggestion how to do this:
- go to LOGBOOK for your class and look up which class_index corresponds to the parameters you are interested in
- now go to LOGGING for
"""

import pickle
from abc import ABC
import os
from time import time
from datetime import timedelta, datetime
import inspect
import logging
from functools import wraps
from typing import Callable

import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError

PATH_OUTPUT_LOGGING = "data/logging/"
PATH_OUTPUT_AUTOSAVE = "data/autosave/"
PATH_OUTPUT_LOGBOOK = "data/logbook/"
PATH_OUTPUT_METHODBOOK = "data/methodbook/"

LOGGING_PATHS = [PATH_OUTPUT_LOGGING, PATH_OUTPUT_AUTOSAVE, PATH_OUTPUT_LOGBOOK, PATH_OUTPUT_METHODBOOK]


def freshly_create_log_folders():
    for path in LOGGING_PATHS:
        if not os.path.exists(path):
            os.makedirs(path)


def _get_arg_values_method(*args, **kwargs) -> list:
    values = list(args)
    values.extend(kwargs.values())
    return values


def _get_arg_names_method(my_method, **kwargs) -> list:
    names = list(inspect.getfullargspec(my_method).args[1:])
    names.extend([k for k in kwargs.keys() if k not in names])
    return names


class Logbook(ABC):
    """
    For every class that is derived from ScientificObject, 1 Logbook will be started. A logbook is initiated once and
    keeps recording all instances of this object and its given input parameters.
    """

    def __init__(self, class_name: str, path_to_use: str, *, class_parameter_names: list = None):
        self.class_name = class_name
        self.class_parameter_names = class_parameter_names
        self.class_logbook_path = f"{path_to_use}{self.class_name}.csv"
        self.current_logbook = self._load_current_logbook()

    def _load_current_logbook(self) -> pd.DataFrame:
        try:
            read_csv = pd.read_csv(self.class_logbook_path, index_col=0, dtype=object)
            self.class_parameter_names = read_csv.columns
            return read_csv
        except (FileNotFoundError, EmptyDataError):
            open(self.class_logbook_path, mode="w").close()
            return pd.DataFrame(columns=self.class_parameter_names)

    def get_current_logbook(self):
        """
        Returns:
            A pandas dataframe including all instances that have been constructed so far.
        """
        return self._load_current_logbook()

    def get_class_index(self, use_saved: bool, parameter_names: list, parameter_values: list):
        assert len(parameter_names) == len(parameter_values)
        parameter_names_values = {n: v for n, v in zip(parameter_names, parameter_values)}
        new_entry = self._get_new_entry(parameter_names_values)
        if use_saved is True:
            # try finding an existing set of data
            existing_index = None
            for index, data in self.current_logbook.iterrows():
                for i, row in new_entry.iterrows():
                    if row.equals(data):
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
        empty_df.to_csv(f"{PATH_OUTPUT_AUTOSAVE}temp.csv")
        empty_df = pd.read_csv(f"{PATH_OUTPUT_AUTOSAVE}temp.csv", index_col=0, dtype=object)
        return empty_df

    def _record_new_entry(self, new_entry: pd.DataFrame):
        self.current_logbook = pd.concat([self.current_logbook, new_entry])
        # update the file immediately
        self.current_logbook.to_csv(self.class_logbook_path)
        self.current_logbook = self._load_current_logbook()


class MethodLogbook(Logbook):

    """
    The Logbook to be used for methods.
    """

    def __init__(self, class_name: str, class_parameter_names: list):
        super().__init__(class_name, path_to_use=PATH_OUTPUT_METHODBOOK, class_parameter_names=class_parameter_names)


class ClassLogbook(Logbook):

    """
    The Logbook to be used for classes.
    """

    def __init__(self, class_name: str, class_parameter_names: list):
        super().__init__(class_name, path_to_use=PATH_OUTPUT_LOGBOOK, class_parameter_names=class_parameter_names)


class ScientificObject(ABC):

    """
    Inherit from this object to get your class registered in a Logbook and logged & also to be able to use the
    wrapper sci_method.
    """

    def __init__(self, *args, use_saved: bool = True, use_logger: bool = True, **kwargs):
        """
        A ScientificObject knows that scientific calculations sometimes take a long time and depend on a ton of
        parameters. That is why this class offers a logger that records parameters of the class and every performed
        method and a wrapper that dumps the output of selected methods to a file.

        An object is associated with a name <class_name>_<class_index>.
        A method of an object is associated with a name <class_name>_<class_index>_<method_name>_<method_index>

        Args:
            use_saved (bool): use True if you want to re-use saved outputs if available
            use_logger (bool): use True if you want to log the parameters and runtimes of classes and methods (you
            really should only turn it off for testing/repeated, uninteresting uses)
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
            self.logger.info(f" ======== SET UP OF: {self.name} ======== ")
            self.logger.info(f"Object initiated at {str(datetime.now())}")
            for n, v in zip(my_parameter_names, my_parameter_values):
                self.logger.info(f"{n}={v}")

    def get_name(self) -> str:
        """
        Name of this class instance consists of ClassName and a 5-digit integer.

        Returns:
            string of the form <class_name>_<class_index>

        """
        return self.name


def sci_method(my_method: Callable):
    """
    This is the wrapper to use for methods that need input parameters and output saved. Simply apply as @sci_wrapper
    before your method (belonging to a class derived from ScientificObject).

    A list of things that happen with this wrapper:
    - a string will be associated with this method run: <class_name>_<class_index>_<method_name>_<method_index>
    - parameters of the method will be added to PATH_OUTPUT_LOGBOOK/<class_name>_<class_index>_<method_name>
    - the output will be saved to PATH_OUTPUT_AUTOSAVE/<class_name>_<class_index>_<method_name>_<method_index>
    - the log of this process (arguments, runtime, name) will be saved to PATH_OUTPUT_LOGGING/<class_name>_<class_index>
    (All of this does not happen if the exact same parameters have been used before and self.use_saved = True,
    in this case, only the already saved output is returned.)

    Args:
        my_method (Callable): a method to which the wrapper should be applied

    Returns:
        the output of my_method
    """
    @wraps(my_method)
    def decorated(*args, return_method_name: bool = False, **kwargs):
        """
        The args and kwargs will be passes to my_method and its output will be returned. For more details see the
        description of the sci_method wrapper.

        Args:
            *args (): named arguments of the method, the first of which must be self
            return_method_name: if True, will return a tuple (output, name)
            **kwargs (): keyword arguments of the method

        Returns:
            whatever my_method returns
        """
        self = args[0]
        args = args[1:]
        assert issubclass(self.__class__, ScientificObject), "Can only use sci_method on subclasses of ScientificObject"

        # determine method index
        names = list(inspect.getfullargspec(my_method).args[1:])
        names.extend(kwargs.keys())
        values = list(args)
        defaults = inspect.getfullargspec(my_method).defaults
        if any(defaults):
            values.extend(defaults)
        values.extend(kwargs.values())
        my_method_logbook = MethodLogbook(f"{self.get_name()}_{my_method.__name__}", names)
        my_method_index = my_method_logbook.get_class_index(self.use_saved, names, values)

        my_method_name = f"{self.get_name()}_{my_method.__name__}_{my_method_index:05d}"
        my_path = f"{PATH_OUTPUT_AUTOSAVE}{my_method_name}"

        # try to find a suitable saved file
        if self.use_saved:
            if os.path.isfile(f"{my_path}.npy"):
                return np.load(f"{my_path}.npy")
            elif os.path.isfile(f"{my_path}.csv"):
                return pd.read_csv(f"{my_path}.csv", index_col=0)
            elif os.path.isfile(my_path):
                with open(my_path, 'rb') as f:
                    loaded_data = pickle.load(f)
                return loaded_data

        # actually running
        t1 = time()
        output = my_method(self, *args, **kwargs)
        t2 = time()

        if self.use_logger:

            my_text = ""
            for n, v in zip(names, values):
                my_text += f"\n{n}={v}"
            self.logger.info(f" ###### RAN THE METHOD {my_method.__name__} ###### ")
            self.logger.info(f"Run started at {str(datetime.now())}")
            self.logger.info(f"Arguments of the method: {my_text}")
            self.logger.info(f"Method output is available at: {my_path}")
            self.logger.info(f"Runtime of the method is {timedelta(seconds=t2 - t1)} hours:minutes:seconds")

        # dumping output
        if isinstance(output, pd.DataFrame):
            output.to_csv(f"{my_path}.csv", index=True)
        elif isinstance(output, np.ndarray):
            np.save(f"{my_path}.npy", output)
        else:
            with open(my_path, 'wb') as f:
                pickle.dump(output, f)

        if return_method_name:
            return output, my_method_name
        return output

    return decorated



