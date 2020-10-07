import attr


class PytestWarning(UserWarning):
    """
    Bases: :class:`UserWarning`.

    Base class for all warnings emitted by pytest.
    """


class PytestDeprecationWarning(PytestWarning, DeprecationWarning):
    """
    Bases: :class:`pytest.PytestWarning`, :class:`DeprecationWarning`.

    Warning class for features that will be removed in a future version.
    """


class RemovedInPytest4Warning(PytestDeprecationWarning):
    """
    Bases: :class:`pytest.PytestDeprecationWarning`.

    Warning class for features scheduled to be removed in pytest 4.0.
    """


class PytestExperimentalApiWarning(PytestWarning, FutureWarning):
    """
    Bases: :class:`pytest.PytestWarning`, :class:`FutureWarning`.

    Warning category used to denote experiments in pytest. Use sparingly as the API might change or even be
    removed completely in future version
    """

    @classmethod
    def simple(cls, apiname):
        return cls(
            "{apiname} is an experimental api that may change over time".format(
                apiname=apiname
            )
        )


@attr.s
class UnformattedWarning(object):
    """Used to hold warnings that need to format their message at runtime, as opposed to a direct message.

    Using this class avoids to keep all the warning types and messages in this module, avoiding misuse.
    """

    category = attr.ib()
    template = attr.ib()

    def format(self, **kwargs):
        """Returns an instance of the warning category, formatted with given kwargs"""
        return self.category(self.template.format(**kwargs))


PYTESTER_COPY_EXAMPLE = PytestExperimentalApiWarning.simple("testdir.copy_example")
