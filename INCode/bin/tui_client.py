# Copyright (C) 2020 R. Knuus

from INCode.call_tree_manager import CallTreeManager
from INCode.tui import TuiViewModel
from prompt_toolkit.history import FileHistory
import appdirs
import click
import click_repl
import os
import re


global manager
manager = CallTreeManager()
global root_callable
root_callable = None
view_model = TuiViewModel(manager)


def clean_up_usage_message_(message, command):
    '''Convert application help message into command help message.'''
    return re.sub('  --help\\s+Show this message and exit.', '\n',
                  message.replace('Usage: tui_client.py', '')  # TODO(KNR): parameterize script name
                         .replace('  help', command))


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    '''Pleasantries CLI'''
    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


@cli.command()
def repl():
    '''Start interactive entry dialog mock'''
    data_directory = appdirs.user_data_dir('INCode', 'rknuus')
    if not os.path.isdir(data_directory):
        try:
            os.makedirs(data_directory)
        except OSError:
            print("Creation of the directory %s failed" % data_directory)
            return
    prompt_kwargs = {
        'history': FileHistory('{}/.edmc_history.txt'.format(data_directory))
    }
    click_repl.repl(click.get_current_context(), prompt_kwargs=prompt_kwargs)


@cli.command()
def exit():
    '''NOT SUPPORTED: to exit press <CTRL>-D'''
    click.echo('NOT SUPPORTED: to exit press <CTRL>-D')


@cli.command()
@click.option('--file', prompt='Open compilation database or source file to analyze')
def open(file):
    '''Open compilation database or source file to analyze and print TUs'''
    global manager
    tu_list = manager.open(file)
    assert tu_list
    for i, tu in zip(range(len(tu_list)), tu_list):
        click.echo('{}: {}\n'.format(i + 1, tu))


@cli.command()
@click.option('--arguments', prompt='Set extra compiler arguments')
def set_extra_arguments(arguments):
    '''Set extra compiler arguments'''
    global manager
    manager.set_extra_arguments(arguments)


@cli.command()
@click.option('--file', prompt='Select translation unit to analyze')
@click.option('--include-system-headers', default=False, type=bool)
def select_tu(file, include_system_headers):
    '''Set translation unit to analyze'''
    global manager
    callable_list = manager.select_tu(file_name=file, include_system_headers=include_system_headers)
    assert callable_list
    for i, callable in zip(range(len(callable_list)), callable_list):
        click.echo('{}: {}\n'.format(i + 1, callable.name))


@cli.command()
@click.option('--root', prompt='Select root callable of the diagram')
def select_root(root):
    '''Set root callable of the diagram'''
    global manager
    global root_callable
    root_callable = manager.select_root(callable_name=root)
    view_model.set_root(root_callable)
    click.echo(view_model.view)


@cli.command()
@click.option('--callable-name', prompt='Enter signature of callable to load')
def load_definition(callable_name):
    '''Enter signature of callable to load'''
    if root_callable is None:
        click.echo('Error: call "select_root" first')
        return
    global manager
    manager.load_definition(callable_name=callable_name)
    click.echo(view_model.view)


@cli.command()
@click.option('--callable-name', prompt='Enter signature of callable to include')
def include(callable_name):
    '''Enter signature of callable to include'''
    if root_callable is None:
        click.echo('Error: call "select_root" first')
        return
    manager.include(callable_name=callable_name)
    click.echo(view_model.view)
    # click.echo(manager.dump_callable_(callable=root_callable, level=0, print_selection=True))


@cli.command()
def debug():
    '''Enters debugger (which cannot be left anymore!)'''
    global manager
    from pdb import set_trace
    set_trace()


@cli.command()
def help():
    '''Print this help'''
    for command in cli.commands.keys():
        message = cli.commands[command].get_help(click.get_current_context())
        click.echo(clean_up_usage_message_(message, command))


if __name__ == '__main__':
    cli(obj={})
