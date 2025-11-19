import React, { useEffect, useState } from 'react';
import { Box, Typography, Grid, Paper, Chip, Divider, Card, CardContent, Stack } from '@mui/material';

// Format number with specified decimal places
const formatNumber = (num, decimals = 1) => {
  if (num === undefined || num === null) return '0';
  return Number(num).toFixed(decimals);
};

// Format timestamp to readable time
const formatTime = (timestamp) => {
  if (!timestamp) return 'N/A';
  const date = new Date(timestamp * 1000);
  return date.toLocaleTimeString();
};

// Format elapsed time in seconds to readable duration (e.g., 2h 15m 30s)
const formatDuration = (seconds) => {
  if (!seconds) return '0s';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  
  let result = '';
  if (hours > 0) result += `${hours}h `;
  if (minutes > 0 || hours > 0) result += `${minutes}m `;
  result += `${remainingSeconds}s`;
  
  return result;
};

// Stat display component for consistent styling
const StatDisplay = ({ label, value, unit = '', color = 'warning.main', subtitle = null }) => (
  <Box sx={{ textAlign: 'center', mb: 1, p: 0.5, borderRadius: 1, bgcolor: 'rgba(0, 0, 0, 0.05)' }}>
    <Typography 
      variant="body2" 
      display="block" 
      sx={{ fontWeight: 'medium' }}
    >
      {label}
    </Typography>
    <Typography 
      variant="h6" 
      color={color} 
      sx={{ fontWeight: 'bold', lineHeight: 1, my: 0.25, fontSize: '1.125rem' }}
    >
      {value}{unit}
    </Typography>
    {subtitle && (
      <Typography 
        variant="caption" 
        color="text.secondary" 
        sx={{ fontSize: '0.75rem', display: 'block', opacity: 0.7 }}
      >
        {subtitle}
      </Typography>
    )}
  </Box>
);

// Format stats for display
const formatStats = (stats) => {
  if (!stats) return { 
    errorEvents: 0,
    latencyEvents: 0,
    conversionEvents: 0,
    totalEvaluations: 0,
    inExperiment: 0
  };
  
  return {
    // For errors, .sum is the actual error count
    errorEvents: stats.error_rate.sum || 0,
    // For latency, .count is the number of events
    latencyEvents: stats.latency.count || 0,
    // For business/conversions, .sum is the actual conversion count
    conversionEvents: stats.business.sum || 0,
    // Evaluations statistics
    totalEvaluations: stats.evaluations || 0,
    inExperiment: stats.in_experiment || 0
  };
};

const StatusPanel = ({ status }) => {
  const controlStats = formatStats(status.stats?.control);
  const treatmentStats = formatStats(status.stats?.treatment);
  
  // State to keep track of elapsed time
  const [elapsedTime, setElapsedTime] = useState(0);
  
  // Update elapsed time every second if simulation is running
  useEffect(() => {
    let interval;
    
    // Reset counter to 0 if simulation is running but no events have been sent yet
    if (status.running && !status.first_event_time) {
      setElapsedTime(0);
    } 
    // Start counting from first event time if available and running
    else if (status.running && status.first_event_time) {
      // Initial calculation from first event time
      const initialElapsed = Math.floor(Date.now() / 1000 - status.first_event_time);
      setElapsedTime(initialElapsed);
      
      // Set up interval to update every second
      interval = setInterval(() => {
        const elapsed = Math.floor(Date.now() / 1000 - status.first_event_time);
        setElapsedTime(elapsed);
      }, 1000);
    } 
    // Use end_time for completed simulations
    else if (!status.running && status.first_event_time && status.end_time) {
      // If not running and we have both first event and end times, calculate final elapsed time
      const finalElapsed = Math.floor(status.end_time - status.first_event_time);
      setElapsedTime(finalElapsed);
    } 
    // Handle case where we have first_event_time but no end_time (unusual, but possible)
    else if (status.first_event_time) {
      // If we only have first event time
      const currentElapsed = Math.floor(Date.now() / 1000 - status.first_event_time);
      setElapsedTime(currentElapsed);
    }
    // Reset counter when simulation has just started but no events have been sent
    else if (status.running) {
      setElapsedTime(0);
    }
    
    // Clean up interval
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [status.running, status.first_event_time, status.end_time]);

  return (
    <Box>
      {/* Guarded Rollout Status */}
      <Paper 
        variant="outlined" 
        sx={{ 
          p: 1.25, 
          backgroundColor: status.guarded_rollout_active ? 'rgba(46, 125, 50, 0.1)' : 'rgba(211, 47, 47, 0.1)',
          borderColor: status.guarded_rollout_active ? 'success.main' : 'error.main',
          mb: 1.5,
          borderRadius: 1.5
        }}
      >
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          mb: 0.75 
        }}>
          <Typography 
            variant="body1" 
            sx={{ 
              fontWeight: 'bold', 
              textTransform: 'uppercase', 
              letterSpacing: 0.5, 
              ml: 1,
              fontSize: '1rem' 
            }}
          >
            Guarded Rollout
          </Typography>
          <Chip
            label={status.guarded_rollout_active ? 'ACTIVE' : 'INACTIVE'}
            color={status.guarded_rollout_active ? 'success' : 'error'}
            variant="filled"
            size="small"
            sx={{ fontWeight: 'bold', mr: 1 }}
          />
        </Box>
        <Typography 
          variant="caption" 
          color="text.secondary"
          sx={{ 
            display: 'block',
            textAlign: 'center',
            fontSize: '0.75rem',
            fontStyle: 'italic',
            opacity: 0.8,
            px: 1
          }}
        >
          Monitors API every 5 seconds • Auto-starts when release detected • Auto-stops when release ends
        </Typography>
      </Paper>
      
      {/* Time Information */}
      <Paper 
        variant="outlined" 
        sx={{ 
          p: 1.25, 
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          borderColor: 'divider',
          mb: 1.5,
          borderRadius: 1.5
        }}
      >
        <Typography 
          variant="body1" 
          sx={{ 
            fontWeight: 'bold', 
            mb: 1, 
            fontSize: '1rem'
          }}
        >
          Timing Information
        </Typography>
        
        <Grid container spacing={1}>
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 0.5, borderRadius: 1, bgcolor: 'rgba(0, 0, 0, 0.05)' }}>
              <Typography variant="body2" sx={{ fontWeight: 'medium' }}>First Event At</Typography>
              <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 'bold', mt: 0.25 }}>
                {formatTime(status.first_event_time)}
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 0.5, borderRadius: 1, bgcolor: 'rgba(0, 0, 0, 0.05)' }}>
              <Typography variant="body2" sx={{ fontWeight: 'medium' }}>Running For</Typography>
              <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 'bold', mt: 0.25 }}>
                {status.running && !status.first_event_time ? 'Waiting...' : formatDuration(elapsedTime)}
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 0.5, borderRadius: 1, bgcolor: 'rgba(0, 0, 0, 0.05)' }}>
              <Typography variant="body2" sx={{ fontWeight: 'medium' }}>Ended At</Typography>
              <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 'bold', mt: 0.25 }}>
                {status.running ? 'Waiting...' : formatTime(status.end_time)}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Flag Evaluations Section */}
      <Paper 
        variant="outlined" 
        sx={{ 
          p: 1.25, 
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          borderColor: 'divider',
          mb: 1.5,
          borderRadius: 1.5
        }}
      >
        <Typography 
          variant="body1" 
          sx={{ 
            fontWeight: 'bold', 
            mb: 1, 
            fontSize: '1rem'
          }}
        >
          Flag Evaluations
        </Typography>
        
        <Grid container spacing={1}>
          {/* Total Evaluations */}
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 0.5, borderRadius: 1, bgcolor: 'rgba(0, 0, 0, 0.05)' }}>
              <Typography variant="body2" sx={{ fontWeight: 'medium' }}>Total Evaluations</Typography>
              <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 'bold', mt: 0.25 }}>
                {(controlStats.totalEvaluations + treatmentStats.totalEvaluations).toLocaleString()}
              </Typography>
            </Box>
          </Grid>
          
          {/* Control In Experiment */}
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 0.5, borderRadius: 1, bgcolor: 'rgba(0, 0, 0, 0.05)' }}>
              <Typography variant="body2" sx={{ fontWeight: 'medium' }}>Control In Experiment</Typography>
              <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 'bold', mt: 0.25 }}>
                {controlStats.inExperiment.toLocaleString()}
              </Typography>
            </Box>
          </Grid>
          
          {/* Treatment In Experiment */}
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 0.5, borderRadius: 1, bgcolor: 'rgba(0, 0, 0, 0.05)' }}>
              <Typography variant="body2" sx={{ fontWeight: 'medium' }}>Treatment In Experiment</Typography>
              <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 'bold', mt: 0.25 }}>
                {treatmentStats.inExperiment.toLocaleString()}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Statistics Section */}
      <Paper 
        variant="outlined" 
        sx={{ 
          p: 1.25, 
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          borderColor: 'divider',
          borderRadius: 1.5
        }}
      >
        <Typography 
          variant="body1" 
          sx={{ 
            fontWeight: 'bold', 
            mb: 1, 
            fontSize: '1rem'
          }}
        >
          Aggregated Events
        </Typography>
        
        <Grid container spacing={1}>
          {/* Control Group */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined" sx={{ backgroundColor: 'rgba(0, 0, 0, 0.1)', height: '100%' }}>
              <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                <Typography 
                  variant="body1" 
                  sx={{ 
                    fontWeight: 'bold', 
                    color: 'text.primary', 
                    mb: 0.5,
                    fontSize: '1rem'
                  }}
                >
                  Control Group
                </Typography>
                <Divider sx={{ mb: 1 }} />
                
                <Grid container spacing={1}>
                  <Grid item xs={4}>
                    <StatDisplay 
                      label="Error Events" 
                      value={controlStats.errorEvents} 
                      color="error.main"
                    />
                  </Grid>
                  <Grid item xs={4}>
                    <StatDisplay 
                      label="Latency Events" 
                      value={controlStats.latencyEvents} 
                      color="warning.main"
                    />
                  </Grid>
                  <Grid item xs={4}>
                    <StatDisplay 
                      label="Conversion Events" 
                      value={controlStats.conversionEvents} 
                      color="success.main"
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Treatment Group */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined" sx={{ backgroundColor: 'rgba(0, 0, 0, 0.1)', height: '100%' }}>
              <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                <Typography 
                  variant="body1" 
                  sx={{ 
                    fontWeight: 'bold', 
                    color: 'text.primary', 
                    mb: 0.5,
                    fontSize: '1rem'
                  }}
                >
                  Treatment Group
                </Typography>
                <Divider sx={{ mb: 1 }} />
                
                <Grid container spacing={1}>
                  <Grid item xs={4}>
                    <StatDisplay 
                      label="Error Events" 
                      value={treatmentStats.errorEvents} 
                      color="error.main"
                    />
                  </Grid>
                  <Grid item xs={4}>
                    <StatDisplay 
                      label="Latency Events" 
                      value={treatmentStats.latencyEvents}
                      color="warning.main" 
                    />
                  </Grid>
                  <Grid item xs={4}>
                    <StatDisplay 
                      label="Conversion Events" 
                      value={treatmentStats.conversionEvents} 
                      color="success.main"
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Last Error Display */}
      {status.last_error && (
        <Paper 
          variant="outlined" 
          sx={{ 
            p: 1.25, 
            backgroundColor: 'rgba(211, 47, 47, 0.1)',
            borderColor: 'error.main',
            mt: 1.5,
            borderRadius: 1.5
          }}
        >
          <Typography 
            variant="body1" 
            sx={{ 
              fontWeight: 'bold', 
              color: 'error.main', 
              mb: 0.25,
              fontSize: '1rem'
            }}
          >
            Last Error
          </Typography>
          <Typography 
            variant="body2" 
            color="error.main"
            sx={{ fontSize: '0.875rem' }}
          >
            {status.last_error}
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default StatusPanel;
