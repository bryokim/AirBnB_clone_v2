#!/usr/bin/python3
"""
Implements the do_pack function that creates a .tgz archive
from the web_static directory
"""

from fabric.api import *
from datetime import datetime

env.hosts = [
    '34.204.60.232',
    '54.160.126.236'
]


def do_pack():
    """
    Generates a .tgz archive from the contents of the web_static
    directory
    """

    # create versions directory if doesn't exist
    with settings(
        hide('warnings', 'running', 'stdout', 'stderr'),
        warn_only=True
    ):
        if local('test -d versions').failed:
            local('mkdir versions')

    # date in the format [<year> <month> <day> <hour> <minute> <second>]
    date = datetime.now().strftime("%Y%m%d%H%M%S")

    archive_path = f'versions/web_static_{date}.tgz'

    print(f'Packing web_static to {archive_path}')
    # Create archive for web_static in versions directory

    with settings(warn_only=True):
        if local(f'tar -cvzf {archive_path} web_static').failed:
            return None

    return archive_path


def do_deploy(archive_path):
    """Distributes an archive to the web server.

    Args:
        archive_path (str): path to the archive.

    Returns:
        Boolean: True if all operations have been done successfully,
            otherwise False is returned.
    """
    if not archive_path:
        return False

    with settings(warn_only=True):
        if local("test -f {}".format(archive_path)).failed:
            return False

        if put(archive_path, "/tmp/").failed:
            return False

        archive_filename = archive_path.split("/")[-1]
        archive_dir = archive_filename.split(".")[0]

        releases_dir = '/data/web_static/releases/'

        # Create a directory for the current archive.
        if run(f'mkdir {releases_dir}{archive_dir}').failed:
            return False

        if run(
            f'tar -xzf /tmp/{archive_filename} -C {releases_dir}{archive_dir}'
        ).failed:
            return False

        move_from = f'{releases_dir}{archive_dir}/web_static/*'
        move_to = f'{releases_dir}{archive_dir}'

        # Move all files in the uncompressed web_static folder to the
        # parent directory that is named after the archive.
        run(f'mv {move_from} {move_to}')

        # Delete the empty folder remaining after moving the files.
        run(f'rm -fr {releases_dir}{archive_dir}/web_static')

        # Delete the archive.
        sudo(f'rm -f /tmp/{archive_filename}')

        # Remove /data/web_static/current symbolic link and create a new one.
        run('rm -fr /data/web_static/current')
        if run(
            f'ln -s {releases_dir}{archive_dir} /data/web_static/current'
        ).failed:
            return False

        print("New version deployed!")
        return True
