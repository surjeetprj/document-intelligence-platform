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
    help = 'Scrapes the top 50 Gutenberg books in batches of 10 to prevent memory crashes and rate limits.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Initializing Batched Multimodal Scraper..."))
        
        # 1. Set up Selenium and Splitters once
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage') # Highly recommended for Docker/Linux environments
        service = Service('/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)

        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

        try:
            # 2. Get the Top 50 URLs
            self.stdout.write("Fetching Top 50 list from Project Gutenberg...")
            driver.get("https://www.gutenberg.org/browse/scores/top")
            time.sleep(2)

            # Extract exactly 50 books (changed from [:2] to [:50])
            top_book_elements = driver.find_elements(By.XPATH, "//h2[@id='books-last1']/following-sibling::ol[1]/li/a")[:50]
            book_urls = [elem.get_attribute('href') for elem in top_book_elements]
            
            self.stdout.write(self.style.SUCCESS(f"Successfully found {len(book_urls)} books. Starting batch processing..."))

            # 3. Process in Batches of 10
            batch_size = 10
            for i in range(0, len(book_urls), batch_size):
                batch = book_urls[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                self.stdout.write(self.style.WARNING(f"\n--- Starting Batch {batch_num} (Books {i+1} to {i+len(batch)}) ---"))
                
                # 4. Process each book in the current batch
                for book_url in batch:
                    driver.get(book_url)
                    time.sleep(1) # Small pause for Selenium

                    try:
                        title_raw = driver.find_element(By.TAG_NAME, "h1").text
                        title, author = title_raw.split(" by ", 1) if " by " in title_raw else (title_raw, "Unknown")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Skipping {book_url} - Could not find title/author: {e}"))
                        continue

                    self.stdout.write(self.style.NOTICE(f"Processing: {title}"))

                    # Download and Extract ZIP
                    try:
                        zip_link_elem = driver.find_element(By.XPATH, "//a[contains(text(), 'HTML') and contains(@href, '.zip')]")
                        zip_url = zip_link_elem.get_attribute('href')
                        
                        response = requests.get(zip_url, timeout=15)
                        response.raise_for_status()

                        html_content = ""
                        cover_image_name = None
                        cover_image_data = None

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

                    # Parse HTML to Markdown
                    md_text = markdownify.markdownify(html_content, heading_style="ATX")
                    
                    # Remove Gutenberg Boilerplate
                    start_marker = "*** START OF THE PROJECT GUTENBERG EBOOK"
                    end_marker = "*** END OF THE PROJECT GUTENBERG EBOOK"
                    if start_marker in md_text:
                        md_text = md_text.split(start_marker)[-1]
                    if end_marker in md_text:
                        md_text = md_text.split(end_marker)[0]
                    
                    # Save to Relational Database
                    book, created = Book.objects.update_or_create(
                        book_url=book_url,
                        defaults={'title': title.strip(), 'author': author.strip(), 'description': "", 'html_content': html_content}
                    )

                    if cover_image_data and cover_image_name:
                        book.cover_image.save(cover_image_name, ContentFile(cover_image_data), save=True)

                    self.stdout.write(self.style.SUCCESS(f"  > Saved to MySQL with Cover Image!"))

                    # Chunking and Embedding
                    md_header_splits = markdown_splitter.split_text(md_text[:50000]) # Processing first 50k chars for speed
                    final_chunks = text_splitter.split_documents(md_header_splits)

                    for chunk in final_chunks:
                        chunk.metadata["book_id"] = book.id
                        chunk.metadata["title"] = book.title
                        chunk.metadata["author"] = book.author

                    vector_store.add_documents(documents=final_chunks)
                    self.stdout.write(self.style.SUCCESS(f"  > Stored {len(final_chunks)} chunks in ChromaDB!"))

                # 5. The Batch Cooldown
                if i + batch_size < len(book_urls):
                    self.stdout.write(self.style.WARNING(f"Batch {batch_num} complete. Resting for 10 seconds to clear memory..."))
                    time.sleep(10)

        finally:
            driver.quit()
            self.stdout.write(self.style.SUCCESS("\n🎉 Bulk Multimodal Ingestion Complete!"))