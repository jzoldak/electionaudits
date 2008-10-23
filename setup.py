import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages
setup(
    name = "ElectionAudits",
    version = "0.8",
    author = "Neal McBurnett",
    author_email = "neal@bcn.boulder.co.us",
    description = "Help audit elections with good statistical confidence",
    license = "MIT",
    keywords = "audit election django",
    url = "http://neal.mcburnett.org/electionaudits/",
    long_description = """
ElectionAudits helps elections officials and/or citizens to work together
to implement good audits according to the "Principles and Best
Practices for Post-Election Audits"
(http://electionaudits.org/principles) and the other work of
ElectionAudits.org, the nation's clearinghouse for election audit
information.
""",

    packages = find_packages(),
    install_requires = ['lxml'], # and non-eggs: Django 1.0 and sqlite
    include_package_data = True,

    entry_points = {
        'setuptools.file_finders': [
            'bzr = setuptools_bzr:find_files_for_bzr',
            ],
        },
    setup_requires = [
        'setuptools_bzr',
        ],

    #entry_points = {
    #    'console_scripts': [
    #        'import = root.manage',   ???
    #        ],
    #    },
)
