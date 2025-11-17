"""PubMed and PubMed Central downloader."""

import logging
from pathlib import Path
from typing import Optional

import requests

from src.config import settings
from src.downloader.base import BaseDownloader
from src.models import DownloadResult, DownloadSource, DownloadStatus, Reference
from src.network.http_client import HTTPClient

logger = logging.getLogger(__name__)


class PubMedDownloader(BaseDownloader):
    """Download papers from PubMed Central."""

    def __init__(self):
        super().__init__()
        self.http_client = HTTPClient()

    def can_download(self, reference: Reference) -> bool:
        """Check if reference has PubMed info."""
        return reference.pmid is not None or (
            reference.title
            and any(
                x in (reference.journal or "").lower()
                for x in ["med", "pubmed", "clinical", "health"]
            )
        )

    def download(
        self, reference: Reference, output_path: Path
    ) -> Optional[DownloadResult]:
        """Download from PubMed Central."""
        if not settings.ENABLE_PUBMED:
            return self._create_result(
                reference,
                DownloadStatus.SKIPPED,
                error_message="PubMed disabled in settings",
            )

        try:
            # Try direct PMC download if we have PMID
            if reference.pmid:
                result = self._try_pmc_download(reference, output_path)
                if result and result.status == DownloadStatus.SUCCESS:
                    return result

            # Try searching by DOI
            if reference.doi:
                result = self._search_and_download(
                    reference, reference.doi, output_path
                )
                if result and result.status == DownloadStatus.SUCCESS:
                    return result

            # Try searching by title
            if reference.title:
                result = self._search_and_download(
                    reference, reference.title, output_path
                )
                if result and result.status == DownloadStatus.SUCCESS:
                    return result

            return self._create_result(
                reference,
                DownloadStatus.NOT_FOUND,
                error_message="Not found in PubMed Central",
            )

        except Exception as e:
            logger.error(f"Error accessing PubMed: {str(e)}")
            return self._create_result(
                reference,
                DownloadStatus.FAILED,
                error_message=f"PubMed download failed: {str(e)}",
            )

    def get_source(self) -> DownloadSource:
        """Get source type."""
        return DownloadSource.PUBMED

    def _try_pmc_download(
        self, reference: Reference, output_path: Path
    ) -> Optional[DownloadResult]:
        """Try to download from PMC using PMID."""
        try:
            pmid = reference.pmid

            # Get PMC ID from PMID
            pmc_id = self._get_pmc_id_from_pmid(pmid)

            if pmc_id:
                return self._download_from_pmc(reference, pmc_id, output_path)

            return None

        except Exception as e:
            logger.debug(f"Error in PMC download: {str(e)}")
            return None

    def _get_pmc_id_from_pmid(self, pmid: str) -> Optional[str]:
        """Get PMC ID from PubMed ID."""
        try:
            # Use NCBI E-utilities to convert PMID to PMCID
            url = (
                f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
                f"?tool=ref-downloader&email={settings.CROSSREF_EMAIL}"
                f"&ids={pmid}&format=json"
            )

            response = self.http_client.get(url)

            data = response.json()
            if "records" in data and len(data["records"]) > 0:
                record = data["records"][0]
                if "pmcid" in record:
                    # Remove "PMC" prefix if present
                    return record["pmcid"].replace("PMC", "")

            return None

        except Exception as e:
            logger.debug(f"Error getting PMC ID: {str(e)}")
            return None

    def _download_from_pmc(
        self, reference: Reference, pmc_id: str, output_path: Path
    ) -> Optional[DownloadResult]:
        """Download PDF from PMC using PMC ID."""
        try:
            # Construct PDF URL
            pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/"

            logger.info(f"Downloading from PMC: {pdf_url}")

            response = self.http_client.get(pdf_url, allow_redirects=True)

            content = response.content
            file_size = self._save_pdf(content, output_path)

            if file_size:
                return self._create_result(
                    reference,
                    DownloadStatus.SUCCESS,
                    file_path=str(output_path),
                    file_size=file_size,
                )
            else:
                return self._create_result(
                    reference,
                    DownloadStatus.FAILED,
                    error_message="Invalid PDF content",
                )

        except Exception as e:
            logger.warning(f"Error downloading from PMC: {str(e)}")
            return None

    def _search_and_download(
        self, reference: Reference, query: str, output_path: Path
    ) -> Optional[DownloadResult]:
        """Search PubMed and download if open access."""
        try:
            # Search PubMed
            search_url = (
                f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
                f"db=pubmed&term={query}&rettype=json&retmode=json"
            )

            response = self.http_client.get(search_url)

            data = response.json()
            if "esearchresult" in data and "idlist" in data["esearchresult"]:
                pmids = data["esearchresult"]["idlist"]

                # Try to download first result
                if pmids:
                    pmid = pmids[0]
                    return self._try_pmc_download(
                        Reference(raw_text="", pmid=pmid), output_path
                    )

            return None

        except Exception as e:
            logger.debug(f"Error searching PubMed: {str(e)}")
            return None
