class SearchError(Exception):
    """Base class for search-related errors"""
    pass

class InvalidQueryError(SearchError):
    """Raised when query is invalid"""
    pass

class ProcessingError(SearchError):
    """Raised when processing results fails"""
    pass

class ValidationError(SearchError):
    """Raised when results fail validation"""
    pass