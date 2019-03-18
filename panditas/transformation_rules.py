import numpy as np

from .models import DataFlow, TransformationRule

CHECK_CONDITIONS = [
    "==",
    "!=",
    ">",
    ">=",
    "<",
    "=<"
    "contains",
    "does not contain",
    "starts with",
    "does not start with",
    "ends with",
]
GROUP_FUNCTIONS = [
    "alpha max",
    "alpha min",
    "concatenate",
    "count",
    "first",
    "first filled",
    "last",
    "max",
    "min",
    "sum",
    "unique",
]


class CalculatedColumn(TransformationRule):
    column_name = None
    expression = None
    insert_position = -1

    def __init__(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass

    def _validate_expression(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass

    def run(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass


class ConditionalFill(TransformationRule):
    fill_column = None
    fill_value = None
    where_column = None
    where_condition = None
    where_condition_values = None

    def __init__(
        self,
        fill_column=None,
        fill_value=None,
        name=None,
        where_column=None,
        where_condition=None,
        where_condition_values=None,
    ):
        """Short summary.

        Parameters
        ----------
        fill_column : type
            Description of parameter `fill_column`.
        fill_value : type
            Description of parameter `fill_value`.
        name : type
            Description of parameter `name`.
        where_column : type
            Description of parameter `where_column`.
        where_condition : type
            Description of parameter `where_condition`.
        where_condition_values : type
            Description of parameter `where_condition_values`.
         : type
            Description of parameter ``.

        Returns
        -------
        type
            Description of returned object.

        """
        self.fill_column = fill_column
        self.fill_value = fill_value
        self.name = name
        self.where_column = where_column
        self.where_condition = where_condition
        self.where_condition_values = where_condition_values

    def _build_operator_expression(
        self, values=None, action=None, column=None, df=None
    ):
        """Short summary.

        Parameters
        ----------
        values : type
            Description of parameter `values`.
        action : type
            Description of parameter `action`.
        column : type
            Description of parameter `column`.
        df : type
            Description of parameter `df`.

        Returns
        -------
        type
            Description of returned object.

        """
        expressions = []
        for value in values:
            if value in df.columns:
                value = 'df["{0}"]'.format(value)
            elif isinstance(value, str) and df[column].dtype.type == np.object_:
                value = value.replace('"', '\\"')
                value = '"{0}"'.format(value)
            if df[column].dtype.type == np.int64 and not isinstance(value, int):
                value = int(value)
            if df[column].dtype.type == np.float64 and not isinstance(value, float):
                value = float(value)
            expression = '(df["{0}"] {1} {2})'.format(column, action, value)
            expressions.append(expression)

        # A large string of a != b | a !=c doesn't really make sense
        # Will assume that they intend to have an & in there when they use !=
        if "!" in action or "not" in action:
            expression = " & ".join(expressions)
        else:
            expression = " | ".join(expressions)

        return expression

    def _build_pandas_expression(self, column=None, action=None, values=None, df=None):
        """Create a string that represents a pandas expression.

        Parameters
        ----------
        column : type
            Description of parameter `column`.
        action : type
            Description of parameter `action`.
        values : type
            Description of parameter `values`.
        df : type
            Description of parameter `df`.

        Returns
        -------
        type
            Description of returned object.

        """
        expression = ""

        # Operator Style
        operators = ["==", "!="]

        # Method Style
        string_methods = {
            "contains": "contains",
            "not contains": "contains",
            "startswith": "startswith",
            "not startswith": "startswith",
            "endswith": "endswith",
            "not endswith": "endswith",
        }

        if action in operators:
            expression = self._build_operator_expression(
                values=values, action=action, column=column, df=df
            )
        elif action in string_methods:
            expression = self._build_string_expression(
                values, action, column, string_methods
            )
        else:
            raise Exception(
                "{0} is an invalid filter, ".format(action)
                + "needs to be one of {0}".format(", ".join(operators + string_methods))
            )
        return expression

    def _build_string_expression(self, values, action, column, string_methods):
        """Short summary.

        Parameters
        ----------
        values : type
            Description of parameter `values`.
        action : type
            Description of parameter `action`.
        column : type
            Description of parameter `column`.
        string_methods : type
            Description of parameter `string_methods`.

        Returns
        -------
        type
            Description of returned object.

        """
        negation = ""
        if "not" in action:
            negation = "~"
        expressions = []
        for value in values:
            if isinstance(value, str):
                value = '"{0}"'.format(value)
            expression = '({0}df["{1}"].str.{2}({3}))'.format(
                negation, column, string_methods[action], value
            )
            expressions.append(expression)
        if "!" in action or "not" in action:
            expression = " & ".join(expressions)
        else:
            expression = " | ".join(expressions)
        return expression

    def run(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        # TODO: If using contains or does not contain need to fillna
        df = DataFlow.get_output_df(self.input_data_sets[-1])
        available_columns = df.columns.tolist()
        if self.where_column not in available_columns:
            raise Exception(
                "{0} is an invalid column name, needs to be one of {1}".format(
                    self.where_column, ", ".join(available_columns)
                )
            )
        pd_expression = self._build_pandas_expression(
            column=self.where_column,
            action=self.where_condition,
            values=self.where_condition_values,
            df=df,
        )
        df[self.fill_column] = np.where(
            eval(pd_expression), self.fill_value, df[self.fill_column]
        )
        self.output_data_set = DataFlow.save_output_df(df, self.name)


class ConstantColumn(TransformationRule):
    column_name = None
    column_value = None

    def __init__(self, column_name=None, column_value=None, name=None):
        """Short summary.

        Parameters
        ----------
        column_name : type
            Description of parameter `column_name`.
        column_value : type
            Description of parameter `column_value`.
        name : type
            Description of parameter `name`.

        Returns
        -------
        type
            Description of returned object.

        """
        self.column_name = column_name
        self.column_value = column_value
        self.name = name

    def run(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        df = DataFlow.get_output_df(self.input_data_sets[-1])
        # TODO: Add support for reference to other column
        df[self.column_name] = self.column_value
        self.output_data_set = DataFlow.save_output_df(df, self.name)


class FilterBy(TransformationRule):
    column_name = None
    filter_conditions = None
    condition_values = None

    def __init__(self, column_name, filter_conditions, condition_values):
        """Short summary.

        Parameters
        ----------
        column_name : str
            Name of the column to be filtered
        filter_conditions : list
            Conditions to be filtered by
        condition_values: list
            values against which the conditions are applied

        Returns
        -------
        None

        """
        self.column_name = column_name
        self.filter_conditions = filter_conditions
        self.condition_values = condition_values

    def __repr__(self):
        return "FilterBy column: {}, with conditions: {} and condition values {}".format(
            self.column_name, self.filter_conditions, self.condition_values
        )

    def _validate_inputs(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        assert isinstance(self.column_name, str)
        assert isinstance(self.filter_conditions, list)
        assert isinstance(self.condition_values, list)
        for filter_condition in self.filter_conditions:
            assert (filter_condition in CHECK_CONDITIONS,
                    "Filter condition {} not found in CHECK_CONDITIONS".format(filter_condition))
        for condition_value in self.condition_values:
            assert (isinstance(condition_value, str) or isinstance(condition_value, int),
                    isinstance(condition_value, float) or isinstance(condition_value, bool))

    def run(self):
        """Filter a dataframe by comparing one column to other column or values

        Parameters
        ----------


        Returns
        -------
        None

        """
        df = DataFlow.get_output_df(self.input_data_sets[-1])
        for condition, value in zip(self.filter_conditions, self.condition_values):
            if condition in ["==", '!=', ">", ">=", "<", "=<"]:
                df = df.query(
                    '{column} {condition} {value}'.format(column=self.column_name,
                                                          condition=condition,
                                                          value=value)
                )
            elif condition == "contains":
                df = df[df[self.column_name].contains(value)]
            elif condition == "starts with":
                df = df[df[self.column_name].startswith(value)]
            elif condition == "ends with":
                df = df[df[self.column_name].endswith(value)]
            elif condition == "does not contain":
                df = df[~df[self.column_name].contains(value)]
            elif condition == "does not start with":
                df = df[~df[self.column_name].startswith(value)]
        self.output_data_set = DataFlow.save_output_df(df, self.name)


class FormatColumns(TransformationRule):
    column_formats = None

    def __init__(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass

    def run(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass


class MapValues(TransformationRule):
    default_map_value = None
    map_column = None
    map_values = None

    def __init__(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass

    def run(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass


class PivotTable(TransformationRule):
    group_columns = None
    group_functions = None
    group_values = None
    preserve_order = True

    def __init__(
        self,
        group_columns=None,
        group_functions=None,
        group_values=None,
        name=None,
        preserve_order=True,
    ):
        """Short summary.

        Parameters
        ----------
        group_columns : type
            Description of parameter `group_columns`.
        group_functions : type
            Description of parameter `group_functions`.
        group_values : type
            Description of parameter `group_values`.
        name : type
            Description of parameter `name`.
        preserve_order : type
            Description of parameter `preserve_order`.

        Returns
        -------
        type
            Description of returned object.

        """
        self.group_columns = group_columns
        self.group_functions = group_functions
        self.group_values = group_values
        self.name = name
        self.preserve_order = preserve_order

    def run(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        df = DataFlow.get_output_df(self.input_data_sets[-1])
        available_columns = df.columns.tolist()
        requested_columns = self.group_columns + self.group_values
        for requested_column in requested_columns:
            if requested_column not in available_columns:
                raise Exception(
                    "{0} is an invalid column, needs to be one of {1}".format(
                        requested_column, ", ".join(available_columns)
                    )
                )
        pivot_functions = {}
        # First add the cols provided for the pivot
        for key, column in enumerate(self.group_values):
            group_function = self.group_functions[key]
            if group_function == "unique":
                group_function = lambda x: ", ".join(set(str(v) for v in x if v))
            pivot_functions[column] = group_function
        # Add not specified ones with default (pandas uses mean)
        df = df[requested_columns]
        pivot_df = df.pivot_table(
            index=self.group_columns, values=self.group_values, aggfunc=pivot_functions
        ).reset_index()
        self.output_data_set = DataFlow.save_output_df(pivot_df, self.name)


class RemoveColumns(TransformationRule):
    column_names = None

    def __init__(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass

    def run(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass


class RemoveDuplicateRows(TransformationRule):
    columns_subset = None
    keep = False

    def __init__(self, columns_subset=None, keep=False):
        """Short summary.

        Parameters
        ----------
        columns_subset : list
            Names of the columns in which to search for duplicates
        keep : str
            if first or last, drop duplicates except first or last occurrence

        Returns
        -------
        None

        """
        self.columns_subset = columns_subset
        self.keep = keep

    def __repr__(self):
        return "RemoveDuplicateRows columns_subset: {}, keep: {}".format(
            self.columns_subset, self.keep
        )

    def _validate_inputs(self):
        if self.keep:
            assert self.keep == "first" or self.keep == "last", "keep can only be 'first', 'last' or None"

    def run(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        df = DataFlow.get_output_df(self.input_data_sets[-1])
        df = df.drop_duplicates(subset=self.columns_subset, keep=self.keep)
        self.output_data_set = DataFlow.save_output_df(df, self.name)


class RenameColumns(TransformationRule):
    columns = None

    def __init__(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass

    def run(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass


class ReplaceText(TransformationRule):
    column = None
    replace_pattern = None
    replace_pattern_is_regex = False
    replace_value = None
    replace_column = None

    def __init__(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass

    def run(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass


class SelectColumns(TransformationRule):
    columns = None

    def __init__(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass

    def run(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass


class SortValuesBy(TransformationRule):
    sort_columns = None
    sort_ascending = None

    def __init__(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass

    def run(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        pass
