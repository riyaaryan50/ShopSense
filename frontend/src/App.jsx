
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";

import { CartProvider } from "./context/CartContext";

import Home from "./pages/Home";
import Cart from "./pages/Cart";
import Wishlist from "./pages/Wishlist";
import ProductDetails from "./pages/ProductDetails";
import InteractionHistory from "./pages/InteractionHistory";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Chatbot from "./pages/Chatbot";
import Survey from "./pages/Survey";

import Footer from "./components/Footer";
import Navbar from "./components/Navbar";
import ChatWidget from "./components/chat/ChatWidget";

const NO_GLOBAL_NAVBAR = ["/", "/login", "/signup"];

function SiteHeader() {
  const { pathname } = useLocation();
  return NO_GLOBAL_NAVBAR.includes(pathname) ? null : <Navbar />;
}

function App() {
  return (
    <CartProvider>
      <BrowserRouter>
        <SiteHeader />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/wishlist" element={<Wishlist />} />
          <Route path="/product/:id" element={<ProductDetails />} />
          <Route path="/history" element={<InteractionHistory />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/chatbot" element={<Chatbot />} />
          <Route path="/survey" element={<Survey />} />
        </Routes>

        <ChatWidget />
        <Footer />
      </BrowserRouter>
    </CartProvider>
  );
}

export default App;
