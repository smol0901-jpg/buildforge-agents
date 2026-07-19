from agents.builders.python_builder import PythonBuilder
from agents.builders.electron_builder import ElectronBuilder
from agents.builders.csharp_builder import CsharpBuilder
from agents.builders.cpp_builder import CppBuilder
from agents.builders.html_builder import HtmlBuilder
from core.types import ProjectKind
BUILDERS = {
    ProjectKind.PYTHON: PythonBuilder, ProjectKind.ELECTRON: ElectronBuilder,
    ProjectKind.CSHARP: CsharpBuilder, ProjectKind.CPP: CppBuilder, ProjectKind.HTML: HtmlBuilder,
}
