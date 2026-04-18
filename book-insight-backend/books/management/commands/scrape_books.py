import time
import requests
import zipfile
import io
import markdownify
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from books.models import Book
from books.ai_services import vector_store
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

class Command(BaseCommand):
    help = 'Downloads Gutenberg ZIPs, extracts HTML/Images, parses to Markdown, and embeds via HuggingFace.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Initializing Multimodal Scraper...")
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        service = Service('/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)

        # 1. OPTIMAL CHUNKING: Split by Markdown headers first, then by character length
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

        try:
            target_url = "https://www.gutenberg.org/browse/scores/top"
            driver.get(target_url)
            time.sleep(2)

            top_book_elements = driver.find_elements(By.XPATH, "//h2[@id='books-last1']/following-sibling::ol[1]/li/a")[:2] # Limit to 2 for testing
            book_urls = [elem.get_attribute('href') for elem in top_book_elements]

            for book_url in book_urls:
                driver.get(book_url)
                time.sleep(1)

                try:
                    title_raw = driver.find_element(By.TAG_NAME, "h1").text
                    title, author = title_raw.split(" by ", 1) if " by " in title_raw else (title_raw, "Unknown")
                except:
                    continue

                self.stdout.write(self.style.WARNING(f"\nProcessing: {title}"))

                # 2. FIND AND DOWNLOAD THE ZIP FILE
                try:
                    zip_link_elem = driver.find_element(By.XPATH, "//a[contains(text(), 'HTML') and contains(@href, '.zip')]")
                    zip_url = zip_link_elem.get_attribute('href')
                    
                    self.stdout.write(f"Downloading ZIP from {zip_url}...")
                    response = requests.get(zip_url)
                    response.raise_for_status()

                    html_content = ""
                    cover_image_name = None
                    cover_image_data = None

                    # Extract files in-memory (highly scalable, no disk I/O bottlenecks)
                    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                        for filename in z.namelist():
                            if filename.endswith('.htm') or filename.endswith('.html'):
                                html_content = z.read(filename).decode('utf-8', errors='ignore')
                            elif 'cover' in filename.lower() and filename.endswith(('.jpg', '.png')):
                                cover_image_name = filename.split('/')[-1]
                                cover_image_data = z.read(filename)

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to process ZIP for {title}: {e}"))
                    continue

                # 3. PARSE HTML TO MARKDOWN (Deterministic & Fast)
                self.stdout.write("Parsing HTML to Markdown...")
                md_text = markdownify.markdownify(html_content, heading_style="ATX")
                # preview = md_text[:1000] + "..."
                
                # --- NEW LOGIC: Remove Gutenberg Boilerplate ---
                start_marker = "*** START OF THE PROJECT GUTENBERG EBOOK"
                end_marker = "*** END OF THE PROJECT GUTENBERG EBOOK"
                
                if start_marker in md_text:
                    md_text = md_text.split(start_marker)[-1] # Keep everything AFTER the start
                if end_marker in md_text:
                    md_text = md_text.split(end_marker)[0]    # Keep everything BEFORE the end
                
                # We leave the description completely empty as preview not available
                preview = ""
                
                # 4. SAVE TO RELATIONAL DATABASE
                book, created = Book.objects.update_or_create(
                    book_url=book_url,
                    defaults={'title': title.strip(), 'author': author.strip(), 'description': preview, 'html_content': html_content}
                )

                if cover_image_data and cover_image_name:
                    book.cover_image.save(cover_image_name, ContentFile(cover_image_data), save=True)

                self.stdout.write(self.style.SUCCESS(f"✅ Saved to MySQL with Cover Image!"))

                # 5. OPTIMAL EMBEDDING STRATEGY
                self.stdout.write("Chunking Markdown and generating HuggingFace Embeddings...")
                
                # Split by logical document structure (Headers)
                md_header_splits = markdown_splitter.split_text(md_text[:50000]) # Limiting size for processing speed
                # Further split large sections
                final_chunks = text_splitter.split_documents(md_header_splits)

                # Add crucial metadata to every chunk
                for chunk in final_chunks:
                    chunk.metadata["book_id"] = book.id
                    chunk.metadata["title"] = book.title
                    chunk.metadata["author"] = book.author

                # Push to ChromaDB
                vector_store.add_documents(documents=final_chunks)
                
                self.stdout.write(self.style.SUCCESS(f"✅ Stored {len(final_chunks)} structured Markdown chunks in ChromaDB!"))

        finally:
            driver.quit()
            self.stdout.write(self.style.SUCCESS("\nMultimodal Ingestion Complete!"))