"""Shared command-line option for selecting a target ranking score."""
import argparse
import re


def ranking_column(value):
    if not re.fullmatch(r"-?[A-Za-z][A-Za-z0-9_]*", value):
        raise argparse.ArgumentTypeError("Use one CSV column name, optionally prefixed with '-' to reverse ranking")
    return value


def add_ranking_argument(parser):
    parser.add_argument(
        "-r", "--rankColumn", type=ranking_column, default="E", metavar="COLUMN",
        help="numeric CSV column for target ranking (default: E, lowest first); "
             "use --rankColumn=-COLUMN for highest first",
    )
