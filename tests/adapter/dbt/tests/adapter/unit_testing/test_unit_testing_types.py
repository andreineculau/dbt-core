import pytest

from dbt.tests.util import write_file, run_dbt


my_model_sql = """
select
    tested_column from {{ ref('my_upstream_model')}}
"""

my_upstream_model_sql = """
select
  {sql_value} as tested_column,
  {sql_value} as untested_column
"""

test_my_model_yml = """
unit_tests:
  - name: test_my_model
    model: my_model
    given:
      - input: ref('my_upstream_model')
        rows:
          - {{ tested_column: {yaml_value} }}
    expect:
      rows:
        - {{ tested_column: {yaml_value} }}
"""


class BaseUnitTestingTypes:
    @pytest.fixture
    def data_types(self):
        # sql_value, yaml_value
        return [
            ["1", "1"],
            ["1.0", "1.0"],
            ["'1'", "1"],
            ["'1'::numeric", "1"],
            ["'string'", "string"],
            ["true", "true"],
            ["DATE '2020-01-02'", "2020-01-02"],
            ["TIMESTAMP '2013-11-03 00:00:00-0'", "2013-11-03 00:00:00-0"],
            ["TIMESTAMPTZ '2013-11-03 00:00:00-0'", "2013-11-03 00:00:00-0"],
            ["ARRAY[1,2,3]", """'{1, 2, 3}'"""],
            ["ARRAY[1.0,2.0,3.0]", """'{1.0, 2.0, 3.0}'"""],
            ["ARRAY[1::numeric,2::numeric,3::numeric]", """'{1.0, 2.0, 3.0}'"""],
            ["ARRAY['a','b','c']", """'{"a", "b", "c"}'"""],
            ["ARRAY[true,true,false]", """'{true, true, false}'"""],
            ["ARRAY[DATE '2020-01-02']", """'{"2020-01-02"}'"""],
            ["ARRAY[TIMESTAMP '2013-11-03 00:00:00-0']", """'{"2013-11-03 00:00:00-0"}'"""],
            ["ARRAY[TIMESTAMPTZ '2013-11-03 00:00:00-0']", """'{"2013-11-03 00:00:00-0"}'"""],
            [
                """'{"bar": "baz", "balance": 7.77, "active": false}'::json""",
                """'{"bar": "baz", "balance": 7.77, "active": false}'""",
            ],
        ]

    @pytest.fixture(scope="class")
    def models(self):
        return {
            "my_model.sql": my_model_sql,
            "my_upstream_model.sql": my_upstream_model_sql,
            "schema.yml": test_my_model_yml,
        }

    def test_unit_test_data_type(self, project, data_types):
        for (sql_value, yaml_value) in data_types:
            # Write parametrized type value to sql files
            write_file(
                my_upstream_model_sql.format(sql_value=sql_value),
                "models",
                "my_upstream_model.sql",
            )

            # Write parametrized type value to unit test yaml definition
            write_file(
                test_my_model_yml.format(yaml_value=yaml_value),
                "models",
                "schema.yml",
            )

            results = run_dbt(["run", "--select", "my_upstream_model"])
            assert len(results) == 1

            try:
                run_dbt(["unit-test", "--select", "my_model"])
            except Exception:
                raise AssertionError(f"unit test failed when testing model with {sql_value}")


class TestUnitTestingTypes(BaseUnitTestingTypes):
    pass