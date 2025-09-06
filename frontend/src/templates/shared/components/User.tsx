import { useRef, useState } from 'react';
import { Menu, Typography, IconButton, Avatar } from '@neo4j-ndl/react';
import { ChevronDownIconOutline } from '@neo4j-ndl/react/icons';

const settings = ['Logout'];

export default function User() {
  const anchorEl = useRef<HTMLButtonElement | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const handleClose = () => {
    setIsOpen(false);
  };

  const menuSelect = (e: string) => {
    window.alert(e);
    handleClose();
  };

return (
    <div
        className='hidden 
        md:flex md:p-1.5 md:gap-2 md:h-12 md:items-center
        md:border md:border-[rgb(var(--theme-palette-neutral-border-strong))] md:rounded-xl'
    >
        <Avatar className='md:flex hidden' name='M' size='large' type='letters' shape='square' />
        <div className='flex flex-col'>
            <Typography variant='body-medium' className='p-0.5'>
                Martin Bucca
            </Typography>

            <Typography variant='body-small' className='p-0.5'>
                mbucca@fi.uba.ar
            </Typography>
            <Menu className='mt-11 ml-12' isOpen={isOpen} anchorRef={anchorEl} onClose={handleClose}>
                <Menu.Items>
                    {settings.map((setting) => (
                        <Menu.Item key={setting} onClick={() => menuSelect(setting)} title={setting} />
                    ))}
                </Menu.Items>
            </Menu>
        </div>
        <IconButton
            ariaLabel='settings'
            isClean
            onClick={() => setIsOpen((prev) => !prev)}
            ref={anchorEl}
        >
            {isOpen ? (
                <ChevronDownIconOutline />
            ) : (
                // Left arrow SVG
                <svg width="24" height="24" fill="none" viewBox="0 0 24 24">
                    <path d="M15 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
            )}
        </IconButton>
    </div>
);
}
