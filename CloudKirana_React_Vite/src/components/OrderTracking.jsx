export default function OrderTracking({ onHome }) {
  return (
    <div className="fade-in flex flex-col h-full relative bg-stone-50">
      <div className="h-[35%] bg-gray-200 relative flex items-center justify-center border-b border-gray-300">
        <i className="fas fa-map-marked-alt text-6xl text-gray-400"></i>
        <button
          onClick={onHome}
          className="absolute top-12 left-5 bg-white w-10 h-10 rounded-full shadow-md flex items-center justify-center text-teal-900 hover:bg-teal-900 hover:text-white transition"
        >
          <i className="fas fa-home"></i>
        </button>
      </div>

      <div className="flex-1 bg-stone-50 rounded-t-3xl -mt-6 z-10 p-6 relative">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-black text-teal-900">Order Confirmed!</h2>
          <p className="text-gray-500 text-sm font-medium">Arriving in 12-15 minutes</p>
        </div>

        <div className="relative pl-6 border-l-2 border-green-500 space-y-6 mb-8 ml-2">
          <div className="relative">
            <div className="absolute -left-[31px] bg-green-500 w-4 h-4 rounded-full border-4 border-stone-50"></div>
            <h4 className="font-bold text-teal-900 text-sm">Order Placed</h4>
            <p className="text-xs text-gray-500">Sent to Sharma Provision Store</p>
          </div>
          <div className="relative">
            <div className="absolute -left-[31px] bg-green-500 w-4 h-4 rounded-full border-4 border-stone-50"></div>
            <h4 className="font-bold text-teal-900 text-sm">Store Verified & Packed</h4>
            <p className="text-xs text-gray-500">Items confirmed authentic</p>
          </div>
          <div className="relative opacity-50">
            <div className="absolute -left-[31px] bg-gray-300 w-4 h-4 rounded-full border-4 border-stone-50"></div>
            <h4 className="font-bold text-gray-600 text-sm">Out for Delivery</h4>
            <p className="text-xs text-gray-500">Raju is picking up your order</p>
          </div>
        </div>

        <div className="bg-white border border-gray-200 p-4 rounded-xl flex items-center gap-4 shadow-sm">
          <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
            <i className="fas fa-motorcycle text-gray-500"></i>
          </div>
          <div>
            <div className="font-bold text-sm text-gray-800">Raju Kumar</div>
            <div className="text-xs text-gray-500">Delivery Partner</div>
          </div>
          <button className="ml-auto w-10 h-10 bg-green-100 text-green-600 rounded-full flex items-center justify-center hover:bg-green-200 transition">
            <i className="fas fa-phone-alt"></i>
          </button>
        </div>
      </div>
    </div>
  );
}
