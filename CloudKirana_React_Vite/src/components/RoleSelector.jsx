export default function RoleSelector({ onSelectRole, onSelectWholesaler, onSelectAuthority }) {
  return (
    <div className="fade-in flex flex-col h-full bg-teal-900 p-8 justify-center items-center text-center z-50">
      <h1 className="text-3xl font-black text-stone-50 mb-2">☁️ CloudKirana</h1>
      <p className="text-teal-200 mb-10 text-sm">Select a role to start the demo flow</p>

      <div className="space-y-4 w-full">
        <button
          onClick={() => onSelectRole('retailer')}
          className="w-full bg-stone-50 text-teal-900 font-bold py-4 rounded-xl shadow-lg hover:bg-yellow-400 transition flex items-center justify-center gap-3"
        >
          <i className="fas fa-store text-xl"></i> Kirana Retailer
        </button>
        <button
          onClick={() => onSelectRole('consumer')}
          className="w-full bg-stone-50 text-teal-900 font-bold py-4 rounded-xl shadow-lg hover:bg-yellow-400 transition flex items-center justify-center gap-3"
        >
          <i className="fas fa-shopping-basket text-xl"></i> Consumer
        </button>
        <button
          onClick={onSelectWholesaler}
          className="w-full bg-stone-50 text-teal-900 font-bold py-4 rounded-xl shadow-lg hover:bg-yellow-400 transition flex items-center justify-center gap-3"
        >
          <i className="fas fa-truck-loading text-xl"></i> Wholesaler
        </button>
        <button
          onClick={onSelectAuthority}
          className="w-full bg-yellow-400 text-teal-900 font-bold py-4 rounded-xl shadow-lg hover:bg-yellow-500 transition flex items-center justify-center gap-3 mt-4"
        >
          <i className="fas fa-shield-alt text-xl"></i> Authority (Desktop)
        </button>
      </div>
    </div>
  );
}
