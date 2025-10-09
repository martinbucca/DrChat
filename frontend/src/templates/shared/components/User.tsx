import { useEffect, useRef, useState } from 'react';
import { Menu, Typography, IconButton, Avatar } from '@neo4j-ndl/react';
import { ChevronDownIconOutline } from '@neo4j-ndl/react/icons';
import { useNavigate } from 'react-router-dom';

const settings = ['Logout'];

type StoredUser = { name?: string; email?: string };

export default function User() {
  const anchorEl = useRef<HTMLButtonElement | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [user, setUser] = useState<StoredUser | null>(null);
  const [hasChecked, setHasChecked] = useState(false);
  const navigate = useNavigate();

  const handleClose = () => {
    setIsOpen(false);
  };

  const menuSelect = (value: string) => {
    if (value === 'Logout') {
      localStorage.removeItem('user');
      handleClose();
      navigate('/login', { replace: true });
      return;
    }
    handleClose();
  };

  useEffect(() => {
    try {
      const stored = localStorage.getItem('user');
      if (stored) {
        setUser(JSON.parse(stored));
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Unable to parse stored user data', error);
      setUser(null);
      localStorage.removeItem('user');
    } finally {
      setHasChecked(true);
    }
  }, []);

  useEffect(() => {
    if (hasChecked && !user) {
      navigate('/login', { replace: true });
    }
  }, [hasChecked, navigate, user]);

  if (!user) {
    return null;
  }

  return (
    <div className='hidden md:flex md:p-1.5 md:gap-2 md:h-12 md:items-center md:border md:border-[rgb(var(--theme-palette-neutral-border-strong))] md:rounded-xl'>
      <Avatar
        className='md:flex hidden'
        name={(user.name || user.email || 'U')[0]}
        size='large'
        type='letters'
        shape='square'
      />
      <div className='flex flex-col'>
        <Typography variant='body-medium' className='p-0.5'>
          {user.name || user.email || 'User'}
        </Typography>

        <Typography variant='body-small' className='p-0.5'>
          {user.email || ''}
        </Typography>
        <Menu className='mt-11 ml-12' isOpen={isOpen} anchorRef={anchorEl} onClose={handleClose}>
          <Menu.Items>
            {settings.map((setting) => (
              <Menu.Item key={setting} onClick={() => menuSelect(setting)} title={setting} />
            ))}
          </Menu.Items>
        </Menu>
      </div>
      <IconButton ariaLabel='settings' isClean onClick={() => setIsOpen((prev) => !prev)} ref={anchorEl}>
        {isOpen ? (
          <ChevronDownIconOutline />
        ) : (
          <svg width='24' height='24' fill='none' viewBox='0 0 24 24'>
            <path d='M15 6l-6 6 6 6' stroke='currentColor' strokeWidth='2' strokeLinecap='round' strokeLinejoin='round' />
          </svg>
        )}
      </IconButton>
    </div>
  );
}
