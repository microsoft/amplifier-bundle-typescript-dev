"""Tests for TypeScriptChecker parsing logic."""

from pathlib import Path
from unittest.mock import patch

from amplifier_bundle_typescript_dev.checker import TypeScriptChecker
from amplifier_bundle_typescript_dev.models import CheckConfig
from amplifier_bundle_typescript_dev.models import CheckResult
from amplifier_bundle_typescript_dev.models import Severity

FIXTURES = Path(__file__).parent / "fixtures"


class TestParsePrettierOutput:
    """Test prettier --check output parsing."""

    def test_parses_files_needing_format(self):
        """Prettier [warn] lines should produce FORMAT issues."""
        output = (FIXTURES / "prettier_check_output.txt").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_prettier_output(output)

        assert len(result.issues) == 2
        assert result.checks_run == ["prettier"]

    def test_first_file_is_utils(self):
        output = (FIXTURES / "prettier_check_output.txt").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_prettier_output(output)

        assert "src/utils.ts" in result.issues[0].file
        assert result.issues[0].code == "FORMAT"
        assert result.issues[0].severity == Severity.WARNING
        assert result.issues[0].source == "prettier"

    def test_second_file_is_button(self):
        output = (FIXTURES / "prettier_check_output.txt").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_prettier_output(output)

        assert "src/components/Button.tsx" in result.issues[1].file

    def test_empty_output_means_clean(self):
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_prettier_output("")

        assert result.clean
        assert result.checks_run == ["prettier"]

    def test_suggestion_mentions_fix(self):
        output = (FIXTURES / "prettier_check_output.txt").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_prettier_output(output)

        assert result.issues[0].suggestion is not None
        assert "fix" in result.issues[0].suggestion.lower()

    def test_skips_summary_line(self):
        """The 'Code style issues found' line should not create an issue."""
        output = (FIXTURES / "prettier_check_output.txt").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_prettier_output(output)

        for issue in result.issues:
            assert "Code style" not in issue.file


class TestParseEslintOutput:
    """Test eslint --format=json output parsing."""

    def test_parses_all_messages(self):
        output = (FIXTURES / "eslint_output.json").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_eslint_output(output)

        assert len(result.issues) == 3
        assert result.checks_run == ["eslint"]

    def test_warning_severity_mapping(self):
        """ESLint severity 1 should map to WARNING."""
        output = (FIXTURES / "eslint_output.json").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_eslint_output(output)

        unused_var = [i for i in result.issues if i.code == "no-unused-vars"][0]
        assert unused_var.severity == Severity.WARNING
        assert unused_var.line == 3
        assert unused_var.column == 7
        assert unused_var.source == "eslint"

    def test_error_severity_mapping(self):
        """ESLint severity 2 should map to ERROR."""
        output = (FIXTURES / "eslint_output.json").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_eslint_output(output)

        any_error = [i for i in result.issues if i.code == "@typescript-eslint/no-explicit-any"][0]
        assert any_error.severity == Severity.ERROR
        assert any_error.line == 10

    def test_fix_suggestion_detected(self):
        """Issues with fix info should have suggestion."""
        output = (FIXTURES / "eslint_output.json").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_eslint_output(output)

        unused_var = [i for i in result.issues if i.code == "no-unused-vars"][0]
        assert unused_var.suggestion is not None
        assert "fix" in unused_var.suggestion.lower()

    def test_suggestion_from_suggestions_array(self):
        """Issues with suggestions array should pick first desc."""
        output = (FIXTURES / "eslint_output.json").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_eslint_output(output)

        any_error = [i for i in result.issues if i.code == "@typescript-eslint/no-explicit-any"][0]
        assert any_error.suggestion is not None
        assert "unknown" in any_error.suggestion.lower()

    def test_file_paths_preserved(self):
        output = (FIXTURES / "eslint_output.json").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_eslint_output(output)

        files = {i.file for i in result.issues}
        assert "/home/user/project/src/app.ts" in files
        assert "/home/user/project/src/utils.ts" in files

    def test_empty_output_means_clean(self):
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_eslint_output("")

        assert result.clean

    def test_invalid_json_means_clean(self):
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_eslint_output("not json at all")

        assert result.clean

    def test_end_line_and_column_captured(self):
        output = (FIXTURES / "eslint_output.json").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_eslint_output(output)

        any_error = [i for i in result.issues if i.code == "@typescript-eslint/no-explicit-any"][0]
        assert any_error.end_line == 10
        assert any_error.end_column == 23


class TestParseTscOutput:
    """Test tsc --noEmit --pretty false output parsing."""

    def test_parses_type_errors(self):
        output = (FIXTURES / "tsc_errors.txt").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_tsc_output(output)

        assert len(result.issues) == 3
        assert result.checks_run == ["tsc"]

    def test_first_error_is_type_mismatch(self):
        output = (FIXTURES / "tsc_errors.txt").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_tsc_output(output)

        issue = result.issues[0]
        assert issue.file == "src/app.ts"
        assert issue.line == 10
        assert issue.column == 5
        assert issue.code == "TS2322"
        assert issue.severity == Severity.ERROR
        assert issue.source == "tsc"
        assert "not assignable" in issue.message

    def test_second_error_has_correct_location(self):
        output = (FIXTURES / "tsc_errors.txt").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_tsc_output(output)

        issue = result.issues[1]
        assert issue.file == "src/app.ts"
        assert issue.line == 15
        assert issue.column == 20
        assert issue.code == "TS2345"

    def test_third_error_different_file(self):
        output = (FIXTURES / "tsc_errors.txt").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_tsc_output(output)

        issue = result.issues[2]
        assert issue.file == "src/utils.ts"
        assert issue.code == "TS2304"

    def test_empty_output_means_clean(self):
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_tsc_output("")

        assert result.clean
        assert result.checks_run == ["tsc"]

    def test_all_issues_are_error_severity(self):
        output = (FIXTURES / "tsc_errors.txt").read_text()
        checker = TypeScriptChecker(CheckConfig())
        result = checker._parse_tsc_output(output)

        for issue in result.issues:
            assert issue.severity == Severity.ERROR


class TestStubDetection:
    """Test stub pattern detection in TS/JS files."""

    def test_finds_todo_comment(self):
        fixture = FIXTURES / "stub_sample.ts"
        checker = TypeScriptChecker(CheckConfig())
        issues = checker._check_file_for_stubs(fixture)

        todo_issues = [i for i in issues if "TODO comment" in i.message]
        assert len(todo_issues) == 1

    def test_finds_fixme_comment(self):
        fixture = FIXTURES / "stub_sample.ts"
        checker = TypeScriptChecker(CheckConfig())
        issues = checker._check_file_for_stubs(fixture)

        fixme = [i for i in issues if "FIXME" in i.message]
        assert len(fixme) == 1

    def test_finds_hack_comment(self):
        fixture = FIXTURES / "stub_sample.ts"
        checker = TypeScriptChecker(CheckConfig())
        issues = checker._check_file_for_stubs(fixture)

        hack = [i for i in issues if "HACK" in i.message]
        assert len(hack) == 1

    def test_finds_not_implemented_error(self):
        fixture = FIXTURES / "stub_sample.ts"
        checker = TypeScriptChecker(CheckConfig())
        issues = checker._check_file_for_stubs(fixture)

        not_impl = [i for i in issues if "Not implemented error" in i.message]
        assert len(not_impl) == 1

    def test_finds_bare_ts_ignore(self):
        fixture = FIXTURES / "stub_sample.ts"
        checker = TypeScriptChecker(CheckConfig())
        issues = checker._check_file_for_stubs(fixture)

        ts_ignore = [i for i in issues if "@ts-ignore" in i.message]
        assert len(ts_ignore) == 1

    def test_finds_bare_ts_expect_error(self):
        fixture = FIXTURES / "stub_sample.ts"
        checker = TypeScriptChecker(CheckConfig())
        issues = checker._check_file_for_stubs(fixture)

        bare_expect = [i for i in issues if "@ts-expect-error without explanation" in i.message]
        assert len(bare_expect) == 1

    def test_ts_expect_error_with_explanation_not_flagged(self):
        """@ts-expect-error with explanation text should NOT be flagged."""
        fixture = FIXTURES / "stub_sample.ts"
        checker = TypeScriptChecker(CheckConfig())
        issues = checker._check_file_for_stubs(fixture)

        # The one with " — testing legacy API compatibility" has text after it
        # The regex only matches bare @ts-expect-error at end of line
        expect_errors = [i for i in issues if "@ts-expect-error" in i.message]
        assert len(expect_errors) == 1  # Only the bare one, not the explained one

    def test_all_issues_are_stub_source(self):
        fixture = FIXTURES / "stub_sample.ts"
        checker = TypeScriptChecker(CheckConfig())
        issues = checker._check_file_for_stubs(fixture)

        for issue in issues:
            assert issue.source == "stub-check"
            assert issue.severity == Severity.WARNING
            assert issue.code == "STUB"


class TestStubExemptionInTestFiles:
    """Test that stubs in test files are exempt."""

    def test_todo_in_test_file_exempt(self, tmp_path):
        test_file = tmp_path / "src" / "app.test.ts"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("// TODO: add more assertions\nconst x = 1;\n")

        checker = TypeScriptChecker(CheckConfig())
        issues = checker._check_file_for_stubs(test_file)

        assert len(issues) == 0, "TODO in test files should be exempt"

    def test_todo_in_spec_file_exempt(self, tmp_path):
        spec_file = tmp_path / "src" / "app.spec.tsx"
        spec_file.parent.mkdir(parents=True)
        spec_file.write_text("// TODO: fix flaky test\nconst y = 2;\n")

        checker = TypeScriptChecker(CheckConfig())
        issues = checker._check_file_for_stubs(spec_file)

        assert len(issues) == 0, "TODO in spec files should be exempt"

    def test_fixme_in_tests_dir_exempt(self, tmp_path):
        test_file = tmp_path / "__tests__" / "utils.test.ts"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("// FIXME: needs better assertion\n")

        checker = TypeScriptChecker(CheckConfig())
        issues = checker._check_file_for_stubs(test_file)

        assert len(issues) == 0, "FIXME in __tests__ directory should be exempt"


class TestCheckResultModel:
    """Test CheckResult computed properties and formatters."""

    def test_empty_result_is_clean(self):
        result = CheckResult()
        assert result.clean
        assert result.success
        assert result.exit_code == 0

    def test_warning_only_result(self):
        from amplifier_bundle_typescript_dev.models import Issue

        result = CheckResult(
            issues=[
                Issue(
                    file="test.ts",
                    line=1,
                    column=1,
                    code="FORMAT",
                    message="needs format",
                    severity=Severity.WARNING,
                    source="prettier",
                )
            ],
            files_checked=1,
        )
        assert result.success  # warnings don't fail
        assert not result.clean
        assert result.exit_code == 1
        assert result.warning_count == 1
        assert result.error_count == 0

    def test_error_result(self):
        from amplifier_bundle_typescript_dev.models import Issue

        result = CheckResult(
            issues=[
                Issue(
                    file="test.ts",
                    line=1,
                    column=1,
                    code="TS2322",
                    message="type error",
                    severity=Severity.ERROR,
                    source="tsc",
                )
            ],
            files_checked=1,
        )
        assert not result.success
        assert result.exit_code == 2
        assert result.error_count == 1

    def test_summary_when_clean(self):
        result = CheckResult(files_checked=5)
        assert "5 files" in result.summary
        assert "passed" in result.summary.lower()

    def test_summary_with_issues(self):
        from amplifier_bundle_typescript_dev.models import Issue

        result = CheckResult(
            issues=[
                Issue(
                    file="a.ts",
                    line=1,
                    column=1,
                    code="E",
                    message="err",
                    severity=Severity.ERROR,
                    source="tsc",
                ),
                Issue(
                    file="b.ts",
                    line=1,
                    column=1,
                    code="W",
                    message="warn",
                    severity=Severity.WARNING,
                    source="eslint",
                ),
            ],
            files_checked=3,
        )
        assert "1 error" in result.summary
        assert "1 warning" in result.summary
        assert "3 files" in result.summary

    def test_merge_combines_issues(self):
        from amplifier_bundle_typescript_dev.models import Issue

        r1 = CheckResult(
            issues=[
                Issue(
                    file="a.ts",
                    line=1,
                    column=1,
                    code="X",
                    message="x",
                    severity=Severity.ERROR,
                    source="tsc",
                )
            ],
            files_checked=2,
            checks_run=["tsc"],
        )
        r2 = CheckResult(
            issues=[
                Issue(
                    file="b.ts",
                    line=1,
                    column=1,
                    code="Y",
                    message="y",
                    severity=Severity.WARNING,
                    source="eslint",
                )
            ],
            files_checked=3,
            checks_run=["eslint"],
        )

        merged = r1.merge(r2)
        assert len(merged.issues) == 2
        assert merged.files_checked == 3  # max
        assert set(merged.checks_run) == {"tsc", "eslint"}

    def test_to_tool_output_structure(self):
        result = CheckResult(files_checked=1, checks_run=["tsc"])
        output = result.to_tool_output()

        assert "success" in output
        assert "clean" in output
        assert "summary" in output
        assert "issues" in output
        assert "error_count" in output
        assert "warning_count" in output

    def test_to_hook_output_empty_when_clean(self):
        result = CheckResult()
        assert result.to_hook_output() == {}


class TestRunPrettierStderr:
    """Test that _run_prettier reads [warn] output from stderr (Prettier v3)."""

    def test_prettier_v3_warns_on_stderr(self):
        """Prettier v3 writes [warn] lines to stderr, not stdout.

        The checker must parse stderr to find formatting issues.
        """
        prettier_stderr = (
            "Checking formatting...\n"
            "[warn] src/utils.ts\n"
            "[warn] src/components/Button.tsx\n"
            "[warn] Code style issues found in 2 files. Run Prettier to fix.\n"
        )
        mock_result = type(
            "CompletedProcess",
            (),
            {
                "stdout": "",
                "stderr": prettier_stderr,
                "returncode": 1,
            },
        )()

        checker = TypeScriptChecker(CheckConfig())
        with patch("amplifier_bundle_typescript_dev.checker.subprocess.run", return_value=mock_result):
            result = checker._run_prettier(["src/"])

        assert len(result.issues) == 2, f"Expected 2 formatting issues from stderr, got {len(result.issues)}"
        assert result.issues[0].file == "src/utils.ts"
        assert result.issues[1].file == "src/components/Button.tsx"
        assert result.issues[0].code == "FORMAT"
        assert result.issues[0].severity == Severity.WARNING
