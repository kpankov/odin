"""VCS GIT module
"""
import logging
import os

import git

import core.printer

logger = logging.getLogger(__name__)


class VcsGit(object):
    """Class for git repositories
    """

    def __init__(self, local_path, url=None):
        """Constructor for VcsGit class.
        :param local_path:
            Local path for git repo
        :param url:
            URL for remote repo
        """
        self._url = url
        self._local_path = local_path
        self._repo = None

    def clone(self) -> bool:
        """Clone repo into local dir.
        :return:
            True if cloned or False in case of errors
        """
        if self._url is None:
            logger.error("You must set URL for the git repo clone!")
            return False
        if self._local_path is None:
            logger.error("You must set local path for the git repo clone!")
            return False
        self._repo = git.Repo.clone_from(url=self._url, to_path=self._local_path)
        if self._repo.__class__ is git.Repo:
            return True
        else:
            logger.error("Can't clone repo from {} to {}!".format(self._url, self._local_path))
            return False

    def close(self) -> None:
        """You can use this method in case of other user wants to manage git repo or for removing repo.
        """
        self._repo.close()

    def checkout(self, branch_or_hash):
        """Checkout branch or commit
        :param branch_or_hash:
            Branch name or commit hash
        :return:
            The active branch after the checkout operation, usually self unless a new branch has been created.
            If there is no active branch, as the HEAD is now detached, the HEAD reference will be returned instead.
        """
        return self._repo.git.checkout(branch_or_hash)

    def get_status(self):
        """Use this method if you want to get information about untracked, changed or staged files  in
        the repository.
        :return:
            Returns a dictionary with fields: untracked, changed, staged. Each field is a list of files or empty list.
        """
        if self._repo.is_dirty() is False and not bool(self._repo.untracked_files):
            return None
        result = {"untracked": self._repo.untracked_files, "changed": [], "staged": []}
        if self._repo.is_dirty():
            result["changed"] = [item.a_path for item in self._repo.index.diff(None)]
            result["staged"] = [item.a_path for item in self._repo.index.diff('Head')]
        return result

    def submodule_update(self) -> int:  # TODO: Switch to gitpython
        """You can get and update all submodules in the repository using this method.
        :return:
            Git submodule return code.
        """
        if self._local_path is None:
            logger.error("Can't update submodule! Wrong local_path?")
            return -1
        else:
            odin_path = os.path.dirname(os.path.dirname(self._local_path))
            command = "cd {} && git submodule update --init --remote {}".format(odin_path, os.path.relpath(self._local_path, odin_path))
            core.printer.cmd(command)
            logger.info(command)
            return os.system(command)

    def log(self, length=1, branch="master"):
        """Get list of commit hashes. Latest commit first.
        :param length:
            Number of commits to get
        :param branch:
            Branch name, default "master"
        :return:
            List of commit hashes
        """
        return list(str(commit) for commit in self._repo.iter_commits(branch, max_count=length))
