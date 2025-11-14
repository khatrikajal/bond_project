from rest_framework.pagination import CursorPagination,PageNumberPagination,LimitOffsetPagination


class BondCursorPagination(CursorPagination):
    page_size = 5                      
    page_size_query_param = 'page_size'   
    max_page_size = 100                   
    ordering =  ('maturity_date', 'isin_code')



class BondPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    

class BondSkipTakePagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100
    limit_query_param = "take"
    offset_query_param = "skip"