from sciobject import ScientificObject, ClassLogbook, sci_method, freshly_create_log_folders


def test_autosave():
    pass
    # if not use_saved should produce a new file

    # if use_saved should be exactly like the saved file

class ExampleObject(ScientificObject):

    def __init__(self, some_arg, some_kwarg=15, **kwargs):
        super().__init__(some_arg, some_kwarg=some_kwarg, **kwargs)

    @sci_method
    def example_method(self, one_arg: float, weird: float, one_kwarg=7):
        return 2 * one_arg + one_kwarg + weird ** 2


if __name__ == "__main__":
    freshly_create_log_folders()
    my_logbook = ClassLogbook("SomeClass", class_parameter_names=["param1", "param2"])

    eo1 = ExampleObject(22, random_kwarg="randomness", use_saved=False)
    print(eo1.get_name())
    print(eo1.example_method(97, 11))
    print(eo1.example_method(77, 8, one_kwarg=88888))
    print(eo1.example_method(97, 11, return_method_name=True))
    # eo1.example_method(15)
    # eo1.example_method(17, 3)