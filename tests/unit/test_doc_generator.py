"""Unit tests for overseer/doc_generator.py"""

from __future__ import annotations

from pathlib import Path

from overseer.doc_generator import DocumentationGenerator


def _make_generator(tmp_path: Path, config=None):
    return DocumentationGenerator(tmp_path, config or {})


class TestDocumentationGeneratorInit:
    def test_creates_with_repo_path(self, tmp_path):
        gen = _make_generator(tmp_path)
        assert gen.repo_path == tmp_path

    def test_repo_info_detected(self, tmp_path):
        gen = _make_generator(tmp_path)
        assert isinstance(gen.repo_info, dict)
        assert "name" in gen.repo_info


class TestDetectRepositoryInfo:
    def test_name_is_dir_name(self, tmp_path):
        gen = _make_generator(tmp_path)
        info = gen._detect_repository_info()
        assert info["name"] == tmp_path.name

    def test_detects_python_files(self, tmp_path):
        (tmp_path / "module.py").write_text("pass")
        gen = _make_generator(tmp_path)
        info = gen._detect_repository_info()
        assert info["has_python"] is True

    def test_no_python_when_no_py_files(self, tmp_path):
        gen = _make_generator(tmp_path)
        info = gen._detect_repository_info()
        assert info["has_python"] is False

    def test_detects_javascript_files(self, tmp_path):
        (tmp_path / "app.js").write_text("const x = 1;")
        gen = _make_generator(tmp_path)
        info = gen._detect_repository_info()
        assert info["has_javascript"] is True

    def test_detects_typescript_files(self, tmp_path):
        (tmp_path / "app.ts").write_text("const x: number = 1;")
        gen = _make_generator(tmp_path)
        info = gen._detect_repository_info()
        assert info["has_javascript"] is True

    def test_detects_ci_workflows(self, tmp_path):
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "ci.yml").write_text("on: push")
        gen = _make_generator(tmp_path)
        info = gen._detect_repository_info()
        assert info["has_ci"] is True

    def test_detects_pytest_in_requirements(self, tmp_path):
        (tmp_path / "module.py").write_text("pass")
        (tmp_path / "requirements.txt").write_text("pytest==7.0.0\nrequests==2.28.0\n")
        gen = _make_generator(tmp_path)
        info = gen._detect_repository_info()
        assert info["has_tests"] is True

    def test_detects_flask_framework(self, tmp_path):
        (tmp_path / "module.py").write_text("pass")
        (tmp_path / "requirements.txt").write_text("flask==2.0.0\n")
        gen = _make_generator(tmp_path)
        info = gen._detect_repository_info()
        assert "Flask" in info["frameworks"]

    def test_detects_django_framework(self, tmp_path):
        (tmp_path / "module.py").write_text("pass")
        (tmp_path / "requirements.txt").write_text("django==4.0.0\n")
        gen = _make_generator(tmp_path)
        info = gen._detect_repository_info()
        assert "Django" in info["frameworks"]


class TestBuildReadmeContent:
    def test_readme_contains_title(self, tmp_path):
        gen = _make_generator(tmp_path)
        content = gen._build_readme_content()
        assert "# " in content
        assert tmp_path.name.replace("-", " ").title().lower() in content.lower()

    def test_readme_contains_installation_section(self, tmp_path):
        gen = _make_generator(tmp_path)
        content = gen._build_readme_content()
        assert "Installation" in content

    def test_readme_contains_contributing_section(self, tmp_path):
        gen = _make_generator(tmp_path)
        content = gen._build_readme_content()
        assert "Contributing" in content

    def test_readme_with_python_includes_pip_install(self, tmp_path):
        (tmp_path / "module.py").write_text("pass")
        gen = _make_generator(tmp_path)
        content = gen._build_readme_content()
        assert "pip install" in content


class TestBuildContributingContent:
    def test_contributing_is_string(self, tmp_path):
        gen = _make_generator(tmp_path)
        content = gen._build_contributing_content()
        assert isinstance(content, str)

    def test_contributing_has_guidelines(self, tmp_path):
        gen = _make_generator(tmp_path)
        content = gen._build_contributing_content()
        assert "Contributing" in content


class TestShouldDocument:
    def test_test_files_not_documented(self, tmp_path):
        gen = _make_generator(tmp_path)
        assert gen._should_document(tmp_path / "test_module.py") is False

    def test_init_files_not_documented(self, tmp_path):
        gen = _make_generator(tmp_path)
        assert gen._should_document(tmp_path / "__init__.py") is False

    def test_venv_files_not_documented(self, tmp_path):
        gen = _make_generator(tmp_path)
        assert gen._should_document(tmp_path / "venv" / "module.py") is False

    def test_git_files_not_documented(self, tmp_path):
        gen = _make_generator(tmp_path)
        assert gen._should_document(tmp_path / ".git" / "module.py") is False


class TestGenerate:
    def test_generate_returns_dict(self, tmp_path):
        gen = _make_generator(tmp_path)
        result = gen.generate()
        assert isinstance(result, dict)
        assert "readme" in result
        assert "contributing" in result
        assert "api_docs" in result


class TestGenerateReadme:
    def test_generates_readme_file(self, tmp_path):
        gen = _make_generator(tmp_path)
        path = gen.generate_readme()
        assert path is not None
        assert path.exists()
        assert path.suffix == ".md"

    def test_readme_content_not_empty(self, tmp_path):
        gen = _make_generator(tmp_path)
        path = gen.generate_readme()
        assert len(path.read_text()) > 0


class TestGenerateContributing:
    def test_generates_contributing_file(self, tmp_path):
        gen = _make_generator(tmp_path)
        path = gen.generate_contributing()
        assert path is not None
        assert path.exists()

    def test_contributing_content_not_empty(self, tmp_path):
        gen = _make_generator(tmp_path)
        path = gen.generate_contributing()
        assert len(path.read_text()) > 0


class TestGenerateApiDocs:
    def test_generates_docs_for_python_files(self, tmp_path):
        (tmp_path / "module.py").write_text(
            'class MyClass:\n    """A test class."""\n    def method(self):\n        pass\n'
        )
        gen = _make_generator(tmp_path)
        docs = gen.generate_api_docs()
        assert isinstance(docs, list)

    def test_no_docs_for_empty_dir(self, tmp_path):
        gen = _make_generator(tmp_path)
        docs = gen.generate_api_docs()
        assert docs == []

    def test_docs_dir_created(self, tmp_path):
        gen = _make_generator(tmp_path)
        gen.generate_api_docs()
        assert (tmp_path / "docs" / "api").exists()
