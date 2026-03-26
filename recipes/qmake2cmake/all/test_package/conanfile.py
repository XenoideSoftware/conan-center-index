import os

from conan import ConanFile
from conan.tools.layout import basic_layout
from conan.tools.build import can_run


class Qmake2CmakeTestConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def build(self):
        # Convert a minimal .pro file to CMakeLists.txt
        pro_path = os.path.join(self.source_folder, "test.pro")
        self.run(f"qmake2cmake \"{pro_path}\"", env="conanbuild")

    def test(self):
        if can_run(self):
            cmake_path = os.path.join(self.source_folder, "CMakeLists.txt")
            assert os.path.isfile(cmake_path), f"Expected CMakeLists.txt at {cmake_path}"
            self.output.info("qmake2cmake successfully generated CMakeLists.txt")
