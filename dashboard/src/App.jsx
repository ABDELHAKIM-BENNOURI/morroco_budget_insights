import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/layout/Header.jsx';
import Sidebar from './components/layout/Sidebar.jsx';
import Footer from './components/layout/Footer.jsx';
import Overview from './pages/Overview.jsx';
import Recettes from './pages/Recettes.jsx';
import Depenses from './pages/Depenses.jsx';
import Methodologie from './pages/Methodologie.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-[color:var(--color-bg)]">
        <Header />
        <div className="flex-1 flex">
          <Sidebar />
          <main className="flex-1 min-w-0 p-6 overflow-x-hidden">
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/recettes" element={<Recettes />} />
              <Route path="/depenses" element={<Depenses />} />
              <Route path="/methodologie" element={<Methodologie />} />
            </Routes>
          </main>
        </div>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
