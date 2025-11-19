import React, { useState, useEffect, useCallback } from 'react';
import { Container, Box, Typography, Paper, Button, CircularProgress, Alert } from '@mui/material';
import ArticleIcon from '@mui/icons-material/Article';
import ConfigForm from './components/ConfigForm';
import SimulationControls from './components/SimulationControls';
import StatusPanel from './components/StatusPanel';
import LogExplorer from './components/LogExplorer';
import { getStatus, getLogs } from './api/simulationApi';
import useWebSocket from './hooks/useWebSocket';

function App() {
  const [status, setStatus] = useState({ running: false, events_sent: 0, last_error: null });
  const [showLogExplorer, setShowLogExplorer] = useState(false);
  const [logsLoading, setLogsLoading] = useState(false);
  const [configStatus, setConfigStatus] = useState({ error: null, success: null });
  
  // Ref to store the ConfigForm's saveAndStart function
  const saveAndStartRef = React.useRef(null);
  
  // Initialize WebSocket connection for real-time updates
  const { connected } = useWebSocket({
    onMessage: (data) => {
      // Handle status messages
      if (data.type === 'status') {
        setStatus(data.data);
      }
    }
  });
  
  // Fetch initial status when component mounts
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await getStatus();
        setStatus(response);
      } catch (error) {
        console.error('Error fetching status:', error);
      }
    };
    
    fetchStatus();
  }, []);
  
  // Hide log explorer when simulation starts
  useEffect(() => {
    if (status.running) {
      setShowLogExplorer(false);
    }
  }, [status.running]);
  
  // Handle showing log explorer
  const handleShowLogs = useCallback(async () => {
    setShowLogExplorer(true);
  }, []);

  // Handle configuration status updates
  const handleConfigStatusChange = useCallback((error, success) => {
    setConfigStatus({ error, success });
  }, []);
  
  // Handle save and start from SimulationControls
  const handleSaveAndStart = useCallback(async () => {
    if (saveAndStartRef.current) {
      return await saveAndStartRef.current();
    } else {
      throw new Error('Configuration form is not ready');
    }
  }, []);
  
  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold' }}>
          LaunchDarkly Guarded Release Runner
        </Typography>
      </Box>
      
      {/* Main content layout */}
      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', md: '3fr 2fr' }, 
        gap: 2,
        alignItems: 'stretch'
      }}>
        {/* Left column - Configuration */}
        <Box sx={{ 
          display: 'flex',
          flexDirection: 'column',
          height: '100%'
        }}>
          <Paper sx={{ 
            p: 2, 
            height: '100%',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              mb: 1,
              minHeight: '28px'
            }}>
              <Typography variant="h6" sx={{ mb: 0 }}>Configuration</Typography>
              {configStatus.error && (
                <Alert 
                  severity="error" 
                  icon={false}
                  sx={{ 
                    py: 0, 
                    px: 1, 
                    ml: 1.5, 
                    fontSize: '0.75rem', 
                    height: '24px',
                    maxWidth: '50%',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    '& .MuiAlert-message': {
                      p: 0,
                      display: 'flex',
                      alignItems: 'center',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }
                  }}
                >
                  {configStatus.error}
                </Alert>
              )}
              {configStatus.success && !configStatus.error && (
                <Alert 
                  severity="success" 
                  icon={false}
                  sx={{ 
                    py: 0, 
                    px: 1, 
                    ml: 1.5, 
                    fontSize: '0.75rem', 
                    height: '24px',
                    maxWidth: '50%',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    '& .MuiAlert-message': {
                      p: 0,
                      display: 'flex',
                      alignItems: 'center',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }
                  }}
                >
                  {configStatus.success}
                </Alert>
              )}
            </Box>
            <ConfigForm 
              disabled={status.running} 
              onStatusChange={handleConfigStatusChange}
              saveAndStartRef={saveAndStartRef}
            />
          </Paper>
        </Box>
        
        {/* Right column - Controls and Status */}
        <Box sx={{ 
          display: 'flex',
          flexDirection: 'column',
          height: '100%'
        }}>
          <Paper sx={{ 
            p: 2,
            mb: 2,
            display: 'flex',
            flexDirection: 'column'
          }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 1 }}>Controls</Typography>
            <SimulationControls 
              running={status.running} 
              connected={connected}
              onSaveAndStart={handleSaveAndStart}
            />
          </Paper>
          
          <Paper sx={{ 
            p: 2,
            mb: 2,
            display: 'flex',
            flexDirection: 'column',
            flex: 1
          }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 1 }}>Status</Typography>
            <StatusPanel status={status} />
          </Paper>
          
          {/* Show log explorer only after simulation has completed */}
          {!status.running && status.events_sent > 0 && (
            <Paper sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="h6" gutterBottom sx={{ mb: 0 }}>Simulation Logs</Typography>
                <Button
                  variant="outlined"
                  startIcon={showLogExplorer ? null : <ArticleIcon />}
                  onClick={handleShowLogs}
                  disabled={logsLoading}
                  size="small"
                >
                  {showLogExplorer ? 'Refresh Logs' : 'View Detailed Logs'}
                  {logsLoading && <CircularProgress size={16} sx={{ ml: 1 }} />}
                </Button>
              </Box>
              
              {showLogExplorer && (
                <LogExplorer 
                  simulationStatus={status}
                  onLogsLoading={setLogsLoading}
                />
              )}
            </Paper>
          )}
        </Box>
      </Box>
    </Container>
  );
}

export default App;
