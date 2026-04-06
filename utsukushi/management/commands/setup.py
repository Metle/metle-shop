# coding=utf-8
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
import importlib

class Command(BaseCommand):

    help = 'Setup users, groups, permissions and data for an app'

    def add_arguments(self, parser):
        # Required argument
        # parser.add_argument('-a', '--app', type=str, required=True, help='Specify a app name', )
        parser.add_argument('-a', '--app', type=str, default='store', help='Specify a app name', )

    @transaction.atomic()
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting...'), ending='\n')

        app = options.get('app')

        try:
            module = importlib.import_module("utsukushi.management.commands.setupfiles."+app+".setup")
            module.start(self)

        except ImportError as e:
            self.stdout.write(self.style.ERROR(str(e)), ending='\n')
