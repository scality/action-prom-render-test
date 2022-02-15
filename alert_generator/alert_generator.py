import argparse
import pathlib
import re
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO

from typing import Callable


yaml = YAML()


PLACEHOLDER_RE = re.compile(r'\$\{(?P<varname>.*?)\}')


def replace_func(inputs: dict, test_values: dict) -> Callable[[re.Match], str]:

    replvals = {
        item['name']: item for item in inputs
    }

    def replacement(match):
        key = match.group('varname')
        try:
            repl_input = replvals[key]
        except KeyError:
            raise Exception(f'Key {key} does not exist in inputs')

        if key not in test_values:
            if 'value' not in repl_input:
                raise Exception(f'Missing value for key {key}')
            return str(repl_input['value'])
        return str(test_values[key])
    return replacement


def replace_inputs(alert_text: str, test_values: dict) -> str:
    alert_dict = yaml.load(alert_text)
    inputs = alert_dict.get('x-inputs', {})

    stream = StringIO()
    yaml.dump({'groups': alert_dict.get('groups')}, stream)
    alert_text = PLACEHOLDER_RE.sub(
        replace_func(inputs, test_values),
        stream.getvalue()
    )
    return alert_text


def check_replacements(filename: pathlib.Path, test_values):
    with open(filename, 'r') as infile:
        file_text = infile.read()
    rendered_text = replace_inputs(file_text, test_values)
    matches = re.findall(PLACEHOLDER_RE, rendered_text)
    assert matches == [], matches


def test_render_file(
        filename: pathlib.Path,
        test_values,
        suffix: str = 'rendered'
) -> None:
    rendered_name = f'{filename.stem}.{suffix}{filename.suffix}'
    with open(filename, 'r') as alert_infile:
        file_text = alert_infile.read()
    rendered_text = replace_inputs(file_text, test_values)
    with open(rendered_name, 'w') as outfile:
        outfile.write(rendered_text)


def render(args):
    print(args.value)
    additional_values = {
        key: value for key, value in args.value
    }
    return test_render_file(args.file, additional_values)


def check(args):
    additional_values = {
        key: value for key, value in args.value
    }
    return check_replacements(args.file, additional_values)


def prepare_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    render_parser = subparsers.add_parser(
        'render',
        help='render the alert rule in the same manner as ZKOP would'
    )
    render_parser.add_argument(
        'file',
        help='relative path of the target file',
        type=lambda path: pathlib.Path.cwd() / path
    )
    render_parser.add_argument(
        '--value',
        required=True,
        nargs='+',
        type=lambda item: item.split(':'),
        help='an additional templating variable in key:value format'
    )
    render_parser.set_defaults(func=render)
    check_parser = subparsers.add_parser(
        'check',
        help='verify all template instances in rendered file were replaced'
    )
    check_parser.add_argument(
        'file',
        help='relative path of the target file',
        type=lambda path: pathlib.Path.cwd() / path
    )
    check_parser.add_argument(
        '--value',
        required=True,
        nargs='+',
        type=lambda item: item.split(':'),
        help='an additional templating variable in key:value format'
    )
    check_parser.set_defaults(func=check)
    return parser


def main():
    parser = prepare_parser()
    args = parser.parse_args()
    if 'func' not in args:
        parser.print_help()
    else:
        args.func(args)


if __name__ == '__main__':
    main()
