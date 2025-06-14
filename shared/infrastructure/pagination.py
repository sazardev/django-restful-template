"""
Shared Pagination Classes.
Clases de paginación personalizadas para la API.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class StandardResultsSetPagination(PageNumberPagination):
    """
    Paginación estándar para la API.
    Incluye metadatos adicionales en la respuesta.
    """
    
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """Respuesta paginada personalizada."""
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.get_page_size(self.request)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class CustomPageNumberPagination(PageNumberPagination):
    """
    Paginación personalizada con información extendida.
    """
    
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 200
    
    def get_paginated_response(self, data):
        """Respuesta con metadatos extendidos."""
        total_pages = self.page.paginator.num_pages
        current_page = self.page.number
        
        return Response({
            'pagination': {
                'count': self.page.paginator.count,
                'total_pages': total_pages,
                'current_page': current_page,
                'page_size': self.get_page_size(self.request),
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
                'next_page': current_page + 1 if self.page.has_next() else None,
                'previous_page': current_page - 1 if self.page.has_previous() else None,
                'start_index': self.page.start_index(),
                'end_index': self.page.end_index(),
            },
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'first': self.get_first_link(),
                'last': self.get_last_link(),
            },
            'results': data
        })
    
    def get_first_link(self):
        """Obtener enlace a la primera página."""
        if not self.page.has_previous():
            return None
        
        url = self.request.build_absolute_uri()
        return self.replace_query_param(url, self.page_query_param, 1)
    
    def get_last_link(self):
        """Obtener enlace a la última página."""
        if not self.page.has_next():
            return None
        
        url = self.request.build_absolute_uri()
        return self.replace_query_param(
            url, 
            self.page_query_param, 
            self.page.paginator.num_pages
        )


class LargeResultsSetPagination(PageNumberPagination):
    """
    Paginación para conjuntos de datos grandes.
    """
    
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500
    
    def get_paginated_response(self, data):
        """Respuesta optimizada para grandes conjuntos."""
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class SmallResultsSetPagination(PageNumberPagination):
    """
    Paginación para conjuntos de datos pequeños.
    """
    
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

# Alias for compatibility
StandardPagination = StandardResultsSetPagination
