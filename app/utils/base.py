from typing import Any


def table_args(
        cls: type,
        __table_args__: dict[str, Any] | tuple[Any, ...]
) -> dict[str, Any] | tuple[Any, ...]:
    """
    Helper class function to merge the __table_args__ attr of a
    SQLAlchemy model that has some inheritance. Use it like this:

    from sqlalchemy.ext.declarative import declared_attr

    class MyModel(MixinOne, MixinTwo, MixinThree, Base):
        __tablename__ = "my_table"

        @declared_attr
        def __table_args__(cls):
            return table_args(cls, {"schema": "my_database"})
    """
    args: dict[Any, None] = {}  # Store args in keys of dictionary for fast lookup and no duplicates
    kwargs: dict[str, Any] = {}
    table_args_attrs = []

    # Collect immediate parent "__table_args__" in reverse order
    for class_ in reversed(cls.__bases__):
        table_args_attr = getattr(class_, "__table_args__", None)
        if table_args_attr:
            table_args_attrs.append(table_args_attr)

    # Also merge the current table args
    table_args_attrs.append(__table_args__)

    for table_args_attr in table_args_attrs:
        # Handle simple dictionary use case first
        if isinstance(table_args_attr, dict):
            kwargs.update(table_args_attr)
            continue

        if isinstance(table_args_attr, tuple):
            if not table_args_attr:
                raise ValueError(f'Empty table arguments found')

            # Add all but last positional argument, if it is not already added
            for positional_arg in table_args_attr[:-1]:
                if positional_arg not in args:
                    args[positional_arg] = None

            last_positional_arg = table_args_attr[-1]
            if isinstance(last_positional_arg, dict):
                kwargs.update(last_positional_arg)
            elif last_positional_arg not in args:
                args[last_positional_arg] = None

    # Either return a tuple or a dictionary depending on what was found
    if args:
        if kwargs:
            return (*args, kwargs)
        else:
            return tuple(args)
    else:
        return kwargs
