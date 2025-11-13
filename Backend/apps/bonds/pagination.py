from rest_framework.pagination import CursorPagination,PageNumberPagination


class BondCursorPagination(CursorPagination):
    page_size = 5                      
    page_size_query_param = 'page_size'   
    max_page_size = 100                   
    ordering =  ('maturity_date', 'isin_code')



class BondPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100