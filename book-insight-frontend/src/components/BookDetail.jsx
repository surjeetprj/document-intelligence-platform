import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import RagChat from './RagChat';
import { ArrowLeft, Tag, Heart, Sparkles } from 'lucide-react';

export default function BookDetail() {
    const { id } = useParams();
    const [book, setBook] = useState(null);
    const [recommendation, setRecommendation] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch Book Details & AI Insights
        fetch(`http://localhost:8000/api/books/${id}/`)
            .then(res => res.json())
            .then(data => {
                setBook(data);
                // Fetch Recommendations concurrently
                return fetch(`http://localhost:8000/api/books/${id}/recommend/`);
            })
            .then(res => res.json())
            .then(data => {
                setRecommendation(data.recommendation);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error fetching details:", err);
                setLoading(false);
            });
    }, [id]);

    if (loading) return <div className="flex justify-center mt-20"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div></div>;
    if (!book) return <div className="text-center mt-20 text-xl text-gray-600">Book not found.</div>;

    const insights = book.insights || {};

    return (
        <div className="max-w-5xl mx-auto pb-12">
            <Link to="/" className="inline-flex items-center text-indigo-600 hover:text-indigo-800 mb-6 font-medium">
                <ArrowLeft className="w-4 h-4 mr-2" /> Back to Dashboard
            </Link>

            {/* Book Header & Metadata */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 mb-8">
                <h1 className="text-4xl font-extrabold text-gray-900 mb-2">{book.title}</h1>
                <p className="text-xl text-gray-600 mb-6">By {book.author}</p>
                
                <div className="flex flex-wrap gap-4 mb-8">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-50 text-blue-700">
                        <Tag className="w-4 h-4 mr-2" /> {insights.genre || 'Unknown Genre'}
                    </span>
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-rose-50 text-rose-700">
                        <Heart className="w-4 h-4 mr-2" /> {insights.sentiment || 'Unknown Tone'}
                    </span>
                </div>

                {/* AI Summary */}
                <div className="border-l-4 border-indigo-500 pl-6 mb-8">
                    <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center">
                        <Sparkles className="w-5 h-5 text-indigo-500 mr-2" /> AI Summary
                    </h3>
                    <div className="prose prose-indigo max-w-none text-gray-700">
                        {/* Format the string to fix escaped newlines before rendering */}
                        <ReactMarkdown>
                            {insights.summary 
                                ? insights.summary.replace(/\\n/g, '\n') 
                                : 'No summary generated yet.'}
                        </ReactMarkdown>
                    </div>
                </div>
``
                {/* AI Recommendation */}
                <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-6">
                    <h3 className="text-sm font-bold text-indigo-900 uppercase tracking-wider mb-2">Recommended Reading</h3>
                    <p className="text-indigo-800">{recommendation || 'Analyzing recommendations...'}</p>
                </div>
            </div>

            {/* Q&A Interface */}
            <RagChat bookId={book.id} bookTitle={book.title} />
        </div>
    );
}