import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Star, BookOpen, ExternalLink, Image as ImageIcon, ChevronLeft, ChevronRight } from 'lucide-react';

export default function Dashboard() {
    const [books, setBooks] = useState([]);
    const [loading, setLoading] = useState(true);
    
    // Pagination State
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalBooks, setTotalBooks] = useState(0);

    useEffect(() => {
        setLoading(true);
        // Fetch the specific page number
        fetch(`http://localhost:8000/api/books/?page=${currentPage}`)
            .then(res => res.json())
            .then(data => {
                // Handle DRF's paginated response structure
                if (data.results) {
                    setBooks(data.results);
                    setTotalBooks(data.count);
                    setTotalPages(Math.ceil(data.count / 12)); // 12 is our PAGE_SIZE
                } else {
                    // Fallback just in case pagination isn't active
                    setBooks(data);
                }
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch books", err);
                setLoading(false);
            });
    }, [currentPage]); // Re-run the effect whenever currentPage changes

    // Scroll to top when changing pages
    const handlePageChange = (newPage) => {
        setCurrentPage(newPage);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    if (loading && books.length === 0) return (
        <div className="flex justify-center mt-32">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
    );

    return (
        <div>
            <div className="flex justify-between items-end mb-8">
                <h2 className="text-3xl font-extrabold text-gray-900">Book Repository</h2>
                <span className="text-sm font-medium text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                    {totalBooks} Books Total
                </span>
            </div>
            
            {/* The Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 mb-12">
                {books.map(book => (
                    <div key={book.id} className="bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 border border-gray-100 overflow-hidden flex flex-col group">
                        
                        <div className="relative h-72 w-full bg-gray-50 overflow-hidden border-b border-gray-100">
                            {book.cover_image ? (
                                <img 
                                    src={book.cover_image} 
                                    alt={`Cover of ${book.title}`} 
                                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-in-out"
                                />
                            ) : (
                                <div className="flex flex-col items-center justify-center w-full h-full text-gray-400 bg-gray-100">
                                    <ImageIcon className="w-12 h-12 mb-3 opacity-40" />
                                    <span className="text-xs font-semibold uppercase tracking-wider">No Cover</span>
                                </div>
                            )}
                        </div>
                        
                        <div className="p-6 flex-grow flex flex-col">
                            <div className="mb-3">
                                <h3 className="text-lg font-bold text-gray-900 line-clamp-1" title={book.title}>
                                    {book.title}
                                </h3>
                                <p className="text-sm text-indigo-600 font-medium">{book.author}</p>
                            </div>
                            
                            <div className="flex items-center gap-4 mb-4 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                                <span className="flex items-center"><Star className="w-4 h-4 text-yellow-400 mr-1" /> {book.rating || 'N/A'}</span>
                                <span className="flex items-center"><BookOpen className="w-4 h-4 text-blue-400 mr-1" /> {book.reviews_count || 0} Reviews</span>
                            </div>
                            
                            <p className="text-gray-600 text-sm line-clamp-3 mb-6 flex-grow">
                                {book.description || "No description available for this title."}
                            </p>
                        </div>
                        
                        <div className="bg-gray-50 px-6 py-4 flex justify-between items-center border-t border-gray-100">
                            <a href={book.book_url} target="_blank" rel="noreferrer" className="text-gray-500 hover:text-indigo-600 flex items-center text-sm font-medium transition-colors">
                                Source <ExternalLink className="w-4 h-4 ml-1" />
                            </a>
                            <Link to={`/book/${book.id}`} className="bg-indigo-600 text-white px-5 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-700 shadow-sm transition-all">
                                Insights
                            </Link>
                        </div>
                    </div>
                ))}
            </div>

            {/* --- NEW: Pagination Controls --- */}
            {totalPages > 1 && (
                <div className="flex justify-center items-center gap-4 border-t border-gray-200 pt-8 pb-12">
                    <button 
                        onClick={() => handlePageChange(currentPage - 1)}
                        disabled={currentPage === 1}
                        className="flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <ChevronLeft className="w-4 h-4 mr-1" /> Previous
                    </button>
                    
                    <span className="text-sm font-medium text-gray-600">
                        Page {currentPage} of {totalPages}
                    </span>
                    
                    <button 
                        onClick={() => handlePageChange(currentPage + 1)}
                        disabled={currentPage === totalPages}
                        className="flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        Next <ChevronRight className="w-4 h-4 ml-1" />
                    </button>
                </div>
            )}
        </div>
    );
}   