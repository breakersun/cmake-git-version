import argparse
import json
import logging
import shlex
import subprocess


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

    def format(self, info_json):
        self.info_json = info_json
        self.info_json['friendly_version'] \
            = f"{info_json.get('FullSemVer')}" \
              f"+rev{info_json.get('ShortSha')}" \
              f"-{'dirty' if info_json.get('UncommittedChanges') else ''}" \

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
    _parser.add_argument('template', help="Template file")
    _parser.add_argument('-o', '--output_file', help="Output file")
    return _parser.parse_args()


if __name__ == "__main__":
    args = parse_option()
    _logger.info(f"Template: {args.template}")
    _logger.info(f"Output: {args.output_file}")
    parser = GitversionParser()
    parser.parse()
    formatter = OutputFormatter(args.template)
    output = formatter.format(parser.info_json)
    if args.output_file:
        update_file(args.output_file, output)
    else:
        print(output)
