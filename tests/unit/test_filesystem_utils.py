import os
from tempfile import TemporaryDirectory
from unittest import TestCase

from pyshrimp import glob_ls
from pyshrimp.exception import IllegalArgumentException
from pyshrimp.utils.filesystem import ls


def _make_file(dir_path, file_name):
    path = os.path.join(dir_path, file_name)
    with open(path, 'w'):
        pass

    return path


class Test(TestCase):

    def setUp(self) -> None:
        # {temp_dir}/a/b/
        #   -> file1.py
        #   -> file2.txt
        #   -> c
        #      -> file3.py
        self._temp_dir_obj = TemporaryDirectory('_pyshrimp_glob_ls_test')
        self.temp_dir = self._temp_dir_obj.name
        self.dir_path_a = os.path.join(self.temp_dir, 'a')
        self.dir_path_b = os.path.join(self.temp_dir, 'a', 'b')
        self.dir_path_c = os.path.join(self.temp_dir, 'a', 'b', 'c')
        os.makedirs(self.dir_path_c)
        self.file_path_1_b_f1_py = _make_file(self.dir_path_b, 'f1.py')
        self.file_path_2_b_f2_txt = _make_file(self.dir_path_b, 'f2.txt')
        self.file_path_3_c_f3_py = _make_file(self.dir_path_c, 'f3.py')

    def tearDown(self) -> None:
        self._temp_dir_obj.cleanup()

    def assertEqualAfterSort(self, a, b, msg=None):
        self.assertEqual(
            list(sorted(a)),
            list(sorted(b)),
            msg=msg
        )

    def test_ls_should_list_files(self):
        self.assertEqualAfterSort(
            [self.file_path_1_b_f1_py, self.file_path_2_b_f2_txt],
            ls(
                self.dir_path_b,
                files_only=True
            )
        )

    def test_ls_should_list_directories(self):
        self.assertEqualAfterSort(
            [self.dir_path_c],
            ls(
                self.dir_path_b,
                dirs_only=True
            )
        )

    def test_ls_should_accept_path_segments(self):
        self.assertEqualAfterSort(
            [self.dir_path_c],
            ls(
                self.dir_path_a, 'b',
                dirs_only=True
            )
        )

    def test_ls_should_raise_when_both_files_only_and_dirs_only_were_requested(self):
        with self.assertRaisesRegex(
            IllegalArgumentException,
            r'Illegal arguments - dirs_only and files_only cannot be true together'
        ):
            ls(
                self.dir_path_a,
                dirs_only=True,
                files_only=True
            )

    def test_glob_ls_should_raise_when_both_files_only_and_dirs_only_were_requested(self):
        with self.assertRaisesRegex(
            IllegalArgumentException,
            r'Illegal arguments - dirs_only and files_only cannot be true together'
        ):
            glob_ls(
                self.dir_path_a,
                dirs_only=True,
                files_only=True
            )

    def test_glob_ls_should_use_glob_matching_for_files(self):
        self.assertEqualAfterSort(
            [self.file_path_1_b_f1_py, self.file_path_3_c_f3_py],
            glob_ls(
                self.dir_path_b, '**', '*.py',
                files_only=True,
                recursive=True
            )
        )

    def test_glob_ls_should_use_glob_matching_for_directories(self):
        self.assertEqualAfterSort(
            [self.dir_path_b, self.dir_path_c],
            glob_ls(
                self.dir_path_a, '**', '*',
                dirs_only=True,
                recursive=True
            )
        )

        self.assertEqualAfterSort(
            [self.dir_path_b],
            glob_ls(
                self.dir_path_a, '**', 'b',
                dirs_only=True,
                recursive=True
            )
        )

    def test_glob_ls_should_remove_trailing_separator_from_results(self):
        self.assertEqualAfterSort(
            [self.dir_path_a, self.dir_path_b, self.dir_path_c],
            glob_ls(
                # due to ** usage the self.dir_path_a would normally be included with / at the end
                # the trailing separator removal deals with this
                self.dir_path_a, '**',
                dirs_only=True,
                recursive=True
            )
        )

    def test_glob_ls_should_not_use_recursion_by_default(self):
        self.assertEqualAfterSort(
            [self.file_path_1_b_f1_py],
            glob_ls(
                # with recursive=False the ** acts as *
                # so this is the same as a/*/*.py
                self.dir_path_a, '**', '*.py',
                files_only=True
            )
        )

    def test_glob_ls_should_return_empty_list_when_nothing_matched(self):
        self.assertEqualAfterSort(
            [],
            glob_ls(
                os.path.join(self.dir_path_a, '**', 'no-such-file'),
                files_only=True
            )
        )
