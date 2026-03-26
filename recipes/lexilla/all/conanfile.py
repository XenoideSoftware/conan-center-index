import glob
import os
import shutil
from os.path import join

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get


class LexillaConanfile(ConanFile):
    name = "lexilla"
    description = "Lexilla - A library of language lexers for use with Scintilla"
    license = "HPND"
    homepage = "https://www.scintilla.org/Lexilla.html"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "compiler", "build_type", "arch"

    exports_sources = "CMakeLists.txt"

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def requirements(self):
        self.requires(f"scintilla/[>={self.version}]")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def generate(self):
        # Copy the exported CMakeLists.txt into source_folder so cmake can find it.
        # exports_sources places files at the recipe folder root, but cmake_layout(src_folder="src")
        # makes cmake look inside the "src" subdirectory.
        base = os.path.dirname(self.source_folder)
        cmakelists_src = os.path.join(base, "CMakeLists.txt")
        if os.path.isfile(cmakelists_src):
            shutil.copy2(cmakelists_src, self.source_folder)

        deps = CMakeDeps(self)
        deps.generate()

        tc = CMakeToolchain(self)

        # Collect lexer and lexlib sources for the CMakeLists.txt
        lexers_dir = os.path.join(self.source_folder, "lexers")
        lexlib_dir = os.path.join(self.source_folder, "lexlib")
        src_dir = os.path.join(self.source_folder, "src")

        lexer_sources = sorted(glob.glob(os.path.join(lexers_dir, "*.cxx")))
        lexlib_sources = sorted(glob.glob(os.path.join(lexlib_dir, "*.cxx")))
        src_sources = sorted(glob.glob(os.path.join(src_dir, "*.cxx")))

        all_sources = lexlib_sources + lexer_sources + src_sources
        tc.variables["LEXILLA_SOURCES"] = ";".join(s.replace("\\", "/") for s in all_sources)

        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "*.h", join(self.source_folder, "include"), join(self.package_folder, "include"))
        copy(self, "*.h", join(self.source_folder, "lexlib"), join(self.package_folder, "include"))
        copy(self, "*.h", join(self.source_folder, "access"), join(self.package_folder, "include"))
        copy(self, "*.cxx", join(self.source_folder, "access"), join(self.package_folder, "include"))

        copy(self, "*.lib", self.build_folder, join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.a", self.build_folder, join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.so*", self.build_folder, join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.dylib", self.build_folder, join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.dll", self.build_folder, join(self.package_folder, "bin"), keep_path=False)

    def package_info(self):
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.libdirs = ["lib"]
        self.cpp_info.libs = ["lexilla"]
        self.cpp_info.set_property("cmake_target_name", "lexilla")
