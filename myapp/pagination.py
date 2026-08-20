from rest_framework.pagination import PageNumberPagination

class ProductPagination(PageNumberPagination):
    page_size = 100                       # Default 100 items per page
    page_size_query_param = 'page_size'   # Allows ?page_size=100
    max_page_size = 1000                  # Upper limit
    page_query_param = 'page'             # URL parameter for page number
