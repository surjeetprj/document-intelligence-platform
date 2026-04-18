"""
URL routing for the Document Intelligence API.
Separates standard metadata endpoints from heavy AI/RAG processing endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Standard Metadata Operations
    path('books/', views.BookListCreateView.as_view(), name='book-list-create'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    
    # AI & Retrieval-Augmented Generation Operations
    path('books/<int:pk>/recommend/', views.BookRecommendationView.as_view(), name='book-recommend'),
    path('rag/query/', views.BookRAGQueryView.as_view(), name='rag-query'),
]