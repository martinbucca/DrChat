import { Typography } from '@neo4j-ndl/react';

import Component from './categories/Component';
import Templates from './categories/Templates';

export default function Content({ activeTab }: { activeTab: string }) {
  return (
    <div className='n-bg-palette-neutral-bg-default w-full p-0.75 gap-1'>
      <Typography variant='body-medium' className='flex p-5'>
        {activeTab === 'Template' ? <Templates /> : activeTab === 'Component' ? <Component /> : <></>}
      </Typography>
    </div>
  );
}