import React from 'react';
import { Box, Button, Typography, Chip } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import { stopSimulation } from '../api/simulationApi';

const SimulationControls = ({ running, connected, onSaveAndStart }) => {
  const handleStart = async () => {
    try {
      // Call the saveAndStart function from ConfigForm
      // This ensures we always use the current React state and proper validation
      await onSaveAndStart();
    } catch (error) {
      console.error('Error starting simulation:', error);
      alert(`Failed to start simulation: ${error.message}`);
    }
  };
  
  const handleStop = async () => {
    try {
      await stopSimulation();
    } catch (error) {
      console.error('Error stopping simulation:', error);
      alert(`Failed to stop simulation: ${error.message}`);
    }
  };
  
  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="subtitle1" sx={{ mr: 2 }}>Status:</Typography>
        <Chip 
          label={connected ? 'Connected' : 'Disconnected'} 
          color={connected ? 'success' : 'error'}
          size="small"
        />
      </Box>
      
      <Box sx={{ display: 'flex', gap: 2 }}>
        <Button
          variant="contained"
          color="warning"
          startIcon={<PlayArrowIcon />}
          onClick={handleStart}
          disabled={running || !connected}
          fullWidth
        >
          Save & Start Simulation
        </Button>
        
        <Button
          variant="contained"
          color="error"
          startIcon={<StopIcon />}
          onClick={handleStop}
          disabled={!running || !connected}
          fullWidth
        >
          Stop Simulation
        </Button>
      </Box>
    </Box>
  );
};

export default SimulationControls;
