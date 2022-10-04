"""VCS SOS module

This module allows the user to work with Cliosoft SoS VCS.
"""
import logging
import os
import re
import sys
from subprocess import PIPE, Popen
from typing import Union

from core.logger import Logger

logger = logging.getLogger(__name__)


class VcsSos(object):
    """Cliosoft SoS VCS class

    Parameters
    ----------
    path : str, optional
        Path to the SoS repository
    """
    soscmd_stdout = ''

    def __init__(self, path=None):
        self.path = path

    def __set_path_if_none(self, new_path):
        """Sets self.path if it is None

        Parameters
        ----------
        new_path : str
            New path of repository
        """
        if self.path is None:
            self.path = os.path.dirname(new_path)

    def run_sos_cli(self, command, amp=False):
        command_line = "cd {} && soscmd {}".format(self.path, command)
        if amp:
            command_line += " &"
        logger.debug(command_line)
        process_handle = Popen(command_line, stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process_handle.communicate()
        stdout, stderr = stdout.decode(sys.stdout.encoding or 'utf-8'), stderr.decode(sys.stderr.encoding or 'utf-8')
        process_return_code = process_handle.returncode
        if process_return_code != 0:
            Logger.error("Return code = {}".format(process_return_code))
            Logger.info("stdout: {}".format(stdout))
            Logger.red("stderr: {}".format(stderr))
        self.soscmd_stdout = stdout
        return process_return_code

    def open_gui(self):
        self.run_sos_cli("gui", amp=True)

    def create_workarea(self, user_name):
        """Creates workareas for all repositories in release.xml

        Parameters
        ----------
        user_name : str
            Name of SoS user
        """
        if os.path.exists(self.path):
            Logger.warning("Path \"{}\" already exists!".format(self.path))
            return
        else:
            path_parsed = re.findall(r"^\/proj\/([a-zA-Z0-9_-]+)\/workareas\/([a-zA-Z0-9_-]+)", self.path)
            project_name, workarea_name = path_parsed[0][0], path_parsed[0][1]
            command_line = "cd {} && ProjectCreateWorkarea -p {} -d {} -u {} -l USCA41".format(os.path.dirname(self.path), project_name, workarea_name, user_name)
            Logger.cmd(command_line)
            process_handle = Popen(command_line, stdout=PIPE, stderr=PIPE, shell=True)
            stdout, stderr = process_handle.communicate()
            stdout, stderr = stdout.decode(sys.stdout.encoding or 'utf-8'), stderr.decode(sys.stderr.encoding or 'utf-8')
            process_return_code = process_handle.returncode
            if process_return_code != 0:
                Logger.fatal("Return code = {}".format(process_return_code))

    def update(self, rso):
        rso_list = rso.split(" ")
        params = "update"
        for tag in rso_list:
            params += " -l{}".format(tag)
        self.run_sos_cli(params)

    def populate(self, path=None):
        self.run_sos_cli("populate .")

    def exit(self):
        self.run_sos_cli("exitsos")

    def checkout_wo_lock(self, file):
        """Checkout file without lock

        Parameters
        ----------
        file : str
            Path to file for checkout

        Returns
        -------
        : int
            Exit code of soscmd
        """
        self.__set_path_if_none(file)
        return self.run_sos_cli("co -Nlock {}".format(file))

    def checkin_or_discard(self, file, message="Checked in automatically"):
        """Checkin but discard the check out of any file or directory to which NO changes have been made.

        Parameters
        ----------
        file : str
            Path to the file
        message : str, optional
            Commit message
        """
        return self.run_sos_cli("ci -D -aLog=\"{}\" {}".format(message, file))

    def get_revision(self, file) -> str:
        """Get revison of file

        Parameters
        ----------
        file : str
            Path to the file

        Returns
        -------
        : str
            Revision (string) of the file
        """
        command_line = 'cd {} && soscmd objstatus -gaCurrentVer {}'.format(os.path.dirname(file), file)
        process_handle = Popen(command_line, stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process_handle.communicate()
        stdout, stderr = stdout.decode(sys.stdout.encoding or 'utf-8'), stderr.decode(sys.stderr.encoding or 'utf-8')
        process_return_code = process_handle.returncode
        if process_return_code != 0:
            Logger.fatal('Return code = {}'.format(process_return_code))
        # Parse output to find revision string
        status = re.findall(r"([0-6]+) ([0-4]+)\s*\{CurrentVer ([A-Za-z0-9/_]+)\}", stdout)
        if status != []:
            return status[0][2]
        else:
            Logger.fatal("Can't get status of file {}".format(file))

    def get_other_revision(self, file, revision):
        """Bring the selected revisions of the selected files into your workarea
        """
        self.__set_path_if_none(file)
        return self.run_sos_cli('exportrev {}/{}'.format(file, revision))

    def get_tags(self, path):  # TODO: Move to objstatus()
        """
        Get tag of object (path)
        :param path:
            Relative path
        :return:
            List of tags of the object
        """
        params = 'objstatus -gaTagList {}'.format(path)
        if self.run_sos_cli(params) == 0:
            labels = re.findall(r'TagList\s+{([^{}]+)}', self.soscmd_stdout)
            if not bool(labels):
                logger.warning("No tags!")
                return []
            return labels[0].split(' ')
        else:
            logger.warning('WARNING: get_tags() failed! SoS returned error code.')
            return []

    def set_tag_to_path(self, tag_name, path):
        """
        Set tag to object (path)
        :param tag_name:
            Name of the tag
        :param path:
            Relative path to apply the tag
        :return:
            0 if OK
        """
        if self.run_sos_cli('definetag {}'.format(tag_name)) != 0:
            logger.error('Can\'t create the tag {}!'.format(tag_name))
            return 1
        return self.run_sos_cli('tag -n{} -q -sm {}'.format(tag_name, path))

    def create(self, attributes: dict = None, file_paths: Union[str, list, None] = None):  # TODO
        # soscmd create [-a<attrname>=<attrvalue>] [-prj<ref_proj_name> [-d<ref_parent_dir>] [-cd<ref_parent_dir>] [-q]] [pathnames]
        params = ['create']
        if attributes is not None:
            for attr in attributes:
                params.append('-a{}="{}"'.format(attr, attributes[attr]))
        if file_paths is not None:
            if type(file_paths) is list:
                for file_path in file_paths:
                    params.append(file_path)
            else:
                params.append(file_paths)

        if self.run_sos_cli(' '.join(params)) == 0:
            print('out = {}'.format(self.soscmd_stdout))
            return True
        else:
            logger.warning('WARNING: create() failed! SoS returned error code.')
            return False

    def discardco(self, file_paths: Union[str, list, None] = None, select_options: str = None, force: bool = False,
                  myd: bool = False, ed: bool = False, verbose: bool = True) -> bool:
        """Cancels the check out of the selected files and directories.
        The check out lock placed on the file or directory is removed allowing others to check it out.
        The permissions of the file in your workarea is changed to read only.

        If a file or directory HAS been modified then it is NOT discarded and a warning is issued unless the '-F'
        option is provided. With the '-F' option the modified file will be discarded and all changes will be lost.

        The '-MYD' and '-ED' are mutually exclusive options.

        If neither option is specified, it implies discard check outs
        by you in this workarea only.

        :param file_paths:
            Paths to discard
        :param select_options:
            These are selection options (raw). Refer to help for the 'select' command.
        :param force:
            Discard check out of the file or directory even if changes have been made. The changes will be lost.
            Without this option changed files are not discarded.
        :param myd:
            Discard checkouts by you in any workarea.
        :param ed:
            Discard checkouts by everyone.
        :param verbose:
            Quiet or non-verbose mode if False. Do not print per object discarded checkout  message. Only command
            summary is printed along with the  object count.
        :return:
            True if all OK, False in case of errors.
        """

        params = ['discardco']
        if force:
            params.append('-F')
        if myd and ed:
            logger.error('The \'-MYD\' and \'-ED\' are mutually exclusive options!')
            return False
        if myd:
            params.append('-MYD')
        if ed:
            params.append('-ED')
        if not verbose:
            params.append('-q')
        if select_options is not None:
            params.append(select_options)
        if file_paths is not None:
            if type(file_paths) is list:
                for file_path in file_paths:
                    params.append(file_path)
            else:
                params.append(file_paths)

        if self.run_sos_cli(' '.join(params)) == 0:
            print('out = {}'.format(self.soscmd_stdout))
            return True
        else:
            logger.warning('WARNING: discardco() failed! SoS returned error code.')
            return False

    def objstatus(self, file_path: str, revision: Union[str, int, None] = None, attributes: Union[str, list, None] = None, local: bool = False) -> dict:
        """This command displays the status and attributes of the file or directory specified by pathname in
        the format used by the sos shared library.

        If rev option is not specified, the command returns the status of the current revision in the workarea.

        The status is returned in the form of 2 numbers where the first indicates the state of the object and
        second value indicates the object type.

        :param file_path:
            Name of file or directory to get the status of.
            This argument is mandatory and only one path can be specified.
        :param revision:
            Specify the version of object to get information about.
        :param attributes:
            This option is used to specify which attributes of the object should be returned by the command.
            If this option is not specified only the object state and type are returned; no attributes will be returned.
            If attrname is the special keyword 'All', then all available attributes are returned.
            (Multiple '-ga' options are allowed.)
        :param local:
            This option is used for optimization. It indicates that the object status should be returned from the
            information available in the client without querying with the server.
            This is typically used for large selections where the client already has the latest information after an
            update of flags & attributes.
        :return:
            Dict with 'status', 'type' and other attributes fields.

            The values for status are:
            0 - Path does not belong in the specified workarea
            1 - Object does not exist in the workarea
            2 - Object exists in the workarea, but is not managed by sos
            3 - Object is currently checked out in the workarea
            4 - Object is currently checked out in a different workarea
            5 - Object is currently checked in at the server
            6 - Object is currently checked out in the workarea but not locked in the server

            The values for object type are:
            0 - Object type not known
            1 - Object is a file
            2 - Object is a directory
            3 - Object is a package
            4 - Object is a symbolic link
        """

        obj_types = ['unknown', 'file', 'directory', 'package', 'symlink']

        params = ['objstatus']
        if revision is not None:
            params.append('-rev{}'.format(revision))
        if attributes is not None:
            if type(attributes) is list:
                for attr in attributes:
                    params.append('-ga{}'.format(attr))
            else:
                params.append('-ga{}'.format(attributes))
        if local:
            params.append('-ucl')
        params.append('{}'.format(file_path))

        result = {}
        if self.run_sos_cli(' '.join(params)) == 0:
            # First digits
            digits = re.findall(r'^(\d)\s(\d)', self.soscmd_stdout)
            result['status'] = int(digits[0][0])
            result['type'] = obj_types[int(digits[0][1])]
            # Simple attributes
            simple_attributes = re.findall(r'\{([\w]+)\s([^\{\}]+)\}[^\}]', self.soscmd_stdout)
            if bool(simple_attributes):
                for attr in simple_attributes:
                    result[attr[0]] = attr[1]
            # Lists
            lists_attributes = re.findall(r'\{([\w]+)\s\{([^\{\}]*)\}\}', self.soscmd_stdout)
            if bool(lists_attributes):
                for attr in lists_attributes:
                    result[attr[0]] = attr[1].split()
        else:
            logger.warning('WARNING: objstatus() failed! SoS returned error code.')
            return []

        return result

    def is_managed_file(self, file_path: str) -> bool:
        file_status = self.objstatus(file_path).get('status')
        if file_status is not None and file_status > 2:
            return True
        else:
            return False
