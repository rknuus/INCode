# Copyright (C) 2020 R. Knuus

from INCode.call_tree_manager import CallTreeManager
from prompt_toolkit.history import FileHistory
import click
import click_repl
import os
import re


global manager
manager = CallTreeManager()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    '''Pleasantries CLI'''
    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


@cli.command()
def exit():
    '''NOT SUPPORTED: Exit the program'''
    click.echo('NOT SUPPORTED: to exit press <CTRL>-D')


@cli.command()
@click.option('--file', prompt='Open compilation database or source file to analyze')
def open(file):
    '''Set compilation database or source file to analyze'''
    global manager
    tu_list = manager.open(file)
    assert tu_list
    for i, tu in zip(range(len(tu_list)), tu_list):
        click.echo('{}: {}\n'.format(i + 1, tu))


@cli.command()
@click.option('--file', prompt='Select translation unit to analyze')
def select_tu(file):
    '''Set translation unit to analyze'''
    global manager
    callable_list = manager.select_tu(file)
    assert callable_list
    for i, callable in zip(range(len(callable_list)), callable_list):
        click.echo('{}: {}\n'.format(i + 1, callable))


def clean_up_usage_message_(message, command):
    '''Convert application help message into command help message.'''
    return re.sub('  --help\\s+Show this message and exit.', '\n',
                  message.replace('Usage: entry_dialog_mock_client.py', '')
                         .replace('  help', command))


@cli.command()
def help():
    '''Print this help'''
    for command in cli.commands.keys():
        message = cli.commands[command].get_help(click.get_current_context())
        click.echo(clean_up_usage_message_(message, command))


@cli.command()
def repl():
    '''Start interactive entry dialog mock'''
    prompt_kwargs = {
        'history': FileHistory(os.path.expanduser('/tmp/.edmc_history.txt'))
    }
    click_repl.repl(click.get_current_context(), prompt_kwargs=prompt_kwargs)


if __name__ == '__main__':
    cli(obj={})
