import os
import logging
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import electionaudits.parsers

class Command(BaseCommand):
    option_list = electionaudits.parsers.option_list + BaseCommand.option_list
    help = ("Parse and save electionaudits data")
    args = "[filename]"
    label = 'filename'

    requires_model_validation = True
    can_import_settings = True

    def handle(self, *args, **options):
        if len(args) < 1:
            args = [(os.path.join(os.path.dirname(__file__), '../../../testdata/testcum.xml'))]
            logging.debug("using test file: " + args[0])

        electionaudits.parsers.parse(args, Bunch(**options))

class Bunch:
    """Map a dictionary into a class for standard optparse referencing syntax"""

    def __init__(self, **kwds):
        self.__dict__.update(kwds)
