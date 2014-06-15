# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import AmbiguityError


class Command(BaseCommand):
    help = "Prints the SQL statements for the named migration."

    def add_arguments(self, parser):
        parser.add_argument('app_label',
            help='App label of the application containing the migration.')
        parser.add_argument('migration_name',
            help='Migration name to print the SQL for.')
        parser.add_argument('--database', default=DEFAULT_DB_ALIAS,
            help='Nominates a database to create SQL for. Defaults to the '
                 '"default" database.')
        parser.add_argument('--backwards', action='store_true', dest='backwards',
            default=False, help='Creates SQL to unapply the migration, rather than to apply it')

    def handle(self, *args, **options):
        # Get the database we're operating from
        connection = connections[options['database']]

        # Load up an executor to get all the migration data
        executor = MigrationExecutor(connection)

        # Resolve command-line arguments into a migration
        app_label, migration_name = options['app_label'], options['migration_name']
        if app_label not in executor.loader.migrated_apps:
            raise CommandError("App '%s' does not have migrations" % app_label)
        try:
            migration = executor.loader.get_migration_by_prefix(app_label, migration_name)
        except AmbiguityError:
            raise CommandError("More than one migration matches '%s' in app '%s'. Please be more specific." % (app_label, migration_name))
        except KeyError:
            raise CommandError("Cannot find a migration matching '%s' from app '%s'. Is it in INSTALLED_APPS?" % (app_label, migration_name))
        targets = [(app_label, migration.name)]

        # Make a plan that represents just the requested migrations and show SQL
        # for it
        plan = [(executor.loader.graph.nodes[targets[0]], options['backwards'])]
        sql_statements = executor.collect_sql(plan)
        for statement in sql_statements:
            self.stdout.write(statement)