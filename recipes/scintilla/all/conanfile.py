import os
from os.path import join

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import Environment
from conan.tools.files import copy, get, replace_in_file


# Qt modules to build from Scintilla's Qt sources
scintilla_qt_modules = [
    "ScintillaEdit",
    # "ScintillaEditBase"
]


class ScintillaConanfile(ConanFile):
    name = "scintilla"
    description = "Scintilla - A free source code editing component"
    license = "HPND"
    homepage = "https://www.scintilla.org/"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "compiler", "build_type", "arch"

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def requirements(self):
        self.requires("qt/[>=6.0.0]")

    def build_requirements(self):
        self.tool_requires("qt/<host_version>")
        self.tool_requires("cpython/[>=3.10]", options={"shared": True})
        self.tool_requires("qmake2cmake/[>=1.0.8]")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def _get_python_exe(self):
        """Get the Python executable path from the cpython build dependency."""
        cpython_dep = self.dependencies.build["cpython"]
        cpython_root = cpython_dep.package_folder

        if self.settings.os == "Windows":
            python_exe = os.path.join(cpython_root, "bin", "python.exe")
        else:
            python_exe = os.path.join(cpython_root, "bin", "python3")

        if not os.path.isfile(python_exe):
            self.output.warning(f"Python executable not found at {python_exe}, falling back to system python3")
            python_exe = "python3"

        return python_exe

    def _get_cpython_env(self):
        """Create an Environment with cpython's shared library path."""
        cpython_lib = os.path.join(self.dependencies.build["cpython"].package_folder, "lib")
        env = Environment()
        env.prepend_path("LD_LIBRARY_PATH", cpython_lib)
        return env.vars(self)

    def _call_widget_gen(self):
        """Run WidgetGen.py to generate the Scintilla Qt editor API."""
        script = os.path.join(self.source_folder, "qt", "ScintillaEdit", "WidgetGen.py")
        if not os.path.isfile(script):
            raise ConanInvalidConfiguration(f"Could not locate WidgetGen.py at {script}")

        python_exe = self._get_python_exe()
        self.output.info(f"Generating Scintilla Qt editor API using {python_exe}")
        with self._get_cpython_env().apply():
            self.run(f'"{python_exe}" "{os.path.basename(script)}"', cwd=os.path.dirname(script))

    def _generate_scintilla_cmakelists(self):
        """Use qmake2cmake (from tool_requires) to generate CMakeLists.txt for each Qt module."""
        for module in scintilla_qt_modules:
            pro_file = os.path.join(self.source_folder, "qt", module, f"{module}.pro")
            module_dir = os.path.join(self.source_folder, "qt", module)
            if not os.path.isfile(pro_file):
                self.output.warning(f".pro file not found for module {module}: {pro_file}")
                continue
            self.output.info(f"Generating CMakeLists.txt for {module} using qmake2cmake")
            self.run(f'qmake2cmake --min-qt-version 6.8 "{pro_file}"', cwd=module_dir, env="conanbuild")

    def _patch_generated_cmakelists(self):
        """Replace Qt:: with Qt6:: in generated CMakeLists.txt files.

        qmake2cmake generates Qt:: namespace prefixes, but the Conan Qt package
        exposes targets under Qt6::.
        """
        for module in scintilla_qt_modules:
            cmakelists_path = os.path.join(self.source_folder, "qt", module, "CMakeLists.txt")
            if not os.path.isfile(cmakelists_path):
                self.output.warning(f"CMakeLists.txt not found for module {module}: {cmakelists_path}")
                continue
            self.output.info(f"Patching CMakeLists.txt for {module}: replacing Qt:: with Qt6::")
            replace_in_file(self, cmakelists_path, "Qt::", "Qt6::")

    def generate(self):
        self._call_widget_gen()
        self._generate_scintilla_cmakelists()
        self._patch_generated_cmakelists()

        deps = CMakeDeps(self)
        deps.generate()

        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        for module in scintilla_qt_modules:
            module_folder = os.path.join(self.source_folder, "qt", module)
            self.output.info(f"Building module {module} in {module_folder}")
            cmake = CMake(self)
            cmake.configure(build_script_folder=module_folder)
            cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        copy(self, "*.h", join(self.source_folder, "include"), join(self.package_folder, "include"))
        copy(self, "*.h", join(self.source_folder, "src"), join(self.package_folder, "include"))
        copy(self, "*.h", join(self.source_folder, "qt", "ScintillaEditBase"), join(self.package_folder, "include"))
        copy(self, "*.h", join(self.source_folder, "qt", "ScintillaEdit"), join(self.package_folder, "include"))

        copy(self, "*.lib", self.build_folder, join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.dll", self.build_folder, join(self.package_folder, "bin"), keep_path=False)
        copy(self, "*.a", self.build_folder, join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.so*", self.build_folder, join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.dylib", self.build_folder, join(self.package_folder, "lib"), keep_path=False)

    def package_info(self):
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.bindirs = ["bin"]
        self.cpp_info.libdirs = ["lib"]
        self.cpp_info.libs = scintilla_qt_modules
        self.cpp_info.set_property("cmake_target_name", "scintilla")

        self.runenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
