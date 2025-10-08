/* eslint-disable no-confusing-arrow */
import { useEffect, useRef, useState } from 'react';
import { Box, Typography, Flex, IconButton, LoadingSpinner, Drawer } from '@neo4j-ndl/react';
import { IoCloseOutline } from 'react-icons/io5';

import './Retrieval.css';
import DrChatLogo from '../assets/dr_chat_logo.png';

import { setDriver, runQuery } from '../utils/Driver';

import { ResetZoomIcon, FitToScreenIcon } from '@neo4j-ndl/react/icons';

import type NVL from '@neo4j-nvl/base';

import type { HitTargets, Node, Relationship } from '@neo4j-nvl/base';
import { InteractiveNvlWrapper } from '@neo4j-nvl/react';
import type { MouseEventCallbacks } from '@neo4j-nvl/react';
import ReactMarkdown from 'react-markdown';

type CypherProps = {
  uri?: string;
  username?: string;
  password?: string;
};

type ExpandedNode = {
  properties?: {
    type?: string;
    text?: string;
    name?: string;
    id?: string;
    image_base64?: string;
    text_as_html?: string;
  };
  captions?: {
    labels?: string[];
  }[];
};

function RetrievalInformation({ sources, model, entities, timeTaken, onClose }) {

  const nvl = useRef<NVL | null>(null);
  const [uri, setURI] = useState(import.meta.env.VITE_NEO4J_URI);
  const [username, setUsername] = useState(import.meta.env.VITE_NEO4J_USERNAME);
  const [password, setPassword] = useState(import.meta.env.VITE_NEO4J_PASSWORD);
  const [loading, setLoading] = useState(true);
  const [isExpanded, handleIsExpanded] = useState(false);
  const [expandedNode, setExpandedNode] = useState(null);

  const handleExpand = (nodes, hitTargets, evt) => {
      console.log('expandedNode:', nodes);
      console.log('expandedNode.properties:', nodes?.properties);

    setExpandedNode(nodes);
    handleIsExpanded(true);
  }

  useEffect(() => {
    run();
  
  }, []);

  const [nodes, setNodes] = useState<Node[]>([]);
  const [rels, setRels] = useState<Relationship[]>([]);

  const fitNodes = () => {
    nvl.current?.fit(nodes.map((n) => n.id));
  };
  const resetZoom = () => {
    nvl.current?.resetZoom();
  };

  const mouseEventCallbacks: MouseEventCallbacks = {
    onHover: (element: Node | Relationship, hitTargets: HitTargets, evt: MouseEvent) =>
      console.log('onHover', element, hitTargets, evt),
    onRelationshipRightClick: (rel: Relationship, hitTargets: HitTargets, evt: MouseEvent) =>
      console.log('onRelationshipRightClick', rel, hitTargets, evt),
    onNodeClick: (node: Node, hitTargets: HitTargets, evt: MouseEvent) =>
      handleExpand(node, hitTargets, evt),
    onNodeRightClick: (node: Node, hitTargets: HitTargets, evt: MouseEvent) =>
      console.log('onNodeRightClick', node, hitTargets, evt),
    onNodeDoubleClick: (node: Node, hitTargets: HitTargets, evt: MouseEvent) =>
      console.log('onNodeDoubleClick', node, hitTargets, evt),
    onRelationshipClick: (rel: Relationship, hitTargets: HitTargets, evt: MouseEvent) =>
      console.log('onRelationshipClick', rel, hitTargets, evt),
    onRelationshipDoubleClick: (rel: Relationship, hitTargets: HitTargets, evt: MouseEvent) =>
      console.log('onRelationshipDoubleClick', rel, hitTargets, evt),
    onCanvasClick: (evt: MouseEvent) => console.log('onCanvasClick', evt),
    onCanvasDoubleClick: (evt: MouseEvent) => console.log('onCanvasDoubleClick', evt),
    onCanvasRightClick: (evt: MouseEvent) => console.log('onCanvasRightClick', evt),
    onDrag: (nodes: Node[]) => console.log('onDrag', nodes),
    onPan: (evt: MouseEvent) => console.log('onPan', evt),
    onZoom: (zoomLevel: number) => console.log('onZoom', zoomLevel),
  };

  function run() {
    const formattedSources = sources.map((source) => `"${source}"`).join(',');
    console.log(`[${formattedSources}]`);

    const query1 = `
    MATCH (a:Chunk)-[r:PART_OF_DOCUMENT]->(b:Document)
    WHERE elementId(a) in [${formattedSources}]
    RETURN DISTINCT a,r,b
    UNION
    MATCH (a:Chunk)-[r:NEXT_CHUNK]-(b:Chunk)
    WHERE elementId(a) in [${formattedSources}] AND elementId(b) in [${formattedSources}]
    RETURN DISTINCT a,r,b
    UNION
    MATCH (a:Chunk)-[r:MENTIONS]-(b:Entity)
    WHERE elementId(a) in [${formattedSources}] AND elementId(b) in [${formattedSources}]
    RETURN DISTINCT a,r,b
    UNION
    MATCH (a:Chunk)-[r:RELATED_CONTENT]->(b:Image|Table)
    WHERE elementId(a) in [${formattedSources}]
    RETURN DISTINCT a,r,b
    LIMIT 500
    `;

    const query2 = `  
    MATCH (a:Chunk)-[r2:PART_OF_DOCUMENT]-(d:Document) WHERE elementId(a) in [${formattedSources}]
    MATCH (a)-[r]-(b)
    WHERE elementId(b) IN [${formattedSources}]
    RETURN a, r, b, r2, d LIMIT 1000

    `;

    setDriver(uri, username, password).then((isSuccessful) => {
      runQuery(query1).then((result) => {

        result.nodes.map((record: any) => {

          const label = record.labels.includes('Document')
            ? record.labels
            : record.labels.includes('Entity')
            ? record.properties.name
            : record.labels.includes('Chunk')
            ? "Text Section"
            : record.properties.type


          const color = record.labels.includes('Chunk')
            ? '#0A6190'
            : record.labels.includes('Document')
            ? '#BCF194'
            : record.labels.includes('Entity')
            ? '#B38EFF'
            : record.labels.includes('Image')
            ? '#FFC300'
            : '#FF8E6A'

          setNodes((prevNodes) => [
            ...prevNodes,
            { id: record.id.toString(), color: color, captions: [{ value: label, labels: record.labels }], properties: record.properties },
          ]);
        });

        result.rels.map((record: any) => {
          if (record.type.toString() === 'NEXT_CHUNK') {
            record.type = 'NEXT_SECTION';
          }
          setRels((prevRels) => [
            ...prevRels,
            {
              id: record.id.toString(),
              from: record.start.toString(),
              to: record.end.toString(),
              captions: [{ value: record.type.toString() }],
              width: 1.2,
              captionSize: 1.5
            },
          ]);
        });
        setLoading(false);
      });
    });
  }

  return (
    <Box
      className='n-bg-palette-neutral-bg-weak p-4'
      style={{ height: '120vh' }}
    >
      <IconButton
        className='n-size-token-7'
        ariaLabel='Close modal'
        onClick={onClose}
        style={{
          position: 'absolute',
          top: 16,   // distancia desde el top del modal
          right: 16, // distancia desde la derecha del modal
          zIndex: 2000,
        }}
      >
        <IoCloseOutline size={20} />
      </IconButton>
      <Flex flexDirection='row' className='flex flex-row p-6 items-center'>
        <img src={DrChatLogo} alt='icon' style={{ width: 95, height: 95, marginRight: 10 }} />
        <Box className='flex flex-col'>
          <Typography variant='h2'>Where This Answer Came From</Typography>
          <Typography variant='h6'>This graph shows the information the system used to build your answer.
            You can tap on each item to see more details about it.</Typography>
        </Box>
      </Flex>
      <Box className='button-container' sx={{ display: 'flex', justifyContent: 'space-between', mt: 2}}>
        <div
          style={{
            margin: 10,
            borderRadius: 25,
            border: '2px solid #2A93A0',
            height: 'calc(110vh - 163px)', 
            flexGrow: 1,
            display: 'flex',
            flexDirection: 'column',
            background: `rgb(var(--theme-palette-primary-bg-weaker));`,
            boxShadow: `2px -2px 10px grey`,
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <Flex
            flexDirection='row'
            className='flex flex-row p-6'
            style={{
              position: 'absolute',
              top: 0,
              right: 0,
              zIndex: 1000,
            }}
          >
            <IconButton className='n-size-token-7' ariaLabel='Fit to screen' onClick={fitNodes}>
              <FitToScreenIcon />
            </IconButton>
            <IconButton className='n-size-token-7' ariaLabel='Reset zoom' onClick={resetZoom}>
              <ResetZoomIcon />
            </IconButton>
          </Flex>
          {loading ? (
            <LoadingSpinner
              size='large'
              style={{
          position: 'absolute',
          top: '50%',
          right: '50%',
              }}
            />
          ) : (
            <></>
          )}
          <InteractiveNvlWrapper
            className='rounded-5xl overflow-hidden'
            ref={nvl}
            nodes={nodes}
            rels={rels}
            onClick={(evt) => console.log('custom click event', evt)}
            mouseEventCallbacks={mouseEventCallbacks}
            style={{ flexGrow: 1 }}
            nvlOptions={{
              initialZoom: 1.1,
              layout: 'd3Force',
              relationshipThreshold: 1,
              selectedBorderColor: '#F5F5F5',
            }}
          />
          <Box className='max-w-[500px]'>
            <Drawer isCloseable={true} isExpanded={isExpanded} position="left" type="overlay" className="rounded-tl-5xl rounded-bl-5xl" onExpandedChange={() => {
              handleIsExpanded(false);
            }}>

              <Drawer.Header>

                <div style={{ marginBottom: '18px' }}>
                  <Typography variant='h5' style={{ fontWeight: 700 }}>Node Details</Typography>
                </div>
                <div
                  style={{
                  borderRadius: '9999px',
                  padding: '6px 12px',
                  background: expandedNode?.color ?? '#eee',
                  color: '#fff',
                  display: 'inline-block',
                  fontWeight: 600,
                  fontSize: '1rem',
                  marginLeft: 0,
                  marginBottom: '24px', // more space below
                  }}
                >
                  {expandedNode?.captions[0]?.labels?.includes('Chunk')
                    ? 'Text Section'
                          : expandedNode?.captions[0]?.labels?.includes('Document')
                          ? 'Document'
                          : expandedNode?.captions[0]?.labels?.includes('Entity')
                          ? 'Entity'
                          : expandedNode?.captions[0]?.labels?.includes('Image')
                          ? 'Image'
                          : expandedNode?.captions[0]?.labels?.includes('Table')
                          ? 'Table'
                          : 'Other'}
                      </div>
              </Drawer.Header>
              <hr style={{ margin: '12px 0' }} />
              <Drawer.Body className="max-w-[500px] pl-5">
                {/* NarrativeText Rendering */}
                {expandedNode?.properties?.type === 'NarrativeText' && (
                  <>
                    <div className='grid grid-cols-2 gap-9 border-b border-gray-300 py-2 text-sm'>
                      <div className='text-gray-600 font-bold'>Text</div>
                      <div className='text-gray-800 break-words max-h-40 overflow-auto'>
                        <ReactMarkdown>{expandedNode.properties.text ?? expandedNode.properties.name ?? expandedNode.properties.id}</ReactMarkdown>
                      </div>                      
                    </div>
                    <div className='grid grid-cols-2 gap-9 border-b border-gray-300 py-2 text-sm'>
                      <div className='text-gray-600 font-bold'>Page</div>
                      <div className='text-gray-800 break-words max-h-40 overflow-auto'>
                        <ReactMarkdown>{String(expandedNode.properties.page_number)}</ReactMarkdown>
                      </div>
                    </div>
                  </>
                )}

                {/* Document Rendering */}
                {expandedNode?.captions?.[0]?.labels?.includes('Document') && (
                    <div className='grid grid-cols-2 gap-9 border-b border-gray-300 py-2 text-sm'>
                      <div className='text-gray-600 font-bold'>Title</div>
                      <div className='text-gray-800 break-words max-h-40 overflow-auto'>
                        <ReactMarkdown>{expandedNode.properties.name}</ReactMarkdown>
                      </div>
                    </div>
                )}
                    

                {/* Document or Entity Labels */}
                {expandedNode?.captions?.[0]?.labels?.includes('Entity') &&  (
                    <>
                    <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', marginBottom: '8px' }}>
                      <div style={{ width: '100px', fontWeight: 500 }}>Name</div>
                      <div style={{ overflowWrap: 'break-word', width: '250px' }}>
                      <ReactMarkdown className="max-w-[250px] object-top overflow-auto">
                        {expandedNode.properties.name}
                      </ReactMarkdown>
                      </div>
                    </div>
                    <hr style={{ margin: '8px 0' }} />
                    <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', marginBottom: '8px' }}>
                      <div style={{ width: '100px', fontWeight: 500 }}>Type</div>
                      <div style={{ overflowWrap: 'break-word', width: '250px' }}>
                      <ReactMarkdown className="max-w-[250px] object-top overflow-auto">
                        {expandedNode.properties.id}
                      </ReactMarkdown>
                      </div>
                    </div>
                    </>
                )}

                {/* Image Rendering */}
                {expandedNode?.properties?.type === 'Image' && (
                  <>
                    <div style={{ width: '100px', fontWeight: 500 }}>Image</div>
                    <img
                      src={`data:image/png;base64,${expandedNode.properties.image_base64}`}
                      alt="Preview"
                      className="max-w-full object-top overflow-auto"
                    />
                  </>
                )}
                <div style={{ height: '12px' }}></div>
                {expandedNode?.properties?.type === 'Image' && expandedNode.properties?.text && (
                    <div className='grid grid-cols-2 gap-9 border-b border-gray-300 py-2 text-sm'>
                      <div className='text-gray-600 font-bold'>Text</div>
                      <div className='text-gray-800 break-words max-h-40 overflow-auto'> 
                        <ReactMarkdown>{expandedNode.properties.text}</ReactMarkdown>
                      </div>
                    </div>
                )}                 
                  
                  

                {/* Table Image */}
                {expandedNode?.properties?.type === 'Table' && (
                  <>
                    <div style={{ width: '100px', fontWeight: 500 }}>Table</div>
                    <img
                      src={`data:image/png;base64,${expandedNode.properties.image_base64}`}
                      alt="Preview"
                      className="max-w-full object-top overflow-auto"
                    />
                  </>
                )}
  
              </Drawer.Body>
            </Drawer>
          </Box>
        </div>
      </Box>
    </Box>
  );
}

export default RetrievalInformation;