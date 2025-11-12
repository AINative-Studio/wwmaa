"""
Tests for Certifications API Routes

Tests all certifications API endpoints for proper functionality,
error handling, and data validation.

Endpoints Tested:
- GET /api/certifications
- GET /api/certifications/{id}
- GET /api/certifications/search/by-name
- GET /api/certifications/levels/list
"""

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# LIST CERTIFICATIONS ENDPOINT TESTS
# ============================================================================

class TestListCertifications:
    """Test GET /api/certifications endpoint"""

    def test_list_all_certifications(self, client):
        """Test retrieval of all certifications"""
        response = client.get('/api/certifications')

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert 'data' in data
        assert 'total' in data
        assert isinstance(data['data'], list)
        assert data['total'] > 0

        # Verify we have the expected certifications
        assert data['total'] == 4
        cert_names = [cert['name'] for cert in data['data']]
        assert 'Judo Instructor' in cert_names
        assert 'Karate Instructor' in cert_names
        assert 'Self-Defense Instructor' in cert_names
        assert 'Tournament Official' in cert_names

    def test_certification_data_structure(self, client):
        """Test that each certification has the correct structure"""
        response = client.get('/api/certifications')

        assert response.status_code == 200
        data = response.json()

        for cert in data['data']:
            # Required fields
            assert 'id' in cert
            assert 'name' in cert
            assert 'description' in cert

            # Verify types
            assert isinstance(cert['id'], str)
            assert isinstance(cert['name'], str)
            assert isinstance(cert['description'], str)

            # Optional fields should be present
            if 'requirements' in cert:
                assert isinstance(cert['requirements'], list)
            if 'duration' in cert:
                assert isinstance(cert['duration'], str)
            if 'level' in cert:
                assert isinstance(cert['level'], str)

    def test_filter_by_level_advanced(self, client):
        """Test filtering certifications by Advanced level"""
        response = client.get('/api/certifications?level=Advanced')

        assert response.status_code == 200
        data = response.json()

        # Should return only Advanced level certifications
        assert data['total'] == 2
        for cert in data['data']:
            assert cert['level'] == 'Advanced'

        cert_names = [cert['name'] for cert in data['data']]
        assert 'Judo Instructor' in cert_names
        assert 'Karate Instructor' in cert_names

    def test_filter_by_level_intermediate(self, client):
        """Test filtering certifications by Intermediate level"""
        response = client.get('/api/certifications?level=Intermediate')

        assert response.status_code == 200
        data = response.json()

        # Should return only Intermediate level certifications
        assert data['total'] == 2
        for cert in data['data']:
            assert cert['level'] == 'Intermediate'

        cert_names = [cert['name'] for cert in data['data']]
        assert 'Self-Defense Instructor' in cert_names
        assert 'Tournament Official' in cert_names

    def test_filter_by_level_case_insensitive(self, client):
        """Test that level filtering is case-insensitive"""
        response_lower = client.get('/api/certifications?level=advanced')
        response_upper = client.get('/api/certifications?level=ADVANCED')
        response_mixed = client.get('/api/certifications?level=Advanced')

        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        assert response_mixed.status_code == 200

        data_lower = response_lower.json()
        data_upper = response_upper.json()
        data_mixed = response_mixed.json()

        # All should return the same results
        assert data_lower['total'] == data_upper['total'] == data_mixed['total']

    def test_filter_by_nonexistent_level(self, client):
        """Test filtering by a level that doesn't exist"""
        response = client.get('/api/certifications?level=Beginner')

        assert response.status_code == 200
        data = response.json()

        # Should return empty list
        assert data['total'] == 0
        assert len(data['data']) == 0

    def test_certification_has_requirements(self, client):
        """Test that certifications include requirements"""
        response = client.get('/api/certifications')

        assert response.status_code == 200
        data = response.json()

        # Check that at least one certification has requirements
        judo_cert = next((cert for cert in data['data'] if cert['id'] == 'cert_judo_instructor'), None)
        assert judo_cert is not None
        assert 'requirements' in judo_cert
        assert isinstance(judo_cert['requirements'], list)
        assert len(judo_cert['requirements']) > 0


# ============================================================================
# GET CERTIFICATION BY ID ENDPOINT TESTS
# ============================================================================

class TestGetCertificationById:
    """Test GET /api/certifications/{id} endpoint"""

    def test_get_judo_instructor_certification(self, client):
        """Test retrieval of Judo Instructor certification by ID"""
        response = client.get('/api/certifications/cert_judo_instructor')

        assert response.status_code == 200
        data = response.json()

        assert data['id'] == 'cert_judo_instructor'
        assert data['name'] == 'Judo Instructor'
        assert data['level'] == 'Advanced'
        assert 'description' in data
        assert 'requirements' in data
        assert 'duration' in data
        assert len(data['requirements']) > 0

    def test_get_karate_instructor_certification(self, client):
        """Test retrieval of Karate Instructor certification by ID"""
        response = client.get('/api/certifications/cert_karate_instructor')

        assert response.status_code == 200
        data = response.json()

        assert data['id'] == 'cert_karate_instructor'
        assert data['name'] == 'Karate Instructor'
        assert data['level'] == 'Advanced'

    def test_get_self_defense_instructor_certification(self, client):
        """Test retrieval of Self-Defense Instructor certification by ID"""
        response = client.get('/api/certifications/cert_self_defense_instructor')

        assert response.status_code == 200
        data = response.json()

        assert data['id'] == 'cert_self_defense_instructor'
        assert data['name'] == 'Self-Defense Instructor'
        assert data['level'] == 'Intermediate'

    def test_get_tournament_official_certification(self, client):
        """Test retrieval of Tournament Official certification by ID"""
        response = client.get('/api/certifications/cert_tournament_official')

        assert response.status_code == 200
        data = response.json()

        assert data['id'] == 'cert_tournament_official'
        assert data['name'] == 'Tournament Official'
        assert data['level'] == 'Intermediate'

    def test_get_nonexistent_certification(self, client):
        """Test retrieval of certification that doesn't exist"""
        response = client.get('/api/certifications/cert_nonexistent')

        assert response.status_code == 404
        data = response.json()
        assert 'detail' in data
        assert 'not found' in data['detail'].lower()

    def test_get_certification_with_invalid_id(self, client):
        """Test retrieval with various invalid ID formats"""
        invalid_ids = [
            'invalid_id',
            '12345',
            'cert_fake',
            '',
            'null'
        ]

        for invalid_id in invalid_ids:
            if invalid_id:  # Skip empty string as it would match different endpoint
                response = client.get(f'/api/certifications/{invalid_id}')
                assert response.status_code == 404

    def test_certification_requirements_detail(self, client):
        """Test that certification requirements are detailed and informative"""
        response = client.get('/api/certifications/cert_karate_instructor')

        assert response.status_code == 200
        data = response.json()

        # Verify requirements exist and are meaningful
        assert len(data['requirements']) >= 5
        # Check for typical requirement patterns
        requirements_text = ' '.join(data['requirements']).lower()
        assert any(keyword in requirements_text for keyword in ['black belt', 'dan', 'experience', 'training'])


# ============================================================================
# SEARCH CERTIFICATIONS ENDPOINT TESTS
# ============================================================================

class TestSearchCertifications:
    """Test GET /api/certifications/search/by-name endpoint"""

    def test_search_by_name_judo(self, client):
        """Test searching for certifications by name with 'judo'"""
        response = client.get('/api/certifications/search/by-name?q=judo')

        assert response.status_code == 200
        data = response.json()

        assert 'data' in data
        assert 'total' in data
        assert 'query' in data
        assert data['query'] == 'judo'
        assert data['total'] > 0

        # Should find Judo Instructor
        cert_names = [cert['name'] for cert in data['data']]
        assert 'Judo Instructor' in cert_names

    def test_search_by_name_instructor(self, client):
        """Test searching for certifications by name with 'instructor'"""
        response = client.get('/api/certifications/search/by-name?q=instructor')

        assert response.status_code == 200
        data = response.json()

        # Should find multiple instructor certifications
        assert data['total'] == 3
        cert_names = [cert['name'] for cert in data['data']]
        assert 'Judo Instructor' in cert_names
        assert 'Karate Instructor' in cert_names
        assert 'Self-Defense Instructor' in cert_names

    def test_search_by_description_tournament(self, client):
        """Test searching by content in description"""
        response = client.get('/api/certifications/search/by-name?q=tournament')

        assert response.status_code == 200
        data = response.json()

        # Should find Tournament Official based on description
        assert data['total'] > 0
        cert_names = [cert['name'] for cert in data['data']]
        assert 'Tournament Official' in cert_names

    def test_search_case_insensitive(self, client):
        """Test that search is case-insensitive"""
        response_lower = client.get('/api/certifications/search/by-name?q=judo')
        response_upper = client.get('/api/certifications/search/by-name?q=JUDO')
        response_mixed = client.get('/api/certifications/search/by-name?q=Judo')

        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        assert response_mixed.status_code == 200

        data_lower = response_lower.json()
        data_upper = response_upper.json()
        data_mixed = response_mixed.json()

        # All should return the same results
        assert data_lower['total'] == data_upper['total'] == data_mixed['total']

    def test_search_no_results(self, client):
        """Test search with query that matches nothing"""
        response = client.get('/api/certifications/search/by-name?q=swimming')

        assert response.status_code == 200
        data = response.json()

        assert data['total'] == 0
        assert len(data['data']) == 0

    def test_search_minimum_length_validation(self, client):
        """Test search query minimum length validation"""
        # Query with only 1 character should fail validation
        response = client.get('/api/certifications/search/by-name?q=j')

        assert response.status_code == 422  # Validation error

    def test_search_missing_query_parameter(self, client):
        """Test search without query parameter"""
        response = client.get('/api/certifications/search/by-name')

        assert response.status_code == 422  # Missing required parameter


# ============================================================================
# LIST CERTIFICATION LEVELS ENDPOINT TESTS
# ============================================================================

class TestListCertificationLevels:
    """Test GET /api/certifications/levels/list endpoint"""

    def test_list_all_levels(self, client):
        """Test retrieval of all certification levels"""
        response = client.get('/api/certifications/levels/list')

        assert response.status_code == 200
        data = response.json()

        assert 'data' in data
        assert 'total' in data
        assert isinstance(data['data'], list)
        assert data['total'] > 0

    def test_level_data_structure(self, client):
        """Test that each level has correct structure"""
        response = client.get('/api/certifications/levels/list')

        assert response.status_code == 200
        data = response.json()

        for level in data['data']:
            assert 'name' in level
            assert 'count' in level
            assert isinstance(level['name'], str)
            assert isinstance(level['count'], int)
            assert level['count'] > 0

    def test_level_counts_accurate(self, client):
        """Test that level counts match actual certifications"""
        # Get all certifications
        all_certs_response = client.get('/api/certifications')
        all_certs = all_certs_response.json()

        # Get levels
        levels_response = client.get('/api/certifications/levels/list')
        levels = levels_response.json()

        # Verify counts
        for level_info in levels['data']:
            level_name = level_info['name']
            expected_count = len([c for c in all_certs['data'] if c.get('level') == level_name])
            assert level_info['count'] == expected_count

    def test_expected_levels_present(self, client):
        """Test that expected levels are present"""
        response = client.get('/api/certifications/levels/list')

        assert response.status_code == 200
        data = response.json()

        level_names = [level['name'] for level in data['data']]

        # Based on our certification data, we should have:
        assert 'Advanced' in level_names
        assert 'Intermediate' in level_names


# ============================================================================
# INTEGRATION AND EDGE CASE TESTS
# ============================================================================

class TestCertificationsIntegration:
    """Integration tests for certifications endpoints"""

    def test_list_then_get_by_id(self, client):
        """Test workflow: list certifications, then get specific one"""
        # First, list all certifications
        list_response = client.get('/api/certifications')
        assert list_response.status_code == 200
        certs = list_response.json()['data']

        # Then, get each certification by ID
        for cert in certs:
            detail_response = client.get(f'/api/certifications/{cert["id"]}')
            assert detail_response.status_code == 200
            detail_data = detail_response.json()

            # Verify data consistency
            assert detail_data['id'] == cert['id']
            assert detail_data['name'] == cert['name']

    def test_filter_then_search(self, client):
        """Test workflow: filter by level, then search within results"""
        # Get Advanced certifications
        filter_response = client.get('/api/certifications?level=Advanced')
        assert filter_response.status_code == 200
        advanced_certs = filter_response.json()['data']

        # Search for 'instructor' (should include some advanced ones)
        search_response = client.get('/api/certifications/search/by-name?q=instructor')
        assert search_response.status_code == 200
        search_results = search_response.json()['data']

        # Verify there's overlap
        advanced_ids = {cert['id'] for cert in advanced_certs}
        search_ids = {cert['id'] for cert in search_results}
        assert len(advanced_ids & search_ids) > 0

    def test_public_endpoint_no_auth_required(self, client):
        """Test that all certifications endpoints are public (no auth required)"""
        endpoints = [
            '/api/certifications',
            '/api/certifications/cert_judo_instructor',
            '/api/certifications/search/by-name?q=judo',
            '/api/certifications/levels/list'
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not return 401 (unauthorized) or 403 (forbidden)
            assert response.status_code not in [401, 403]


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestCertificationsErrorHandling:
    """Test error handling for certifications endpoints"""

    def test_malformed_level_parameter(self, client):
        """Test handling of various edge cases for level parameter"""
        # These should all return successfully (200) but with 0 results
        edge_cases = [
            '?level=',  # Empty level
            '?level=invalid_level',  # Invalid level
            '?level=123',  # Numeric level
        ]

        for params in edge_cases:
            response = client.get(f'/api/certifications{params}')
            assert response.status_code == 200
            # Empty or invalid levels should return all or filtered results
            data = response.json()
            assert 'data' in data
            assert 'total' in data

    def test_special_characters_in_search(self, client):
        """Test search with special characters"""
        special_queries = [
            'instructor&admin',
            'karate/judo',
            'self-defense',  # This should work
            'instructor (advanced)',
        ]

        for query in special_queries:
            response = client.get(f'/api/certifications/search/by-name?q={query}')
            # Should handle gracefully
            assert response.status_code in [200, 422]  # Either success or validation error

    def test_very_long_search_query(self, client):
        """Test search with very long query string"""
        long_query = 'a' * 1000
        response = client.get(f'/api/certifications/search/by-name?q={long_query}')

        # Should handle gracefully
        assert response.status_code in [200, 422]
