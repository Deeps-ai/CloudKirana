export default function ScannerModal({ onClose }) {
  return (
    <div className="absolute inset-0 bg-gray-900 z-40 flex flex-col justify-end">
      <button onClick={onClose} className="absolute top-12 right-5 text-white z-50 p-2">
        <i className="fas fa-times text-2xl"></i>
      </button>

      <div className="absolute inset-0 flex items-center justify-center -mt-32">
        <div className="w-56 h-56 border-2 border-yellow-400 border-dashed rounded-xl flex items-end justify-center pb-4 animate-pulse">
          <span className="bg-black text-yellow-400 text-xs px-2 py-1 rounded">
            Scanning Legal Metrology...
          </span>
        </div>
      </div>

      <div className="bg-stone-50 rounded-t-3xl p-6 relative z-50 shadow-[0_-10px_30px_rgba(0,0,0,0.5)]">
        <div className="bg-green-500 text-white text-xs font-bold px-3 py-1 rounded-full inline-block mb-3">
          COMPLIANT
        </div>
        <ul className="text-sm mb-4 space-y-2 font-medium text-gray-700">
          <li>
            <i className="fas fa-check text-green-500 mr-2"></i> MRP: ₹120.00
          </li>
          <li>
            <i className="fas fa-check text-green-500 mr-2"></i> Net Qty: 500g
          </li>
          <li>
            <i className="fas fa-check text-green-500 mr-2"></i> Mfr: ITC Limited
          </li>
        </ul>
        <button
          onClick={onClose}
          className="w-full bg-yellow-400 text-teal-900 font-bold py-4 rounded-xl shadow-md hover:bg-yellow-500 transition"
        >
          Add to Inventory
        </button>
      </div>
    </div>
  );
}
