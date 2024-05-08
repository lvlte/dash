import json

import pytest

from dash import Dash, html, dcc, Output, Input, State, Patch
from dash.exceptions import PreventUpdate

from selenium.webdriver.common.keys import Keys

sample_dropdown_options = [
    {"label": "New York City", "value": "NYC"},
    {"label": "Montreal", "value": "MTL"},
    {"label": "San Francisco", "value": "SF"},
]


@pytest.mark.parametrize("searchable", (True, False))
def test_ddro001_remove_option_single(dash_dcc, searchable):
    dropdown_options = sample_dropdown_options

    app = Dash(__name__)
    value = "SF"

    app.layout = html.Div(
        [
            dcc.Dropdown(
                options=dropdown_options,
                value=value,
                searchable=searchable,
                id="dropdown",
            ),
            html.Button("Remove option", id="remove"),
            html.Div(id="value-output"),
        ]
    )

    @app.callback(Output("dropdown", "options"), [Input("remove", "n_clicks")])
    def on_click(n_clicks):
        if not n_clicks:
            raise PreventUpdate
        return sample_dropdown_options[:-1]

    @app.callback(Output("value-output", "children"), [Input("dropdown", "value")])
    def on_change(val):
        return val or "Nothing Here"

    dash_dcc.start_server(app)
    btn = dash_dcc.wait_for_element("#remove")
    btn.click()

    dash_dcc.wait_for_text_to_equal("#value-output", "Nothing Here")


@pytest.mark.parametrize("searchable", (True, False))
def test_ddro002_remove_option_multi(dash_dcc, searchable):
    dropdown_options = sample_dropdown_options

    app = Dash(__name__)
    value = ["MTL", "SF"]

    app.layout = html.Div(
        [
            dcc.Dropdown(
                options=dropdown_options,
                value=value,
                multi=True,
                id="dropdown",
                searchable=searchable,
            ),
            html.Button("Remove option", id="remove"),
            html.Div(id="value-output"),
        ]
    )

    @app.callback(Output("dropdown", "options"), [Input("remove", "n_clicks")])
    def on_click(n_clicks):
        if not n_clicks:
            raise PreventUpdate
        return sample_dropdown_options[:-1]

    @app.callback(Output("value-output", "children"), [Input("dropdown", "value")])
    def on_change(val):
        return json.dumps(val)

    dash_dcc.start_server(app)
    btn = dash_dcc.wait_for_element("#remove")
    btn.click()

    dash_dcc.wait_for_text_to_equal("#value-output", '["MTL"]')


def test_ddro003_remove_option_multiple_dropdowns(dash_dcc):
    app = Dash(__name__)
    app.layout = html.Div(
        [
            dcc.Dropdown(
                id="available-options",
                multi=True,
                options=sample_dropdown_options,
                value=["MTL", "NYC", "SF"],
            ),
            dcc.Dropdown(
                id="chosen",
                multi=True,
                options=sample_dropdown_options,
                value=["NYC", "SF"],
            ),
            html.Button(id="remove-btn", children="Remove"),
            html.Button(id="submit-btn", children="Submit"),
            html.Div(id="value-output"),
            html.Div(id="options-output"),
        ],
    )

    @app.callback(
        Output("chosen", "options"),
        Input("available-options", "value"),
    )
    def update_options(available_options):
        if available_options is None:
            return []
        else:
            return [{"label": i, "value": i} for i in available_options]

    @app.callback(
        Output("available-options", "options"), [Input("remove-btn", "n_clicks")]
    )
    def on_click(n_clicks):
        if not n_clicks:
            raise PreventUpdate
        return sample_dropdown_options[:-1]

    @app.callback(
        [Output("value-output", "children"), Output("options-output", "children")],
        Input("submit-btn", "n_clicks"),
        State("chosen", "options"),
        State("chosen", "value"),
    )
    def print_value(n_clicks, options, value):
        if not n_clicks:
            raise PreventUpdate
        return [json.dumps(value), json.dumps([i["value"] for i in options])]

    dash_dcc.start_server(app)
    btn = dash_dcc.wait_for_element("#remove-btn")
    btn.click()
    btn = dash_dcc.wait_for_element("#submit-btn")
    btn.click()
    dash_dcc.wait_for_text_to_equal("#value-output", '["NYC"]')
    dash_dcc.wait_for_text_to_equal("#options-output", '["MTL", "NYC"]')


def test_ddro004_empty_string_not_updated(dash_dcc):
    # The value should stay as empty string and not null.
    app = Dash()
    app.layout = html.Div(
        [
            dcc.Dropdown(["a", "b", "c"], value="", id="drop"),
            html.Div(id="output"),
            dcc.Store(data={"count": 0}, id="count"),
            html.Div(id="count-output"),
        ]
    )

    @app.callback(
        Output("output", "children"),
        Output("count", "data"),
        Input("drop", "value"),
    )
    def on_value(value):
        count = Patch()
        count.count += 1
        if value is None:
            return "Value is none", count
        return f"Value={value}", count

    app.clientside_callback(
        "data => data.count", Output("count-output", "children"), Input("count", "data")
    )

    dash_dcc.start_server(app)
    dash_dcc.wait_for_text_to_equal("#output", "Value=")

    dash_dcc.wait_for_text_to_equal("#count-output", "1")

    select_input = dash_dcc.find_element("#drop input")
    select_input.send_keys("a")
    select_input.send_keys(Keys.ENTER)

    dash_dcc.wait_for_text_to_equal("#output", "Value=a")
    dash_dcc.wait_for_text_to_equal("#count-output", "2")
