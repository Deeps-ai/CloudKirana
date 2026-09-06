import { useState, useEffect } from 'react';
import apiClient from '../api/client';

export default function ConsumerStorefront({ cart, setCart, onLogout, onViewCart }) {
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await apiClient.get('/api/consumer/products').catch(() => ({
          // Fallback mock data
          data: [
            { id: 1, name: 'Tata Salt 1kg', price: 28 },
            { id: 2, name: 'Maggi 70g', price: 14 }
          ]
        }));
        setProducts(response.data);
      } catch (error) {
        console.error('Failed to fetch products', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchProducts();
  }, []);

  const addToCart = (product) => {
    setCart(prevCart => {
      const existing = prevCart.find(item => item.id === product.id);
      if (existing) {
        return prevCart.map(item => 
          item.id === product.id ? { ...item, qty: item.qty + 1 } : item
        );
      }
      return [...prevCart, { ...product, qty: 1 }];
    });
  };

  const getQtyInCart = (productId) => {
    const item = cart.find(item => item.id === productId);
    return item ? item.qty : 0;
  };

  const totalItems = cart.reduce((sum, item) => sum + item.qty, 0);
  const totalPrice = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);

  return (
    <div className="fade-in flex flex-col h-full relative bg-stone-50">
      <div className="bg-white p-5 pt-12 shadow-sm z-20 relative flex justify-between items-center">
        <div>
          <div className="text-xs text-gray-500">Delivering to</div>
          <div className="text-sm font-bold text-teal-900">
            Sector 4, Greater Noida <i className="fas fa-chevron-down text-xs ml-1"></i>
          </div>
        </div>
        <button
          onClick={onLogout}
          className="text-xs bg-gray-100 text-gray-600 px-3 py-1 rounded-full hover:bg-red-500 hover:text-white transition"
        >
          <i className="fas fa-power-off"></i>
        </button>
      </div>

      <div className="p-5 flex-1 overflow-y-auto pb-24">
        <div className="bg-teal-900 text-white p-4 rounded-2xl mb-6 shadow-md">
          <h2 className="font-bold text-lg">Sharma Provision Store</h2>
          <div className="text-xs text-teal-200 mt-1">⭐ 4.8 | 🛵 15 Mins Delivery</div>
        </div>

        <h3 className="text-sm font-bold text-gray-800 mb-3">Verified Essentials</h3>
        
        {isLoading ? (
          <p className="text-center text-gray-500 my-4">Loading products...</p>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {products.map((item) => {
              const qty = getQtyInCart(item.id);
              return (
                <div
                  key={item.id}
                  className="bg-white p-3 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center text-center"
                >
                  <i className="fas fa-box text-4xl text-gray-200 mb-2 mt-2"></i>
                  <h4 className="font-bold text-xs">{item.name}</h4>
                  <div className="text-xs text-teal-900 font-bold mb-2">₹{item.price}</div>
                  <div className="text-[8px] bg-green-50 text-green-600 px-1 rounded mb-2 font-bold">
                    ✅ VERIFIED
                  </div>
                  <button 
                    onClick={() => addToCart(item)}
                    className={`w-full text-white text-xs font-bold py-2 rounded-lg ${qty > 0 ? 'bg-green-500' : 'bg-teal-600 hover:bg-teal-700'}`}
                  >
                    {qty > 0 ? `ADDED (${qty})` : 'ADD TO CART'}
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {totalItems > 0 && (
        <button
          onClick={onViewCart}
          className="absolute bottom-6 left-5 right-5 bg-teal-900 text-white p-4 rounded-xl flex justify-between items-center shadow-lg hover:bg-teal-800 transition"
        >
          <div className="text-sm">
            {totalItems} Items | <b>₹{totalPrice}</b>
          </div>
          <div className="text-sm font-bold text-yellow-400">
            View Cart <i className="fas fa-arrow-right ml-1"></i>
          </div>
        </button>
      )}
    </div>
  );
}
