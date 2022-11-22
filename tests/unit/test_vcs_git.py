import os
import unittest
import shutil
import time

from core.vcs_git import VcsGit


def onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def tmp_dir_remove(test_dir_path):
    if os.path.exists(test_dir_path):
        print("Clean directory {}".format(test_dir_path))
        while os.path.isdir(test_dir_path):
            shutil.rmtree(test_dir_path, onerror=onerror)


class TestVcsGit(unittest.TestCase):
    _test_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_test_repo_")
    _test_git_url = "https://github.com/kpankov/odin.git"
    _test_git_branch = "test"
    _test_git_hash = "1dc5d175569"
    _test_untracked_file_name = "test.test"
    _test_changed_file_name = "requirements.txt"

    def test_000_clone_simple(self):
        tmp_dir_remove(self._test_dir_path)
        print("Clone...")
        repo = VcsGit(self._test_dir_path, url=self._test_git_url)
        self.assertTrue(repo.clone())
        repo.close()
        tmp_dir_remove(self._test_dir_path)

    def test_010_checkout_branch(self):
        tmp_dir_remove(self._test_dir_path)
        print("Clone from {} to {}".format(self._test_git_url, self._test_dir_path))
        repo = VcsGit(self._test_dir_path, url=self._test_git_url)
        repo.clone()
        print("Checkout to branch \"{}\"".format(self._test_git_branch))
        repo.checkout(self._test_git_branch)
        pid = os.popen("cd {} && git rev-parse --abbrev-ref HEAD".format(self._test_dir_path))
        real_branch = pid.read().strip()
        pid.close()
        print("Real branch is \"{}\"".format(real_branch))
        self.assertEqual(real_branch, self._test_git_branch)
        repo.close()
        tmp_dir_remove(self._test_dir_path)

    def test_011_checkout_commit(self):
        tmp_dir_remove(self._test_dir_path)
        print("Clone from {} to {}".format(self._test_git_url, self._test_dir_path))
        repo = VcsGit(url=self._test_git_url, local_path=self._test_dir_path)
        repo.clone()
        print("Checkout to commit \"{}\"".format(self._test_git_hash))
        repo.checkout(self._test_git_hash)
        pid = os.popen("cd {} && git rev-parse HEAD".format(self._test_dir_path))
        real_branch = pid.read().strip()
        pid.close()
        print("Real hash is \"{}\"".format(real_branch))
        self.assertTrue(real_branch.startswith(self._test_git_hash))
        repo.close()
        tmp_dir_remove(self._test_dir_path)

    def test_020_get_status_simple(self):
        tmp_dir_remove(self._test_dir_path)
        print("Clone from {} to {}".format(self._test_git_url, self._test_dir_path))
        repo = VcsGit(url=self._test_git_url, local_path=self._test_dir_path)
        repo.clone()
        self.assertIsNone(repo.get_status())
        repo.close()
        tmp_dir_remove(self._test_dir_path)

    def test_021_get_status_untracked_file(self):
        tmp_dir_remove(self._test_dir_path)
        print("Clone from {} to {}".format(self._test_git_url, self._test_dir_path))
        repo = VcsGit(url=self._test_git_url, local_path=self._test_dir_path)
        repo.clone()
        with open(os.path.join(self._test_dir_path, self._test_untracked_file_name), "w") as test_file:
            test_file.write("test")
        status = repo.get_status()
        self.assertIsNotNone(status)
        print("{}".format(status))
        self.assertEqual(status["untracked"][0], self._test_untracked_file_name)
        repo.close()
        tmp_dir_remove(self._test_dir_path)

    def test_022_get_status_changed_file(self):
        tmp_dir_remove(self._test_dir_path)
        print("Clone from {} to {}".format(self._test_git_url, self._test_dir_path))
        repo = VcsGit(url=self._test_git_url, local_path=self._test_dir_path)
        repo.clone()
        with open(os.path.join(self._test_dir_path, self._test_changed_file_name), "a") as test_file:
            test_file.write("test")
        status = repo.get_status()
        self.assertIsNotNone(status)
        print("{}".format(status))
        self.assertEqual(status["changed"][0], self._test_changed_file_name)
        repo.close()
        tmp_dir_remove(self._test_dir_path)

    def test_023_get_status_staged_file(self):
        tmp_dir_remove(self._test_dir_path)
        print("Clone from {} to {}".format(self._test_git_url, self._test_dir_path))
        repo = VcsGit(url=self._test_git_url, local_path=self._test_dir_path)
        repo.clone()
        with open(os.path.join(self._test_dir_path, self._test_changed_file_name), "a") as test_file:
            test_file.write("test")
        os.system("cd {} && git add {}".format(self._test_dir_path, self._test_changed_file_name))
        status = repo.get_status()
        self.assertIsNotNone(status)
        print("{}".format(status))
        self.assertEqual(status["staged"][0], self._test_changed_file_name)
        repo.close()
        tmp_dir_remove(self._test_dir_path)

    def test_030_log_simple(self):
        tmp_dir_remove(self._test_dir_path)
        print("Clone from {} to {}".format(self._test_git_url, self._test_dir_path))
        repo = VcsGit(url=self._test_git_url, local_path=self._test_dir_path)
        repo.clone()
        commits = repo.log(length=10)
        print("\n".join(commits))
        self.assertEqual(len(commits), 10)
        repo.close()
        tmp_dir_remove(self._test_dir_path)

    def test_040_submodule_update(self):
        tmp_dir_remove(self._test_dir_path)
        print("Clone from {} to {}".format(self._test_git_url, self._test_dir_path))
        repo = VcsGit(url=self._test_git_url, local_path=self._test_dir_path)
        repo.clone()

        repo.submodule_update()

        flows_dir_path = os.path.join(self._test_dir_path, "flows")
        for flow in os.listdir(flows_dir_path):
            flow_abs_path = os.path.join(flows_dir_path, flow)
            if os.path.isdir(flow_abs_path) and flow != "common":
                readme_file_path = os.path.join(flow_abs_path, "readme.md")
                print("Checking flow \"{}\", file {}...".format(flow, readme_file_path))
                self.assertTrue(os.path.isfile(readme_file_path))

        repo.close()
        tmp_dir_remove(self._test_dir_path)


if __name__ == '__main__':
    unittest.main()
