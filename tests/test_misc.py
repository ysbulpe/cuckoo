# Copyright (C) 2016 Cuckoo Foundation.
# This file is part of Cuckoo Sandbox - http://www.cuckoosandbox.org
# See the file 'docs/LICENSE' for copying permission.

import mock
import os
import pytest
import subprocess
import sys
import tempfile
import time

from cuckoo.misc import dispatch, cwd, set_cwd, getuser, mkdir, Popen
from cuckoo.misc import HAVE_PWD, is_linux, is_windows, is_macosx

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

def return_value(value):
    return value

def sleep2(value):
    time.sleep(2)
    return value

def test_dispatch():
    assert dispatch(return_value, (1,)) == 1
    assert dispatch(return_value, ("foo",)) == "foo"

    assert dispatch(sleep2, (2,)) == 2
    assert dispatch(sleep2, (2,), timeout=1) is None

    with pytest.raises(RuntimeError):
        dispatch(None, args=None)

    with pytest.raises(RuntimeError):
        dispatch(None, kwargs=None)

    with pytest.raises(RuntimeError):
        dispatch(None, process=False)

def test_cwd():
    set_cwd("/tmp/foo")
    assert cwd() == "/tmp/foo"
    assert cwd("a") == os.path.join("/tmp/foo", "a")
    assert cwd("a", "b") == os.path.join("/tmp/foo", "a", "b")

    set_cwd("/home/user/.cuckoo", "~/.cuckoo")
    assert cwd(raw=True) == "~/.cuckoo"

    assert os.path.exists(cwd("guids.txt", private=True))

@pytest.mark.skipif("not HAVE_PWD")
def test_getuser():
    # TODO This probably doesn't work on all platforms.
    assert getuser() == subprocess.check_output(["id", "-un"]).strip()

def test_mkdir():
    dirpath = tempfile.mkdtemp()
    assert os.path.isdir(dirpath)
    mkdir(dirpath)
    assert os.path.isdir(dirpath)

    dirpath = tempfile.mktemp()
    assert not os.path.exists(dirpath)
    mkdir(dirpath)
    assert os.path.isdir(dirpath)

@pytest.mark.skipif("sys.platform != 'win32'")
def test_is_windows():
    assert is_windows() is True
    assert is_linux() is False
    assert is_macosx() is False

@pytest.mark.skipif("sys.platform != 'darwin'")
def test_is_macosx():
    assert is_windows() is False
    assert is_linux() is False
    assert is_macosx() is True

@pytest.mark.skipif("sys.platform != 'linux2'")
def test_is_windows():
    assert is_windows() is False
    assert is_linux() is True
    assert is_macosx() is False

def test_platforms():
    """Ensure that the above unit tests are complete (for our supported
    platforms)."""
    assert sys.platform in ("win32", "linux2", "darwin")

def test_popen():
    """Ensures that Popen is working properly."""
    with mock.patch("subprocess.Popen") as p:
        p.return_value = None
        Popen(["foo", "bar"])

    p.assert_called_once_with(["foo", "bar"])

    with mock.patch("subprocess.Popen") as p:
        p.return_value = None
        Popen(
            ["foo", "bar"], close_fds=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

    if is_windows():
        p.assert_called_once_with(
            ["foo", "bar"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    else:
        p.assert_called_once_with(
            ["foo", "bar"], close_fds=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

    # Test that the method actually works.
    p = Popen("echo 123", stdout=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    assert out.strip() == "123" and not err

    # The following would normally throw an exception on Windows.
    p = Popen("echo 1234", close_fds=True, stdout=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    assert out.strip() == "1234" and not err
