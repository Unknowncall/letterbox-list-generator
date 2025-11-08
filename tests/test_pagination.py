"""Tests for utils/pagination.py"""
import pytest
from utils.pagination import paginate_data


class TestPaginateData:
    """Test suite for paginate_data function"""

    def test_basic_pagination_first_page(self):
        """Test basic pagination on first page"""
        data = list(range(1, 51))  # 50 items
        result = paginate_data(data, page=1, page_size=10)

        assert result['total_count'] == 50
        assert result['page'] == 1
        assert result['page_size'] == 10
        assert result['total_pages'] == 5
        assert result['items_count'] == 10
        assert result['has_next'] is True
        assert result['has_previous'] is False
        assert result['paginated_data'] == list(range(1, 11))

    def test_basic_pagination_middle_page(self):
        """Test basic pagination on middle page"""
        data = list(range(1, 51))
        result = paginate_data(data, page=3, page_size=10)

        assert result['page'] == 3
        assert result['has_next'] is True
        assert result['has_previous'] is True
        assert result['paginated_data'] == list(range(21, 31))

    def test_basic_pagination_last_page(self):
        """Test basic pagination on last page"""
        data = list(range(1, 51))
        result = paginate_data(data, page=5, page_size=10)

        assert result['page'] == 5
        assert result['has_next'] is False
        assert result['has_previous'] is True
        assert result['paginated_data'] == list(range(41, 51))

    def test_pagination_with_partial_last_page(self):
        """Test pagination when last page is partial"""
        data = list(range(1, 48))  # 47 items
        result = paginate_data(data, page=5, page_size=10)

        assert result['total_pages'] == 5
        assert result['items_count'] == 7
        assert result['paginated_data'] == list(range(41, 48))

    def test_pagination_beyond_last_page(self):
        """Test pagination when requesting page beyond available data"""
        data = list(range(1, 21))
        result = paginate_data(data, page=5, page_size=10)

        assert result['total_pages'] == 2
        assert result['items_count'] == 0
        assert result['paginated_data'] == []
        assert result['has_next'] is False

    def test_empty_data(self):
        """Test pagination with empty data"""
        result = paginate_data([], page=1, page_size=10)

        assert result['total_count'] == 0
        assert result['total_pages'] == 1
        assert result['items_count'] == 0
        assert result['paginated_data'] == []
        assert result['has_next'] is False
        assert result['has_previous'] is False

    def test_single_page(self):
        """Test pagination when all data fits on one page"""
        data = list(range(1, 6))
        result = paginate_data(data, page=1, page_size=10)

        assert result['total_count'] == 5
        assert result['total_pages'] == 1
        assert result['items_count'] == 5
        assert result['has_next'] is False
        assert result['has_previous'] is False

    def test_sorting_ascending(self):
        """Test sorting in ascending order"""
        data = [{'title': 'C'}, {'title': 'A'}, {'title': 'B'}]
        result = paginate_data(
            data,
            page=1,
            page_size=10,
            sort_key=lambda x: x['title'],
            reverse=False
        )

        assert result['paginated_data'][0]['title'] == 'A'
        assert result['paginated_data'][1]['title'] == 'B'
        assert result['paginated_data'][2]['title'] == 'C'

    def test_sorting_descending(self):
        """Test sorting in descending order"""
        data = [{'title': 'A'}, {'title': 'C'}, {'title': 'B'}]
        result = paginate_data(
            data,
            page=1,
            page_size=10,
            sort_key=lambda x: x['title'],
            reverse=True
        )

        assert result['paginated_data'][0]['title'] == 'C'
        assert result['paginated_data'][1]['title'] == 'B'
        assert result['paginated_data'][2]['title'] == 'A'

    def test_sorting_by_numeric_field(self):
        """Test sorting by numeric field"""
        data = [
            {'year': 1999},
            {'year': 1972},
            {'year': 2008}
        ]
        result = paginate_data(
            data,
            page=1,
            page_size=10,
            sort_key=lambda x: x['year'],
            reverse=False
        )

        assert result['paginated_data'][0]['year'] == 1972
        assert result['paginated_data'][1]['year'] == 1999
        assert result['paginated_data'][2]['year'] == 2008

    def test_limit_before_pagination(self):
        """Test applying limit before pagination"""
        data = list(range(1, 101))  # 100 items
        result = paginate_data(data, limit=25, page=1, page_size=10)

        assert result['total_count'] == 100  # Original count
        assert result['total_pages'] == 3  # Based on 25 items / 10 per page
        assert result['items_count'] == 10
        assert result['paginated_data'] == list(range(1, 11))

    def test_limit_with_last_page(self):
        """Test limit with pagination on last page"""
        data = list(range(1, 101))
        result = paginate_data(data, limit=25, page=3, page_size=10)

        assert result['total_pages'] == 3
        assert result['items_count'] == 5
        assert result['paginated_data'] == list(range(21, 26))

    def test_limit_smaller_than_page_size(self):
        """Test when limit is smaller than page size"""
        data = list(range(1, 101))
        result = paginate_data(data, limit=5, page=1, page_size=10)

        assert result['total_pages'] == 1
        assert result['items_count'] == 5
        assert result['paginated_data'] == list(range(1, 6))

    def test_sorting_with_pagination(self):
        """Test sorting combined with pagination"""
        data = [
            {'title': 'Film E', 'year': 2020},
            {'title': 'Film A', 'year': 1990},
            {'title': 'Film D', 'year': 2010},
            {'title': 'Film B', 'year': 2000},
            {'title': 'Film C', 'year': 2005}
        ]
        result = paginate_data(
            data,
            page=1,
            page_size=3,
            sort_key=lambda x: x['year'],
            reverse=False
        )

        assert result['items_count'] == 3
        assert result['paginated_data'][0]['title'] == 'Film A'
        assert result['paginated_data'][1]['title'] == 'Film B'
        assert result['paginated_data'][2]['title'] == 'Film C'

    def test_sorting_limit_and_pagination(self):
        """Test sorting, limit, and pagination all together"""
        data = [
            {'rating': 5.0, 'title': 'A'},
            {'rating': 3.0, 'title': 'B'},
            {'rating': 4.5, 'title': 'C'},
            {'rating': 4.0, 'title': 'D'},
            {'rating': 3.5, 'title': 'E'},
            {'rating': 4.8, 'title': 'F'},
        ]
        result = paginate_data(
            data,
            limit=4,  # Take top 4 after sorting
            page=1,
            page_size=2,
            sort_key=lambda x: x['rating'],
            reverse=True
        )

        assert result['total_pages'] == 2
        assert result['items_count'] == 2
        # Should get top 2 from the top 4 rated
        assert result['paginated_data'][0]['title'] == 'A'  # 5.0
        assert result['paginated_data'][1]['title'] == 'F'  # 4.8

    def test_case_insensitive_sorting(self):
        """Test case-insensitive sorting"""
        data = [
            {'title': 'apple'},
            {'title': 'Banana'},
            {'title': 'cherry'},
            {'title': 'Apple'}
        ]
        result = paginate_data(
            data,
            page=1,
            page_size=10,
            sort_key=lambda x: x['title'].lower(),
            reverse=False
        )

        assert result['paginated_data'][0]['title'].lower() == 'apple'
        assert result['paginated_data'][2]['title'].lower() == 'banana'

    def test_none_values_in_sorting(self):
        """Test sorting with None values"""
        data = [
            {'year': 2000},
            {'year': None},
            {'year': 1990},
            {'year': None}
        ]
        # Use 0 as default for None values
        result = paginate_data(
            data,
            page=1,
            page_size=10,
            sort_key=lambda x: x['year'] if x['year'] else 0,
            reverse=False
        )

        # None values (treated as 0) should come first
        assert result['paginated_data'][0]['year'] is None
        assert result['paginated_data'][1]['year'] is None
        assert result['paginated_data'][2]['year'] == 1990

    def test_complex_objects(self):
        """Test pagination with complex objects"""
        data = [
            {'film': {'title': 'A', 'year': 2000}, 'rating': 5.0},
            {'film': {'title': 'B', 'year': 1990}, 'rating': 4.0},
            {'film': {'title': 'C', 'year': 2010}, 'rating': 4.5},
        ]
        result = paginate_data(
            data,
            page=1,
            page_size=2,
            sort_key=lambda x: x['rating'],
            reverse=True
        )

        assert result['items_count'] == 2
        assert result['paginated_data'][0]['rating'] == 5.0
        assert result['paginated_data'][1]['rating'] == 4.5

    def test_large_page_size(self):
        """Test with page size larger than data"""
        data = list(range(1, 11))
        result = paginate_data(data, page=1, page_size=100)

        assert result['total_pages'] == 1
        assert result['items_count'] == 10
        assert result['has_next'] is False

    def test_page_size_one(self):
        """Test with page size of 1"""
        data = [1, 2, 3, 4, 5]
        result = paginate_data(data, page=3, page_size=1)

        assert result['total_pages'] == 5
        assert result['items_count'] == 1
        assert result['paginated_data'] == [3]
        assert result['has_next'] is True
        assert result['has_previous'] is True

    def test_no_sort_key_maintains_order(self):
        """Test that without sort_key, original order is maintained"""
        data = [5, 2, 8, 1, 9, 3]
        result = paginate_data(data, page=1, page_size=3)

        assert result['paginated_data'] == [5, 2, 8]

    def test_metadata_consistency(self):
        """Test that all metadata is consistent"""
        data = list(range(1, 100))
        result = paginate_data(data, limit=50, page=3, page_size=15)

        # Verify calculations
        expected_total_pages = (50 + 15 - 1) // 15  # Ceiling division
        assert result['total_pages'] == expected_total_pages

        start_index = (3 - 1) * 15
        end_index = min(start_index + 15, 50)
        expected_items = end_index - start_index
        assert result['items_count'] == expected_items
