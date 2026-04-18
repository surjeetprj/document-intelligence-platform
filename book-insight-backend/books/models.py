"""
Database models for the Document Intelligence Platform.
Handles storage of scraped book metadata, raw HTML content, and AI-generated insights.
"""
from django.db import models

class Book(models.Model):
    """
    Core model representing a scraped book from Project Gutenberg.
    Stores metadata, the original URL to prevent duplicate scrapes, and the raw HTML.
    """
    title = models.CharField(max_length=255, help_text="Official title of the book")
    author = models.CharField(max_length=255, help_text="Primary author(s)")
    
    # Scraped metrics
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    reviews_count = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True, help_text="Synopsis or back-cover text")
    
    # Source & Content
    book_url = models.URLField(
        max_length=255, 
        unique=True, 
        help_text="Direct URL to prevent duplicate scrapes"
    )
    html_content = models.TextField(null=True, blank=True, help_text="Raw HTML from the extracted ZIP")
    cover_image = models.ImageField(upload_to='covers/', null=True, blank=True)
    
    # Audit timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.author}"


class BookInsight(models.Model):
    """
    Stores AI-generated RAG insights for a specific book.
    Linked 1:1 with the Book model to keep the main table lightweight.
    """
    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name='insights')
    
    # Using TextField here instead of CharField to prevent database crashes 
    # in case the LLM generates slightly wordier genres or sentiments than requested.
    summary = models.TextField(null=True, blank=True)
    genre = models.TextField(null=True, blank=True)
    sentiment = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Insights for {self.book.title}"