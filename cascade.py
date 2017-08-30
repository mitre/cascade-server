# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.


from __future__ import print_function

import argparse
import getpass
import logging

import app.async

parent_logger = logging.getLogger("app")


def configure_base_logger(args):
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
    ch.setFormatter(formatter)

    if not args.verbose:
        # normal running mode
        # Only show completely uncommon/unexpected errors.
        ch.setLevel(level=logging.ERROR)
        parent_logger.setLevel(level=logging.ERROR)

    elif args.verbose == 1:
        # Show expected/common errors
        ch.setLevel(level=logging.WARNING)
        parent_logger.setLevel(level=logging.WARNING)

    elif args.verbose == 2:
        # show normal program logic
        ch.setLevel(level=logging.INFO)
        parent_logger.setLevel(level=logging.INFO)

    elif args.verbose >= 3:
        # show EVERYTHING
        ch.setLevel(level=logging.DEBUG)
        parent_logger.setLevel(level=logging.DEBUG)

    parent_logger.addHandler(ch)


def get_password(username=None):
    prompt = "Password for {}: ".format(username) if username else "Password: "

    while True:
        password = getpass.getpass(prompt)
        if getpass.getpass("Confirm: ") == password:
            return password.strip()
        print("Password did not match. Try again...")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="CASCADE Server",
        epilog="As an alternative to the command-line, params can be placed in a file, "
               "one per line, and specified on the command line like '%(prog)s @params.conf'.",
        fromfile_prefix_chars='@'
    )
    parser.add_argument('-v', '--verbose', action="count", help="Logging verbosity -v=warning -vv=info -vvv=debug")

    job_runner = parser.add_argument_group('Job Runner')
    job_runner.add_argument('--jobs', '-j', '--job_runner', help='Run the Job runner service', action='store_true')

    setup_commands = parser.add_argument_group('Initialization')
    setup_commands.add_argument("--setup", help='Initialize cascade.yml settings and load database from .bson files', action='store_true')
    setup_commands.add_argument("--setup_with_defaults", help='Initialize cascade.yml automatically based on the '
                                                              'settings stored in defaults.yml (without prompting the '
                                                              'user', action='store_true')

    user_group = parser.add_argument_group('User Management')
    user_commands = user_group.add_mutually_exclusive_group()
    reset_group = parser.add_argument_group('Password Resets')

    # user_group = group.add_mutually_exclusive_group()
    user_commands.add_argument('--create_user', metavar='username', help='Create a new CASCADE user.', action='store')
    user_commands.add_argument('--change_password', metavar='username', help='Change password for user via console.', action='store')

    reset_group.add_argument('--reset_password', metavar='username', help='Print out password reset link to console.', action='store')
    reset_group.add_argument('--send_email', help='Send a password reset email to the user.', action='store_true', default=False)

    database_group = parser.add_argument_group('MongoDB Database Management')
    database_commands = database_group.add_mutually_exclusive_group()

    # io_group = database_commands.add_argument_group('I/O Commands')
    # io_commands = io_group.add_mutually_exclusive_group()
    database_commands.add_argument("-e", "--export_collection", "--export", metavar='exportFile.bson', help="Export MongoDB collections to disk", action="store")
    database_commands.add_argument("-i", "--import_collection", "--import", metavar='importFile.bson', help="Import MongoDB collections to disk", action="store")
    database_commands.add_argument("-p", "--purge", help="Remove the specified collections from MongoDB", action="store_true")

    # database_flags = database_group.add_mutually_exclusive_group()
    database_group.add_argument('-a', '--all', help='Select all MongoDB Collections', action='store_true')
    database_group.add_argument("-c", "--collection", metavar='collection_name', help="Collection to import/export", action="append")
    database_group.add_argument("--overwrite", help='Do NOT prompt when overwriting existing collection', action='store_true')

    args = parser.parse_args()

    # Turn on debug printing automatically if a debugger is attached
    try:
        import pydevd
        debug = True
        args.verbose = 3

    except ImportError:
        debug = False

    # setup parent logger
    configure_base_logger(args)

    if args.export_collection:
        app.utils.export_database(args.export_collection, collections=args.collection, select_all=args.all)

    elif args.import_collection:
        app.utils.import_database_from_file(args.import_collection, collections=args.collection, overwrite=args.overwrite)

    elif args.purge:
        app.utils.purge_database(args.collection, select_all=args.all)

    elif args.jobs:
        app.server.run_job_loop()

    elif args.create_user:
        user_name = args.create_user
        password = get_password(user_name)
        email = raw_input("Email: ").strip()
        full_name = raw_input("Full Name: ").strip()

        import app.users
        app.server.connect_to_database()
        user = app.users.create_user(user_name, password, email, full_name)
        print("User created successfully" if user else "ERROR! User already exists. Try --change_password")

    elif args.change_password:
        user_name = args.change_password

        import app.users
        app.server.connect_to_database()
        user = app.users.User.objects(username=user_name).first()
        if user is None:
            print("User not found!")
            exit()

        user.set_password(get_password(user_name))
        user.save()
        print("Password set successfully.")

    elif args.reset_password:
        user_name = args.reset_password

        import app.users
        app.server.connect_to_database()
        user = app.users.User.objects(username=user_name).first()
        if user is None:
            print("User not found!")
            exit()

        if args.send_email:
            user.send_reset_email()

        else:
            print("Reset link\n{url}".format(url=user.generate_reset_link()))

    elif args.setup:
        import app.settings
        app.settings.setup()

    elif args.setup_with_defaults:
        import app.settings
        app.settings.setup(auto_defaults=True)

    else:
        from app import plugin_loader

        plug = plugin_loader.PluginLoader()
        plug.enumerate_plugins()
        plug.load_plugins()
        app.server.run_server(debug=debug)

