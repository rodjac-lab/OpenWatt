from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import requests

from scripts.check_sources import SourceChecker


class TestSourceChecker:
    """Test suite for SourceChecker class."""

    def test_check_url_success_200(self):
        """Test successful URL check with 200 response."""
        checker = SourceChecker(timeout=10, max_retries=2)

        mock_response = Mock()
        mock_response.status_code = 200

        with patch.object(checker.session, "head", return_value=mock_response):
            result = checker.check_url("EDF", "https://example.com/tarifs.pdf")

        assert result["supplier"] == "EDF"
        assert result["url"] == "https://example.com/tarifs.pdf"
        assert result["status_code"] == 200
        assert result["error"] is None
        assert "timestamp" in result
        assert isinstance(result["response_time_ms"], int)
        assert result["response_time_ms"] >= 0

    def test_check_url_failure_404(self):
        """Test URL check with 404 response."""
        checker = SourceChecker(timeout=10, max_retries=2)

        mock_response = Mock()
        mock_response.status_code = 404

        with patch.object(checker.session, "head", return_value=mock_response):
            result = checker.check_url("Engie", "https://example.com/notfound.pdf")

        assert result["supplier"] == "Engie"
        assert result["status_code"] == 404
        assert result["error"] == "ERROR"

    def test_check_url_timeout_with_retries(self):
        """Test URL check that times out after max retries."""
        checker = SourceChecker(timeout=1, max_retries=2)

        with patch.object(
            checker.session,
            "head",
            side_effect=requests.exceptions.Timeout("Connection timed out"),
        ):
            result = checker.check_url("TotalEnergies", "https://slow.example.com/tarifs.pdf")

        assert result["supplier"] == "TotalEnergies"
        assert result["status_code"] is None
        assert result["response_time_ms"] is None
        assert result["error"] == "TIMEOUT"

    def test_check_url_request_exception(self):
        """Test URL check with general request exception."""
        checker = SourceChecker(timeout=10, max_retries=2)

        with patch.object(
            checker.session,
            "head",
            side_effect=requests.exceptions.ConnectionError("DNS lookup failed"),
        ):
            result = checker.check_url("MintEnergie", "https://invalid.example.com/tarifs.pdf")

        assert result["supplier"] == "MintEnergie"
        assert result["status_code"] is None
        assert result["error"].startswith("REQUEST_ERROR:")
        assert "DNS lookup failed" in result["error"]

    def test_check_url_retry_success_on_second_attempt(self):
        """Test successful URL check after initial timeout."""
        checker = SourceChecker(timeout=10, max_retries=2)

        mock_response = Mock()
        mock_response.status_code = 200

        with patch.object(
            checker.session,
            "head",
            side_effect=[requests.exceptions.Timeout("Timeout"), mock_response],
        ):
            result = checker.check_url("Engie", "https://example.com/tarifs.pdf")

        assert result["status_code"] == 200
        assert result["error"] is None

    def test_load_config_valid_yaml(self, tmp_path: Path):
        """Test loading a valid YAML config file."""
        checker = SourceChecker()

        config_content = """supplier: EDF
parser_version: edf_pdf_v1
source:
  url: https://particulier.edf.fr/tarifs.pdf
  format: pdf
"""
        config_file = tmp_path / "edf.yaml"
        config_file.write_text(config_content, encoding="utf-8")

        config = checker.load_config(config_file)

        assert config["supplier"] == "EDF"
        assert config["parser_version"] == "edf_pdf_v1"
        assert config["source"]["url"] == "https://particulier.edf.fr/tarifs.pdf"
        assert config["source"]["format"] == "pdf"

    def test_check_all_sources_multiple_suppliers(self, tmp_path: Path):
        """Test checking all sources from config directory."""
        checker = SourceChecker(timeout=10, max_retries=0)

        # Create config files
        edf_config = tmp_path / "edf.yaml"
        edf_config.write_text(
            "supplier: EDF\nsource:\n  url: https://edf.example.com/tarifs.pdf\n",
            encoding="utf-8",
        )

        engie_config = tmp_path / "engie.yaml"
        engie_config.write_text(
            "supplier: Engie\nsource:\n  url: https://engie.example.com/tarifs.pdf\n",
            encoding="utf-8",
        )

        mock_response = Mock()
        mock_response.status_code = 200

        with patch.object(checker.session, "head", return_value=mock_response):
            results = checker.check_all_sources(tmp_path)

        assert len(results) == 2
        suppliers = {r["supplier"] for r in results}
        assert suppliers == {"EDF", "Engie"}
        assert all(r["status_code"] == 200 for r in results)

    def test_check_all_sources_with_filter(self, tmp_path: Path):
        """Test checking sources with supplier filter."""
        checker = SourceChecker(timeout=10, max_retries=0)

        # Create config files
        edf_config = tmp_path / "edf.yaml"
        edf_config.write_text(
            "supplier: EDF\nsource:\n  url: https://edf.example.com/tarifs.pdf\n",
            encoding="utf-8",
        )

        engie_config = tmp_path / "engie.yaml"
        engie_config.write_text(
            "supplier: Engie\nsource:\n  url: https://engie.example.com/tarifs.pdf\n",
            encoding="utf-8",
        )

        mock_response = Mock()
        mock_response.status_code = 200

        with patch.object(checker.session, "head", return_value=mock_response):
            results = checker.check_all_sources(tmp_path, supplier_filter="edf")

        assert len(results) == 1
        assert results[0]["supplier"] == "EDF"

    def test_check_all_sources_missing_url(self, tmp_path: Path, capsys):
        """Test handling of config file without source URL."""
        checker = SourceChecker()

        # Create config without source URL
        config = tmp_path / "invalid.yaml"
        config.write_text("supplier: Invalid\nparser_version: v1\n", encoding="utf-8")

        results = checker.check_all_sources(tmp_path)

        assert len(results) == 0
        captured = capsys.readouterr()
        assert "No source URL found" in captured.err

    def test_check_all_sources_empty_directory(self, tmp_path: Path):
        """Test checking sources in empty directory."""
        checker = SourceChecker()
        results = checker.check_all_sources(tmp_path)
        assert len(results) == 0

    def test_check_url_server_error_500(self):
        """Test URL check with 500 server error."""
        checker = SourceChecker(timeout=10, max_retries=0)

        mock_response = Mock()
        mock_response.status_code = 500

        with patch.object(checker.session, "head", return_value=mock_response):
            result = checker.check_url("EDF", "https://example.com/error.pdf")

        assert result["status_code"] == 500
        assert result["error"] == "ERROR"

    def test_check_url_redirect_3xx(self):
        """Test URL check with redirect (should follow and return final status)."""
        checker = SourceChecker(timeout=10, max_retries=0)

        mock_response = Mock()
        mock_response.status_code = 200  # Final status after redirect

        with patch.object(checker.session, "head", return_value=mock_response):
            result = checker.check_url("EDF", "https://example.com/redirect.pdf")

        # allow_redirects=True in the actual implementation
        assert result["status_code"] == 200
        assert result["error"] is None
