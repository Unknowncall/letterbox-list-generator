"""Pagination utilities for list endpoints"""

from typing import Any, Callable, Dict, List, Optional, TypeVar

T = TypeVar("T")


def paginate_data(
    data: List[T],
    limit: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    sort_key: Optional[Callable[[T], Any]] = None,
    reverse: bool = False,
) -> Dict[str, Any]:
    """
    Apply sorting and pagination to a list of data

    Args:
        data: List of items to paginate
        limit: Optional limit to apply before pagination
        page: Page number (1-indexed)
        page_size: Number of items per page
        sort_key: Optional function to extract comparison key from each item
        reverse: If True, sort in descending order

    Returns:
        Dictionary containing pagination metadata and paginated data
    """
    total_count = len(data)

    # Apply sorting if sort_key is provided
    if sort_key:
        data = sorted(data, key=sort_key, reverse=reverse)

    # Apply limit if specified
    if limit:
        data = data[:limit]

    # Calculate pagination
    total_for_pagination = len(data)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_data = data[start_index:end_index]

    total_pages = (total_for_pagination + page_size - 1) // page_size if total_for_pagination > 0 else 1

    return {
        "total_count": total_count,
        "paginated_data": paginated_data,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
        "items_count": len(paginated_data),
    }
