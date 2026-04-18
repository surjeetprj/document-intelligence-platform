"""
API Serializers for the books app.
Splits list and detail views to optimize payload sizes and improve frontend load times.
"""
from rest_framework import serializers
from .models import Book, BookInsight

class BookInsightSerializer(serializers.ModelSerializer):
    """Formats the AI-generated insights for API responses."""
    class Meta:
        model = BookInsight
        fields = ['summary', 'genre', 'sentiment']


class BookListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for the dashboard grid.
    Deliberately excludes `html_content` and `insights` to keep the JSON payload 
    small and ensure fast page loads when paginating through dozens of books.
    """
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'rating', 'reviews_count', 
            'description', 'book_url', 'cover_image'
        ]


class BookDetailSerializer(serializers.ModelSerializer):
    """
    Heavy serializer for the individual book detail page.
    Includes the nested AI insights. Still excludes `html_content` as the frontend
    does not need to render the raw 50,000+ word HTML string.
    """
    insights = BookInsightSerializer(read_only=True)
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'rating', 'reviews_count', 
            'description', 'book_url', 'cover_image', 'insights'
        ]