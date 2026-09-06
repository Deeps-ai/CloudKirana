import { useState } from 'react';
import RoleSelector from './components/RoleSelector.jsx';
import AuthPhone from './components/AuthPhone.jsx';
import AuthOtp from './components/AuthOtp.jsx';
import RetailerDashboard from './components/RetailerDashboard.jsx';
import InvoiceScanner from './components/InvoiceScanner.jsx';
import ConsumerStorefront from './components/ConsumerStorefront.jsx';
import Cart from './components/Cart.jsx';
import OrderTracking from './components/OrderTracking.jsx';
import AuthorityDashboard from './components/AuthorityDashboard.jsx';
import WholesalerPlaceholder from './components/WholesalerPlaceholder.jsx';

export default function App() {
  const [view, setView] = useState('role-selector');
  const [isDesktop, setIsDesktop] = useState(false);
  const [targetDashboard, setTargetDashboard] = useState('');
  const [mobileNumber, setMobileNumber] = useState('');
  const [cart, setCart] = useState([]);

  // Equivalent of the original navigateTo(viewId, isDesktop) router function
  const navigateTo = (viewId, desktop = false) => {
    setView(viewId);
    setIsDesktop(desktop);
  };

  // Equivalent of startLoginFlow(role)
  const startLoginFlow = (role) => {
    setTargetDashboard(role);
    navigateTo('auth-phone');
  };

  // Equivalent of finishLogin()
  const finishLogin = () => navigateTo(targetDashboard);

  const frameSizeClasses = isDesktop
    ? 'w-[1000px] h-[700px] rounded-lg border-[2px]'
    : 'w-[375px] h-[812px] rounded-[40px] border-[12px]';

  return (
    <div className="bg-gray-300 flex items-center justify-center min-h-screen font-sans">
      <div
        className={`bg-stone-50 ${frameSizeClasses} shadow-2xl overflow-hidden relative border-gray-900 flex flex-col transition-all duration-500`}
      >
        {view === 'role-selector' && (
          <RoleSelector
            onSelectRole={startLoginFlow}
            onSelectWholesaler={() => navigateTo('wholesaler')}
            onSelectAuthority={() => navigateTo('authority', true)}
          />
        )}

        {view === 'auth-phone' && (
          <AuthPhone 
            onBack={() => navigateTo('role-selector')} 
            onNext={(num) => {
              setMobileNumber(num);
              navigateTo('auth-otp');
            }} 
          />
        )}

        {view === 'auth-otp' && (
          <AuthOtp 
            mobileNumber={mobileNumber}
            onBack={() => navigateTo('auth-phone')} 
            onVerify={finishLogin} 
          />
        )}

        {view === 'retailer' && (
          <RetailerDashboard
            onLogout={() => navigateTo('role-selector')}
            onOpenInvoices={() => navigateTo('invoice')}
          />
        )}

        {view === 'invoice' && <InvoiceScanner onBack={() => navigateTo('retailer')} />}

        {view === 'consumer' && (
          <ConsumerStorefront
            cart={cart}
            setCart={setCart}
            onLogout={() => navigateTo('role-selector')}
            onViewCart={() => navigateTo('cart')}
          />
        )}

        {view === 'cart' && (
          <Cart 
            cart={cart}
            setCart={setCart}
            onBack={() => navigateTo('consumer')} 
            onPlaceOrder={() => navigateTo('tracking')} 
          />
        )}

        {view === 'tracking' && <OrderTracking onHome={() => navigateTo('consumer')} />}

        {view === 'authority' && <AuthorityDashboard onExit={() => navigateTo('role-selector')} />}

        {view === 'wholesaler' && <WholesalerPlaceholder onBack={() => navigateTo('role-selector')} />}
      </div>
    </div>
  );
}
