import { useState } from 'react';

import Header from '../templates/shared/components/Header';
import Chatbot from '../templates/shared/components/Chatbot';
import { ChatSessionProvider } from '../context/ChatSessionContext';

export default function Dashboard() {
  const [activeNavItem, setActiveNavItem] = useState('Chat');

  return (
    <ChatSessionProvider>
      <div className='flex min-h-screen flex-col n-bg-palette-neutral-bg-default'>
        <Header
          title='DrChat'
          navItems={['Chat']}
          activeNavItem={activeNavItem}
          setActiveNavItem={setActiveNavItem}
          useNeo4jConnect={false}
          documentation=''
        />
        <main className='flex-1 overflow-hidden'>
          <Chatbot />
        </main>
      </div>
    </ChatSessionProvider>
  );
}
