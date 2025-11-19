import React, { useState } from 'react';
import { Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, Typography, Box, Alert, CircularProgress, List, ListItem, ListItemIcon, ListItemText, Divider, Link } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import PendingIcon from '@mui/icons-material/Pending';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import { createLaunchDarklyResources, updateEnvironmentKey } from '../api/launchDarklyApi';

// Helper function to save the configuration, similar to handleSubmit in ConfigForm
const saveConfiguration = (currentConfig) => {
  try {
    // Create a copy of the config
    const submissionConfig = { ...currentConfig };
    
    // Process the ranges
    ['latency_metric_1_false_range', 'latency_metric_1_true_range'].forEach(rangeKey => {
      if (typeof submissionConfig[rangeKey] === 'string') {
        try {
          const values = submissionConfig[rangeKey].split(',').map(v => parseInt(v.trim(), 10));
          const validValues = values.filter(v => !isNaN(v));
          
          // Ensure array has exactly 2 elements
          if (validValues.length !== 2) {
            throw new Error(`${rangeKey} must have exactly 2 values`);
          }
          
          submissionConfig[rangeKey] = validValues;
        } catch (err) {
          throw new Error(`Invalid range format for ${rangeKey}: ${err.message}`);
        }
      } else if (!Array.isArray(submissionConfig[rangeKey])) {
        // If it's neither a string nor an array, default to the placeholder values
        submissionConfig[rangeKey] = rangeKey.includes('false') ? [50, 125] : [52, 131];
      }
    });
    
    // Make sure all number fields are integers
    ['error_metric_1_false_converted', 'error_metric_1_true_converted', 
     'business_metric_1_false_converted', 'business_metric_1_true_converted'].forEach(field => {
      if (typeof submissionConfig[field] === 'string') {
        submissionConfig[field] = parseInt(submissionConfig[field], 10) || 0;
      }
    });
    
    // Ensure toggle states are properly saved as booleans
    ['error_metric_enabled', 'latency_metric_enabled', 'business_metric_enabled'].forEach(toggleKey => {
      // Explicitly convert to boolean
      if (submissionConfig[toggleKey] === false || submissionConfig[toggleKey] === 'false' || submissionConfig[toggleKey] === 0) {
        submissionConfig[toggleKey] = false;
      } else {
        submissionConfig[toggleKey] = true;
      }
    });
    
    // Save to localStorage
    localStorage.setItem('ldConfig', JSON.stringify(submissionConfig));
    
    // Return the processed config
    return submissionConfig;
  } catch (error) {
    console.error('Error saving configuration:', error);
    throw error;
  }
};

const LaunchDarklyResourceCreator = ({ disabled }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [configValues, setConfigValues] = useState({
    flag_key: '',
    project_key: '',
    error_metric_1: '',
    latency_metric_1: '',
    business_metric_1: '',
    error_metric_enabled: true,
    latency_metric_enabled: true,
    business_metric_enabled: true
  });
  const [resourceStatuses, setResourceStatuses] = useState({
    flag: { status: 'pending', message: '' },
    errorMetric: { status: 'pending', message: '' },
    latencyMetric: { status: 'pending', message: '' },
    businessMetric: { status: 'pending', message: '' },
    metricAttachment: { status: 'pending', message: '' }
  });

  // Helper function to generate the LaunchDarkly flag URL
  const getFlagUrl = () => {
    if (!configValues.project_key || !configValues.flag_key) return null;
    
    // Get current config to access environment_key
    let currentConfig = {};
    try {
      const savedConfig = localStorage.getItem('ldConfig');
      if (savedConfig) {
        currentConfig = JSON.parse(savedConfig);
      }
    } catch (error) {
      console.error('Error loading config:', error);
    }
    
    // Use environment_key if available, otherwise don't include env parameters
    const envKey = currentConfig.environment_key;
    if (envKey) {
      return `https://app.launchdarkly.com/projects/${configValues.project_key}/flags/${configValues.flag_key}/targeting?env=${envKey}&selected-env=${envKey}`;
    } else {
      return `https://app.launchdarkly.com/projects/${configValues.project_key}/flags/${configValues.flag_key}/`;
    }
  };

  const handleClickOpen = () => {
    setOpen(true);
    // Reset states
    setLoading(false);
    setError(null);
    setResult(null);
    
    // Get the current form values directly from the form elements
    const formElements = document.querySelectorAll('input[name], textarea[name]');
    let currentConfig = {};
    
    // First get the saved config as a base
    try {
      const savedConfig = localStorage.getItem('ldConfig');
      if (savedConfig) {
        currentConfig = JSON.parse(savedConfig);
      }
      
      // Update with latest values from the form
      formElements.forEach(element => {
        if (element.name) {
          // Handle checkbox/switch inputs
          if (element.type === 'checkbox') {
            currentConfig[element.name] = element.checked;
          } 
          // Handle regular inputs
          else {
            currentConfig[element.name] = element.value;
          }
        }
      });
      
      // Update display values with current form values
      setConfigValues({
        flag_key: currentConfig.flag_key || '',
        project_key: currentConfig.project_key || '',
        error_metric_1: currentConfig.error_metric_1 || '',
        latency_metric_1: currentConfig.latency_metric_1 || '',
        business_metric_1: currentConfig.business_metric_1 || '',
        error_metric_enabled: currentConfig.error_metric_enabled !== false,
        latency_metric_enabled: currentConfig.latency_metric_enabled !== false,
        business_metric_enabled: currentConfig.business_metric_enabled !== false
      });
    } catch (error) {
      console.error('Error loading config values:', error);
    }
    
    setResourceStatuses({
      flag: { status: 'pending', message: '' },
      errorMetric: { status: 'pending', message: '' },
      latencyMetric: { status: 'pending', message: '' },
      businessMetric: { status: 'pending', message: '' },
      metricAttachment: { status: 'pending', message: '' }
    });
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleCreate = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Get current form values directly from the DOM to ensure we have the latest values
      // even if the user hasn't clicked Save in the ConfigForm
      const formElements = document.querySelectorAll('input[name], textarea[name]');
      let currentConfig = {};
      
      // First get the saved config as a base
      const savedConfig = localStorage.getItem('ldConfig');
      if (savedConfig) {
        currentConfig = JSON.parse(savedConfig);
      }
      
      // Update config with latest values from form fields
      formElements.forEach(element => {
        if (element.name) {
          // Handle checkbox/switch inputs
          if (element.type === 'checkbox') {
            currentConfig[element.name] = element.checked;
          } 
          // Handle regular inputs
          else {
            currentConfig[element.name] = element.value;
          }
        }
      });
      
      // Validate required fields
      if (!currentConfig.sdk_key || !currentConfig.api_key || !currentConfig.project_key || !currentConfig.flag_key) {
        throw new Error('Please fill out all required fields (SDK Key, API Key, Project Key, Flag Key)');
      }
      
      // Save current config to localStorage before proceeding
      const processedConfig = saveConfiguration(currentConfig);
      
      // Update environment key before creating resources
      if (processedConfig.sdk_key && processedConfig.api_key && processedConfig.project_key) {
        console.log('ResourceCreator: Updating environment key before creating resources');
        await updateEnvironmentKey(processedConfig);
      }
      
      // Create LaunchDarkly resources
      const result = await createLaunchDarklyResources(processedConfig);
      
      // Update statuses based on results
      const newStatuses = { 
        flag: { 
          status: result.flag.error ? 'error' : 'success',
          message: result.flag.error || 'Flag created successfully!'
        },
        errorMetric: { 
          status: !processedConfig.error_metric_enabled ? 'disabled' : 
                  result.metrics.error?.error ? 'error' : 'success',
          message: !processedConfig.error_metric_enabled ? 'Metric disabled' :
                   result.metrics.error?.error || 'Error metric created successfully!'
        },
        latencyMetric: { 
          status: !processedConfig.latency_metric_enabled ? 'disabled' : 
                  result.metrics.latency?.error ? 'error' : 'success',
          message: !processedConfig.latency_metric_enabled ? 'Metric disabled' :
                   result.metrics.latency?.error || 'Latency metric created successfully!'
        },
        businessMetric: { 
          status: !processedConfig.business_metric_enabled ? 'disabled' : 
                  result.metrics.business?.error ? 'error' : 'success',
          message: !processedConfig.business_metric_enabled ? 'Metric disabled' :
                   result.metrics.business?.error || 'Business metric created successfully!'
        },
        metricAttachment: {
          status: getMetricAttachmentStatus(processedConfig, result.metricAttachment),
          message: getMetricAttachmentMessage(processedConfig, result.metricAttachment)
        }
      };
      
      setResourceStatuses(newStatuses);
      setResult(result);
    } catch (error) {
      console.error('Error creating LaunchDarkly resources:', error);
      setError(error.message || 'An error occurred while creating resources');
      
      // Update all pending statuses to error
      setResourceStatuses(prev => {
        const updated = {...prev};
        Object.keys(updated).forEach(key => {
          if (updated[key].status === 'pending' || updated[key].status === 'loading') {
            updated[key] = { status: 'error', message: 'Failed to process' };
          }
        });
        return updated;
      });
    } finally {
      setLoading(false);
    }
  };

  // Helper function to render status icon
  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'disabled':
        return <PendingIcon color="disabled" />;
      case 'loading':
        return <CircularProgress size={20} />;
      default:
        return <PendingIcon color="disabled" />;
    }
  };

  // Helper to format the metrics that will be attached
  const getMetricKeysString = (values) => {
    const metrics = [];
    if (values.error_metric_enabled && values.error_metric_1) metrics.push(`"${values.error_metric_1}"`);
    if (values.latency_metric_enabled && values.latency_metric_1) metrics.push(`"${values.latency_metric_1}"`);
    if (values.business_metric_enabled && values.business_metric_1) metrics.push(`"${values.business_metric_1}"`);
    
    if (metrics.length === 0) return 'No metrics';
    if (metrics.length === 1) return metrics[0];
    if (metrics.length === 2) return `${metrics[0]} and ${metrics[1]}`;
    return `${metrics.slice(0, -1).join(', ')}, and ${metrics[metrics.length - 1]}`;
  };

  // Add a helper function above handleCreate
  const getMetricAttachmentMessage = (config, attachResult) => {
    // No metrics enabled
    if (!config.error_metric_enabled && !config.latency_metric_enabled && !config.business_metric_enabled) {
      return 'No metrics to attach';
    }
    
    // No response at all
    if (!attachResult) {
      return 'Error: No response from attachment process';
    }
    
    // Success cases
    if (attachResult.success) {
      if (attachResult.message) {
        return attachResult.message;
      }
      if (attachResult.metricKeys && attachResult.metricKeys.length > 0) {
        return `Attached ${attachResult.metricKeys.length} metrics to flag: ${attachResult.metricKeys.join(', ')}`;
      }
      return 'Metrics attached to flag successfully!';
    }
    
    // Error with success status code (sometimes happens with 200 responses)
    if (attachResult.error && (
      attachResult.status_code === 200 || 
      (attachResult.raw_response && attachResult.raw_response.status_code === 200) ||
      attachResult.error.includes('200')
    )) {
      return 'Metrics successfully attached (or already attached) to flag';
    }
    
    // Resource already exists error (409)
    if (attachResult.error && (
      attachResult.status_code === 409 || 
      attachResult.error.includes('409') ||
      attachResult.error.includes('already exists')
    )) {
      return 'Metrics are already attached to this flag';
    }
    
    // General error case
    if (attachResult.error) {
      return attachResult.error;
    }
    
    // Fallback
    return 'Processing attachment request...';
  };

  // Add the new helper function for determining metric attachment status
  const getMetricAttachmentStatus = (config, attachResult) => {
    // No metrics enabled
    if (!config.error_metric_enabled && !config.latency_metric_enabled && !config.business_metric_enabled) {
      return 'disabled';
    }
    
    // No response at all
    if (!attachResult) {
      return 'pending';
    }
    
    // Success is explicitly set
    if (attachResult.success) {
      return 'success';
    }
    
    // Error with success code (200)
    if (attachResult.raw_response && attachResult.raw_response.status_code === 200) {
      return 'success';
    }
    
    if (attachResult.status_code === 200) {
      return 'success';
    }
    
    // Conflict/already exists (409)
    if (attachResult.status_code === 409 || 
       (attachResult.error && attachResult.error.includes('409'))) {
      return 'success';
    }
    
    // Genuine error
    if (attachResult.error && !attachResult.success) {
      return 'error';
    }
    
    // Default fallback
    return 'pending';
  };

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleClickOpen}
          disabled={disabled}
          sx={{ px: 4 }}
        >
          ✨ Auto-Create LaunchDarkly Resources ✨
        </Button>
      </Box>
      
      <Dialog open={open} onClose={handleClose} maxWidth="md">
        <DialogTitle>Create LaunchDarkly Resources</DialogTitle>
        <DialogContent>
          <DialogContentText>
            This will create the following resources in LaunchDarkly based on your configuration:
          </DialogContentText>
          
          <List sx={{ mt: 2 }}>
            <ListItem>
              <ListItemIcon>
                {getStatusIcon(resourceStatuses.flag.status)}
              </ListItemIcon>
              <ListItemText 
                primary={
                  <Box display="flex" alignItems="center">
                    <Typography fontWeight="bold" mr={1}>Boolean Flag:</Typography>
                    <Typography color="info.main" fontFamily="monospace">
                      {configValues.flag_key || 'Not set'}
                    </Typography>
                    {result && resourceStatuses.flag.status === 'success' && getFlagUrl() && (
                      <Button 
                        component={Link}
                        href={getFlagUrl()}
                        target="_blank"
                        rel="noopener noreferrer"
                        size="small"
                        endIcon={<OpenInNewIcon fontSize="small" />}
                        sx={{ ml: 1 }}
                      >
                        View in LaunchDarkly
                      </Button>
                    )}
                  </Box>
                }
                secondary={resourceStatuses.flag.status !== 'pending' ? resourceStatuses.flag.message : 'Pending creation'} 
              />
            </ListItem>
            
            <Divider component="li" />
            
            <ListItem>
              <ListItemIcon>
                {getStatusIcon(resourceStatuses.errorMetric.status)}
              </ListItemIcon>
              <ListItemText 
                primary={
                  <Box display="flex" alignItems="center" sx={{ opacity: configValues.error_metric_enabled ? 1 : 0.5 }}>
                    <Typography fontWeight="bold" mr={1}>Error Metric (lower is better):</Typography>
                    <Typography color="info.main" fontFamily="monospace">
                      {configValues.error_metric_enabled 
                        ? configValues.error_metric_1 || 'Not set'
                        : 'Disabled'}
                    </Typography>
                  </Box>
                }
                secondary={resourceStatuses.errorMetric.status !== 'pending' ? resourceStatuses.errorMetric.message : 'Pending creation'} 
              />
            </ListItem>
            
            <Divider component="li" />
            
            <ListItem>
              <ListItemIcon>
                {getStatusIcon(resourceStatuses.latencyMetric.status)}
              </ListItemIcon>
              <ListItemText 
                primary={
                  <Box display="flex" alignItems="center" sx={{ opacity: configValues.latency_metric_enabled ? 1 : 0.5 }}>
                    <Typography fontWeight="bold" mr={1}>Latency Metric (lower is better):</Typography>
                    <Typography color="info.main" fontFamily="monospace">
                      {configValues.latency_metric_enabled 
                        ? configValues.latency_metric_1 || 'Not set'
                        : 'Disabled'}
                    </Typography>
                  </Box>
                }
                secondary={resourceStatuses.latencyMetric.status !== 'pending' ? resourceStatuses.latencyMetric.message : 'Pending creation'} 
              />
            </ListItem>
            
            <Divider component="li" />
            
            <ListItem>
              <ListItemIcon>
                {getStatusIcon(resourceStatuses.businessMetric.status)}
              </ListItemIcon>
              <ListItemText 
                primary={
                  <Box display="flex" alignItems="center" sx={{ opacity: configValues.business_metric_enabled ? 1 : 0.5 }}>
                    <Typography fontWeight="bold" mr={1}>Conversion Metric (higher is better):</Typography>
                    <Typography color="info.main" fontFamily="monospace">
                      {configValues.business_metric_enabled 
                        ? configValues.business_metric_1 || 'Not set'
                        : 'Disabled'}
                    </Typography>
                  </Box>
                }
                secondary={resourceStatuses.businessMetric.status !== 'pending' ? resourceStatuses.businessMetric.message : 'Pending creation'} 
              />
            </ListItem>
            
            <Divider component="li" />
            
            {/* <ListItem>
              <ListItemIcon>
                {getStatusIcon(resourceStatuses.metricAttachment.status)}
              </ListItemIcon>
              <ListItemText 
                primary={
                  <Box display="flex" alignItems="center">
                    <Typography fontWeight="bold" mr={1}>Attach Metrics to Flag:</Typography>
                    <Typography color="info.main" fontFamily="monospace">
                      {(configValues.error_metric_enabled || configValues.latency_metric_enabled || configValues.business_metric_enabled) 
                        ? `${getMetricKeysString(configValues)} will be attached for measured rollout`
                        : 'No metrics to attach'}
                    </Typography>
                  </Box>
                }
                secondary={
                  resourceStatuses.metricAttachment.status === 'loading' 
                    ? 'Attaching metrics to flag...' 
                    : resourceStatuses.metricAttachment.status === 'pending' 
                      ? 'Waiting to attach metrics...' 
                      : resourceStatuses.metricAttachment.message
                } 
              />
            </ListItem> */}
          </List>
          
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
          
          {result && !error && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Resources created successfully!
              {getFlagUrl() && (
                <Box mt={1}>
                  <Link 
                    href={getFlagUrl()} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    sx={{ display: 'inline-flex', alignItems: 'center' }}
                  >
                    View flag in LaunchDarkly <OpenInNewIcon fontSize="small" sx={{ ml: 0.5 }} />
                  </Link>
                </Box>
              )}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} color="primary">
            Close
          </Button>
          <Button 
            onClick={handleCreate} 
            color="primary" 
            variant="contained"
            disabled={loading || !!result}
            startIcon={loading && <CircularProgress size={20} />}
          >
            {loading ? 'Creating...' : result ? 'Created' : 'Create Resources'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default LaunchDarklyResourceCreator; 