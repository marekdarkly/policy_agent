import React from 'react';
import { Box, List, ListItem, ListItemText, Typography, Paper } from '@mui/material';

const EventsLog = ({ logs = [] }) => {
  if (logs.length === 0) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          No events logged yet. Start the simulation to see events.
        </Typography>
      </Box>
    );
  }
  
  return (
    <Paper 
      variant="outlined" 
      sx={{ 
        maxHeight: '400px', 
        overflow: 'auto',
        backgroundColor: 'rgba(0, 0, 0, 0.1)' 
      }}
    >
      <List dense>
        {logs.map((log, index) => (
          <ListItem key={index} divider={index < logs.length - 1}>
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Typography component="span" variant="caption" color="text.secondary">
                    [{log.timestamp}]
                  </Typography>
                  <Typography component="span" variant="body2">
                    {log.message}
                  </Typography>
                </Box>
              }
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
};

export default EventsLog;
