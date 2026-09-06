import { useState, useEffect } from 'react';
import apiClient from '../api/client';

export default function AuthorityDashboard({ onExit }) {
  const [incident, setIncident] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchIncident = async () => {
      try {
        const response = await apiClient.get('/api/authority/incidents/latest').catch(() => ({
          // Fallback mock data
          data: {
            id: '8842',
            storeName: 'Sharma Provision Store (API)',
            location: 'Sector 4, Greater Noida',
            timestamp: '10:43 PM IST, Sep 5, 2026',
            rules: [
              { id: 1, name: 'Retail Sale Price (MRP)', value: '₹45.00', status: 'Match' },
              { id: 2, name: 'Net Quantity', value: '200g', status: 'Match' },
              { id: 3, name: 'Manufacturer Details', value: 'NOT FOUND', status: 'Violation' },
              { id: 4, name: 'Country of Origin (2026 Rule)', value: 'NOT FOUND', status: 'Violation' }
            ]
          }
        }));
        setIncident(response.data);
      } catch (error) {
        console.error('Failed to fetch incident', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchIncident();
  }, []);

  const handleIssueNotice = async () => {
    if (!incident) return;
    try {
      await apiClient.post(`/api/authority/incidents/${incident.id}/notice`);
      alert('Notice issued to supplier successfully!');
    } catch (error) {
      console.error('Failed to issue notice', error);
      alert('Failed to issue notice. Please try again.');
    }
  };

  const handleRecallBatch = async () => {
    if (!incident) return;
    try {
      await apiClient.post(`/api/authority/incidents/${incident.id}/recall`);
      alert('Batch recalled successfully!');
    } catch (error) {
      console.error('Failed to recall batch', error);
      alert('Failed to recall batch. Please try again.');
    }
  };

  return (
    <div className="fade-in flex flex-col h-full relative bg-stone-50">
      <div className="bg-gray-900 text-white p-4 pt-8 flex justify-between items-center shadow-md z-10">
        <div className="flex items-center gap-4">
          <div className="bg-teal-600 px-3 py-1 rounded text-xs font-bold tracking-widest uppercase">
            SIH26034 Auditor
          </div>
          <div className="font-bold text-lg">Legal Metrology Control Room</div>
        </div>
        <button
          onClick={onExit}
          className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded font-bold transition flex items-center gap-2"
        >
          <i className="fas fa-power-off"></i> Exit
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <div className="w-64 bg-white border-r border-gray-200 p-4 space-y-2">
          <button className="w-full text-left bg-teal-50 text-teal-900 font-bold p-3 rounded-lg">
            <i className="fas fa-exclamation-triangle mr-2"></i> Flagged Scans (1)
          </button>
          <button className="w-full text-left text-gray-600 hover:bg-gray-50 font-bold p-3 rounded-lg transition">
            <i className="fas fa-chart-line mr-2"></i> Anomaly Radar
          </button>
          <button className="w-full text-left text-gray-600 hover:bg-gray-50 font-bold p-3 rounded-lg transition">
            <i className="fas fa-store mr-2"></i> Registered Stores
          </button>
        </div>

        <div className="flex-1 p-8 overflow-y-auto bg-gray-50">
          {isLoading ? (
            <div className="flex justify-center items-center h-full">
              <p className="text-gray-500 text-lg">Loading incident data...</p>
            </div>
          ) : incident ? (
            <>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-black text-gray-800">Compliance Incident #{incident.id}</h2>
                <span className="bg-red-100 text-red-700 font-bold px-3 py-1 rounded border border-red-200">
                  <i className="fas fa-shield-alt mr-1"></i> ACTION REQUIRED
                </span>
              </div>

              <div className="flex gap-6">
                <div className="w-1/3 bg-white p-4 rounded-xl shadow-sm border border-gray-200">
                  <h3 className="text-xs font-bold text-gray-400 mb-3 uppercase tracking-wider">
                    Source Evidence (Kirana Scan)
                  </h3>
                  <div className="bg-gray-900 h-64 rounded-lg mb-4 relative overflow-hidden flex items-center justify-center">
                    <i className="fas fa-image text-4xl text-gray-600"></i>
                    <div className="absolute bottom-10 right-10 w-24 h-12 border-2 border-red-500 bg-red-500/20"></div>
                  </div>
                  <div className="text-sm text-gray-600 mb-1">
                    <b>Uploaded By:</b> {incident.storeName}
                  </div>
                  <div className="text-sm text-gray-600 mb-1">
                    <b>Location:</b> {incident.location}
                  </div>
                  <div className="text-sm text-gray-600">
                    <b>Timestamp:</b> {incident.timestamp}
                  </div>
                </div>

                <div className="flex-1 bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                  <h3 className="text-xs font-bold text-gray-400 mb-4 uppercase tracking-wider">
                    AI Rule Engine Extraction
                  </h3>

                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b-2 border-gray-100 text-sm text-teal-900">
                        <th className="pb-2">LMPC Mandate</th>
                        <th className="pb-2">Extracted Value</th>
                        <th className="pb-2">Status</th>
                      </tr>
                    </thead>
                    <tbody className="text-sm">
                      {incident.rules.map(rule => (
                        <tr 
                          key={rule.id} 
                          className={rule.status === 'Violation' ? 'bg-red-50 border-l-4 border-red-500 border-b border-gray-50' : 'border-b border-gray-50'}
                        >
                          <td className={`py-3 ${rule.status === 'Violation' ? 'pl-3 font-bold text-gray-900' : 'font-bold text-gray-700'}`}>
                            {rule.name}
                          </td>
                          <td className={`py-3 ${rule.status === 'Violation' ? 'text-red-600 font-bold' : 'text-gray-600'}`}>
                            {rule.value}
                          </td>
                          <td className="py-3">
                            {rule.status === 'Match' ? (
                              <><i className="fas fa-check-circle text-green-500"></i> Match</>
                            ) : (
                              <><i className="fas fa-times-circle text-red-500"></i> Violation</>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  <div className="mt-8 flex gap-3">
                    <button 
                      onClick={handleIssueNotice}
                      className="bg-yellow-400 hover:bg-yellow-500 text-teal-900 font-bold py-3 px-6 rounded-lg transition shadow-md flex-1"
                    >
                      <i className="fas fa-paper-plane mr-2"></i> Issue Notice to Supplier
                    </button>
                    <button 
                      onClick={handleRecallBatch}
                      className="bg-gray-800 hover:bg-gray-900 text-white font-bold py-3 px-6 rounded-lg transition flex-1"
                    >
                      <i className="fas fa-ban mr-2"></i> Recall Batch
                    </button>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <p className="text-red-500 text-center">Error loading incident data.</p>
          )}
        </div>
      </div>
    </div>
  );
}
