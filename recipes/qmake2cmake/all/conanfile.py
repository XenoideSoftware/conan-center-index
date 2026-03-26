import os
import textwrap

from conan import ConanFile
from conan.tools.files import copy, get, save
from conan.tools.layout import basic_layout

required_conan_version = ">=2.0"


class Qmake2CmakeConan(ConanFile):
    name = "qmake2cmake"
    description = "A tool to convert Qt qmake .pro project files to CMake"
    license = "GPL-3.0-only"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/qt/qmake2cmake"
    topics = ("qmake", "cmake", "converter", "qt")
    package_type = "application"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def build_requirements(self):
        # cpython is needed to run pip during packaging
        self.tool_requires("cpython/[>=3.10]", options={"shared": True})

    def package_id(self):
        # qmake2cmake is pure Python; the bundled dependencies (pyparsing, sympy,
        # packaging, platformdirs) are also pure Python. portalocker uses OS-level
        # locking APIs so the OS matters, but compiler and build_type do not.
        del self.info.settings.compiler
        del self.info.settings.build_type

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        """Install qmake2cmake and all its dependencies into a local site-packages dir."""
        python = self.dependencies.build["cpython"].conf_info.get("user.cpython:python")
        site_pkgs = os.path.join(self.build_folder, "site-packages")
        # --no-build-isolation uses the already-available pip; --target bundles
        # everything (qmake2cmake + all transitive deps) into one directory.
        self.run(f'"{python}" -m pip install --target "{site_pkgs}" "{self.source_folder}"')

    def package(self):
        copy(self, "LICENSE*", self.source_folder, os.path.join(self.package_folder, "licenses"))

        # Bundle the full Python package tree so the tool is self-contained.
        site_pkgs = os.path.join(self.build_folder, "site-packages")
        copy(self, "*", site_pkgs, os.path.join(self.package_folder, "lib", "qmake2cmake-site"))

        # Unix wrapper
        save(self, os.path.join(self.package_folder, "bin", "qmake2cmake"),
             textwrap.dedent("""\
                 #!/usr/bin/env bash
                 SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
                 export PYTHONPATH="${SCRIPT_DIR}/../lib/qmake2cmake-site${PYTHONPATH:+:${PYTHONPATH}}"
                 exec python3 -c "from qmake2cmake.__main__ import main; main()" "$@"
             """))

        # Windows wrapper
        save(self, os.path.join(self.package_folder, "bin", "qmake2cmake.cmd"),
             textwrap.dedent("""\
                 @echo off
                 set SCRIPT_DIR=%~dp0
                 set PYTHONPATH=%SCRIPT_DIR%..\lib\qmake2cmake-site;%PYTHONPATH%
                 python -c "from qmake2cmake.__main__ import main; main()" %*
             """))

    @staticmethod
    def _chmod_plus_x(filename):
        if os.name == "posix":
            os.chmod(filename, os.stat(filename).st_mode | 0o111)

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.frameworkdirs = []

        bindir = os.path.join(self.package_folder, "bin")
        self._chmod_plus_x(os.path.join(bindir, "qmake2cmake"))
        self.buildenv_info.prepend_path("PATH", bindir)
