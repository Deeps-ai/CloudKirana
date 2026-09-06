import { useState, useEffect } from 'react';
import ScannerModal from './ScannerModal.jsx';
import apiClient from '../api/client';

export default function RetailerDashboard({ onLogout, onOpenInvoices }) {
  const [scannerOpen, setScannerOpen] = useState(false);
  const [profile, setProfile] = useState({ storeName: 'Loading...', totalStock: 0 });
  const [inventory, setInventory] = useState([]);
  const [ondcSync, setOndcSync] = useState(true);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fallback or mock URLs for now
        const profileRes = await apiClient.get('/api/retailer/profile').catch(() => ({
          data: { storeName: 'Sharma Provision (API)', totalStock: 1204, ondcSync: true }
        }));
        setProfile(profileRes.data);
        setOndcSync(profileRes.data.ondcSync);
        
        const inventoryRes = await apiClient.get('/api/retailer/inventory').catch(() => ({
          data: [
            { id: 1, name: 'Aashirvaad Atta 5kg', price: 250, qty: 45, verified: true }
          ]
        }));
        setInventory(inventoryRes.data);
      } catch (error) {
        console.error('Failed to fetch dashboard data', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleOndcSyncToggle = async (e) => {
    const newValue = e.target.checked;
    setOndcSync(newValue);
    try {
      await apiClient.post('/api/retailer/ondc-sync', { sync: newValue });
    } catch (error) {
      console.error('Failed to update ONDC sync preference', error);
      // Revert on failure if it's a real API call
      // setOndcSync(!newValue); 
    }
  };

  return (
    <div className="fade-in flex flex-col h-full relative bg-stone-50">
      <div className="bg-teal-900 text-stone-50 p-5 pt-12 pb-6 rounded-b-2xl shadow-md z-20">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-sm text-teal-100">Welcome back,</h1>
            <h2 className="text-base font-bold tracking-wide">{profile.storeName}</h2>
          </div>
          <button
            onClick={onLogout}
            className="text-xs bg-teal-800 px-3 py-1 rounded-full hover:bg-red-500 transition"
          >
            <i className="fas fa-power-off"></i>
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pb-24 px-5 pt-4 space-y-4">
        <div className="flex gap-4">
          <div className="bg-white flex-1 p-4 rounded-2xl shadow-sm border border-gray-100">
            <div className="text-xs font-bold text-gray-400">TOTAL STOCK</div>
            <div className="text-2xl font-black text-teal-900">{profile.totalStock}</div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-teal-900 to-teal-700 p-4 rounded-2xl shadow-md text-white mt-4 flex items-center justify-between">
          <div>
            <h4 className="font-bold text-sm flex items-center">
              <i className="fas fa-globe-asia mr-2 text-yellow-400"></i> ONDC Network Sync
            </h4>
            <p className="text-[10px] text-teal-200 mt-1">Publish catalog to national buyers</p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input 
              type="checkbox" 
              checked={ondcSync} 
              onChange={handleOndcSyncToggle}
              className="sr-only peer" 
            />
            <div className="w-11 h-6 bg-teal-950 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-yellow-400"></div>
          </label>
        </div>

        <h3 className="text-sm font-bold text-teal-900 mt-4 uppercase">Live Inventory</h3>
        
        {isLoading ? (
          <p className="text-center text-gray-500 my-4">Loading inventory...</p>
        ) : (
          inventory.map(item => (
            <div key={item.id} className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-4 mt-2">
              <i className="fas fa-box text-3xl text-gray-300"></i>
              <div className="flex-1">
                <h4 className="font-bold text-gray-900 text-sm">{item.name}</h4>
                <div className="text-xs text-gray-500 mb-1">₹{item.price} • Qty: {item.qty}</div>
                {item.verified && (
                  <div className="text-[10px] font-bold text-green-600 bg-green-50 px-2 py-1 rounded w-max mt-1">
                    <i className="fas fa-shield-check"></i> VERIFIED
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      <button
        onClick={() => setScannerOpen(true)}
        className="absolute bottom-24 right-5 w-14 h-14 bg-yellow-400 rounded-full shadow-lg flex items-center justify-center text-teal-900 z-30 hover:scale-105 transition"
      >
        <i className="fas fa-camera text-xl"></i>
      </button>

      <div className="bg-white h-20 absolute bottom-0 w-full border-t border-gray-200 flex justify-around items-center px-2 pb-4 z-20">
        <button className="text-teal-900 flex flex-col items-center">
          <i className="fas fa-store text-xl mb-1"></i>
          <span className="text-[10px] font-bold">Store</span>
        </button>
        <button
          onClick={onOpenInvoices}
          className="text-gray-400 hover:text-teal-900 flex flex-col items-center transition"
        >
          <i className="fas fa-file-invoice text-xl mb-1"></i>
          <span className="text-[10px] font-bold">Invoices</span>
        </button>
        <div className="w-10"></div>
        <button className="text-gray-400 hover:text-teal-900 flex flex-col items-center transition">
          <i className="fas fa-shopping-basket text-xl mb-1"></i>
          <span className="text-[10px] font-bold">Orders</span>
        </button>
      </div>

      {scannerOpen && <ScannerModal onClose={() => setScannerOpen(false)} />}
    </div>
  );
}
