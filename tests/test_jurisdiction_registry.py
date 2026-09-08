"""Tests for JurisdictionSourceRegistry contract, data, and validation rules."""

from datetime import date
import pytest
from pydantic import ValidationError

from nora_legal_research.jurisdiction_registry import (
    AcquisitionMethod,
    AcquisitionMode,
    AuthorityFamily,
    AuthorityLevel,
    AvailabilityStatus,
    CoverageStatus,
    GeographicScope,
    ImplementationStatus,
    JurisdictionSourceRegistry,
    LegalDomain,
    OfficialStatus,
    SourceDefinition,
    UpdateCadence,
    CurrentnessCapability,
)
from nora_legal_research.jurisdiction_data import (
    WISCONSIN_SOURCES,
    MINNESOTA_SOURCES,
    FEDERAL_OVERLAY_SOURCES,
    build_canonical_registry,
)


def test_canonical_registry_builds_and_validates():
    registry = build_canonical_registry()
    assert len(registry.sources) >= 25
    assert len(WISCONSIN_SOURCES) >= 8
    assert len(MINNESOTA_SOURCES) >= 8
    assert len(FEDERAL_OVERLAY_SOURCES) >= 9

    # Confirm unique IDs
    ids = [s.source_id for s in registry.sources]
    assert len(ids) == len(set(ids))

    # Confirm WI sources filtered correctly
    wi_sources = registry.filter_by_jurisdiction("US-WI")
    assert len(wi_sources) == len(WISCONSIN_SOURCES)

    # Confirm MN sources filtered correctly
    mn_sources = registry.filter_by_jurisdiction("US-MN")
    assert len(mn_sources) == len(MINNESOTA_SOURCES)


def test_no_unearned_deep_coverage():
    """Verify invariant: No state source has DEEP_COVERAGE without evaluation certification."""
    registry = build_canonical_registry()
    for source in registry.sources:
        assert source.coverage_status != CoverageStatus.DEEP_COVERAGE, (
            f"Source {source.source_id} has unearned DEEP_COVERAGE status"
        )


def test_controlling_authority_cannot_be_marked_explanatory():
    """Invariant: A constitution or statute cannot be marked EXPLANATORY or PROCESS."""
    with pytest.raises(ValidationError, match="cannot be classified as EXPLANATORY"):
        SourceDefinition(
            source_id="TEST-INVALID-STATUTE",
            jurisdiction="US-WI",
            geographic_scope=GeographicScope.STATEWIDE,
            legal_domain=LegalDomain.STATUTORY if hasattr(LegalDomain, "STATUTORY") else LegalDomain.GENERAL,
            authority_family=AuthorityFamily.STATUTE,
            source_name="Invalid Statute",
            provider_name="Test Provider",
            official_status=OfficialStatus.OFFICIAL,
            authority_level=AuthorityLevel.EXPLANATORY,  # Illegal!
            canonical_url="https://legis.test.gov",
            acquisition_method=AcquisitionMethod.WEB_FETCH,
            acquisition_mode=AcquisitionMode.HTML_DOCUMENT,
            update_cadence=UpdateCadence.DAILY,
            temporal_version_semantics="test",
            effective_date_semantics="test",
            publication_date_semantics="test",
            parser_normalizer_id="test_v1",
            citation_syntax=("Test § 1",),
            currentness_capability=CurrentnessCapability.OFFICIAL_BULLETIN,
            historical_version_capability=False,
            provenance_capability=True,
            licensing_terms_notes="test",
            availability_status=AvailabilityStatus.AVAILABLE,
            implementation_status=ImplementationStatus.IMPLEMENTED,
            coverage_status=CoverageStatus.BASIC,
            last_verified_date=date(2026, 9, 1),
            verification_evidence="test",
        )


def test_forms_cannot_be_marked_primary_controlling():
    """Invariant: Forms and guidance cannot be marked PRIMARY_CONTROLLING."""
    with pytest.raises(ValidationError, match="Forms and guidance must be classified as EXPLANATORY or PROCESS"):
        SourceDefinition(
            source_id="TEST-INVALID-FORM",
            jurisdiction="US-WI",
            geographic_scope=GeographicScope.STATEWIDE,
            legal_domain=LegalDomain.JUVENILE_CHILD_WELFARE,
            authority_family=AuthorityFamily.FORMS_GUIDANCE,
            source_name="Invalid Form",
            provider_name="Test Provider",
            official_status=OfficialStatus.OFFICIAL,
            authority_level=AuthorityLevel.PRIMARY_CONTROLLING,  # Illegal!
            canonical_url="https://forms.test.gov",
            acquisition_method=AcquisitionMethod.WEB_FETCH,
            acquisition_mode=AcquisitionMode.PDF_DOWNLOAD,
            update_cadence=UpdateCadence.ANNUAL,
            temporal_version_semantics="test",
            effective_date_semantics="test",
            publication_date_semantics="test",
            parser_normalizer_id="test_v1",
            citation_syntax=("Form § 1",),
            currentness_capability=CurrentnessCapability.OFFICIAL_BULLETIN,
            historical_version_capability=False,
            provenance_capability=True,
            licensing_terms_notes="test",
            availability_status=AvailabilityStatus.AVAILABLE,
            implementation_status=ImplementationStatus.IMPLEMENTED,
            coverage_status=CoverageStatus.BASIC,
            last_verified_date=date(2026, 9, 1),
            verification_evidence="test",
        )


def test_courtlistener_cannot_be_marked_official_or_live_currentness():
    """Invariant: CourtListener mirror is unofficial and not a live feed."""
    with pytest.raises(ValidationError, match="cannot be marked as OFFICIAL"):
        SourceDefinition(
            source_id="US-WI-COURTLISTENER-TEST",
            jurisdiction="US-WI",
            geographic_scope=GeographicScope.STATEWIDE,
            legal_domain=LegalDomain.GENERAL,
            authority_family=AuthorityFamily.JUDICIAL_OPINION,
            source_name="CourtListener WI",
            provider_name="CourtListener",
            official_status=OfficialStatus.OFFICIAL,  # Illegal!
            authority_level=AuthorityLevel.PRIMARY_CONTROLLING,
            canonical_url="https://courtlistener.com/api",
            acquisition_method=AcquisitionMethod.REST_API,
            acquisition_mode=AcquisitionMode.JSON_API,
            update_cadence=UpdateCadence.MONTHLY,
            temporal_version_semantics="test",
            effective_date_semantics="test",
            publication_date_semantics="test",
            parser_normalizer_id="test_v1",
            citation_syntax=("Wis. 2d",),
            currentness_capability=CurrentnessCapability.SNAPSHOT_ONLY,
            historical_version_capability=True,
            provenance_capability=True,
            licensing_terms_notes="test",
            availability_status=AvailabilityStatus.AVAILABLE,
            implementation_status=ImplementationStatus.IMPLEMENTED,
            coverage_status=CoverageStatus.BASIC,
            last_verified_date=date(2026, 9, 1),
            verification_evidence="test",
        )


def test_duplicate_source_ids_rejected():
    source1 = WISCONSIN_SOURCES[0]
    with pytest.raises(ValidationError, match="Duplicate source_id"):
        JurisdictionSourceRegistry(
            sources=(source1, source1)
        )
