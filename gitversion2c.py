import argparse
import json
import logging
import shlex
import subprocess
import os


FORMAT = "%(levelname)7s %(asctime)s [%(filename)13s:%(lineno)4d] %(message)s"
DATEFMT = "%H:%M:%S"
logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=DATEFMT)

_logger = logging.getLogger(__name__)


class ShellError(Exception):
    pass


class FileError(Exception):
    pass


class GitversionParser(object):
    def __init__(self):
        self.info_json = {}

    def parse(self):
        _cmd = shlex.split('gitversion')
        _logger.info(f"Executing: {_cmd}")
        try:
            output = subprocess.check_output(_cmd, text=True)
            _logger.debug(f"Output: {output}")
            self.info_json = json.loads(output)
        except subprocess.CalledProcessError:
            _logger.error("Error executing gitversion")
            raise ShellError


class OutputFormatter(object):
    def __init__(self, template_file):
        self.info_json = None
        self.template_file = template_file

    @staticmethod
    def generate_friendly_version(info_json) -> str:
        return f"{info_json.get('FullSemVer')}" \
               f"+rev{info_json.get('ShortSha')}" \
               f"{'-dirty' if info_json.get('UncommittedChanges') else ''}"

    def format(self, info_json):
        self.info_json = info_json
        self.info_json['friendly_version'] = self.generate_friendly_version(self.info_json)
        with open(self.template_file, 'r') as _template_file:
            _template = _template_file.read()
            _logger.debug(f"Template: {_template}")
            _output = _template.format(**self.info_json)
            _logger.debug(f"Output: {_output}")
            return _output


def update_file(filename, new_contents):
    existing_contents = ""
    try:
        with open(filename, "r") as input_file:
            existing_contents = input_file.read()
    except FileNotFoundError:
        _logger.info(f"File {filename} not found")
    if existing_contents != new_contents:
        with open(filename, "w") as output_file:
            output_file.write(new_contents)


def parse_option():
    _parser = argparse.ArgumentParser(description="GitVerion Code Generator")
    subparsers = _parser.add_subparsers()
    gen_parser = subparsers.add_parser("generate", help="Generate code")
    gen_parser.add_argument('template', help="Template file")
    gen_parser.add_argument('-o', '--output_file', help="Output file, default to stdout")
    gen_parser.set_defaults(func=generate_code)
    rename_parser = subparsers.add_parser("rename", help='Rename artifact')
    rename_parser.add_argument('artifact', help="Path to artifact")
    rename_parser.add_argument('-proj', '--projectname', default='project', help="Project name as prefix")
    rename_parser.set_defaults(func=rename_artifact)
    return _parser.parse_args()


def rename_artifact(args):
    _logger.info(f"Renaming artifact {args.artifact}")
    _parser = GitversionParser()
    _parser.parse()
    friendly_version = OutputFormatter(None).generate_friendly_version(_parser.info_json)
    path, name = os.path.split(args.artifact)
    suffix = name.split('.')[-1]
    new_name = os.path.join(path, f"{args.projectname}-{friendly_version}.{suffix}")
    os.rename(args.artifact, new_name)


def generate_code(args):
    _logger.info(f"Generating code from {args.template}")
    _parser = GitversionParser()
    _parser.parse()
    _formatter = OutputFormatter(args.template)
    _output = _formatter.format(_parser.info_json)
    if args.output_file:
        update_file(args.output_file, _output)
    else:
        print(_output)


if __name__ == "__main__":
    args = parse_option()
    args.func(args)
