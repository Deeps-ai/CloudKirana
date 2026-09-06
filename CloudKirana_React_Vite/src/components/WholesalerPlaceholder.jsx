export default function WholesalerPlaceholder({ onBack }) {
  return (
    <div className="fade-in flex flex-col h-full relative bg-stone-50 justify-center items-center p-6 text-center">
      <i className="fas fa-truck-loading text-6xl text-gray-300 mb-4"></i>
      <h2 className="text-2xl font-bold text-teal-900">Wholesaler View</h2>
      <p className="text-gray-500 text-sm mb-6">B2B Order fulfillment goes here.</p>
      <button
        onClick={onBack}
        className="bg-teal-900 text-white px-6 py-3 rounded-xl font-bold shadow-md hover:bg-teal-800 transition"
      >
        Go Back
      </button>
    </div>
  );
}
